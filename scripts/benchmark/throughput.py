"""Measure ``fix_source`` throughput across workload size buckets.

Builds workloads of 1 k, 4 k and 12 k lines by concatenating corpus modules,
times ``fix_source`` over three runs per bucket, and keeps the median.

"""

from __future__ import annotations

from json import dumps, loads
from pathlib import Path
from statistics import median
from sys import version_info
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import TYPE_CHECKING, Final, TypedDict, final

from astart.rules import default_registries
from astart.rules.catalog import load_default_catalog
from astart.rules.runner import FixSettings, fix_source
from astart.rules.vocabulary import FixSafety

from scripts.benchmark.profile_perf import build_workload

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        buckets (Final[tuple[int, ...]]): Default line-count buckets to
            measure.
        runs (Final[int]): Number of timed runs per bucket (median kept).
        baseline (Final[Path]): Default baseline file path.
        max_slowdown (Final[float]): Allowed relative slowdown over the
            baseline (20%).
        indent (Final[int]): JSON indentation spaces.

    """

    buckets: Final[tuple[int, ...]] = (1_000, 4_000, 12_000)
    runs: Final[int] = 3
    baseline: Final[Path] = Path(
        "scripts/benchmark/artifacts/resources/baseline_perf.json",
    )
    max_slowdown: Final[float] = 0.20
    indent: Final[int] = 2


class BucketEntry(TypedDict):
    """Serialized measurement for one line-count bucket.

    Attributes:
        lines (int): Target line count of the bucket.
        actual_lines (int): Actual line count of the constructed workload.
        median_seconds (float): Median ``fix_source`` duration in seconds.

    """

    lines: int
    actual_lines: int
    median_seconds: float


class PerfReport(TypedDict):
    """Serialized throughput report.

    Attributes:
        python (str): Running Python ``major.minor.micro`` version string.
        buckets (dict[str, BucketEntry]): Measurements keyed by target bucket
            size string.

    """

    python: str
    buckets: dict[str, BucketEntry]


def measure_bucket(*, lines: int, runs: int = Constants.runs) -> BucketEntry:
    """Time ``fix_source`` on a synthetic workload of ``lines`` lines.

    Args:
        lines (int): Minimum target line count.
        runs (int): Number of timed repetitions; the median is returned.

    Returns:
        BucketEntry:
            The bucket entry with actual line count and median seconds.

    """
    source: str = build_workload(lines=lines)
    actual_lines: int = source.count("\n")
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    samples: list[float] = []
    with TemporaryDirectory() as directory:
        stubs_path: Path = Path(directory)
        settings: FixSettings = FixSettings(
            ceiling=FixSafety.guarded,
            stubs_path=stubs_path,
        )
        for _ in range(max(1, runs)):
            started: float = perf_counter()
            _ = fix_source(
                source=source,
                filename="workload.py",
                catalog=catalog,
                registries=registries,
                settings=settings,
            )
            samples.append(perf_counter() - started)
    return {
        "lines": lines,
        "actual_lines": actual_lines,
        "median_seconds": round(number=median(data=samples), ndigits=3),
    }


def measure_all(
    *,
    buckets: Sequence[int] = Constants.buckets,
    runs: int = Constants.runs,
) -> PerfReport:
    """Measure all requested line-count buckets.

    Args:
        buckets (Sequence[int]): Target line counts to benchmark.
        runs (int): Repetitions per bucket.

    Returns:
        PerfReport: The complete throughput report with
            Python version and bucket medians.

    """
    measured: dict[str, BucketEntry] = {
        str(object=size): measure_bucket(lines=size, runs=runs)
        for size in buckets
    }
    version_text: str = (
        f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    )
    return {
        "python": version_text,
        "buckets": measured,
    }


def to_json(*, report: PerfReport) -> str:
    """Serialize a throughput report to JSON.

    Args:
        report (PerfReport): The throughput report.

    Returns:
        str: Formatted JSON string.

    """
    return dumps(obj=report, indent=Constants.indent, sort_keys=True)


def from_json(*, text: str) -> PerfReport:
    """Load a serialized throughput report from JSON.

    Args:
        text (str): JSON document string.

    Returns:
        PerfReport: Decoded throughput report.

    """
    raw: PerfReport = loads(s=text)
    return raw


def compare_perf(
    *,
    current: Mapping[str, BucketEntry],
    baseline: Mapping[str, BucketEntry],
    max_slowdown: float = Constants.max_slowdown,
) -> tuple[str, ...]:
    """Compare measured bucket medians against the stored baseline.

    Args:
        current (Mapping[str, BucketEntry]): Newly measured buckets keyed by
            size string.
        baseline (Mapping[str, BucketEntry]): Baseline buckets keyed by size
            string.
        max_slowdown (float): Maximum allowed fractional increase over
            baseline.

    Returns:
        tuple[str, ...]: Problem descriptions for any bucket
            slower than allowed; empty when clean.

    """
    problems: list[str] = []
    for key, entry in current.items():
        base_entry: BucketEntry | None = baseline.get(key)
        if base_entry is None:
            continue
        limit: float = base_entry["median_seconds"] * (1.0 + max_slowdown)
        actual: float = entry["median_seconds"]
        if actual > limit:
            problems.append(
                f"bucket {key} lines took {actual:.3f}s, "
                f"exceeding baseline {base_entry['median_seconds']:.3f}s "
                f"by more than {max_slowdown * 100:.0f}% (limit {limit:.3f}s)",
            )
    return tuple(problems)


def format_table(
    *,
    current: Mapping[str, BucketEntry],
    baseline: Mapping[str, BucketEntry],
) -> str:
    """Format a human-readable comparison table of throughput buckets.

    Args:
        current (Mapping[str, BucketEntry]): Measured bucket entries.
        baseline (Mapping[str, BucketEntry]): Baseline bucket entries.

    Returns:
        str: Multi-line table string.

    """
    lines: list[str] = [
        f"{'bucket':>8} {'lines':>8} {'median_s':>10} {'baseline_s':>12}",
    ]
    for key in sorted(current, key=int):
        entry: BucketEntry = current[key]
        base_entry: BucketEntry | None = baseline.get(key)
        base_text: str = (
            f"{base_entry['median_seconds']:.3f}"
            if base_entry is not None
            else "n/a"
        )
        lines.append(
            f"{key:>8} {entry['actual_lines']:>8} "
            f"{entry['median_seconds']:>10.3f} {base_text:>12}",
        )
    return "\n".join(lines) + "\n"
