"""Detect where a file lives so a checker can resolve its imports.

The external checker runs on a scratch copy kept outside the project. For it
to see what the real file sees, three things are derived from the file's
location: the package it belongs to (the chain of ``__init__.py`` files), the
directories absolute imports start from (the package's parent, a ``src``
layout, the project root), and its relative imports, which are rewritten
against the package because the scratch copy is not inside it.

"""

from __future__ import annotations

from ast import ImportFrom, Module, parse, unparse, walk
from dataclasses import dataclass
from os import environ, pathsep
from pathlib import Path
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        package_marker (Final[str]): File that makes a directory a package.
        source_directory (Final[str]): Conventional directory holding the
            source tree.
        path_variable (Final[str]): Environment variable listing extra import
            roots.

    """

    package_marker: Final[str] = "__init__.py"
    source_directory: Final[str] = "src"
    path_variable: Final[str] = "PYTHONPATH"


@final
@dataclass(frozen=True, slots=True)
class Environment:
    """What a checker needs to resolve a file's imports.

    Attributes:
        roots (tuple[Path, ...]): Directories absolute imports are resolved
            from, most specific first, without duplicates.
        package (tuple[str, ...]): Dotted package of the file as names; empty
            for a module that is not inside a package.

    """

    roots: tuple[Path, ...]
    package: tuple[str, ...]


def _package_of(*, directory: Path) -> tuple[tuple[str, ...], Path]:
    """Walk up through package directories.

    Args:
        directory (Path): Directory holding the file.

    Returns:
        tuple[tuple[str, ...], Path]: The package names, outermost first, and
            the directory that contains
            the outermost package (or ``directory`` itself when it is not one).

    """
    names: list[str] = []
    current: Path = directory
    while (current / Constants.package_marker).is_file():
        names.append(current.name)
        if current.parent == current:
            break
        current = current.parent
    return tuple(reversed(names)), current


def detect_environment(
    *,
    file: Path,
    project: Path,
    source_roots: tuple[Path, ...] = (),
) -> Environment:
    """Work out the import environment of a file.

    Args:
        file (Path): The checked file.
        project (Path): Project root the checker is configured for.
        source_roots (tuple[Path, ...]): Directories the user named explicitly;
            they come first.

    Returns:
        Environment:
            The package of the file and the roots imports resolve from.

    """
    directory: Path = file.resolve().parent
    package, top = _package_of(directory=directory)
    candidates: list[Path] = [*source_roots, top]
    if not package:
        candidates.append(directory)
    source: Path = project / Constants.source_directory
    if source.is_dir():
        candidates.append(source)
    candidates.append(project)
    candidates.extend(
        Path(entry)
        for entry in environ.get(Constants.path_variable, "").split(
            sep=pathsep,
        )
        if entry and Path(entry).is_dir()
    )
    return Environment(
        roots=tuple(dict.fromkeys(item.resolve() for item in candidates)),
        package=package,
    )


def absolutize_relative_imports(
    *,
    source: str,
    package: tuple[str, ...],
) -> str:
    """Rewrite relative imports as absolute ones against a package.

    Imports that climb above the outermost package, files outside a package
    and source that does not parse are left as written.

    Args:
        source (str): Module text.
        package (tuple[str, ...]): Package of the module, outermost first.

    Returns:
        str: Text whose imports mean the same but need no package context.

    """
    if not package:
        return source
    try:
        tree: Module = parse(source=source)
    except SyntaxError:
        return source
    changed: bool = False
    for node in walk(node=tree):
        if not isinstance(node, ImportFrom) or node.level == 0:
            continue
        keep: int = len(package) - (node.level - 1)
        if keep <= 0:
            continue
        base: list[str] = [*package[:keep]]
        if node.module:
            base.append(node.module)
        node.module = ".".join(base)
        node.level = 0
        changed = True
    return unparse(ast_obj=tree) + "\n" if changed else source
