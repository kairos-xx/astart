"""Build a :class:`ProjectIndex` from source files.

Scanning is deliberately cheap: each file is parsed once, and files that
fail to parse or resolve to no module name are skipped rather than
aborting the build — their callers simply see them as external. Module
name collisions (the same dotted name from two files) keep the file that
sorts first, so results are deterministic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from astart.project.index import ProjectConfig, ProjectIndex
from astart.project.naming import module_name
from astart.project.scan import ModuleScan, scan_module

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path


@final
class BuildResult:
    """What a project build found.

    Attributes:
        index: The built index.
        skipped: Files that could not be scanned (unreadable or
            unparseable), each with the reason.
        collisions: Dotted names claimed by more than one file; the first
            sorted file won.

    """

    def __init__(
        self,
        *,
        index: ProjectIndex,
        skipped: tuple[tuple[Path, str], ...],
        collisions: tuple[str, ...],
    ) -> None:
        """Record the build outcome.

        Args:
            index: The built index.
            skipped: Unscanned files with reasons.
            collisions: Duplicate dotted names.

        """
        self.index: ProjectIndex = index
        self.skipped: tuple[tuple[Path, str], ...] = skipped
        self.collisions: tuple[str, ...] = collisions


def build_index(
    *,
    files: Iterable[Path],
    source_roots: Sequence[Path] | None = None,
    config: ProjectConfig | None = None,
) -> BuildResult:
    """Scan a set of files and index them as one project.

    Args:
        files: Source files making up the project.
        source_roots: Import roots for dotted naming; defaults to the
            package-chain and directory fallback of
            :func:`module_name`.
        config: Open-world policy for the index.

    Returns:
        The index plus what could not be scanned.

    """
    scans: dict[str, ModuleScan] = {}
    skipped: list[tuple[Path, str]] = []
    collisions: set[str] = set()
    for path in sorted({file.resolve() for file in files}):
        name: str | None = module_name(
            path=path,
            source_roots=tuple(source_roots or ()),
        )
        if name is None:
            skipped.append((path, "no module name"))
            continue
        if name in scans:
            collisions.add(name)
            continue
        try:
            source: str = path.read_text(encoding="utf-8")
        except OSError as error:
            skipped.append((path, f"unreadable: {error}"))
            continue
        try:
            scans[name] = scan_module(source=source, name=name, path=path)
        except (SyntaxError, ValueError) as error:
            skipped.append((path, f"unparseable: {error}"))
    return BuildResult(
        index=ProjectIndex(scans=scans, config=config),
        skipped=tuple(skipped),
        collisions=tuple(sorted(collisions)),
    )
