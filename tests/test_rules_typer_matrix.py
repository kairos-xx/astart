"""Pin every verified ``expression_type`` row as a regression matrix."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1 + 2", "int"),
        ("1 + 2.0", "float"),
        ("1 / 2", "float"),
        ("7 // 2", "int"),
        ("7 % 2", "int"),
        ("2 ** 3", "int"),
        ("-1", "int"),
        ("True + True", "int"),
        ("'a' + 'b'", "str"),
        ("'a' * 3", "str"),
        ("1 < 2", "bool"),
        ("'a' in 'b'", "bool"),
        ("not 1", "bool"),
        ("1 if True else 2", "int"),
        ("1 and 2", "int"),
        ("str(1)", "str"),
        ("chr(97)", "str"),
        ("repr(1)", "str"),
        ("int('1')", "int"),
        ("ord('a')", "int"),
        ("float(1)", "float"),
        ("bool(0)", "bool"),
        ("isinstance(1, int)", "bool"),
        ("{1, 2}", "set[int]"),
        ("(1, 'a')", "tuple[int, str]"),
        ("b'x'", "bytes"),
        ("[i for i in range(3)]", "list[int]"),
        ("1 if True else 'a'", None),
        ("1 or 'a'", None),
        ("[1, 'a']", None),
        ("f(1)", None),
    ],
)
def test_typer_matrix(*, text: str, expected: str | None) -> None:
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
