"""Implement the ``check`` and ``fix`` commands."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from difflib import unified_diff
from enum import StrEnum
from io import BytesIO
from os import fsync
from pathlib import Path
from shutil import copymode
from sysconfig import get_paths
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Final, final

from astart.cli.cache import (
    CachedFix,
    FixCache,
    tool_fingerprint,
)
from astart.cli.cache import (
    Constants as CacheConstants,
)
from astart.cli.discovery import DiscoveryResult, discover_files
from astart.cli.render import FileReport, render_json, render_text
from astart.project.builder import build_index
from astart.project.index import ProjectConfig
from astart.project.libraries import LibraryIndex, find_library_roots
from astart.project.naming import module_name
from astart.project.versions import (
    PythonTarget,
    find_pyproject,
    resolve_target,
)
from astart.rules import (
    CheckOptions,
    CheckResult,
    FixResult,
    FixSettings,
    FormatTarget,
    check,
    default_registries,
    fix_and_format,
    fix_source,
    load_default_catalog,
)
from astart.rules.checker import build_checker
from astart.rules.process import run_command
from astart.rules.project_bridge import ProjectView
from astart.rules.vocabulary import FixSafety, Severity

if TYPE_CHECKING:
    from typing import TextIO

    from astart.project.index import ProjectIndex
    from astart.rules.checker import Checker
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        cache_ignored: Settings that do not change a file's result.
        severity_rank: Grouped module constant.
        usage_error: Grouped module constant.
        findings: Grouped module constant.
        text_format: Grouped module constant.
        no_checker_floor: Precision floor when no checker runs.

    """

    severity_rank: Final[tuple[Severity, ...]] = (
        Severity.error,
        Severity.warning,
        Severity.info,
    )
    usage_error: Final[int] = 2
    findings: Final[int] = 1
    text_format: Final[str] = "text"
    no_checker_floor: Final[float] = 0.95
    cache_ignored: Final[frozenset[str]] = frozenset(
        {"paths", "mode", "use_cache"},
    )


@final
@dataclass(frozen=True, slots=True)
class CheckSettings:
    """Options of the ``check`` command.

    Attributes:
        paths: Files and directories to check.
        output_format: ``text`` or ``json``.
        fail_on: Least severe finding that makes the exit status non-zero.
        stubs_path: Stub directory for type hints, or ``None``.
        project: Whether to analyse the discovered files as one project.
        assume_external_callers: In project mode, whether exported
            functions may have callers outside the file set.
        source_roots: Import roots for deriving dotted module names.
        target_version: Oldest Python version emitted code must run on,
            or ``None`` to read ``pyproject.toml``/the interpreter.
        exclude: ``fnmatch`` globs discovery skips.

    """

    paths: tuple[Path, ...]
    output_format: str
    fail_on: Severity
    stubs_path: Path | None
    project: bool = False
    assume_external_callers: bool = True
    source_roots: tuple[Path, ...] = ()
    target_version: str | None = None
    exclude: tuple[str, ...] = ()


@final
class FixMode(StrEnum):
    """What ``fix`` does with the fixed text.

    Attributes:
        write: Replace the file.
        diff: Print a unified diff and leave the file.
        check: Only report whether changes are pending.

    """

    write = "write"
    diff = "diff"
    check = "check"


