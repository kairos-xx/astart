"""Render findings as text lines or a JSON document."""

from __future__ import annotations

from dataclasses import dataclass
from json import dumps
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Finding, Rule


@final
@dataclass(frozen=True, slots=True)
class FileReport:
    """Findings, or the reason there are none, for one file.

    Attributes:
        path: File name as given on the command line.
        findings: Findings in source order.
        error: Why the file could not be analysed, if it could not.

    """

    path: str
    findings: tuple[Finding, ...]
    error: str | None


def _text(*, value: JsonValue) -> str:
    """Spell an evidence value for a message.

    Args:
        value: Evidence value.

    Returns:
        The value, with lists joined by commas.

    """
    if isinstance(value, list):
        return ", ".join(_text(value=item) for item in value)
    return str(object=value)


def render_message(*, rule: Rule, finding: Finding) -> str:
    """Fill a rule's message template from a finding's evidence.

    Args:
        rule: Rule whose template is used.
        finding: Finding that provides the evidence.

    Returns:
        The message text.

    """
    values: Mapping[str, str] = {
        key: _text(value=value) for key, value in finding.evidence.items()
    }
    return rule.message.format_map(values)


def render_text(*, finding: Finding, catalog: Catalog) -> str:
    """Render one finding as ``path:line:col: CODE severity message``.

    Args:
        finding: Finding to render.
        catalog: Catalog that owns the finding's rule.

    Returns:
        A single line.

    """
    rule: Rule = catalog.rule(key=finding.rule_key)
    span = finding.span
    return (
        f"{span.file}:{span.start_line}:{span.start_column}: {rule.code} "
        f"{finding.severity.value} "
        f"{render_message(rule=rule, finding=finding)}"
    )


def render_json(*, results: Sequence[FileReport], catalog: Catalog) -> str:
    """Render reports as a JSON array with sorted keys.

    Args:
        results: One report per file.
        catalog: Catalog that owns the findings' rules.

    Returns:
        The JSON text.

    """
    document: list[dict[str, JsonValue]] = []
    for report in results:
        entries: list[JsonValue] = []
        for finding in report.findings:
            rule: Rule = catalog.rule(key=finding.rule_key)
            entries.append(
                {
                    "rule": rule.key,
                    "code": rule.code,
                    "severity": finding.severity.value,
                    "line": finding.span.start_line,
                    "column": finding.span.start_column,
                    "message": render_message(rule=rule, finding=finding),
                    "fingerprint": finding.fingerprint,
                    "fixes": [offer.fix_key for offer in finding.fix_offers],
                },
            )
        document.append(
            {"path": report.path, "error": report.error, "findings": entries},
        )
    return dumps(obj=document, indent=2, sort_keys=True)
