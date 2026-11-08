"""``astart fix --cache`` skips files whose inputs have not changed."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart.__main__ import main
from astart.cli import commands

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest
    from astart.rules import FixResult, FixSettings, FormatTarget
    from astart.rules.formatter import FormatOutcome
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Constants used in the test_cli_cache module.

    Attributes:
        source: Tiny module fixed repeatedly to exercise the cache.

    """

    source: Final[str] = "def run(a, b):\n    return a\n\n\nrun(1, 2)\n"


def _count_fixes(*, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Count real fixing work by wrapping the formatter-aware entry point.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        List collecting the filename of every file actually fixed.

    """
    calls: list[str] = []
    original: Callable[..., tuple[FixResult, FormatOutcome]] = (
        commands.fix_and_format
    )

    def counting(
        *,
        source: str,
        target: FormatTarget,
        catalog: Catalog,
        registries: Registries,
        settings: FixSettings,
    ) -> tuple[FixResult, FormatOutcome]:
        """Record the filename, then delegate to the real fixer.

        Args:
            source: Source text handed to the fixer.
            target: Format target describing the file.
            catalog: Rule catalog.
            registries: Rule registries.
            settings: Fix settings.

        Returns:
            The real fixer's result.

        """
        calls.append(target.filename)
        return original(
            source=source,
            target=target,
            catalog=catalog,
            registries=registries,
            settings=settings,
        )

    monkeypatch.setattr(target=commands, name="fix_and_format", value=counting)
    return calls


def _run(*, target: Path, extra: tuple[str, ...] = ()) -> int:
    """Invoke ``astart fix --check`` on one file.

    Args:
        target: File to check.
        extra: Additional CLI flags.

    Returns:
        The process exit code.

    """
    return main(
        argv=[
            "fix",
            "--check",
            "--checker",
            "off",
            *extra,
            str(object=target),
        ],
    )


def test_an_unchanged_file_is_not_fixed_twice(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that the second run is served from the cache.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    monkeypatch.chdir(path=tmp_path)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    calls: list[str] = _count_fixes(monkeypatch=monkeypatch)
    first: int = _run(target=target, extra=("--cache",))
    second: int = _run(target=target, extra=("--cache",))
    expect_equal(actual=first, expected=second)
    expect_equal(actual=len(calls), expected=1)


def test_a_changed_file_is_fixed_again(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that new content misses the cache.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    monkeypatch.chdir(path=tmp_path)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    calls: list[str] = _count_fixes(monkeypatch=monkeypatch)
    _ = _run(target=target, extra=("--cache",))
    _ = target.write_text(
        data=Constants.source + "\nx = 1\n",
        encoding="utf-8",
    )
    _ = _run(target=target, extra=("--cache",))
    expect_equal(actual=len(calls), expected=2)


def test_other_settings_miss_the_cache(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that ``--safe-only`` does not reuse a guarded result.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    monkeypatch.chdir(path=tmp_path)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    calls: list[str] = _count_fixes(monkeypatch=monkeypatch)
    _ = _run(target=target, extra=("--cache",))
    _ = _run(target=target, extra=("--cache", "--safe-only"))
    expect_equal(actual=len(calls), expected=2)


def test_without_the_flag_nothing_is_cached(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that the cache is opt-in.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    monkeypatch.chdir(path=tmp_path)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    calls: list[str] = _count_fixes(monkeypatch=monkeypatch)
    _ = _run(target=target)
    _ = _run(target=target)
    expect_equal(actual=len(calls), expected=2)
    expect_true(condition=not (tmp_path / ".astart_cache").exists())


def test_a_corrupt_entry_is_recomputed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that garbage on disk never breaks a run.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    monkeypatch.chdir(path=tmp_path)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    calls: list[str] = _count_fixes(monkeypatch=monkeypatch)
    _ = _run(target=target, extra=("--cache",))
    for entry in (tmp_path / ".astart_cache").glob(pattern="*.json"):
        _ = entry.write_text(data="{not json", encoding="utf-8")
    _ = _run(target=target, extra=("--cache",))
    expect_equal(actual=len(calls), expected=2)
