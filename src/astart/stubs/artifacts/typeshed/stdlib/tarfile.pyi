import bz2
import io
import sys
from builtins import list as _list
from collections.abc import Callable, Iterable, Iterator, Mapping
from gzip import (
    _ReadableFileobj as _GzipReadableFileobj,
)
from gzip import (
    _WritableFileobj as _GzipWritableFileobj,
)
from types import TracebackType
from typing import (
    IO,
    ClassVar,
    Final,
    Literal,
    Protocol,
    Self,
    overload,
    type_check_only,
)
from warnings import deprecated

from _typeshed import (
    ReadableBuffer,
    StrOrBytesPath,
    StrPath,
    SupportsRead,
    WriteableBuffer,
)

if sys.version_info >= (3, 14):
    from compression.zstd import ZstdDict
__all__ = [
    "DEFAULT_FORMAT",
    "ENCODING",
    "GNU_FORMAT",
    "PAX_FORMAT",
    "USTAR_FORMAT",
    "CompressionError",
    "ExtractError",
    "HeaderError",
    "ReadError",
    "StreamError",
    "TarError",
    "TarFile",
    "TarInfo",
    "is_tarfile",
    "open",
]
__all__ += [
    "AbsoluteLinkError",
    "AbsolutePathError",
    "FilterError",
    "LinkOutsideDestinationError",
    "OutsideDestinationError",
    "SpecialFileError",
    "data_filter",
    "fully_trusted_filter",
    "tar_filter",
]
__all__ += ["LinkFallbackError"]
type _FilterFunction = Callable[[TarInfo, str], TarInfo | None]
type _TarfileFilter = Literal["fully_trusted", "tar", "data"] | _FilterFunction

@type_check_only
class _Fileobj(Protocol):
    def read(self, size: int, /) -> bytes: ...
    def write(self, b: bytes, /) -> object: ...
    def tell(self) -> int: ...
    def seek(self, pos: int, /) -> object: ...
    def close(self) -> object: ...

@type_check_only
class _Bz2ReadableFileobj(bz2._ReadableFileobj):
    def close(self) -> object: ...

@type_check_only
class _Bz2WritableFileobj(bz2._WritableFileobj):
    def close(self) -> object: ...

NUL: Final = b"\0"
BLOCKSIZE: Final = 512
RECORDSIZE: Final = 10240
GNU_MAGIC: Final = b"ustar  \0"
POSIX_MAGIC: Final = b"ustar\x0000"
LENGTH_NAME: Final = 100
LENGTH_LINK: Final = 100
LENGTH_PREFIX: Final = 155
REGTYPE: Final = b"0"
AREGTYPE: Final = b"\0"
LNKTYPE: Final = b"1"
SYMTYPE: Final = b"2"
CHRTYPE: Final = b"3"
BLKTYPE: Final = b"4"
DIRTYPE: Final = b"5"
FIFOTYPE: Final = b"6"
CONTTYPE: Final = b"7"
GNUTYPE_LONGNAME: Final = b"L"
GNUTYPE_LONGLINK: Final = b"K"
GNUTYPE_SPARSE: Final = b"S"
XHDTYPE: Final = b"x"
XGLTYPE: Final = b"g"
SOLARIS_XHDTYPE: Final = b"X"
type _TarFormat = Literal[0, 1, 2]
USTAR_FORMAT: Final = 0
GNU_FORMAT: Final = 1
PAX_FORMAT: Final = 2
DEFAULT_FORMAT: Final = PAX_FORMAT
SUPPORTED_TYPES: Final[tuple[bytes, ...]]
REGULAR_TYPES: Final[tuple[bytes, ...]]
GNU_TYPES: Final[tuple[bytes, ...]]
PAX_FIELDS: Final[tuple[str, ...]]
PAX_NUMBER_FIELDS: Final[dict[str, type]]
PAX_NAME_FIELDS: Final[set[str]]
ENCODING: Final[str]

