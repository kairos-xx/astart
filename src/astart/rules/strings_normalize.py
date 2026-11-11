r"""String literal normalisation fixer (M8-24, wired by WSP003).

``normalize_strings`` rewrites single-line string constants:

- literals containing ``\n`` escapes become triple-quoted strings with
  real newlines when the result cannot contain the closing delimiter;
- literals and f-strings that overflow the line budget become
  parenthesised implicit concatenations split at atom boundaries.

f-string pieces keep their ``{...}`` fields verbatim; bytes, raw strings,
triple-quoted strings, docstrings, dict keys, ``__all__`` members, match
patterns, multi-line f-strings and strings already part of an implicit
concatenation are refused.

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
from typing import TYPE_CHECKING, Final, final

type ListStr = list[str]

if TYPE_CHECKING:
    from collections.abc import Callable


@final
@dataclass(frozen=True, slots=True)
class StringChange:
    """One applied literal rewrite.

    Attributes:
        kind (str): ``"triple"``, ``"split"`` or ``"collapse"``.
        line (int): 1-based line of the original literal.
        reason (str): Why the rewrite was applied.

    """

    kind: str
    line: int
    reason: str


@final
@dataclass(slots=True)
class StringReport:
    """Outcome of a normalisation pass.

    Attributes:
        changes (list[StringChange]): Applied rewrites, in source order.
        output (str): Rewritten source.
        skipped (dict[str, int]): Refusal reason to count.

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
    "\n": """\
\\n""",
    "\t": "\\t",
    "\r": "\\r",
}


def _escape_char(*, char: str, code: int, quote: str) -> str:
    """Render one character as literal-body source.

    Args:
        char (str): The character to escape.
        code (int): Its Unicode code point.
        quote (str): The quote delimiter to escape against.

    Returns:
        str: The escaped source text for the character.

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
        quote (str): ``'`` or ``"`` delimiter to escape against.
        text (str): Decoded string value.

    Returns:
        str | None: Escaped body without delimiters.

    """
    return "".join(
        _escape_char(char=char, code=ord(char), quote=quote) for char in text
    )


def _literal_parts(*, segment: str) -> tuple[str, str, str] | None:
    """Split a literal segment into ``(prefix, quote, body)``.

    Args:
        segment (str): Exact source text of the string token.

    Returns:
        tuple[str, str, str] | None: Parts, or ``None`` for non-plain
            literals (f/r/b prefixes, triple quotes).

    """
    index: int = 0
    prefix: str = ""
    while index < len(segment) and segment[index] in "rRbBfFuU":
        prefix += segment[index]
        index += 1
    if prefix and prefix.lower() != "u":
        return None
    if segment.startswith(('"""', "'''"), index):
        return None
    quote: str = segment[index : index + 1]
    if quote not in ("'", '"') or not segment.endswith(quote):
        return None
    body: str = segment[index + 1 : -1]
    cursor: int = 0
    while cursor < len(body):
        if body[cursor] == "\\":
            cursor += 2
            continue
        if body[cursor] == quote:
            return None
        cursor += 1
    return prefix, quote, body


def _triple_body(*, body: str) -> str | None:
    r"""Convert ``\n`` escapes in ``body`` to real newlines.

    Args:
        body (str): Literal body source text.

    Returns:
        str | None:
            New body for a triple-quoted literal, or ``None`` when unsafe.

    """
    out: ListStr = []
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
    if not text.strip() or any(
        line != line.rstrip() for line in text.split(sep="\n")
    ):
        return None
    return text


def _triple_literal(*, body: str) -> str | None:
    """Render ``body`` as a triple-quoted literal.

    The opening delimiter sits on the original line followed by a
    backslash-newline, so content lines stay dedented to column zero and
    the closing delimiter lands after the body's own last line. A
    delimiter that would collide with a quote at the body's end is
    swapped for the other triple quote.

    Args:
        body (str): Converted body from :func:`_triple_body`.

    Returns:
        str | None: Replacement text or ``None``.

    """
    quote: str = '"""'
    if '"""' in body or body.endswith('"'):
        quote = "'''"
    if "'''" in body or (quote == "'''" and body.endswith("'")):
        return None
    return f"{quote}\\\n{body}{quote}"


