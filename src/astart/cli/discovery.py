"""Find the Python files a command should process."""

from __future__ import annotations

from dataclasses import dataclass
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        skipped_directories: Grouped module constant.
        suffix: Grouped module constant.

    """

    skipped_directories: Final[frozenset[str]] = frozenset(
        {
            ".git",
            ".hg",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "build",
            "dist",
            ".tox",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
        },
    )
    suffix: Final[str] = ".py"


@final
@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Files found for a command.

    Attributes:
        files: Sorted, de-duplicated Python files.
        missing: Arguments that name nothing on disk.

    """

    files: tuple[Path, ...]
    missing: tuple[Path, ...]


def discover_files(*, paths: Sequence[Path]) -> DiscoveryResult:
    """Expand command arguments into Python files.

    Explicit files are always kept, whatever their name or directory.
    Directories are walked, skipping virtual environments and caches.

    Args:
        paths: Files and directories named on the command line.

    Returns:
        The files to process and the arguments that do not exist.

    """
    found: set[Path] = set()
    missing: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.update(_walk(root=path))
        elif path.is_file():
            found.add(path)
        else:
            missing.append(path)
    return DiscoveryResult(files=tuple(sorted(found)), missing=tuple(missing))


def _walk(*, root: Path) -> list[Path]:
    """Collect Python files below a directory, pruning skipped names.

    Args:
        root: Directory to walk.

    Returns:
        Python files below the directory.

    """
    collected: list[Path] = []
    for directory, names, files in walk(top=root):
        names[:] = [
            name for name in names if name not in Constants.skipped_directories
        ]
        collected.extend(
            Path(directory) / name
            for name in files
            if name.endswith(Constants.suffix)
        )
    return collected
