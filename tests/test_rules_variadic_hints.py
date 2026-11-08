"""``*args`` and ``**kwargs`` are typed only when every call proves it."""

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


def test_star_args_take_the_type_every_call_passes() -> None:
    """Check that ``*args`` becomes the shared element type."""
    out: str = _fixed(
        source="""
        def total(*values):
            return sum(values)

        total(1, 2)
        total(3)
        """,
    )
    expect_in(item="*values: int", container=out)


def test_double_star_kwargs_take_the_shared_value_type() -> None:
    """Check that ``**options`` becomes the shared value type."""
    out: str = _fixed(
        source="""
        def configure(**options):
            return options

        configure(a="x", b="y")
        """,
    )
    expect_in(item="**options: str", container=out)


def test_mixed_types_are_left_alone() -> None:
    """Check that disagreeing extras leave ``*args`` unannotated."""
    out: str = _fixed(
        source="""
        def show(*items):
            return items

        show(1, "a")
        """,
    )
    expect_not_in(item="*items:", container=out)


def test_an_unpacked_call_blocks_the_hint() -> None:
    """Check that ``f(*xs)`` makes the extras unknown."""
    out: str = _fixed(
        source="""
        def total(*values):
            return values

        def run(xs):
            return total(*xs)

        total(1, 2)
        """,
    )
    expect_not_in(item="*values:", container=out)


def test_a_function_without_extras_at_any_call_gets_no_guess() -> None:
    """Check that no evidence means no annotation."""
    out: str = _fixed(
        source="""
        def total(first, *rest):
            return first

        total(1)
        """,
    )
    expect_not_in(item="*rest:", container=out)


def test_the_name_inside_the_body_is_not_typed_as_the_element() -> None:
    """Check that ``values`` in the body stays a tuple, not an ``int``."""
    out: str = _fixed(
        source="""
        def total(*values):
            return values

        total(1, 2)
        """,
    )
    expect_not_in(item="-> int", container=out)
