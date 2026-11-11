"""Protocol dunders take their declared result, not the body-derived one."""

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


def _fixed(
    *,
    source: str,
    ceiling: FixSafety = FixSafety.guarded,
) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source (str): Module source to fix.
        ceiling (FixSafety): Highest fix safety level allowed.

    Returns:
        str: Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling),
    ).source


def test_exit_methods_get_the_protocol_result() -> None:
    """Check that exit methods get the protocol result."""
    out: str = _fixed(
        source="""
        class C:
            def __exit__(self, a, b, c):
                print("x")

            async def __aexit__(self, a, b, c):
                return False
        """,
    )
    expect_in(
        item="def __exit__(self, a, b, c) -> bool | None:",
        container=out,
    )
    expect_in(
        item="async def __aexit__(self, a, b, c) -> bool | None:",
        container=out,
    )


def test_exit_is_never_narrowed_to_none_by_the_proven_fix() -> None:
    """Check that exit is never narrowed to none by the proven fix."""
    out: str = _fixed(
        source="""
        class C:
            def __exit__(self, a, b, c):
                print("x")
        """,
        ceiling=FixSafety.proven,
    )
    expect_not_in(item="-> None", container=out)


def test_scalar_dunders_keep_their_declared_type() -> None:
    """Check that scalar dunders keep their declared type."""
    out: str = _fixed(
        source="""
        class C:
            def __bool__(self):
                return True

            def __len__(self):
                return 3

            def __str__(self):
                return f"C{1}"

            def __hash__(self):
                return 1
        """,
    )
    for expected in (
        "def __bool__(self) -> bool:",
        "def __len__(self) -> int:",
        "def __str__(self) -> str:",
        "def __hash__(self) -> int:",
    ):
        expect_in(item=expected, container=out)


def test_bodies_that_contradict_the_protocol_get_nothing() -> None:
    """Check that bodies that contradict the protocol get nothing."""
    out: str = _fixed(
        source="""
        class C:
            def __len__(self):
                return 0.5

            def __exit__(self, a, b, c):
                return 1
        """,
    )
    expect_not_in(item="-> int", container=out)
    expect_not_in(item="-> bool | None", container=out)
