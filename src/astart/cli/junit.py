"""Render findings as a JUnit XML document."""

from __future__ import annotations

from typing import TYPE_CHECKING, final
from xml.etree.ElementTree import Element, SubElement, tostring

from astart.cli.render import render_message
from astart.rules.vocabulary import Severity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from astart.cli.render import FileReport
    from astart.rules.model import Catalog, Rule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        suite_name (str): Name of the emitted test suite.
        failure_severities (frozenset[Severity]): Severities rendered as
            failures.

    """

    suite_name: str = "astart"
    failure_severities: frozenset[Severity] = frozenset(
        {Severity.error, Severity.warning},
    )


def render_junit(
    *,
    results: Sequence[FileReport],
    catalog: Catalog,
) -> str:
    """Render reports as a JUnit XML document.

    Each file becomes a ``testcase`` per finding; errors and warnings are
    ``failure`` elements, informational findings are skipped (skipped
    cases) and file-level errors become a single failing case.

    Args:
        results (Sequence[FileReport]): One report per file.
        catalog (Catalog): Catalog that owns the findings' rules.

    Returns:
        str: The XML text.

    """
    suite: Element = Element("testsuite", name=Constants.suite_name)
    tests: int = 0
    failures: int = 0
    skipped: int = 0
    for report in results:
        case: Element = SubElement(
            parent=suite,
            tag="testcase",
            name=report.path,
            classname=Constants.suite_name,
        )
        if report.error is not None:
            failure: Element = SubElement(
                parent=case,
                tag="failure",
                message="file error",
            )
            failure.text = report.error
            tests += 1
            failures += 1
            continue
        for finding in report.findings:
            rule: Rule = catalog.rule(key=finding.rule_key)
            tests += 1
            message: str = render_message(rule=rule, finding=finding)
            if finding.severity in Constants.failure_severities:
                failures += 1
                failure = SubElement(
                    parent=case,
                    tag="failure",
                    message=f"{rule.code}: {message}",
                )
                failure.text = (
                    f"{finding.span.start_line}:{finding.span.start_column} "
                    f"{message}"
                )
            else:
                skipped += 1
                skip: Element = SubElement(
                    parent=case,
                    tag="skipped",
                    message=f"{rule.code}: {message}",
                )
                skip.text = message
    suite.set("tests", str(object=tests))
    suite.set("failures", str(object=failures))
    suite.set("skipped", str(object=skipped))
    document: Element = Element("testsuites")
    document.append(suite)
    return tostring(element=document, encoding="unicode")
