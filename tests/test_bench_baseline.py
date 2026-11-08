"""The accepted benchmark baseline is well formed and clean."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Final, final

from benchmarks.__main__ import main
from benchmarks.report import Report, from_json
from tests.expectations import expect_equal, expect_in, expect_true


@final
class Constants:
    """Constants used in the test_bench_baseline module.

    Attributes:
        baseline: Path of the stored benchmark baseline.
        precision_gate: Minimum precision the baseline must hold.
        min_external_modules: Fewest external modules the corpus needs.

    """

    baseline: Final[Path] = (
        Path(__file__).parent.parent / "benchmarks" / "baseline.json"
    )

    precision_gate: Final[float] = 0.995
    min_external_modules: Final[int] = 150


def test_the_baseline_gates_against_itself() -> None:
    """Check that the stored baseline passes its own gate."""
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=Constants.baseline),
                "--baseline",
                str(object=Constants.baseline),
            ],
            out=out,
        ),
        expected=0,
    )
    expect_in(item="PASS", container=out.getvalue())


def test_the_baseline_records_a_clean_gated_run() -> None:
    """Check zero wrong annotations, zero crashes and zero new errors."""
    report: Report = from_json(
        text=Constants.baseline.read_text(encoding="utf-8"),
    )
    for item in report.modules:
        expect_equal(actual=len(item.wrong), expected=0, message=item.name)
        expect_equal(actual=item.crash, expected=None, message=item.name)
        expect_equal(
            actual=item.new_errors or 0,
            expected=0,
            message=item.name,
        )


EXTERNAL: Final[Path] = (
    Path(__file__).parent.parent / "benchmarks" / "baseline_ext.json"
)


def test_the_external_baseline_gates_against_itself() -> None:
    """Check that the external-corpus baseline passes its own gate."""
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=EXTERNAL),
                "--baseline",
                str(object=EXTERNAL),
            ],
            out=out,
        ),
        expected=0,
    )
    expect_in(item="PASS", container=out.getvalue())


def test_the_external_baseline_stays_above_the_precision_gate() -> None:
    """Check no crashes, no new checker errors and precision >= 99.5 %."""
    report: Report = from_json(
        text=EXTERNAL.read_text(encoding="utf-8"),
    )
    expect_equal(actual=report.crashed, expected=())
    expect_equal(actual=report.new_errors or 0, expected=0)
    expect_true(condition=report.precision >= Constants.precision_gate)
    expect_true(
        condition=len(report.modules) >= Constants.min_external_modules,
    )
