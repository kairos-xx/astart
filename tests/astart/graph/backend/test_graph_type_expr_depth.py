"""Keep inferred type expressions shallow enough to render and key safely."""

from __future__ import annotations

from typing import final

from astart.graph.backend.engine import Constants, TypeExpr, merge_types

from tests.support.expectations import expect_equal, expect_true


@final
class Fixtures:
    """Group module-level constants.

    Attributes:
        str_type (TypeExpr): Grouped module constant.
        int_type (TypeExpr): Grouped module constant.

    """

    str_type: TypeExpr = TypeExpr.name_expr(name=Constants.str)
    int_type: TypeExpr = TypeExpr.name_expr(name=Constants.int)


def _nested_tuple(*, depth: int) -> TypeExpr:
    """Build a tuple type nested to the requested depth.

    Args:
        depth (int): Number of generic wraps around the leaf type.

    Returns:
        TypeExpr: The nested generic type expression.

    """
    expr: TypeExpr = Fixtures.str_type
    for _ in range(depth):
        expr = TypeExpr.generic("tuple", expr)
    return expr


def test_generic_depth_is_bounded() -> None:
    """Collapse args that would exceed the maximum type depth."""
    expr: TypeExpr = _nested_tuple(
        depth=Constants.max_type_depth + 10,
    )
    expect_true(condition=expr.depth <= Constants.max_type_depth)
    _ = expr.key()
    _ = expr.to_source()


def test_union_depth_is_bounded() -> None:
    """Keep union members within the depth budget when flattening."""
    deep: TypeExpr = _nested_tuple(depth=Constants.max_type_depth)
    expr: TypeExpr = TypeExpr.union(deep, Fixtures.int_type)
    expect_true(condition=expr.depth <= Constants.max_type_depth)
    _ = expr.key()
    _ = expr.to_source()


def test_callable_depth_is_bounded() -> None:
    """Bound callable parameters and return types independently."""
    deep: TypeExpr = _nested_tuple(depth=Constants.max_type_depth)
    expr: TypeExpr = TypeExpr.callable_expr(
        parameters=[deep],
        return_type=deep,
    )
    expect_true(condition=expr.depth <= Constants.max_type_depth)
    _ = expr.key()
    _ = expr.to_source()


def test_shallow_types_keep_their_structure() -> None:
    """Preserve moderate nesting so annotations stay precise."""
    expr: TypeExpr = _nested_tuple(depth=3)
    expect_equal(actual=expr.depth, expected=4)
    expect_equal(actual=expr.to_source(), expected="tuple[tuple[tuple[str]]]")


def test_merge_types_on_bounded_expressions() -> None:
    """Merge deeply nested expressions without unbounded recursion."""
    left: TypeExpr = _nested_tuple(depth=Constants.max_type_depth + 5)
    right: TypeExpr = _nested_tuple(depth=Constants.max_type_depth + 5)
    merged: TypeExpr = merge_types(left=left, right=right)
    expect_true(condition=merged.depth <= Constants.max_type_depth)
