"""Public one-call ``check_source``/``fix_source`` wrappers (API-02)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart import (
    __all__,
)
from astart import (
    check_source as root_check_source,
)
from astart import (
    fix_source as root_fix_source,
)
from astart.api import check_source, fix_source
from astart.rules import FixSettings
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart.rules.engine import CheckResult
    from astart.rules.runner import FixResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        untyped (Final[str]): Small module without annotations.
        annotated (Final[str]): Small module with one existing annotation.
        flagged (Final[str]): Small module with one ``TYP001`` finding.

    """

    untyped: Final[str] = """\
def add(a, b):
    return a + b
"""
    annotated: Final[str] = """\
def add(a: int, b: int) -> int:
    return a + b
"""
    flagged: Final[str] = """\
from typing import Any


def f(x: Any) -> int:
    return 1
"""


def test_fix_source_is_importable_from_package_root() -> None:
    """``from astart import fix_source`` resolves lazily."""
    expect_true(condition=root_fix_source is fix_source)
    expect_true(condition=root_check_source is check_source)
    expect_true(condition="fix_source" in __all__)
    expect_true(condition="check_source" in __all__)


def test_fix_source_round_trip() -> None:
    """The wrapper applies the default guarded catalog."""
    result: FixResult = fix_source(source=Constants.untyped, filename="mod.py")
    expect_equal(actual=result.parse_error, expected=None)
    expect_true(condition="->" in result.source)


def test_fix_source_respects_explicit_settings() -> None:
    """A caller-supplied ``FixSettings`` replaces the default."""
    settings: FixSettings = FixSettings(ceiling=FixSafety.proven)
    result: FixResult = fix_source(
        source=Constants.untyped,
        filename="mod.py",
        settings=settings,
    )
    expect_equal(actual=result.parse_error, expected=None)


def test_fix_source_keeps_existing_annotations() -> None:
    """Existing annotations survive a wrapper fix run."""
    result: FixResult = fix_source(
        source=Constants.annotated,
        filename="mod.py",
    )
    expect_equal(actual=result.parse_error, expected=None)
    expect_true(condition="a: int" in result.source)
    expect_true(condition="-> int" in result.source)


def test_check_source_returns_findings() -> None:
    """The wrapper reports catalog findings on real source."""
    result: CheckResult = check_source(
        source=Constants.flagged,
        filename="mod.py",
    )
    expect_equal(actual=result.parse_error, expected=None)
    expect_equal(
        actual=[finding.rule_key for finding in result.findings],
        expected=["typing.no-any"],
    )


def test_check_source_reports_parse_errors() -> None:
    """Invalid source surfaces through ``parse_error``."""
    result: CheckResult = check_source(
        source="""\
def broken(:
""",
        filename="bad.py",
    )
    expect_true(condition=result.parse_error is not None)
    expect_equal(actual=result.findings, expected=())
