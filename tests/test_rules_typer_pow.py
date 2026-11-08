"""``**`` types to ``int``/``float`` only when no ``complex`` is possible."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2 ** 3", "int"),
        ("2 ** 0", "int"),
        ("True ** 2", "int"),
        ("2 ** -1", None),
        ("2.0 ** 2", "float"),
        ("2 ** 0.5", "float"),
        ("2.0 ** 0.5", "float"),
        ("(-2) ** 0.5", None),
        ("x ** 2", None),
        ("2 ** x", None),
        ("'a' ** 2", None),
    ],
)
def test_pow_operator(*, text: str, expected: str | None) -> None:
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
