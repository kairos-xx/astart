"""Verify ``fix --backup`` and ``astart undo``."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Final, final

from astart.cli.commands import (
    FixCommandSettings,
    FixMode,
    run_fix,
    run_undo,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


@final
class Constants:
    """Group module-level constants.

    Attributes:
        sample (Final[str]): Source the fixer rewrites.
        backup_root (Final[str]): Name of the backup directory under the cwd.

    """

    sample: Final[str] = """\
# header
LIMIT = 3  # limit


def scale(x, k=2):  # scale
    print(x * k)


scale(2, 3)  # call
"""
    backup_root: Final[str] = ".astart-backup"


def _fix(*, paths: list[Path], backup: bool) -> tuple[int, str]:
    """Run the fix command while capturing its output.

    Args:
        paths (list[Path]): Files or directories to fix.
        backup (bool): Whether to save before-images.

    Returns:
        tuple[int, str]: The exit code and the captured output.

    """
    out: StringIO = StringIO()
    code: int = run_fix(
        settings=FixCommandSettings(
            paths=tuple(paths),
            ceiling=FixSafety.guarded,
            stubs_path=None,
            mode=FixMode.write,
            run_formatter=False,
            backup=backup,
        ),
        out=out,
    )
    return code, out.getvalue()


def _undo(*, run_id: str | None = None) -> tuple[int, str, str]:
    """Run the undo command while capturing its streams.

    Args:
        run_id (str | None): Run id to restore, or ``None`` for the newest.

    Returns:
        tuple[int, str, str]: The exit code and the captured stdout and stderr.

    """
    out: StringIO = StringIO()
    err: StringIO = StringIO()
    code: int = run_undo(run_id=run_id, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def _sample(*, tmp_path: Path) -> Path:
    """Write the sample file and return its path.

    Args:
        tmp_path (Path): Directory holding the sample file.

    Returns:
        Path: The written file's path.

    """
    path: Path = tmp_path / "sample.py"
    path.write_text(data=Constants.sample, encoding="utf-8")
    return path


def test_backup_then_undo_restores_original(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``fix --backup`` then ``undo`` returns the file to its original text.

    Args:
        tmp_path (Path): Working directory for the run.
        monkeypatch (pytest.MonkeyPatch): Fixture changing the working
            directory.

    """
    monkeypatch.chdir(path=tmp_path)
    path: Path = _sample(tmp_path=tmp_path)
    original: str = path.read_text(encoding="utf-8")
    code, _out = _fix(paths=[path], backup=True)
    expect_equal(actual=code, expected=1)
    expect_true(condition=path.read_text(encoding="utf-8") != original)
    runs: list[Path] = list((tmp_path / Constants.backup_root).iterdir())
    expect_equal(actual=len(runs), expected=1)
    undo_code, undo_out, undo_err = _undo()
    expect_equal(actual=undo_code, expected=0)
    expect_equal(actual=undo_err, expected="")
    expect_in(item="restored:", container=undo_out)
    expect_equal(
        actual=path.read_text(encoding="utf-8"),
        expected=original,
    )


def test_undo_skips_file_edited_since(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file edited after the fix is left untouched and reported.

    Args:
        tmp_path (Path): Working directory for the run.
        monkeypatch (pytest.MonkeyPatch): Fixture changing the working
            directory.

    """
    monkeypatch.chdir(path=tmp_path)
    path: Path = _sample(tmp_path=tmp_path)
    _code, _out = _fix(paths=[path], backup=True)
    edited: str = (
        path.read_text(encoding="utf-8")
        + """\

# manual edit
"""
    )
    path.write_text(data=edited, encoding="utf-8")
    undo_code, undo_out, _err = _undo()
    expect_equal(actual=undo_code, expected=1)
    expect_in(item="skipped (edited since):", container=undo_out)
    expect_equal(
        actual=path.read_text(encoding="utf-8"),
        expected=edited,
    )


def test_undo_without_backup_run_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``undo`` with no ``.astart-backup`` exits with the usage error.

    Args:
        tmp_path (Path): Working directory for the run.
        monkeypatch (pytest.MonkeyPatch): Fixture changing the working
            directory.

    """
    monkeypatch.chdir(path=tmp_path)
    code, _out, err = _undo()
    expect_equal(actual=code, expected=2)
    expect_in(item="no backup run found", container=err)


def test_fix_without_backup_creates_no_run(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain ``fix`` leaves no ``.astart-backup`` directory behind.

    Args:
        tmp_path (Path): Working directory for the run.
        monkeypatch (pytest.MonkeyPatch): Fixture changing the working
            directory.

    """
    monkeypatch.chdir(path=tmp_path)
    path: Path = _sample(tmp_path=tmp_path)
    code, _out = _fix(paths=[path], backup=False)
    expect_equal(actual=code, expected=1)
    expect_true(
        condition=not (tmp_path / Constants.backup_root).exists(),
    )
