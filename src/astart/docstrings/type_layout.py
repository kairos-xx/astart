"""Width-aware layout for type expressions inside docstring labels.

A type hint in a docstring is Python code living inside a string. It is
parsed into a real expression tree and laid out as a shadow AST: union
operands stay at the union's own level while subscript, tuple and list
arguments sit one level deeper, so breaks land on type-structure
boundaries and the docstring parser can rejoin the lines into the
identical type expression.

"""

from __future__ import annotations

from ast import (
    BinOp,
    BitOr,
    Call,
    Lambda,
    List,
    Subscript,
    Tuple,
    expr,
    parse,
    unparse,
    walk,
)
from ast import (
    dump as ast_dump,
)
from io import StringIO
from tokenize import (
    NAME,
    NUMBER,
    OP,
    STRING,
    TokenInfo,
    generate_tokens,
)
from typing import Final, final


@final
class Constants:
    """Layout controls for docstring type expressions.

    Attributes:
        step (Final[int]): Columns added per nesting level.
        union_tail (Final[int]): Columns reserved for a `` |`` line ending.

    """

    step: Final[int] = 4
    union_tail: Final[int] = 2


def type_lines(
    *,
    type_name: str,
    first_width: int,
    budget: int,
    base_indent: int = 8,
    parenthesize_union: bool = False,
) -> list[str] | None:
    """Layout ``type_name`` for a docstring entry label.

    Args:
        type_name (str): Source-language type expression text.
        first_width (int): Columns available on the label's first line.
        budget (int): Columns available per emitted line, indent included.
        base_indent (int): Render-space indent of the type's level.
        parenthesize_union (bool): Wrap a multi-line bare union in parentheses
            so the parser can
            track the label across lines.

    Returns:
        list[str] | None:
            Content lines — element ``0`` continues the label line inline
            and later elements carry absolute indentation — or ``None``
            when the text is not a parseable type expression or cannot
            improve on the flat form.

    """
    node: expr | None = _expression(source=type_name)
    if node is None or any(
        isinstance(child, (Call, Lambda)) for child in walk(node=node)
    ):
        return None
    flat: str = unparse(ast_obj=node)
    if len(flat) <= first_width:
        return [flat]
    pieces: list[tuple[int, str]] = _pieces(
        node=node,
        indent=base_indent,
        budget=budget,
        first_budget=first_width,
    )
    if len(pieces) <= 1 or len(pieces[0][1]) > first_width:
        return None
    lines: list[str] = [pieces[0][1]]
    lines.extend(" " * indent + text for indent, text in pieces[1:])
    if (
        parenthesize_union
        and isinstance(node, BinOp)
        and isinstance(node.op, BitOr)
    ):
        lines[0] = f"({lines[0]}"
        lines[-1] = f"{lines[-1]})"
    return lines


def _expression(*, source: str) -> expr | None:
    """Parse ``source`` as a single expression, or return ``None``.

    Args:
        source (str): Candidate expression text.

    Returns:
        expr | None: The parsed expression body.

    """
    try:
        return parse(source=source.strip(), mode="eval").body
    except (SyntaxError, ValueError):
        return None


def _pieces(
    *,
    node: expr,
    indent: int,
    budget: int,
    first_budget: int | None = None,
) -> list[tuple[int, str]]:
    """Lay out ``node`` as ``(indent, text)`` lines.

    Args:
        node (expr): Type expression node.
        indent (int): Indent of this node's continuation level.
        budget (int): Columns available per line, indent included.
        first_budget (int | None): Columns for the first line when it continues
            a parent line.

    Returns:
        list[tuple[int, str]]: Best-effort lines; unbreakable nodes keep
            their flat text even over budget.

    """
    flat: str = unparse(ast_obj=node)
    capacity: int = (
        first_budget if first_budget is not None else budget - indent
    )
    if len(flat) <= capacity:
        return [(indent, flat)]
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return _union_lines(
            operands=_union_operands(node=node),
            indent=indent,
            budget=budget,
            first_budget=first_budget,
        )
    bracket: tuple[str, list[expr], str, bool] | None = _bracket(node=node)
    if bracket is not None:
        return _bracket_lines(
            bracket=bracket,
            indent=indent,
            budget=budget,
        )
    return [(indent, flat)]


def _union_operands(*, node: BinOp) -> list[expr]:
    """Flatten a left-associative ``|`` chain into its operands.

    Args:
        node (BinOp): Union expression node.

    Returns:
        list[expr]: Operands in source order.

    """
    operands: list[expr] = []
    cursor: expr = node
    while isinstance(cursor, BinOp) and isinstance(cursor.op, BitOr):
        operands.append(cursor.right)
        cursor = cursor.left
    operands.append(cursor)
    operands.reverse()
    return operands


