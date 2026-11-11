"""Characterize parameter-hint synthesis through the fixer."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
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
    """Run the fix pipeline on one source.

    Args:
        source (str): Python source text.

    Returns:
        str: The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
def f(x=1):
    return x
""",
            "x: int = 1",
        ),
        (
            """\
def f(x='a'):
    return x
""",
            "x: str = 'a'",
        ),
        (
            """\
def f(x=1.5):
    return x
""",
            "x: float = 1.5",
        ),
        (
            """\
def f(x=True):
    return x
""",
            "x: bool = True",
        ),
        pytest.param(
            """\
def f(x):
    return x

f(1)
f(2)
""",
            "x: int",
            marks=pytest.mark.xfail(
                strict=True,
                reason="Q-58 BLOCKED: call-site hints synthesize "
                "TypeVar T instead of int",
            ),
        ),
    ],
)
def test_param_hint_matrix(*, source: str, expected: str) -> None:
    """Check the fixed source contains ``expected``.

    Args:
        source (str): Python source text.
        expected (str): Substring the fixed source must contain.

    """
    out: str = _fixed(source=source)
    expect_in(item=expected, container=out)


def test_mixed_call_sites_get_no_scalar_hint() -> None:
    """Check ``f(1)``/``f('a')`` yields neither ``x: int`` nor ``x: str``."""
    out: str = _fixed(
        source="""
        def f(x):
            return x

        f(1)
        f('a')
        """,
    )
    expect_not_in(item="x: int", container=out)
    expect_not_in(item="x: str", container=out)