def _docstring_lines(*, tree: AST) -> set[int]:
    """Line numbers of docstring constants.

    Args:
        tree (AST): Parsed module.

    Returns:
        set[int]: First lines of every docstring expression.

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
        tree (AST): Parsed module.

    Returns:
        dict[int, AST]: Node id to parent.

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
        node (AST): The string constant.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        str | None: Skip reason or ``None``.

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
        node (Constant): The constant.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        str | None: Skip reason or ``None``.

    """
    if not isinstance(node.value, str):
        return "bytes"
    parent: AST | None = parents.get(id(node))
    if isinstance(parent, (JoinedStr, FormattedValue)):
        return "fstring-part"
    if isinstance(parent, Dict) and any(key is node for key in parent.keys):
        return "dict-key"
    return _contextual_skip(node=node, parents=parents)


def _fstring_eligible(
    *,
    node: JoinedStr,
    parents: dict[int, AST],
) -> str | None:
    """Refusal reason for an f-string, or ``None`` when eligible.

    Args:
        node (JoinedStr): The joined-string node.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        str | None: Skip reason or ``None``.

    """
    parent: AST | None = parents.get(id(node))
    if isinstance(parent, (JoinedStr, FormattedValue)):
        return "fstring-part"
    if isinstance(parent, Dict) and any(key is node for key in parent.keys):
        return "dict-key"
    return _contextual_skip(node=node, parents=parents)


def _fstring_atoms(
    *,
    node: JoinedStr,
    source: str,
    offsets: list[int],
) -> tuple[tuple[str, str], ...] | None:
    """Collect ``(kind, text)`` atoms of an f-string in order.

    Args:
        node (JoinedStr): The joined-string node.
        source (str): Full module source.
        offsets (list[int]): Line start offsets.

    Returns:
        tuple[tuple[str, str], ...] | None:
            ``("lit", decoded)`` literal and ``("field", "{...}")``
            verbatim atoms, or ``None`` for unexpected value shapes.

    """
    atoms: list[tuple[str, str]] = []
    for value in node.values:
        if isinstance(value, Constant):
            if not isinstance(value.value, str):
                return None
            atoms.append(("lit", value.value))
        elif isinstance(value, FormattedValue):
            if value.end_lineno is None or value.end_col_offset is None:
                return None
            start: int = offsets[value.lineno - 1] + value.col_offset
            end: int = offsets[value.end_lineno - 1] + value.end_col_offset
            atoms.append(("field", source[start:end]))
        else:
            return None
    return tuple(atoms)


def _fstring_body(*, text: str, quote: str) -> str:
    """Render decoded literal ``text`` as an f-string body fragment.

    Braces are doubled for the f-string and the quote/backslashes escaped
    for ``quote``.

    Args:
        quote (str): ``'`` or ``"`` delimiter to escape against.
        text (str): Decoded literal text.

    Returns:
        str: Escaped body fragment without quotes.

    """
    doubled: str = text.replace("{", "{{").replace("}", "}}")
    return _quote_piece(text=doubled, quote=quote) or ""


def _pack_words(
    *,
    words: ListStr,
    fits: Callable[[list[str]], bool],
) -> list[ListStr]:
    """Pack words greedily, then repair a one-word final line.

    A trailing single word reads as a widow; when the previous line can
    spare its last word and the widened final line still fits, the word
    moves down so the last line carries at least two words.

    Args:
        words (ListStr): Words in source order.
        fits (Callable[[list[str]], bool]): Whether a word group still fits
            the width budget.

    Returns:
        list[ListStr]: Word groups, one per emitted line.

    """
    lines: list[ListStr] = []
    current: ListStr = []
    for word in words:
        if current and not fits([*current, word]):
            lines.append(current)
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(current)
    if len(lines) > 1 and len(lines[-1]) == 1 and len(lines[-2]) > 1:
        moved: ListStr = [lines[-2][-1], *lines[-1]]
        if fits(moved):
            lines[-2].pop()
            lines[-1] = moved
    return lines


