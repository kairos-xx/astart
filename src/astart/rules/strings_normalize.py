r"""String literal normalisation fixer (standalone, M8-24).

``normalize_strings`` rewrites plain single-line string constants:

- literals containing ``\\n`` escapes become triple-quoted strings with
  real newlines when the result cannot contain the closing delimiter;
- literals that overflow the line budget become parenthesised implicit
  concatenations split at whitespace boundaries.

f-strings, bytes, raw strings, triple-quoted strings, docstrings,
dict keys, ``__all__`` members, match patterns and strings already part
of an implicit concatenation are refused.  Catalog/applier wiring is
deferred (M8-22).
"""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Dict,
    Expr,
    FormattedValue,
    FunctionDef,
    JoinedStr,
    Lambda,
    Match,
    Module,
    Name,
    iter_child_nodes,
    literal_eval,
    parse,
    stmt,
    walk,
)
from dataclasses import dataclass, field
from typing import Final, final


@final
@dataclass(frozen=True, slots=True)
class StringChange:
    """One applied literal rewrite.

    Attributes:
        kind: ``"triple"`` or ``"split"``.
        line: 1-based line of the original literal.
        reason: Why the rewrite was applied.

    """

    kind: str
    line: int
    reason: str


@final
@dataclass(slots=True)
class StringReport:
    """Outcome of a normalisation pass.

    Attributes:
        changes: Applied rewrites, in source order.
        output: Rewritten source.
        skipped: Refusal reason to count.

    """

    changes: list[StringChange] = field(default_factory=list)
    output: str = ""
    skipped: dict[str, int] = field(default_factory=dict)


_SIMPLE_ESCAPES: Final[dict[int, str]] = {
    0x07: "\\a",
    0x08: "\\b",
    0x0B: "\\v",
    0x0C: "\\f",
}

_PRINTABLE_MIN: Final[int] = 0x20
_PRINTABLE_MAX: Final[int] = 0x7F
_NON_ASCII_MIN: Final[int] = 0xA0
_BYTE_MAX: Final[int] = 0x100
_BMP_MAX: Final[int] = 0x10000
_MIN_SPLIT_WORDS: Final[int] = 2


_NAMED_ESCAPES: Final[dict[str, str]] = {
    "\\": "\\\\",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
}


def _escape_char(*, char: str, code: int, quote: str) -> str:
    """Render one character as literal-body source.

    Args:
        char: The character to escape.
        code: Its Unicode code point.
        quote: The quote delimiter to escape against.

    Returns:
        The escaped source text for the character.

    """
    if char == quote:
        return "\\" + quote
    named: str | None = _NAMED_ESCAPES.get(char) or _SIMPLE_ESCAPES.get(code)
    if named is not None:
        return named
    if _PRINTABLE_MIN <= code < _PRINTABLE_MAX or code >= _NON_ASCII_MIN:
        return char
    if code < _BYTE_MAX:
        return f"\\x{code:02x}"
    if code < _BMP_MAX:
        return f"\\u{code:04x}"
    return f"\\U{code:08x}"


def _quote_piece(*, text: str, quote: str) -> str | None:
    """Render ``text`` as a single-quoted literal body.

    Args:
        quote: ``'`` or ``"`` delimiter to escape against.
        text: Decoded string value.

    Returns:
        Escaped body without delimiters.

    """
    return "".join(
        _escape_char(char=char, code=ord(char), quote=quote) for char in text
    )


def _literal_parts(*, segment: str) -> tuple[str, str, str] | None:
    """Split a literal segment into ``(prefix, quote, body)``.

    Args:
        segment: Exact source text of the string token.

    Returns:
        Parts, or ``None`` for non-plain literals (f/r/b prefixes,
        triple quotes).

    """
    index: int = 0
    prefix: str = ""
    while index < len(segment) and segment[index] in "rRbBfFuU":
        prefix += segment[index]
        index += 1
    if prefix and prefix.lower() not in ("u",):
        return None
    if segment.startswith(('"""', "'''"), index):
        return None
    quote: str = segment[index : index + 1]
    if quote not in ("'", '"') or not segment.endswith(quote):
        return None
    return prefix, quote, segment[index + 1 : -1]


