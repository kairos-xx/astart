"""Locate the typeshed snapshot bundled with astart.

astart ships its own typeshed copy as package data under
``astart.stubs.artifacts.typeshed``. ``find_typeshed`` honours an explicit
directory and the ``ASTART_TYPESHED`` environment variable first, then
falls back to the bundled snapshot; it never scans other installed
packages or editor extensions, so every machine resolves the same stubs.

"""

from __future__ import annotations

from importlib.resources import files
from os import environ
from pathlib import Path
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        environment (Final[str]): Variable that names a typeshed directory.
        bundled (Final[str]): Package-data directory holding the shipped
            typeshed root.
        marker (Final[tuple[str, str]]): File that every typeshed root has.

    """

    environment: Final[str] = "ASTART_TYPESHED"
    bundled: Final[str] = "typeshed"
    marker: Final[tuple[str, str]] = ("stdlib", "VERSIONS")


def is_typeshed(*, root: Path) -> bool:
    """Tell whether a directory is a typeshed root.

    Args:
        root (Path): Candidate directory.

    Returns:
        bool: ``True`` when it holds ``stdlib/VERSIONS``.

    """
    return root.joinpath(*Constants.marker).is_file()


def bundled_typeshed() -> Path | None:
    """Return the typeshed snapshot shipped inside the package.

    Returns:
        Path | None: The bundled root when present and valid, or ``None``.

    """
    root: Path = Path(
        str(
            object=files(anchor="astart.stubs").joinpath(
                "artifacts",
                Constants.bundled,
            ),
        ),
    )
    return root if is_typeshed(root=root) else None


def find_typeshed(*, explicit: Path | None = None) -> Path | None:
    """Find the typeshed root to read stubs from.

    Args:
        explicit (Path | None): A directory the caller chose; used first when
            valid.

    Returns:
        Path | None:
            The explicit directory, the ``ASTART_TYPESHED`` directory, the
            bundled snapshot, or ``None`` when none is a valid typeshed root.

    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    named: str | None = environ.get(Constants.environment)
    if named:
        candidates.append(Path(named))
    for root in candidates:
        if is_typeshed(root=root):
            return root
    return bundled_typeshed()
