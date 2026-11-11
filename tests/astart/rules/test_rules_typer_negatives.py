"""The typer never guesses: unprovable expressions give ``None``."""

from __future__ import annotations

from ast import Await, Module, Starred, Yield, expr, parse, walk

import pytest
from astart.rules.provable import expression_type

from tests.support.expectations import expect_equal, expect_not_none


@pytest.mark.parametrize(
    "text",
    [
        "x",
        "x.attr",
        "f()",
        "a + b",
        "[]",
        "{}",
        "()",
        "lambda: 1",
    ],
)
def test_unprovable_expressions_give_none(*, text: str) -> None:
    """Check that ``text`` has no provable type.

    Args:
        text (str): Expression source.

    """
    node: expr = parse(source=text, mode="eval").body
    expect_equal(actual=expression_type(node=node, counts={}), expected=None)


@pytest.mark.parametrize(
    ("kind", "source"),
    [
        (
            "await",
            """\
async def f():
    await x
""",
        ),
        (
            "yield",
            """\
def f():
    yield
""",
        ),
        (
            "starred",
            """\
f(*a)
""",
        ),
        ("ifexp", "x if y else z"),
    ],
)
def test_unprovable_special_forms_give_none(
    *,
    kind: str,
    source: str,
) -> None:
    """Check that ``kind`` parses to an unprovable expression.

    Args:
        kind (str): Which special form ``source`` holds.
        source (str): Module or expression source.

    """
    node: expr = expect_not_none(
        value=_special_node(kind=kind, source=source),
    )
    expect_equal(actual=expression_type(node=node, counts={}), expected=None)


def _special_node(*, kind: str, source: str) -> expr | None:
    """Extract the expression a special form parses to.

    Args:
        kind (str): One of ``await``, ``yield``, ``starred`` or ``ifexp``.
        source (str): Source holding the form.

    Returns:
        expr | None: The awaited, yielded, starred or conditional
            expression, or ``None`` when the form is absent.

    """
    if kind == "ifexp":
        return parse(source=source, mode="eval").body
    tree: Module = parse(source=source, mode="exec")
    for node in walk(node=tree):
        if kind == "await" and isinstance(node, Await):
            return node
        if kind == "yield" and isinstance(node, Yield):
            return node
        if kind == "starred" and isinstance(node, Starred):
            return node
    return None
