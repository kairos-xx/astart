"""Public ``Settings``: ``from_pyproject`` and ``to_fix_settings`` (API-04)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

import pytest
from astart import Settings as RootSettings
from astart import __all__
from astart.cli.config import ConfigError
from astart.rules.vocabulary import FixSafety
from astart.settings import Settings

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules import FixSettings


@final
class Constants:
    """Group module-level constants.

    Attributes:
        pyproject (Final[str]): Minimal ``[tool.astart]`` table exercising
            every mapped key.

    """

    pyproject: Final[str] = """\
[tool.astart]
safety-ceiling = "proven"
min-confidence = 0.7
target-version = "3.11"
checker = "off"
protocol-placement = "function"
"""


def _write(*, tmp_path: Path, text: str, name: str = "pyproject.toml") -> Path:
    """Write a ``pyproject.toml`` fixture.

    Args:
        tmp_path (Path): pytest temporary directory.
        text (str): File contents.
        name (str): File name inside the directory.

    Returns:
        Path: The written path.

    """
    path: Path = tmp_path / name
    _: int = path.write_text(data=text, encoding="utf-8")
    return path


def test_settings_is_importable_from_package_root() -> None:
    """``from astart import Settings`` resolves and is listed."""
    expect_true(condition=RootSettings is Settings)
    expect_true(condition="Settings" in __all__)


def test_defaults_match_the_cli() -> None:
    """An empty ``Settings`` mirrors ``astart fix`` defaults."""
    settings: Settings = Settings()
    expect_equal(actual=settings.ceiling, expected=FixSafety.guarded)
    expect_equal(actual=settings.min_confidence, expected=0.8)
    expect_equal(actual=settings.target_version, expected=None)
    expect_equal(actual=settings.checker, expected=None)
    expect_equal(actual=settings.protocol_placement, expected="module")


def test_from_pyproject_maps_the_table(*, tmp_path: Path) -> None:
    """Every mapped ``[tool.astart]`` key reaches ``Settings``.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    path: Path = _write(tmp_path=tmp_path, text=Constants.pyproject)
    settings: Settings = Settings.from_pyproject(path=path)
    expect_equal(actual=settings.ceiling, expected=FixSafety.proven)
    expect_equal(actual=settings.min_confidence, expected=0.7)
    expect_equal(actual=settings.target_version, expected="3.11")
    expect_equal(actual=settings.checker, expected="off")
    expect_equal(actual=settings.protocol_placement, expected="function")


def test_from_pyproject_without_table_gives_defaults(
    *,
    tmp_path: Path,
) -> None:
    """A ``pyproject.toml`` without ``[tool.astart]`` is not an error.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    path: Path = _write(
        tmp_path=tmp_path,
        text="""\
[project]
name = 'x'
""",
    )
    expect_equal(
        actual=Settings.from_pyproject(path=path),
        expected=Settings(),
    )


def test_from_pyproject_rejects_malformed_table(*, tmp_path: Path) -> None:
    """Malformed config raises ``ConfigError``.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    path: Path = _write(
        tmp_path=tmp_path,
        text="""\
[tool.astart]
min-confidence = "high"
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        Settings.from_pyproject(path=path)


def test_to_fix_settings_converts(*, tmp_path: Path) -> None:
    """``to_fix_settings`` produces a working ``FixSettings``.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    path: Path = _write(tmp_path=tmp_path, text=Constants.pyproject)
    settings: Settings = Settings.from_pyproject(path=path)
    fix: FixSettings = settings.to_fix_settings()
    expect_equal(actual=fix.ceiling, expected=FixSafety.proven)
    expect_equal(actual=fix.min_confidence, expected=0.7)
    expect_equal(actual=fix.protocol_placement, expected="function")
    expect_equal(actual=fix.checker, expected=None)
    expect_true(condition=fix.target is not None)