@final
@dataclass(frozen=True, slots=True)
class FixCommandSettings:
    """Options of the ``fix`` command.

    Attributes:
        paths: Files and directories to fix.
        ceiling: Highest fix safety to apply.
        stubs_path: Stub directory for type hints, or ``None``.
        mode: Write, diff or check.
        run_formatter: Whether ruff formats the result.
        use_checker: Whether an installed pyright must accept guarded fixes.
        min_confidence: Fixes with less confidence than this are skipped.
        create_constants: Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        stub_docstrings: Whether undocumented public definitions get a stub
            docstring.
        annotate_variables: Whether function-local variables get a type
            annotation.
        negotiate: Whether negotiated annotations supplement the hint
            index.
        engine: Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        use_cache: Whether unchanged files are served from the on-disk cache.
        source_roots: Extra directories the type checker resolves absolute
            imports from.
        project: Whether to analyse the discovered files as one project.
        assume_external_callers: In project mode, whether exported
            functions may have callers outside the file set.
        target_version: Oldest Python version emitted code must run on,
            or ``None`` to read ``pyproject.toml``/the interpreter.
        exclude: ``fnmatch`` globs discovery skips.
        no_docs: Whether ``docs.*`` fixes are excluded from the run.

    """

    paths: tuple[Path, ...]
    ceiling: FixSafety
    stubs_path: Path | None
    mode: FixMode
    run_formatter: bool
    use_checker: bool = False
    min_confidence: float = 0.0
    create_constants: bool = False
    stub_docstrings: bool = False
    annotate_variables: bool = False
    negotiate: bool = True
    engine: bool = False
    use_cache: bool = False
    source_roots: tuple[Path, ...] = ()
    project: bool = False
    assume_external_callers: bool = True
    target_version: str | None = None
    exclude: tuple[str, ...] = ()
    no_docs: bool = False


@final
@dataclass(frozen=True, slots=True)
class FixOutcome:
    """Result of fixing one file.

    Attributes:
        path: File name.
        before: Original text.
        after: Fixed text.
        applied: Number of fixes applied.
        skipped: Descriptions of fixes that were not applied.
        error: Why the file could not be fixed, if it could not.
        note: Formatter note, empty when there is none.

    """

    path: Path
    before: str
    after: str
    applied: int
    skipped: tuple[str, ...]
    error: str | None
    note: str


@final
@dataclass(frozen=True, slots=True)
class SourceFile:
    """A decoded source file.

    Attributes:
        text: Decoded source text.
        encoding: Encoding to write the file back with.

    """

    text: str
    encoding: str


def severity_reaches(*, severity: Severity, threshold: Severity) -> bool:
    """Tell whether a severity is at least as severe as a threshold.

    Args:
        severity: Severity of a finding.
        threshold: Least severe level of interest.

    Returns:
        ``True`` when ``severity`` is the threshold or more severe.

    """
    ranks: tuple[Severity, ...] = Constants.severity_rank
    return ranks.index(severity) <= ranks.index(threshold)


def read_source(*, path: Path) -> SourceFile:
    """Read a Python file using its declared encoding.

    Args:
        path: File to read.

    Returns:
        The decoded text and its encoding.

    Raises:
        OSError: The file cannot be read.
        SyntaxError: The encoding declaration is invalid.
        UnicodeError: The bytes do not decode in the declared encoding.

    """
    data: bytes = path.read_bytes()
    encoding: str = detect_encoding(
        readline=BytesIO(initial_bytes=data).readline,
    )[0]
    return SourceFile(text=data.decode(encoding=encoding), encoding=encoding)


def _target_for(
    *,
    configured: str | None,
    paths: tuple[Path, ...],
) -> PythonTarget:
    """Resolve the Python version emitted code must run on.

    Args:
        configured: Explicit ``major.minor`` target, or ``None``.
        paths: Command paths, used to find the governing
            ``pyproject.toml``.

    Returns:
        The target.

    """
    return resolve_target(
        configured=configured,
        pyproject=find_pyproject(paths=paths),
    )


def _index_for(
    *,
    found: DiscoveryResult,
    enabled: bool,
    assume_external_callers: bool,
    source_roots: tuple[Path, ...],
) -> ProjectIndex | None:
    """Build the project index when project mode is on.

    Args:
        found: Discovered files.
        enabled: Whether project mode was requested.
        assume_external_callers: Whether exported functions may have
            callers outside the file set.
        source_roots: Import roots for dotted module naming.

    Returns:
        The index, or ``None`` when project mode is off.

    """
    if not enabled:
        return None
    return build_index(
        files=found.files,
        source_roots=source_roots,
        config=ProjectConfig(
            assume_external_callers=assume_external_callers,
        ),
    ).index


