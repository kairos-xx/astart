"""Union and intersection of type annotations written as source text.

Every result is deterministic and independent of the order of the inputs.
Only collapses that never change what the annotation accepts are applied
here; lossy ones (``int | float`` to ``float``, ``list | set`` to
``Collection``) need calibration first (``docs/planning/TODO.md`` F-24).

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
        numeric_ranks (Final[dict[str, int]]): Builtin numeric types from
            narrowest to widest.
        scalar_order (Final[tuple[str, ...]]): Sort order of the common scalar
            types in a union.
        closed_builtins (Final[frozenset[str]]): Builtin types no class can
            inherit from two of.
        literal_types (Final[dict[type, str]]): Builtin type each literal
            constant belongs to.
        top (Final[str]): The type that absorbs every union.
        bottom (Final[str]): The type that vanishes from every union.
        nothing (Final[str]): The spelling of an absent value.
        empty_limit (Final[int]): Most members an intersection result may keep.

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
        type_text (str | None): The narrowed type, or ``None`` when nothing
            is left or the relation is unknown.
        decided (bool): ``True`` when the algebra knows the answer; an
            undecided intersection must leave the belief as it was.

    """

    type_text: str | None
    decided: bool


def _parse(*, source: str) -> expr | None:
    """Parse an annotation source.

    Args:
        source (str): Annotation text.

    Returns:
        expr | None:
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
        node (AST): Parsed annotation.

    Returns:
        tuple[str, tuple[expr, ...] | None]: The origin text and the arguments,
            or ``None`` when not subscripted.

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
            source (str): Annotation text.

        Returns:
            tuple[str, ...]: The members in source order; the text itself
                when it is not a union or does not parse.

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

    @staticmethod
    def origin(*, source: str) -> str | None:
        """Spell the origin of one member, dropping its arguments.

        Args:
            source (str): Annotation text such as ``list[int]``.

        Returns:
            str | None: The origin text (``list``), or ``None`` when
                the source does not parse as a type expression.

        """
        node: expr | None = _parse(source=source)
        if node is None:
            return None
        head, _arguments = _head(node=node)
        return head

    def union(self, *, types: Sequence[str], limit: int) -> str | None:
        """Join several types into one normalized union.

        Args:
            types (Sequence[str]): Annotation sources, each possibly a union
                itself.
            limit (int): Most members the result may have.

        Returns:
            str | None: The union, ``object`` when any member is
                ``object``, or ``None`` when there is
                nothing to join or too many members remain.

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

    def subtract(self, *, current: str, removed: str) -> str | None:
        """Remove the members of ``current`` that ``removed`` covers.

        A member is dropped only when every value of it is provably an
        instance of a removed type — ``isinstance`` semantics, so ``bool``
        is covered by ``int`` but ``int`` is not covered by ``float``.
        Anything else is kept, which makes the result a sound
        over-approximation of the complement.

        Args:
            current (str): The type believed so far.
            removed (str): The type the complement excludes.

        Returns:
            str | None:
                The remaining union, or ``None`` when no member survives.

        """
        parts: tuple[str, ...] = tuple(
            part.strip() for part in removed.split(sep=" & ")
        )
        kept: list[str] = [
            member
            for member in self.members(source=current)
            if not all(
                self._subsumed(member=member, removed=part) for part in parts
            )
        ]
        if not kept:
            return None
        return self.union(types=kept, limit=len(kept))

    @classmethod
    def _subsumed(cls, *, member: str, removed: str) -> bool:
        """Tell whether a removed type covers every value of a member.

        Args:
            member (str): One union member of the current type.
            removed (str): The excluded type, possibly a union itself.

        Returns:
            bool: ``True`` when the member is provably inside ``removed``.

        """
        return any(
            cls._covers(outer=outer, inner=member)
            for outer in cls.members(source=removed)
        )

    @classmethod
    def _covers(cls, *, outer: str, inner: str) -> bool:
        """Tell whether ``inner`` is provably a subtype of ``outer``.

        Args:
            outer (str): The covering type.
            inner (str): The covered type.

        Returns:
            bool: ``True`` only for proofs: the same type, a parameterisation
                of a bare origin, ``bool`` inside ``int``, or a
                ``Literal`` whose values all belong to ``outer``.

        """
        if inner == outer:
            return True
        if inner.startswith("Literal["):
            return cls._literal_covered(outer=outer, inner=inner)
        inner_node: expr | None = _parse(source=inner)
        outer_node: expr | None = _parse(source=outer)
        if inner_node is None or outer_node is None:
            return False
        inner_origin, _inner_args = _head(node=inner_node)
        outer_origin, outer_args = _head(node=outer_node)
        if inner_origin == outer_origin:
            return outer_args is None
        return inner_origin == "bool" and outer_origin == "int"

    @classmethod
    def _literal_covered(cls, *, outer: str, inner: str) -> bool:
        """Tell whether every value of a ``Literal`` fits ``outer``.

        Args:
            outer (str): The covering type.
            inner (str): The ``Literal[...]`` member.

        Returns:
            bool: ``True`` when each literal constant's builtin type is
                covered.

        """
        node: expr | None = _parse(source=inner)
        if not isinstance(node, Subscript):
            return False
        slice_node: expr = node.slice
        values: tuple[expr, ...] = (
            tuple(slice_node.elts)
            if isinstance(slice_node, Tuple)
            else (slice_node,)
        )
        names: set[str] = set()
        for value in values:
            if not isinstance(value, Constant):
                return False
            name: str | None = Constants.literal_types.get(type(value.value))
            if name is None:
                return False
            names.add(name)
        return bool(names) and all(
            cls._covers(outer=outer, inner=name) for name in names
        )

    def intersect(self, *, left: str, right: str) -> Intersection:
        """Narrow one type by another.

        Args:
            left (str): The type believed so far.
            right (str): The type that narrows it.

        Returns:
            Intersection: The narrowed type; empty when no value fits
                both; undecided when the relation between
                the types is not known (user classes).

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
            member (str): Union member.
            present (frozenset[str]): Every member of the union.

        Returns:
            bool: ``True`` for ``bool`` beside ``int`` and for a ``Literal``
                whose values all belong to a builtin that is also present.

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
            member (str): Union member.

        Returns:
            tuple[int, int, str]: A key placing common scalars first,
                then everything else by text.

        """
        if member in Constants.scalar_order:
            return 0, Constants.scalar_order.index(member), member
        return 1, 0, member

    def _meet(self, *, left: str, right: str) -> tuple[str, str | None]:
        """Narrow two single (non-union) types.

        Args:
            left (str): First type.
            right (str): Second type.

        Returns:
            tuple[str, str | None]: ``("type", text)``, ``("empty", None)``
                or ``("undecided", None)``.

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
            names (tuple[str, str]): Origin text of each type.

        Returns:
            bool: ``True`` when both are different closed builtins or ``None``.

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
            origin (str): The shared origin text.
            left (tuple[expr, ...] | None): Arguments of the first, or ``None``
                when bare.
            right (tuple[expr, ...] | None): Arguments of the second, or
                ``None`` when bare.

        Returns:
            tuple[str, str | None]: The narrowed generic, or the
                empty/undecided verdicts.

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

    def narrow(self, *, current: str, constraint: str) -> str | None:
        """Apply a ``" & "``-joined narrowing constraint to a type.

        ``!X`` atoms subtract ``X``; bare atoms intersect. This is the
        same semantics a settled belief applies to its candidates.

        Args:
            current (str): The type believed so far.
            constraint (str): Constraint text such as ``"!None"`` or
                ``"C & !None"``.

        Returns:
            str | None:
                The narrowed type, or ``None`` when an atom decides it away.

        """
        kept: str = current
        for part in constraint.split(sep=" & "):
            atom: str = part.strip()
            if atom.startswith("!"):
                narrowed: str | None = self.subtract(
                    current=kept,
                    removed=atom.removeprefix("!"),
                )
                if narrowed is None:
                    return None
                kept = narrowed
                continue
            result: Intersection = self.intersect(left=kept, right=atom)
            if result.decided:
                if result.type_text is None:
                    return None
                kept = result.type_text
        return kept
