"""A literal default is only as trustworthy as its measured exactness."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.confidence import Constants as ConfidenceConstants
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart.rules.registry import Registries


def _fixed(*, source: str, floor: float) -> str:
    """Fix a module at the guarded ceiling with a custom floor.

    Args:
        source (str): Module text.
        floor (float): Minimum confidence a fix needs to be written.

    Returns:
        str: The fixed text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded, min_confidence=floor),
    ).source


DEFAULT_FLOOR: Final[float] = ConfidenceConstants.default_minimum


def test_the_default_floor_sits_between_the_tiers() -> None:
    """Check the tier boundaries the policy relies on."""
    by: Mapping[str, float] = ConfidenceConstants.by_literal
    expect_equal(actual=by["bool"] >= DEFAULT_FLOOR, expected=True)
    expect_equal(actual=by["float"] >= DEFAULT_FLOOR, expected=True)
    expect_equal(actual=by["int"] < DEFAULT_FLOOR, expected=True)
    expect_equal(actual=by["str"] < DEFAULT_FLOOR, expected=True)


def test_bool_and_float_defaults_are_written_at_the_default_floor() -> None:
    """Check the reliable literal types."""
    out: str = _fixed(
        source="""
        def f(flag=True, ratio=0.5):
            return flag
        """,
        floor=DEFAULT_FLOOR,
    )
    expect_in(item="flag: bool = True", container=out)
    expect_in(item="ratio: float = 0.5", container=out)


def test_int_and_str_defaults_are_held_back_at_the_default_floor() -> None:
    """Check that a bare ``int``/``str`` default is not enough."""
    out: str = _fixed(
        source="""
        def f(timeout=5, mode="r"):
            return timeout
        """,
        floor=DEFAULT_FLOOR,
    )
    expect_not_in(item="timeout: int", container=out)
    expect_not_in(item="mode: str", container=out)


def test_they_are_written_when_the_floor_is_lowered() -> None:
    """Check that ``--min-confidence 0`` opts into the riskier tier."""
    out: str = _fixed(
        source="""
        def f(timeout=5, mode="r"):
            return timeout
        """,
        floor=0.0,
    )
    expect_in(item="timeout: int = 5", container=out)
    expect_in(item='mode: str = "r"', container=out)


def test_agreeing_call_sites_lift_a_default_to_the_strong_tier() -> None:
    """Check that independent evidence restores the annotation."""
    out: str = _fixed(
        source="""
        def f(timeout=5):
            return timeout

        f(1)
        f(timeout=2)
        """,
        floor=DEFAULT_FLOOR,
    )
    expect_in(item="timeout: int = 5", container=out)


def test_disagreeing_call_sites_do_not_lift_it() -> None:
    """Check that a float call site keeps the int default held back."""
    out: str = _fixed(
        source="""
        def f(timeout=5):
            return timeout

        f(1.5)
        """,
        floor=DEFAULT_FLOOR,
    )
    expect_not_in(item="timeout: int", container=out)