def _fstring_literal_chunks(
    *,
    text: str,
    quote: str,
    budget: int,
) -> ListStr | None:
    """Split literal ``text`` into word chunks whose bodies fit ``budget``.

    Edge spaces — common around ``{...}`` fields — are glued to the
    boundary chunks so concatenation preserves the value.

    Args:
        budget (int): Maximum escaped body length per chunk.
        quote (str): Quote delimiter used for the size probe.
        text (str): Decoded literal text.

    Returns:
        ListStr | None:
            Chunk texts with boundary spaces preserved, or ``None``.

    """
    leading: str = text[: len(text) - len(text.lstrip(" "))]
    trailing: str = text[len(text.rstrip(" ")) :]
    core: str = text[len(leading) : len(text) - len(trailing)]
    words: ListStr = core.split(sep=" ")
    if len(words) < _MIN_SPLIT_WORDS or any(word == "" for word in words):
        return None

    def fits(group: ListStr) -> bool:
        """Describe fits.

        Args:
            group (ListStr): TODO.

        Returns:
            bool: TODO.

        """
        return len(_fstring_body(text=" ".join(group), quote=quote)) <= budget

    groups: list[ListStr] = _pack_words(words=words, fits=fits)
    if len(groups) <= 1:
        return None
    chunks: ListStr = [" ".join(group) for group in groups]
    result: ListStr = [f"{chunk} " for chunk in chunks[:-1]] + chunks[-1:]
    result[0] = f"{leading}{result[0]}"
    result[-1] = f"{result[-1]}{trailing}"
    return result


@final
@dataclass(frozen=True, slots=True)
class _FStringContext:
    """Resolved source context for one eligible f-string.

    Attributes:
        atoms (tuple[tuple[str, str], ...]): ``(kind, text)`` pieces in source
            order.
        end (int): End offset of the f-string in the source.
        indent (str): Leading whitespace of the f-string's line.
        line_text (str): Full text of the f-string's line.
        start (int): Start offset of the f-string in the source.
        trailing (str): Source text after the f-string on its line.

    """

    atoms: tuple[tuple[str, str], ...]
    end: int
    indent: str
    line_text: str
    start: int
    trailing: str


def _fstring_context(
    *,
    node: JoinedStr,
    source: str,
    source_lines: ListStr,
    offsets: list[int],
    parents: dict[int, AST],
) -> _FStringContext | str:
    """Resolve an f-string's rewrite context, or return a skip reason.

    Args:
        node (JoinedStr): The joined-string node.
        source (str): Full module source.
        source_lines (ListStr): Source split into lines.
        offsets (list[int]): Line start offsets.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        _FStringContext | str: The f-string context, or a skip reason string.

    """
    reason: str | None = _fstring_eligible(node=node, parents=parents)
    if reason is not None:
        return reason
    if (
        node.end_lineno is None
        or node.end_col_offset is None
        or node.end_lineno != node.lineno
    ):
        return "multiline"
    start: int = offsets[node.lineno - 1] + node.col_offset
    end: int = offsets[node.end_lineno - 1] + node.end_col_offset
    segment: str = source[start:end]
    index: int = 0
    prefix: str = ""
    while index < len(segment) and segment[index] in "rRbBfFuU":
        prefix += segment[index]
        index += 1
    lowered: str = prefix.lower()
    if (
        "f" not in lowered
        or "r" in lowered
        or "b" in lowered
        or "u" in lowered
    ):
        return "non-plain"
    atoms: tuple[tuple[str, str], ...] | None = _fstring_atoms(
        node=node,
        source=source,
        offsets=offsets,
    )
    if atoms is None:
        return "non-plain"
    line_text: str = source_lines[node.lineno - 1].rstrip("\n")
    indent: str = line_text[: len(line_text) - len(line_text.lstrip())]
    return _FStringContext(
        atoms=atoms,
        end=end,
        indent=indent,
        line_text=line_text,
        start=start,
        trailing=line_text[node.end_col_offset :],
    )


