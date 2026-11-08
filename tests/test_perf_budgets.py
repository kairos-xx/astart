"""Performance budgets: structural counters first, generous clocks second."""

from __future__ import annotations

from os import environ
from pathlib import Path
from sys import modules
from time import perf_counter
from typing import TYPE_CHECKING, Final, final

import pytest
from astart import CommentedModule
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_true

if TYPE_CHECKING:
    from collections.abc import Callable

    from astart.rules.registry import Registries


@final
class Constants:
    """Constants for the test.

    Attributes:
        corpus: Directory of corpus modules timed by the budgets.
        max_index_rebuilds: Most hint-index rebuilds allowed per fix.
        small_seconds: Clock budget for a small module.
        large_seconds: Clock budget for the 1800-line module.

    """

    corpus: Final[Path] = Path(__file__).parent / "corpus"
    max_index_rebuilds: Final[int] = 20
    small_seconds: Final[float] = 3.0
    large_seconds: Final[float] = 15.0


def _instrumented() -> bool:
    """Check whether the interpreter is collecting coverage data.

    Wall-clock budgets are meaningless under coverage instrumentation,
    which slows execution several-fold; the structural counters still run.

    Returns:
        ``True`` when coverage tracing is active.

    """
    env: str | None = environ.get("COVERAGE_RUN")
    return "coverage" in modules or env == "true"


def _run(*, name: str) -> float:
    """Fix one corpus module and return the seconds it took.

    Args:
        name: Corpus module name, without the ``.py.txt`` suffix.

    Returns:
        Elapsed seconds of the ``fix_source`` call.

    """
    registries: Registries = default_registries()
    text: str = (Constants.corpus / f"{name}.py.txt").read_text(
        encoding="utf-8",
    )
    started: float = perf_counter()
    _ = fix_source(
        source=text,
        filename=f"{name}.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    return perf_counter() - started


@pytest.mark.parametrize("name", ["bisect", "heapq", "colorsys"])
def test_token_index_is_rebuilt_a_bounded_number_of_times(
    *,
    name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that rebuilds do not scale with the number of nodes asked.

    A per-node ``token_text`` read once rebuilt the index 238 times on a
    1 800-line module; the budget catches that whole class of mistake.

    Args:
        name: Corpus module.
        monkeypatch: Fixture wrapping the rebuild.

    """
    calls: list[int] = []
    original: Callable[[CommentedModule], object] = (
        CommentedModule.refresh_token_index
    )

    def counting(self: CommentedModule) -> object:
        """Count one token-index rebuild, then delegate.

        Args:
            self: Module whose token index is rebuilt.

        Returns:
            The real rebuild's result.

        """
        calls.append(1)
        return original(self)

    monkeypatch.setattr(
        target=CommentedModule,
        name="refresh_token_index",
        value=counting,
    )
    _ = _run(name=name)
    expect_true(
        condition=len(calls) <= Constants.max_index_rebuilds,
        message=str(object=len(calls)),
    )


def test_a_small_module_stays_fast() -> None:
    """Check a 120-line module against a generous clock."""
    if _instrumented():
        pytest.skip(reason="wall-clock budgets are meaningless under coverage")
    elapsed: float = _run(name="bisect")
    expect_true(
        condition=elapsed < Constants.small_seconds,
        message=f"{elapsed:.2f}s",
    )


@pytest.mark.slow
def test_an_1800_line_module_stays_in_budget() -> None:
    """Check the largest routine case against a generous clock."""
    if _instrumented():
        pytest.skip(reason="wall-clock budgets are meaningless under coverage")
    elapsed: float = _run(name="statistics")
    expect_true(
        condition=elapsed < Constants.large_seconds,
        message=f"{elapsed:.2f}s",
    )
