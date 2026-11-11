"""Implement the ``check`` and ``fix`` commands."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from datetime import UTC, datetime
from difflib import unified_diff
from enum import StrEnum
from os import environ
from pathlib import Path
from sysconfig import get_paths
from typing import TYPE_CHECKING, Final, final

from astart.cli import backup
from astart.cli.atomic import write_atomic
from astart.cli.baseline import (
    BaselineError,
    apply_baseline,
    load_baseline,
    save_baseline,
)
from astart.cli.cache import (
    CachedFix,
    FixCache,
    tool_fingerprint,
)
from astart.cli.cache import (
    Constants as CacheConstants,
)
from astart.cli.discovery import DiscoveryResult, discover_files
from astart.cli.github import render_github
from astart.cli.junit import render_junit
from astart.cli.render import (
    FileReport,
    render_evidence,
    render_json,
    render_message,
    render_text,
)
from astart.cli.sarif import render_sarif
from astart.files import SourceFile, read_source
from astart.project.builder import build_index
from astart.project.index import ProjectConfig
from astart.project.libraries import LibraryIndex, find_library_roots
from astart.project.naming import module_name
from astart.project.typeshed_client import TypeshedClientIndex
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
from astart.rules.jsonvalue import canonical_dumps
from astart.rules.process import run_command
from astart.rules.project_bridge import ProjectView
from astart.rules.vocabulary import FixSafety, Severity
from astart.stubs.locate import find_typeshed

if TYPE_CHECKING:
    from typing import TextIO

    from astart.project.index import ProjectIndex
    from astart.rules.checker import Checker
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Finding, Rule
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        cache_ignored (Final[frozenset[str]]): Settings that do not change a
            file's result.
        severity_rank (Final[tuple[Severity, ...]]): Grouped module constant.
        usage_error (Final[int]): Grouped module constant.
        findings (Final[int]): Grouped module constant.
        text_format (Final[str]): Grouped module constant.
        no_checker_floor (Final[float]): Precision floor when no checker runs.
        typeshed_client_environment (Final[str]): Opt-in variable enabling the
            ``typeshed_client`` stub backend in project mode.

    """

    typeshed_client_environment: Final[str] = "ASTART_TYPESHED_CLIENT"

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
        paths (tuple[Path, ...]): Files and directories to check.
        output_format (str): ``text``, ``json``, ``sarif``, ``junit`` or
            ``github``.
        fail_on (Severity): Least severe finding that makes the exit status
            non-zero.
        stubs_path (Path | None): Stub directory for type hints, or ``None``.
        project (bool): Whether to analyse the discovered files as one project.
        assume_external_callers (bool): In project mode, whether exported
            functions may have callers outside the file set.
        source_roots (tuple[Path, ...]): Import roots for deriving dotted
            module names.
        target_version (str | None): Oldest Python version emitted code must
            run on, or
            ``None`` to read ``pyproject.toml`` /the interpreter.
        exclude (tuple[str, ...]): ``fnmatch`` globs discovery skips.
        write_baseline (Path | None): File that captures every current finding,
            or ``None``.
        baseline (Path | None): File whose findings are suppressed, or ``None``
            .

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
    write_baseline: Path | None = None
    baseline: Path | None = None


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
        paths (tuple[Path, ...]): Files and directories to fix.
        ceiling (FixSafety): Highest fix safety to apply.
        stubs_path (Path | None): Stub directory for type hints, or ``None``.
        mode (FixMode): Write, diff or check.
        run_formatter (bool): Whether ruff formats the result.
        use_checker (bool): Whether an installed pyright must accept guarded
            fixes.
        min_confidence (float): Fixes with less confidence than this are
            skipped.
        create_constants (bool): Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        docstring_types (bool): Include annotation types in generated
            documentation.
        stub_docstrings (bool): Whether undocumented public definitions get a
            stub docstring.
        annotate_variables (bool): Whether function-local variables get a type
            annotation.
        negotiate (bool): Whether negotiated annotations supplement the hint
            index.
        engine (bool): Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        use_cache (bool): Whether unchanged files are served from the on-disk
            cache.
        source_roots (tuple[Path, ...]): Extra directories the type checker
            resolves absolute imports from.
        project (bool): Whether to analyse the discovered files as one project.
        assume_external_callers (bool): In project mode, whether exported
            functions may have callers outside the file set.
        target_version (str | None): Oldest Python version emitted code must
            run on, or
            ``None`` to read ``pyproject.toml`` /the interpreter.
        exclude (tuple[str, ...]): ``fnmatch`` globs discovery skips.
        no_docs (bool): Whether ``docs.*`` fixes are excluded from the run.
        runtime_protocols (bool): Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general (bool): Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement (str): Where synthesized protocols land:
            ``"module"``, ``"function"`` or ``"type-checking"``.
        backup (bool): Whether rewritten files get a before-image under
            ``.astart-backup/<run-id>/`` for ``astart undo``.
        optimize_aliases (bool): Whether repeated type patterns are
            extracted into PEP 695 ``type`` aliases after the fixes settle.

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
    docstring_types: bool = True
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
    runtime_protocols: bool = False
    accept_general: bool = False
    protocol_placement: str = "module"
    backup: bool = False
    optimize_aliases: bool = True


