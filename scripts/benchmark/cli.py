"""Command line of the benchmark harness.

``python -m scripts.benchmark recovery`` measures annotation recovery and
prints a JSON report; ``gate`` compares a report with the accepted baseline
and exits non-zero on a regression; ``baseline`` accepts a report as the new
baseline.

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import replace
from datetime import UTC, datetime
from json import dumps, loads
from os import environ, process_cpu_count
from pathlib import Path
from sys import argv as process_argv
from sys import stdout
from typing import TYPE_CHECKING, Final, Protocol, final

from astart.rules.checker import build_checker

from scripts.benchmark.activity import Activity
from scripts.benchmark.paths import Paths
from scripts.benchmark.presentation import JsonValue, publish
from scripts.benchmark.profile_perf import main as profile_main
from scripts.benchmark.report import (
    Report,
    Thresholds,
    compare,
    from_json,
    to_json,
)
from scripts.benchmark.runner import Plan, run_recovery
from scripts.benchmark.semantic import (
    ProjectResult,
    load_projects,
    run_semantic,
)
from scripts.benchmark.semantic import to_json as semantic_json
from scripts.benchmark.sensors import arm, metrics
from scripts.benchmark.targets import (
    Target,
    collect,
    evaluate,
    format_row,
    load_targets,
)
from scripts.benchmark.throughput import (
    PerfReport,
    compare_perf,
    format_table,
    measure_all,
)
from scripts.benchmark.throughput import from_json as perf_from_json
from scripts.benchmark.throughput import to_json as perf_to_json
from scripts.benchmark.treehash import tree_hash

if TYPE_CHECKING:
    from typing import TextIO


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus (Final[Path]): Default directory of typed modules.
        baseline (Final[Path]): Default accepted report.
        baseline_log (Final[Path]): Default append-only log of accepted
            baselines.
        pattern (Final[str]): File pattern of corpus modules.
        projects (Final[Path]): Default list of pinned projects.
        perf_baseline (Final[Path]): Default accepted throughput report.
        targets_file (Final[Path]): Default accuracy-contract target list.
        report_dir (Final[Path]): Default directory of recovery ``--json``
            reports.
        root (Final[Path]): Repository root containing the benchmark tree.
        suite (Final[tuple[str, ...]]): Self-contained tools run by a bare
            invocation.

    """

    corpus: Final[Path] = Paths.root / "tests" / "corpus" / "base"
    baseline: Final[Path] = Paths.resources / "baseline.json"
    baseline_log: Final[Path] = Paths.resources / "baseline_log.md"
    pattern: Final[str] = "*.py"
    projects: Final[Path] = Paths.resources / "projects.json"
    perf_baseline: Final[Path] = Paths.resources / "baseline_perf.json"
    targets_file: Final[Path] = Paths.resources / "targets.json"
    report_dir: Final[Path] = Paths.results
    root: Final[Path] = Paths.root
    suite: Final[tuple[str, ...]] = (
        "recovery",
        "semantic",
        "perf",
        "targets",
    )


class _Subcommands(Protocol):
    """The ``add_subparsers`` result surface the CLI uses."""

    def add_parser(self, name: str) -> ArgumentParser:
        """Create a subcommand parser.

        Args:
            name (str): Subcommand name.

        Returns:
            The new subparser.

        """
        ...


