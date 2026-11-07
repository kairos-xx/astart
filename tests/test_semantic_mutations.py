"""Differential mutation checks against fresh full static analysis."""

from __future__ import annotations

from ast import Constant, Module, fix_missing_locations, stmt, unparse
from typing import TYPE_CHECKING

import pytest
from astart.ast import CommentedModule
from astart.semantic.values import AbstractValue, LiteralValue, UnknownValue

from tests.expectations import expect_equal, expect_instance, expect_is

if TYPE_CHECKING:
    from astart.semantic.analyzer import SemanticAnalyzer


@pytest.mark.parametrize("changed", range(80))
def test_incremental_mutation_matches_fresh_full_analysis(
    *,
    changed: int,
) -> None:
    """A changed definition and its dependents match a fresh parse.

    Args:
        changed: Changed supplied as int for this operation.

    """
    source: str = """\
a=1
b=a+2
c=b*3
d=100
e=c+d
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    semantic: SemanticAnalyzer = tree.semantic
    expect_equal(
        actual=(tree.infer(node="e")),
        expected=LiteralValue(value=109),
    )
    value: None | Constant = getattr(tree.body[0], "value", None)
    if value is not None:
        value.value = changed
    expect_equal(actual=bool(semantic.refresh()), expected=changed != 1)
    incremental: AbstractValue = tree.infer(node="e")
    reconstructed: Module = Module(body=tree.body, type_ignores=[])
    fix_missing_locations(node=reconstructed)
    fresh: CommentedModule = CommentedModule.parse(
        source=unparse(ast_obj=reconstructed),
    )
    expect_equal(actual=fresh.infer(node="e"), expected=incremental)
    expect_equal(
        actual=incremental,
        expected=LiteralValue(value=(changed + 2) * 3 + 100),
    )
    expect_equal(actual=tree.infer(node="d"), expected=LiteralValue(value=100))


@pytest.mark.parametrize("position", range(3))
def test_move_reanalysis_matches_fresh(*, position: int) -> None:
    """Moving a binding updates reachability without changing node IDs.

    Args:
        position: Position supplied as int for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+2
c=b+3
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    moved: stmt = tree.body.pop(0)
    tree.body.insert(position, moved)
    semantic.refresh()
    fresh: CommentedModule = CommentedModule.parse(
        source=(unparse(ast_obj=Module(body=tree.body, type_ignores=[]))),
    )
    for name in ("a", "b", "c"):
        new_value: AbstractValue = fresh.infer(node=name)
        old_value: AbstractValue = tree.infer(node=name)
        expect_is(actual=type(old_value), expected=type(new_value))
        if isinstance(old_value, LiteralValue):
            expect_equal(actual=old_value, expected=new_value)
        else:
            old_value = expect_instance(value=old_value, kind=UnknownValue)
