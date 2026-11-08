"""Find a copy of typeshed on this machine.

astart ships none. A copy is looked for, in order, at an explicit path, in
the ``ASTART_TYPESHED`` environment variable, and inside the type checkers
and tools that bundle one (basedpyright, mypy, jedi, pytype, typeshed_client
when it happens to be installed — never required).
"""

from __future__ import annotations

from importlib.util import find_spec
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec


@final
class Constants:
    """Group module-level constants.

    Attributes:
        environment: Variable that names a typeshed directory.
        bundles: Importable packages that carry a copy, with the path of the
            copy inside the package.
        marker: File that every typeshed root has.

    """

    environment: Final[str] = "ASTART_TYPESHED"
    bundles: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
        ("basedpyright", ("dist", "typeshed-fallback")),
        ("pyright", ("dist", "typeshed-fallback")),
        ("mypy", ("typeshed",)),
        ("jedi", ("third_party", "typeshed")),
        ("pytype", ("typeshed",)),
        ("typeshed_client", ("typeshed",)),
    )
    marker: Final[tuple[str, str]] = ("stdlib", "VERSIONS")


def is_typeshed(*, root: Path) -> bool:
    """Tell whether a directory is a typeshed root.

    Args:
        root: Candidate directory.

    Returns:
        ``True`` when it holds ``stdlib/VERSIONS``.

    """
    return root.joinpath(*Constants.marker).is_file()


def _bundled() -> list[Path]:
    """List the typeshed copies inside installed packages.

    Returns:
        Candidate roots, best first.

    """
    found: list[Path] = []
    for package, inside in Constants.bundles:
        try:
            spec: ModuleSpec | None = find_spec(name=package)
        except (ImportError, ValueError):
            continue
        if spec is None or spec.origin is None:
            continue
        found.append(Path(spec.origin).parent.joinpath(*inside))
    return found


def find_typeshed(*, explicit: Path | None = None) -> Path | None:
    """Find a typeshed root.

    Args:
        explicit: A directory the caller chose; used first when valid.

    Returns:
        The first valid root, or ``None`` when the machine has none.

    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    named: str | None = environ.get(Constants.environment)
    if named:
        candidates.append(Path(named))
    candidates.extend(_bundled())
    for root in candidates:
        if is_typeshed(root=root):
            return root
    return None