def _triple_body(*, body: str) -> str | None:
    r"""Convert ``\\n`` escapes in ``body`` to real newlines.

    Args:
        body: Literal body source text.

    Returns:
        New body for a triple-quoted literal, or ``None`` when unsafe.

    """
    out: list[str] = []
    index: int = 0
    while index < len(body):
        char: str = body[index]
        if char == "\\" and index + 1 < len(body):
            nxt: str = body[index + 1]
            if nxt == "n":
                out.append("\n")
            else:
                out.append(char + nxt)
            index += 2
            continue
        out.append(char)
        index += 1
    text: str = "".join(out)
    if text.endswith("\\") or '"""' in text or "'''" in text:
        return None
    return text


def _triple_literal(*, body: str) -> str | None:
    """Render ``body`` as a triple-quoted literal.

    Args:
        body: Converted body from :func:`_triple_body`.

    Returns:
        Replacement text or ``None``.

    """
    quote: str = '"""' if '"""' not in body else "'''"
    if quote in body:
        return None
    return f"{quote}{body}{quote}"


def _docstring_lines(*, tree: AST) -> set[int]:
    """Line numbers of docstring constants.

    Args:
        tree: Parsed module.

    Returns:
        First lines of every docstring expression.

    """
    lines: set[int] = set()
    for node in walk(node=tree):
        for field_name in ("body", "orelse", "finalbody"):
            child: None | list[stmt] | AST = getattr(node, field_name, None)
            if not (isinstance(child, list) and child):
                continue
            first: stmt = child[0]
            if (
                isinstance(first, Expr)
                and isinstance(first.value, Constant)
                and isinstance(first.value.value, str)
            ):
                lines.add(first.value.lineno)
    return lines


def _parents(*, tree: AST) -> dict[int, AST]:
    """Map each node id to its parent node.

    Args:
        tree: Parsed module.

    Returns:
        Node id to parent.

    """
    result: dict[int, AST] = {}
    for node in walk(node=tree):
        for child in iter_child_nodes(node=node):
            result[id(child)] = node
    return result


_BOUNDARY_NODES: Final[tuple[type, ...]] = (
    Module,
    FunctionDef,
    AsyncFunctionDef,
    ClassDef,
    Lambda,
)


def _contextual_skip(
    *,
    node: AST,
    parents: dict[int, AST],
) -> str | None:
    """Refusal reason from enclosing context, or ``None``.

    Args:
        node: The string constant.
        parents: Node id to parent map.

    Returns:
        Skip reason or ``None``.

    """
    cursor: AST = node
    while True:
        holder: AST | None = parents.get(id(cursor))
        if isinstance(holder, Match):
            return "match-pattern"
        if isinstance(holder, Assign):
            for target in holder.targets:
                if isinstance(target, Name) and target.id == "__all__":
                    return "all-members"
            break
        if holder is None or isinstance(holder, _BOUNDARY_NODES):
            break
        cursor = holder
    return None


def _eligible(
    *,
    node: Constant,
    parents: dict[int, AST],
) -> str | None:
    """Refusal reason for a string constant, or ``None`` when eligible.

    Args:
        node: The constant.
        parents: Node id to parent map.

    Returns:
        Skip reason or ``None``.

    """
    if not isinstance(node.value, str):
        return "bytes"
    parent: AST | None = parents.get(id(node))
    if isinstance(parent, (JoinedStr, FormattedValue)):
        return "fstring-part"
    if isinstance(parent, Dict) and any(key is node for key in parent.keys):
        return "dict-key"
    return _contextual_skip(node=node, parents=parents)


