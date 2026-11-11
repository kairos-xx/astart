"""Disagreeing call sites become a union when the engine corroborates it."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Fix a module at the guarded ceiling.

    Args:
        source (str): Module text.

    Returns:
        str: The fixed text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_two_proven_types_with_matching_candidate_make_a_union() -> None:
    """Check that ``int`` and ``str`` callers give ``int | str``."""
    fixed: str = _fixed(
        source="""
        def f(x):
            return len(str(x))

        f(1)
        f("a")
        """,
    )
    expect_in(item="x: int | str", container=fixed)


def test_one_unproven_site_blocks_the_union() -> None:
    """Check that an argument the syntax cannot prove blocks the union."""
    fixed: str = _fixed(
        source="""
        def f(x):
            return len(str(x))

        def g(y):
            f(y)

        f(1)
        f("a")
        """,
    )
    expect_not_in(item="x: int | str", container=fixed)


def test_four_distinct_types_exceed_the_union_limit() -> None:
    """Check that more than three member types are refused."""
    fixed: str = _fixed(
        source="""
        def f(x):
            return len(str(x))

        f(1)
        f("a")
        f(1.5)
        f(b"b")
        """,
    )
    expect_not_in(item="x: int | str | float | bytes", container=fixed)


def test_bool_beside_int_collapses_to_int() -> None:
    """Check that ``bool`` and ``int`` callers give plain ``int``."""
    fixed: str = _fixed(
        source="""
        def f(x):
            return len(str(x))

        f(True)
        f(1)
        """,
    )
    expect_in(item="x: int)", container=fixed)
    expect_not_in(item="bool", container=fixed)
