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

if TYPE_CHECKING:
    from astart.rules.registry import Registries

from tests.expectations import expect_in, expect_not_in


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
        "no call sites": "def f(x=None):\n    print(x)\n",
        "only None": "def f(x=None):\n    print(x)\n\n\nf(None)\n",
        "disagree": "def f(x=None):\n    print(x)\n\n\nf(1)\nf('a')\n",
        "unprovable argument": (
            "def f(x=None):\n    print(x)\n\n\ny = input()\nf(y)\n"
        ),
        "escapes": ("def f(x=None):\n    print(x)\n\n\nhandler = f\nf(1)\n"),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_not_in(item="| None", container=out, message=label)
