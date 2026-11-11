"""Helpers for rule authors writing gold-case tests.

``fixed`` runs the guarded fix pipeline on one source string and returns
the rewritten module; ``assert_fixed`` asserts that an expected fragment
appears in that output. Both dedent their inputs, so tests can indent
fixtures naturally.

"""

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


def _run(*, source: str, settings: FixSettings) -> FixResult:
    """Run the fix pipeline on one dedented source.

    Args:
        source (str): Module source to fix.
        settings (FixSettings): Fix run options.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=settings,
    )


def fixed(
    *,
    source: str,
    settings: FixSettings | None = None,
) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source (str): Module source to fix; dedented before the run.
        settings (FixSettings | None): Fix run options; defaults to the guarded
            ceiling.

    Returns:
        str: Fixed source text.

    """
    return _run(
        source=source,
        settings=(
            settings
            if settings is not None
            else FixSettings(ceiling=FixSafety.guarded)
        ),
    ).source


def assert_fixed(
    *,
    source: str,
    expected: str,
    settings: FixSettings | None = None,
) -> None:
    """Assert ``expected`` appears in the fixed ``source``.

    Args:
        source (str): Module source to fix; dedented before the run.
        expected (str): Dedented fragment that must appear in the output.
        settings (FixSettings | None): Fix run options; defaults to the guarded
            ceiling.

    Raises:
        AssertionError: When the fragment is absent; the message shows
            the fixed source.

    """
    out: str = fixed(source=source, settings=settings)
    want: str = dedent(text=expected)
    if want not in out:
        msg: str = (
            f"expected fragment not in fixed source:\n{want}\n---\n{out}"
        )
        raise AssertionError(msg)
