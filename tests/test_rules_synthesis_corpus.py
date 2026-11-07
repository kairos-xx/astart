"""Run every synthesizing fix over real modules."""

from __future__ import annotations

from dataclasses import replace
from io import StringIO
from pathlib import Path
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart.rules import Catalog


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_files: Vendored modules to fix.
        stable_check_lines: Longest file whose rerun is checked.

    """

    corpus_files: Final[tuple[Path, ...]] = tuple(
        sorted((Path(__file__).parent / "corpus").glob(pattern="*.py.txt")),
    )
    stable_check_lines: Final[int] = 700


def _catalog() -> Catalog:
    """Restrict the default catalog to the typing rule and all its fixes.

    Returns:
        The catalog with TYP003 only.

    """
    catalog = load_default_catalog(registries=default_registries())
    return replace(
        catalog,
        rules=tuple(r for r in catalog.rules if r.code == "TYP003"),
    )


def _comments(*, text: str) -> list[str]:
    """List the comment texts of a source.

    Args:
        text: Python source.

    Returns:
        Comments in order.

    """
    return [
        token.string
        for token in generate_tokens(StringIO(initial_value=text).readline)
        if token.type == COMMENT
    ]


def _fix(*, source: str, name: str) -> FixResult:
    """Fix a source with every typing fix.

    Args:
        source: Python source.
        name: File name.

    Returns:
        The fix result.

    """
    return fix_source(
        source=source,
        filename=name,
        catalog=_catalog(),
        registries=default_registries(),
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


@pytest.mark.parametrize(
    "path",
    Constants.corpus_files,
    ids=[path.name for path in Constants.corpus_files],
)
def test_synthesis_compiles_keeps_comments_and_is_stable(
    *,
    path: Path,
) -> None:
    """Compile the fixed module, keep its comments and reach a fixed point.

    Args:
        path: Vendored module under test.

    """
    source = path.read_text(encoding="utf-8")
    result = _fix(source=source, name=path.name)
    expect_equal(actual=result.parse_error, expected=None)
    _ = compile(result.source, path.name, "exec")
    expect_equal(
        actual=_comments(text=result.source),
        expected=_comments(text=source),
    )
    if source.count("\n") <= Constants.stable_check_lines:
        again = _fix(source=result.source, name=path.name)
        expect_true(condition=again.source == result.source)
