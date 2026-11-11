"""Union and intersection of annotation sources."""

from __future__ import annotations

from typing import Final, final

import pytest
from astart.rules.negotiation import Intersection, TypeAlgebra

from tests.support.expectations import expect_equal, expect_false, expect_true


@final
class Constants:
    """Constants for the test.

    Attributes:
        algebra (Final[TypeAlgebra]): Shared type algebra the parametrized
            cases run against.

    """

    algebra: Final[TypeAlgebra] = TypeAlgebra()


@pytest.mark.parametrize(
    ("types", "expected"),
    [
        (["int", "str"], "int | str"),
        (["str", "int"], "int | str"),
        (["int", "int"], "int"),
        (["bool", "int"], "int"),
        (["int", "bool"], "int"),
        (["None", "int"], "int | None"),
        (["int | None", "str"], "int | str | None"),
        (["Never", "int"], "int"),
        (["object", "int"], "object"),
        (["Literal['x']", "str"], "str"),
        (["Literal[1]", "int"], "int"),
        (["Literal[True]", "int"], "int"),
        (["Literal['x']", "int"], "int | Literal['x']"),
        (["list[int]", "dict[str, int]"], "dict[str, int] | list[int]"),
        (["int", "str", "bytes", "float"], None),
        ([], None),
    ],
)
def test_union(*, types: list[str], expected: str | None) -> None:
    """Check the normalized union of several types.

    Args:
        types (list[str]): Input annotation sources.
        expected (str | None): Normalized union, or ``None`` when refused.

    """
    expect_equal(
        actual=Constants.algebra.union(types=types, limit=3),
        expected=expected,
    )


def test_union_does_not_depend_on_input_order() -> None:
    """Check that every permutation yields the same text."""
    first: str | None = Constants.algebra.union(
        types=["str", "None", "int"],
        limit=3,
    )
    second: str | None = Constants.algebra.union(
        types=["None", "int", "str"],
        limit=3,
    )
    expect_equal(actual=first, expected=second)


@pytest.mark.parametrize(
    ("left", "right", "expected", "decided"),
    [
        ("int", "int", "int", True),
        ("object", "str", "str", True),
        ("int", "bool", "bool", True),
        ("float", "int", "int", True),
        ("int | None", "int", "int", True),
        ("int | str", "str", "str", True),
        ("int", "str", None, True),
        ("None", "int", None, True),
        ("list[int]", "list", "list[int]", True),
        ("list[int | str]", "list[str]", "list[str]", True),
        ("list[int]", "list[str]", None, True),
        ("list[int]", "dict[str, int]", None, True),
        ("Foo", "Bar", None, False),
        ("Foo", "int", None, False),
        ("None", "Foo", None, False),
    ],
)
def test_intersection(
    *,
    left: str,
    right: str,
    expected: str | None,
    decided: bool,
) -> None:
    """Check narrowing, emptiness and undecided user classes.

    Args:
        left (str): Type believed so far.
        right (str): Narrowing type.
        expected (str | None): Narrowed type, or ``None``.
        decided (bool): Whether the algebra knows the answer.

    """
    result: Intersection = Constants.algebra.intersect(left=left, right=right)
    expect_equal(actual=result.type_text, expected=expected)
    expect_equal(actual=result.decided, expected=decided)


def test_members_flattens_nested_unions() -> None:
    """Check that members come out flat and deduplicated."""
    expect_equal(
        actual=Constants.algebra.members(source="int | (str | int)"),
        expected=("int", "str"),
    )


def test_unparsable_text_is_one_member() -> None:
    """Check that garbage is kept whole instead of raising."""
    expect_equal(
        actual=Constants.algebra.members(source="in t"),
        expected=("in t",),
    )
    expect_true(
        condition=Constants.algebra.intersect(left="in t", right="int").decided
        is False,
    )
    expect_false(
        condition=Constants.algebra.intersect(
            left="int",
            right="str",
        ).type_text
        is not None,
    )


@pytest.mark.parametrize(
    ("current", "removed", "expected"),
    [
        ("int | str", "int", "str"),
        ("int | str | None", "int", "str | None"),
        ("int | str", "int | str", None),
        ("int | str", "bytes", "int | str"),
        ("int | str", "bool", "int | str"),
        ("bool | str", "int", "str"),
        ("int", "bool", "int"),
        ("None | int", "None", "int"),
        ("Literal[1] | str", "int", "str"),
        ("list[int] | dict[str, int]", "list", "dict[str, int]"),
        ("list[int] | str", "list[int]", "str"),
        ("int | str", "Foo", "int | str"),
        ("Foo | str", "int", "str | Foo"),
        ("int | str", "int & str", "int | str"),
        ("bool | str", "int & bool", "str"),
        ("int | str | bytes", "int & bytes", "int | str | bytes"),
    ],
)
def test_subtract(
    *,
    current: str,
    removed: str,
    expected: str | None,
) -> None:
    """Check that complement narrowing drops only covered members.

    Args:
        current (str): The type believed so far.
        removed (str): The excluded type.
        expected (str | None): What remains, or ``None`` when nothing does.

    """
    expect_equal(
        actual=Constants.algebra.subtract(current=current, removed=removed),
        expected=expected,
    )
