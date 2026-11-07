"""Verify the one-shot ruff formatting phase."""

from __future__ import annotations

from asyncio import run
from typing import TYPE_CHECKING

from astart.rules import default_registries, load_default_catalog
from astart.rules.formatter import (
    FormatOutcome,
    FormatTarget,
    fix_and_format,
    format_source,
)
from astart.rules.runner import FixSettings
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path
MESSY = """\
x=1
def f( a ):return a
"""
SAMPLE = """\
# header
LIMIT = 3  # limit


def scale(x, k):  # scale
    print(x * k)


scale(2, 3)  # call
"""


def test_format_source_runs_ruff_once(*, tmp_path: Path) -> None:
    """Normalise spacing through ruff.

    Args:
        tmp_path: Directory used for ruff's configuration lookup.

    """
    outcome: FormatOutcome = format_source(
        source=MESSY,
        target=FormatTarget(filename="m.py", cwd=tmp_path),
    )
    expect_true(condition=outcome.formatted)
    expect_equal(
        actual=outcome.source,
        expected="""\
x = 1


def f(a):
    return a
""",
    )


def test_missing_ruff_is_reported_not_fatal(*, tmp_path: Path) -> None:
    """Keep the source and explain why nothing happened.

    Args:
        tmp_path: Working directory.

    """
    outcome = format_source(
        source=MESSY,
        target=FormatTarget(filename="m.py", cwd=tmp_path),
        command=("definitely-not-a-formatter",),
    )
    expect_false(condition=outcome.formatted)
    expect_equal(actual=outcome.source, expected=MESSY)
    expect_in(item="not found", container=outcome.note)


def test_ruff_error_keeps_original_source(*, tmp_path: Path) -> None:
    """Never replace the source with ruff's error output.

    Args:
        tmp_path: Working directory.

    """
    outcome = format_source(
        source="""\
def (:
""",
        target=FormatTarget(filename="m.py", cwd=tmp_path),
    )
    expect_false(condition=outcome.formatted)
    expect_equal(
        actual=outcome.source,
        expected="""\
def (:
""",
    )
    expect_true(condition=outcome.note != "")


def test_fix_and_format_output_is_stable(*, tmp_path: Path) -> None:
    """Make ruff a no-op on astart's output and converge on rerun.

    Args:
        tmp_path: Working directory.

    """
    registries = default_registries()
    catalog = load_default_catalog(registries=registries)
    settings = FixSettings(ceiling=FixSafety.guarded)
    target = FormatTarget(filename="s.py", cwd=tmp_path)
    fixed, formatted = fix_and_format(
        source=SAMPLE,
        target=target,
        catalog=catalog,
        registries=registries,
        settings=settings,
    )
    expect_true(condition=len(fixed.applied) > 0)
    expect_true(condition=formatted.formatted)
    again = format_source(
        source=formatted.source,
        target=target,
    )
    expect_equal(actual=again.source, expected=formatted.source)
    second_fixed, second_formatted = fix_and_format(
        source=formatted.source,
        target=target,
        catalog=catalog,
        registries=registries,
        settings=settings,
    )
    expect_equal(actual=second_fixed.applied, expected=())
    expect_equal(actual=second_formatted.source, expected=formatted.source)


def test_format_source_works_inside_a_running_event_loop(
    *,
    tmp_path: Path,
) -> None:
    """Format from async code without nesting event loops.

    Args:
        tmp_path: Directory used for ruff's configuration lookup.

    """

    async def caller() -> FormatOutcome:
        return format_source(
            source=MESSY,
            target=FormatTarget(filename="m.py", cwd=tmp_path),
        )

    expect_true(condition=(run(main=caller())).formatted)
