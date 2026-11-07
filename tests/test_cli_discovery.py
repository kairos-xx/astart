"""Verify file discovery for the command line."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.cli.discovery import DiscoveryResult, discover_files

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from pathlib import Path


def _touch(*, root: Path, name: str) -> Path:
    """Write a minimal Python file under a root.

    Args:
        root: Directory the file is created under.
        name: Relative path of the file.

    Returns:
        The written file's path.

    """
    path: Path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        data="""\
x = 1
""",
        encoding="utf-8",
    )
    return path


def test_directory_walk_finds_python_files_sorted(*, tmp_path: Path) -> None:
    """Check that directory walk finds python files sorted.

    Args:
        tmp_path: Directory to walk for files.

    """
    second: Path = _touch(root=tmp_path, name="b.py")
    first: Path = _touch(root=tmp_path, name="a.py")
    nested: Path = _touch(root=tmp_path, name="pkg/c.py")
    _ = _touch(root=tmp_path, name="notes.txt")
    result: DiscoveryResult = discover_files(paths=[tmp_path])
    expect_equal(actual=result.files, expected=(first, second, nested))


def test_skips_virtualenv_and_cache_directories(*, tmp_path: Path) -> None:
    """Check that skips virtualenv and cache directories.

    Args:
        tmp_path: Directory to walk for files.

    """
    kept: Path = _touch(root=tmp_path, name="app.py")
    skipped: list[Path] = [
        _touch(root=tmp_path, name=".venv/x.py"),
        _touch(root=tmp_path, name="__pycache__/y.py"),
        _touch(root=tmp_path, name="node_modules/z.py"),
    ]
    result: DiscoveryResult = discover_files(paths=[tmp_path])
    expect_in(item=kept, container=result.files)
    for path in skipped:
        expect_not_in(item=path, container=result.files)


def test_explicit_file_honoured_even_in_skipped_dir(*, tmp_path: Path) -> None:
    """Check that explicit file honoured even in skipped dir.

    Args:
        tmp_path: Directory to walk for files.

    """
    explicit: Path = _touch(root=tmp_path, name=".venv/x.py")
    result: DiscoveryResult = discover_files(paths=[explicit])
    expect_equal(actual=result.files, expected=(explicit,))


def test_missing_path_reported_not_raised(*, tmp_path: Path) -> None:
    """Check that missing path reported not raised.

    Args:
        tmp_path: Directory to walk for files.

    """
    missing: Path = tmp_path / "nope.py"
    result: DiscoveryResult = discover_files(paths=[missing])
    expect_equal(actual=result.missing, expected=(missing,))
    expect_equal(actual=result.files, expected=())


def test_duplicate_arguments_collapse(*, tmp_path: Path) -> None:
    """Check that duplicate arguments collapse.

    Args:
        tmp_path: Directory to walk for files.

    """
    only: Path = _touch(root=tmp_path, name="a.py")
    result: DiscoveryResult = discover_files(paths=[only, tmp_path, only])
    expect_equal(actual=result.files, expected=(only,))
