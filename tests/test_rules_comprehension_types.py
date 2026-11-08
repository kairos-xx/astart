"""Comprehension displays are typed when their element types are provable."""

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

from tests.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source: Module source to fix.

    Returns:
        Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_range_targets_are_ints() -> None:
    """Check that a ``range`` loop variable types the element."""
    out: str = _fixed(
        source="def f(n):\n    return [i * 2 for i in range(n)]\n",
    )
    expect_in(item="def f(n) -> list[int]:", container=out)


def test_dict_and_set_comprehensions() -> None:
    """Check that dict and set comprehensions type keys and values."""
    out: str = _fixed(
        source="""
        def g():
            return {c: 0 for c in "ab"}

        def h():
            return {str(i) for i in range(3)}
        """,
    )
    expect_in(item="def g() -> dict[str, int]:", container=out)
    expect_in(item="def h() -> set[str]:", container=out)


def test_unknown_iterables_prove_nothing() -> None:
    """Check that iterating an untyped value leaves the element unknown."""
    out: str = _fixed(source="def f(xs):\n    return [x for x in xs]\n")
    expect_not_in(item="def f(xs) ->", container=out)


def test_the_loop_variable_shadows_an_outer_name() -> None:
    """Check that the target hides a same-named outer constant."""
    out: str = _fixed(
        source="""
        i = "s"

        def f():
            return [i for i in range(3)]
        """,
    )
    expect_in(item="def f() -> list[int]:", container=out)


def test_async_comprehensions_are_left_alone() -> None:
    """Check that ``async for`` comprehensions are never typed."""
    out: str = _fixed(
        source="""
        async def f(src):
            return [i async for i in src]
        """,
    )
    expect_not_in(item="-> list", container=out)