def parser() -> ArgumentParser:
    """Build the argument parser.

    Returns:
        ArgumentParser: The parser with the three subcommands.

    """
    parser: ArgumentParser = ArgumentParser(prog="python -m scripts.benchmark")
    commands: _Subcommands = parser.add_subparsers(
        dest="command",
        required=False,
    )
    recovery: ArgumentParser = commands.add_parser(name="recovery")
    recovery.add_argument("--corpus", type=Path, default=Constants.corpus)
    recovery.add_argument("--json", type=Path, dest="output")
    recovery.add_argument("--limit", type=int, default=0)
    recovery.add_argument("--checker-delta", action="store_true")
    recovery.add_argument("--checker-gate", action="store_true")
    recovery.add_argument("--delta-limit", type=int, default=20)
    recovery.add_argument("--jobs", type=int, default=process_cpu_count() or 1)
    recovery.add_argument(
        "--no-negotiate",
        dest="negotiate",
        action="store_false",
    )
    recovery.add_argument("--variables", action="store_true")
    recovery.add_argument("--engine", action="store_true")
    gate: ArgumentParser = commands.add_parser(name="gate")
    gate.add_argument("--report", type=Path, required=True)
    gate.add_argument("--baseline", type=Path, default=Constants.baseline)
    gate.add_argument("--min-precision", type=float, default=0.995)
    gate.add_argument("--recall-slack", type=float, default=0.005)
    gate.add_argument("--max-rounds", type=int, default=3)
    gate.add_argument("--method-recall-factor", type=float, default=3.0)
    gate.add_argument("--method-precision-slack", type=float, default=0.001)
    gate.add_argument("--log", type=Path, default=Constants.baseline_log)
    semantic: ArgumentParser = commands.add_parser(name="semantic")
    semantic.add_argument(
        "--projects",
        type=Path,
        default=Constants.projects,
    )
    semantic.add_argument("--json", type=Path, dest="output")
    accept: ArgumentParser = commands.add_parser(name="baseline")
    accept.add_argument("--report", type=Path, required=True)
    accept.add_argument("--out", type=Path, default=Constants.baseline)
    accept.add_argument("--reason", required=True)
    accept.add_argument("--log", type=Path, default=Constants.baseline_log)
    perf: ArgumentParser = commands.add_parser(name="perf")
    perf.add_argument(
        "--baseline",
        type=Path,
        default=Constants.perf_baseline,
    )
    perf.add_argument("--runs", type=int, default=0)
    perf.add_argument("--json", type=Path, dest="output")
    perf.add_argument("--update", action="store_true")
    targets: ArgumentParser = commands.add_parser(name="targets")
    targets.add_argument(
        "--report",
        type=Path,
        default=Constants.report_dir,
        dest="report_dir",
    )
    targets.add_argument("--only", type=str, default="")
    targets.add_argument(
        "--targets",
        type=Path,
        default=Constants.targets_file,
    )
    profiling: ArgumentParser = commands.add_parser(name="profile")
    profiling.add_argument("--lines", type=int, default=12_000)
    profiling.add_argument("--top", type=int, default=25)
    profiling.add_argument("--json", action="store_true")
    profiling.add_argument("--profile", action="store_true")
    return parser


def _recovery(
    *,
    args: Namespace,
    out: TextIO,
    activity: Activity | None = None,
) -> int:
    """Run the recovery benchmark and write its report.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream the report goes to when no file is given.
        activity (Activity | None): Optional live module-progress recorder.

    Returns:
        int: Zero.

    """
    paths: list[Path] = sorted(args.corpus.glob(pattern=Constants.pattern))
    if args.limit:
        paths = paths[: args.limit]
    report: Report = run_recovery(
        paths=paths,
        activity=activity,
        plan=Plan(
            delta=build_checker(root=Path.cwd())
            if args.checker_delta
            else None,
            delta_limit=args.delta_limit,
            gated=args.checker_gate,
            jobs=args.jobs,
            negotiate=args.negotiate,
            variables=args.variables,
            engine=args.engine,
        ),
    )
    report = replace(
        report,
        tree_hash=tree_hash(root=Constants.root),
        corpus=args.corpus.name,
    )
    text: str = to_json(report=report) + "\n"
    label: str = {
        "corpus": "std",
        "base": "std",
        "corpus_ext": "ext",
        "extended": "ext",
    }.get(
        args.corpus.name,
        args.corpus.name or "std",
    )
    text = publish(
        name=f"recovery-{label}.json",
        text=text,
        output=args.output,
        tool="recovery",
        variant=label,
    )
    if args.output is None:
        _ = out.write(text)
    return 0


def _gate(*, args: Namespace, out: TextIO) -> int:
    """Compare a report with the baseline.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream the verdict is written to.

    Returns:
        int: ``0`` when the run passes, ``1``
            with the reasons on stdout when not.

    """
    report: Report = from_json(
        text=args.report.read_text(encoding="utf-8"),
    )
    problems: tuple[str, ...] = compare(
        report=report,
        baseline=from_json(text=args.baseline.read_text(encoding="utf-8")),
        limits=Thresholds(
            min_precision=args.min_precision,
            recall_slack=args.recall_slack,
            max_rounds=args.max_rounds,
            method_recall_factor=args.method_recall_factor,
            method_precision_slack=args.method_precision_slack,
        ),
    )
    current_hash: str = tree_hash(root=Constants.root)
    if report.tree_hash and report.tree_hash != current_hash:
        problems = (
            f"stale report: tree {report.tree_hash} != current {current_hash}",
            *problems,
        )
    _ = publish(
        name="gate.json",
        text=dumps(
            obj={
                "passed": not problems,
                "problems": problems,
                "tree": current_hash,
            },
            indent=2,
        )
        + "\n",
        tool="gate",
    )
    for problem in problems:
        _ = out.write(f"FAIL {problem}\n")
    if not problems:
        _ = out.write("""\
PASS
""")
    else:
        _ = _last_log_entry(path=args.log, out=out)
    return 1 if problems else 0


