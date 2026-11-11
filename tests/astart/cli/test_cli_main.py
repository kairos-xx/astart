"""Verify command-line wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

import pytest
from astart.__main__ import main

from tests.support.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        sample (Final[str]): Grouped module constant.

    """

    sample: Final[str] = """\
LIMIT = 3


def scale(x, k=2):
    print(x * k)


scale(2, 3)
"""


def _sample(*, tmp_path: Path) -> Path:
    """Write the sample module into a temporary directory.

    Args:
        tmp_path (Path): Directory holding the sample file.

    Returns:
        Path: The written file's path.

    """
    path: Path = tmp_path / "m.py"
    path.write_text(data=Constants.sample, encoding="utf-8")
    return path


def test_check_subcommand_exit_codes(*, tmp_path: Path) -> None:
    """Check that check subcommand exit codes.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _sample(tmp_path=tmp_path)
    expect_equal(actual=main(argv=["check", str(object=path)]), expected=1)
    expect_equal(
        actual=main(argv=["check", str(object=tmp_path / "gone.py")]),
        expected=2,
    )


def test_fix_defaults_to_automatic_keywords_and_hints(
    *,
    tmp_path: Path,
) -> None:
    """Check that fix defaults to automatic keywords and hints.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _sample(tmp_path=tmp_path)
    _ = main(argv=["fix", "--no-format", "--checker", "off", str(object=path)])
    text: str = path.read_text(encoding="utf-8")
    expect_in(item="scale(x=2, k=3)", container=text)
    expect_in(item="k: int = 2", container=text)
    expect_in(item="LIMIT: Final[int] = 3", container=text)


def test_safe_only_limits_fixes_to_proven(*, tmp_path: Path) -> None:
    """Check that safe only limits fixes to proven.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _sample(tmp_path=tmp_path)
    _ = main(
        argv=[
            "fix",
            "--safe-only",
            "--no-format",
            "--checker",
            "off",
            str(object=path),
        ],
    )
    text: str = path.read_text(encoding="utf-8")
    expect_in(item="scale(2, 3)", container=text)
    expect_in(item="LIMIT: Final[int] = 3", container=text)


def test_diff_and_check_are_mutually_exclusive(*, tmp_path: Path) -> None:
    """Check that diff and check are mutually exclusive.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _sample(tmp_path=tmp_path)
    with pytest.raises(expected_exception=SystemExit) as raised:
        _ = main(argv=["fix", "--diff", "--check", str(object=path)])
    expect_equal(actual=raised.value.code, expected=2)


def test_no_command_prints_help_exit_zero() -> None:
    """Check that no command prints help exit zero."""
    expect_equal(actual=main(argv=[]), expected=0)


def test_checker_flag_is_accepted_and_keeps_good_fixes(
    *,
    tmp_path: Path,
) -> None:
    """Check that checker flag is accepted and keeps good fixes.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _sample(tmp_path=tmp_path)
    _ = main(
        argv=["fix", "--no-format", "--checker", "auto", str(object=path)],
    )
    expect_in(item="k: int = 2", container=path.read_text(encoding="utf-8"))


def test_create_constants_class_flag_groups_final_constants(
    *,
    tmp_path: Path,
) -> None:
    """Check that create constants class flag groups final constants.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = tmp_path / "c.py"
    path.write_text(
        data="""\
LIMIT = 3


def f():
    return LIMIT
""",
        encoding="utf-8",
    )
    _ = main(
        argv=[
            "fix",
            "--no-format",
            "--checker",
            "off",
            "--create-constants-class",
            str(object=path),
        ],
    )
    text: str = path.read_text(encoding="utf-8")
    expect_in(item="class Constants", container=text)
    expect_in(item="return Constants.LIMIT", container=text)
