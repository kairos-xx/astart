"""Verify text and JSON rendering of findings."""

from __future__ import annotations

from json import loads
from typing import TYPE_CHECKING, Final, cast, final

from astart.cli.render import FileReport, render_json, render_text
from astart.rules import (
    Catalog,
    CheckResult,
    check,
    default_registries,
    load_default_catalog,
)

from tests.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Finding
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source: Grouped module constant.

    """

    source: Final[str] = """\
from typing import Any


def f(x: Any):
    return x
"""


def _check() -> tuple[Catalog, CheckResult]:
    """Run the checker on the sample source.

    Returns:
        The default catalog and the check result.

    """
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    return (
        catalog,
        check(
            source=Constants.source,
            filename="a.py",
            catalog=catalog,
            registries=registries,
        ),
    )


def test_text_line_has_location_code_and_message() -> None:
    """Check that text line has location code and message."""
    catalog, result = _check()
    finding: Finding = next(
        item for item in result.findings if item.rule_key == "typing.no-any"
    )
    line: str = render_text(finding=finding, catalog=catalog)
    expect_true(condition=line.startswith("a.py:4:9: "), message=line)
    expect_in(item="TYP001", container=line)
    expect_in(item="`Any` is used in the annotation of `x`.", container=line)


def test_json_round_trips_and_lists_fix_keys() -> None:
    """Check that json round trips and lists fix keys."""
    catalog, result = _check()
    report: FileReport = FileReport(
        path="a.py",
        findings=result.findings,
        error=None,
    )
    entry: dict[str, JsonValue] = cast(
        typ="dict[str, JsonValue]",
        val=loads(s=render_json(results=[report], catalog=catalog))[0],
    )
    expect_equal(actual=entry["path"], expected="a.py")
    expect_equal(actual=entry["error"], expected=None)
    findings: list[dict[str, JsonValue]] = cast(
        typ="list[dict[str, JsonValue]]",
        val=entry["findings"],
    )
    expect_in(
        item="TYP001",
        container={cast(typ="str", val=item["code"]) for item in findings},
    )
    first: dict[str, JsonValue] = findings[0]
    for key in ("rule", "severity", "line", "column", "message", "fixes"):
        expect_in(item=key, container=first)


def test_json_reports_parse_error_per_file() -> None:
    """Check that json reports parse error per file."""
    catalog, _ = _check()
    report: FileReport = FileReport(path="b.py", findings=(), error="bad")
    data: list[dict[str, JsonValue]] = cast(
        typ="list[dict[str, JsonValue]]",
        val=loads(s=render_json(results=[report], catalog=catalog)),
    )
    expect_equal(actual=data[0]["error"], expected="bad")
    expect_equal(actual=data[0]["findings"], expected=[])