def _literal_chunks(
    *,
    value: str,
    quote: str,
    budget: int,
) -> list[str] | None:
    """Split ``value`` into whitespace-boundary chunks fitting ``budget``.

    Args:
        value: Decoded string value.
        quote: Quote delimiter in use.
        budget: Maximum characters per chunk.

    Returns:
        Chunk texts, or ``None`` when the value cannot be split safely.

    """
    words: list[str] = value.split(sep=" ")
    if len(words) < _MIN_SPLIT_WORDS or any(word == "" for word in words):
        # Repeated spaces would collapse; refuse to alter the value.
        return None
    chunks: list[str] = []
    current: str = ""
    for word in words:
        candidate: str = word if not current else f"{current} {word}"
        piece: str | None = _quote_piece(text=candidate, quote=quote)
        if piece is not None and len(piece) + 2 <= budget:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = word
    if current:
        chunks.append(current)
    if len(chunks) <= 1:
        return None
    # Implicit concatenation inserts no space: keep each boundary space
    # as a trailing space inside its chunk's quotes.
    return [f"{chunk} " for chunk in chunks[:-1]] + chunks[-1:]


def _split_literal(
    *,
    segment: str,
    indent: str,
    line_length: int,
    quote: str,
) -> str | None:
    """Render an overlong literal as a parenthesised concatenation.

    Args:
        indent: Leading whitespace of the literal's line.
        line_length: Maximum emitted line width.
        quote: Quote character to reuse.
        segment: Exact literal source.

    Returns:
        Replacement text, or ``None`` when splitting is unsafe.

    """
    parts: tuple[str, str, str] | None = _literal_parts(segment=segment)
    if parts is None:
        return None
    try:
        value: str | bytes = literal_eval(node_or_string=segment)
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, str):
        return None
    budget: int = line_length - len(indent) - 8
    chunks: list[str] | None = _literal_chunks(
        value=value,
        quote=quote,
        budget=budget,
    )
    if chunks is None:
        return None
    inner_indent: str = f"{indent}    "
    lines: list[str] = ["("]
    for chunk in chunks:
        piece: str | None = _quote_piece(text=chunk, quote=quote)
        if piece is None:
            return None
        lines.append(f"{inner_indent}{quote}{piece}{quote}")
    lines.append(f"{indent})")
    return "\n".join(lines)


@final
@dataclass(frozen=True, slots=True)
class _LiteralContext:
    """Resolved source context for one eligible string constant.

    Attributes:
        body: Literal body text without quotes.
        end: End offset of the literal in the source.
        indent: Leading whitespace of the literal's line.
        line_text: Full text of the literal's line.
        quote: Quote delimiter character.
        segment: Full literal segment including quotes.
        start: Start offset of the literal in the source.

    """

    body: str
    end: int
    indent: str
    line_text: str
    quote: str
    segment: str
    start: int


@final
@dataclass(frozen=True, slots=True)
class _NodeRewrite:
    """Outcome of the transform attempts for one literal.

    Attributes:
        kind: Rewrite kind applied, or ``None``.
        reason: Reason the rewrite was chosen.
        replacement: Replacement source text, or ``None``.
        skips: Reasons the attempts were refused.

    """

    kind: str | None = None
    reason: str | None = None
    replacement: str | None = None
    skips: tuple[str, ...] = ()


def _rewrite_literal(
    *,
    ctx: _LiteralContext,
    line_length: int,
) -> _NodeRewrite:
    """Try the triple-quote then split rewrites for one literal.

    Args:
        ctx: Resolved literal context.
        line_length: Maximum allowed line length.

    Returns:
        The rewrite outcome.

    """
    skips: list[str] = []
    replacement: str | None = None
    kind: str | None = None
    reason: str | None = None
    if "\\n" in ctx.body:
        replacement = _triple_rewrite(body=ctx.body)
        if replacement is None:
            skips.append("unsafe-triple")
        else:
            kind, reason = "triple", "escaped-newline"
    if (
        replacement is None
        and len(ctx.line_text) > line_length
        and len(ctx.segment) > line_length // 2
    ):
        split: str | None = _split_literal(
            segment=ctx.segment,
            indent=ctx.indent,
            line_length=line_length,
            quote=ctx.quote,
        )
        if split is None:
            skips.append("unsplittable")
        else:
            replacement, kind, reason = split, "split", "overlong"
    return _NodeRewrite(
        kind=kind,
        reason=reason,
        replacement=replacement,
        skips=tuple(skips),
    )


