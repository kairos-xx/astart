"""``str`` method calls type by method name."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.support.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("'a'.upper()", "str"),
        ("'a'.lower()", "str"),
        ("'a'.strip()", "str"),
        ("'a'.replace('a', 'b')", "str"),
        ("'a,b'.join(['x'])", "str"),
        ("'a'.startswith('b')", "bool"),
        ("'a'.endswith('b')", "bool"),
        ("'a'.isdigit()", "bool"),
        ("'a'.isidentifier()", "bool"),
        ("'a'.find('b')", "int"),
        ("'a'.count('b')", "int"),
        ("'a'.index('b')", "int"),
        ("x.upper()", None),
        ("'a'.bogus()", None),
        ("[1].upper()", None),
    ],
)
def test_str_method_calls(*, text: str, expected: str | None) -> None:
    """Check ``text`` types to ``expected`` (``None`` means refusal).

    Args:
        text (str): Expression source.
        expected (str | None): Required type string, or ``None`` for a refusal.

    """
    node: expr = parse(source=text, mode="eval").body
    expect_equal(
        actual=expression_type(node=node, counts={}),
        expected=expected,
    )
