"""Verify NoReturn for functions that always raise."""

from __future__ import annotations

from ast import parse
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

from tests.support.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the proven fix pipeline over dedented source.

    Args:
        source (str): Source text to fix.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.proven),
    )


def test_raise_only_function_returns_noreturn() -> None:
    """Check that raise only function returns noreturn."""
    result: FixResult = _fix(
        source="""\
def fail():
    raise ValueError('x')
""",
    )
    parse(source=result.source)
    expect_in(item="def fail() -> NoReturn:", container=result.source)
    expect_in(item="from typing import NoReturn", container=result.source)


def test_every_branch_raising_is_noreturn() -> None:
    """Check that every branch raising is noreturn."""
    result: FixResult = _fix(
        source="""
        def fail(flag):
            if flag:
                raise ValueError("a")
            else:
                raise KeyError("b")
        """,
    )
    expect_in(item=") -> NoReturn:", container=result.source)


def test_async_raise_only_function_is_noreturn() -> None:
    """Check that async raise only function is noreturn."""
    result: FixResult = _fix(
        source="""\
async def fail():
    raise ValueError('x')
""",
    )
    expect_in(item="async def fail() -> NoReturn:", container=result.source)


def test_conditional_raise_still_returns_none() -> None:
    """Check that conditional raise still returns none."""
    result: FixResult = _fix(
        source=dedent(
            text="""\
    def check(flag):
        if flag:
            raise ValueError('x')
    """,
        ),
    )
    expect_in(item=") -> None:", container=result.source)
    expect_not_in(item="NoReturn", container=result.source)


def test_generator_and_return_functions_are_not_noreturn() -> None:
    """Check that generator and return functions are not noreturn."""
    for source in (
        """\
def gen():
    yield 1
    raise ValueError('x')
""",
        dedent(
            text="""\
    def early(flag):
        if flag:
            return
        raise ValueError('x')
    """,
        ),
    ):
        expect_not_in(item="NoReturn", container=_fix(source=source).source)
