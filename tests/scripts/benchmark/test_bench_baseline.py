"""The accepted benchmark baseline is well formed and clean."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Final, final

import pytest

from scripts.benchmark import paths as benchmark_paths
from scripts.benchmark.cli import main
from scripts.benchmark.report import Report, from_json
from tests.support.expectations import expect_equal, expect_in, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Constants used in the test_bench_baseline module.

    Attributes:
        baseline (Final[Path]): Path of the stored benchmark baseline.
        precision_gate (Final[float]): Minimum precision the baseline must
            hold.
        min_external_modules (Final[int]): Fewest external modules the corpus
            needs.
        external (Final[Path]): Grouped module constant.

    """

    baseline: Final[Path] = (
        Paths.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "baseline.json"
    )

    precision_gate: Final[float] = 0.995
    min_external_modules: Final[int] = 150

    external: Final[Path] = (
        Paths.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "baseline_ext.json"
    )


@pytest.fixture(autouse=True)
def _isolated_artifacts(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Redirect benchmark artifacts away from the repository.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): pytest fixture patching artifact
            locations.

    """
    monkeypatch.setattr(
        target=benchmark_paths.Paths,
        name="results",
        value=tmp_path / "artifacts",
    )


_ = _isolated_artifacts


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


def test_the_external_baseline_gates_against_itself() -> None:
    """Check that the external-corpus baseline passes its own gate."""
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=Constants.external),
                "--baseline",
                str(object=Constants.external),
            ],
            out=out,
        ),
        expected=0,
    )
    expect_in(item="PASS", container=out.getvalue())


def test_the_external_baseline_stays_above_the_precision_gate() -> None:
    """Check no crashes, no new checker errors and precision >= 99.5 %."""
    report: Report = from_json(
        text=Constants.external.read_text(encoding="utf-8"),
    )
    expect_equal(actual=report.crashed, expected=())
    expect_equal(actual=report.new_errors or 0, expected=0)
    expect_true(condition=report.precision >= Constants.precision_gate)
    expect_true(
        condition=len(report.modules) >= Constants.min_external_modules,
    )
