"""Keep generic alias and variadic tuple report comparisons accurate."""

from __future__ import annotations

import pytest
from astart.rules.recovery import Context, module_context, relation

from tests.support.expectations import expect_equal


@pytest.mark.parametrize(
    argnames=("written", "truth", "expected"),
    argvalues=[
        ("list[int]", "Vec[int]", None),
        ("Callable[P, R]", "Fn[P, R]", None),
        ("tuple[list[int], list[int]]", "Vectors", "narrower"),
        ("tuple[int, int, str]", "tuple[*tuple[int, ...], str]", "narrower"),
        ("tuple[int, str]", "tuple[int, ...]", "contradiction"),
        ("tuple[int, ...]", "tuple[int, int]", "looser"),
        (
            "tuple[int | None, int | None]",
            "tuple[int | None, ...]",
            "narrower",
        ),
        ("tuple[()]", "tuple[int, ...]", "narrower"),
        ("tuple[int, ...]", "tuple[()]", "looser"),
        (
            "tuple[int | None, ...]",
            "tuple[int, ...] | tuple[None, ...]",
            "looser",
        ),
    ],
)
def test_generic_aliases_and_tuple_length_contracts(
    *,
    written: str,
    truth: str,
    expected: str | None,
) -> None:
    """Distinguish equivalent aliases, safe narrowing and incompatible tuples.

    Args:
        written (str): Actual annotation emitted by inference.
        truth (str): Curated reference contract.
        expected (str | None): Independently specified relationship.

    """
    context: Context = module_context(
        source=(
            "from collections.abc import Callable\n"
            "type Vec[T] = list[T]\n"
            "type Vectors = tuple[Vec[int], ...]\n"
            "type Fn[**P, R] = Callable[P, R]\n"
        ),
    )
    expect_equal(
        actual=relation(written=written, truth=truth, context=context),
        expected=expected,
    )
