"""Repeated ``fix_source`` calls on identical text give identical output."""

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

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Run the fix pipeline on one source.

    Args:
        source: Python source text.

    Returns:
        The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_repeated_fix_source_calls_are_identical() -> None:
    """Check five small modules fix identically on a second call."""
    modules: tuple[str, ...] = (
        "def f(a, b):\n    pass\n\nf(1, 2)\n",
        "x = 1\n",
        "def f():\n    return 1\n",
        "class A:\n    pass\n",
        "import os\nos.getcwd()\n",
    )
    for source in modules:
        first: str = _fixed(source=source)
        second: str = _fixed(source=source)
        expect_equal(actual=second, expected=first)