def _site_packages() -> tuple[Path, ...]:
    """Directories holding the running environment's installed packages.

    Returns:
        The ``purelib``/``platlib`` directories that exist.

    """
    paths: dict[str, str] = get_paths()
    out: list[Path] = []
    for key in ("purelib", "platlib"):
        candidate: Path = Path(paths[key])
        if candidate.is_dir() and candidate not in out:
            out.append(candidate)
    return tuple(out)


def _libraries_for(
    *,
    enabled: bool,
    stubs_path: Path | None,
) -> LibraryIndex | None:
    """Build the external signature index when project mode is on.

    Args:
        enabled: Whether project mode was requested.
        stubs_path: Typeshed root, or ``None``.

    Returns:
        The index over typeshed, ``py.typed`` and stub-only packages, or
        ``None``.

    """
    if not enabled:
        return None
    return LibraryIndex(
        typeshed=stubs_path,
        roots=find_library_roots(
            site_packages=_site_packages(),
            typeshed=stubs_path,
        ),
    )


def _view_for(
    *,
    index: ProjectIndex | None,
    path: Path,
    source_roots: tuple[Path, ...],
    libraries: LibraryIndex | None = None,
) -> ProjectView | None:
    """Derive one file's view of the project index.

    Args:
        index: Whole-project index, or ``None``.
        path: File being analysed.
        source_roots: Import roots for dotted module naming.
        libraries: External signature index, or ``None``.

    Returns:
        The view, or ``None`` when the file is not part of the index.

    """
    if index is None:
        return None
    name: str | None = module_name(path=path, source_roots=source_roots)
    if name is None or index.module_scan(module=name) is None:
        return None
    return ProjectView(index=index, module=name, libraries=libraries)


def _check_file(
    *,
    path: Path,
    catalog: Catalog,
    options: CheckOptions,
) -> FileReport:
    """Check one file, turning every failure into a report.

    Args:
        path: File to check.
        catalog: Rules to apply.
        options: Engine options.

    Returns:
        The findings, or the reason the file could not be analysed.

    """
    try:
        source: SourceFile = read_source(path=path)
    except (OSError, SyntaxError, UnicodeError) as error:
        return FileReport(
            path=str(object=path),
            findings=(),
            error=str(object=error),
        )
    result: CheckResult = check(
        source=source.text,
        filename=str(object=path),
        catalog=catalog,
        registries=default_registries(),
        options=options,
    )
    return FileReport(
        path=str(object=path),
        findings=result.findings,
        error=result.parse_error,
    )


def run_check(*, settings: CheckSettings, out: TextIO) -> int:
    """Check files and print the findings.

    Args:
        settings: Paths and output options.
        out: Stream the report is written to.

    Returns:
        ``0`` when clean, ``1`` when a finding reaches ``fail_on``, ``2`` when
        a path is missing or a file cannot be analysed.

    """
    found: DiscoveryResult = discover_files(
        paths=settings.paths,
        exclude=settings.exclude,
    )
    catalog: Catalog = load_default_catalog(registries=default_registries())
    index: ProjectIndex | None = _index_for(
        found=found,
        enabled=settings.project,
        assume_external_callers=settings.assume_external_callers,
        source_roots=settings.source_roots,
    )
    libraries: LibraryIndex | None = _libraries_for(
        enabled=settings.project,
        stubs_path=settings.stubs_path,
    )
    target: PythonTarget = _target_for(
        configured=settings.target_version,
        paths=settings.paths,
    )
    reports: list[FileReport] = [
        _check_file(
            path=path,
            catalog=catalog,
            options=CheckOptions(
                stubs_path=settings.stubs_path,
                project=_view_for(
                    index=index,
                    path=path,
                    source_roots=settings.source_roots,
                    libraries=libraries,
                ),
                libraries=libraries,
                target=target,
            ),
        )
        for path in found.files
    ]
    reports.extend(
        FileReport(
            path=str(object=path),
            findings=(),
            error="no such file or directory",
        )
        for path in found.missing
    )
    if settings.output_format == "json":
        _ = out.write(
            render_json(results=reports, catalog=catalog)
            + """\

""",
        )
    else:
        for report in reports:
            if report.error is not None:
                _ = out.write(f"""\
{report.path}: error: {report.error}
""")
            for finding in report.findings:
                _ = out.write(
                    render_text(finding=finding, catalog=catalog)
                    + """\

""",
                )
    if any(report.error is not None for report in reports):
        return Constants.usage_error
    reached: bool = any(
        severity_reaches(severity=finding.severity, threshold=settings.fail_on)
        for report in reports
        for finding in report.findings
    )
    return Constants.findings if reached else 0


