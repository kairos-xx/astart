"""Persistent content-hash cache for ``astart fix``.

A file's fix result depends only on its text, its path, the options of the
run, the tool itself (its code and rule catalog), the type checker, the
formatter and the project's configuration files. All of those are folded into
one key, so a hit is a result that would be recomputed identically. Entries
are small JSON files; anything unreadable is a miss.

"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict, final

if TYPE_CHECKING:
    from _hashlib import HASH


@final
class Constants:
    """Group module-level constants.

    Attributes:
        directory (Final[str]): Default cache directory, relative to the
            working directory.
        schema (Final[int]): Entry layout version; bump it to invalidate old
            entries.
        suffixes (Final[tuple[str, ...]]): Package files that change what the
            tool does.
        configs (Final[tuple[str, ...]]): Project files that change the
            formatter or the checker.

    """

    directory: Final[str] = ".astart_cache"
    schema: Final[int] = 1
    suffixes: Final[tuple[str, ...]] = ("*.py", "*.json")
    configs: Final[tuple[str, ...]] = (
        "pyproject.toml",
        "ruff.toml",
        ".ruff.toml",
        "pyrightconfig.json",
        "mypy.ini",
    )


@final
@dataclass(frozen=True, slots=True)
class CachedFix:
    """What a run produced for one file.

    Attributes:
        after (str): The fixed (and formatted) text.
        applied (int): Number of fixes applied.
        skipped (tuple[str, ...]): Descriptions of fixes that were not applied.
        note (str): Formatter note, empty when there is none.

    """

    after: str
    applied: int
    skipped: tuple[str, ...]
    note: str


class _Entry(TypedDict):
    """Fields of one stored cache entry.

    Attributes:
        schema (int): Entry layout version.
        after (str): The fixed (and formatted) text.
        applied (int): Number of fixes applied.
        skipped (list[str]): Descriptions of fixes that were not applied.
        note (str): Formatter note, empty when there is none.

    """

    schema: int
    after: str
    applied: int
    skipped: list[str]
    note: str


def tool_fingerprint(*, environment: str, root: Path) -> str:
    """Hash everything besides the file that decides a fix result.

    Args:
        environment (str): Text describing the run's options, checker and
            formatter version.
        root (Path): Directory whose configuration files count.

    Returns:
        str: A hex digest.

    """
    digest: HASH = sha256()
    digest.update(environment.encode())
    package: Path = Path(__file__).parent.parent
    for pattern in Constants.suffixes:
        for path in sorted(package.rglob(pattern=pattern)):
            digest.update(path.relative_to(package).as_posix().encode())
            digest.update(path.read_bytes())
    for name in Constants.configs:
        found: Path = root / name
        if found.is_file():
            digest.update(name.encode())
            digest.update(found.read_bytes())
    return digest.hexdigest()


@final
class FixCache:
    """Look up and store fix results on disk."""

    def __init__(self, *, directory: Path, fingerprint: str) -> None:
        """Remember where entries live and what they are valid for.

        Args:
            directory (Path): Cache directory; created on first store.
            fingerprint (str): Digest from :func:`tool_fingerprint`.

        """
        self._directory: Path = directory
        self._fingerprint: str = fingerprint

    def _entry(self, *, path: Path, source: str) -> Path:
        """Locate the entry for one file and text.

        Args:
            path (Path): The file.
            source (str): Its current text.

        Returns:
            Path: The entry's path.

        """
        digest: HASH = sha256()
        digest.update(self._fingerprint.encode())
        digest.update(str(object=path.resolve()).encode())
        digest.update(source.encode())
        return self._directory / f"{digest.hexdigest()}.json"

    def load(self, *, path: Path, source: str) -> CachedFix | None:
        """Return the stored result for a file, if there is a valid one.

        Args:
            path (Path): The file.
            source (str): Its current text.

        Returns:
            CachedFix | None:
                The result, or ``None`` on a miss or an unreadable entry.

        """
        try:
            data: _Entry = loads(
                s=self._entry(path=path, source=source).read_text(
                    encoding="utf-8",
                ),
            )
            if data["schema"] != Constants.schema:
                return None
            return CachedFix(
                after=str(object=data["after"]),
                applied=data["applied"],
                skipped=tuple(str(object=item) for item in data["skipped"]),
                note=str(object=data["note"]),
            )
        except (OSError, JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def store(self, *, path: Path, source: str, entry: CachedFix) -> None:
        """Save a result; failures to write are ignored.

        Args:
            path (Path): The file.
            source (str): Its text before fixing.
            entry (CachedFix): The result to remember.

        """
        target: Path = self._entry(path=path, source=source)
        temporary: Path = target.with_suffix(suffix=".tmp")
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            _ = temporary.write_text(
                data=dumps(
                    obj={
                        "schema": Constants.schema,
                        "after": entry.after,
                        "applied": entry.applied,
                        "skipped": list(entry.skipped),
                        "note": entry.note,
                    },
                ),
                encoding="utf-8",
            )
            _ = temporary.replace(target=target)
        except OSError:
            return


def clear_cache(*, root: Path) -> int:
    """Delete every cached fix result under ``root``.

    Args:
        root (Path): Directory containing the ``.astart_cache`` directory.

    Returns:
        int: Number of entry files removed; ``0`` when no cache exists.

    """
    directory: Path = root / Constants.directory
    if not directory.is_dir():
        return 0
    entries: list[Path] = sorted(directory.glob(pattern="*.json"))
    for entry in entries:
        entry.unlink()
    return len(entries)
