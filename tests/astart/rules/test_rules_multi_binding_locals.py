"""Locals bound several times are typed when every binding agrees."""

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
    """Fix ``source`` and return the rewritten module.

    Args:
        source (str): Module source to fix.

    Returns:
        str: Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_branch_assignments_of_one_type() -> None:
    """Check that two literal assignments of the same type agree."""
    out: str = _fixed(
        source="""
        def f(flag):
            n = 0
            if flag:
                n = 1
            return n
        """,
    )
    expect_in(item="def f(flag) -> int:", container=out)


def test_counter_with_augmented_assignment() -> None:
    """Check that ``total += 1`` keeps the counter an ``int``."""
    out: str = _fixed(
        source="""
        def count(items):
            total = 0
            for _ in items:
                total += 1
            return total
        """,
    )
    expect_in(item="def count(items: Iterable) -> int:", container=out)


def test_self_referential_update() -> None:
    """Check that ``x = x * 2`` agrees with its own start value."""
    out: str = _fixed(
        source="""
        def grow(steps):
            x = 1
            for _ in steps:
                x = x * 2
            return x
        """,
    )
    expect_in(item="def grow(steps: Iterable) -> int:", container=out)


def test_disagreeing_bindings_prove_nothing() -> None:
    """Check that an int and a str binding leave the return untyped."""
    out: str = _fixed(
        source="""
        def f(flag):
            v = 1
            if flag:
                v = "a"
            return v
        """,
    )
    expect_not_in(item="def f(flag) ->", container=out)


def test_widening_augmented_assignment_is_refused() -> None:
    """Check that ``int += float`` is not an ``int``."""
    out: str = _fixed(
        source="""
        def f(items):
            v = 0
            for _ in items:
                v += 0.5
            return v
        """,
    )
    expect_not_in(item="-> int", container=out)


def test_a_loop_target_with_the_same_name_blocks_the_proof() -> None:
    """Check that ``for x in ...`` makes ``x`` unknowable."""
    out: str = _fixed(
        source="""
        def f(xs):
            x = 0
            for x in xs:
                pass
            return x
        """,
    )
    expect_not_in(item="def f(xs) ->", container=out)
