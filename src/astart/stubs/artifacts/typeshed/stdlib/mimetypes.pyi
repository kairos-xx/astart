from collections.abc import Iterable
from typing import IO

from _typeshed import StrPath

__all__ = [
    "MimeTypes",
    "add_type",
    "common_types",
    "encodings_map",
    "guess_all_extensions",
    "guess_extension",
    "guess_type",
    "init",
    "inited",
    "knownfiles",
    "read_mime_types",
    "suffix_map",
    "types_map",
]
__all__ += ["guess_file_type"]

def guess_type(
    url: StrPath,
    strict: bool = True,
) -> tuple[str | None, str | None]: ...
def guess_all_extensions(type: str, strict: bool = True) -> list[str]: ...
def guess_extension(type: str, strict: bool = True) -> str | None: ...
def init(files: Iterable[StrPath] | None = None) -> None: ...
def read_mime_types(file: StrPath) -> dict[str, str] | None: ...
def add_type(type: str, ext: str, strict: bool = True) -> None: ...
def guess_file_type(
    path: StrPath,
    *,
    strict: bool = True,
) -> tuple[str | None, str | None]: ...

inited: bool
knownfiles: list[StrPath]
suffix_map: dict[str, str]
encodings_map: dict[str, str]
types_map: dict[str, str]
common_types: dict[str, str]

class MimeTypes:
    suffix_map: dict[str, str]
    encodings_map: dict[str, str]
    types_map: tuple[dict[str, str], dict[str, str]]
    types_map_inv: tuple[dict[str, str], dict[str, str]]
    def __init__(
        self,
        filenames: Iterable[StrPath] = (),
        strict: bool = True,
    ) -> None: ...
    def add_type(self, type: str, ext: str, strict: bool = True) -> None: ...
    def guess_extension(
        self,
        type: str,
        strict: bool = True,
    ) -> str | None: ...
    def guess_type(
        self,
        url: StrPath,
        strict: bool = True,
    ) -> tuple[str | None, str | None]: ...
    def guess_all_extensions(
        self,
        type: str,
        strict: bool = True,
    ) -> list[str]: ...
    def read(self, filename: StrPath, strict: bool = True) -> None: ...
    def readfp(self, fp: IO[str], strict: bool = True) -> None: ...
    def read_windows_registry(self, strict: bool = True) -> None: ...
    def guess_file_type(
        self,
        path: StrPath,
        *,
        strict: bool = True,
    ) -> tuple[str | None, str | None]: ...
