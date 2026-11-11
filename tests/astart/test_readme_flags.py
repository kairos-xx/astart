"""Check ``astart`` flags are documented in the README and CLI guide."""

from __future__ import annotations

from re import findall
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.__main__ import main

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        ignored (Final[frozenset[str]]): Flags argparse provides itself,
            needing no docs.
        commands (Final[tuple[str, ...]]): Every CLI subcommand with a
            ``--help`` listing.
        non_cli_flags (Final[frozenset[str]]): ``--`` tokens in the README that
            are not astart
            flags (pytest options, Markdown anchors).

    """

    root: Final[Path] = Paths.root
    ignored: Final[frozenset[str]] = frozenset({"--help"})
    commands: Final[tuple[str, ...]] = (
        "check",
        "fix",
        "transform",
        "convert",
        "rules",
        "explain",
        "undo",
    )
    non_cli_flags: Final[frozenset[str]] = frozenset(
        {
            "--cov",
            "--cov-branch",
            "--cov-report",
            "--verify-declared-ast-mutations-before-committing-edits",
        },
    )


def test_fix_help_flags_appear_in_readme(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check each ``fix --help`` flag is mentioned in the README.

    Args:
        capsys (pytest.CaptureFixture[str]): pytest output capture.

    """
    with pytest.raises(expected_exception=SystemExit) as caught:
        _ = main(argv=["fix", "--help"])
    expect_true(condition=caught.value.code == 0)
    out: str = capsys.readouterr().out
    flags: set[str] = set(
        findall(pattern=r"--[a-zA-Z][a-zA-Z-]*", string=out),
    )
    flags -= Constants.ignored
    readme: str = (Constants.root / "README.md").read_text(encoding="utf-8")
    missing: list[str] = sorted(flag for flag in flags if flag not in readme)
    expect_equal(actual=missing, expected=[])


def _help_flags(capsys: pytest.CaptureFixture[str], command: str) -> set[str]:
    """Collect the long flags a subcommand's ``--help`` advertises.

    Args:
        capsys (pytest.CaptureFixture[str]): pytest output capture.
        command (str): Subcommand name.

    Returns:
        set[str]: The ``--flag`` tokens minus argparse's own ``--help``.

    """
    with pytest.raises(expected_exception=SystemExit) as caught:
        _ = main(argv=[command, "--help"])
    expect_true(condition=caught.value.code == 0)
    out: str = capsys.readouterr().out
    return set(findall(pattern=r"--[a-zA-Z][a-zA-Z-]*", string=out)) - (
        Constants.ignored
    )


def test_every_command_flag_is_in_cli_reference(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every ``--help`` flag appears in ``docs/guides/cli.md``.

    Args:
        capsys (pytest.CaptureFixture[str]): pytest output capture.

    """
    cli_md: str = (Constants.root / "docs" / "guides" / "cli.md").read_text(
        encoding="utf-8",
    )
    missing: list[str] = []
    for command in Constants.commands:
        missing.extend(
            f"{command}:{flag}"
            for flag in sorted(_help_flags(capsys=capsys, command=command))
            if flag not in cli_md
        )
    expect_equal(actual=missing, expected=[])


def test_readme_flags_appear_in_cli_reference() -> None:
    """Check README ``--flag`` tokens appear in ``docs/guides/cli.md``."""
    readme: str = (Constants.root / "README.md").read_text(encoding="utf-8")
    cli_md: str = (Constants.root / "docs" / "guides" / "cli.md").read_text(
        encoding="utf-8",
    )
    flags: set[str] = set(
        findall(pattern=r"--[a-zA-Z][a-zA-Z-]*", string=readme),
    )
    flags -= Constants.ignored | Constants.non_cli_flags
    missing: list[str] = sorted(flag for flag in flags if flag not in cli_md)
    expect_equal(actual=missing, expected=[])
