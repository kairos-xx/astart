import sys
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
from genericpath import isdevdrive as isdevdrive
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
from os import PathLike
from posixpath import (
    abspath as abspath,
)
from posixpath import (
    basename as basename,
)
from posixpath import (
    commonpath as commonpath,
)
from posixpath import (
    curdir as curdir,
)
from posixpath import (
    defpath as defpath,
)
from posixpath import (
    devnull as devnull,
)
from posixpath import (
    dirname as dirname,
)
from posixpath import (
    expanduser as expanduser,
)
from posixpath import (
    expandvars as expandvars,
)
from posixpath import (
    extsep as extsep,
)
from posixpath import (
    isabs as isabs,
)
from posixpath import isjunction as isjunction
from posixpath import (
    islink as islink,
)
from posixpath import (
    ismount as ismount,
)
from posixpath import (
    lexists as lexists,
)
from posixpath import (
    normcase as normcase,
)
from posixpath import (
    normpath as normpath,
)
from posixpath import (
    pardir as pardir,
)
from posixpath import (
    pathsep as pathsep,
)
from posixpath import (
    relpath as relpath,
)
from posixpath import (
    sep as sep,
)
from posixpath import (
    split as split,
)
from posixpath import (
    splitdrive as splitdrive,
)
from posixpath import (
    splitext as splitext,
)
from posixpath import splitroot as splitroot
from posixpath import (
    supports_unicode_filenames as supports_unicode_filenames,
)
from typing import AnyStr, LiteralString, overload

from _typeshed import BytesPath, StrOrBytesPath, StrPath

if sys.version_info >= (3, 15):
    from genericpath import ALL_BUT_LAST as ALL_BUT_LAST
__all__ = [
    "ALLOW_MISSING",
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
__all__ += ["isjunction", "splitroot"]
__all__ += ["isdevdrive", "isreserved"]
if sys.version_info >= (3, 15):
    __all__ += ["ALL_BUT_LAST"]
altsep: LiteralString

@overload
def join(path: LiteralString, /, *paths: LiteralString) -> LiteralString: ...
@overload
def join(path: StrPath, /, *paths: StrPath) -> str: ...
@overload
def join(path: BytesPath, /, *paths: BytesPath) -> bytes: ...

if sys.version_info >= (3, 15):
    @overload
    def realpath[AnyStr: (bytes, str)](
        path: PathLike[AnyStr],
        /,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
    @overload
    def realpath[AnyStr: (bytes, str)](
        path: AnyStr,
        /,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
elif sys.platform == "win32":
    @overload
    def realpath[AnyStr: (bytes, str)](
        path: PathLike[AnyStr],
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
    @overload
    def realpath[AnyStr: (bytes, str)](
        path: AnyStr,
        *,
        strict: bool | _AllowMissingType = False,
    ) -> AnyStr: ...
else:
    realpath = abspath

def isreserved(path: StrOrBytesPath) -> bool: ...