def _rewrite_fstring(
    *,
    ctx: _FStringContext,
    line_length: int,
) -> _NodeRewrite:
    """Split an overlong f-string into parenthesised ``f"..."`` pieces.

    Args:
        ctx (_FStringContext): Resolved f-string context.
        line_length (int): Maximum emitted line width.

    Returns:
        _NodeRewrite: The rewrite outcome.

    """
    if len(ctx.line_text) <= line_length:
        return _NodeRewrite()

    min_budget: int = 8
    budget: int = line_length - len(ctx.indent) - min_budget
    if budget < min_budget:
        return _NodeRewrite(skips=("unsplittable",))

    expanded: list[tuple[str, str]] = []
    for kind, text in ctx.atoms:
        chunks: ListStr | None = (
            _fstring_literal_chunks(
                text=text,
                quote='"',
                budget=budget,
            )
            if kind != "field"
            and len(_fstring_body(text=text, quote='"')) > budget
            else [text]
        )
        if chunks is None:
            return _NodeRewrite(skips=("unsplittable",))
        expanded.extend((kind, chunk) for chunk in chunks)

    pieces: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    current_len: int = 0

    for kind, text in expanded:
        cost: int = (
            len(text)
            if kind == "field"
            else len(_fstring_body(text=text, quote='"'))
        )
        if current and current_len + cost > budget:
            pieces.append(current)
            current = []
            current_len = 0
        current.append((kind, text))
        current_len += cost

    pieces.extend([current] if current else [])

    inner_indent: str = f"{ctx.indent}    "
    lines: ListStr = ["("]
    reason: str | None = None

    for piece in pieces:
        fields: ListStr = [text for kind, text in piece if kind == "field"]
        quote: str | None = next(
            (
                candidate
                for candidate in ('"', "'")
                if all(candidate not in field for field in fields)
            ),
            None,
        )
        if quote is None:
            reason = "unquotable"
            break

        body: str = "".join(
            text if kind == "field" else _fstring_body(text=text, quote=quote)
            for kind, text in piece
        )
        line: str = f"{inner_indent}f{quote}{body}{quote}"
        if len(line) > line_length:
            reason = "unsplittable"
            break
        lines.append(line)

    reason = (
        "unsplittable"
        if reason is None and len(f"{ctx.indent}){ctx.trailing}") > line_length
        else reason
    )
    lines.append(f"{ctx.indent})")

    return (
        _NodeRewrite(skips=(reason,))
        if reason is not None
        else _NodeRewrite(
            kind="split",
            reason="overlong",
            replacement="\n".join(lines),
        )
    )


