"""Public one-call API for checking and fixing Python source (API-02).

Library callers get the same default catalog, registries and safety
ceiling the CLI uses, built once per process and cached.

"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from astart.rules import (
    CheckOptions,
    CheckResult,
    FixResult,
    FixSettings,
    check,
    default_registries,
    load_default_catalog,
)
from astart.rules import (
    fix_source as _fix_source,
)
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from astart.rules import Catalog
    from astart.rules.registry import Registries

__all__: list[str] = ["check_source", "fix_source"]


@lru_cache(maxsize=1)
def _defaults() -> tuple[Registries, Catalog]:
    """Build the default registries and catalog once per process.

    Returns:
        tuple[Registries, Catalog]: ``(registries, catalog)`` shared by every
            call.

    """
    registries: Registries = default_registries()
    return registries, load_default_catalog(registries=registries)


def check_source(
    *,
    source: str,
    filename: str = "<memory>",
    options: CheckOptions | None = None,
) -> CheckResult:
    """Check source against the default rule catalog.

    Args:
        source (str): Python source text.
        filename (str): Name used in finding spans.
        options (CheckOptions | None): Optional fact providers and stub
            directory.

    Returns:
        CheckResult: Findings in source order, or the parse
            error when the source is invalid.

    """
    registries, catalog = _defaults()
    return check(
        source=source,
        filename=filename,
        catalog=catalog,
        registries=registries,
        options=options,
    )


def fix_source(
    *,
    source: str,
    filename: str = "<memory>",
    settings: FixSettings | None = None,
) -> FixResult:
    """Fix source with the default catalog and a ``guarded`` ceiling.

    Args:
        source (str): Python source text.
        filename (str): Name used in spans and cache keys.
        settings (FixSettings | None): Fix options; ``None`` selects
            ``FixSettings`` defaults
            with a ``guarded`` ceiling, matching ``astart fix``.

    Returns:
        FixResult: The fix outcome: final source, applied and
            skipped fixes, and remaining findings.

    """
    registries, catalog = _defaults()
    chosen: FixSettings = settings or FixSettings(ceiling=FixSafety.guarded)
    return _fix_source(
        source=source,
        filename=filename,
        catalog=catalog,
        registries=registries,
        settings=chosen,
    )
