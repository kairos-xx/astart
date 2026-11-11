"""M8-25 fixer: normalise f-string replacement-field interiors.

Rewrites whitespace *placement* inside ``JoinedStr`` fields —
``f"{ x }"`` → ``f"{x}"``, ``f"{x !r}"`` → ``f"{x!r}"`` — while
preserving the expression text, conversion flags and format-spec text
verbatim. ``=``-debug fields, unusual expression spacing and anything
the scanner cannot prove safe are refused. Standalone module;
catalog/applier wiring is deferred (M8-22).

"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from tokenize import (
    FSTRING_END,
    FSTRING_START,
    OP,
    TokenError,
    TokenInfo,
    generate_tokens,
)
from typing import Final, final


@final
@dataclass(frozen=True, slots=True)
class FStringChange:
    """One applied interior rewrite.

    Attributes:
        kind (str): Always ``"interior"``.
        line (int): 1-based line of the field.

    """

    kind: str
    line: int


@final
@dataclass(slots=True)
class FStringReport:
    """Outcome of an f-string normalisation pass.

    Attributes:
        changes (list[FStringChange]): Applied rewrites.
        output (str): Rewritten source.
        skipped (dict[str, int]): Refusal reason to count.

    """

    changes: list[FStringChange] = field(default_factory=list)
    output: str = ""
    skipped: dict[str, int] = field(default_factory=dict)


_BRACKETS: Final[dict[str, str]] = {"(": ")", "[": "]", "{": "}"}
_CLOSERS: Final[dict[str, str]] = {")": "(", "]": "[", "}": "{"}
_QUOTES: Final[dict[str, str]] = {'"': '"', "'": "'"}


@final
class _InteriorScanner:
    """Depth/string-aware scanner for one field interior.

    Tracks bracket depth and string literals while recording the first
    top-level ``!``, ``:``, ``=`` positions. ``step`` consumes one
    lexical unit (char, escape pair or triple-quote opener).

    """

    __slots__ = (
        "bang_at",
        "colon_at",
        "depth",
        "equals_at",
        "quote",
        "triple",
    )

    def __init__(self) -> None:
        """Reset the scanner to its initial state."""
        self.depth: int = 0
        self.quote: str | None = None
        self.triple: str | None = None
        self.bang_at: int = -1
        self.colon_at: int = -1
        self.equals_at: int = -1

    def step(self, *, text: str, index: int) -> int:
        """Consume the unit starting at ``index``.

        Args:
            index (int): Current offset.
            text (str): Interior text.

        Returns:
            int: Number of characters consumed (1, 2 or 3).

        """
        char: str = text[index]
        if self.quote is not None:
            return self._in_string(text=text, index=index)
        if char in _QUOTES:
            return self._open_string(text=text, index=index, char=char)
        return self._code(index=index, char=char)

    def _in_string(self, *, text: str, index: int) -> int:
        """Advance inside a quoted region.

        Args:
            index (int): Current offset.
            text (str): Interior text.

        Returns:
            int: Characters consumed.

        """
        char: str = text[index]
        if char == "\\":
            return 2
        if self.triple is not None:
            if text.startswith(self.triple, index):
                self.quote = None
                self.triple = None
                return 3
            return 1
        if char == self.quote:
            self.quote = None
        return 1

    def _open_string(self, *, text: str, index: int, char: str) -> int:
        """Open a quoted region, triple when the delimiter repeats.

        Args:
            char (str): Quote character.
            index (int): Current offset.
            text (str): Interior text.

        Returns:
            int: Characters consumed.

        """
        self.quote = char
        if text.startswith(char * 3, index):
            self.triple = char * 3
            return 3
        return 1

    def _code(self, *, index: int, char: str) -> int:
        """Advance outside strings: brackets and separators.

        Args:
            char (str): Current character.
            index (int): Current offset.

        Returns:
            int: Always 1.

        """
        if char in _BRACKETS:
            self.depth += 1
        elif char in _CLOSERS:
            self.depth -= 1
        elif self.depth == 0:
            self._mark(char=char, index=index)
        return 1

    def _mark(self, *, char: str, index: int) -> None:
        """Record the first top-level separator positions.

        Args:
            char (str): Current character.
            index (int): Current offset.

        """
        if char == "!" and self.bang_at < 0:
            self.bang_at = index
        elif char == ":" and self.colon_at < 0:
            self.colon_at = index
        elif char == "=" and self.equals_at < 0:
            self.equals_at = index


def _scan_interior(*, text: str) -> tuple[str, str, str] | None:
    """Split field interior into ``(expr, conv, spec)`` parts.

    Args:
        text (str): Raw text between ``{`` and ``}``.

    Returns:
        tuple[str, str, str] | None:
            ``(expr, conversion, spec)`` where conversion includes the
        leading ``!`` (or is empty) and spec includes the leading ``:``
            (or is empty); ``None`` when the interior is unsafe.

    """
    scanner: _InteriorScanner = _InteriorScanner()
    index: int = 0
    while index < len(text):
        index += scanner.step(text=text, index=index)
    if scanner.depth != 0:
        return None
    conv_at: int = scanner.bang_at
    spec_at: int = scanner.colon_at
    if conv_at >= 0 and spec_at >= 0 and spec_at < conv_at:
        return None
    if conv_at >= 0:
        expr_text: str = text[:conv_at]
        conv_text: str = text[
            conv_at : spec_at if spec_at > conv_at else len(text)
        ]
        spec_text: str = text[spec_at:] if spec_at > conv_at else ""
    elif spec_at >= 0:
        expr_text, conv_text, spec_text = (
            text[:spec_at],
            "",
            text[spec_at:],
        )
    else:
        expr_text, conv_text, spec_text = text, "", ""
    expr: str = expr_text.strip()
    if not expr or _has_debug_equals(text=text, position=scanner.equals_at):
        return None
    conv: str = conv_text.strip()
    if conv:
        body: str = conv[1:].strip()
        if len(body) != 1 or body not in "sra":
            return None
        conv = f"!{body}"
    return expr, conv, spec_text


def _has_debug_equals(*, text: str, position: int) -> bool:
    """Whether the interior carries a top-level ``=`` debug marker.

    Args:
        position (int): Offset of the first top-level ``=`` (-1 when absent).
        text (str): Interior text.

    Returns:
        bool: ``True`` when a bare ``=`` appears outside strings/brackets and
        is not part of ``==``, ``!=``, ``<=``, ``>=`` or ``:=``.

    """
    if position < 0:
        return False
    previous: str = text[position - 1] if position > 0 else ""
    following: str = text[position + 1] if position + 1 < len(text) else ""
    return previous not in "=!<>:" and following != "="


def _normalise_spec(*, spec: str) -> str:
    """Strip whitespace between ``:`` and spec start.

    Args:
        spec (str): Spec text including the leading colon (or empty).

    Returns:
        str: Spec with leading whitespace removed; spec content is
            preserved byte-for-byte.

    """
    return spec.lstrip()


def _normalise_spec_fields(*, spec: str) -> str:
    """Normalise replacement fields nested inside a format spec.

    Args:
        spec (str): Spec text including the leading colon.

    Returns:
        str: Spec with each nested ``{...}`` interior canonicalised;
            literal ``{{``/``}}`` escapes and unparseable fields are
            preserved.

    """
    output: list[str] = []
    index: int = 0
    while index < len(spec):
        pair: str = spec[index : index + 2]
        if pair in ("{{", "}}"):
            output.append(pair)
            index += 2
            continue
        if spec[index] != "{":
            output.append(spec[index])
            index += 1
            continue
        end: int = _match_brace(text=spec, start=index)
        if end < 0:
            output.append(spec[index])
            index += 1
            continue
        interior: str = spec[index + 1 : end]
        parts: tuple[str, str, str] | None = _scan_interior(text=interior)
        if parts is None:
            output.append(spec[index : end + 1])
        else:
            expr, conv, nested = parts
            inner: str = (
                expr
                + conv
                + _normalise_spec_fields(
                    spec=_normalise_spec(spec=nested),
                )
            )
            output.append("{" + inner + "}")
        index = end + 1
    return "".join(output)


def _match_brace(*, text: str, start: int) -> int:
    """Index of the ``}`` matching ``text[start] == '{'``, or -1.

    Args:
        start (int): Position of the opening brace.
        text (str): Source text.

    Returns:
        int: Closing brace index or -1.

    """
    depth: int = 0
    quote: str | None = None
    index: int = start
    while index < len(text):
        char: str = text[index]
        if quote is not None:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in _QUOTES:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _line_offsets(*, source: str) -> list[int]:
    """Absolute offset of each line start.

    Args:
        source (str): Module source.

    Returns:
        list[int]: Offsets list.

    """
    offsets: list[int] = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _field_brace_indices(
    *,
    tokens: list[TokenInfo],
    source: str,
    offsets: list[int],
) -> list[int]:
    """Collect indices of OP ``{`` tokens that open f-string fields.

    Args:
        offsets (list[int]): Line-start offsets.
        source (str): Module source.
        tokens (list[TokenInfo]): Token stream.

    Returns:
        list[int]: Token indices of field-opening braces.

    """

    def to_offset(position: tuple[int, int]) -> int:
        """Convert a ``(line, column)`` pair to a source offset.

        Args:
            position (tuple[int, int]): One-based line and zero-based column.

        Returns:
            int: Absolute offset in the source.

        """
        line, column = position
        return offsets[line - 1] + column

    indices: list[int] = []
    fstring_open: int = 0
    claimed_until: int = -1
    for i, token in enumerate(iterable=tokens):
        if token.type == FSTRING_START:
            fstring_open += 1
        elif token.type == FSTRING_END:
            fstring_open = max(0, fstring_open - 1)
        elif (
            fstring_open > 0
            and token.type == OP
            and token.string == "{"
            and to_offset(position=token.start) > claimed_until
        ):
            brace_end: int = _match_brace(
                text=source,
                start=to_offset(position=token.start),
            )
            if brace_end < 0:
                continue
            indices.append(i)
            claimed_until = brace_end
    return indices


def _rewrite_field(
    *,
    report: FStringReport,
    source: str,
    token: TokenInfo,
    offsets: list[int],
) -> tuple[int, int, str] | None:
    """Compute the canonical replacement for one field.

    Args:
        offsets (list[int]): Line-start offsets.
        report (FStringReport): Report to record skips/changes on.
        source (str): Module source.
        token (TokenInfo): The field's opening ``{`` token.

    Returns:
        tuple[int, int, str] | None: ``(start, end, replacement)`` or ``None``.

    """

    def to_offset(position: tuple[int, int]) -> int:
        """Convert a ``(line, column)`` pair to a source offset.

        Args:
            position (tuple[int, int]): One-based line and zero-based column.

        Returns:
            int: Absolute offset in the source.

        """
        line, column = position
        return offsets[line - 1] + column

    brace_end: int = _match_brace(
        text=source,
        start=to_offset(position=token.start),
    )
    interior: str = source[to_offset(position=token.end) : brace_end]
    parts: tuple[str, str, str] | None = _scan_interior(text=interior)
    if parts is None:
        report.skipped["unsafe-field"] = (
            report.skipped.get("unsafe-field", 0) + 1
        )
        return None
    expr, conv, spec = parts
    canonical: str = (
        expr + conv + _normalise_spec_fields(spec=_normalise_spec(spec=spec))
    )
    if canonical == interior:
        return None
    report.changes.append(FStringChange(kind="interior", line=token.start[0]))
    return to_offset(position=token.end), brace_end, canonical


def normalize_fstrings(*, source: str) -> FStringReport:
    """Normalise replacement-field interiors in ``source``.

    Args:
        source (str): Python module source.

    Returns:
        FStringReport: Report with rewritten output and evidence.

    """
    report: FStringReport = FStringReport(output=source)
    try:
        tokens: list[TokenInfo] = list(
            generate_tokens(readline=StringIO(initial_value=source).readline),
        )
    except (TokenError, IndentationError, SyntaxError):
        report.skipped["tokenize"] = 1
        return report
    offsets: list[int] = _line_offsets(source=source)
    edits: list[tuple[int, int, str]] = []
    for i in _field_brace_indices(
        tokens=tokens,
        source=source,
        offsets=offsets,
    ):
        edit: tuple[int, int, str] | None = _rewrite_field(
            report=report,
            source=source,
            token=tokens[i],
            offsets=offsets,
        )
        if edit is not None:
            edits.append(edit)
    edits.sort(key=lambda item: item[0], reverse=True)
    output: str = source
    for start, finish, new in edits:
        output = output[:start] + new + output[finish:]
    report.output = output
    return report
