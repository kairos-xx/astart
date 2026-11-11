"""Non-literal defaults (``-1``, ``LIMIT``) corroborate a parameter's type."""

from __future__ import annotations

from tests.support import fixed
from tests.support.expectations import expect_in, expect_not_in


def test_negative_literal_default_types_the_parameter() -> None:
    """Check that ``x=-1`` with an int-only use yields ``int``."""
    out: str = fixed(
        source="""
        def clamp(x=-1):
            return x + 1
        """,
    )
    expect_in(item="x: int = -1", container=out)


def test_constant_default_types_the_parameter() -> None:
    """Check that a default naming an int constant yields ``int``."""
    out: str = fixed(
        source="""
        LIMIT = 10

        def cap(n=LIMIT):
            return n * 2
        """,
    )
    expect_in(item="n: int = LIMIT", container=out)


def test_a_rebound_constant_does_not_type_the_default() -> None:
    """Check that a name bound twice proves nothing about the default."""
    out: str = fixed(
        source="""
        LIMIT = 10
        LIMIT = "ten"

        def cap(n=LIMIT):
            return n
        """,
    )
    expect_not_in(item="n: int", container=out)
    expect_not_in(item="n: str", container=out)
