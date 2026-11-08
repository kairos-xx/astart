"""The untyped-to-typed conversion benchmark keeps its accepted baseline."""

from __future__ import annotations

from pathlib import Path
from typing import Final, final

import pytest
from astart.rules.recovery import variable_map

from benchmarks.pair import Mode, compare
from tests.expectations import expect_equal, expect_true


@final
class Constants:
    """Constants used in the test_bench_pair module.

    Attributes:
        pairs: Directory holding the typed/untyped fixture pairs.
        baseline_correct: Correct annotations the stored baseline records.
        most_contradictions: Most contradictions tolerated before failing.

    """

    pairs: Final[Path] = Path(__file__).parent / "pairs"
    baseline_correct: Final[int] = 71
    most_contradictions: Final[int] = 2


def _read(*, name: str) -> str:
    """Read one half of the pair.

    Args:
        name: File name inside ``tests/pairs``.

    Returns:
        The file text.

    """
    return (Constants.pairs / name).read_text(encoding="utf-8")


def test_variable_map_reads_annotated_names_by_scope() -> None:
    """Check that variable annotations are keyed by their scope."""
    found: dict[str, str] = variable_map(
        source=(
            "x: int = 1\ndef f():\n    y: str = ''\nclass C:\n    z: float\n"
        ),
    )
    expect_equal(
        actual=found,
        expected={"x": "int", "f.y": "str", "C.z": "float"},
    )


@pytest.mark.slow
def test_conversion_never_regresses_and_never_contradicts() -> None:
    """Check recall stays at the baseline and nothing contradicts the twin."""
    result: dict[str, dict[str, int]] = compare(
        untyped=_read(name="resolver_extended_untyped.py.txt"),
        typed=_read(name="resolver_extended_typed.py.txt"),
        mode=Mode(floor=0.8),
    )
    recovered: dict[str, int] = result["parameters_and_returns"]
    expect_true(condition=recovered["correct"] >= Constants.baseline_correct)
    expect_true(condition=recovered["wrong"] <= Constants.most_contradictions)
