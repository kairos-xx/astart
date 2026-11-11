import sys
from typing import Any

from gevent._fileobjectcommon import FileObjectBlock as FileObjectBlock
from gevent._fileobjectcommon import FileObjectThread as FileObjectThread

if sys.platform != "win32":
    import io
    from typing import IO, AnyStr, Literal, overload

    from _typeshed import (
        FileDescriptorOrPath,
        OpenBinaryMode,
        OpenBinaryModeReading,
        OpenBinaryModeUpdating,
        OpenBinaryModeWriting,
        OpenTextMode,
    )
    from gevent._fileobjectcommon import _IOT, FileObjectBase
    class FileObjectPosix(FileObjectBase[_IOT, AnyStr]):
        default_bufsize = io.DEFAULT_BUFFER_SIZE
        fileio: io.RawIOBase
        @overload
        def __init__(
            self: FileObjectPosix[io.TextIOWrapper, str],
            fobj: FileDescriptorOrPath,
            mode: OpenTextMode = "r",
            bufsize: int | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: int | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[io.FileIO, bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryMode,
            bufsize: Literal[0],
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: Literal[0] | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[io.FileIO, bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryMode,
            bufsize: Literal[0] | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            *,
            buffering: Literal[0],
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[io.BufferedRandom, bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryModeUpdating,
            bufsize: Literal[-1, 1] | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: Literal[-1, 1] | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[io.BufferedWriter, bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryModeWriting,
            bufsize: Literal[-1, 1] | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: Literal[-1, 1] | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[io.BufferedReader, bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryModeReading,
            bufsize: Literal[-1, 1] | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: Literal[-1, 1] | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[IO[bytes], bytes],
            fobj: FileDescriptorOrPath,
            mode: OpenBinaryMode,
            bufsize: int | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: int | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...
        @overload
        def __init__(
            self: FileObjectPosix[IO[Any], Any],
            fobj: FileDescriptorOrPath,
            mode: str,
            bufsize: int | None = None,
            close: bool | None = None,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
            buffering: int | None = None,
            closefd: bool | None = None,
            atomic_write: bool = False,
        ) -> None: ...

    type _FileObjectType = type[
        FileObjectPosix[Any, Any]
        | FileObjectBlock[Any, Any]
        | FileObjectThread[Any, Any]
    ]
    __all__ = [
        "FileObject",
        "FileObjectBlock",
        "FileObjectPosix",
        "FileObjectThread",
    ]
else:
    type _FileObjectType = type[
        FileObjectBlock[Any, Any] | FileObjectThread[Any, Any]
    ]
    __all__ = ["FileObject", "FileObjectBlock", "FileObjectThread"]
FileObject: _FileObjectType
