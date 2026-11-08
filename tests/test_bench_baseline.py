"""The accepted benchmark baseline is well formed and clean."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Final

from benchmarks.__main__ import Constants, main
from benchmarks.report import Report, from_json
from tests.expectations import expect_equal, expect_in

BASELINE: Final[Path] = Path(__file__).parent.parent / Constants.baseline


def test_the_baseline_gates_against_itself() -> None:
    """Check that the stored baseline passes its own gate."""
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=BASELINE),
                "--baseline",
                str(object=BASELINE),
            ],
            out=out,
        ),
        expected=0,
    )
    expect_in(item="PASS", container=out.getvalue())


def test_the_baseline_records_a_clean_gated_run() -> None:
    """Check zero wrong annotations, zero crashes and zero new errors."""
    report: Report = from_json(text=BASELINE.read_text(encoding="utf-8"))
    for item in report.modules:
        expect_equal(actual=len(item.wrong), expected=0, message=item.name)
        expect_equal(actual=item.crash, expected=None, message=item.name)
        expect_equal(
            actual=item.new_errors or 0,
            expected=0,
            message=item.name,
        )
