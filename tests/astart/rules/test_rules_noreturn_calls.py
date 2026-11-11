"""``NoReturn`` follows tail calls to in-module helpers that never return."""

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


def test_a_tail_call_to_a_raising_helper_is_noreturn() -> None:
    """Check that ``f(); fail()`` never returns."""
    out: str = _fixed(
        source="""
        def fail():
            raise RuntimeError("x")

        def wrapper(a):
            print(a)
            fail()
        """,
    )
    expect_in(item="def fail() -> NoReturn:", container=out)
    expect_in(item="def wrapper(a) -> NoReturn:", container=out)


def test_helpers_chain_to_a_fixed_point() -> None:
    """Check two levels of forwarding."""
    out: str = _fixed(
        source="""
        def one():
            raise RuntimeError("x")

        def two():
            one()

        def three():
            two()
        """,
    )
    expect_in(item="def three() -> NoReturn:", container=out)


def test_a_helper_that_can_return_does_not_propagate() -> None:
    """Check that a conditional raise is not NoReturn."""
    out: str = _fixed(
        source="""
        def maybe(flag):
            if flag:
                raise RuntimeError("x")

        def caller(flag):
            maybe(flag)
        """,
    )
    expect_not_in(item="NoReturn", container=out)


def test_a_rebound_helper_name_is_not_trusted() -> None:
    """Check that a name bound twice may be anything."""
    out: str = _fixed(
        source="""
        def fail():
            raise RuntimeError("x")

        fail = print

        def wrapper():
            fail()
        """,
    )
    expect_not_in(item="def wrapper() -> NoReturn", container=out)


def test_not_implemented_placeholders_are_not_noreturn() -> None:
    """Check that an abstract hook may be overridden by one that returns."""
    out: str = _fixed(
        source="""
        class Base:
            def hook(self):
                raise NotImplementedError("override me")
        """,
    )
    expect_not_in(item="NoReturn", container=out)
