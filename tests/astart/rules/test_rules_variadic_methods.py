"""``*args``/``**kwargs`` hints on methods via ``self`` and instances."""

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


def test_star_args_take_the_type_every_method_call_passes() -> None:
    """Check that a method's ``*args`` becomes the shared element type."""
    out: str = _fixed(
        source="""
        class Total:
            def total(self, *values):
                return sum(values)

            def go(self):
                return self.total(1, 2)

        acc = Total()
        acc.total(3)
        Total().total(4, 5)
        """,
    )
    expect_in(item="*values: int", container=out)


def test_double_star_kwargs_take_the_shared_value_type() -> None:
    """Check that a method's ``**options`` becomes the shared value type."""
    out: str = _fixed(
        source="""
        class Configure:
            def configure(self, **options):
                return options

            def go(self):
                return self.configure(a="x")

        conf = Configure()
        conf.configure(b="y")
        Configure().configure(c="z")
        """,
    )
    expect_in(item="**options: str", container=out)


def test_mixed_types_are_left_alone() -> None:
    """Check that disagreeing extras leave a method's ``*args`` bare."""
    out: str = _fixed(
        source="""
        class Show:
            def show(self, *items):
                return items

        show = Show()
        show.show(1, "a")
        """,
    )
    expect_not_in(item="*items:", container=out)


def test_an_unpacked_method_call_blocks_the_hint() -> None:
    """Check that ``self.m(*xs)`` makes a method's extras unknown."""
    out: str = _fixed(
        source="""
        class Total:
            def total(self, *values):
                return values

            def run(self, xs):
                return self.total(*xs)

        total = Total()
        total.total(1, 2)
        """,
    )
    expect_not_in(item="*values:", container=out)


def test_a_method_without_extras_at_any_call_gets_no_guess() -> None:
    """Check that no method-call evidence means no annotation."""
    out: str = _fixed(
        source="""
        class Total:
            def total(self, first, *rest):
                return first

        total = Total()
        total.total(1)
        """,
    )
    expect_not_in(item="*rest:", container=out)


def test_the_name_inside_a_method_body_is_not_typed_as_the_element() -> None:
    """Check that ``values`` in the body stays a tuple, not an ``int``."""
    out: str = _fixed(
        source="""
        class Total:
            def total(self, *values):
                return values

            def go(self):
                return self.total(1, 2)

        Total().total(3, 4)
        """,
    )
    expect_not_in(item="-> int", container=out)
