"""M1-14: full-run idempotence beyond the small-file test.

The check covers the corpus modules the small-file test skips, plus a pass
through the real ``main`` CLI entry.

``test_cli_idempotence_corpus`` covers modules up to 700 lines via
``fix_and_format``; this file extends the same check to every larger
module and drives a representative subset through ``astart.__main__.main``
so argument parsing, file IO and the format pipeline are exercised too.

"""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.__main__ import main
from astart.rules import (
    FixSettings,
    FormatTarget,
    default_registries,
    fix_and_format,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus (Final[Path]): Directory of corpus ``.py`` modules.
        small_file_lines (Final[int]): Modules at or below this size are
            covered
            by ``test_cli_idempotence_corpus`` already.
        cli_modules (Final[tuple[str, ...]]): Corpus modules driven through the
            real CLI entry.

    """

    corpus: Final[Path] = Paths.tests / "corpus" / "base"
    small_file_lines: Final[int] = 700
    cli_modules: Final[tuple[str, ...]] = (
        "os.py",
        "statistics.py",
        "zipfile___init__.py",
    )


_MODULES: Final[tuple[Path, ...]] = tuple(
    sorted(Constants.corpus.glob(pattern="*.py")),
)
_LARGE: Final[tuple[Path, ...]] = tuple(
    path
    for path in _MODULES
    if path.read_text(encoding="utf-8").count("\n")
    > Constants.small_file_lines
)


def _format_once(*, text: str, name: str) -> str:
    """Run one fix-and-format pass over ``text``.

    Args:
        text (str): Source text to process.
        name (str): File name reported to the formatter.

    Returns:
        str: The formatted source.

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
    _LARGE,
    ids=lambda p: p.name,
)
def test_large_module_second_run_changes_nothing(*, path: Path) -> None:
    """A second fix-and-format pass is byte-identical on large modules.

    Args:
        path (Path): Corpus file larger than the small-file test's bound.

    """
    first: str = _format_once(
        text=path.read_text(encoding="utf-8"),
        name=path.name,
    )
    second: str = _format_once(text=first, name=path.name)
    expect_equal(actual=second, expected=first)


def test_cli_fix_twice_is_byte_identical(*, tmp_path: Path) -> None:
    """``astart fix`` through ``main`` reaches a fixed point on disk.

    Args:
        tmp_path (Path): Directory receiving the corpus copies.

    """
    targets: list[Path] = []
    for name in Constants.cli_modules:
        target: Path = tmp_path / name.removesuffix(".py")
        copyfile(src=Constants.corpus / name, dst=target)
        targets.append(target)
    argv: list[str] = [
        "fix",
        "--checker",
        "off",
        *(str(object=path) for path in targets),
    ]
    # ``astart fix`` exits 1 when it changed files, 0 at a fixed point.
    expect_equal(actual=main(argv=argv), expected=1)
    after_first: dict[Path, bytes] = {
        path: path.read_bytes() for path in targets
    }
    expect_equal(actual=main(argv=argv), expected=0)
    for path in targets:
        expect_equal(actual=path.read_bytes(), expected=after_first[path])
