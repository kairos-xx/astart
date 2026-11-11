"""Find the Python files a command should process."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        skipped_directories (Final[frozenset[str]]): Grouped module constant.
        suffix (Final[str]): Grouped module constant.

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
        files (tuple[Path, ...]): Sorted, de-duplicated Python files.
        missing (tuple[Path, ...]): Arguments that name nothing on disk.

    """

    files: tuple[Path, ...]
    missing: tuple[Path, ...]


def discover_files(
    *,
    paths: Sequence[Path],
    exclude: Sequence[str] = (),
) -> DiscoveryResult:
    """Expand command arguments into Python files.

    Explicit files are always kept, whatever their name or directory,
    unless an ``exclude`` glob matches them. Directories are walked,
    skipping virtual environments, caches and ``exclude`` matches.

    Args:
        paths (Sequence[Path]): Files and directories named on the command
            line.
        exclude (Sequence[str]): ``fnmatch`` globs; a path is skipped when its
            posix string —
            absolute, or relative to the walked root — matches any of them.

    Returns:
        DiscoveryResult:
            The files to process and the arguments that do not exist.

    """
    found: set[Path] = set()
    missing: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.update(_walk(root=path, exclude=exclude))
        elif path.is_file():
            if not _excluded(path=path, bases=(), globs=exclude):
                found.add(path)
        else:
            missing.append(path)
    return DiscoveryResult(files=tuple(sorted(found)), missing=tuple(missing))


def _walk(*, root: Path, exclude: Sequence[str]) -> list[Path]:
    """Collect Python files below a directory, pruning skipped names.

    Args:
        root (Path): Directory to walk.
        exclude (Sequence[str]): ``fnmatch`` globs matched against each file's
            path
            relative to ``root`` (and its absolute posix string).

    Returns:
        list[Path]: Python files below the directory.

    """
    collected: list[Path] = []
    for directory, names, files in walk(top=root):
        names[:] = [
            name for name in names if name not in Constants.skipped_directories
        ]
        for name in files:
            if not name.endswith(Constants.suffix):
                continue
            path: Path = Path(directory) / name
            if not _excluded(path=path, bases=(root,), globs=exclude):
                collected.append(path)
    return collected


def _excluded(
    *,
    path: Path,
    bases: Sequence[Path],
    globs: Sequence[str],
) -> bool:
    """Answer whether ``path`` matches any exclude glob.

    Args:
        path (Path): Candidate file.
        bases (Sequence[Path]): Directories the path is also matched relative
            to.
        globs (Sequence[str]): ``fnmatch`` patterns.

    Returns:
        bool: ``True`` when any pattern matches the absolute posix string or a
            base-relative one.

    """
    if not globs:
        return False
    names: set[str] = {path.as_posix()}
    for base in bases:
        try:
            names.add(path.relative_to(base).as_posix())
        except ValueError:
            continue
    return any(
        fnmatch(name=name, pat=pattern) for name in names for pattern in globs
    )
