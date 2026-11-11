"""A ``None`` default becomes ``T | None`` when call sites prove ``T``."""

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


def test_agreeing_value_sites_give_an_optional_hint() -> None:
    """Check that agreeing value sites give an optional hint."""
    out: str = _fixed(
        source="""
        def f(x=None):
            print(x)


        f(1)
        f(2)
        f(None)
        """,
    )
    expect_in(item="x: int | None = None", container=out)


def test_string_sites_and_keyword_sites() -> None:
    """Check that string sites and keyword sites."""
    out: str = _fixed(
        source="""
        def f(x=None):
            print(x)


        f(x="a")
        """,
    )
    expect_in(item="x: str | None = None", container=out)


def test_method_sites_resolve_through_self() -> None:
    """Check that method sites resolve through self."""
    out: str = _fixed(
        source="""
        class K:
            def m(self, a=None):
                print(a)

            def run(self):
                self.m(1)
        """,
    )
    expect_in(item="a: int | None = None", container=out)


def test_refusals() -> None:
    """Check that refusals leave the parameter alone."""
    cases: dict[str, str] = {
        "no call sites": """\
def f(x=None):
    print(x)
""",
        "only None": """\
def f(x=None):
    print(x)


f(None)
""",
        "disagree": """\
def f(x=None):
    print(x)


f(1)
f('a')
""",
        "unprovable argument": (
            """\
def f(x=None):
    print(x)


y = input()
f(y)
"""
        ),
        "escapes": (
            """\
def f(x=None):
    print(x)


handler = f
f(1)
"""
        ),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_not_in(item="| None", container=out, message=label)