def _triple_rewrite(*, body: str) -> str | None:
    r"""Triple-quote rewrite for a body containing ``\\n`` escapes.

    Args:
        body: Literal body text.

    Returns:
        Replacement literal source, or ``None`` when unsafe.

    """
    new_body: str | None = _triple_body(body=body)
    if new_body is None:
        return None
    return _triple_literal(body=new_body)


def _literal_context(
    *,
    node: Constant,
    source: str,
    source_lines: list[str],
    offsets: list[int],
    parents: dict[int, AST],
) -> _LiteralContext | str:
    """Resolve a node's literal context, or return a skip reason.

    Args:
        node: The string constant.
        source: Full module source.
        source_lines: Source split into lines.
        offsets: Line start offsets.
        parents: Node id to parent map.

    Returns:
        The literal context, or a skip reason string.

    """
    reason: str | None = _eligible(node=node, parents=parents)
    if reason is not None:
        return reason
    if node.end_lineno is None or node.end_col_offset is None:
        return "no-span"
    start: int = offsets[node.lineno - 1] + node.col_offset
    end: int = offsets[node.end_lineno - 1] + node.end_col_offset
    segment: str = source[start:end]
    parts: tuple[str, str, str] | None = _literal_parts(segment=segment)
    if parts is None:
        return "non-plain"
    _prefix, quote, body = parts
    line_text: str = source_lines[node.lineno - 1].rstrip("\n")
    indent: str = line_text[: len(line_text) - len(line_text.lstrip())]
    return _LiteralContext(
        body=body,
        end=end,
        indent=indent,
        line_text=line_text,
        quote=quote,
        segment=segment,
        start=start,
    )


def normalize_strings(
    *,
    source: str,
    line_length: int = 88,
) -> StringReport:
    """Normalise eligible plain string literals in ``source``.

    Args:
        line_length: Maximum emitted line width for splits.
        source: Python module source.

    Returns:
        Report with rewritten output and per-change evidence.

    """
    report: StringReport = StringReport(output=source)
    try:
        tree: Module = parse(source=source)
    except SyntaxError:
        report.skipped["parse"] = 1
        return report
    docstrings: set[int] = _docstring_lines(tree=tree)
    parents: dict[int, AST] = _parents(tree=tree)
    source_lines: list[str] = source.splitlines(keepends=True)
    offsets: list[int] = [0]
    for line in source_lines:
        offsets.append(offsets[-1] + len(line))
    edits: list[tuple[int, int, str]] = []
    for node in walk(node=tree):
        if not (
            isinstance(node, Constant)
            and isinstance(node.value, str)
            and node.lineno not in docstrings
        ):
            continue
        ctx: _LiteralContext | str = _literal_context(
            node=node,
            source=source,
            source_lines=source_lines,
            offsets=offsets,
            parents=parents,
        )
        if isinstance(ctx, str):
            report.skipped[ctx] = report.skipped.get(ctx, 0) + 1
            continue
        outcome: _NodeRewrite = _rewrite_literal(
            ctx=ctx,
            line_length=line_length,
        )
        for skip_reason in outcome.skips:
            report.skipped[skip_reason] = (
                report.skipped.get(skip_reason, 0) + 1
            )
        if (
            outcome.replacement is None
            or outcome.kind is None
            or outcome.reason is None
        ):
            continue
        edits.append((ctx.start, ctx.end, outcome.replacement))
        report.changes.append(
            StringChange(
                kind=outcome.kind,
                line=node.lineno,
                reason=outcome.reason,
            ),
        )
    edits.sort(key=lambda item: item[0], reverse=True)
    output: str = source
    for start, end, new in edits:
        output = output[:start] + new + output[end:]
    report.output = output
    return report
