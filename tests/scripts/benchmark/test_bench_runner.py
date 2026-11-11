"""The benchmark runner's per-kind and per-basis attribution (M2-13, F-29)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from scripts.benchmark.runner import Plan, run_recovery
from tests.support.expectations import (
    expect_equal,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.benchmark.report import ModuleResult, Report


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source (Final[str]): Typed mini-module with a plain function and a
            method.
        methods_recovered (Final[int]): Least method annotations the run must
            recover.

    """

    source: Final[str] = '''\
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


class Bag:
    """A container with an annotated method."""

    def put(self, item: str) -> None:
        """Store ``item``."""
        self.item = item
'''
    methods_recovered: Final[int] = 1


def test_runner_splits_recovery_counts_by_kind(tmp_path: Path) -> None:
    """Check ``by_kind`` attributes function keys and method keys separately.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    source: Path = tmp_path / "mod.py"
    _ = source.write_text(data=Constants.source, encoding="utf-8")
    report: Report = run_recovery(
        paths=[source],
        plan=Plan(attribute=False, negotiate=True),
    )
    by_kind: dict[str, dict[str, int]] = {
        score.kind: {
            "truth": score.truth,
            "correct": score.correct,
            "wrong": score.wrong,
            "compatible": score.compatible,
        }
        for score in report.modules[0].by_kind
    }
    expect_equal(actual=by_kind["function"]["truth"], expected=3)
    expect_equal(actual=by_kind["method"]["truth"], expected=2)
    expect_true(
        condition=by_kind["method"]["correct"] >= Constants.methods_recovered,
    )
    aggregate: dict[str, int] = {
        kind: score.correct for kind, score in report.by_kind.items()
    }
    expect_equal(
        actual=aggregate.get("function", 0) + aggregate.get("method", 0),
        expected=report.correct,
    )


def test_runner_records_hint_bases_for_written_annotations(
    tmp_path: Path,
) -> None:
    """Check ``by_basis`` counts every recorded annotation once.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    source: Path = tmp_path / "mod.py"
    _ = source.write_text(data=Constants.source, encoding="utf-8")
    report: Report = run_recovery(
        paths=[source],
        plan=Plan(attribute=False, negotiate=True),
    )
    module: ModuleResult = report.modules[0]
    written: int = (
        module.correct
        + len(module.wrong)
        + len(module.compatible)
        + module.synthesized
    )
    by_basis: dict[str, int] = dict(module.by_basis)
    expect_equal(actual=sum(by_basis.values()), expected=written)
    if written:
        expect_true(
            condition=any(
                basis
                in (
                    "proven_none",
                    "call_sites",
                    "negotiated",
                    "engine",
                    "derived_return",
                    "syntax_proven",
                    "optional_default",
                    "attribute_assignments",
                    "protocol_result",
                    "union_sites",
                    "default_literal",
                    "calibrated_candidate",
                    "synthesized",
                    "unattributed",
                )
                for basis in by_basis
            ),
        )
    expect_true(condition=len(report.by_basis) > 0)
