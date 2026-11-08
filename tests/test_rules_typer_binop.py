"""``%`` formatting and ``+`` on lists type when provable."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("'%s' % 1", "str"),
        ("'%s %s' % ('a', 1)", "str"),
        ("1 % 2", "int"),
        ("1.5 % 2", "float"),
        ("[1] + [2]", "list[int]"),
        ("['a'] + ['b']", "list[str]"),
        ("[1] + ['a']", None),
        ("[1] + (2,)", None),
        ("x + [2]", None),
    ],
)
def test_binop_extensions(*, text: str, expected: str | None) -> None:
    """Check ``text`` types to ``expected`` (``None`` means refusal).

    Args:
        text: Expression source.
        expected: Required type string, or ``None`` for a refusal.

    """
    node: expr = parse(source=text, mode="eval").body
    expect_equal(
        actual=expression_type(node=node, counts={}),
        expected=expected,
    )
