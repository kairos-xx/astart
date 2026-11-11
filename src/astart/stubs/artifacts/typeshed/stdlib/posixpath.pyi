import sys
from collections.abc import Iterable
from genericpath import (
    ALLOW_MISSING as ALLOW_MISSING,
)
from genericpath import (
    _AllowMissingType,
)
from genericpath import (
    commonprefix as commonprefix,
)
from genericpath import (
    exists as exists,
)
from genericpath import (
    getatime as getatime,
)
from genericpath import (
    getctime as getctime,
)
from genericpath import (
    getmtime as getmtime,
)
from genericpath import (
    getsize as getsize,
)
from genericpath import (
    isdir as isdir,
)
from genericpath import (
    isfile as isfile,
)
from genericpath import (
    samefile as samefile,
)
from genericpath import (
    sameopenfile as sameopenfile,
)
from genericpath import (
    samestat as samestat,
)

from _typeshed import (
    AnyOrLiteralStr,
    BytesPath,
    FileDescriptorOrPath,
    StrOrBytesPath,
    StrPath,
)

if sys.version_info >= (3, 15):
    from genericpath import ALL_BUT_LAST as ALL_BUT_LAST
from genericpath import isdevdrive as isdevdrive
from os import PathLike
from typing import AnyStr, LiteralString, overload

__all__ = [
    "abspath",
    "altsep",
    "basename",
    "commonpath",
    "commonprefix",
    "curdir",
    "defpath",
    "devnull",
    "dirname",
    "exists",
    "expanduser",
    "expandvars",
    "extsep",
    "getatime",
    "getctime",
    "getmtime",
    "getsize",
    "isabs",
    "isdir",
    "isfile",
    "islink",
    "ismount",
    "join",
    "lexists",
    "normcase",
    "normpath",
    "pardir",
    "pathsep",
    "realpath",
    "relpath",
    "samefile",
    "sameopenfile",
    "samestat",
    "sep",
    "split",
    "splitdrive",
    "splitext",
    "supports_unicode_filenames",
]
__all__ += ["ALLOW_MISSING"]
if sys.version_info >= (3, 15):
    __all__ += ["ALL_BUT_LAST"]
__all__ += ["isjunction", "splitroot"]
__all__ += ["isdevdrive"]
supports_unicode_filenames: bool
curdir: LiteralString
pardir: LiteralString
sep: LiteralString
altsep: LiteralString | None
extsep: LiteralString
pathsep: LiteralString
defpath: LiteralString
devnull: LiteralString

@overload
def abspath[AnyStr: (bytes, str)](path: PathLike[AnyStr]) -> AnyStr: ...
@overload
def abspath[AnyStr: (bytes, str)](path: AnyStr) -> AnyStr: ...

if sys.version_info >= (3, 15):
    @overload
    def basename[AnyStr: (bytes, str)](p: PathLike[AnyStr], /) -> AnyStr: ...
    @overload
    def basename(p: AnyOrLiteralStr, /) -> AnyOrLiteralStr: ...
    @overload
    def dirname[AnyStr: (bytes, str)](p: PathLike[AnyStr], /) -> AnyStr: ...
    @overload
    def dirname(p: AnyOrLiteralStr, /) -> AnyOrLiteralStr: ...
else:
    @overload
    def basename[AnyStr: (bytes, str)](p: PathLike[AnyStr]) -> AnyStr: ...
    @overload
    def basename(p: AnyOrLiteralStr) -> AnyOrLiteralStr: ...
    @overload
    def dirname[AnyStr: (bytes, str)](p: PathLike[AnyStr]) -> AnyStr: ...
    @overload
    def dirname(p: AnyOrLiteralStr) -> AnyOrLiteralStr: ...

@overload
def expanduser[AnyStr: (bytes, str)](path: PathLike[AnyStr]) -> AnyStr: ...
@overload
def expanduser[AnyStr: (bytes, str)](path: AnyStr) -> AnyStr: ...
@overload
def expandvars[AnyStr: (bytes, str)](path: PathLike[AnyStr]) -> AnyStr: ...
@overload
def expandvars[AnyStr: (bytes, str)](path: AnyStr) -> AnyStr: ...

