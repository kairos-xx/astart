"""Immutable, normalized type shapes and their join operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from astart.semantic.type_expressions import TypeExpression


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeShape:
    """Immutable normalized type shape with generic type arguments.

    Attributes:
        arguments (tuple[TypeShape, ...]): Arguments retained as
            tuple[TypeShape, ...] by this instance.
        name (str): Identifier used to refer to the name.

    """

    name: str
    arguments: tuple[TypeShape, ...] = ()

    def __str__(self) -> str:
        """Return deterministic Python-like type spelling.

        Returns:
            str: TODO.

        """
        if self.name == "union":
            return " | ".join(str(object=item) for item in self.arguments)
        if self.name == "parameters":
            return (
                "["
                + ", ".join(str(object=item) for item in self.arguments)
                + "]"
            )
        return (
            (
                f"{self.name}[{
                    ', '.join((str(object=item) for item in self.arguments))
                }]"
            )
            if self.arguments
            else self.name
        )


class ShapeConstants:
    """Deterministic abstract-type stabilization budgets.

    Attributes:
        MAX_TYPE_DEPTH (int): Max type depth retained as int by this instance.
        MAX_UNION_MEMBERS (int): Max union members retained as int by this
            instance.

    """

    MAX_TYPE_DEPTH: int = 12
    MAX_UNION_MEMBERS: int = 16


def shape_depth(*, shape: TypeShape, limit: int) -> int:
    """Measure nesting with an explicit stack and bounded traversal.

    Args:
        limit (int): Limit supplied as int for this operation.
        shape (TypeShape): Shape supplied as TypeShape for this operation.

    Returns:
        int: int produced by this operation.

    """
    deepest: int = 0
    pending: list[tuple[TypeShape, int]] = [(shape, 1)]
    while pending:
        current, level = pending.pop()
        deepest = max(deepest, level)
        if deepest > limit:
            return deepest
        pending.extend((child, level + 1) for child in current.arguments)
    return deepest


def atomic(*, name: str) -> TypeShape:
    """Create a simple type name.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    return TypeShape(name=name)


def _promote_numeric(*, flattened: set[TypeShape]) -> None:
    """Drop numeric members already covered by a wider numeric member.

    Args:
        flattened (set[TypeShape]): Flattened supplied as set[TypeShape] for
            this operation.

    """
    numeric: set[str] = {item.name for item in flattened if not item.arguments}
    if "complex" in numeric:
        flattened.difference_update(
            {atomic(name="float"), atomic(name="int"), atomic(name="bool")},
        )
    elif "float" in numeric:
        flattened.difference_update({atomic(name="int"), atomic(name="bool")})
    elif "int" in numeric:
        flattened.discard(atomic(name="bool"))


def union_shapes(
    *,
    shapes: tuple[TypeShape, ...],
    promote: bool = True,
) -> TypeShape:
    """Canonicalize unions, optionally promoting numeric containers.

    Args:
        promote (bool): Promote supplied as bool for this operation.
        shapes (tuple[TypeShape, ...]): Shapes supplied as tuple[TypeShape,
            ...] for this operation.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    flattened: set[TypeShape] = set()
    if any(item.name == "WidenedUnknown" for item in shapes):
        return atomic(name="WidenedUnknown")
    for item in shapes:
        if item.name == "union":
            flattened.update(item.arguments)
        elif item.name not in ("Never", "Unknown"):
            flattened.add(item)
    if not flattened:
        return (
            atomic(name="Unknown")
            if any(item.name == "Unknown" for item in shapes)
            else atomic(name="Never")
        )
    if promote:
        _promote_numeric(flattened=flattened)
    if len(flattened) > ShapeConstants.MAX_UNION_MEMBERS:
        return atomic(name="WidenedUnknown")
    ordered: tuple[TypeShape, ...] = tuple(sorted(flattened, key=str))
    return (
        ordered[0]
        if len(ordered) == 1
        else TypeShape(name="union", arguments=ordered)
    )


def join_types(
    *,
    left: TypeShape,
    right: TypeShape,
    promote: bool = True,
) -> TypeShape:
    """Join two inferred types with structural container-aware widening.

    Args:
        left (TypeShape): Left supplied as TypeShape for this operation.
        promote (bool): Promote supplied as bool for this operation.
        right (TypeShape): Right supplied as TypeShape for this operation.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    limit: int = ShapeConstants.MAX_TYPE_DEPTH
    if (
        left.name == "WidenedUnknown"
        or right.name == "WidenedUnknown"
        or shape_depth(shape=left, limit=limit) > limit
        or shape_depth(shape=right, limit=limit) > limit
    ):
        return atomic(name="WidenedUnknown")
    if left == right:
        return left
    if left.name in ("Never", "Unknown"):
        return right
    if right.name in ("Never", "Unknown"):
        return left
    if (
        left.name == right.name
        and left.name in ("list", "set", "dict", "tuple")
        and len(left.arguments) == len(right.arguments)
    ):
        return TypeShape(
            name=left.name,
            arguments=tuple(
                join_types(left=a, right=b, promote=promote)
                for a, b in zip(left.arguments, right.arguments, strict=True)
            ),
        )
    return union_shapes(shapes=(left, right), promote=promote)


def type_shape(*, expression: TypeExpression) -> TypeShape:
    """Project structured annotation syntax into the type lattice.

    Args:
        expression (TypeExpression): The expression examined while project
            structured
            annotation syntax into the type lattice.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    if expression.name == "union":
        items: tuple[TypeShape, ...] = tuple(
            type_shape(expression=item) for item in expression.arguments
        )
        return (
            items[0]
            if len(items) == 1
            else TypeShape(name="union", arguments=items)
        )
    return TypeShape(
        name=expression.name,
        arguments=tuple(
            type_shape(expression=item) for item in expression.arguments
        ),
    )
