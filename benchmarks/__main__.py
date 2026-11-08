"""Command line of the benchmark harness.

``python -m benchmarks recovery`` measures annotation recovery and prints a
JSON report; ``gate`` compares a report with the accepted baseline and exits
non-zero on a regression; ``baseline`` accepts a report as the new baseline.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import argv as process_argv
from sys import stdout
from typing import TYPE_CHECKING, Final, Protocol, final

from astart.rules.checker import build_checker

from benchmarks.report import Report, Thresholds, compare, from_json, to_json
from benchmarks.runner import Plan, run_recovery
from benchmarks.semantic import (
    ProjectResult,
    load_projects,
    run_semantic,
)
from benchmarks.semantic import to_json as semantic_json

if TYPE_CHECKING:
    from typing import TextIO


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus: Default directory of typed modules.
        baseline: Default accepted report.
        pattern: File pattern of corpus modules.
        projects: Default list of pinned projects.

    """

    corpus: Final[Path] = Path("tests/corpus")
    baseline: Final[Path] = Path("benchmarks/baseline.json")
    pattern: Final[str] = "*.py.txt"
    projects: Final[Path] = Path("benchmarks/projects.json")


class _Subcommands(Protocol):
    """The ``add_subparsers`` result surface the CLI uses."""

    def add_parser(self, name: str) -> ArgumentParser:
        """Create a subcommand parser.

        Args:
            name: Subcommand name.

        Returns:
            The new subparser.

        """
        ...


def _parser() -> ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser with the three subcommands.

    """
    parser: ArgumentParser = ArgumentParser(prog="python -m benchmarks")
    commands: _Subcommands = parser.add_subparsers(
        dest="command",
        required=True,
    )
    recovery: ArgumentParser = commands.add_parser(name="recovery")
    recovery.add_argument("--corpus", type=Path, default=Constants.corpus)
    recovery.add_argument("--json", type=Path, dest="output")
    recovery.add_argument("--limit", type=int, default=0)
    recovery.add_argument("--checker-delta", action="store_true")
    recovery.add_argument("--checker-gate", action="store_true")
    recovery.add_argument("--delta-limit", type=int, default=20)
    recovery.add_argument("--jobs", type=int, default=1)
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
    return parser


def _recovery(*, args: Namespace, out: TextIO) -> int:
    """Run the recovery benchmark and write its report.

    Args:
        args: Parsed arguments.
        out: Stream the report goes to when no file is given.

    Returns:
        Zero.

    """
    paths: list[Path] = sorted(args.corpus.glob(pattern=Constants.pattern))
    if args.limit:
        paths = paths[: args.limit]
    report: Report = run_recovery(
        paths=paths,
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
    text: str = to_json(report=report) + "\n"
    if args.output is None:
        _ = out.write(text)
    else:
        _ = args.output.write_text(data=text, encoding="utf-8")
    return 0


def _gate(*, args: Namespace, out: TextIO) -> int:
    """Compare a report with the baseline.

    Args:
        args: Parsed arguments.
        out: Stream the verdict is written to.

    Returns:
        ``0`` when the run passes, ``1`` with the reasons on stdout when not.

    """
    problems: tuple[str, ...] = compare(
        report=from_json(text=args.report.read_text(encoding="utf-8")),
        baseline=from_json(text=args.baseline.read_text(encoding="utf-8")),
        limits=Thresholds(
            min_precision=args.min_precision,
            recall_slack=args.recall_slack,
            max_rounds=args.max_rounds,
        ),
    )
    for problem in problems:
        _ = out.write(f"FAIL {problem}\n")
    if not problems:
        _ = out.write("PASS\n")
    return 1 if problems else 0


def _semantic(*, args: Namespace, out: TextIO) -> int:
    """Run the semantic-equivalence projects.

    Args:
        args: Parsed arguments.
        out: Stream the report goes to when no file is given.

    Returns:
        ``0`` when every project is equivalent after fixing, else ``1``.

    """
    results: tuple[ProjectResult, ...] = run_semantic(
        projects=load_projects(path=args.projects),
    )
    text: str = semantic_json(results=results) + "\n"
    if args.output is None:
        _ = out.write(text)
    else:
        _ = args.output.write_text(data=text, encoding="utf-8")
    return 0 if all(item.passed for item in results) else 1


def main(*, argv: list[str] | None = None, out: TextIO = stdout) -> int:
    """Dispatch a subcommand.

    Args:
        argv: Arguments after the program name; defaults to the process's.
        out: Stream for reports and verdicts.

    Returns:
        The exit status.

    """
    args: Namespace = _parser().parse_args(
        args=process_argv[1:] if argv is None else argv,
    )
    if args.command == "recovery":
        return _recovery(args=args, out=out)
    if args.command == "gate":
        return _gate(args=args, out=out)
    if args.command == "semantic":
        return _semantic(args=args, out=out)
    _ = args.out.write_text(
        data=args.report.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
