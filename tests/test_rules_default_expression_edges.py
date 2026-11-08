"""Default-expression hints refuse contradictory or unprovable types."""

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


def test_str_call_site_blocks_int_default_hint() -> None:
    """Check ``x=-1`` stays unannotated when ``f('a')`` is called."""
    out: str = _fixed(
        source="""
        def f(x=-1):
            return x

        f('a')
        """,
    )
    expect_in(item="def f(x=-1):", container=out)
    expect_not_in(item="x: int", container=out)


def test_parameter_default_name_gets_no_hint() -> None:
    """Check ``x=A`` stays unannotated when ``A`` is only a default."""
    out: str = _fixed(
        source="""
        def g(A=1):
            return A

        def f(x=A):
            return x
        """,
    )
    expect_in(item="def f(x=A):", container=out)
    expect_not_in(item="x: int", container=out)


def test_expression_default_types_to_float_not_int() -> None:
    """Check ``x=1 + 2.0`` is hinted ``float``, never ``int``."""
    out: str = _fixed(
        source="""
        def f(x=1 + 2.0):
            return x
        """,
    )
    expect_in(item="x: float = 1 + 2.0", container=out)
    expect_not_in(item="x: int", container=out)
