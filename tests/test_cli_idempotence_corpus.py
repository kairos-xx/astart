"""A full fix-and-format run must reach a fixed point on real modules."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    FormatTarget,
    default_registries,
    fix_and_format,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_files: Vendored modules to fix.
        max_lines: Longest module whose second run is checked.

    """

    corpus_files: Final[tuple[Path, ...]] = tuple(
        sorted((Path(__file__).parent / "corpus").glob(pattern="*.py.txt")),
    )
    max_lines: Final[int] = 700


def _run(*, text: str, name: str) -> str:
    """Run one fix-and-format pass over ``text``.

    Args:
        text: Source text to process.
        name: File name reported to the formatter.

    Returns:
        The formatted source.

    """
    registries: Registries = default_registries()
    _fixed, formatted = fix_and_format(
        source=text,
        target=FormatTarget(filename=name, cwd=Path.cwd()),
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    return formatted.source


@pytest.mark.parametrize(
    "path",
    [
        path
        for path in Constants.corpus_files
        if path.read_text(encoding="utf-8").count("\n") <= Constants.max_lines
    ],
    ids=lambda path: path.name,
)
def test_second_full_run_changes_nothing(*, path: Path) -> None:
    """Check that second full run changes nothing.

    Args:
        path: Corpus file to fix twice.

    """
    first: str = _run(text=path.read_text(encoding="utf-8"), name=path.name)
    second: str = _run(text=first, name=path.name)
    expect_equal(actual=second, expected=first)
