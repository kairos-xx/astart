"""Before-images and undo journal for ``astart fix --backup``."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

from astart.cli.atomic import write_atomic

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TextIO

    from astart.rules.jsonvalue import JsonValue

BACKUP_ROOT: Final[str] = ".astart-backup"
JOURNAL_NAME: Final[str] = "journal.json"


@final
@dataclass(frozen=True, slots=True)
class Entry:
    """One file's backup record.

    Attributes:
        path (str): File that was rewritten, as given on the command line.
        before_sha (str): SHA-256 of the text before the fix.
        after_sha (str): SHA-256 of the text after the fix.
        saved (str): Name of the ``.bak`` file inside the run directory.

    """

    path: str
    before_sha: str
    after_sha: str
    saved: str


def _sha(*, text: str, encoding: str) -> str:
    """Hash a text the way undo will compare it.

    Args:
        text (str): Text to hash.
        encoding (str): Encoding the text is stored with.

    Returns:
        str: Hexadecimal SHA-256 digest.

    """
    return sha256(data=text.encode(encoding=encoding)).hexdigest()


def save(
    *,
    run_dir: Path,
    path: Path,
    before: str,
    after: str,
    encoding: str,
) -> Entry:
    """Store the before-image of one rewritten file.

    Args:
        run_dir (Path): Run directory receiving the ``.bak`` file.
        path (Path): File that was rewritten.
        before (str): Text the file held before the fix.
        after (str): Text the file holds after the fix.
        encoding (str): Encoding the file is written with.

    Returns:
        Entry: The journal entry describing the backup.

    """
    index: int = len(list(run_dir.glob(pattern="*.bak")))
    saved: str = f"{index:05d}.bak"
    write_atomic(
        path=run_dir / saved,
        text=before,
        encoding=encoding,
    )
    return Entry(
        path=str(object=path),
        before_sha=_sha(text=before, encoding=encoding),
        after_sha=_sha(text=after, encoding=encoding),
        saved=saved,
    )


def write_journal(*, run_dir: Path, entries: Sequence[Entry]) -> None:
    """Write ``journal.json`` for one backup run.

    Args:
        run_dir (Path): Run directory receiving the journal.
        entries (Sequence[Entry]): Backup entries of the run, in write order.

    """
    document: str = dumps(
        obj={"entries": [asdict(obj=entry) for entry in entries]},
        indent=2,
    )
    write_atomic(path=run_dir / JOURNAL_NAME, text=document, encoding="utf-8")


def _entries(*, run_dir: Path) -> list[Entry]:
    """Read the journal of one run directory.

    Args:
        run_dir (Path): Run directory holding ``journal.json``.

    Returns:
        list[Entry]: The recorded entries, or an empty list when unreadable.

    """
    journal: Path = run_dir / JOURNAL_NAME
    try:
        document: JsonValue = loads(
            s=journal.read_text(encoding="utf-8"),
        )
    except (OSError, JSONDecodeError):
        return []
    if not isinstance(document, dict):
        return []
    raw: JsonValue = document.get("entries")
    if not isinstance(raw, list):
        return []
    entries: list[Entry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            entries.append(
                Entry(
                    path=str(object=item["path"]),
                    before_sha=str(object=item["before_sha"]),
                    after_sha=str(object=item["after_sha"]),
                    saved=str(object=item["saved"]),
                ),
            )
        except KeyError:
            continue
    return entries


def undo(*, run_dir: Path, out: TextIO) -> int:
    """Restore every file of a run whose content is unchanged since.

    Args:
        run_dir (Path): Run directory holding ``journal.json`` and the ``.bak``
            files.
        out (TextIO): Stream the per-file outcome is written to.

    Returns:
        int: ``1`` when any file was edited since
            the fix and skipped, else ``0``.

    """
    skipped: bool = False
    for entry in _entries(run_dir=run_dir):
        path: Path = Path(entry.path)
        saved: Path = run_dir / entry.saved
        try:
            current: str = path.read_text(encoding="utf-8")
            before: str = saved.read_text(encoding="utf-8")
        except OSError:
            skipped = True
            _ = out.write(f"skipped (missing): {entry.path}\n")
            continue
        if _sha(text=current, encoding="utf-8") != entry.after_sha:
            skipped = True
            _ = out.write(f"skipped (edited since): {entry.path}\n")
            continue
        write_atomic(path=path, text=before, encoding="utf-8")
        _ = out.write(f"restored: {entry.path}\n")
    return 1 if skipped else 0
