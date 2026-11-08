"""Fixed sources keep the input's CRLF line endings."""

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

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Run the fix pipeline on one source.

    Args:
        source: Python source text.

    Returns:
        The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_crlf_source_keeps_crlf_endings() -> None:
    r"""Check no bare ``\\n`` survives the rewrite."""
    out: str = _fixed(source="def f(x):\r\n    return 1\r\n")
    expect_true(condition="\r\n" in out)
    expect_equal(
        actual=out.count("\n"),
        expected=out.count("\r\n"),
    )
