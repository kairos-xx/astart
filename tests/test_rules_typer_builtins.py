"""``abs``/``round``/``min``/``max``/``sorted`` and container constructors."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("abs(-1)", "int"),
        ("abs(1.5)", "float"),
        ("abs('a')", None),
        ("round(1.5)", "int"),
        ("round(1)", "int"),
        ("round(1.5, 2)", None),
        ("sorted([1])", "list[int]"),
        ("sorted(['a'])", "list[str]"),
        ("sorted('ab')", None),
        ("min(1, 2)", "int"),
        ("max('a', 'b')", "str"),
        ("min(1, 'a')", None),
        ("min(1)", None),
        ("list([1])", "list[int]"),
        ("list('ab')", "list[str]"),
        ("set([1])", "set[int]"),
        ("set('ab')", "set[str]"),
        ("tuple((1, 'a'))", "tuple[int, str]"),
        ("tuple([1])", None),
        ("list({'a': 1})", None),
        ("list(x)", None),
    ],
)
def test_builtin_calls(*, text: str, expected: str | None) -> None:
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
