"""Union and intersection of type annotations written as source text.

Every result is deterministic and independent of the order of the inputs.
Only collapses that never change what the annotation accepts are applied
here; lossy ones (``int | float`` to ``float``, ``list | set`` to
``Collection``) need calibration first (``docs/TODO.md`` F-24).
"""

from __future__ import annotations

from ast import (
    AST,
    BinOp,
    BitOr,
    Constant,
    Expression,
    Subscript,
    Tuple,
    expr,
    parse,
    unparse,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        numeric_ranks: Builtin numeric types from narrowest to widest.
        scalar_order: Sort order of the common scalar types in a union.
        closed_builtins: Builtin types no class can inherit from two of.
        literal_types: Builtin type each literal constant belongs to.
        top: The type that absorbs every union.
        bottom: The type that vanishes from every union.
        nothing: The spelling of an absent value.
        empty_limit: Most members an intersection result may keep.

    """

    numeric_ranks: Final[dict[str, int]] = {
        "bool": 0,
        "int": 1,
        "float": 2,
        "complex": 3,
    }
    scalar_order: Final[tuple[str, ...]] = (
        "int",
        "float",
        "complex",
        "str",
        "bytes",
    )
    closed_builtins: Final[frozenset[str]] = frozenset(
        {
            "bool",
            "int",
            "float",
            "complex",
            "str",
            "bytes",
            "bytearray",
            "list",
            "dict",
            "set",
            "frozenset",
            "tuple",
        },
    )
    literal_types: Final[dict[type, str]] = {
        bool: "bool",
        int: "int",
        str: "str",
        bytes: "bytes",
    }
    top: Final[str] = "object"
    bottom: Final[str] = "Never"
    nothing: Final[str] = "None"
    empty_limit: Final[int] = 8


@final
@dataclass(frozen=True, slots=True)
class Intersection:
    """Outcome of narrowing one type by another.

    Attributes:
        type_text: The narrowed type, or ``None`` when nothing is left or
            the relation is unknown.
        decided: ``True`` when the algebra knows the answer; an undecided
            intersection must leave the belief as it was.

    """

    type_text: str | None
    decided: bool


def _parse(*, source: str) -> expr | None:
    """Parse an annotation source.

    Args:
        source: Annotation text.

    Returns:
        The expression, or ``None`` when the text is not an expression.

    """
    try:
        tree: Expression = parse(source=source, mode="eval")
    except SyntaxError:
        return None
    return tree.body


def _head(*, node: AST) -> tuple[str, tuple[expr, ...] | None]:
    """Split a type expression into its origin and its arguments.

    Args:
        node: Parsed annotation.

    Returns:
        The origin text and the arguments, or ``None`` when not subscripted.

    """
    if isinstance(node, Subscript):
        inner: expr = node.slice
        arguments: tuple[expr, ...] = (
            tuple(inner.elts) if isinstance(inner, Tuple) else (inner,)
        )
        return unparse(ast_obj=node.value), arguments
    return unparse(ast_obj=node), None


@final
class TypeAlgebra:
    """Union and intersection over annotation sources."""

    @staticmethod
    def members(*, source: str) -> tuple[str, ...]:
        """Flatten ``A | B | C`` into its distinct top-level members.

        Args:
            source: Annotation text.

        Returns:
            The members in source order; the text itself when it is not a
            union or does not parse.

        """
        node: expr | None = _parse(source=source)
        if node is None:
            return (source,)
        pending: list[expr] = [node]
        found: list[str] = []
        while pending:
            current: expr = pending.pop()
            if isinstance(current, BinOp) and isinstance(current.op, BitOr):
                pending.extend((current.right, current.left))
            else:
                found.append(unparse(ast_obj=current))
        return tuple(dict.fromkeys(found))

    def union(self, *, types: Sequence[str], limit: int) -> str | None:
        """Join several types into one normalized union.

        Args:
            types: Annotation sources, each possibly a union itself.
            limit: Most members the result may have.

        Returns:
            The union, ``object`` when any member is ``object``, or ``None``
            when there is nothing to join or too many members remain.

        """
        found: list[str] = [
            member
            for text in types
            for member in self.members(source=text)
            if member != Constants.bottom
        ]
        if not found:
            return None
        if Constants.top in found:
            return Constants.top
        present: frozenset[str] = frozenset(found)
        kept: list[str] = [
            member
            for member in dict.fromkeys(found)
            if not self._absorbed(member=member, present=present)
        ]
        ordered: list[str] = sorted(
            (item for item in kept if item != Constants.nothing),
            key=self._order,
        )
        if Constants.nothing in kept:
            ordered.append(Constants.nothing)
        if len(ordered) > limit:
            return None
        return " | ".join(ordered)

    def intersect(self, *, left: str, right: str) -> Intersection:
        """Narrow one type by another.

        Args:
            left: The type believed so far.
            right: The type that narrows it.

        Returns:
            The narrowed type; empty when no value fits both; undecided when
            the relation between the types is not known (user classes).

        """
        if left == right:
            return Intersection(type_text=left, decided=True)
        if Constants.top in (left, right):
            other: str = right if left == Constants.top else left
            return Intersection(type_text=other, decided=True)
        survivors: list[str] = []
        for first in self.members(source=left):
            for second in self.members(source=right):
                kind, text = self._meet(left=first, right=second)
                if kind == "undecided":
                    return Intersection(type_text=None, decided=False)
                if text is not None:
                    survivors.append(text)
        if not survivors:
            return Intersection(type_text=None, decided=True)
        joined: str | None = self.union(
            types=survivors,
            limit=Constants.empty_limit,
        )
        return Intersection(type_text=joined, decided=True)

    @staticmethod
    def _absorbed(*, member: str, present: frozenset[str]) -> bool:
        """Tell whether another member already covers this one.

        Args:
            member: Union member.
            present: Every member of the union.

        Returns:
            ``True`` for ``bool`` beside ``int`` and for a ``Literal`` whose
            values all belong to a builtin that is also present.

        """
        if member == "bool":
            return "int" in present
        if not member.startswith("Literal["):
            return False
        node: expr | None = _parse(source=member)
        if not isinstance(node, Subscript):
            return False
        inner: expr = node.slice
        values: tuple[expr, ...] = (
            tuple(inner.elts) if isinstance(inner, Tuple) else (inner,)
        )
        names: set[str] = set()
        for value in values:
            if not isinstance(value, Constant):
                return False
            name: str | None = Constants.literal_types.get(type(value.value))
            if name is None:
                return False
            names.add(name)
        return all(
            name in present or (name == "bool" and "int" in present)
            for name in names
        )

    @staticmethod
    def _order(member: str) -> tuple[int, int, str]:
        """Give a union member its deterministic sort key.

        Args:
            member: Union member.

        Returns:
            A key placing common scalars first, then everything else by text.

        """
        if member in Constants.scalar_order:
            return 0, Constants.scalar_order.index(member), member
        return 1, 0, member

    def _meet(self, *, left: str, right: str) -> tuple[str, str | None]:
        """Narrow two single (non-union) types.

        Args:
            left: First type.
            right: Second type.

        Returns:
            ``("type", text)``, ``("empty", None)`` or ``("undecided", None)``.

        """
        if left == right:
            return "type", left
        first: expr | None = _parse(source=left)
        second: expr | None = _parse(source=right)
        if first is None or second is None:
            return "undecided", None
        left_origin, left_args = _head(node=first)
        right_origin, right_args = _head(node=second)
        if left_origin == right_origin:
            return self._meet_arguments(
                origin=left_origin,
                left=left_args,
                right=right_args,
            )
        ranks: dict[str, int] = Constants.numeric_ranks
        if left_origin in ranks and right_origin in ranks:
            narrow: str = min(left_origin, right_origin, key=ranks.__getitem__)
            return "type", narrow
        if self._disjoint(names=(left_origin, right_origin)):
            return "empty", None
        return "undecided", None

    @staticmethod
    def _disjoint(*, names: tuple[str, str]) -> bool:
        """Tell whether no value can belong to both types.

        Args:
            names: Origin text of each type.

        Returns:
            ``True`` when both are different closed builtins or ``None``.

        """
        return all(
            name in Constants.closed_builtins or name == Constants.nothing
            for name in names
        )

    def _meet_arguments(
        self,
        *,
        origin: str,
        left: tuple[expr, ...] | None,
        right: tuple[expr, ...] | None,
    ) -> tuple[str, str | None]:
        """Narrow two uses of one generic origin argument by argument.

        Args:
            origin: The shared origin text.
            left: Arguments of the first, or ``None`` when bare.
            right: Arguments of the second, or ``None`` when bare.

        Returns:
            The narrowed generic, or the empty/undecided verdicts.

        """
        if left is None or right is None:
            chosen: tuple[expr, ...] | None = left if right is None else right
            if chosen is None:
                return "type", origin
            shown: str = ", ".join(unparse(ast_obj=item) for item in chosen)
            return "type", f"{origin}[{shown}]"
        if len(left) != len(right):
            return "undecided", None
        merged: list[str] = []
        for first, second in zip(left, right, strict=True):
            result: Intersection = self.intersect(
                left=unparse(ast_obj=first),
                right=unparse(ast_obj=second),
            )
            if not result.decided:
                return "undecided", None
            if result.type_text is None:
                return "empty", None
            merged.append(result.type_text)
        return "type", f"{origin}[{', '.join(merged)}]"
