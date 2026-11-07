"""Verify that imported constructors type their calls."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the guarded fixer on a dedented snippet.

    Args:
        source: Python source.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def test_imported_constructor_proves_the_return_type() -> None:
    """Check that imported constructor proves the return type."""
    result: FixResult = _fix(
        source="""
        from pathlib import Path


        def home():
            return Path("x")
        """,
    )
    expect_in(item="def home() -> Path:", container=result.source)


def test_call_site_argument_built_by_a_constructor_gives_the_hint() -> None:
    """Check that call site argument built by a constructor gives the hint."""
    result: FixResult = _fix(
        source="""
        from pathlib import Path


        def show(p):
            print(p)


        show(Path("x"))
        """,
    )
    expect_in(item="def show(p: Path)", container=result.source)


def test_shadowed_or_aliased_names_are_not_constructors() -> None:
    """Check that shadowed or aliased names are not constructors."""
    for source in (
        """\
def Path(x):
    return x


def home():
    return Path('x')
""",
        """\
from pathlib import Path as P


def home():
    return P('x')
""",
        """\
from mine import Path


def home():
    return Path('x')
""",
    ):
        expect_not_in(item="-> Path", container=_fix(source=source).source)
