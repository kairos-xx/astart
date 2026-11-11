"""Comprehension displays are typed when their element types are provable."""

from __future__ import annotations

from tests.support import fixed
from tests.support.expectations import expect_in, expect_not_in


def test_range_targets_are_ints() -> None:
    """Check that a ``range`` loop variable types the element."""
    out: str = fixed(
        source="""\
def f(n):
    return [i * 2 for i in range(n)]
""",
    )
    expect_in(item="def f(n) -> list[int]:", container=out)


def test_dict_and_set_comprehensions() -> None:
    """Check that dict and set comprehensions type keys and values."""
    out: str = fixed(
        source="""
        def g():
            return {c: 0 for c in "ab"}

        def h():
            return {str(i) for i in range(3)}
        """,
    )
    expect_in(item="def g() -> dict[str, int]:", container=out)
    expect_in(item="def h() -> set[str]:", container=out)


def test_unknown_iterables_prove_nothing() -> None:
    """Check that iterating an untyped value leaves the element unknown."""
    out: str = fixed(
        source="""\
def f(xs):
    return [x for x in xs]
""",
    )
    expect_not_in(item="def f(xs) ->", container=out)


def test_the_loop_variable_shadows_an_outer_name() -> None:
    """Check that the target hides a same-named outer constant."""
    out: str = fixed(
        source="""
        i = "s"

        def f():
            return [i for i in range(3)]
        """,
    )
    expect_in(item="def f() -> list[int]:", container=out)


def test_async_comprehensions_are_left_alone() -> None:
    """Check that ``async for`` comprehensions are never typed."""
    out: str = fixed(
        source="""
        async def f(src):
            return [i async for i in src]
        """,
    )
    expect_not_in(item="-> list", container=out)
