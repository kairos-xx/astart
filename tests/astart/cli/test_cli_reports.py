"""Tests for the SARIF, JUnit, GitHub, baseline and ignore reporters."""

from __future__ import annotations

from json import loads
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, cast, final

import pytest
from astart.cli.baseline import (
    BaselineError,
    apply_baseline,
    load_baseline,
    save_baseline,
)
from astart.cli.config import (
    AstartConfig,
    ConfigError,
    Selection,
    load_config,
)
from astart.cli.github import render_github
from astart.cli.ignores import (
    ResolvedSelection,
    apply_ignores,
    resolve,
    selected_rules,
)
from astart.cli.junit import render_junit
from astart.cli.render import FileReport
from astart.cli.sarif import render_sarif
from astart.rules import default_registries
from astart.rules.catalog import load_default_catalog
from astart.rules.engine import CheckOptions, CheckResult, check
from astart.rules.model import Catalog, Profile
from astart.rules.vocabulary import FixSafety, Severity

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Rule


class _DefusedParser(Protocol):
    """Typed view of defusedxml's untyped ``ElementTree.fromstring``."""

    def fromstring(self, *, text: str) -> Element:
        """Parse XML text into an element.

        Args:
            text (str): XML document text.

        Returns:
            The parsed root element.

        """
        ...


@final
class Constants:
    """Group module-level constants.

    Attributes:
        flagged_source (Final[str]): Source that produces a typing finding.
        clean_source (Final[str]): Source that produces none.
        minimum_results (Final[int]): Lower bound on SARIF results for one
            report set.

    """

    flagged_source: Final[str] = """\
def f(x):
    return x

f(1)
"""
    clean_source: Final[str] = """\
def g(y: int) -> int:
    return y
"""
    minimum_results: Final[int] = 2


def _xml_root(*, text: str) -> Element:
    """Parse reporter XML with defusedxml, skipping when it is absent.

    Args:
        text (str): XML document text.

    Returns:
        Element: The parsed root element.

    """
    parser: _DefusedParser = cast(
        typ="_DefusedParser",
        val=pytest.importorskip(modname="defusedxml.ElementTree"),
    )
    return parser.fromstring(text=text)


def _catalog() -> Catalog:
    """Load the default catalog.

    Returns:
        Catalog: The default rule catalog.

    """
    return load_default_catalog(registries=default_registries())


def _reports() -> tuple[FileReport, FileReport, FileReport]:
    """Produce one flagged, one clean and one errored report.

    Returns:
        tuple[FileReport, FileReport, FileReport]: Reports for a flagged file,
            a clean file and a parse error.

    """
    catalog: Catalog = _catalog()
    result: CheckResult = check(
        source=Constants.flagged_source,
        filename="src/flagged.py",
        catalog=catalog,
        registries=default_registries(),
        options=CheckOptions(stubs_path=None),
    )
    clean: CheckResult = check(
        source=Constants.clean_source,
        filename="src/clean.py",
        catalog=catalog,
        registries=default_registries(),
        options=CheckOptions(stubs_path=None),
    )
    return (
        FileReport(
            path="src/flagged.py",
            findings=result.findings,
            error=None,
        ),
        FileReport(path="src/clean.py", findings=clean.findings, error=None),
        FileReport(path="src/bad.py", findings=(), error="parse error"),
    )


def test_sarif_structure() -> None:
    """SARIF output is valid 2.1.0 with results and rules."""
    catalog: Catalog = _catalog()
    text: str = render_sarif(results=_reports(), catalog=catalog)
    document: dict[str, JsonValue] = loads(s=text)
    expect_equal(actual=document["version"], expected="2.1.0")
    runs: list[JsonValue] = cast(
        typ="list[JsonValue]",
        val=document["runs"],
    )
    run: dict[str, JsonValue] = cast(
        typ="dict[str, JsonValue]",
        val=runs[0],
    )
    results: list[dict[str, JsonValue]] = cast(
        typ="list[dict[str, JsonValue]]",
        val=run["results"],
    )
    expect_true(
        condition=len(results) >= Constants.minimum_results,
    )
    first: dict[str, JsonValue] = results[0]
    expect_in(item="ruleId", container=first)
    expect_in(item="level", container=first)
    fingerprints: dict[str, JsonValue] = cast(
        typ="dict[str, JsonValue]",
        val=first.get("partialFingerprints", {}),
    )
    expect_in(item="astart/fingerprint", container=fingerprints)


