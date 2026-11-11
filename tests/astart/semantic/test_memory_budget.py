"""Peak-memory budgets for ``fix_source`` on large modules (M7-06)."""

from __future__ import annotations

from tracemalloc import get_traced_memory, start, stop
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_true

if TYPE_CHECKING:
    from astart.rules import Catalog, FixResult
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        functions_small (Final[int]): Function count of the baseline module.
        functions_large (Final[int]): Function count of the scaling module.
        budget_bytes (Final[int]): Absolute peak budget for the baseline
            module.
        scale_factor (Final[float]): Allowed peak ratio between the two sizes.
        function_lines (Final[int]): Lines emitted per generated function.

    """

    functions_small: Final[int] = 2000
    functions_large: Final[int] = 4000
    budget_bytes: Final[int] = 400 * 1024 * 1024
    scale_factor: Final[float] = 2.5
    function_lines: Final[int] = 12


def _big_module(*, functions: int) -> str:
    """Build a module of ``functions`` repeated untyped functions.

    Args:
        functions (int): Number of functions to emit.

    Returns:
        str: Source text of roughly ``functions * 12`` lines.

    """
    block: str = """\
def f{i}(a, b=1):
    x = a + b
    y = x * 2
    z = y - a
    if z > 0:
        w = z + b
    else:
        w = b - z
    return w
"""
    return "".join(block.format(i=index) for index in range(functions))


def _peak_bytes(*, source: str) -> int:
    """Measure the tracemalloc peak of one ``fix_source`` call.

    Args:
        source (str): Module source to fix.

    Returns:
        int: Peak traced memory in bytes.

    """
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    start()
    try:
        result: FixResult = fix_source(
            source=source,
            filename="big.py",
            catalog=catalog,
            registries=registries,
            settings=FixSettings(ceiling=FixSafety.guarded),
        )
        expect_true(condition=result.parse_error is None)
        _, peak = get_traced_memory()
    finally:
        stop()
    return peak


@pytest.mark.slow
def test_fix_source_peak_memory_budget() -> None:
    """2000 functions (~24k lines) stay under the absolute budget.

    Measured peak on 2026-11-09: see TODO M7-06 evidence.

    """
    source: str = _big_module(functions=Constants.functions_small)
    peak: int = _peak_bytes(source=source)
    expect_true(
        condition=peak < Constants.budget_bytes,
        message=f"peak {peak / 1024 / 1024:.1f} MiB exceeds "
        f"{Constants.budget_bytes / 1024 / 1024:.0f} MiB budget",
    )


@pytest.mark.slow
def test_fix_source_memory_scales_linearly() -> None:
    """Peak for 4000 functions stays under 2.5x the 2000-function peak."""
    small: str = _big_module(functions=Constants.functions_small)
    large: str = _big_module(functions=Constants.functions_large)
    peak_small: int = _peak_bytes(source=small)
    peak_large: int = _peak_bytes(source=large)
    expect_true(
        condition=peak_large < Constants.scale_factor * peak_small,
        message=f"peak grew {peak_large / peak_small:.2f}x for 2x input "
        f"(limit {Constants.scale_factor}x)",
    )
