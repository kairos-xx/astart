"""Single command-line entry point using the astart Python API."""

from __future__ import annotations

from argparse import Action, ArgumentParser
from io import BytesIO
from json import dumps
from pathlib import Path
from sys import stdout
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Protocol, cast, final

from astart import GraphConversion, Module, convert, parse, unparse
from astart.cli.commands import (
    CheckSettings,
    FixCommandSettings,
    FixMode,
    run_check,
    run_fix,
)
from astart.rules.vocabulary import FixSafety, Severity

if TYPE_CHECKING:
    from collections.abc import Callable


class _Arguments(Protocol):
    """Typed projection of supported command-line arguments.

    Attributes:
        command: Selected operation.
        source: Input filename.
        stubs: Directory containing type stubs.
        output: Output filename.
        report: Optional JSON report destination.
        dry_run: Whether to omit source-file changes.
        strict_formatting: Whether unsafe lexical edits should fail.
        paths: Files or directories to inspect.
        output_format: Output format for check findings.
        fail_on: Minimum severity that fails the run.
        stubs_dir: Optional stub directory for check and fix.
        safe_only: Whether only provably safe fixes may run.
        diff: Whether to print a diff without writing.
        check: Whether to report pending fixes without writing.
        no_format: Whether to skip the final formatting pass.
        checker: ``auto`` lets an installed pyright veto guarded fixes.
        min_confidence: Least confidence a fix needs to be applied.
        create_constants_class: Whether to create a missing ``Constants``
            class for ``Final`` module constants.
        source_root: Extra import roots for the type checker.

    """

    command: str | None
    source: str
    stubs: str
    output: str
    report: str | None
    dry_run: bool
    strict_formatting: bool
    paths: list[str]
    output_format: str
    fail_on: str
    stubs_dir: str | None
    safe_only: bool
    diff: bool
    check: bool
    no_format: bool
    checker: str
    min_confidence: float
    create_constants_class: bool
    source_root: list[str] | None


@final
class _Group(Protocol):
    """Subset of a mutually-exclusive argument group used here."""

    def add_argument(self, name: str, /, *, action: str) -> Action:
        """Register a flag on the group.

        Args:
            name: Flag name.
            action: argparse action name.

        Returns:
            The created action.

        """
        ...


@final
class _SubParsers(Protocol):
    """Subset of the sub-parser registry used here.

    Attributes:
        add_parser: Factory for subcommand parsers.

    """

    add_parser: Callable[..., ArgumentParser]


def _stubs(*, args: _Arguments) -> Path | None:
    """Return the optional stub directory.

    Args:
        args: Parsed arguments.

    Returns:
        The directory, or ``None`` when it was not given.

    """
    return Path(args.stubs_dir) if args.stubs_dir else None


def _mode(*, args: _Arguments) -> FixMode:
    """Pick the fix mode from the flags.

    Args:
        args: Parsed arguments.

    Returns:
        ``diff``, ``check`` or ``write``.

    """
    if args.diff:
        return FixMode.diff
    return FixMode.check if args.check else FixMode.write


def _configure_check(*, command: ArgumentParser) -> None:
    """Add the ``check`` subcommand's arguments.

    Args:
        command: Parser of the ``check`` subcommand.

    """
    command.add_argument("paths", nargs="+")
    command.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
    )
    command.add_argument(
        "--fail-on",
        choices=tuple(item.value for item in Severity),
        default=Severity.error.value,
    )
    command.add_argument("--stubs", dest="stubs_dir")