def test_junit_counts() -> None:
    """JUnit XML counts tests, failures and skips."""
    catalog: Catalog = _catalog()
    text: str = render_junit(results=_reports(), catalog=catalog)
    root: Element = _xml_root(text=text)
    suite: Element = expect_not_none(value=root.find(path="testsuite"))
    expect_true(condition=int(suite.get(key="tests", default="0")) >= 1)
    expect_true(condition=int(suite.get(key="failures", default="0")) >= 1)


def test_github_annotations() -> None:
    """GitHub output emits workflow commands per finding and error."""
    catalog: Catalog = _catalog()
    text: str = render_github(results=_reports(), catalog=catalog)
    expect_in(item="::error file=src/bad.py::parse error", container=text)
    for line in text.splitlines():
        if "bad.py" in line:
            continue
        expect_true(condition=line.startswith("::"))
        expect_in(item="file=", container=line)


def test_github_escapes_newlines() -> None:
    """Newlines in messages are escaped for the command grammar."""
    catalog: Catalog = _catalog()
    reports: tuple[FileReport] = (
        FileReport(
            path="a b.py",
            findings=(),
            error="""\
line1
line2""",
        ),
    )
    text: str = render_github(results=reports, catalog=catalog)
    expect_in(item="line1%0Aline2", container=text)


def test_baseline_roundtrip(tmp_path: Path) -> None:
    """Saved baselines reload and suppress captured findings.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    reports: tuple[FileReport, FileReport, FileReport] = _reports()
    path: Path = tmp_path / "baseline.json"
    save_baseline(results=reports, path=path)
    fingerprints: frozenset[str] = load_baseline(path=path)
    expect_true(condition=len(fingerprints) >= 1)
    filtered: tuple[FileReport, ...] = apply_baseline(
        results=reports,
        fingerprints=fingerprints,
    )
    remaining: int = sum(len(report.findings) for report in filtered)
    expect_equal(actual=remaining, expected=0)


def test_baseline_malformed(tmp_path: Path) -> None:
    """Malformed baseline files raise BaselineError.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    path: Path = tmp_path / "bad.json"
    path.write_text(data='{"version": 99}', encoding="utf-8")
    with pytest.raises(expected_exception=BaselineError):
        load_baseline(path=path)
    path.write_text(data='["not an object"]', encoding="utf-8")
    with pytest.raises(expected_exception=BaselineError):
        load_baseline(path=path)


