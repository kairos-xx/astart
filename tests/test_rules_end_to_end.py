"""Exercise the seeded rule catalog end to end."""

from __future__ import annotations

from importlib.resources import files
from json import loads
from pathlib import Path
from re import MULTILINE, Pattern
from re import compile as compile_pattern
from typing import TYPE_CHECKING, Final, final

from astart import rules
from astart.rules import (
    Catalog,
    CheckResult,
    Finding,
    apply_fix,
    check,
    default_registries,
    load_default_catalog,
    verify_catalog,
)
from astart.rules.jsonvalue import canonical_dumps

from tests.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        catalog_files: Grouped module constant.
        sample: Grouped module constant.
        forbidden: Grouped module constant.

    """

    catalog_files: Final[tuple[str, ...]] = (
        "calls.json",
        "docs.json",
        "typing.json",
    )
    sample: Final[str] = """\
\"""Sample.\"""
from typing import Any

LIMIT = 3


def run(a, b, c: Any):
    \"""Run.

    Args:
        a: First value.
    \"""
    return a


run(1, 2, 3)
"""
    forbidden: Final[Pattern[str]] = compile_pattern(
        pattern=(
            "^\\s*(from|import)\\s+astart(\\.(ast|semantic|_graph))?\\b(?!"
            "\\.rules)"
        ),
        flags=MULTILINE,
    )


def _catalog() -> Catalog:
    """Load the default catalog.

    Returns:
        The validated seed catalog.

    """
    return load_default_catalog(registries=default_registries())


def _check(*, source: str) -> CheckResult:
    """Check a source with the default catalog.

    Args:
        source: Python source.

    Returns:
        The check result.

    """
    return check(
        source=source,
        filename="sample.py",
        catalog=_catalog(),
        registries=default_registries(),
    )


def test_default_catalog_loads_and_validates() -> None:
    """Load the seed rules and prove their examples and fixes."""
    catalog: Catalog = _catalog()
    expect_equal(
        actual=sorted(rule.code for rule in catalog.rules),
        expected=["CAL001", "DOC002", "TYP001", "TYP003", "TYP004"],
    )
    verify_catalog(catalog=catalog, registries=default_registries())


def test_default_catalog_files_are_canonical() -> None:
    """Keep the shipped JSON in canonical form."""
    for name in Constants.catalog_files:
        resource: Traversable = files("astart.rules").joinpath(
            "catalog",
            name,
        )
        text: str = resource.read_text(encoding="utf-8")
        expect_equal(
            actual=canonical_dumps(value=loads(s=text)),
            expected=text,
        )


def test_check_reports_all_five_rules_on_one_module() -> None:
    """Report each seeded rule on the sample."""
    result: CheckResult = _check(source=Constants.sample)
    expect_equal(
        actual=sorted({f.rule_key for f in result.findings}),
        expected=[
            "calls.missing-keyword",
            "docs.missing-parameter",
            "typing.missing-annotation",
            "typing.no-any",
            "typing.uppercase-global-not-final",
        ],
    )
    by_rule: dict[str, Finding] = {f.rule_key: f for f in result.findings}
    expect_equal(
        actual=by_rule["calls.missing-keyword"].evidence["parameters"],
        expected=["a", "b", "c"],
    )
    expect_equal(
        actual=by_rule["docs.missing-parameter"].evidence["parameters"],
        expected=["b", "c"],
    )
    expect_equal(
        actual=by_rule["typing.no-any"].evidence["name"],
        expected="c",
    )
    expect_equal(
        actual=sorted(
            f.subject_path
            for f in result.findings
            if f.rule_key == "typing.missing-annotation"
        ),
        expected=["run", "run.a", "run.b"],
    )


def test_fix_then_check_clears_fixable_findings() -> None:
    """Apply both fixes; only the unfixable findings remain."""
    catalog: Catalog = _catalog()
    registries: Registries = default_registries()
    source: str = Constants.sample
    for rule_key, fix_key in (
        ("typing.uppercase-global-not-final", "typing.add-final"),
        ("calls.missing-keyword", "calls.add-keywords"),
    ):
        finding: Finding = next(
            f for f in _check(source=source).findings if f.rule_key == rule_key
        )
        source = apply_fix(
            source=source,
            finding=finding,
            fix=catalog.fix(key=fix_key),
            registries=registries,
        )
    expect_in(item="LIMIT: Final[int] = 3", container=source)
    expect_in(item="run(a=1, b=2, c=3)", container=source)
    expect_equal(
        actual=sorted({f.rule_key for f in _check(source=source).findings}),
        expected=[
            "docs.missing-parameter",
            "typing.missing-annotation",
            "typing.no-any",
        ],
    )


def test_aliases_map_back_to_exactus_ids() -> None:
    """Keep the Exactus ids reachable for report comparison."""
    expect_equal(
        actual={
            rule.code: rule.aliases["exactus"] for rule in _catalog().rules
        },
        expected={
            "TYP001": "CMP002",
            "TYP004": "PY002",
            "CAL001": "KWARGS:missing-kwargs",
            "DOC002": "DOC002",
            "TYP003": "KWARGS:missing-hint",
        },
    )


def test_package_data_ships_catalog_files() -> None:
    """Resolve every data file through importlib.resources."""
    root: Traversable = files("astart.rules")
    for name in Constants.catalog_files:
        expect_true(condition=root.joinpath("catalog", name).is_file())
    expect_true(condition=root.joinpath("schema.json").is_file())
    expect_true(condition="check" in dir(rules))


def test_model_layer_does_not_import_astart_internals() -> None:
    """Keep the ontology independent of the AST packages."""
    package: Path = Path(str(object=files("astart.rules")))
    for name in (
        "vocabulary",
        "jsonvalue",
        "predicate",
        "model",
        "registry",
        "catalog",
        "schema",
    ):
        text: str = (package / f"{name}.py").read_text(encoding="utf-8")
        expect_equal(
            actual=Constants.forbidden.findall(string=text),
            expected=[],
            message=(f"{name}.py imports astart internals"),
        )