def run_rules(*, out: TextIO) -> int:
    """Print every catalog rule, one per line, sorted by code.

    Args:
        out: Stream the listing is written to.

    Returns:
        Always zero.

    """
    catalog: Catalog = load_default_catalog(registries=default_registries())
    for rule in sorted(catalog.rules, key=lambda item: item.code):
        _ = out.write(
            f"{rule.code}  {rule.key}  {rule.severity.value}  {rule.title}\n",
        )
    return 0


def run_explain(*, code: str, out: TextIO, err: TextIO) -> int:
    """Print a rule's rationale and its triggering and clean examples.

    Args:
        code: Rule code to explain.
        out: Stream the explanation is written to.
        err: Stream the error is written to.

    Returns:
        Zero when the code is known, ``Constants.usage_error`` otherwise.

    """
    catalog: Catalog = load_default_catalog(registries=default_registries())
    for rule in catalog.rules:
        if rule.code == code:
            break
    else:
        _ = err.write(f"astart: unknown rule code: {code}\n")
        return Constants.usage_error
    _ = out.write(f"{rule.code}  {rule.key}  {rule.title}\n")
    _ = out.write(f"{rule.rationale}\n")
    for example in rule.examples:
        marker: str = "flagged" if example.triggers else "clean"
        _ = out.write(f"\n{marker}:\n{example.source}\n")
    return 0


def _write_atomic(*, path: Path, text: str, encoding: str) -> None:
    """Replace a file without ever leaving it half written.

    Symbolic links are followed, so the link stays a link; the file keeps its
    permissions; the temporary file never outlives the call.

    Args:
        path: File to replace.
        text: New text.
        encoding: Encoding to write with.

    """
    target: Path = path.resolve()
    temporary: Path = target.with_name(name=target.name + ".astart-tmp")
    try:
        with temporary.open(mode="wb") as handle:
            _ = handle.write(text.encode(encoding=encoding))
            handle.flush()
            fsync(fd=handle.fileno())
        copymode(src=target, dst=temporary)
        _ = temporary.replace(target=target)
    finally:
        temporary.unlink(missing_ok=True)


def _make_checker(*, settings: FixCommandSettings) -> Checker | None:
    """Build the external type-checker gate when it is wanted and installed.

    Args:
        settings: Command options.

    Returns:
        A checker, or ``None`` when disabled or no checker is installed.

    """
    if not settings.use_checker:
        return None
    return build_checker(
        root=Path.cwd(),
        source_roots=settings.source_roots,
    )


@final
@dataclass(frozen=True, slots=True)
class _ProjectContext:
    """Whole-project services shared by every file of a run.

    Attributes:
        index: Whole-project index, or ``None`` for single-file mode.
        libraries: External signature index, or ``None``.
        cache: On-disk result cache, or ``None``.

    """

    index: ProjectIndex | None = None
    libraries: LibraryIndex | None = None
    cache: FixCache | None = None


