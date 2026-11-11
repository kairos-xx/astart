"""Tests for the WSP catalog rules and their text-level fixes."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules.catalog import load_default_catalog
from astart.rules.engine import check
from astart.rules.facts import default_registries
from astart.rules.runner import FixResult, FixSettings, fix_source
from astart.rules.vocabulary import FixSafety
from astart.rules.whitespace_rules import (
    collapse_blank_lines,
    strip_trailing_space,
)

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.engine import CheckResult
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_names (Final[tuple[str, ...]]): Vendored modules used for
            idempotence checks.
        dirty (Final[str]): Source with both violation kinds.
        clean (Final[str]): Source without violations.
        stringy (Final[str]): Violations inside a string literal only.

    """

    corpus_names: Final[tuple[str, ...]] = (
        "codeop.py",
        "copy.py",
        "genericpath.py",
    )
    dirty: Final[str] = "x = 1\n\n\n\ny = 2  \nz = 3\n"
    clean: Final[str] = """\
x = 1


y = 2
z = 3
"""
    stringy: Final[str] = 's = """a\n\n\n\nb  \n"""\nx = 1\n'


def _catalog() -> Catalog:
    """Load the default catalog restricted to the whitespace rules.

    Returns:
        Catalog: A catalog holding only WSP rules and fixes.

    """
    registries: Registries = default_registries()
    full: Catalog = load_default_catalog(registries=registries)
    return replace(
        full,
        rules=tuple(r for r in full.rules if r.key.startswith("whitespace.")),
        fixes=tuple(f for f in full.fixes if f.key.startswith("whitespace.")),
    )


def _fix(*, source: str) -> FixResult:
    """Run the guarded fixer with only the whitespace rules.

    Args:
        source (str): Python source.

    Returns:
        FixResult: The fix result.

    """
    return fix_source(
        source=source,
        filename="t.py",
        catalog=_catalog(),
        registries=default_registries(),
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def _wsp_keys(*, result: FixResult) -> set[str]:
    """Return the whitespace fix keys applied in a result.

    Args:
        result (FixResult): Fix result.

    Returns:
        set[str]: The applied whitespace fix keys.

    """
    return {item.fix_key for item in result.applied}


def test_collapse_blank_lines_module_and_block() -> None:
    """Module runs keep two blanks, indented runs keep one."""
    source: str = """\
x = 1




def f():
    a = 1



    b = 2
"""
    expect_equal(
        actual=collapse_blank_lines(source=source),
        expected="""\
x = 1


def f():
    a = 1

    b = 2
""",
    )


def test_collapse_blank_lines_end_of_file() -> None:
    """Trailing blank runs at end of file are removed."""
    expect_equal(
        actual=collapse_blank_lines(
            source="""\
x = 1



""",
        ),
        expected="""\
x = 1
""",
    )


def test_collapse_blank_lines_skips_string_interior() -> None:
    """Blank runs inside a triple-quoted string are content."""
    source: str = Constants.stringy
    expect_equal(actual=collapse_blank_lines(source=source), expected=source)


def test_strip_trailing_space_skips_string_interior() -> None:
    """Trailing whitespace inside a string literal is preserved."""
    source: str = Constants.stringy
    expect_equal(actual=strip_trailing_space(source=source), expected=source)


def test_check_reports_whitespace_findings() -> None:
    """WSP001 and WSP002 fire on the module with fix offers."""
    result: CheckResult = check(
        source=Constants.dirty,
        filename="t.py",
        catalog=_catalog(),
        registries=default_registries(),
    )
    by_rule: dict[str, list[str]] = {}
    for finding in result.findings:
        by_rule[finding.rule_key] = [
            offer.fix_key for offer in finding.fix_offers
        ]
    expect_equal(
        actual=by_rule.get("whitespace.excessive-blank-lines"),
        expected=["whitespace.collapse-blank-lines"],
    )
    expect_equal(
        actual=by_rule.get("whitespace.trailing-space"),
        expected=["whitespace.strip-trailing-space"],
    )


def test_fix_applies_whitespace_and_is_idempotent() -> None:
    """Both text fixes apply; a second run changes nothing."""
    first: FixResult = _fix(source=Constants.dirty)
    expect_equal(
        actual=_wsp_keys(result=first),
        expected={
            "whitespace.collapse-blank-lines",
            "whitespace.strip-trailing-space",
        },
    )
    expect_equal(actual=first.source, expected=Constants.clean)
    second: FixResult = _fix(source=first.source)
    expect_equal(actual=second.source, expected=first.source)
    expect_equal(actual=_wsp_keys(result=second), expected=set())


def test_proven_ceiling_leaves_whitespace_alone() -> None:
    """Guarded text fixes are not applied under the proven ceiling."""
    result: FixResult = fix_source(
        source=Constants.dirty,
        filename="t.py",
        catalog=_catalog(),
        registries=default_registries(),
        settings=FixSettings(ceiling=FixSafety.proven),
    )
    expect_equal(actual=_wsp_keys(result=result), expected=set())
    expect_equal(actual=result.source, expected=Constants.dirty)


def test_string_only_violations_stay_silent() -> None:
    """Violations inside string literals are string content, not findings."""
    result: FixResult = _fix(source=Constants.stringy)
    expect_equal(actual=result.source, expected=Constants.stringy)
    expect_equal(actual=_wsp_keys(result=result), expected=set())
    expect_equal(actual=result.skipped, expected=())


@pytest.mark.parametrize("name", Constants.corpus_names)
def test_corpus_whitespace_fixes_are_idempotent(*, name: str) -> None:
    """Fixing a vendored module twice yields the same source.

    Args:
        name (str): Corpus file name under ``tests/corpus/base``.

    """
    path: Path = Paths.tests / "corpus" / "base" / name
    source: str = path.read_text(encoding="utf-8")
    first: FixResult = _fix(source=source)
    second: FixResult = _fix(source=first.source)
    expect_equal(actual=second.source, expected=first.source)