@final
@dataclass(frozen=True, slots=True)
class FixOutcome:
    """Result of fixing one file.

    Attributes:
        path (Path): File name.
        before (str): Original text.
        after (str): Fixed text.
        applied (int): Number of fixes applied.
        skipped (tuple[str, ...]): Descriptions of fixes that were not applied.
        error (str | None): Why the file could not be fixed, if it could not.
        note (str): Formatter note, empty when there is none.

    """

    path: Path
    before: str
    after: str
    applied: int
    skipped: tuple[str, ...]
    error: str | None
    note: str


def severity_reaches(*, severity: Severity, threshold: Severity) -> bool:
    """Tell whether a severity is at least as severe as a threshold.

    Args:
        severity (Severity): Severity of a finding.
        threshold (Severity): Least severe level of interest.

    Returns:
        bool: ``True`` when ``severity`` is the threshold or more severe.

    """
    ranks: tuple[Severity, ...] = Constants.severity_rank
    return ranks.index(severity) <= ranks.index(threshold)


def _target_for(
    *,
    configured: str | None,
    paths: tuple[Path, ...],
) -> PythonTarget:
    """Resolve the Python version emitted code must run on.

    Args:
        configured (str | None): Explicit ``major.minor`` target, or ``None``.
        paths (tuple[Path, ...]): Command paths, used to find the governing
            ``pyproject.toml``.

    Returns:
        PythonTarget: The target.

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
        found (DiscoveryResult): Discovered files.
        enabled (bool): Whether project mode was requested.
        assume_external_callers (bool): Whether exported functions may have
            callers outside the file set.
        source_roots (tuple[Path, ...]): Import roots for dotted module naming.

    Returns:
        ProjectIndex | None: The index, or ``None`` when project mode is off.

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
        tuple[Path, ...]: The ``purelib``/``platlib`` directories that exist.

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
        enabled (bool): Whether project mode was requested.
        stubs_path (Path | None): Typeshed root, or ``None``.

    Returns:
        LibraryIndex | None: The index over typeshed, ``py.typed``
            and stub-only packages, or ``None``.

    """
    if not enabled:
        return None
    client: TypeshedClientIndex | None = (
        TypeshedClientIndex()
        if environ.get(Constants.typeshed_client_environment)
        else None
    )
    typeshed: Path | None = (
        stubs_path if stubs_path is not None else find_typeshed()
    )
    return LibraryIndex(
        typeshed=typeshed,
        roots=find_library_roots(
            site_packages=_site_packages(),
            typeshed=typeshed,
        ),
        client=client,
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
        index (ProjectIndex | None): Whole-project index, or ``None``.
        path (Path): File being analysed.
        source_roots (tuple[Path, ...]): Import roots for dotted module naming.
        libraries (LibraryIndex | None): External signature index, or ``None``.

    Returns:
        ProjectView | None:
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
        path (Path): File to check.
        catalog (Catalog): Rules to apply.
        options (CheckOptions): Engine options.

    Returns:
        FileReport: The findings, or the reason the file could not be analysed.

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
        settings (CheckSettings): Paths and output options.
        out (TextIO): Stream the report is written to.

    Returns:
        int: ``0`` when clean, ``1`` when a finding reaches ``fail_on`` ,
            ``2`` when a path is missing or a file cannot be analysed.

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
    reports, baseline_error = _with_baselines(
        settings=settings,
        reports=reports,
        out=out,
    )
    if baseline_error is not None:
        return baseline_error
    return _emit_check(
        settings=settings,
        reports=reports,
        catalog=catalog,
        out=out,
    )


def _emit_check(
    *,
    settings: CheckSettings,
    reports: list[FileReport],
    catalog: Catalog,
    out: TextIO,
) -> int:
    """Render the reports and compute the exit status.

    Args:
        settings (CheckSettings): Command options (format and ``fail_on``).
        reports (list[FileReport]): Reports to render, baselines already
            applied.
        catalog (Catalog): Rules catalog used to resolve rule metadata.
        out (TextIO): Stream the report is written to.

    Returns:
        int: ``0`` when clean, ``1`` when a finding reaches ``fail_on``, ``2``
            when a file could not be analysed.

    """
    payload: str | None = None
    if settings.output_format == "json":
        payload = render_json(results=reports, catalog=catalog)
    elif settings.output_format == "sarif":
        payload = render_sarif(results=reports, catalog=catalog)
    elif settings.output_format == "junit":
        payload = render_junit(results=reports, catalog=catalog)
    elif settings.output_format == "github":
        payload = render_github(results=reports, catalog=catalog)
    if payload is not None:
        _ = out.write(
            payload + "\n",
        )
    else:
        for report in reports:
            if report.error is not None:
                _ = out.write(f"""\
{report.path}: error: {report.error}
""")
            for finding in report.findings:
                _ = out.write(
                    render_text(finding=finding, catalog=catalog) + "\n",
                )
    if any(report.error is not None for report in reports):
        return Constants.usage_error
    reached: bool = any(
        severity_reaches(severity=finding.severity, threshold=settings.fail_on)
        for report in reports
        for finding in report.findings
    )
    return Constants.findings if reached else 0


def _with_baselines(
    *,
    settings: CheckSettings,
    reports: list[FileReport],
    out: TextIO,
) -> tuple[list[FileReport], int | None]:
    """Apply ``--write-baseline`` and ``--baseline`` to the reports.

    Args:
        settings (CheckSettings): Command options carrying the baseline paths.
        reports (list[FileReport]): Freshly collected reports.
        out (TextIO): Stream baseline errors are written to.

    Returns:
        tuple[list[FileReport], int | None]: ``(reports, None)`` on success —
            with baselined findings removed
            when ``--baseline`` was given — or ``(reports, exit_code)``
            when a baseline file cannot be written or read.

    """
    if settings.write_baseline is not None:
        try:
            save_baseline(results=reports, path=settings.write_baseline)
        except OSError as error:
            _ = out.write(f"error: cannot write baseline: {error}\n")
            return reports, Constants.usage_error
    if settings.baseline is None:
        return reports, None
    try:
        fingerprints: frozenset[str] = load_baseline(path=settings.baseline)
    except (OSError, BaselineError) as error:
        _ = out.write(f"error: cannot read baseline: {error}\n")
        return reports, Constants.usage_error
    return (
        list(apply_baseline(results=reports, fingerprints=fingerprints)),
        None,
    )


def run_rules(*, out: TextIO, as_json: bool = False) -> int:
    """Print every catalog rule, sorted by code.

    Args:
        out (TextIO): Stream the listing is written to.
        as_json (bool): Emit the machine-readable listing instead of text.

    Returns:
        int: Always zero.

    """
    catalog: Catalog = load_default_catalog(registries=default_registries())
    ordered: list[Rule] = sorted(catalog.rules, key=lambda item: item.code)
    if as_json:
        _ = out.write(_rules_json(catalog=catalog, rules=ordered))
        return 0
    for rule in ordered:
        _ = out.write(
            f"{rule.code}  {rule.key}  {rule.severity.value}  {rule.title}\n",
        )
    return 0


def _rules_json(*, catalog: Catalog, rules: list[Rule]) -> str:
    """Render the rule listing as a JSON array.

    Args:
        catalog (Catalog): Catalog owning the rules and fixes.
        rules (list[Rule]): Rules to list, already sorted.

    Returns:
        str: JSON text with one ``code``/``key``/``title``/``maturity``/
            ``severity``/``fixes`` object per rule; each fix carries its
            ``key`` and ``safety``.

    """
    safety_of: dict[str, str] = {
        fix.key: fix.safety.value for fix in catalog.fixes
    }
    document: JsonValue = [
        {
            "code": rule.code,
            "key": rule.key,
            "title": rule.title,
            "maturity": rule.maturity.value,
            "severity": rule.severity.value,
            "fixes": [
                {"key": fix_key, "safety": safety_of.get(fix_key)}
                for fix_key in rule.fixes
            ],
        }
        for rule in rules
    ]
    return canonical_dumps(value=document)


def run_explain(*, code: str, out: TextIO, err: TextIO) -> int:
    """Print a rule's rationale and its triggering and clean examples.

    Args:
        code (str): Rule code to explain.
        out (TextIO): Stream the explanation is written to.
        err (TextIO): Stream the error is written to.

    Returns:
        int: Zero when the code is known, ``Constants.usage_error`` otherwise.

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


def _split_location(*, location: str) -> tuple[str, int, int | None]:
    """Split a ``path:line[:col]`` location into its parts.

    Args:
        location (str): Location text, ``path:line`` or ``path:line:col``.

    Returns:
        tuple[str, int, int | None]: The path, the one-based line and the
            zero-based
            column, or ``None`` when no column was given.

    Raises:
        ValueError: When the location does not end in ``:line[:col]``.

    """
    head, separator, tail = location.rpartition(":")
    if not separator or not tail.isdigit():
        raise ValueError(location)
    before, inner, maybe_line = head.rpartition(":")
    if inner and maybe_line.isdigit() and tail.isdigit():
        return before, int(maybe_line), int(tail)
    return head, int(tail), None


def run_explain_at(
    *,
    code: str,
    location: str,
    out: TextIO,
    err: TextIO,
) -> int:
    """Print a rule's rationale and the findings it reports at a location.

    Args:
        code (str): Rule code to explain.
        location (str): ``path:line[:col]`` of the finding.
        out (TextIO): Stream the explanation is written to.
        err (TextIO): Stream errors are written to.

    Returns:
        int: ``0`` when matches print, ``1`` when none match and
            ``Constants.usage_error`` for a bad location, unknown code or an
            unreadable file.

    """
    catalog: Catalog = load_default_catalog(registries=default_registries())
    rule: Rule | None = None
    for candidate in catalog.rules:
        if candidate.code == code:
            rule = candidate
            break
    if rule is None:
        _ = err.write(f"astart: unknown rule code: {code}\n")
        return Constants.usage_error
    try:
        path_text, line, column = _split_location(location=location)
    except ValueError:
        _ = err.write("""\
astart: bad location
""")
        return Constants.usage_error
    report: FileReport = _check_file(
        path=Path(path_text),
        catalog=catalog,
        options=CheckOptions(),
    )
    if report.error is not None:
        _ = err.write(f"{report.path}: error: {report.error}\n")
        return Constants.usage_error
    matches: list[Finding] = [
        finding
        for finding in report.findings
        if catalog.rule(key=finding.rule_key).code == code
        and finding.span.start_line == line
        and (column is None or finding.span.start_column == column)
    ]
    if not matches:
        _ = err.write(f"astart: no {code} finding at {location}\n")
        return 1
    _ = out.write(f"{rule.code}  {rule.key}  {rule.title}\n")
    _ = out.write(f"{rule.rationale}\n")
    for finding in matches:
        _ = out.write(
            f"\n{render_message(rule=rule, finding=finding)}\n"
            f"{render_evidence(finding=finding)}",
        )
    return 0


def run_undo(
    *,
    run_id: str | None,
    out: TextIO,
    err: TextIO,
) -> int:
    """Restore the files of a ``fix --backup`` run.

    Args:
        run_id (str | None): Run directory name under ``.astart-backup``
            ; the newest run is used when ``None``.
        out (TextIO): Stream the per-file outcome is written to.
        err (TextIO): Stream errors are written to.

    Returns:
        int: The undo status: ``0`` restored or nothing skipped, ``1`` when a
            file was edited since the fix, ``Constants.usage_error`` when no
            matching run exists.

    """
    base: Path = Path.cwd() / backup.BACKUP_ROOT
    run_dir: Path | None = None
    if run_id is not None:
        candidate: Path = base / run_id
        if candidate.is_dir():
            run_dir = candidate
    elif base.is_dir():
        runs: list[Path] = sorted(
            item for item in base.iterdir() if item.is_dir()
        )
        if runs:
            run_dir = runs[-1]
    if run_dir is None or not (run_dir / backup.JOURNAL_NAME).is_file():
        _ = err.write("""\
astart: no backup run found
""")
        return Constants.usage_error
    return backup.undo(run_dir=run_dir, out=out)


def _make_checker(*, settings: FixCommandSettings) -> Checker | None:
    """Build the external type-checker gate when it is wanted and installed.

    Args:
        settings (FixCommandSettings): Command options.

    Returns:
        Checker | None:
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
        index (ProjectIndex | None): Whole-project index, or ``None`` for
            single-file mode.
        libraries (LibraryIndex | None): External signature index, or ``None``.
        cache (FixCache | None): On-disk result cache, or ``None``.

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
        path (Path): File to fix.
        settings (FixCommandSettings): Command options.
        catalog (Catalog): Rules and fixes.
        checker (Checker | None): External type-checker gate, or ``None``.
        project (_ProjectContext): Whole-project services, empty for
            single-file mode.

    Returns:
        FixOutcome: What happened; failures are reported, never raised.

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
        docstring_types=settings.docstring_types,
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
        runtime_protocols=settings.runtime_protocols,
        accept_general=settings.accept_general,
        protocol_placement=settings.protocol_placement,
        optimize_aliases=settings.optimize_aliases,
    )
    registries: Registries = default_registries()
    note: str = ""
    if settings.run_formatter:
        fixed, formatted = fix_and_format(
            source=source.text,
            target=FormatTarget(
                filename=str(object=path.resolve()),
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
        path (Path): File name.
        before (str): Original text.
        after (str): Final text.
        fixed (FixResult): Fix runner result.
        note (str): Formatter note.

    Returns:
        FixOutcome: The per-file outcome.

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
        settings (FixCommandSettings): Command options.
        checker (Checker | None): External type-checker gate, or ``None``.

    Returns:
        FixCache | None:
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
        settings (FixCommandSettings): Paths, safety ceiling and mode.
        out (TextIO): Stream the report is written to.

    Returns:
        int: ``0`` when nothing changes, ``1`` when files changed or would
            change, ``2`` when a path is missing or a file cannot be fixed.

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
    run_dir: Path | None = _backup_dir(settings=settings)
    entries: list[backup.Entry] = []
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
        skipped += _report_outcome(path=path, outcome=outcome, out=out)
        if outcome.after == outcome.before:
            continue
        changed += 1
        applied += outcome.applied
        entry: backup.Entry | None = _emit(
            path=path,
            outcome=outcome,
            settings=settings,
            run_dir=run_dir,
            out=out,
        )
        if entry is not None:
            entries.append(entry)
    if run_dir is not None:
        backup.write_journal(run_dir=run_dir, entries=entries)
    summary: str = f"""\
{changed} files changed, {applied} fixes applied, {skipped} skipped
"""
    _ = out.write(summary)
    if failed:
        return Constants.usage_error
    return Constants.findings if changed else 0


def _report_outcome(
    *,
    path: Path,
    outcome: FixOutcome,
    out: TextIO,
) -> int:
    """Print the skipped fixes and formatter note of one outcome.

    Args:
        path (Path): File name.
        outcome (FixOutcome): Its fix outcome.
        out (TextIO): Report stream.

    Returns:
        int: The number of skipped fixes.

    """
    for line in outcome.skipped:
        _ = out.write(f"""\
{path}: skipped {line}
""")
    if outcome.note:
        _ = out.write(f"""\
{path}: note: {outcome.note}
""")
    return len(outcome.skipped)


def _backup_dir(*, settings: FixCommandSettings) -> Path | None:
    """Create the ``.astart-backup/<run-id>`` directory for a fix run.

    Args:
        settings (FixCommandSettings): Command options.

    Returns:
        Path | None: The new run directory, or ``None`` when
            backups are off or the run only reports.

    """
    if not settings.backup or settings.mode is not FixMode.write:
        return None
    stamp: datetime = datetime.now(tz=UTC)
    stamp_text: str = stamp.strftime(format="%Y%m%dT%H%M%S")
    run_dir: Path = Path.cwd() / backup.BACKUP_ROOT / stamp_text
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _emit(
    *,
    path: Path,
    outcome: FixOutcome,
    settings: FixCommandSettings,
    run_dir: Path | None,
    out: TextIO,
) -> backup.Entry | None:
    """Write, diff or just count one changed file.

    Args:
        path (Path): File name.
        outcome (FixOutcome): Its fix outcome.
        settings (FixCommandSettings): Command options.
        run_dir (Path | None): Backup run directory, or ``None`` when backups
            are off.
        out (TextIO): Report stream.

    Returns:
        backup.Entry | None:
            The backup entry when a before-image was saved, else ``None``.

    """
    entry: backup.Entry | None = None
    if settings.mode is FixMode.write:
        encoding: str = read_source(path=path).encoding
        if run_dir is not None:
            entry = backup.save(
                run_dir=run_dir,
                path=path,
                before=outcome.before,
                after=outcome.after,
                encoding=encoding,
            )
        write_atomic(path=path, text=outcome.after, encoding=encoding)
    elif settings.mode is FixMode.diff:
        _ = out.writelines(
            unified_diff(
                a=outcome.before.splitlines(keepends=True),
                b=outcome.after.splitlines(keepends=True),
                fromfile=str(object=path),
                tofile=str(object=path),
            ),
        )
    return entry
