"""The ``perf`` throughput gate: comparison, serialization and CLI wiring."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, Final, final

import pytest

from scripts.benchmark import cli
from scripts.benchmark import paths as benchmark_paths
from scripts.benchmark.cli import main
from scripts.benchmark.throughput import (
    BucketEntry,
    PerfReport,
    compare_perf,
    format_table,
    from_json,
    measure_bucket,
    to_json,
)
from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        baseline_file (Final[Path]): The shipped perf baseline.
        python_key (Final): Serialization key carrying the interpreter version.

    """

    baseline_file: Final[Path] = (
        Paths.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "baseline_perf.json"
    )
    python_key: Final = "python"


@pytest.fixture(autouse=True)
def isolated_artifacts(
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


def _entry(*, seconds: float, lines: int = 100) -> BucketEntry:
    """Build a bucket entry with the given median.

    Args:
        seconds (float): Median seconds to record.
        lines (int): Actual workload lines.

    Returns:
        BucketEntry: The bucket entry.

    """
    return {
        "lines": 100,
        "actual_lines": lines,
        "median_seconds": seconds,
    }


def _report(*, buckets: Mapping[str, BucketEntry]) -> PerfReport:
    """Build a perf report around the given buckets.

    Args:
        buckets (Mapping[str, BucketEntry]): Bucket entries keyed by target
            size string.

    Returns:
        PerfReport: The perf report.

    """
    return {"python": "3.13.9", "buckets": dict(buckets)}


def test_compare_perf_passes_within_twenty_percent() -> None:
    """Check a bucket at the slowdown boundary still passes."""
    problems: tuple[str, ...] = compare_perf(
        current={"1000": _entry(seconds=1.2)},
        baseline={"1000": _entry(seconds=1.0)},
    )
    expect_equal(actual=problems, expected=())


def test_compare_perf_fails_past_the_bound_and_ignores_new_buckets() -> None:
    """Check a >20% regression is reported and unbaselined buckets pass."""
    problems: tuple[str, ...] = compare_perf(
        current={
            "1000": _entry(seconds=1.21),
            "4000": _entry(seconds=99.0),
        },
        baseline={"1000": _entry(seconds=1.0)},
    )
    expect_equal(actual=len(problems), expected=1)
    expect_in(item="bucket 1000", container=problems[0])
    expect_in(item="20%", container=problems[0])
    expect_false(
        condition=any("4000" in problem for problem in problems),
    )


def test_serialization_round_trips() -> None:
    """Check ``to_json``/``from_json`` keep buckets and the python key."""
    report: PerfReport = _report(
        buckets={"1000": _entry(seconds=1.5)},
    )
    decoded: PerfReport = from_json(text=to_json(report=report))
    expect_equal(actual=decoded, expected=report)


def test_format_table_lists_buckets_and_na_baseline() -> None:
    """Check the table renders each bucket and ``n/a`` without a baseline."""
    table: str = format_table(
        current={
            "1000": _entry(seconds=1.0),
            "4000": _entry(seconds=4.0),
        },
        baseline={"1000": _entry(seconds=1.0)},
    )
    expect_in(item="median_s", container=table)
    expect_in(item="1000", container=table)
    expect_in(item="4000", container=table)
    expect_in(item="n/a", container=table)


def test_shipped_baseline_loads_with_all_buckets() -> None:
    """Check ``baseline_perf.json`` parses and covers the three buckets."""
    baseline: PerfReport = from_json(
        text=Constants.baseline_file.read_text(encoding="utf-8"),
    )
    expect_equal(
        actual=sorted(baseline["buckets"], key=int),
        expected=["1000", "4000", "12000"],
    )
    expect_true(condition=bool(baseline[Constants.python_key]))
    for entry in baseline["buckets"].values():
        expect_true(condition=entry["median_seconds"] > 0)
        expect_true(condition=entry["actual_lines"] > 0)


def test_measure_bucket_reports_shape() -> None:
    """Check one real measurement returns a well-formed bucket entry."""
    entry: BucketEntry = measure_bucket(lines=200, runs=1)
    expect_equal(actual=entry["lines"], expected=200)
    expect_true(condition=entry["actual_lines"] > 0)
    expect_true(condition=entry["median_seconds"] > 0)


def test_perf_command_passes_and_writes_json(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check ``perf`` prints PASS and persists the report when clean.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): pytest fixture patching the real
            measurement.

    """
    baseline: Path = tmp_path / "baseline_perf.json"
    _ = baseline.write_text(
        data=to_json(report=_report(buckets={"1000": _entry(seconds=1.0)})),
        encoding="utf-8",
    )
    out_file: Path = tmp_path / "perf.json"

    def _fake_measure(*, runs: int) -> PerfReport:
        """Return a canned report ignoring the run count.

        Args:
            runs (int): Unused run count.

        Returns:
            PerfReport: A report with one measured bucket.

        """
        _: int = runs
        return _report(buckets={"1000": _entry(seconds=1.1)})

    monkeypatch.setattr(target=cli, name="measure_all", value=_fake_measure)
    out: StringIO = StringIO()
    code: int = main(
        argv=[
            "perf",
            "--baseline",
            str(object=baseline),
            "--json",
            str(object=out_file),
        ],
        out=out,
    )
    expect_equal(actual=code, expected=0)
    expect_in(item="PASS", container=out.getvalue())
    decoded: PerfReport = loads(s=out_file.read_text(encoding="utf-8"))
    expect_equal(
        actual=decoded["buckets"]["1000"]["median_seconds"],
        expected=1.1,
    )


def test_perf_command_fails_and_update_writes_baseline(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check ``perf`` exits 1 on regression and ``--update`` rewrites it.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): pytest fixture patching the real
            measurement.

    """
    baseline: Path = tmp_path / "baseline_perf.json"
    _ = baseline.write_text(
        data=to_json(report=_report(buckets={"1000": _entry(seconds=1.0)})),
        encoding="utf-8",
    )

    def _fake_measure(*, runs: int) -> PerfReport:
        """Return a canned report ignoring the run count.

        Args:
            runs (int): Unused run count.

        Returns:
            PerfReport: A report with one measured bucket.

        """
        _: int = runs
        return _report(buckets={"1000": _entry(seconds=2.0)})

    monkeypatch.setattr(target=cli, name="measure_all", value=_fake_measure)
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=["perf", "--baseline", str(object=baseline)],
            out=out,
        ),
        expected=1,
    )
    expect_in(item="FAIL", container=out.getvalue())
    expect_in(item="bucket 1000", container=out.getvalue())
    expect_equal(
        actual=main(
            argv=[
                "perf",
                "--baseline",
                str(object=baseline),
                "--update",
            ],
            out=out,
        ),
        expected=1,
    )
    updated: PerfReport = from_json(
        text=baseline.read_text(encoding="utf-8"),
    )
    expect_equal(
        actual=updated["buckets"]["1000"]["median_seconds"],
        expected=2.0,
    )
