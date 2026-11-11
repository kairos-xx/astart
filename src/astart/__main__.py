"""Single command-line entry point using the astart Python API."""

from __future__ import annotations

from argparse import Action, ArgumentParser, BooleanOptionalAction
from atexit import register
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from json import dumps
from pathlib import Path
from signal import SIGUSR1, signal
from sys import modules, stderr, stdout
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Protocol, cast, final

from astart import (
    CommentedModule,
    GraphConversion,
    convert,
    parse,
    unparse,
)
from astart.cli.commands import (
    CheckSettings,
    FixCommandSettings,
    FixMode,
    run_check,
    run_explain,
    run_explain_at,
    run_fix,
    run_rules,
    run_undo,
)
from astart.cli.transforms import (
    TransformArguments,
    configure_transform,
    run_transform,
)
from astart.rules.confidence import Constants as ConfidenceConstants
from astart.rules.vocabulary import FixSafety, Severity
from astart.source import metrics as sensors

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType


class _Arguments(Protocol):
    """Typed projection of supported command-line arguments.

    Attributes:
        command (str | None): Selected operation.
        source (str): Input filename.
        stubs (str | None): Directory containing type stubs.
        output (str): Output filename.
        report (str | None): Optional JSON report destination.
        dry_run (bool): Whether to omit source-file changes.
        strict_formatting (bool): Whether unsafe lexical edits should fail.
        paths (list[str]): Files or directories to inspect.
        output_format (str): Output format for check findings.
        fail_on (str): Minimum severity that fails the run.
        stubs_dir (str | None): Optional stub directory for check and fix.
        safe_only (bool): Whether only provably safe fixes may run.
        diff (bool): Whether to print a diff without writing.
        check (bool): Whether to report pending fixes without writing.
        no_format (bool): Whether to skip the final formatting pass.
        checker (str): ``auto`` lets an installed pyright veto guarded fixes.
        min_confidence (float | None): Least confidence a fix needs to be
            applied.
        create_constants_class (bool): Whether to create a missing
            ``Constants``
            class for ``Final`` module constants.
        docstring_types (bool): Include annotation types in documentation.
        stub_docstrings (bool): Whether to stub missing docstrings.
        annotate_variables (bool): Whether to annotate function-local
            variables.
        negotiate (bool): Whether to use contract negotiation for hints.
        engine (bool): Conversion mode: take the inference engine's
            annotations.
        cache (bool): Whether to reuse results for unchanged files.
        source_root (list[str] | None): Extra import roots for the type
            checker.
        project (bool): Whether to analyse the paths as one project.
        closed_world (bool): In project mode, assume every caller is in the
            file set.
        target_version (str | None): Oldest Python version emitted code must
            run on.
        exclude (list[str] | None): Path globs discovery skips.
        write_baseline (Path | None): File recording every current finding.
        baseline (Path | None): Accepted-baseline file suppressing known
            findings.
        no_docs (bool): Whether ``docs.*`` fixes are excluded.
        runtime_protocols (bool): Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general (bool): Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement (str): Where synthesized protocols land.
        backup (bool): Whether ``fix`` saves before-images for ``undo``.
        optimize_aliases (bool): Whether ``fix`` extracts repeated type
            patterns into PEP 695 ``type`` aliases.
        code (str): Rule code for the ``explain`` subcommand.
        location (str | None): Optional ``path:line[:col]`` finding location
            for ``explain``.
        run_id (str | None): Optional backup run id for ``undo``.
        json (bool): Whether ``rules`` emits the catalog as JSON.

    """

    command: str | None
    source: str
    stubs: str | None
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
    min_confidence: float | None
    create_constants_class: bool
    stub_docstrings: bool
    docstring_types: bool
    annotate_variables: bool
    negotiate: bool
    engine: bool
    cache: bool
    source_root: list[str] | None
    project: bool
    closed_world: bool
    target_version: str | None
    exclude: list[str] | None
    write_baseline: Path | None
    baseline: Path | None
    no_docs: bool
    runtime_protocols: bool
    accept_general: bool
    protocol_placement: str
    backup: bool
    optimize_aliases: bool
    code: str
    location: str | None
    run_id: str | None
    json: bool


