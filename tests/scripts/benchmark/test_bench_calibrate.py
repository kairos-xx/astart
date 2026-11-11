"""Unit tests for ``scripts.benchmark.calibrate`` split and share math."""

from __future__ import annotations

from scripts.benchmark.calibrate import exact, halves, shares
from scripts.benchmark.report import ModuleResult
from tests.support.expectations import expect_equal


def _module(
    *,
    name: str,
    outcomes: tuple[tuple[str, str, int], ...],
) -> ModuleResult:
    """Build a module result carrying only basis outcomes.

    Args:
        name (str): Module file name.
        outcomes (tuple[tuple[str,str,int],...]): ``(basis, outcome, count)``
            triples.

    Returns:
        ModuleResult: The module result.

    """
    return ModuleResult(
        name=name,
        truth=0,
        correct=0,
        wrong=(),
        synthesized=0,
        seconds=0.0,
        rounds=0,
        missed_reasons=(),
        new_errors=None,
        crash=None,
        basis_outcomes=outcomes,
    )


def test_halves_interleave_sorted_names() -> None:
    """Check that halves alternate over name-sorted modules."""
    modules: list[ModuleResult] = [
        _module(name=name, outcomes=())
        for name in ("d.py", "a.py", "c.py", "b.py")
    ]
    first, second = halves(modules=modules)
    expect_equal(
        actual=[item.name for item in first],
        expected=["a.py", "c.py"],
    )
    expect_equal(
        actual=[item.name for item in second],
        expected=["b.py", "d.py"],
    )


def test_shares_aggregates_scored_outcomes() -> None:
    """Check that only scored outcomes count toward a basis share."""
    modules: list[ModuleResult] = [
        _module(
            name="m.py",
            outcomes=(
                ("engine", "correct", 3),
                ("engine", "wrong", 1),
                ("engine", "compatible", 2),
                ("engine", "synthesized", 5),
                ("negotiated", "correct", 4),
            ),
        ),
    ]
    _shares_result: dict[str, tuple[int, int, int]] = shares(modules=modules)
    expect_equal(actual=_shares_result["engine"], expected=(3, 1, 2))
    expect_equal(actual=_shares_result["negotiated"], expected=(4, 0, 0))


def test_exact_share_is_a_percentage() -> None:
    """Check the exact-share formula and the empty case."""
    expect_equal(actual=exact(counts=(3, 1, 0)), expected=75.0)
    expect_equal(actual=exact(counts=(0, 0, 0)), expected=0.0)