def _fix_file(
    *,
    path: Path,
    settings: FixCommandSettings,
    catalog: Catalog,
    checker: Checker | None,
    project: _ProjectContext,
) -> FixOutcome:
    """Fix one file in memory.

    Args:
        path: File to fix.
        settings: Command options.
        catalog: Rules and fixes.
        checker: External type-checker gate, or ``None``.
        project: Whole-project services, empty for single-file mode.

    Returns:
        What happened; failures are reported, never raised.

    """
    try:
        source: SourceFile = read_source(path=path)
    except (OSError, SyntaxError, UnicodeError) as error:
        return FixOutcome(
            path=path,
            before="",
            after="",
            applied=0,
            skipped=(),
            error=str(object=error),
            note="",
        )
    cache: FixCache | None = project.cache if project.index is None else None
    if cache is not None:
        hit: CachedFix | None = cache.load(path=path, source=source.text)
        if hit is not None:
            return FixOutcome(
                path=path,
                before=source.text,
                after=hit.after,
                applied=hit.applied,
                skipped=hit.skipped,
                error=None,
                note=hit.note,
            )
    fix_settings: FixSettings = FixSettings(
        ceiling=settings.ceiling,
        stubs_path=settings.stubs_path,
        min_confidence=settings.min_confidence,
        create_constants=settings.create_constants,
        stub_docstrings=settings.stub_docstrings,
        annotate_variables=settings.annotate_variables,
        negotiate=settings.negotiate,
        engine=settings.engine,
        checker=checker,
        project=_view_for(
            index=project.index,
            path=path,
            source_roots=settings.source_roots,
            libraries=project.libraries,
        ),
        libraries=project.libraries,
        target=_target_for(
            configured=settings.target_version,
            paths=settings.paths,
        ),
        excluded_prefixes=("docs.",) if settings.no_docs else (),
    )
    registries: Registries = default_registries()
    note: str = ""
    if settings.run_formatter:
        fixed, formatted = fix_and_format(
            source=source.text,
            target=FormatTarget(
                filename=str(object=path),
                cwd=path.resolve().parent,
            ),
            catalog=catalog,
            registries=registries,
            settings=fix_settings,
        )
        text: str = formatted.source
        note = formatted.note
    else:
        fixed: FixResult = fix_source(
            source=source.text,
            filename=str(object=path),
            catalog=catalog,
            registries=registries,
            settings=fix_settings,
        )
        text = fixed.source
    outcome: FixOutcome = _outcome(
        path=path,
        before=source.text,
        after=text,
        fixed=fixed,
        note=note,
    )
    if cache is not None and outcome.error is None:
        cache.store(
            path=path,
            source=source.text,
            entry=CachedFix(
                after=outcome.after,
                applied=outcome.applied,
                skipped=outcome.skipped,
                note=outcome.note,
            ),
        )
    return outcome


def _outcome(
    *,
    path: Path,
    before: str,
    after: str,
    fixed: FixResult,
    note: str,
) -> FixOutcome:
    """Summarise a fix result.

    Args:
        path: File name.
        before: Original text.
        after: Final text.
        fixed: Fix runner result.
        note: Formatter note.

    Returns:
        The per-file outcome.

    """
    return FixOutcome(
        path=path,
        before=before,
        after=after if fixed.parse_error is None else before,
        applied=len(fixed.applied),
        skipped=tuple(
            (f"{item.fix_key} at {item.subject_path}: {item.reason}")
            for item in fixed.skipped
        ),
        error=fixed.parse_error,
        note=note,
    )


