"""Render findings as a SARIF 2.1.0 document."""

from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING, Final, final

from astart.cli.render import render_message
from astart.rules.vocabulary import Severity

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.cli.render import FileReport
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Finding, Rule, Span


@final
class Constants:
    """Group module-level constants.

    Attributes:
        schema (Final[str]): The SARIF schema URL.
        version (Final[str]): The SARIF version emitted.
        driver_name (Final[str]): Name of the reporting tool.
        information_uri (Final[str]): Public URI for the tool.
        levels (Final[Mapping[Severity, str]]): SARIF level per severity.

    """

    schema: Final[str] = "https://json.schemastore.org/sarif-2.1.0.json"
    version: Final[str] = "2.1.0"
    driver_name: Final[str] = "astart"
    information_uri: Final[str] = "https://devin.ai"
    levels: Final[Mapping[Severity, str]] = {
        Severity.error: "error",
        Severity.warning: "warning",
        Severity.info: "note",
    }


def render_sarif(
    *,
    results: Sequence[FileReport],
    catalog: Catalog,
) -> str:
    """Render reports as a SARIF 2.1.0 document.

    Args:
        results (Sequence[FileReport]): One report per file.
        catalog (Catalog): Catalog that owns the findings' rules.

    Returns:
        str: The SARIF JSON text.

    """
    rules: dict[str, Rule] = {}
    entries: list[JsonValue] = []
    for report in results:
        if report.error is not None:
            entries.append(_error_result(report=report))
            continue
        for finding in report.findings:
            rule: Rule = catalog.rule(key=finding.rule_key)
            rules.setdefault(rule.key, rule)
            entries.append(
                _finding_result(report=report, finding=finding, rule=rule),
            )
    document: JsonValue = {
        "$schema": Constants.schema,
        "version": Constants.version,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": Constants.driver_name,
                        "informationUri": Constants.information_uri,
                        "rules": [
                            {
                                "id": rule.key,
                                "name": rule.code,
                                "shortDescription": {
                                    "text": rule.title,
                                },
                            }
                            for rule in rules.values()
                        ],
                    },
                },
                "results": entries,
            },
        ],
    }
    return dumps(obj=document, indent=2, sort_keys=True)


def _finding_result(
    *,
    report: FileReport,
    finding: Finding,
    rule: Rule,
) -> JsonValue:
    """Build the SARIF result for one finding.

    Args:
        report (FileReport): File the finding came from.
        finding (Finding): The finding.
        rule (Rule): Its catalog rule.

    Returns:
        JsonValue: A SARIF result object.

    """
    span: Span = finding.span
    return {
        "ruleId": rule.key,
        "level": Constants.levels.get(finding.severity, "warning"),
        "message": {
            "text": render_message(rule=rule, finding=finding),
        },
        "partialFingerprints": {"astart/fingerprint": finding.fingerprint},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": report.path},
                    "region": {
                        "startLine": span.start_line,
                        "startColumn": span.start_column + 1,
                        "endLine": span.end_line,
                        "endColumn": span.end_column + 1,
                    },
                },
            },
        ],
    }


def _error_result(*, report: FileReport) -> JsonValue:
    """Build the SARIF result for a file that failed.

    Args:
        report (FileReport): The failed report.

    Returns:
        JsonValue: A SARIF result object.

    """
    return {
        "ruleId": "astart/parse-error",
        "level": "error",
        "message": {"text": report.error},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": report.path},
                },
            },
        ],
    }
