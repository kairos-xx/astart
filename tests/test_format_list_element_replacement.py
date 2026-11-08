"""The writer can swap one element of a child list for an atom."""

from __future__ import annotations

from ast import (
    Assign,
    Attribute,
    Call,
    Constant,
    Expr,
    FunctionDef,
    Load,
    Name,
    Tuple,
)
from typing import TYPE_CHECKING

from astart import parse, unparse

if TYPE_CHECKING:
    from astart.ast import CommentedModule

from tests.expectations import expect_equal, expect_instance


def _qualified() -> Attribute:
    """Build a ``Constants.LIMIT`` attribute node.

    Returns:
        The attribute node.

    """
    return Attribute(
        value=Name(id="Constants", ctx=Load()),
        attr="LIMIT",
        ctx=Load(),
    )


def test_a_default_value_can_be_replaced() -> None:
    """Check that a default value can be replaced."""
    module: CommentedModule = parse(
        source="def f(a, n=LIMIT, *, k=2):  # keep\n    return n\n",
        filename="m.py",
    )
    function: FunctionDef = expect_instance(
        value=module.body[0],
        kind=FunctionDef,
    )
    function.args.defaults[0] = _qualified()
    expect_equal(
        actual=unparse(tree=module, preserve_formatting=True),
        expected=(
            "def f(a, n=Constants.LIMIT, *, k=2):  # keep\n    return n\n"
        ),
    )


def test_call_arguments_and_tuple_elements_can_be_replaced() -> None:
    """Check that call arguments and tuple elements can be replaced."""
    module: CommentedModule = parse(
        source="f(1, LIMIT, 3)  # c\nx = (A, B)\n",
        filename="m.py",
    )
    statement: Expr = expect_instance(value=module.body[0], kind=Expr)
    call: Call = expect_instance(value=statement.value, kind=Call)
    call.args[1] = _qualified()
    assignment: Assign = expect_instance(value=module.body[1], kind=Assign)
    pair: Tuple = expect_instance(value=assignment.value, kind=Tuple)
    pair.elts[0] = Constant(value=7)
    expect_equal(
        actual=unparse(tree=module, preserve_formatting=True),
        expected="f(1, Constants.LIMIT, 3)  # c\nx = (7, B)\n",
    )
