from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

__all__ = ["ZipAppError", "create_archive", "get_interpreter"]
type _Path = str | Path | BinaryIO

class ZipAppError(ValueError): ...

def create_archive(
    source: _Path,
    target: _Path | None = None,
    interpreter: str | None = None,
    main: str | None = None,
    filter: Callable[[Path], bool] | None = None,
    compressed: bool = False,
) -> None: ...
def get_interpreter(archive: _Path) -> str: ...
