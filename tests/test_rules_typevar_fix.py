"""Verify TypeVar synthesis through the fix runner."""

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

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str, ceiling: FixSafety = FixSafety.guarded) -> FixResult:
    """Run the fixer on a dedented snippet.

    Args:
        source: Python source.
        ceiling: Highest fix safety to apply.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling),
    )


def test_identity_function_becomes_generic() -> None:
    """Check that identity function becomes generic."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    parse(source=result.source)
    expect_in(item="from typing import TypeVar", container=result.source)
    expect_in(item="T = TypeVar(", container=result.source)
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_declaration_precedes_the_function() -> None:
    """Check that declaration precedes the function."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    expect_in(item="T = TypeVar", container=result.source)
    assert_order: bool = result.source.index(
        "T = TypeVar",
    ) < result.source.index(
        "def identity",
    )
    expect_equal(actual=assert_order, expected=True)


def test_container_of_the_parameter_keeps_the_variable() -> None:
    """Check that container of the parameter keeps the variable."""
    wrapped: FixResult = _fix(
        source="""\
def wrap(x):
    return [x]
""",
    )
    expect_in(item="def wrap(x: T) -> list[T]:", container=wrapped.source)
    paired: FixResult = _fix(
        source="""\
def pair(x):
    return (x, x)
""",
    )
    expect_in(item="-> tuple[T, T]:", container=paired.source)


def test_call_sites_do_not_override_the_variable() -> None:
    """Check that call sites do not override the variable."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x


identity(1)
""",
    )
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_existing_declaration_is_reused() -> None:
    """Check that existing declaration is reused."""
    result: FixResult = _fix(
        source="""
        from typing import TypeVar

        T = TypeVar("T")


        def a(x):
            return x


        def b(y):
            return y
        """,
    )
    expect_equal(actual=result.source.count("TypeVar("), expected=1)
    expect_in(item="def b(y: T) -> T:", container=result.source)


def test_name_collision_picks_a_fresh_variable() -> None:
    """Check that name collision picks a fresh variable."""
    result: FixResult = _fix(
        source="""\
T = 3


def identity(x):
    return x
""",
    )
    expect_in(item="def identity(x: T2) -> T2:", container=result.source)


def test_constraining_uses_get_no_variable() -> None:
    """Check that constraining uses get no variable."""
    for source in (
        """\
def f(x):
    return x + 1
""",
        """\
def f(x):
    return x.name
""",
        """\
def f(x):
    print(x)
    return x
""",
        """\
def f(x):
    print(x)
""",
        """\
def f(x):
    return 1
""",
        """\
def f(x=1):
    return x
""",
        """\
def f(x):
    yield x
""",
    ):
        expect_not_in(
            item="TypeVar",
            container=_fix(source=source).source,
            message=source,
        )


def test_method_declaration_precedes_the_class() -> None:
    """Check that method declaration precedes the class."""
    result: FixResult = _fix(
        source="""
        class Box:
            def get(self, x):
                return x
        """,
    )
    parse(source=result.source)
    expect_equal(
        actual=result.source.index("T = TypeVar")
        < result.source.index("class Box"),
        expected=True,
    )
    expect_in(item="def get(self, x: T) -> T:", container=result.source)


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    expect_equal(
        actual=(_fix(source=first.source)).source,
        expected=first.source,
    )


def test_proven_ceiling_does_not_synthesize() -> None:
    """Check that proven ceiling does not synthesize."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
        ceiling=FixSafety.proven,
    )
    expect_not_in(item="TypeVar", container=result.source)