def _literal_chunks(
    *,
    value: str,
    quote: str,
    budget: int,
) -> ListStr | None:
    """Split ``value`` into whitespace-boundary chunks fitting ``budget``.

    Args:
        value (str): Decoded string value.
        quote (str): Quote delimiter in use.
        budget (int): Maximum characters per chunk.

    Returns:
        ListStr | None:
            Chunk texts, or ``None`` when the value cannot be split safely.

    """
    words: ListStr = value.split(sep=" ")
    if len(words) < _MIN_SPLIT_WORDS or any(word == "" for word in words):
        # Repeated spaces would collapse; refuse to alter the value.
        return None

    def fits(group: ListStr) -> bool:
        """Describe fits.

        Args:
            group (ListStr): TODO.

        Returns:
            bool: TODO.

        """
        piece: str | None = _quote_piece(text=" ".join(group), quote=quote)
        return piece is not None and len(piece) + 2 <= budget

    groups: list[ListStr] = _pack_words(words=words, fits=fits)
    if len(groups) <= 1:
        return None
    chunks: ListStr = [" ".join(group) for group in groups]
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
        indent (str): Leading whitespace of the literal's line.
        line_length (int): Maximum emitted line width.
        quote (str): Quote character to reuse.
        segment (str): Exact literal source.

    Returns:
        str | None: Replacement text, or ``None`` when splitting is unsafe.

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
    chunks: ListStr | None = _literal_chunks(
        value=value,
        quote=quote,
        budget=budget,
    )
    if chunks is None:
        # Wrap-only fallback: surrounding code pushed the line over budget
        # while the literal itself fits on its own line.
        piece: str | None = _quote_piece(text=value, quote=quote)
        if piece is None or len(piece) + 2 > budget:
            return None
        chunks = [value]
    inner_indent: str = f"{indent}    "
    lines: ListStr = ["("]
    for chunk in chunks:
        piece = _quote_piece(text=chunk, quote=quote)
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
        body (str): Literal body text without quotes.
        end (int): End offset of the literal in the source.
        indent (str): Leading whitespace of the literal's line.
        line_text (str): Full text of the literal's line.
        quote (str): Quote delimiter character.
        segment (str): Full literal segment including quotes.
        start (int): Start offset of the literal in the source.

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
        kind (str | None): Rewrite kind applied, or ``None``.
        reason (str | None): Reason the rewrite was chosen.
        replacement (str | None): Replacement source text, or ``None``.
        skips (tuple[str, ...]): Reasons the attempts were refused.

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
        ctx (_LiteralContext): Resolved literal context.
        line_length (int): Maximum allowed line length.

    Returns:
        _NodeRewrite: The rewrite outcome.

    """
    skips: ListStr = []
    replacement: str | None = None
    kind: str | None = None
    reason: str | None = None
    if (
        """\
\\n"""
        in ctx.body
    ):
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
    r"""Triple-quote rewrite for a body containing ``\n`` escapes.

    Args:
        body (str): Literal body text.

    Returns:
        str | None: Replacement literal source, or ``None`` when unsafe.

    """
    new_body: str | None = _triple_body(body=body)
    if new_body is None:
        return None
    return _triple_literal(body=new_body)


def _literal_context(
    *,
    node: Constant,
    source: str,
    source_lines: ListStr,
    offsets: list[int],
    parents: dict[int, AST],
) -> _LiteralContext | str:
    """Resolve a node's literal context, or return a skip reason.

    Args:
        node (Constant): The string constant.
        source (str): Full module source.
        source_lines (ListStr): Source split into lines.
        offsets (list[int]): Line start offsets.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        _LiteralContext | str: The literal context, or a skip reason string.

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


def _collapse_newlines(
    *,
    node: Constant,
    source: str,
    offsets: list[int],
    parents: dict[int, AST],
) -> tuple[int, int, str] | None:
    """Collapse a whitespace-only triple literal back to escape form.

    Args:
        node (Constant): The string constant.
        source (str): Full module source.
        offsets (list[int]): Line start offsets.
        parents (dict[int, AST]): Node id to parent map.

    Returns:
        tuple[int, int, str] | None:
            ``(start, end, replacement)`` edit, or ``None`` when the literal
            is not a collapse candidate.

    """
    value: object = node.value
    if not isinstance(value, str) or not value or set(value) != {"\n"}:
        return None
    if _eligible(node=node, parents=parents) is not None:
        return None
    if node.end_lineno is None or node.end_col_offset is None:
        return None
    start: int = offsets[node.lineno - 1] + node.col_offset
    end: int = offsets[node.end_lineno - 1] + node.end_col_offset
    segment: str = source[start:end]
    body: str = segment.lstrip("rRbBuUfF")
    if not body.startswith(('"""', "'''")):
        return None
    return (
        start,
        end,
        f'"{
            """\
\\n"""
            * len(value)
        }"',
    )


