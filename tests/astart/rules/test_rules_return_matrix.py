"""Characterize return-type synthesis through the fixer."""

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
def f():
    return 1
""",
            "def f() -> int:",
        ),
        (
            """\
def f():
    return 1.5
""",
            "def f() -> float:",
        ),
        (
            """\
def f():
    return 'a'
""",
            "def f() -> str:",
        ),
        (
            """\
def f():
    return [1, 2]
""",
            "def f() -> list[int]:",
        ),
        (
            """\
def f():
    return {'a': 1}
""",
            "def f() -> dict[str, int]:",
        ),
        (
            """\
def f(x):
    if x:
        return 1
""",
            "def f(x) -> int | None:",
        ),
        (
            """\
def f():
    return None
""",
            "def f() -> None:",
        ),
        pytest.param(
            """\
def f():
    pass
""",
            "def f() -> None:",
            marks=pytest.mark.xfail(
                strict=True,
                reason="Q-57 BLOCKED: pass-only body gets no "
                "return annotation",
            ),
        ),
    ],
)
def test_return_type_matrix(*, source: str, expected: str) -> None:
    """Check the fixed source contains ``expected``.

    Args:
        source (str): Python source text.
        expected (str): Substring the fixed source must contain.

    """
    out: str = _fixed(source=source)
    expect_in(item=expected, container=out)


def test_unknown_attribute_return_gets_no_annotation() -> None:
    """Check ``return x.y`` leaves the ``def`` line without ``->``."""
    out: str = _fixed(
        source="""
        def f(x):
            return x.y
        """,
    )
    def_line: str = next(
        line for line in out.splitlines() if line.startswith("def ")
    )
    expect_not_in(item="->", container=def_line)
