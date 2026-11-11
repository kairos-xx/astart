"""``tests.support`` helpers for rule authors."""

from __future__ import annotations

from textwrap import dedent

import pytest
from astart.rules import FixSettings
from astart.rules.vocabulary import FixSafety

from tests.support import assert_fixed, fixed
from tests.support.expectations import expect_in


def test_fixed_returns_guarded_output() -> None:
    """Check that ``fixed`` applies a guarded annotation."""
    out: str = fixed(
        source=dedent(
            text="""
            def size():
                return 3
            """,
        ),
    )
    expect_in(item="-> int", container=out)


def test_fixed_honours_settings() -> None:
    """Check that a caller-supplied ``FixSettings`` is used."""
    out: str = fixed(
        source="""\
def size():
    return 3
""",
        settings=FixSettings(ceiling=FixSafety.guarded, negotiate=False),
    )
    expect_in(item="-> int", container=out)


def test_assert_fixed_passes_on_present_fragment() -> None:
    """Check that ``assert_fixed`` accepts a matching fragment."""
    assert_fixed(
        source="""\
def size():
    return 3
""",
        expected="-> int",
    )


def test_assert_fixed_raises_on_missing_fragment() -> None:
    """Check that ``assert_fixed`` reports the fixed source."""
    with pytest.raises(expected_exception=AssertionError) as caught:
        assert_fixed(
            source="""\
def size():
    return 3
""",
            expected="def missing():",
        )
    expect_in(
        item="expected fragment not in fixed source",
        container=str(object=caught.value),
    )
    expect_in(item="-> int", container=str(object=caught.value))
