"""Render findings as GitHub Actions workflow annotations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart.cli.render import render_message
from astart.rules.vocabulary import Severity

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.cli.render import FileReport
    from astart.rules.model import Catalog, Finding, Rule, Span


@final
class Constants:
    """Group module-level constants.

    Attributes:
        commands: Workflow command per severity.
        replacements: Message escapes GitHub requires.

    """

    commands: Final[Mapping[Severity, str]] = {
        Severity.error: "error",
        Severity.warning: "warning",
        Severity.info: "notice",
    }
    replacements: Final[tuple[tuple[str, str], ...]] = (
        ("%", "%25"),
        ("\r", "%0D"),
        ("\n", "%0A"),
    )


def render_github(
    *,
    results: Sequence[FileReport],
    catalog: Catalog,
) -> str:
    """Render reports as workflow annotation commands.

    Args:
        results: One report per file.
        catalog: Catalog that owns the findings' rules.

    Returns:
        One ``::error``/``::warning``/``::notice`` line per finding,
        plus one ``::error`` line per file that could not be analysed.

    """
    lines: list[str] = []
    for report in results:
        if report.error is not None:
            lines.append(
                f"::error file={_escape_data(value=report.path)}::"
                f"{_escape_data(value=report.error)}",
            )
            continue
        for finding in report.findings:
            rule: Rule = catalog.rule(key=finding.rule_key)
            lines.append(_line(report=report, finding=finding, rule=rule))
    return "\n".join(lines)


def _line(*, report: FileReport, finding: Finding, rule: Rule) -> str:
    """Build one annotation line.

    Args:
        report: File the finding came from.
        finding: The finding.
        rule: Its catalog rule.

    Returns:
        A workflow command line.

    """
    command: str = Constants.commands.get(finding.severity, "warning")
    span: Span = finding.span
    props: str = (
        f"file={_escape_property(value=report.path)},"
        f"line={span.start_line},col={span.start_column + 1},"
        f"endLine={span.end_line},endColumn={span.end_column + 1},"
        f"title={_escape_property(value=rule.code)}"
    )
    message: str = render_message(rule=rule, finding=finding)
    return f"::{command} {props}::{_escape_data(value=message)}"


def _escape_data(*, value: str) -> str:
    """Escape a message body for the workflow command grammar.

    Args:
        value: Raw text.

    Returns:
        Escaped text.

    """
    for raw, escaped in Constants.replacements:
        value = value.replace(raw, escaped)
    return value


def _escape_property(*, value: str) -> str:
    """Escape a property value for the workflow command grammar.

    Args:
        value: Raw text.

    Returns:
        Escaped text.

    """
    return _escape_data(value=value).replace(":", "%3A").replace(",", "%2C")