def test_apply_ignores_excludes_and_filters(tmp_path: Path) -> None:
    """Config excludes drop files; ignores drop findings per path.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data='[tool.astart]\nexclude = ["src/bad.py"]\n'
        '[tool.astart.overrides."src/flagged.py"]\n'
        'ignore = ["TYP", "CAL"]\n',
        encoding="utf-8",
    )
    config: AstartConfig = expect_not_none(
        value=load_config(path=pyproject),
    )
    filtered: tuple[FileReport, ...] = apply_ignores(
        results=_reports(),
        config=config,
        catalog=_catalog(),
    )
    paths: tuple[str, ...] = tuple(report.path for report in filtered)
    expect_true(condition="src/bad.py" not in paths)
    flagged: FileReport = next(
        r for r in filtered if r.path == "src/flagged.py"
    )
    expect_equal(actual=len(flagged.findings), expected=0)


def test_selected_rules_root_only() -> None:
    """Root select narrows the rules offered."""
    catalog: Catalog = _catalog()
    all_rules: tuple[Rule, ...] = tuple(catalog.rules)
    config: AstartConfig = AstartConfig(
        root=Path("/nonexistent-root"),
        selection=Selection(select=("NOMATCH",)),
    )
    kept: tuple[Rule, ...] = selected_rules(
        rules=all_rules,
        config=config,
        catalog=catalog,
    )
    expect_equal(actual=len(kept), expected=0)


def _profiled_catalog(*, drop_key: str) -> Catalog:
    """Build the default catalog plus a ``strict`` profile.

    The profile enables every rule except ``drop_key``, downgrades all
    severities to ``info``, overrides one param and caps fixes at
    ``proven``.

    Args:
        drop_key (str): Rule key the profile leaves disabled.

    Returns:
        Catalog: A catalog holding the profile.

    """
    base: Catalog = _catalog()
    return Catalog(
        rules=base.rules,
        fixes=base.fixes,
        profiles=(
            Profile(
                key="strict",
                rules=tuple(
                    rule.key for rule in base.rules if rule.key != drop_key
                ),
                severities={rule.key: Severity.info for rule in base.rules},
                params={"profile-param": 1},
                safety_ceiling=FixSafety.proven,
            ),
        ),
        relations=base.relations,
    )


def test_apply_ignores_profile_filters_and_reseverities(
    tmp_path: Path,
) -> None:
    """A named profile drops its disabled rules and rewrites severities.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    reports: tuple[FileReport, FileReport, FileReport] = _reports()
    drop_key: str = reports[0].findings[0].rule_key
    catalog: Catalog = _profiled_catalog(drop_key=drop_key)
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data="""\
[tool.astart]
profile = "strict"
""",
        encoding="utf-8",
    )
    config: AstartConfig = expect_not_none(
        value=load_config(path=pyproject),
    )
    filtered: tuple[FileReport, ...] = apply_ignores(
        results=reports,
        config=config,
        catalog=catalog,
    )
    flagged: FileReport = next(
        report for report in filtered if report.path == "src/flagged.py"
    )
    expect_true(
        condition=all(
            finding.rule_key != drop_key for finding in flagged.findings
        ),
    )
    expect_true(
        condition=all(
            finding.severity == Severity.info for finding in flagged.findings
        ),
    )


def test_selected_rules_profile_enables_subset() -> None:
    """A profile narrows the offered rules to its own set."""
    catalog: Catalog = _profiled_catalog(drop_key="no-such-rule")
    config: AstartConfig = AstartConfig(
        root=Path("/nonexistent-root"),
        selection=Selection(profile="strict"),
    )
    kept: tuple[Rule, ...] = selected_rules(
        rules=tuple(catalog.rules),
        config=config,
        catalog=catalog,
    )
    expect_equal(actual=len(kept), expected=len(catalog.rules))
    narrowed: Catalog = _profiled_catalog(
        drop_key=catalog.rules[0].key,
    )
    kept_fewer: tuple[Rule, ...] = selected_rules(
        rules=tuple(narrowed.rules),
        config=config,
        catalog=narrowed,
    )
    expect_equal(
        actual=len(kept_fewer),
        expected=len(narrowed.rules) - 1,
    )


def test_resolve_unknown_profile_raises() -> None:
    """A profile key missing from the catalog is a ConfigError."""
    catalog: Catalog = _catalog()
    with pytest.raises(expected_exception=ConfigError):
        resolve(
            selection=Selection(profile="missing"),
            catalog=catalog,
        )


def test_resolved_selection_merges_params_and_ceiling() -> None:
    """Params layer rule < profile < selection; ceiling prefers explicit."""
    catalog: Catalog = _profiled_catalog(drop_key="no-such-rule")
    rule: Rule = catalog.rules[0]
    resolved: ResolvedSelection = resolve(
        selection=Selection(
            profile="strict",
            params={"profile-param": 2, "extra": "x"},
            safety_ceiling=FixSafety.suggest,
        ),
        catalog=catalog,
    )
    expect_equal(
        actual=resolved.params(rule=rule),
        expected={"profile-param": 2, "extra": "x"},
    )
    expect_equal(actual=resolved.ceiling, expected=FixSafety.suggest)
    inherited: ResolvedSelection = resolve(
        selection=Selection(profile="strict"),
        catalog=catalog,
    )
    expect_equal(
        actual=inherited.params(rule=rule),
        expected={"profile-param": 1},
    )
    expect_equal(actual=inherited.ceiling, expected=FixSafety.proven)