def _configure_fix(*, command: ArgumentParser) -> None:
    """Add the ``fix`` subcommand's arguments.

    Args:
        command: Parser of the ``fix`` subcommand.

    """
    command.add_argument("paths", nargs="+")
    command.add_argument(
        "--safe-only",
        action="store_true",
        help="Apply only provably safe fixes",
    )
    group: _Group = command.add_mutually_exclusive_group()
    group.add_argument("--diff", action="store_true")
    group.add_argument("--check", action="store_true")
    command.add_argument("--no-format", action="store_true")
    command.add_argument(
        "--checker",
        choices=("auto", "off"),
        default="auto",
        help="Let an installed pyright veto guarded fixes (default: auto)",
    )
    command.add_argument("--stubs", dest="stubs_dir")
    command.add_argument("--min-confidence", type=float, default=0.0)
    command.add_argument(
        "--create-constants-class",
        action="store_true",
        help="Create a Constants class when a module has none",
    )
    command.add_argument(
        "--source-root",
        action="append",
        help="Directory the type checker resolves imports from (repeatable)",
    )


def main(*, argv: list[str] | None = None) -> int:
    """Convert a Python file through the same safe AST API as library callers.

    Args:
        argv: Optional CLI arguments; defaults to process arguments.

    Returns:
        Process status, zero after successful transformation.

    Raises:
        OSError: Source, output, or stub paths cannot be accessed.
        SyntaxError: The input or reconstructed source is not valid Python.
        UnicodeError: Source cannot be decoded using its declared encoding.

    """
    parser: ArgumentParser = ArgumentParser(prog="astart")
    commands: _SubParsers = cast(
        typ="_SubParsers",
        val=parser.add_subparsers(dest="command"),
    )
    _configure_check(
        command=commands.add_parser(
            name="check",
            help="Report rule violations",
        ),
    )
    _configure_fix(
        command=commands.add_parser(
            name="fix",
            help="Automatically fix violations, then format once",
        ),
    )
    command: ArgumentParser = commands.add_parser(
        name="convert",
        help="Infer and safely apply source annotations",
    )
    command.add_argument("--source", required=True)
    command.add_argument("--stubs", required=True)
    command.add_argument("--output", required=True)
    command.add_argument("--report")
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--strict-formatting", action="store_true")
    args: _Arguments = cast(typ="_Arguments", val=parser.parse_args(args=argv))
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "check":
        return run_check(
            settings=CheckSettings(
                paths=tuple(Path(item) for item in args.paths),
                output_format=args.output_format,
                fail_on=Severity(args.fail_on),
                stubs_path=_stubs(args=args),
            ),
            out=stdout,
        )
    if args.command == "fix":
        return run_fix(
            settings=FixCommandSettings(
                paths=tuple(Path(item) for item in args.paths),
                ceiling=FixSafety.proven
                if args.safe_only
                else FixSafety.guarded,
                stubs_path=_stubs(args=args),
                mode=_mode(args=args),
                run_formatter=not args.no_format,
                use_checker=args.checker == "auto",
                min_confidence=args.min_confidence,
                create_constants=args.create_constants_class,
                source_roots=tuple(
                    Path(item) for item in args.source_root or ()
                ),
            ),
            out=stdout,
        )
    input_path: Path = Path(args.source)
    data: bytes = input_path.read_bytes()
    encoding: str = detect_encoding(
        readline=BytesIO(initial_bytes=data).readline,
    )[0]
    source: str = data.decode(encoding=encoding)
    tree: Module = parse(source=source, filename=str(object=input_path))
    result: GraphConversion = convert(
        tree=tree,
        stubs_path=Path(args.stubs),
        filename=str(object=input_path),
        apply=not args.dry_run,
    )
    if not args.dry_run:
        Path(args.output).write_bytes(
            data=unparse(
                tree=tree,
                preserve_formatting=True,
                on_format_conflict="raise"
                if args.strict_formatting
                else "fallback",
            ).encode(encoding=encoding),
        )
    if args.report:
        Path(args.report).write_text(
            data=dumps(
                obj={
                    "proposals": result.proposal_count,
                    "stages": result.stages,
                    "skipped": result.skipped,
                    "warnings": result.warnings,
                    "dry_run": args.dry_run,
                },
                indent=2,
            )
            + """\

""",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
