"""Verify the closed vocabulary of skip and rejection reasons."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.reasons import Rejection, SkipCode
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult


def test_conflicting_fix_is_skipped_with_the_conflict_code() -> None:
    """Check that conflicting fix is skipped with the conflict code."""
    registries: Registries = default_registries()
    result: FixResult = fix_source(
        source="""\
def identity(x):
    return x


identity(1)
""",
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    codes: set[SkipCode] = {item.code for item in result.skipped}
    expect_in(item=SkipCode.conflict, container=codes)


def test_codes_are_stable_strings() -> None:
    """Check that codes are stable strings."""
    expect_equal(actual=str(object=SkipCode.write_back), expected="write-back")
    expect_equal(
        actual=str(object=SkipCode.checker_rejected),
        expected="checker-rejected",
    )
    expect_equal(
        actual=str(object=Rejection.no_candidate),
        expected="no candidate",
    )
    expect_equal(
        actual=str(object=Rejection.escapes),
        expected="escapes as a value",
    )
