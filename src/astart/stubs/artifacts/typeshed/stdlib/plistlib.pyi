from collections.abc import Mapping, MutableMapping
from datetime import datetime
from enum import Enum
from typing import IO, Any, Final, Self

from _typeshed import ReadableBuffer

__all__ = [
    "FMT_BINARY",
    "FMT_XML",
    "UID",
    "InvalidFileException",
    "dump",
    "dumps",
    "load",
    "loads",
]

class PlistFormat(Enum):
    FMT_XML = 1
    FMT_BINARY = 2

FMT_XML: Final = PlistFormat.FMT_XML
FMT_BINARY: Final = PlistFormat.FMT_BINARY

def load(
    fp: IO[bytes],
    *,
    fmt: PlistFormat | None = None,
    dict_type: type[MutableMapping[str, Any]] = ...,
    aware_datetime: bool = False,
) -> Any: ...
def loads(
    value: ReadableBuffer | str,
    *,
    fmt: PlistFormat | None = None,
    dict_type: type[MutableMapping[str, Any]] = ...,
    aware_datetime: bool = False,
) -> Any: ...
def dump(
    value: Mapping[str, Any]
    | list[Any]
    | tuple[Any, ...]
    | str
    | bool
    | float
    | bytes
    | bytearray
    | datetime,
    fp: IO[bytes],
    *,
    fmt: PlistFormat = ...,
    sort_keys: bool = True,
    skipkeys: bool = False,
    aware_datetime: bool = False,
) -> None: ...
def dumps(
    value: Mapping[str, Any]
    | list[Any]
    | tuple[Any, ...]
    | str
    | bool
    | float
    | bytes
    | bytearray
    | datetime,
    *,
    fmt: PlistFormat = ...,
    skipkeys: bool = False,
    sort_keys: bool = True,
    aware_datetime: bool = False,
) -> bytes: ...

class UID:
    data: int
    def __init__(self, data: int) -> None: ...
    def __index__(self) -> int: ...
    def __reduce__(self) -> tuple[type[Self], tuple[int]]: ...
    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...

class InvalidFileException(ValueError):
    def __init__(self, message: str = "Invalid file") -> None: ...
