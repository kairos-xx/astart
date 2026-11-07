"""Verify TypeVar synthesis through the fix runner."""

from __future__ import annotations

import ast
from textwrap import dedent

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_in, expect_not_in


def _fix(*, source: str, ceiling: FixSafety = FixSafety.guarded) -> FixResult:
    registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling),
    )


def test_identity_function_becomes_generic() -> None:
    """Check that identity function becomes generic."""
    result = _fix(source="def identity(x):\n    return x\n")
    ast.parse(source=result.source)
    expect_in(item="from typing import TypeVar", container=result.source)
    expect_in(item="T = TypeVar(", container=result.source)
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_declaration_precedes_the_function() -> None:
    """Check that declaration precedes the function."""
    result = _fix(source="def identity(x):\n    return x\n")
    expect_in(item="T = TypeVar", container=result.source)
    assert_order = result.source.index("T = TypeVar") < result.source.index(
        "def identity",
    )
    expect_equal(actual=assert_order, expected=True)


def test_container_of_the_parameter_keeps_the_variable() -> None:
    """Check that container of the parameter keeps the variable."""
    wrapped = _fix(source="def wrap(x):\n    return [x]\n")
    expect_in(item="def wrap(x: T) -> list[T]:", container=wrapped.source)
    paired = _fix(source="def pair(x):\n    return (x, x)\n")
    expect_in(item="-> tuple[T, T]:", container=paired.source)


def test_call_sites_do_not_override_the_variable() -> None:
    """Check that call sites do not override the variable."""
    result = _fix(source="def identity(x):\n    return x\n\n\nidentity(1)\n")
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_existing_declaration_is_reused() -> None:
    """Check that existing declaration is reused."""
    result = _fix(
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
    result = _fix(source="T = 3\n\n\ndef identity(x):\n    return x\n")
    expect_in(item="def identity(x: T2) -> T2:", container=result.source)


def test_constraining_uses_get_no_variable() -> None:
    """Check that constraining uses get no variable."""
    for source in (
        "def f(x):\n    return x + 1\n",
        "def f(x):\n    return x.name\n",
        "def f(x):\n    print(x)\n    return x\n",
        "def f(x):\n    print(x)\n",
        "def f(x):\n    return 1\n",
        "def f(x=1):\n    return x\n",
        "def f(x):\n    yield x\n",
    ):
        expect_not_in(
            item="TypeVar",
            container=_fix(source=source).source,
            message=source,
        )


def test_method_declaration_precedes_the_class() -> None:
    """Check that method declaration precedes the class."""
    result = _fix(
        source="""
        class Box:
            def get(self, x):
                return x
        """,
    )
    ast.parse(source=result.source)
    expect_equal(
        actual=result.source.index("T = TypeVar")
        < result.source.index("class Box"),
        expected=True,
    )
    expect_in(item="def get(self, x: T) -> T:", container=result.source)


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first = _fix(source="def identity(x):\n    return x\n")
    second = _fix(source=first.source)
    expect_equal(actual=second.source, expected=first.source)


def test_proven_ceiling_does_not_synthesize() -> None:
    """Check that proven ceiling does not synthesize."""
    result = _fix(
        source="def identity(x):\n    return x\n",
        ceiling=FixSafety.proven,
    )
    expect_not_in(item="TypeVar", container=result.source)
