"""``return self.x`` is typed from the class's agreed attribute table."""

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
        settings=FixSettings(ceiling=FixSafety.guarded, negotiate=False),
    ).source


def test_returning_an_agreed_attribute_gets_its_type() -> None:
    """Check that ``return self.size`` is annotated ``-> int``."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self) -> None:
                self.size = 3

            def get(self):
                return self.size
        """,
    )
    expect_in(item="def get(self) -> int:", container=out)


def test_arithmetic_on_attributes_keeps_the_type() -> None:
    """Check that ``self.a + 1`` is typed through the table."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self) -> None:
                self.a = 1

            def next(self):
                return self.a + 1
        """,
    )
    expect_in(item="def next(self) -> int:", container=out)


def test_optional_attributes_return_optional() -> None:
    """Check that ``None`` plus ``int`` writes give ``int | None``."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self) -> None:
                self.size = None

            def grow(self) -> None:
                self.size = 2

            def get(self):
                return self.size
        """,
    )
    expect_in(item="def get(self) -> int | None:", container=out)


def test_disagreeing_writes_leave_the_read_untyped() -> None:
    """Check that an attribute with conflicting writes proves nothing."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self) -> None:
                self.size = 3

            def rename(self) -> None:
                self.size = "big"

            def get(self):
                return self.size
        """,
    )
    expect_not_in(item="def get(self) ->", container=out)


def test_a_rebound_receiver_is_not_trusted() -> None:
    """Check that reassigning ``self`` inside the method blocks the proof."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self) -> None:
                self.size = 3

            def get(self, other):
                self = other
                return self.size
        """,
    )
    expect_not_in(item="def get(self, other) ->", container=out)


def test_another_class_with_the_same_attribute_is_independent() -> None:
    """Check that each class uses its own table."""
    out: str = _fixed(
        source="""
        class A:
            def __init__(self) -> None:
                self.v = 1

            def get(self):
                return self.v

        class B:
            def __init__(self) -> None:
                self.w = "x"

            def get(self):
                return self.w
        """,
    )
    expect_in(item="def get(self) -> int:", container=out)
    expect_in(item="def get(self) -> str:", container=out)