if sys.version_info >= (3, 15):
    @overload
    def normcase[AnyStr: (bytes, str)](s: PathLike[AnyStr], /) -> AnyStr: ...
    @overload
    def normcase(s: AnyOrLiteralStr, /) -> AnyOrLiteralStr: ...
else:
    @overload
    def normcase[AnyStr: (bytes, str)](s: PathLike[AnyStr]) -> AnyStr: ...
    @overload
    def normcase(s: AnyOrLiteralStr) -> AnyOrLiteralStr: ...

@overload
def normpath[AnyStr: (bytes, str)](path: PathLike[AnyStr]) -> AnyStr: ...
@overload
def normpath(path: AnyOrLiteralStr) -> AnyOrLiteralStr: ...
@overload
def commonpath(paths: Iterable[LiteralString]) -> LiteralString: ...
@overload
def commonpath(paths: Iterable[StrPath]) -> str: ...
@overload
def commonpath(paths: Iterable[BytesPath]) -> bytes: ...
@overload
def join(a: LiteralString, /, *paths: LiteralString) -> LiteralString: ...
@overload
def join(a: StrPath, /, *paths: StrPath) -> str: ...
@overload
def join(a: BytesPath, /, *paths: BytesPath) -> bytes: ...

if sys.version_info >= (3, 15):
    @overload
    def realpath[AnyStr: (bytes, str)](
        filename: PathLike[AnyStr],
        /,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
    @overload
    def realpath[AnyStr: (bytes, str)](
        filename: AnyStr,
        /,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
else:
    @overload
    def realpath[AnyStr: (bytes, str)](
        filename: PathLike[AnyStr],
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
    @overload
    def realpath[AnyStr: (bytes, str)](
        filename: AnyStr,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...

@overload
def relpath(
    path: LiteralString,
    start: LiteralString | None = None,
) -> LiteralString: ...
@overload
def relpath(path: BytesPath, start: BytesPath | None = None) -> bytes: ...
@overload
def relpath(path: StrPath, start: StrPath | None = None) -> str: ...

if sys.version_info >= (3, 15):
    @overload
    def split[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
        /,
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def split(
        p: AnyOrLiteralStr,
        /,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...
    @overload
    def splitdrive[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
        /,
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def splitdrive(
        p: AnyOrLiteralStr,
        /,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...
else:
    @overload
    def split[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def split(
        p: AnyOrLiteralStr,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...
    @overload
    def splitdrive[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def splitdrive(
        p: AnyOrLiteralStr,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...

if sys.version_info >= (3, 15):
    @overload
    def splitext[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
        /,
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def splitext(
        p: AnyOrLiteralStr,
        /,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...
else:
    @overload
    def splitext[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
    ) -> tuple[AnyStr, AnyStr]: ...
    @overload
    def splitext(
        p: AnyOrLiteralStr,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr]: ...

if sys.version_info >= (3, 15):
    def isabs(s: StrOrBytesPath, /) -> bool: ...
else:
    def isabs(s: StrOrBytesPath) -> bool: ...

def islink(path: FileDescriptorOrPath) -> bool: ...
def ismount(path: FileDescriptorOrPath) -> bool: ...
def lexists(path: FileDescriptorOrPath) -> bool: ...
def isjunction(path: StrOrBytesPath) -> bool: ...

if sys.version_info >= (3, 15):
    @overload
    def splitroot(
        path: AnyOrLiteralStr,
        /,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr, AnyOrLiteralStr]: ...
    @overload
    def splitroot[AnyStr: (bytes, str)](
        path: PathLike[AnyStr],
        /,
    ) -> tuple[AnyStr, AnyStr, AnyStr]: ...
else:
    @overload
    def splitroot(
        p: AnyOrLiteralStr,
    ) -> tuple[AnyOrLiteralStr, AnyOrLiteralStr, AnyOrLiteralStr]: ...
    @overload
    def splitroot[AnyStr: (bytes, str)](
        p: PathLike[AnyStr],
    ) -> tuple[AnyStr, AnyStr, AnyStr]: ...
