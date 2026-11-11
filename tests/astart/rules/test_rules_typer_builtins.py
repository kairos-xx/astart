"""``abs``/``round``/``min``/``max``/``sorted`` and container constructors."""

from __future__ import annotations

from ast import expr, parse

import pytest
from astart.rules.provable import expression_type

from tests.support.expectations import expect_equal


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
        ("tuple([1])", "tuple[int, ...]"),
        ("list({'a': 1})", "list[str]"),
        ("list(x)", None),
        ("dict({'a': 1})", "dict[str, int]"),
        ("dict([('a', 1)])", "dict[str, int]"),
        ("dict()", None),
        ("dict(a=1)", None),
        ("sum([1, 2])", "int"),
        ("sum([1.0])", "float"),
        ("sum([1], 0.0)", "float"),
        ("sum(['a'])", None),
        ("next([1])", "int"),
        ("next([1], 'x')", "int | str"),
        ("next([])", None),
        ("any([1])", "bool"),
        ("all([])", "bool"),
        ("{'a': 1}.get('a')", "int | None"),
        ("{'a': 1}.get('a', 0)", "int"),
        ("{'a': 1}.pop('a')", "int"),
        ("{'a': 1}.pop('a', 'x')", "int | str"),
        ("{'a': 1}.popitem()", "tuple[str, int]"),
        ("{'a': 1}.copy()", "dict[str, int]"),
        ("{'a': 1}.setdefault('b')", "int"),
        ("{'a': 1}.update({'b': 2})", "None"),
        ("{'a': 1}.keys()", None),
        ("[1, 2].copy()", "list[int]"),
        ("[1].pop()", "int"),
        ("[1].append(2)", "None"),
        ("[1].index(1)", "int"),
        ("{'a', 'b'}.copy()", "set[str]"),
        ("{'a', 'b'}.pop()", "str"),
    ],
)
def test_builtin_calls(*, text: str, expected: str | None) -> None:
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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("list((x * 2 for x in xs))", "list[int]"),
        ("tuple(xs)", "tuple[int, ...]"),
        ("set(data.values())", "set[int]"),
        ("tuple(data.items())", "tuple[tuple[str, int], ...]"),
        ("[x for x in (1, 's')]", "list[int | str]"),
        ("[v for v in data.missing()]", None),
        ("[v for v in data.items(1)]", None),
        ("[v for v in enumerate(xs, iterable=xs)]", None),
        ("[v for v in enumerate() ]", None),
        ("[v for v in enumerate(xs, nonsense=True)]", None),
        ("list(enumerate(xs))", "list[tuple[int, int]]"),
        ("{k: v for k, v in enumerate(xs)}", "dict[int, int]"),
        ("{k: v for k, v in enumerate(iterable=xs)}", "dict[int, int]"),
        ("[v for k, v in data.items()]", "list[int]"),
        ("[k for k in data.keys()]", "list[str]"),
        ("[v for v in data.values()]", "list[int]"),
        ("[k for k in data]", "list[str]"),
        ("[x for x in b'abc']", "list[int]"),
        ("[b for a, (b, c) in pairs]", "list[int]"),
        ("[x + y for x in xs for y in xs]", "list[int]"),
        ("(x * 3 for x in xs)", "Generator[int]"),
        ("{k: v for k, v in unknown}", None),
        ("[v for k, v in xs]", None),
        ("[a for a, b, c in pairs]", None),
        ("[x for x, y in unknown]", None),
        ("[x for x in xs if x > 0]", "list[int]"),
    ],
)
def test_comprehension_item_bindings(
    *,
    text: str,
    expected: str | None,
) -> None:
    """Preserve iterable item structure without borrowing shadowed names.

    Args:
        text (str): Comprehension to analyse.
        expected (str | None): Proven result or a deliberate refusal.

    """
    expect_equal(
        actual=expression_type(
            node=parse(source=text, mode="eval").body,
            counts={},
            env={
                "xs": "list[int]",
                "data": "dict[str, int]",
                "pairs": "list[tuple[str, tuple[int, bool]]]",
                "x": "str",
            },
        ),
        expected=expected,
    )


def test_shadowed_enumerate_does_not_supply_tuple_items() -> None:
    """A rebound builtin must not manufacture index and value bindings."""
    expect_equal(
        actual=expression_type(
            node=parse(
                source="{k: v for k, v in enumerate(xs)}",
                mode="eval",
            ).body,
            counts={"enumerate": 1},
            env={"xs": "list[int]"},
        ),
        expected=None,
    )
