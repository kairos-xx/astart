"""Fix Python files on disk through the public API (API-03).

``fix_file``/``fix_paths`` read a file with its declared encoding, run
the same guarded fix pipeline as ``astart.api.fix_source`` and replace
the file atomically. Failures are reported in the outcome, never raised.

"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from os import fsync
from pathlib import Path
from shutil import copymode
from tempfile import NamedTemporaryFile
from tokenize import detect_encoding
from typing import TYPE_CHECKING, Final, final

from astart.api import fix_source

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from threading import Event

    from astart.rules import FixResult, FixSettings


@final
class Constants:
    """Group module-level constants.

    Attributes:
        default_filename (Final[str]): Display name used when only text is
            fixed.

    """

    default_filename: Final[str] = "<memory>"


@dataclass(frozen=True, slots=True)
class SourceFile:
    """A decoded source file.

    Attributes:
        text (str): Decoded source text.
        encoding (str): Encoding to write the file back with.

    """

    text: str
    encoding: str


@dataclass(frozen=True, slots=True)
class FileOutcome:
    """Result of fixing one file on disk.

    Attributes:
        path (Path): File that was processed.
        before (str): Original text, empty when the file could not be read.
        after (str): Fixed text; equals ``before`` on error or dry run.
        applied (int): Number of fixes applied.
        changed (bool): Whether ``after`` differs from ``before``.
        written (bool): Whether the file was replaced on disk.
        error (str | None): Why the file could not be fixed, if it could not.

    """

    path: Path
    before: str
    after: str
    applied: int
    changed: bool
    written: bool
    error: str | None


def write_atomic(*, path: Path, text: str, encoding: str) -> None:
    """Replace a file without ever leaving it half written.

    Symbolic links are followed, so the link stays a link; the file keeps its
    permissions; the temporary file never outlives the call.

    Args:
        path (Path): File to replace.
        text (str): New text.
        encoding (str): Encoding to write with.

    """
    target: Path = path.resolve()
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.astart-",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            _ = handle.write(text.encode(encoding=encoding))
            handle.flush()
            fsync(fd=handle.fileno())
        if target.exists():
            copymode(src=target, dst=temporary)
        _ = temporary.replace(target=target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_source(*, path: Path) -> SourceFile:
    """Read a Python file using its declared encoding.

    Args:
        path (Path): File to read.

    Returns:
        SourceFile: The decoded text and its encoding.

    Raises:
        OSError: The file cannot be read.
        SyntaxError: The encoding declaration is invalid.
        UnicodeError: The bytes do not decode in the declared encoding.

    """
    data: bytes = path.read_bytes()
    encoding: str = detect_encoding(
        readline=BytesIO(initial_bytes=data).readline,
    )[0]
    return SourceFile(text=data.decode(encoding=encoding), encoding=encoding)


def fix_file(
    *,
    path: Path,
    settings: FixSettings | None = None,
    write: bool = True,
) -> FileOutcome:
    """Fix one file, optionally writing the result back.

    Args:
        path (Path): Python file to fix.
        settings (FixSettings | None): Fix options; ``None`` selects the
            ``guarded`` defaults.
        write (bool): ``False`` computes the outcome without touching disk.

    Returns:
        FileOutcome: The per-file outcome; read, parse and write
            failures are reported in ``error``, never raised.

    """
    try:
        source: SourceFile = read_source(path=path)
    except (OSError, SyntaxError, UnicodeError) as error:
        return FileOutcome(
            path=path,
            before="",
            after="",
            applied=0,
            changed=False,
            written=False,
            error=str(object=error),
        )
    fixed: FixResult = fix_source(
        source=source.text,
        filename=str(object=path),
        settings=settings,
    )
    after: str = fixed.source if fixed.parse_error is None else source.text
    changed: bool = after != source.text
    written: bool = False
    write_error: str | None = fixed.parse_error
    if write_error is None and changed and write:
        try:
            write_atomic(path=path, text=after, encoding=source.encoding)
            written = True
        except OSError as error:
            write_error = str(object=error)
    return FileOutcome(
        path=path,
        before=source.text,
        after=after,
        applied=len(fixed.applied),
        changed=changed,
        written=written,
        error=write_error,
    )


def fix_paths(
    *,
    paths: Iterable[Path],
    settings: FixSettings | None = None,
    write: bool = True,
    on_file: Callable[[Path, FileOutcome], None] | None = None,
    cancel: Event | None = None,
) -> tuple[FileOutcome, ...]:
    """Fix every file in order, one outcome per input path.

    Args:
        paths (Iterable[Path]): Python files to fix, in the order outcomes are
            returned.
        settings (FixSettings | None): Fix options shared by every file.
        write (bool): ``False`` computes outcomes without touching disk.
        on_file (Callable[[Path, FileOutcome], None] | None): Optional callback
            invoked once per processed file
            with its path and outcome, after the file is done.
        cancel (Event | None): Optional :class:`threading.Event`; when set,
            processing stops before the next file and
            the outcomes collected so far are returned.

    Returns:
        tuple[FileOutcome, ...]: One ``FileOutcome`` per processed path, in
            input
            order; a failure in one file does not stop the others,
            and a set ``cancel`` event ends the run early.

    """
    outcomes: list[FileOutcome] = []
    for path in paths:
        if cancel is not None and cancel.is_set():
            break
        outcome: FileOutcome = fix_file(
            path=path,
            settings=settings,
            write=write,
        )
        outcomes.append(outcome)
        if on_file is not None:
            on_file(path, outcome)
    return tuple(outcomes)