def _semantic(*, args: Namespace, out: TextIO) -> int:
    """Run the semantic-equivalence projects.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream the report goes to when no file is given.

    Returns:
        int: ``0`` when every project is equivalent after fixing, else ``1``.

    """
    results: tuple[ProjectResult, ...] = run_semantic(
        projects=load_projects(path=args.projects),
    )
    text: str = semantic_json(results=results) + "\n"
    text = publish(
        name="semantic.json",
        text=text,
        output=args.output,
        tool="semantic",
    )
    if args.output is None:
        _ = out.write(text)
    return 0 if all(item.passed for item in results) else 1


def _perf(*, args: Namespace, out: TextIO) -> int:
    """Measure throughput and compare it with the perf baseline.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream the table and verdict are written to.

    Returns:
        int: ``0`` when no bucket regresses by more than 20%, else ``1``.

    """
    report: PerfReport = measure_all(runs=args.runs or 3)
    baseline: PerfReport = perf_from_json(
        text=args.baseline.read_text(encoding="utf-8"),
    )
    if args.update:
        _ = args.baseline.write_text(
            data=perf_to_json(report=report) + "\n",
            encoding="utf-8",
        )
    _ = publish(
        name="perf.json",
        text=perf_to_json(report=report) + "\n",
        output=args.output,
        tool="perf",
    )
    _ = out.write(
        format_table(
            current=report["buckets"],
            baseline=baseline["buckets"],
        ),
    )
    problems: tuple[str, ...] = compare_perf(
        current=report["buckets"],
        baseline=baseline["buckets"],
    )
    for problem in problems:
        _ = out.write(f"FAIL {problem}\n")
    if not problems:
        _ = out.write("""\
PASS
""")
    return 1 if problems else 0


def _targets(*, args: Namespace, out: TextIO) -> int:
    """Check the accuracy-contract targets.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream the verdict rows are written to.

    Returns:
        int: ``0`` when every selected target passes, else ``1``.

    """
    selected: tuple[Target, ...] = tuple(
        target
        for target in load_targets(path=args.targets)
        if not args.only or target.id == args.only
    )
    reports: dict[str, float] = collect(
        report_dir=args.report_dir,
        metrics={target.metric for target in selected},
    )
    _ = publish(
        name="targets-metrics.json",
        text=dumps(obj=reports, indent=2) + "\n",
        tool="targets",
    )
    stamp: str = provenance_stamp(report_dir=args.report_dir)
    failed: int = 0
    for target in selected:
        _ = out.write(
            format_row(target=target, reports=reports) + f"  · {stamp}\n",
        )
        failed += 0 if evaluate(target=target, reports=reports) else 1
    return 1 if failed or not selected else 0


def provenance_stamp(*, report_dir: Path) -> str:
    """Build the ``tree · corpus · date`` stamp for target rows.

    Args:
        report_dir (Path): Directory recovery reports were read from; its
            ``*std*``/``*ext*`` JSON names identify the corpus set.

    Returns:
        str: One-line provenance text appended to every verdict row.

    """
    labels: list[str] = []
    names: list[str] = []
    if report_dir.is_dir():
        names.extend(
            path.name for path in report_dir.glob(pattern="recovery*.json")
        )
        aggregate: Path = report_dir / "report.json"
        if aggregate.is_file():
            try:
                document: JsonValue = loads(
                    s=aggregate.read_text(encoding="utf-8"),
                )
            except (OSError, ValueError):
                document = {}
            tools: JsonValue = (
                document.get("tools") if isinstance(document, dict) else None
            )
            if isinstance(tools, dict):
                names.extend(
                    key.partition(".")[2]
                    for key in tools
                    if key.startswith("recovery.")
                )
    if any("std" in name for name in names):
        labels.append("stdlib")
    if any("ext" in name for name in names):
        labels.append("external")
    corpus: str = "+".join(labels) if labels else "no-reports"
    today: str = datetime.now(tz=UTC).date().isoformat()
    return f"tree {tree_hash(root=Constants.root)} · corpus {corpus} · {today}"


