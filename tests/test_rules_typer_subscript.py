"""Subscripts type through ``list``/``str``/``dict`` element rules."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[1][0]", "int"),
        ("['a'][0]", "str"),
        ("[[1]][0]", "list[int]"),
        ("[1][1:2]", "list[int]"),
        ('"ab"[0]', "str"),
        ('"ab"[1:2]', "str"),
        ("{'a': 1}['a']", "int"),
        ("{1: 'a'}[1]", "str"),
        ("{'a': 1}[0]", None),
        ("[1]['a']", None),
        ("{'a': {'b': 1}}['a']['b']", "int"),
        ("{'a': 1}[1:2]", None),
    ],
)
def test_subscripts(*, text: str, expected: str | None) -> None:
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
