"""Every ``astart fix`` flag is documented in ``README.md``."""

from __future__ import annotations

from pathlib import Path
from re import findall
from typing import Final, final

import pytest
from astart.__main__ import main

from tests.expectations import expect_equal, expect_true


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root: Repository root directory.
        ignored: Flags argparse provides itself, needing no docs.

    """

    root: Final[Path] = Path(__file__).parent.parent
    ignored: Final[frozenset[str]] = frozenset({"--help"})


def test_fix_help_flags_appear_in_readme(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check each ``fix --help`` flag is mentioned in the README.

    Args:
        capsys: pytest output capture.

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