def _union_lines(
    *,
    operands: list[expr],
    indent: int,
    budget: int,
    first_budget: int | None,
) -> list[tuple[int, str]]:
    """Pack union operands onto lines at the union's own level.

    Args:
        operands (list[expr]): Union operands in source order.
        indent (int): Indent shared by every operand line.
        budget (int): Columns available per line, indent included.
        first_budget (int | None): Columns for the first line when it continues
            a parent line.

    Returns:
        list[tuple[int, str]]: Lines whose text joins back with spaces.

    """
    blocks: list[list[tuple[int, str]]] = [
        _pieces(node=operand, indent=indent, budget=budget)
        for operand in operands
    ]
    lines: list[tuple[int, str]] = []
    current: str = ""
    capacity: int = (
        first_budget if first_budget is not None else budget - indent
    )
    for index, block in enumerate(iterable=blocks):
        last: bool = index == len(blocks) - 1
        if len(block) == 1:
            _, text = block[0]
            separator: str = " | " if current else ""
            reserve: int = 0 if last else Constants.union_tail
            candidate: str = current + separator + text
            if current and len(candidate) + reserve > capacity:
                lines.append((indent, f"{current} |"))
                current = text
                capacity = budget - indent
            else:
                current = candidate
            continue
        if current:
            lines.append((indent, f"{current} |"))
            current = ""
            capacity = budget - indent
        lines.extend(block)
    if current:
        lines.append((indent, current))
    return lines


def _bracket(
    *,
    node: expr,
) -> tuple[str, list[expr], str, bool] | None:
    """Decompose a bracketed type node into head, args and closer.

    Args:
        node (expr): Candidate expression node.

    Returns:
        tuple[str, list[expr], str, bool] | None:
            ``(head, args, closer, force_comma)`` for subscript, tuple and
            list nodes, or ``None`` for other expressions.

    """
    if isinstance(node, Subscript):
        args: list[expr] = (
            list(node.slice.elts)
            if isinstance(node.slice, Tuple)
            else [node.slice]
        )
        return (f"{unparse(ast_obj=node.value)}[", args, "]", False)
    if isinstance(node, Tuple):
        return ("(", list(node.elts), ")", len(node.elts) == 1)
    if isinstance(node, List):
        return ("[", list(node.elts), "]", False)
    return None


def _bracket_lines(
    *,
    bracket: tuple[str, list[expr], str, bool],
    indent: int,
    budget: int,
) -> list[tuple[int, str]]:
    """Lay out a bracketed node with one argument per level.

    Args:
        bracket (tuple[str, list[expr], str, bool]): Bracket components.
        indent (int): Indent of the bracket's own level.
        budget (int): Columns available per line, indent included.

    Returns:
        list[tuple[int, str]]: Lines for the whole bracketed expression.

    """
    head, args, closer, force_comma = bracket
    lines: list[tuple[int, str]] = [(indent, head)]
    step: int = Constants.step
    for index, arg in enumerate(iterable=args):
        arg_lines: list[tuple[int, str]] = _pieces(
            node=arg,
            indent=indent + step,
            budget=budget,
        )
        comma: str = (
            ","
            if index < len(args) - 1 or (force_comma and len(args) == 1)
            else ""
        )
        last_index, last_text = arg_lines[-1]
        arg_lines[-1] = (last_index, f"{last_text}{comma}")
        lines.extend(arg_lines)
    lines.append((indent, closer))
    return lines


def canonical_type(*, type_text: str) -> str | None:
    """Canonicalize type text through a real expression round trip.

    Args:
        type_text (str): Candidate type expression text.

    Returns:
        str | None: ``unparse`` of the parsed expression, or ``None``
            when the text is not a call-free Python expression.

    """
    node: expr | None = _expression(source=type_text)
    if node is None or any(
        isinstance(child, (Call, Lambda)) for child in walk(node=node)
    ):
        return None
    return unparse(ast_obj=node)


def compact_type(*, type_text: str) -> str | None:
    """Render ``type_text`` with cosmetic whitespace removed.

    The expression is parsed, unparsed to its canonical spaced form, then
    re-joined from the token stream so string literals keep their content.
    Spaces survive only where dropping them would merge two word tokens.

    Args:
        type_text (str): Candidate type expression text.

    Returns:
        str | None: The compact rendering, or ``None`` when the text is
            not a call-free Python expression or compaction does not
            round-trip to the same expression tree.

    """
    node: expr | None = _expression(source=type_text)
    if node is None or any(
        isinstance(child, (Call, Lambda)) for child in walk(node=node)
    ):
        return None
    flat: str = unparse(ast_obj=node)
    kept: list[TokenInfo] = [
        tok
        for tok in generate_tokens(
            readline=StringIO(initial_value=flat).readline,
        )
        if tok.type in {NAME, OP, NUMBER, STRING}
    ]
    word: frozenset[int] = frozenset({NAME, NUMBER, STRING})
    parts: list[str] = []
    previous: TokenInfo | None = None
    for tok in kept:
        if previous is not None and previous.type in word and tok.type in word:
            parts.append(" ")
        parts.append(tok.string)
        previous = tok
    compact: str = "".join(parts)
    try:
        reparsed: expr = parse(source=compact, mode="eval").body
    except (SyntaxError, ValueError):
        return None
    if ast_dump(node=reparsed) != ast_dump(node=node):
        return None
    return compact