class ExFileObject(io.BufferedReader):
    def __init__(self, tarfile: TarFile, tarinfo: TarInfo) -> None: ...

class TarFile:
    OPEN_METH: ClassVar[Mapping[str, str]]
    name: StrOrBytesPath | None
    mode: Literal["r", "a", "w", "x"]
    fileobj: _Fileobj
    format: _TarFormat
    tarinfo: type[TarInfo]
    dereference: bool
    ignore_zeros: bool
    encoding: str
    errors: str
    fileobject: type[ExFileObject]
    pax_headers: Mapping[str, str]
    debug: Literal[0, 1, 2, 3]
    errorlevel: Literal[0, 1, 2]
    offset: int
    extraction_filter: _FilterFunction | None
    stream: bool
    if sys.version_info >= (3, 15):
        def __init__(
            self,
            name: StrOrBytesPath | None = None,
            mode: Literal["r", "a", "w", "x"] = "r",
            fileobj: _Fileobj | None = None,
            format: int | None = None,
            tarinfo: type[TarInfo] | None = None,
            dereference: bool | None = None,
            ignore_zeros: bool | None = None,
            encoding: str | None = None,
            errors: str = "surrogateescape",
            pax_headers: Mapping[str, str] | None = None,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
            copybufsize: int | None = None,
            stream: bool = False,
            mtime: float | None = None,
        ) -> None: ...
    else:
        def __init__(
            self,
            name: StrOrBytesPath | None = None,
            mode: Literal["r", "a", "w", "x"] = "r",
            fileobj: _Fileobj | None = None,
            format: int | None = None,
            tarinfo: type[TarInfo] | None = None,
            dereference: bool | None = None,
            ignore_zeros: bool | None = None,
            encoding: str | None = None,
            errors: str = "surrogateescape",
            pax_headers: Mapping[str, str] | None = None,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
            copybufsize: int | None = None,
            stream: bool = False,
        ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def __iter__(self) -> Iterator[TarInfo]: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None = None,
        mode: Literal["r", "r:*", "r:", "r:gz", "r:bz2", "r:xz"] = "r",
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    if sys.version_info >= (3, 14):
        @overload
        @classmethod
        def open(
            cls,
            name: StrOrBytesPath | None,
            mode: Literal["r:zst"],
            fileobj: _Fileobj | None = None,
            bufsize: int = 10240,
            *,
            format: int | None = ...,
            tarinfo: type[TarInfo] | None = ...,
            dereference: bool | None = ...,
            ignore_zeros: bool | None = ...,
            encoding: str | None = ...,
            errors: str = ...,
            pax_headers: Mapping[str, str] | None = ...,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
            level: None = None,
            options: Mapping[int, int] | None = None,
            zstd_dict: ZstdDict | tuple[ZstdDict, int] | None = None,
        ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["x", "x:", "a", "a:", "w", "w:", "w:tar"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None = None,
        *,
        mode: Literal["x", "x:", "a", "a:", "w", "w:", "w:tar"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["x:gz", "x:bz2", "w:gz", "w:bz2"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        compresslevel: int = 9,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None = None,
        *,
        mode: Literal["x:gz", "x:bz2", "w:gz", "w:bz2"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        compresslevel: int = 9,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["x:xz", "w:xz"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        preset: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] | None = ...,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | None = None,
        *,
        mode: Literal["x:xz", "w:xz"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        preset: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9] | None = ...,
    ) -> Self: ...
    if sys.version_info >= (3, 14):
        @overload
        @classmethod
        def open(
            cls,
            name: StrOrBytesPath | None,
            mode: Literal["x:zst", "w:zst"],
            fileobj: _Fileobj | None = None,
            bufsize: int = 10240,
            *,
            format: int | None = ...,
            tarinfo: type[TarInfo] | None = ...,
            dereference: bool | None = ...,
            ignore_zeros: bool | None = ...,
            encoding: str | None = ...,
            errors: str = ...,
            pax_headers: Mapping[str, str] | None = ...,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
            options: Mapping[int, int] | None = None,
            zstd_dict: ZstdDict | tuple[ZstdDict, int] | None = None,
        ) -> Self: ...
        @overload
        @classmethod
        def open(
            cls,
            name: StrOrBytesPath | None = None,
            *,
            mode: Literal["x:zst", "w:zst"],
            fileobj: _Fileobj | None = None,
            bufsize: int = 10240,
            format: int | None = ...,
            tarinfo: type[TarInfo] | None = ...,
            dereference: bool | None = ...,
            ignore_zeros: bool | None = ...,
            encoding: str | None = ...,
            errors: str = ...,
            pax_headers: Mapping[str, str] | None = ...,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
            options: Mapping[int, int] | None = None,
            zstd_dict: ZstdDict | tuple[ZstdDict, int] | None = None,
        ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | ReadableBuffer | None,
        mode: Literal["r|*", "r|", "r|gz", "r|bz2", "r|xz", "r|zst"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | ReadableBuffer | None = None,
        *,
        mode: Literal["r|*", "r|", "r|gz", "r|bz2", "r|xz", "r|zst"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | WriteableBuffer | None,
        mode: Literal["w|", "w|xz", "w|zst"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | WriteableBuffer | None = None,
        *,
        mode: Literal["w|", "w|xz", "w|zst"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | WriteableBuffer | None,
        mode: Literal["w|gz", "w|bz2"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        compresslevel: int = 9,
    ) -> Self: ...
    @overload
    @classmethod
    def open(
        cls,
        name: StrOrBytesPath | WriteableBuffer | None = None,
        *,
        mode: Literal["w|gz", "w|bz2"],
        fileobj: _Fileobj | None = None,
        bufsize: int = 10240,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        errors: str = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
        compresslevel: int = 9,
    ) -> Self: ...
    @classmethod
    def taropen(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["r", "a", "w", "x"] = "r",
        fileobj: _Fileobj | None = None,
        *,
        compresslevel: int = ...,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def gzopen(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["r"] = "r",
        fileobj: _GzipReadableFileobj | None = None,
        compresslevel: int = 9,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def gzopen(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["w", "x"],
        fileobj: _GzipWritableFileobj | None = None,
        compresslevel: int = 9,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def bz2open(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["w", "x"],
        fileobj: _Bz2WritableFileobj | None = None,
        compresslevel: int = 9,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def bz2open(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["r"] = "r",
        fileobj: _Bz2ReadableFileobj | None = None,
        compresslevel: int = 9,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    @classmethod
    def xzopen(
        cls,
        name: StrOrBytesPath | None,
        mode: Literal["r", "w", "x"] = "r",
        fileobj: IO[bytes] | None = None,
        preset: int | None = None,
        *,
        format: int | None = ...,
        tarinfo: type[TarInfo] | None = ...,
        dereference: bool | None = ...,
        ignore_zeros: bool | None = ...,
        encoding: str | None = ...,
        pax_headers: Mapping[str, str] | None = ...,
        debug: Literal[0, 1, 2, 3] | None = None,
        errorlevel: Literal[0, 1, 2] | None = None,
    ) -> Self: ...
    if sys.version_info >= (3, 14):
        @overload
        @classmethod
        def zstopen(
            cls,
            name: StrOrBytesPath | None,
            mode: Literal["r"] = "r",
            fileobj: IO[bytes] | None = None,
            level: None = None,
            options: Mapping[int, int] | None = None,
            zstd_dict: ZstdDict | tuple[ZstdDict, int] | None = None,
            *,
            format: int | None = ...,
            tarinfo: type[TarInfo] | None = ...,
            dereference: bool | None = ...,
            ignore_zeros: bool | None = ...,
            encoding: str | None = ...,
            pax_headers: Mapping[str, str] | None = ...,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
        ) -> Self: ...
        @overload
        @classmethod
        def zstopen(
            cls,
            name: StrOrBytesPath | None,
            mode: Literal["w", "x"],
            fileobj: IO[bytes] | None = None,
            level: int | None = None,
            options: Mapping[int, int] | None = None,
            zstd_dict: ZstdDict | tuple[ZstdDict, int] | None = None,
            *,
            format: int | None = ...,
            tarinfo: type[TarInfo] | None = ...,
            dereference: bool | None = ...,
            ignore_zeros: bool | None = ...,
            encoding: str | None = ...,
            pax_headers: Mapping[str, str] | None = ...,
            debug: Literal[0, 1, 2, 3] | None = None,
            errorlevel: Literal[0, 1, 2] | None = None,
        ) -> Self: ...
    def getmember(self, name: str) -> TarInfo: ...
    def getmembers(self) -> _list[TarInfo]: ...
    def getnames(self) -> _list[str]: ...
    def list(
        self,
        verbose: bool = True,
        *,
        members: Iterable[TarInfo] | None = None,
    ) -> None: ...
    def next(self) -> TarInfo | None: ...
    def extractall(
        self,
        path: StrOrBytesPath = ".",
        members: Iterable[TarInfo] | None = None,
        *,
        numeric_owner: bool = False,
        filter: _TarfileFilter | None = None,
    ) -> None: ...
    def extract(
        self,
        member: str | TarInfo,
        path: StrOrBytesPath = "",
        set_attrs: bool = True,
        *,
        numeric_owner: bool = False,
        filter: _TarfileFilter | None = None,
    ) -> None: ...
    def _extract_member(
        self,
        tarinfo: TarInfo,
        targetpath: str,
        set_attrs: bool = True,
        numeric_owner: bool = False,
        *,
        filter_function: _FilterFunction | None = None,
        extraction_root: str | None = None,
    ) -> None: ...
    def extractfile(self, member: str | TarInfo) -> IO[bytes] | None: ...
    def makedir(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makefile(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makeunknown(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makefifo(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makedev(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makelink(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
    ) -> None: ...
    def makelink_with_filter(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
        filter_function: _FilterFunction,
        extraction_root: str,
    ) -> None: ...
    def chown(
        self,
        tarinfo: TarInfo,
        targetpath: StrOrBytesPath,
        numeric_owner: bool,
    ) -> None: ...
    def chmod(self, tarinfo: TarInfo, targetpath: StrOrBytesPath) -> None: ...
    def utime(self, tarinfo: TarInfo, targetpath: StrOrBytesPath) -> None: ...
    def add(
        self,
        name: StrPath,
        arcname: StrPath | None = None,
        recursive: bool = True,
        *,
        filter: Callable[[TarInfo], TarInfo | None] | None = None,
    ) -> None: ...
    def addfile(
        self,
        tarinfo: TarInfo,
        fileobj: SupportsRead[bytes] | None = None,
    ) -> None: ...
    def gettarinfo(
        self,
        name: StrOrBytesPath | None = None,
        arcname: str | None = None,
        fileobj: IO[bytes] | None = None,
    ) -> TarInfo: ...
    def close(self) -> None: ...

open = TarFile.open

def is_tarfile(name: StrOrBytesPath | IO[bytes]) -> bool: ...

class TarError(Exception): ...
class ReadError(TarError): ...
class CompressionError(TarError): ...
class StreamError(TarError): ...
class ExtractError(TarError): ...
class HeaderError(TarError): ...

class FilterError(TarError):
    tarinfo: TarInfo

class AbsolutePathError(FilterError):
    def __init__(self, tarinfo: TarInfo) -> None: ...

class OutsideDestinationError(FilterError):
    def __init__(self, tarinfo: TarInfo, path: str) -> None: ...

class SpecialFileError(FilterError):
    def __init__(self, tarinfo: TarInfo) -> None: ...

class AbsoluteLinkError(FilterError):
    def __init__(self, tarinfo: TarInfo) -> None: ...

class LinkOutsideDestinationError(FilterError):
    def __init__(self, tarinfo: TarInfo, path: str) -> None: ...

class LinkFallbackError(FilterError):
    def __init__(self, tarinfo: TarInfo, path: str) -> None: ...

def fully_trusted_filter(member: TarInfo, dest_path: str) -> TarInfo: ...
def tar_filter(member: TarInfo, dest_path: str) -> TarInfo: ...
def data_filter(member: TarInfo, dest_path: str) -> TarInfo: ...

class TarInfo:
    __slots__ = (
        "_link_target",
        "_sparse_structs",
        "_tarfile",
        "chksum",
        "devmajor",
        "devminor",
        "gid",
        "gname",
        "linkname",
        "mode",
        "mtime",
        "name",
        "offset",
        "offset_data",
        "pax_headers",
        "size",
        "sparse",
        "type",
        "uid",
        "uname",
    )
    name: str
    path: str
    size: int
    mtime: int | float
    chksum: int
    devmajor: int
    devminor: int
    offset: int
    offset_data: int
    sparse: bytes | None
    mode: int
    type: bytes
    linkname: str
    uid: int
    gid: int
    uname: str
    gname: str
    pax_headers: Mapping[str, str]
    def __init__(self, name: str = "") -> None: ...
    @property
    @deprecated(
        "Deprecated since Python 3.13; will be removed in Python 3.16.",
    )
    def tarfile(self) -> TarFile | None: ...
    @tarfile.setter
    @deprecated(
        "Deprecated since Python 3.13; will be removed in Python 3.16.",
    )
    def tarfile(self, tarfile: TarFile | None) -> None: ...
    @classmethod
    def frombuf(
        cls,
        buf: bytes | bytearray,
        encoding: str,
        errors: str,
    ) -> Self: ...
    @classmethod
    def fromtarfile(cls, tarfile: TarFile) -> Self: ...
    @property
    def linkpath(self) -> str: ...
    @linkpath.setter
    def linkpath(self, linkname: str) -> None: ...
    def replace(
        self,
        *,
        name: str = ...,
        mtime: float = ...,
        mode: int = ...,
        linkname: str = ...,
        uid: int = ...,
        gid: int = ...,
        uname: str = ...,
        gname: str = ...,
        deep: bool = True,
    ) -> Self: ...
    def get_info(
        self,
    ) -> Mapping[str, str | int | bytes | Mapping[str, str]]: ...
    def tobuf(
        self,
        format: _TarFormat | None = 2,
        encoding: str | None = "utf-8",
        errors: str = "surrogateescape",
    ) -> bytes: ...
    def create_ustar_header(
        self,
        info: Mapping[str, str | int | bytes | Mapping[str, str]],
        encoding: str,
        errors: str,
    ) -> bytes: ...
    def create_gnu_header(
        self,
        info: Mapping[str, str | int | bytes | Mapping[str, str]],
        encoding: str,
        errors: str,
    ) -> bytes: ...
    def create_pax_header(
        self,
        info: Mapping[str, str | int | bytes | Mapping[str, str]],
        encoding: str,
    ) -> bytes: ...
    @classmethod
    def create_pax_global_header(
        cls,
        pax_headers: Mapping[str, str],
    ) -> bytes: ...
    def isfile(self) -> bool: ...
    def isreg(self) -> bool: ...
    def issparse(self) -> bool: ...
    def isdir(self) -> bool: ...
    def issym(self) -> bool: ...
    def islnk(self) -> bool: ...
    def ischr(self) -> bool: ...
    def isblk(self) -> bool: ...
    def isfifo(self) -> bool: ...
    def isdev(self) -> bool: ...
