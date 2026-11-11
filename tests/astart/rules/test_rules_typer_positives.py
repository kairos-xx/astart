"""Provable expressions give their exact type."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.support.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1", "int"),
        ("'a'", "str"),
        ("1.5", "float"),
        ("True", "bool"),
        ("not x", "bool"),
        ("len('a')", "int"),
        ("[1, 2]", "list[int]"),
        ("{'a': 1}", "dict[str, int]"),
        ("f'{x}'", "str"),
    ],
)
def test_provable_expressions_give_their_type(
    *,
    text: str,
    expected: str,
) -> None:
    """Check that ``text`` types to ``expected``.

    Args:
        text (str): Expression source.
        expected (str): Required type string.

    """
    node: expr = parse(source=text, mode="eval").body
    expect_equal(
        actual=expression_type(node=node, counts={}),
        expected=expected,
    )
