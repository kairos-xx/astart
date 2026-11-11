"""Map filesystem paths to dotted Python module names.

A module's name is its import identity: ``pkg/sub/mod.py`` is
``pkg.sub.mod`` and ``pkg/sub/__init__.py`` is ``pkg.sub``. Source roots are
the directories imports are resolved from (``src/``, the project root, a
site-packages directory). Without a root the name is derived from the chain
of ``__init__.py`` markers above the file itself.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        init_file (Final[str]): Name marking a directory as a package.
        init_stub (Final[str]): Stub name marking a directory as a package.

    """

    init_file: Final[str] = "__init__.py"
    init_stub: Final[str] = "__init__.pyi"


def _is_package_dir(*, directory: Path) -> bool:
    """Tell whether a directory declares itself a package.

    Args:
        directory (Path): Directory to test.

    Returns:
        bool: ``True`` when the directory holds an ``__init__`` marker.

    """
    return (directory / Constants.init_file).is_file() or (
        directory / Constants.init_stub
    ).is_file()


def module_name(
    *,
    path: Path,
    source_roots: tuple[Path, ...] = (),
) -> str | None:
    """Compute the dotted import name of a source file.

    The first source root containing the file wins, and the name is the
    file's path relative to it. Without a matching root, the chain of
    packages is derived from ``__init__`` markers: the name climbs from the
    file's directory through every ancestor that is itself a package.

    Args:
        path (Path): The ``.py``/``.pyi`` file to name.
        source_roots (tuple[Path, ...]): Directories imports are resolved from,
            most specific first.

    Returns:
        str | None: The dotted module name, or ``None`` when
            the path cannot name an importable module.

    """
    resolved: Path = path.resolve()
    leaf: tuple[str, ...] = (
        () if resolved.stem == "__init__" else (resolved.stem,)
    )
    for root in source_roots:
        try:
            inside: Path = resolved.parent.relative_to(root.resolve())
        except ValueError:
            continue
        parts: tuple[str, ...] = (*inside.parts, *leaf)
        if parts and all(part.isidentifier() for part in parts):
            return ".".join(parts)
        return None
    chain: list[str] = [*leaf]
    directory: Path = resolved.parent
    while _is_package_dir(directory=directory):
        chain.insert(0, directory.name)
        directory = directory.parent
    if not chain or not all(part.isidentifier() for part in chain):
        return None
    return ".".join(chain)


def package_of(*, name: str, is_package: bool) -> str:
    """Return the package a module's relative imports resolve against.

    ``from . import x`` inside ``pkg.mod`` means ``pkg.x``; inside
    ``pkg/__init__.py`` it still means ``pkg.x`` because the module *is* the
    package.

    Args:
        name (str): Dotted module name.
        is_package (bool): Whether the module is a package ``__init__``.

    Returns:
        str: The dotted package name; empty for a top-level module.

    """
    return name if is_package else name.rpartition(".")[0]
