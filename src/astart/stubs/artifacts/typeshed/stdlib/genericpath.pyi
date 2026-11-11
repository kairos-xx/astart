import os
import sys
from collections.abc import Sequence
from typing import Literal, LiteralString, NewType, overload
from warnings import deprecated

from _typeshed import (
    BytesPath,
    FileDescriptorOrPath,
    StrOrBytesPath,
    StrPath,
    SupportsRichComparisonT,
)

__all__ = [
    "ALLOW_MISSING",
    "commonprefix",
    "exists",
    "getatime",
    "getctime",
    "getmtime",
    "getsize",
    "isdir",
    "isfile",
    "samefile",
    "sameopenfile",
    "samestat",
]
__all__ += ["islink"]
__all__ += ["isdevdrive", "isjunction", "lexists"]
if sys.version_info >= (3, 15):
    __all__ += ["ALL_BUT_LAST"]
if sys.version_info >= (3, 15):
    @overload
    @deprecated(
        "Deprecated since Python 3.15; use os.path.commonpath() for path prefixes.",
    )
    def commonprefix(m: Sequence[LiteralString], /) -> LiteralString: ...
    @overload
    @deprecated(
        "Deprecated since Python 3.15; use os.path.commonpath() for path prefixes.",
    )
    def commonprefix(m: Sequence[StrPath], /) -> str: ...
    @overload
    @deprecated(
        "Deprecated since Python 3.15; use os.path.commonpath() for path prefixes.",
    )
    def commonprefix(m: Sequence[BytesPath], /) -> bytes | Literal[""]: ...
    @overload
    @deprecated(
        "Deprecated since Python 3.15; use os.path.commonpath() for path prefixes.",
    )
    def commonprefix(
        m: Sequence[list[SupportsRichComparisonT]],
        /,
    ) -> Sequence[SupportsRichComparisonT]: ...
    @overload
    @deprecated(
        "Deprecated since Python 3.15; use os.path.commonpath() for path prefixes.",
    )
    def commonprefix(
        m: Sequence[tuple[SupportsRichComparisonT, ...]],
        /,
    ) -> Sequence[SupportsRichComparisonT]: ...
else:
    @overload
    def commonprefix(m: Sequence[LiteralString]) -> LiteralString: ...
    @overload
    def commonprefix(m: Sequence[StrPath]) -> str: ...
    @overload
    def commonprefix(m: Sequence[BytesPath]) -> bytes | Literal[""]: ...
    @overload
    def commonprefix(
        m: Sequence[list[SupportsRichComparisonT]],
    ) -> Sequence[SupportsRichComparisonT]: ...
    @overload
    def commonprefix(
        m: Sequence[tuple[SupportsRichComparisonT, ...]],
    ) -> Sequence[SupportsRichComparisonT]: ...

def exists(path: FileDescriptorOrPath) -> bool: ...
def isfile(path: FileDescriptorOrPath) -> bool: ...
def isdir(s: FileDescriptorOrPath) -> bool: ...
def islink(path: StrOrBytesPath) -> bool: ...
def sameopenfile(fp1: int, fp2: int) -> bool: ...

if sys.version_info >= (3, 15):
    def getsize(filename: FileDescriptorOrPath, /) -> int: ...
    def getatime(filename: FileDescriptorOrPath, /) -> float: ...
    def getmtime(filename: FileDescriptorOrPath, /) -> float: ...
    def getctime(filename: FileDescriptorOrPath, /) -> float: ...
    def samefile(
        f1: FileDescriptorOrPath,
        f2: FileDescriptorOrPath,
        /,
    ) -> bool: ...
    def samestat(s1: os.stat_result, s2: os.stat_result, /) -> bool: ...
else:
    def getsize(filename: FileDescriptorOrPath) -> int: ...
    def getatime(filename: FileDescriptorOrPath) -> float: ...
    def getmtime(filename: FileDescriptorOrPath) -> float: ...
    def getctime(filename: FileDescriptorOrPath) -> float: ...
    def samefile(
        f1: FileDescriptorOrPath,
        f2: FileDescriptorOrPath,
    ) -> bool: ...
    def samestat(s1: os.stat_result, s2: os.stat_result) -> bool: ...

def isjunction(path: StrOrBytesPath) -> bool: ...
def isdevdrive(path: StrOrBytesPath) -> bool: ...
def lexists(path: StrOrBytesPath) -> bool: ...

_AllowMissingType = NewType("_AllowMissingType", object)
ALLOW_MISSING: _AllowMissingType
if sys.version_info >= (3, 15):
    _AllButLastType = NewType("_AllButLastType", object)
    ALL_BUT_LAST: _AllButLastType
