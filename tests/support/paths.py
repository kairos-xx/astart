"""Shared locations independent of mirrored test-module depth."""

from __future__ import annotations

from pathlib import Path
from typing import Final, final


@final
class Paths:
    """Canonical test and repository directories.

    Attributes:
        root (Final[Path]): Repository root.
        tests (Final[Path]): Shared corpus data and suite root.
        fixtures (Final[Path]): Root-level paired typing references.
        runtime (Final[Path]): Tests mirroring the installed package.
        scripts (Final[Path]): Tests mirroring repository tools.

    """

    root: Final[Path] = Path(__file__).resolve().parents[2]
    tests: Final[Path] = root / "tests"
    fixtures: Final[Path] = root / "fixtures"
    runtime: Final[Path] = tests / "astart"
    scripts: Final[Path] = tests / "scripts"