def _make_cache(
    *,
    settings: FixCommandSettings,
    checker: Checker | None,
) -> FixCache | None:
    """Open the result cache when it is wanted.

    Args:
        settings: Command options.
        checker: External type-checker gate, or ``None``.

    Returns:
        A cache keyed on everything that decides a result, or ``None``.

    """
    if not settings.use_cache:
        return None
    options: list[str] = [
        f"{item.name}={getattr(settings, item.name)!r}"
        for item in fields(class_or_instance=settings)
        if item.name not in Constants.cache_ignored
    ]
    try:
        formatter: str = run_command(
            arguments=("ruff", "--version"),
            cwd=Path.cwd(),
        ).stdout
    except (OSError, TimeoutError):
        formatter = ""
    environment: str = repr((options, type(checker).__name__, formatter))
    return FixCache(
        directory=Path.cwd() / CacheConstants.directory,
        fingerprint=tool_fingerprint(environment=environment, root=Path.cwd()),
    )


def run_fix(*, settings: FixCommandSettings, out: TextIO) -> int:
    """Fix files in place, or show or check what would change.

    Args:
        settings: Paths, safety ceiling and mode.
        out: Stream the report is written to.

    Returns:
        ``0`` when nothing changes, ``1`` when files changed or would change,
        ``2`` when a path is missing or a file cannot be fixed.

    """
    found: DiscoveryResult = discover_files(
        paths=settings.paths,
        exclude=settings.exclude,
    )
    catalog: Catalog = load_default_catalog(registries=default_registries())
    failed: bool = bool(found.missing)
    index: ProjectIndex | None = _index_for(
        found=found,
        enabled=settings.project,
        assume_external_callers=settings.assume_external_callers,
        source_roots=settings.source_roots,
    )
    libraries: LibraryIndex | None = _libraries_for(
        enabled=settings.project,
        stubs_path=settings.stubs_path,
    )
    checker: Checker | None = _make_checker(settings=settings)
    if settings.use_checker and checker is None:
        settings = replace(
            settings,
            min_confidence=max(
                settings.min_confidence,
                Constants.no_checker_floor,
            ),
        )
        _ = out.write(f"""\
note: no type checker found; guarded fixes need confidence >= \
{Constants.no_checker_floor}
""")
    cache: FixCache | None = _make_cache(settings=settings, checker=checker)
    for path in found.missing:
        _ = out.write(f"""\
{path}: error: no such file or directory
""")
    changed: int = 0
    applied: int = 0
    skipped: int = 0
    for path in found.files:
        outcome: FixOutcome = _fix_file(
            path=path,
            settings=settings,
            catalog=catalog,
            checker=checker,
            project=_ProjectContext(
                index=index,
                libraries=libraries,
                cache=cache,
            ),
        )
        if outcome.error is not None:
            failed = True
            _ = out.write(f"""\
{path}: error: {outcome.error}
""")
            continue
        skipped += len(outcome.skipped)
        for line in outcome.skipped:
            _ = out.write(f"""\
{path}: skipped {line}
""")
        if outcome.note:
            _ = out.write(f"""\
{path}: note: {outcome.note}
""")
        if outcome.after == outcome.before:
            continue
        changed += 1
        applied += outcome.applied
        _emit(path=path, outcome=outcome, settings=settings, out=out)
    summary: str = f"""\
{changed} files changed, {applied} fixes applied, {skipped} skipped
"""
    _ = out.write(summary)
    if failed:
        return Constants.usage_error
    return Constants.findings if changed else 0


def _emit(
    *,
    path: Path,
    outcome: FixOutcome,
    settings: FixCommandSettings,
    out: TextIO,
) -> None:
    """Write, diff or just count one changed file.

    Args:
        path: File name.
        outcome: Its fix outcome.
        settings: Command options.
        out: Report stream.

    """
    if settings.mode is FixMode.write:
        encoding: str = read_source(path=path).encoding
        _write_atomic(path=path, text=outcome.after, encoding=encoding)
    elif settings.mode is FixMode.diff:
        _ = out.writelines(
            unified_diff(
                a=outcome.before.splitlines(keepends=True),
                b=outcome.after.splitlines(keepends=True),
                fromfile=str(object=path),
                tofile=str(object=path),
            ),
        )
