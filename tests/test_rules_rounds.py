"""``FixResult`` reports how many rounds a run needed."""

from __future__ import annotations

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

if TYPE_CHECKING:
    from astart.rules.registry import Registries

from tests.expectations import expect_equal, expect_true


def _run(*, source: str) -> FixResult:
    """Run the guarded fixer on ``source``.

    Args:
        source: Module source to fix.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def test_a_clean_file_takes_one_round() -> None:
    """Check that a clean file takes one round."""
    result: FixResult = _run(source="def f(x: int) -> int:\n    return x\n")
    expect_equal(actual=result.rounds, expected=1)


def test_a_fixed_file_converges_within_the_budget() -> None:
    """Check that a fixed file converges within the budget."""
    result: FixResult = _run(
        source="""
        def f(x):
            return g(x)


        def g(y):
            return y


        f(1)
        """,
    )
    expect_true(condition=result.rounds in {2, 3})


def test_the_parse_error_path_reports_its_round() -> None:
    """Check that the parse error path reports its round."""
    result: FixResult = _run(source="def (:\n")
    expect_equal(actual=result.rounds, expected=1)
