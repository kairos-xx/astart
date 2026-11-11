"""Render findings as text lines or a JSON document."""

from __future__ import annotations

from dataclasses import dataclass
from json import dumps
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Finding, Rule, Span


@final
@dataclass(frozen=True, slots=True)
class FileReport:
    """Findings, or the reason there are none, for one file.

    Attributes:
        path (str): File name as given on the command line.
        findings (tuple[Finding, ...]): Findings in source order.
        error (str | None): Why the file could not be analysed, if it could
            not.

    """

    path: str
    findings: tuple[Finding, ...]
    error: str | None


def _text(*, value: JsonValue) -> str:
    """Spell an evidence value for a message.

    Args:
        value (JsonValue): Evidence value.

    Returns:
        str: The value, with lists joined by commas.

    """
    if isinstance(value, list):
        return ", ".join(_text(value=item) for item in value)
    return str(object=value)


def render_message(*, rule: Rule, finding: Finding) -> str:
    """Fill a rule's message template from a finding's evidence.

    Args:
        rule (Rule): Rule whose template is used.
        finding (Finding): Finding that provides the evidence.

    Returns:
        str: The message text.

    """
    values: Mapping[str, str] = {
        key: _text(value=value) for key, value in finding.evidence.items()
    }
    return rule.message.format_map(values)


def render_evidence(*, finding: Finding) -> str:
    """Render a finding's evidence as ``key: value`` lines.

    Args:
        finding (Finding): Finding whose evidence is rendered.

    Returns:
        str: One ``key: value`` line per evidence slot, each
            newline-terminated.

    """
    return "".join(
        f"{key}: {_text(value=value)}\n"
        for key, value in finding.evidence.items()
    )


def render_text(*, finding: Finding, catalog: Catalog) -> str:
    """Render one finding as ``path:line:col: CODE severity message``.

    Args:
        finding (Finding): Finding to render.
        catalog (Catalog): Catalog that owns the finding's rule.

    Returns:
        str: A single line.

    """
    rule: Rule = catalog.rule(key=finding.rule_key)
    span: Span = finding.span
    return (
        f"{span.file}:{span.start_line}:{span.start_column}: {rule.code} "
        f"{finding.severity.value} "
        f"{render_message(rule=rule, finding=finding)}"
    )


def render_json(*, results: Sequence[FileReport], catalog: Catalog) -> str:
    """Render reports as a JSON array with sorted keys.

    Args:
        results (Sequence[FileReport]): One report per file.
        catalog (Catalog): Catalog that owns the findings' rules.

    Returns:
        str: The JSON text.

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
