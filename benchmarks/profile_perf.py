"""Profile the analysis pipeline on a large synthetic workload.

Concatenates corpus modules into one ``~12k``-line source, then times
``check`` and ``fix_source`` and prints the ``cProfile`` hot list.
``--json`` emits a machine-readable row for ``docs/benchmarks.md``.

Usage::

    PYTHONPATH=src python -m benchmarks.profile_perf [--lines 12000]
        [--json] [--top 25] [--profile]
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from cProfile import Profile
from dataclasses import replace
from io import StringIO
from json import dumps
from pathlib import Path
from pstats import Stats
from sys import stdout
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import TYPE_CHECKING, Final, final

from astart.rules import default_registries
from astart.rules.catalog import load_default_catalog
from astart.rules.engine import CheckOptions, CheckResult, check
from astart.rules.runner import FixResult, FixSettings, fix_source
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Sequence

    from astart.rules.model import Catalog


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus: Directory of corpus ``.py.txt`` modules.
        target_lines: Default workload size.
        top: Default number of profile rows printed.
        fix_keys: Fix keys the timed fix run offers.

    """

    corpus: Final[Path] = Path(__file__).parent.parent / "tests" / "corpus"
    target_lines: Final[int] = 12_000
    top: Final[int] = 25
    fix_keys: Final[tuple[str, ...]] = (
        "typing.add-none-return",
        "typing.add-inferred-annotation",
    )


def build_workload(*, lines: int) -> str:
    """Concatenate corpus modules into one source of ``lines`` lines.

    Each module is wrapped in a uniquely-named function so the combined
    source remains valid and gives every rule real subjects.

    Args:
        lines: Minimum total line count.

    Returns:
        The combined source text.

    """
    parts: list[str] = []
    used: int = 0
    index: int = 0
    files: list[Path] = sorted(Constants.corpus.glob(pattern="*.py.txt"))
    while used < lines:
        path: Path = files[index % len(files)]
        index += 1
        text: str = path.read_text(encoding="utf-8")
        indent: str = "\n".join(
            f"    {line}" if line.strip() else line
            for line in text.splitlines()
        )
        parts.append(f"def workload_{index}():\n{indent}\n\n")
        used += text.count("\n") + 3
    return "".join(parts)


def run(*, source: str, stubs_path: Path) -> dict[str, float]:
    """Time the check and fix stages on a workload.

    Args:
        source: Combined source text.
        stubs_path: Stub directory (empty temporary dir is fine).

    Returns:
        Seconds per stage plus finding/offer counts.

    """
    catalog: Catalog = load_default_catalog(
        registries=default_registries(),
    )
    started: float = perf_counter()
    result: CheckResult = check(
        source=source,
        filename="workload.py",
        catalog=catalog,
        registries=default_registries(),
        options=CheckOptions(stubs_path=stubs_path),
    )
    check_seconds: float = perf_counter() - started
    fixed: FixResult = fix_source(
        source=source,
        filename="workload.py",
        catalog=_fix_catalog(catalog=catalog),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            stubs_path=stubs_path,
        ),
    )
    fix_seconds: float = perf_counter() - started - check_seconds
    return {
        "lines": float(source.count("\n")),
        "check_seconds": check_seconds,
        "fix_seconds": fix_seconds,
        "total_seconds": check_seconds + fix_seconds,
        "findings": float(len(result.findings)),
        "applied": float(len(fixed.applied)),
        "skipped": float(len(fixed.skipped)),
    }


def _fix_catalog(*, catalog: Catalog) -> Catalog:
    """Restrict a catalog to the annotation fixes being timed.

    Args:
        catalog: Full catalog.

    Returns:
        A catalog offering only the annotation fixes.

    """
    allowed: set[str] = set(Constants.fix_keys)
    return replace(
        catalog,
        rules=tuple(
            replace(
                rule,
                fixes=tuple(key for key in rule.fixes if key in allowed),
            )
            for rule in catalog.rules
            if rule.code == "TYP003"
        ),
        fixes=tuple(f for f in catalog.fixes if f.key in allowed),
    )


def _profile(*, source: str, stubs_path: Path, top: int) -> str:
    """Profile one ``check`` run and return the hot list.

    Args:
        source: Combined source text.
        stubs_path: Stub directory.
        top: Rows to print.

    Returns:
        The formatted stats table.

    """
    catalog: Catalog = load_default_catalog(
        registries=default_registries(),
    )
    profiler: Profile = Profile()
    profiler.enable()
    _ = check(
        source=source,
        filename="workload.py",
        catalog=catalog,
        registries=default_registries(),
        options=CheckOptions(stubs_path=stubs_path),
    )
    profiler.disable()
    buffer: StringIO = StringIO()
    stats: Stats = Stats(profiler, stream=buffer)
    stats.sort_stats(*("cumulative",))
    stats.print_stats(top)
    return buffer.getvalue()


def main(*, argv: Sequence[str] | None = None) -> int:
    """Run the workload and print timings.

    Args:
        argv: Command-line arguments.

    Returns:
        Zero.

    """
    parser: ArgumentParser = ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--lines",
        type=int,
        default=Constants.target_lines,
    )
    _ = parser.add_argument("--json", action="store_true")
    _ = parser.add_argument("--profile", action="store_true")
    _ = parser.add_argument("--top", type=int, default=Constants.top)
    args: Namespace = parser.parse_args(args=argv)
    source: str = build_workload(lines=args.lines)
    with TemporaryDirectory() as directory:
        stubs_path: Path = Path(directory)
        if args.profile:
            _ = stdout.write(
                _profile(
                    source=source,
                    stubs_path=stubs_path,
                    top=args.top,
                ),
            )
        metrics: dict[str, float] = run(source=source, stubs_path=stubs_path)
    if args.json:
        _ = stdout.write(dumps(obj=metrics, sort_keys=True) + "\n")
    else:
        _ = stdout.write(
            f"lines {metrics['lines']:.0f} "
            f"check {metrics['check_seconds']:.2f}s "
            f"fix {metrics['fix_seconds']:.2f}s "
            f"total {metrics['total_seconds']:.2f}s "
            f"findings {metrics['findings']:.0f} "
            f"applied {metrics['applied']:.0f} "
            f"skipped {metrics['skipped']:.0f}\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
