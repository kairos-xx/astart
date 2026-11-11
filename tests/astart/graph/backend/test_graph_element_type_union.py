"""The element type of a union of containers is the merge of their elements."""

from __future__ import annotations

import pytest
from astart.graph.backend.refiner import element_type

from tests.support.expectations import expect_equal


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("list[int]", "int"),
        ("list[int] | list[tuple[str, int]]", "int | tuple[str, int]"),
        ("set[str] | list[str]", "str"),
        ("list[int] | None", "int"),
        ("dict[str, int]", "str"),
        ("tuple[int, ...]", "int"),
    ],
)
def test_element_type(*, source: str, expected: str) -> None:
    """Check the element type, including for unions of containers.

    Args:
        source (str): Container annotation text.
        expected (str): Expected element annotation text.

    """
    expect_equal(actual=element_type(source=source), expected=expected)
