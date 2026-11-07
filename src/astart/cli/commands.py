"""Implement the ``check`` and ``fix`` commands."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from enum import StrEnum
from io import BytesIO
from os import fsync
from shutil import copymode
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Final, final

from astart.cli.discovery import DiscoveryResult, discover_files
from astart.cli.render import FileReport, render_json, render_text
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
from astart.rules.vocabulary import FixSafety, Severity

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO

    from astart.rules.model import Catalog


@final
class Constants:
    """Group module-level constants.

    Attributes:
        severity_rank: Grouped module constant.
        usage_error: Grouped module constant.
        findings: Grouped module constant.
        text_format: Grouped module constant.

    """

    severity_rank: Final[tuple[Severity, ...]] = (
        Severity.error,
        Severity.warning,
        Severity.info,
    )
    usage_error: Final[int] = 2
    findings: Final[int] = 1
    text_format: Final[str] = "text"


@final
@dataclass(frozen=True, slots=True)
class CheckSettings:
    """Options of the ``check`` command.

    Attributes:
        paths: Files and directories to check.
        output_format: ``text`` or ``json``.
        fail_on: Least severe finding that makes the exit status non-zero.
        stubs_path: Stub directory for type hints, or ``None``.

    """

    paths: tuple[Path, ...]
    output_format: str
    fail_on: Severity
    stubs_path: Path | None


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

    """

    paths: tuple[Path, ...]
    ceiling: FixSafety
    stubs_path: Path | None
    mode: FixMode
    run_formatter: bool


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
    found: DiscoveryResult = discover_files(paths=settings.paths)
    catalog: Catalog = load_default_catalog(registries=default_registries())
    options: CheckOptions = CheckOptions(stubs_path=settings.stubs_path)
    reports: list[FileReport] = [
        _check_file(path=path, catalog=catalog, options=options)
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


def _fix_file(
    *,
    path: Path,
    settings: FixCommandSettings,
    catalog: Catalog,
) -> FixOutcome:
    """Fix one file in memory.

    Args:
        path: File to fix.
        settings: Command options.
        catalog: Rules and fixes.

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
    fix_settings: FixSettings = FixSettings(
        ceiling=settings.ceiling,
        stubs_path=settings.stubs_path,
    )
    registries = default_registries()
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
        fixed = fix_source(
            source=source.text,
            filename=str(object=path),
            catalog=catalog,
            registries=registries,
            settings=fix_settings,
        )
        text = fixed.source
    return _outcome(
        path=path,
        before=source.text,
        after=text,
        fixed=fixed,
        note=note,
    )


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


def run_fix(*, settings: FixCommandSettings, out: TextIO) -> int:
    """Fix files in place, or show or check what would change.

    Args:
        settings: Paths, safety ceiling and mode.
        out: Stream the report is written to.

    Returns:
        ``0`` when nothing changes, ``1`` when files changed or would change,
        ``2`` when a path is missing or a file cannot be fixed.

    """
    found: DiscoveryResult = discover_files(paths=settings.paths)
    catalog: Catalog = load_default_catalog(registries=default_registries())
    failed: bool = bool(found.missing)
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