def _collect(
    *,
    report: StringReport,
    edits: list[tuple[int, int, str]],
    context: _LiteralContext | _FStringContext,
    line: int,
    outcome: _NodeRewrite,
) -> None:
    """Record skip reasons and the edit for one rewrite outcome.

    Args:
        report (StringReport): Report being filled.
        edits (list[tuple[int, int, str]]): Pending source edits.
        context (_LiteralContext | _FStringContext): The literal or f-string
            context.
        line (int): 1-based line of the original literal.
        outcome (_NodeRewrite): The rewrite outcome.

    """
    start: int = context.start
    end: int = context.end
    for skip_reason in outcome.skips:
        report.skipped[skip_reason] = report.skipped.get(skip_reason, 0) + 1
    if (
        outcome.replacement is None
        or outcome.kind is None
        or outcome.reason is None
    ):
        return
    edits.append((start, end, outcome.replacement))
    report.changes.append(
        StringChange(
            kind=outcome.kind,
            line=line,
            reason=outcome.reason,
        ),
    )


def normalize_strings(
    *,
    source: str,
    line_length: int = 88,
) -> StringReport:
    """Normalise eligible string literals and f-strings in ``source``.

    Args:
        line_length (int): Maximum emitted line width for splits.
        source (str): Python module source.

    Returns:
        StringReport: Report with rewritten output and per-change evidence.

    """
    report: StringReport = StringReport(output=source)
    try:
        tree: Module = parse(source=source)
    except SyntaxError:
        report.skipped["parse"] = 1
        return report

    docstrings: set[int] = _docstring_lines(tree=tree)
    parents: dict[int, AST] = _parents(tree=tree)
    source_lines: ListStr = source.splitlines(keepends=True)
    offsets: list[int] = [0]
    for line in source_lines:
        offsets.append(offsets[-1] + len(line))

    edits: list[tuple[int, int, str]] = []
    for node in walk(node=tree):
        if (
            not isinstance(node, (JoinedStr, Constant))
            or node.lineno in docstrings
            or (isinstance(node, Constant) and not isinstance(node.value, str))
        ):
            continue

        if isinstance(node, Constant):
            collapsed: tuple[int, int, str] | None = _collapse_newlines(
                node=node,
                source=source,
                offsets=offsets,
                parents=parents,
            )
            if collapsed is not None:
                start, end, replacement = collapsed
                edits.append((start, end, replacement))
                report.changes.append(
                    StringChange(
                        kind="collapse",
                        line=node.lineno,
                        reason="whitespace-only",
                    ),
                )
                continue

        context: _FStringContext | _LiteralContext | str = (
            _fstring_context(
                node=node,
                source=source,
                source_lines=source_lines,
                offsets=offsets,
                parents=parents,
            )
            if isinstance(node, JoinedStr)
            else _literal_context(
                node=node,
                source=source,
                source_lines=source_lines,
                offsets=offsets,
                parents=parents,
            )
        )
        if isinstance(context, str):
            report.skipped[context] = report.skipped.get(context, 0) + 1
            continue

        outcome: _NodeRewrite = (
            _rewrite_fstring(ctx=context, line_length=line_length)
            if isinstance(context, _FStringContext)
            else _rewrite_literal(ctx=context, line_length=line_length)
        )
        _collect(
            report=report,
            edits=edits,
            context=context,
            line=node.lineno,
            outcome=outcome,
        )

    edits.sort(key=lambda item: item[0], reverse=True)
    output: str = source
    for start, end, new in edits:
        output = output[:start] + new + output[end:]

    try:
        parse(source=output)
    except SyntaxError:
        report.skipped["invalid-output"] = 1
        report.changes.clear()
        return report

    report.output = output
    return report
