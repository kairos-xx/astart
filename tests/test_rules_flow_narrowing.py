"""``is None`` guards narrow an Optional parameter for return typing."""

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
    """Fix ``source`` and return the rewritten module.

    Args:
        source: Module source to fix.

    Returns:
        The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded, negotiate=False),
    ).source


def test_early_return_on_none_narrows_the_rest() -> None:
    """Check that code after ``if x is None: return`` sees ``int``."""
    out: str = _fixed(
        source="""
        def f(x: int | None):
            if x is None:
                return 0
            return x + 1
        """,
    )
    expect_in(item="def f(x: int | None) -> int:", container=out)


def test_is_not_none_branch_narrows() -> None:
    """Check the positive form."""
    out: str = _fixed(
        source="""
        def g(x: int | None):
            if x is not None:
                return x * 2
            return 0
        """,
    )
    expect_in(item="def g(x: int | None) -> int:", container=out)


def test_else_branch_is_narrowed_too() -> None:
    """Check both arms of an if/else."""
    out: str = _fixed(
        source="""
        def h(x: int | None):
            if x is None:
                return 0
            else:
                return x
        """,
    )
    expect_in(item="def h(x: int | None) -> int:", container=out)


def test_a_guard_that_falls_through_narrows_nothing() -> None:
    """Check that a guard without return proves nothing afterwards."""
    out: str = _fixed(
        source="""
        def k(x: int | None):
            if x is None:
                print(1)
            return x + 1
        """,
    )
    expect_not_in(item="def k(x: int | None) ->", container=out)


def test_a_reassigned_parameter_is_never_narrowed() -> None:
    """Check that rebinding disables the narrowing."""
    out: str = _fixed(
        source="""
        def m(x: int | None):
            if x is None:
                return 0
            x = None
            return x
        """,
    )
    expect_not_in(item="def m(x: int | None) -> int:", container=out)


def test_the_none_arm_never_claims_a_plain_int() -> None:
    """Check that returning ``x`` inside ``x is None`` is not ``int``."""
    out: str = _fixed(
        source="""
        def n(x: int | None):
            if x is None:
                return x
            return 1
        """,
    )
    expect_not_in(item="def n(x: int | None) -> int:", container=out)


def test_isinstance_narrows_a_union_parameter() -> None:
    """Check that ``isinstance`` picks one arm of ``int | str``."""
    out: str = _fixed(
        source="""
        def p(x: int | str):
            if isinstance(x, str):
                return len(x)
            return x + 1
        """,
    )
    expect_in(item="def p(x: int | str) -> int:", container=out)


def test_not_isinstance_swaps_the_arms() -> None:
    """Check the negated form."""
    out: str = _fixed(
        source="""
        def q(x: int | str):
            if not isinstance(x, int):
                return x + "!"
            return str(x)
        """,
    )
    expect_in(item="def q(x: int | str) -> str:", container=out)


def test_isinstance_with_a_tuple_of_classes() -> None:
    """Check ``isinstance(x, (int, float))`` over a three-way union."""
    out: str = _fixed(
        source="""
        def r(x: int | float | str):
            if isinstance(x, (int, float)):
                return x * 2
            return len(x)
        """,
    )
    expect_not_in(item="-> str", container=out)


def test_bool_in_the_union_blocks_int_narrowing() -> None:
    """Check that ``bool`` is an ``int`` so the false arm is unsafe."""
    out: str = _fixed(
        source="""
        def s(x: bool | str):
            if isinstance(x, int):
                return 1
            return x.upper()
        """,
    )
    expect_not_in(item="def s(x: bool | str) ->", container=out)


def test_isinstance_on_an_unlisted_class_narrows_nothing() -> None:
    """Check that a class that is not a union member proves nothing."""
    out: str = _fixed(
        source="""
        def t(x: int | str):
            if isinstance(x, bytes):
                return b""
            return x
        """,
    )
    expect_not_in(item="def t(x: int | str) ->", container=out)


def test_assert_is_not_none_narrows_what_follows() -> None:
    """Check that ``assert x is not None`` removes the ``None`` arm."""
    out: str = _fixed(
        source="""
        def a(x: int | None):
            assert x is not None
            return x + 1
        """,
    )
    expect_in(item="def a(x: int | None) -> int:", container=out)


def test_assert_isinstance_narrows_what_follows() -> None:
    """Check ``assert isinstance(x, int)`` over ``int | str``."""
    out: str = _fixed(
        source="""
        def b(x: int | str):
            assert isinstance(x, int)
            return x * 2
        """,
    )
    expect_in(item="def b(x: int | str) -> int:", container=out)


def test_falsy_early_return_removes_none() -> None:
    """Check that ``if not x: return`` leaves a non-``None`` value."""
    out: str = _fixed(
        source="""
        def c(x: int | None):
            if not x:
                return 0
            return x + 1
        """,
    )
    expect_in(item="def c(x: int | None) -> int:", container=out)


def test_truthy_branch_removes_none() -> None:
    """Check that the body of ``if x:`` sees a non-``None`` value."""
    out: str = _fixed(
        source="""
        def d(x: int | None):
            if x:
                return x + 1
            return 0
        """,
    )
    expect_in(item="def d(x: int | None) -> int:", container=out)


def test_the_falsy_arm_keeps_none_possible() -> None:
    """Check that ``x`` may still be ``0`` or ``None`` when ``if x`` fails."""
    out: str = _fixed(
        source="""
        def e(x: int | None):
            if x:
                return 0
            return x + 1
        """,
    )
    expect_not_in(item="def e(x: int | None) ->", container=out)


def test_a_failing_assert_does_not_narrow_the_other_way() -> None:
    """Check that code before the assert is not narrowed by it."""
    out: str = _fixed(
        source="""
        def f(x: int | None):
            y = x + 1
            assert x is not None
            return y
        """,
    )
    expect_not_in(item="def f(x: int | None) -> int:", container=out)


def test_split_and_encode_are_typed() -> None:
    """Check ``str.split`` and the ``encode``/``decode`` pair."""
    out: str = _fixed(
        source="""
        def g():
            return "a b".split()

        def h():
            return "a".encode()

        def i():
            return b"a".decode()
        """,
    )
    expect_in(item="def g() -> list[str]:", container=out)
    expect_in(item="def h() -> bytes:", container=out)
    expect_in(item="def i() -> str:", container=out)


def test_defaulting_a_none_parameter_narrows_it() -> None:
    """Check ``if x is None: x = 5`` followed by arithmetic."""
    out: str = _fixed(
        source="""
        def a(x: int | None = None):
            if x is None:
                x = 5
            return x + 1
        """,
    )
    expect_in(item="-> int:", container=out)


def test_a_default_of_another_type_blocks_the_proof() -> None:
    """Check that assigning a ``str`` breaks the narrowing."""
    out: str = _fixed(
        source="""
        def b(x: int | None = None):
            if x is None:
                x = "five"
            return x
        """,
    )
    expect_not_in(item="-> int", container=out)
    expect_not_in(item="-> int | None", container=out)


def test_other_writes_to_the_parameter_block_the_proof() -> None:
    """Check that a second assignment makes the name unknowable."""
    out: str = _fixed(
        source="""
        def c(x: int | None = None):
            if x is None:
                x = 5
            x = str(x)
            return x
        """,
    )
    expect_not_in(item="def c(x: int | None = None) -> int", container=out)


def test_a_default_with_an_else_branch_is_not_the_idiom() -> None:
    """Check that only the bare guard form is understood."""
    out: str = _fixed(
        source="""
        def d(x: int | None = None):
            if x is None:
                x = 5
            else:
                x = 6
            return x + 1
        """,
    )
    expect_not_in(item="-> int", container=out)


def test_an_unprovable_default_blocks_the_proof() -> None:
    """Check that ``x = make()`` with an unknown ``make`` proves nothing."""
    out: str = _fixed(
        source="""
        def e(x: int | None = None):
            if x is None:
                x = make()
            return x + 1
        """,
    )
    expect_not_in(item="-> int", container=out)