def main(*, argv: list[str] | None = None, out: TextIO = stdout) -> int:
    """Dispatch a subcommand.

    Args:
        argv (list[str] | None): Arguments after the program name; defaults to
            the process's.
        out (TextIO): Stream for reports and verdicts.

    Returns:
        int: The exit status.

    """
    _ = environ.setdefault("ASTART_SENSORS", "1")
    metrics.reset()
    arm(register_exit=False)
    args: Namespace = parser().parse_args(
        args=process_argv[1:] if argv is None else argv,
    )
    if args.command is None:
        return _run_suite(out=out)
    if args.command == "recovery" and args.jobs < 1:
        parser().error(message="--jobs must be at least 1")
    with Activity(
        directory=Paths.results,
        command=args.command,
        jobs=args.jobs if args.command == "recovery" else 1,
    ) as activity:
        activity.exit_code = _execute(args=args, out=out, activity=activity)
        return activity.exit_code


def _run_suite(*, out: TextIO) -> int:
    """Run every self-contained benchmark tool and consolidate the report.

    Args:
        out (TextIO): Stream for reports and verdicts.

    Returns:
        int: ``0`` when every tool passes, else ``1``.

    """
    with Activity(
        directory=Paths.results,
        command="all",
        jobs=process_cpu_count() or 1,
    ) as activity:
        codes: list[int] = []
        for name in Constants.suite:
            tool_args: Namespace = parser().parse_args(args=[name])
            codes.append(_dispatch(args=tool_args, out=out, activity=activity))
        activity.exit_code = 1 if any(code != 0 for code in codes) else 0
        return activity.exit_code


def _execute(*, args: Namespace, out: TextIO, activity: Activity) -> int:
    """Run the selected benchmark within its activity lifecycle.

    Args:
        args (Namespace): Parsed command options.
        out (TextIO): Command output stream.
        activity (Activity): Live run progress.

    Returns:
        int: Selected command exit code.

    """
    if args.command == "profile":
        return profile_main(
            argv=[
                "--lines",
                str(object=args.lines),
                "--top",
                str(object=args.top),
                *(["--json"] if args.json else []),
                *(["--profile"] if args.profile else []),
            ],
        )
    return _dispatch(args=args, out=out, activity=activity)


def _dispatch(*, args: Namespace, out: TextIO, activity: Activity) -> int:
    """Dispatch non-profile benchmark commands.

    Args:
        args (Namespace): Parsed benchmark options.
        out (TextIO): Report output stream.
        activity (Activity): Live run progress.

    Returns:
        int: Selected command exit status.

    """
    if args.command == "recovery":
        return _recovery(args=args, out=out, activity=activity)
    if args.command == "gate":
        return _gate(args=args, out=out)
    if args.command == "semantic":
        return _semantic(args=args, out=out)
    if args.command == "perf":
        return _perf(args=args, out=out)
    if args.command == "targets":
        return _targets(args=args, out=out)
    return _accept_baseline(args=args, out=out)


def _accept_baseline(*, args: Namespace, out: TextIO) -> int:
    """Accept a report as the new baseline and log the change.

    Args:
        args (Namespace): Parsed arguments.
        out (TextIO): Stream for diagnostics.

    Returns:
        int: Zero.

    """
    new: Report = from_json(text=args.report.read_text(encoding="utf-8"))
    old: Report | None = (
        from_json(text=args.out.read_text(encoding="utf-8"))
        if args.out.exists()
        else None
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    _ = args.out.write_text(
        data=args.report.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _log_baseline(args=args, old=old, new=new, out=out)
    return 0


def _log_baseline(
    *,
    args: Namespace,
    old: Report | None,
    new: Report,
    out: TextIO,
) -> None:
    """Append the baseline change to the log.

    Args:
        args (Namespace): Parsed arguments.
        old (Report | None): Previous baseline report, or ``None`` on first
            accept.
        new (Report): Accepted report.
        out (TextIO): Stream for diagnostics.

    """
    stamp: str = datetime.now(tz=UTC).date().isoformat()
    before: str = (
        f"{old.precision * 100:.2f}/{old.recall * 100:.2f}"
        if old is not None
        else "—"
    )
    entry: str = (
        f"- {stamp} · baseline · precision/recall {before} → "
        f"{new.precision * 100:.2f}/{new.recall * 100:.2f} · "
        f"{args.reason}\n"
    )
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open(mode="a", encoding="utf-8") as handle:
        _ = handle.write(entry)
    _ = out.write(f"baseline accepted; logged to {args.log}\n")


def _last_log_entry(*, path: Path, out: TextIO) -> None:
    """Print the last entry of the baseline log.

    Args:
        path (Path): Log file to read.
        out (TextIO): Stream the entry is written to.

    """
    if not path.exists():
        return
    lines: list[str] = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if lines:
        _ = out.write(f"last baseline change: {lines[-1]}\n")


if __name__ == "__main__":
    raise SystemExit(main())
