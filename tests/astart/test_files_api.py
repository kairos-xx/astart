"""File-level fix API: ``fix_file``/``fix_paths`` (API-03)."""

from __future__ import annotations

from threading import Event
from typing import TYPE_CHECKING, Final, final

from astart.files import FileOutcome, fix_file, fix_paths

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        untyped (Final[str]): Source that gains annotations under the guarded
            fixes.
        annotated (Final[str]): Source that is already fully annotated.

    """

    untyped: Final[str] = """\
def add(a, b):
    return a + b
"""
    annotated: Final[str] = """\
def add(a: int, b: int) -> int:
    return a + b
"""


def _write(*, directory: Path, name: str, text: str) -> Path:
    """Create one source file under ``directory``.

    Args:
        directory (Path): Parent directory.
        name (str): File name.
        text (str): File contents.

    Returns:
        Path: The file path.

    """
    path: Path = directory / name
    _: int = path.write_text(data=text, encoding="utf-8")
    return path


def test_fix_file_writes_result(tmp_path: Path) -> None:
    """``write=True`` replaces the file atomically.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.

    """
    path: Path = _write(
        directory=tmp_path,
        name="mod.py",
        text=Constants.untyped,
    )
    outcome: FileOutcome = fix_file(path=path)
    expect_equal(actual=outcome.error, expected=None)
    expect_true(condition=outcome.written)
    expect_true(condition=outcome.changed)
    expect_true(condition="->" in outcome.after)
    expect_equal(
        actual=path.read_text(encoding="utf-8"),
        expected=outcome.after,
    )


def test_fix_file_dry_run_leaves_disk_untouched(tmp_path: Path) -> None:
    """``write=False`` reports the outcome without writing.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.

    """
    path: Path = _write(
        directory=tmp_path,
        name="mod.py",
        text=Constants.untyped,
    )
    outcome: FileOutcome = fix_file(path=path, write=False)
    expect_equal(actual=outcome.error, expected=None)
    expect_true(condition=not outcome.written)
    expect_true(condition=outcome.changed)
    expect_equal(
        actual=path.read_text(encoding="utf-8"),
        expected=Constants.untyped,
    )


def test_fix_file_reports_errors_instead_of_raising(tmp_path: Path) -> None:
    """Missing and unparsable files surface in ``error``.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.

    """
    missing: FileOutcome = fix_file(path=tmp_path / "nope.py")
    expect_true(condition=missing.error is not None)
    expect_true(condition=not missing.written)

    broken: Path = _write(
        directory=tmp_path,
        name="broken.py",
        text="""\
def broken(:
""",
    )
    outcome: FileOutcome = fix_file(path=broken)
    expect_true(condition=outcome.error is not None)
    expect_equal(
        actual=broken.read_text(encoding="utf-8"),
        expected="""\
def broken(:
""",
    )


def test_fix_paths_preserves_input_order(tmp_path: Path) -> None:
    """One outcome per path, in order, failures included.

    Args:
        tmp_path (Path): Directory receiving the fixture source files.

    """
    first: Path = _write(
        directory=tmp_path,
        name="a.py",
        text=Constants.untyped,
    )
    second: Path = _write(
        directory=tmp_path,
        name="b.py",
        text=Constants.annotated,
    )
    third: Path = tmp_path / "missing.py"
    outcomes: tuple[FileOutcome, ...] = fix_paths(
        paths=(first, second, third),
        write=False,
    )
    expect_equal(actual=len(outcomes), expected=3)
    expect_equal(actual=outcomes[0].path, expected=first)
    expect_equal(actual=outcomes[1].path, expected=second)
    expect_equal(actual=outcomes[2].path, expected=third)
    expect_true(condition=outcomes[2].error is not None)
    expect_true(condition=outcomes[1].error is None)


def test_fix_file_respects_declared_encoding(tmp_path: Path) -> None:
    """A ``# -*- coding:`` file round-trips in its own encoding.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.

    """
    path: Path = tmp_path / "latin.py"
    text: str = """\
# -*- coding: latin-1 -*-
def f(x):
    return 'caf\xe9'
"""
    _ = path.write_bytes(data=text.encode(encoding="latin-1"))
    outcome: FileOutcome = fix_file(path=path, write=False)
    expect_equal(actual=outcome.error, expected=None)
    expect_equal(
        actual=outcome.before.splitlines()[0],
        expected="# -*- coding: latin-1 -*-",
    )


def test_fix_paths_calls_on_file_once_per_file(tmp_path: Path) -> None:
    """The callback fires once per processed file, in order.

    Args:
        tmp_path (Path): Directory receiving the fixture source files.

    """
    paths: tuple[Path, ...] = tuple(
        _write(
            directory=tmp_path,
            name=f"mod_{index}.py",
            text=Constants.untyped,
        )
        for index in range(3)
    )
    seen: list[tuple[Path, FileOutcome]] = []
    outcomes: tuple[FileOutcome, ...] = fix_paths(
        paths=paths,
        write=False,
        on_file=lambda path, outcome: seen.append((path, outcome)),
    )
    expect_equal(actual=len(seen), expected=3)
    expect_equal(actual=len(outcomes), expected=3)
    for index, (path, outcome) in enumerate(iterable=seen):
        expect_equal(actual=path, expected=paths[index])
        expect_true(condition=outcome is outcomes[index])


def test_fix_paths_cancel_stops_between_files(tmp_path: Path) -> None:
    """A set cancel event ends the run before the next file.

    Args:
        tmp_path (Path): Directory receiving the fixture source files.

    """
    paths: tuple[Path, ...] = tuple(
        _write(
            directory=tmp_path,
            name=f"mod_{index}.py",
            text=Constants.untyped,
        )
        for index in range(4)
    )
    cancel: Event = Event()
    seen: list[Path] = []

    def _stop_after_first(path: Path, _outcome: FileOutcome) -> None:
        """Record the path and trip the cancel event.

        Args:
            path (Path): File about to be processed.
            _outcome (FileOutcome): Outcome of the previous file; unused.

        """
        seen.append(path)
        cancel.set()

    outcomes: tuple[FileOutcome, ...] = fix_paths(
        paths=paths,
        write=False,
        on_file=_stop_after_first,
        cancel=cancel,
    )
    expect_equal(actual=len(outcomes), expected=1)
    expect_equal(actual=seen, expected=[paths[0]])
