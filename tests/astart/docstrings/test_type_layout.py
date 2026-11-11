"""Compact rendering of type expressions for docstring labels."""

from __future__ import annotations

from typing import Final, final

from astart.docstrings.type_layout import compact_type

from tests.support.expectations import expect_equal, expect_true


@final
class Constants:
    """Constants for the test.

    Attributes:
        cases (Final[tuple[tuple[str, str], ...]]): ``(source, compact)`` pairs
            that must round-trip.

    """

    cases: Final[tuple[tuple[str, str], ...]] = (
        (
            "tuple[tuple[str, str, int], ...]",
            "tuple[tuple[str,str,int],...]",
        ),
        (
            "tuple[TypeExpression, ...] | EllipsisExpression",
            "tuple[TypeExpression,...]|EllipsisExpression",
        ),
        (
            "Module | FunctionDef | AsyncFunctionDef | ClassDef",
            "Module|FunctionDef|AsyncFunctionDef|ClassDef",
        ),
        (
            "dict[str, tuple[tuple[str, ...], bool, tuple[str, ...], bool]]",
            "dict[str,tuple[tuple[str,...],bool,tuple[str,...],bool]]",
        ),
        ("Literal['a, b'] | None", "Literal['a, b']|None"),
        (
            "list[tuple[str, expr | None, bool]]",
            "list[tuple[str,expr|None,bool]]",
        ),
    )


def test_compact_type_removes_cosmetic_whitespace() -> None:
    """Check each type expression compacts to its minimal spacing."""
    for source, expected in Constants.cases:
        expect_equal(
            actual=compact_type(type_text=source),
            expected=expected,
        )


def test_compact_type_preserves_string_literal_content() -> None:
    """Whitespace inside ``Literal`` strings is content, not layout."""
    actual: str | None = compact_type(type_text="Literal['a,  b']")
    expect_equal(actual="Literal['a,  b']", expected=actual)


def test_compact_type_rejects_unparseable_text() -> None:
    """Non-expression text yields ``None`` instead of a guess."""
    expect_true(
        condition=compact_type(type_text="not a type !") is None,
    )
