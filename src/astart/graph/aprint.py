"""Helper function that mimics print() with file path support."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from sys import stdout
from typing import TextIO


def aprint(
    *args: str | bytes | float | bool | Path | None,
    sep: str | None = None,
    end: str | None = None,
    file: str | Path | TextIO | None = None,
    mode: str = "a",
    flush: bool = False,
) -> None:
    """Mimic print() using write(), optionally writing to a file path.

    Args:
        args (str | bytes | float | bool | Path | None): Collection of args
            supplied for this operation.
        end (str | None): End identifying a position in the relevant sequence
            or source.
        file (str | Path | TextIO | None): File supplied as str | Path | TextIO
            | None for this operation.
        flush (bool): Flush supplied as bool for this operation.
        mode (str): Mode supplied as str for this operation.
        sep (str | None): Sep supplied as str | None for this operation.

    """
    with (
        Path(file).open(mode=mode, encoding="utf-8")
        if isinstance(file, str | Path)
        else nullcontext(enter_result=file or stdout)
    ) as stream:
        stream.write(
            (sep if sep is not None else " ").join(map(str, args))
            + (end if end is not None else "\n"),
        )
        if flush:
            stream.flush()