def _package_version() -> str:
    """Return the installed astart version.

    Returns:
        str: The distribution version, or ``"0+unknown"`` when astart is not
            installed as a distribution.

    """
    try:
        return version(distribution_name="astart")
    except PackageNotFoundError:
        return "0+unknown"


@final
class _Group(Protocol):
    """Subset of a mutually-exclusive argument group used here."""

    def add_argument(self, name: str, /, *, action: str) -> Action:
        """Register a flag on the group.

        Args:
            name (str): Flag name.
            action (str): argparse action name.

        Returns:
            The created action.

        """
        ...


@final
class _SubParsers(Protocol):
    """Subset of the sub-parser registry used here.

    Attributes:
        add_parser (Callable[..., ArgumentParser]): Factory for subcommand
            parsers.

    """

    add_parser: Callable[..., ArgumentParser]


def _stubs(*, args: _Arguments) -> Path | None:
    """Return the optional stub directory.

    Args:
        args (_Arguments): Parsed arguments.

    Returns:
        Path | None: The directory, or ``None`` when it was not given.

    """
    return Path(args.stubs_dir) if args.stubs_dir else None


def _floor(*, args: _Arguments) -> float:
    """Pick the confidence floor: the flag, else the mode's default.

    Args:
        args (_Arguments): Parsed arguments.

    Returns:
        float: The flag when given; ``0.5`` in conversion mode (``--engine``),
            otherwise the standard default.

    """
    if args.min_confidence is not None:
        return args.min_confidence
    return 0.5 if args.engine else ConfidenceConstants.default_minimum


def _mode(*, args: _Arguments) -> FixMode:
    """Pick the fix mode from the flags.

    Args:
        args (_Arguments): Parsed arguments.

    Returns:
        FixMode: ``diff``, ``check`` or ``write``.

    """
    if args.diff:
        return FixMode.diff
    return FixMode.check if args.check else FixMode.write


def _configure_check(*, command: ArgumentParser) -> None:
    """Add the ``check`` subcommand's arguments.

    Args:
        command (ArgumentParser): Parser of the ``check`` subcommand.

    """
    command.add_argument("paths", nargs="+")
    command.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json", "sarif", "junit", "github"),
        default="text",
    )
    command.add_argument(
        "--fail-on",
        choices=tuple(item.value for item in Severity),
        default=Severity.error.value,
    )
    command.add_argument("--stubs", dest="stubs_dir")
    command.add_argument(
        "--project",
        action="store_true",
        help="Analyse the discovered files as one project",
    )
    command.add_argument(
        "--closed-world",
        action="store_true",
        help="With --project, assume all callers are in the file set",
    )
    command.add_argument(
        "--source-root",
        action="append",
        help="Directory absolute imports resolve from (repeatable)",
    )
    command.add_argument(
        "--target-version",
        help="Oldest Python version emitted code must run on",
    )
    command.add_argument(
        "--exclude",
        action="append",
        help="Skip paths matching this glob during discovery (repeatable)",
    )
    command.add_argument(
        "--write-baseline",
        type=Path,
        help="Record every current finding in this baseline file",
    )
    command.add_argument(
        "--baseline",
        type=Path,
        help="Suppress findings already recorded in this baseline file",
    )


