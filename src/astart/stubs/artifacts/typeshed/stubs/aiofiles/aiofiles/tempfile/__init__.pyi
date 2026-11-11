from asyncio import AbstractEventLoop
from concurrent.futures import Executor
from typing import AnyStr, Literal, overload

from _typeshed import (
    BytesPath,
    OpenBinaryMode,
    OpenBinaryModeReading,
    OpenBinaryModeUpdating,
    OpenBinaryModeWriting,
    OpenTextMode,
    StrOrBytesPath,
    StrPath,
)

from ..base import AiofilesContextManager
from ..threadpool.binary import (
    AsyncBufferedIOBase,
    AsyncBufferedReader,
    AsyncFileIO,
)
from ..threadpool.text import AsyncTextIOWrapper

@overload
def TemporaryFile(
    mode: OpenTextMode,
    buffering: int = -1,
    encoding: str | None = None,
    newline: str | None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncTextIOWrapper]: ...
@overload
def TemporaryFile(
    mode: OpenBinaryMode,
    buffering: Literal[0],
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncFileIO]: ...
@overload
def TemporaryFile(
    mode: OpenBinaryModeReading | OpenBinaryModeUpdating = "w+b",
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedReader]: ...
@overload
def TemporaryFile(
    mode: OpenBinaryModeWriting,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedIOBase]: ...
@overload
def NamedTemporaryFile(
    mode: OpenTextMode,
    buffering: int = -1,
    encoding: str | None = None,
    newline: str | None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    delete: bool = True,
    delete_on_close: bool = True,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncTextIOWrapper]: ...
@overload
def NamedTemporaryFile(
    mode: OpenBinaryMode,
    buffering: Literal[0],
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    delete: bool = True,
    delete_on_close: bool = True,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncFileIO]: ...
@overload
def NamedTemporaryFile(
    mode: OpenBinaryModeReading | OpenBinaryModeUpdating = "w+b",
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    delete: bool = True,
    delete_on_close: bool = True,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedReader]: ...
@overload
def NamedTemporaryFile(
    mode: OpenBinaryModeWriting,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    delete: bool = True,
    delete_on_close: bool = True,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedIOBase]: ...
@overload
def SpooledTemporaryFile(
    max_size: int = 0,
    *,
    mode: OpenTextMode,
    buffering: int = -1,
    encoding: str | None = None,
    newline: str | None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncTextIOWrapper]: ...
@overload
def SpooledTemporaryFile(
    max_size: int,
    mode: OpenTextMode,
    buffering: int = -1,
    encoding: str | None = None,
    newline: str | None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncTextIOWrapper]: ...
@overload
def SpooledTemporaryFile(
    max_size: int = 0,
    mode: OpenBinaryMode = "w+b",
    *,
    buffering: Literal[0],
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncFileIO]: ...
@overload
def SpooledTemporaryFile(
    max_size: int,
    mode: OpenBinaryMode,
    buffering: Literal[0],
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncFileIO]: ...
@overload
def SpooledTemporaryFile(
    max_size: int = 0,
    mode: OpenBinaryModeReading | OpenBinaryModeUpdating = "w+b",
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedReader]: ...
@overload
def SpooledTemporaryFile(
    max_size: int = 0,
    *,
    mode: OpenBinaryModeWriting,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedIOBase]: ...
@overload
def SpooledTemporaryFile(
    max_size: int,
    mode: OpenBinaryModeWriting,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    newline: None = None,
    suffix: AnyStr | None = None,
    prefix: AnyStr | None = None,
    dir: StrOrBytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedIOBase]: ...
@overload
def TemporaryDirectory(
    suffix: str | None = None,
    prefix: str | None = None,
    dir: StrPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManagerTempDir: ...
@overload
def TemporaryDirectory(
    suffix: bytes | None = None,
    prefix: bytes | None = None,
    dir: BytesPath | None = None,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManagerTempDir: ...

class AiofilesContextManagerTempDir(AiofilesContextManager[str]):
    async def __aenter__(self) -> str: ...

__all__ = [
    "NamedTemporaryFile",
    "SpooledTemporaryFile",
    "TemporaryDirectory",
    "TemporaryFile",
]
