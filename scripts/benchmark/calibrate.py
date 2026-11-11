r"""Cross-validate per-basis confidence on two corpus halves (I-20).

Splits the measured modules deterministically (sorted by name, then
alternating) and recomputes the exact share of each hint basis on each
half. Exits non-zero when a basis's halves differ by more than
``--max-delta`` points; bases with fewer than ``--min-count`` scored
annotations across both halves are reported but not gated.

Usage::

    PYTHONPATH=src python -m scripts.benchmark.calibrate \\\\
        --corpus tests/corpus/extended --jobs 8

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from pathlib import Path
from sys import argv, stderr, stdout
from typing import TYPE_CHECKING, Final, final

from scripts.benchmark.runner import Plan, run_recovery

if TYPE_CHECKING:
    from collections.abc import Sequence

    from scripts.benchmark.report import ModuleResult, Report


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus (Final[Path]): Default directory of typed modules.
        pattern (Final[str]): File pattern of corpus modules.
        max_delta (Final[float]): Default point gap allowed between halves.
        min_count (Final[int]): Default scored annotations a basis needs before
            the gap is gated.
        outcomes (Final[frozenset[str]]): Scored outcomes that count toward the
            exact share.

    """

    corpus: Final[Path] = Path("tests/corpus/extended")
    pattern: Final[str] = "*.py"
    max_delta: Final[float] = 3.0
    min_count: Final[int] = 30
    outcomes: Final[frozenset[str]] = frozenset(
        {"correct", "wrong", "compatible"},
    )


def halves(
    *,
    modules: Sequence[ModuleResult],
) -> tuple[list[ModuleResult], list[ModuleResult]]:
    """Split modules into two interleaved halves.

    Args:
        modules (Sequence[ModuleResult]): Measured module results.

    Returns:
        tuple[list[ModuleResult], list[ModuleResult]]: ``(first, second)``
            halves; names sorted, then alternated
            so each half samples the whole corpus ordering.

    """
    ordered: list[ModuleResult] = sorted(
        modules,
        key=lambda item: item.name,
    )
    return ordered[0::2], ordered[1::2]


def shares(
    *,
    modules: Sequence[ModuleResult],
) -> dict[str, tuple[int, int, int]]:
    """Aggregate per-basis ``(correct, wrong, compatible)`` counts.

    Args:
        modules (Sequence[ModuleResult]): Measured module results.

    Returns:
        dict[str, tuple[int, int, int]]:
            ``basis: (correct, wrong, compatible)`` over the
            recorded written annotations; synthesized annotations
            carry no original to match and are excluded.

    """
    counts: dict[str, Counter[str]] = {}
    for item in modules:
        for basis, outcome, count in item.basis_outcomes:
            if outcome in Constants.outcomes:
                bucket: Counter[str] = counts.setdefault(basis, Counter())
                bucket[outcome] += count
    return {
        basis: (
            bucket["correct"],
            bucket["wrong"],
            bucket["compatible"],
        )
        for basis, bucket in counts.items()
    }


def exact(*, counts: tuple[int, int, int]) -> float:
    """Share of scored annotations that are exactly correct.

    Args:
        counts (tuple[int, int, int]): ``(correct, wrong, compatible)`` counts.

    Returns:
        float: ``correct / scored`` in percent, or ``0.0`` when nothing scored.

    """
    total: int = sum(counts)
    return 0.0 if total == 0 else 100.0 * counts[0] / total


def main() -> int:
    """Run the calibration and print the per-basis table.

    Returns:
        int: ``0`` when every gated basis is within ``--max-delta`` points,
            ``1`` otherwise.

    """
    parser: ArgumentParser = ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Constants.corpus)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-delta", type=float, default=Constants.max_delta)
    parser.add_argument("--min-count", type=int, default=Constants.min_count)
    parser.add_argument(
        "--no-negotiate",
        dest="negotiate",
        action="store_false",
    )
    parser.add_argument("--variables", action="store_true")
    parser.add_argument("--engine", action="store_true")
    args: Namespace = parser.parse_args(args=argv[1:])

    paths: list[Path] = sorted(args.corpus.glob(pattern=Constants.pattern))
    if args.limit:
        paths = paths[: args.limit]
    plan: Plan = Plan(
        attribute=False,
        jobs=args.jobs,
        negotiate=args.negotiate,
        variables=args.variables,
        engine=args.engine,
    )
    report: Report = run_recovery(paths=paths, plan=plan)
    first, second = halves(modules=report.modules)
    shares_a: dict[str, tuple[int, int, int]] = shares(modules=first)
    shares_b: dict[str, tuple[int, int, int]] = shares(modules=second)

    _ = stdout.write(
        f"{'basis':24} {'half A':>7} {'n A':>6} "
        f"{'half B':>7} {'n B':>6} {'delta':>7}\n",
    )
    failures: int = 0
    for basis in sorted(set(shares_a) | set(shares_b)):
        counts_a: tuple[int, int, int] = shares_a.get(basis, (0, 0, 0))
        counts_b: tuple[int, int, int] = shares_b.get(basis, (0, 0, 0))
        share_a: float = exact(counts=counts_a)
        share_b: float = exact(counts=counts_b)
        delta: float = abs(share_a - share_b)
        total: int = sum(counts_a) + sum(counts_b)
        gated: bool = (
            total >= args.min_count
            and counts_a != (0, 0, 0)
            and counts_b != (0, 0, 0)
        )
        mark: str = ""
        if gated and delta > args.max_delta:
            mark = "  FAIL"
            failures += 1
        elif not gated:
            mark = "  (few)"
        _ = stdout.write(
            f"{basis:24} {share_a:6.1f}% {sum(counts_a):6} "
            f"{share_b:6.1f}% {sum(counts_b):6} {delta:6.1f} {mark}\n",
        )
    _ = stderr.write(
        f"calibrate: {len(first)} + {len(second)} modules, "
        f"{failures} basis(es) over {args.max_delta} points\n",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
