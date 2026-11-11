"""Verify the ``--version``, ``rules`` and ``explain`` commands."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, cast, final

import pytest
from astart.__main__ import main
from astart.cli.commands import run_explain, run_rules
from astart.rules import default_registries, load_default_catalog

from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Rule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        known_code (str): Grouped module constant.
        unknown_code (str): Grouped module constant.

    """

    known_code: str = "TYP005"
    unknown_code: str = "NOPE99"


def _catalog() -> Catalog:
    """Load the shipped catalog.

    Returns:
        Catalog: The validated default catalog.

    """
    return load_default_catalog(registries=default_registries())


def test_version_flag_prints_version(
    *,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check ``--version`` exits zero with a non-empty line.

    Args:
        capsys (pytest.CaptureFixture[str]): pytest output capture.

    """
    with pytest.raises(expected_exception=SystemExit) as raised:
        _ = main(argv=["--version"])
    expect_equal(actual=raised.value.code, expected=0)
    expect_true(condition=bool(capsys.readouterr().out.strip()))


def test_rules_lists_every_catalog_rule() -> None:
    """Check ``run_rules`` prints one line per catalog rule."""
    out: StringIO = StringIO()
    expect_equal(actual=run_rules(out=out), expected=0)
    lines: list[str] = out.getvalue().splitlines()
    expect_equal(actual=len(lines), expected=len(_catalog().rules))
    expect_in(item="TYP005", container=out.getvalue())
    expect_in(item="STR001", container=out.getvalue())


def test_rules_json_lists_documented_keys() -> None:
    """Check ``run_rules(as_json=True)`` emits the schema keys."""
    out: StringIO = StringIO()
    expect_equal(actual=run_rules(out=out, as_json=True), expected=0)
    entries: list[dict[str, JsonValue]] = cast(
        typ="list[dict[str, JsonValue]]",
        val=loads(s=out.getvalue()),
    )
    expect_equal(actual=len(entries), expected=len(_catalog().rules))
    for entry in entries:
        for key in ("code", "key", "title", "maturity", "severity", "fixes"):
            expect_in(item=key, container=entry)
        fixes: list[dict[str, JsonValue]] = cast(
            typ="list[dict[str, JsonValue]]",
            val=entry["fixes"],
        )
        for fix in fixes:
            expect_in(item="key", container=fix)
            expect_in(item="safety", container=fix)


def test_explain_prints_rationale_and_examples() -> None:
    """Check ``run_explain`` prints rationale and flagged/clean examples."""
    catalog: Catalog = _catalog()
    rule: Rule = next(
        item for item in catalog.rules if item.code == Constants.known_code
    )
    out: StringIO = StringIO()
    err: StringIO = StringIO()
    expect_equal(
        actual=run_explain(code=Constants.known_code, out=out, err=err),
        expected=0,
    )
    text: str = out.getvalue()
    expect_in(item=rule.rationale, container=text)
    expect_in(item="flagged:", container=text)
    expect_in(item="clean:", container=text)
    for example in rule.examples:
        expect_in(item=example.source, container=text)


def test_explain_unknown_code_returns_two() -> None:
    """Check ``run_explain`` rejects an unknown code with status two."""
    out: StringIO = StringIO()
    err: StringIO = StringIO()
    expect_equal(
        actual=run_explain(code=Constants.unknown_code, out=out, err=err),
        expected=2,
    )
    expect_in(item=Constants.unknown_code, container=err.getvalue())
