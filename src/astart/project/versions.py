"""Python-version awareness for emitted syntax.

The annotation a fix may write depends on the oldest Python the project
supports. The floor comes from an explicit ``target-version``
configuration when present, otherwise from the ``requires-python``
specifier of the project's ``pyproject.toml``, otherwise from the
interpreter astart itself runs on — generated code must at least run
there.

"""

from __future__ import annotations

from dataclasses import dataclass
from sys import version_info
from tomllib import TOMLDecodeError, load
from typing import TYPE_CHECKING, Final, cast, final

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        floor_specifiers (Final[frozenset[str]]): Operators whose clause sets a
            lower bound.
        floor_markers (Final[tuple[str, ...]]): Longest-first operator
            spellings.
        table_key (Final[tuple[str, ...]]): ``pyproject.toml`` keys locating
            ``requires-python``.

    """

    floor_specifiers: Final[frozenset[str]] = frozenset(
        {">=", ">", "~=", "=="},
    )
    floor_markers: Final[tuple[str, ...]] = (">=", "~=", "==", ">")
    table_key: Final[tuple[str, ...]] = ("project", "requires-python")


@final
@dataclass(frozen=True, slots=True)
class PythonTarget:
    """The oldest Python version generated code must run on.

    Attributes:
        floor (tuple[int, int]): ``(major, minor)`` lower bound.

    """

    floor: tuple[int, int]

    @property
    def union_syntax(self) -> bool:
        """Whether ``X | Y`` annotation syntax is allowed.

        Returns:
            bool: ``True`` for Python 3.10 and newer.

        """
        return self.floor >= (3, 10)

    @property
    def pep695_generics(self) -> bool:
        """Whether PEP 695 ``def f[T]()``/``class C[T]`` is allowed.

        Returns:
            bool: ``True`` for Python 3.12 and newer.

        """
        return self.floor >= (3, 12)

    @property
    def type_statement(self) -> bool:
        """Whether the PEP 695 ``type X = ...`` statement is allowed.

        Returns:
            bool: ``True`` for Python 3.12 and newer.

        """
        return self.floor >= (3, 12)

    @property
    def self_type(self) -> bool:
        """Whether ``typing.Self`` exists in ``typing``.

        Returns:
            bool: ``True`` for Python 3.11 and newer.

        """
        return self.floor >= (3, 11)

    @property
    def type_alias_name(self) -> bool:
        """Whether ``typing.TypeAlias`` exists in ``typing``.

        Returns:
            bool: ``True`` for Python 3.10 and newer.

        """
        return self.floor >= (3, 10)

    @property
    def param_spec(self) -> bool:
        """Whether PEP 612 ``typing.ParamSpec`` exists in ``typing``.

        Returns:
            bool: ``True`` for Python 3.10 and newer.

        """
        return self.floor >= (3, 10)

    def union(self, *, members: str) -> str:
        """Spell a union for this target.

        Args:
            members (str): Type names joined by ``" | "``.

        Returns:
            str: ``X | Y`` when allowed, otherwise ``Union[X, Y]``.

        """
        if self.union_syntax:
            return members
        return f"Union[{members.replace(' | ', ', ')}]"

    def optional(self, *, inner: str) -> str:
        """Spell ``T | None`` for this target.

        Args:
            inner (str): The non-``None`` member.

        Returns:
            str: ``T | None`` when allowed, otherwise ``Optional[T]``.

        """
        if self.union_syntax:
            return f"{inner} | None"
        return f"Optional[{inner}]"


def parse_version(*, text: str) -> tuple[int, int] | None:
    """Parse a ``major.minor`` version string.

    Args:
        text (str): Version text like ``"3.10"`` or ``"3.10.4"``.

    Returns:
        tuple[int, int] | None: ``(major, minor)``, or ``None``
            when the text is not a plain version.

    """
    parts: list[str] = text.strip().split(sep=".")
    if len(parts) <= 1 or not all(part.isdigit() for part in parts):
        return None
    return int(parts[0]), int(parts[1])


def _floor_of(*, specifier: str) -> tuple[int, int] | None:
    """Extract the minimum version a ``requires-python`` value allows.

    Only ``>=``, ``>``, ``~=`` and ``==`` clauses set floors; ``>`` is
    treated as its version (a conservative under-approximation of the
    true floor, which restricts emitted syntax rather than allowing
    too-new syntax).

    Args:
        specifier (str): The ``requires-python`` string, e.g.
            ``">=3.9,!=3.10"``.

    Returns:
        tuple[int, int] | None:
            The lowest allowed ``(major, minor)``, or ``None``.

    """
    floors: list[tuple[int, int]] = []
    for clause in specifier.split(sep=","):
        _clause: str = clause.strip()
        for marker in Constants.floor_markers:
            if _clause.startswith(marker):
                version: tuple[int, int] | None = parse_version(
                    text=_clause.removeprefix(marker).strip(),
                )
                if version is not None:
                    floors.append(version)
                break
    return min(floors, default=None)


def requires_python_floor(*, pyproject: Path) -> tuple[int, int] | None:
    """Read the minimum Python version of a ``pyproject.toml``.

    Args:
        pyproject (Path): Path to the project's ``pyproject.toml``.

    Returns:
        tuple[int, int] | None: ``(major, minor)`` of the ``requires-python``
            floor, or ``None`` when absent or unreadable.

    """
    try:
        with pyproject.open(mode="rb") as handle:
            data: dict[str, object] = load(handle)
    except (OSError, TOMLDecodeError):
        return None
    project: object = data.get(Constants.table_key[0])
    specifier: str | None = None
    if isinstance(project, dict):
        specifier = next(
            (
                value
                for key, value in cast(
                    typ="dict[str, str]",
                    val=project,
                ).items()
                if key == Constants.table_key[1]
            ),
            None,
        )
    if not isinstance(specifier, str):
        return None
    return _floor_of(specifier=specifier)


def find_pyproject(*, paths: Iterable[Path]) -> Path | None:
    """Locate the ``pyproject.toml`` governing a set of paths.

    Each path's directory (or the path itself when it is a directory) and
    its ancestors are tried, nearest first.

    Args:
        paths (Iterable[Path]): Files or directories the command will touch.

    Returns:
        Path | None: The first ``pyproject.toml`` found, or ``None``.

    """
    for path in paths:
        directory: Path = (
            path.resolve() if path.is_dir() else path.resolve().parent
        )
        for candidate_dir in (directory, *directory.parents):
            candidate: Path = candidate_dir / "pyproject.toml"
            if candidate.is_file():
                return candidate
    return None


def resolve_target(
    *,
    configured: str | None = None,
    pyproject: Path | None = None,
) -> PythonTarget:
    """Pick the target version for emitted code.

    An explicit ``target-version`` wins over ``requires-python``, which
    wins over the running interpreter's own version.

    Args:
        configured (str | None): Explicit ``major.minor`` target, or ``None``.
        pyproject (Path | None): ``pyproject.toml`` to read ``requires-python``
            from, or ``None``.

    Returns:
        PythonTarget: The target.

    """
    if configured is not None:
        parsed: tuple[int, int] | None = parse_version(text=configured)
        if parsed is not None:
            return PythonTarget(floor=parsed)
    if pyproject is not None:
        floor: tuple[int, int] | None = requires_python_floor(
            pyproject=pyproject,
        )
        if floor is not None:
            return PythonTarget(floor=floor)
    return PythonTarget(floor=(version_info.major, version_info.minor))