def _configure_fix(*, command: ArgumentParser) -> None:
    """Add the ``fix`` subcommand's arguments.

    Args:
        command (ArgumentParser): Parser of the ``fix`` subcommand.

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
    command.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        help="Skip fixes below this confidence (default: 0.8, or 0.5 with "
        "--engine; 0 also "
        "writes int/str annotations taken from a literal default alone)",
    )
    command.add_argument(
        "--create-constants-class",
        action="store_true",
        help="Create a Constants class when a module has none",
    )
    command.add_argument(
        "--docstring-types",
        action=BooleanOptionalAction,
        default=True,
        help="Include annotation types in docstrings (default: enabled)",
    )
    command.add_argument(
        "--stub-docstrings",
        action="store_true",
        help="Add a stub docstring to undocumented public definitions",
    )
    command.add_argument(
        "--annotate-variables",
        action="store_true",
        help="Annotate function-local variables the evidence proves",
    )
    command.add_argument(
        "--engine",
        action="store_true",
        help="Conversion mode: also take the inference engine's own "
        "annotations where nothing else decided (lowers the default "
        "--min-confidence to 0.5; the checker gate still applies)",
    )
    command.add_argument(
        "--no-negotiate",
        dest="negotiate",
        action="store_false",
        help="Do not use contract negotiation for parameter and return hints",
    )
    command.add_argument(
        "--cache",
        action="store_true",
        help="Reuse results for unchanged files (stored in .astart_cache)",
    )
    command.add_argument(
        "--source-root",
        action="append",
        help="Directory the type checker resolves imports from (repeatable)",
    )
    command.add_argument(
        "--project",
        action="store_true",
        help="Analyse the discovered files as one project",
    )
    command.add_argument(
        "--closed-world",
        action="store_true",
        help="With --project, assume all callers are in the file set",
    )
    command.add_argument(
        "--target-version",
        help="Oldest Python version emitted code must run on",
    )
    command.add_argument(
        "--exclude",
        action="append",
        help="Skip paths matching this glob during discovery (repeatable)",
    )
    command.add_argument(
        "--no-docs",
        action="store_true",
        help="Skip docs.* fixes, applying typing and structure fixes only",
    )
    command.add_argument(
        "--runtime-protocols",
        action="store_true",
        help=(
            "Emit @runtime_checkable on synthesized protocols used "
            "under isinstance"
        ),
    )
    command.add_argument(
        "--accept-general",
        action="store_true",
        help="Prefer abstract collection types over synthesized "
        "protocols for read-only container parameters",
    )
    command.add_argument(
        "--protocol-placement",
        choices=("module", "function", "type-checking"),
        default="module",
        help="Where synthesized protocols land (default: module)",
    )
    command.add_argument(
        "--optimize-aliases",
        action=BooleanOptionalAction,
        default=True,
        help="Extract repeated type patterns as PEP 695 aliases "
        "(default: enabled)",
    )
    command.add_argument(
        "--backup",
        action="store_true",
        help=(
            "Save before-images under .astart-backup/<run-id>/ for astart undo"
        ),
    )


def _run_catalog_command(*, args: _Arguments) -> int:
    """Dispatch the catalog commands: ``rules``, ``explain`` and ``undo``.

    Args:
        args (_Arguments): Parsed command-line arguments.

    Returns:
        int: The command's exit status.

    """
    if args.command == "rules":
        return run_rules(out=stdout, as_json=args.json)
    if args.command == "undo":
        return run_undo(run_id=args.run_id, out=stdout, err=stderr)
    if args.location is None:
        return run_explain(code=args.code, out=stdout, err=stderr)
    return run_explain_at(
        code=args.code,
        location=args.location,
        out=stdout,
        err=stderr,
    )


def _arm_sensors() -> None:
    """Wrap every loaded ``astart`` callable when ``ASTART_SENSORS`` is set.

    Registers an exit-time report of wall and CPU time per function on
    ``stderr``. ``astart.source.metrics`` itself is excluded so the
    collector is never measured.

    """
    if not sensors.enabled():
        return
    for module in list(modules.values()):
        if (
            getattr(module, "__name__", "").startswith("astart.")
            and module.__name__ != "astart.source.metrics"
        ):
            sensors.instrument(module=module, skip_private=False)

    def _emit(*args: int | FrameType | None) -> None:
        """Write the flat table and cascade to the artifact and stderr.

        Args:
            args (int | FrameType | None): Signal arguments forwarded on
                ``SIGUSR1``; unused.

        """
        _ = args
        out_dir: Path = Path("scripts") / "benchmark" / "artifacts" / "results"
        sensors.dump(directory=out_dir)
        sensors.report()
        sensors.trace_report(min_wall_ns=1_000_000)

    register(_emit)
    signal(signalnum=SIGUSR1, handler=_emit)


def main(*, argv: list[str] | None = None) -> int:
    """Convert a Python file through the same safe AST API as library callers.

    Args:
        argv (list[str] | None): Optional CLI arguments; defaults to process
            arguments.

    Returns:
        int: Process status, zero after successful transformation.

    Raises:
        OSError: Source, output, or stub paths cannot be accessed.
        SyntaxError: The input or reconstructed source is not valid Python.
        UnicodeError: Source cannot be decoded using its declared encoding.

    """
    _arm_sensors()
    parser: ArgumentParser = ArgumentParser(prog="astart")
    parser.add_argument(
        "--version",
        action="version",
        version=_package_version(),
    )
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
    configure_transform(
        command=commands.add_parser(
            name="transform",
            help="Explicit native AST wrapping and runtime insertion",
        ),
    )
    command: ArgumentParser = commands.add_parser(
        name="convert",
        help="Infer and safely apply source annotations",
    )
    command.add_argument("--source", required=True)
    command.add_argument("--stubs")
    command.add_argument("--output", required=True)
    command.add_argument("--report")
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--strict-formatting", action="store_true")
    rules_parser: ArgumentParser = commands.add_parser(
        name="rules",
        help="List every rule",
    )
    rules_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the listing as JSON",
    )
    explain: ArgumentParser = commands.add_parser(
        name="explain",
        help="Explain a rule code",
    )
    explain.add_argument("code")
    explain.add_argument(
        "location",
        nargs="?",
        help="Optional path:line[:col] of a finding to explain",
    )
    undo: ArgumentParser = commands.add_parser(
        name="undo",
        help="Restore files of a fix --backup run",
    )
    undo.add_argument(
        "run_id",
        nargs="?",
        help="Run id under .astart-backup (default: newest)",
    )
    args: _Arguments = cast(typ="_Arguments", val=parser.parse_args(args=argv))
    if args.command is None:
        parser.print_help()
    else:
        if args.command == "transform":
            return run_transform(
                args=cast(typ="TransformArguments", val=args),
                out=stdout,
            )
        if args.command in ("rules", "explain", "undo"):
            return _run_catalog_command(args=args)
        if args.command == "check":
            return run_check(
                settings=CheckSettings(
                    paths=tuple(Path(item) for item in args.paths),
                    output_format=args.output_format,
                    fail_on=Severity(args.fail_on),
                    stubs_path=_stubs(args=args),
                    project=args.project,
                    assume_external_callers=not args.closed_world,
                    source_roots=tuple(
                        Path(item) for item in args.source_root or ()
                    ),
                    target_version=args.target_version,
                    exclude=tuple(args.exclude or ()),
                    write_baseline=args.write_baseline,
                    baseline=args.baseline,
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
                    min_confidence=_floor(args=args),
                    create_constants=args.create_constants_class,
                    stub_docstrings=args.stub_docstrings,
                    docstring_types=args.docstring_types,
                    annotate_variables=args.annotate_variables,
                    negotiate=args.negotiate,
                    engine=args.engine,
                    use_cache=args.cache,
                    source_roots=tuple(
                        Path(item) for item in args.source_root or ()
                    ),
                    project=args.project,
                    assume_external_callers=not args.closed_world,
                    target_version=args.target_version,
                    exclude=tuple(args.exclude or ()),
                    no_docs=args.no_docs,
                    runtime_protocols=args.runtime_protocols,
                    accept_general=args.accept_general,
                    protocol_placement=args.protocol_placement,
                    backup=args.backup,
                    optimize_aliases=args.optimize_aliases,
                ),
                out=stdout,
            )
        input_path: Path = Path(args.source)
        data: bytes = input_path.read_bytes()
        encoding: str = detect_encoding(
            readline=BytesIO(initial_bytes=data).readline,
        )[0]
        source: str = data.decode(encoding=encoding)
        tree: CommentedModule = parse(
            source=source,
            filename=str(object=input_path),
        )
        result: GraphConversion = convert(
            tree=tree,
            stubs_path=Path(args.stubs) if args.stubs else None,
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
