from asyncio import AbstractEventLoop
from collections.abc import Callable
from concurrent.futures import Executor
from functools import _SingleDispatchCallable
from typing import Any, Literal, overload

from _typeshed import (
    FileDescriptorOrPath,
    OpenBinaryMode,
    OpenBinaryModeReading,
    OpenBinaryModeUpdating,
    OpenBinaryModeWriting,
    OpenTextMode,
)

from ..base import AiofilesContextManager
from .binary import (
    AsyncBufferedIOBase,
    AsyncBufferedReader,
    AsyncFileIO,
    AsyncIndirectBufferedIOBase,
    _UnknownAsyncBinaryIO,
)
from .text import AsyncTextIndirectIOWrapper, AsyncTextIOWrapper

type _Opener = Callable[[str, int], int]

@overload
def open(
    file: FileDescriptorOrPath,
    mode: OpenTextMode = "r",
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener: _Opener | None = None,
    *,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncTextIOWrapper]: ...
@overload
def open(
    file: FileDescriptorOrPath,
    mode: OpenBinaryMode,
    buffering: Literal[0],
    encoding: None = None,
    errors: None = None,
    newline: None = None,
    closefd: bool = True,
    opener: _Opener | None = None,
    *,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncFileIO]: ...
@overload
def open(
    file: FileDescriptorOrPath,
    mode: OpenBinaryModeReading | OpenBinaryModeUpdating,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    errors: None = None,
    newline: None = None,
    closefd: bool = True,
    opener: _Opener | None = None,
    *,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedReader]: ...
@overload
def open(
    file: FileDescriptorOrPath,
    mode: OpenBinaryModeWriting,
    buffering: Literal[-1, 1] = -1,
    encoding: None = None,
    errors: None = None,
    newline: None = None,
    closefd: bool = True,
    opener: _Opener | None = None,
    *,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[AsyncBufferedIOBase]: ...
@overload
def open(
    file: FileDescriptorOrPath,
    mode: OpenBinaryMode,
    buffering: int = -1,
    encoding: None = None,
    errors: None = None,
    newline: None = None,
    closefd: bool = True,
    opener: _Opener | None = None,
    *,
    loop: AbstractEventLoop | None = None,
    executor: Executor | None = None,
) -> AiofilesContextManager[_UnknownAsyncBinaryIO]: ...

wrap: _SingleDispatchCallable[Any]
stdin: AsyncTextIndirectIOWrapper
stdout: AsyncTextIndirectIOWrapper
stderr: AsyncTextIndirectIOWrapper
stdin_bytes: AsyncIndirectBufferedIOBase
stdout_bytes: AsyncIndirectBufferedIOBase
stderr_bytes: AsyncIndirectBufferedIOBase
__all__ = (
    "open",
    "stderr",
    "stderr_bytes",
    "stdin",
    "stdin_bytes",
    "stdout",
    "stdout_bytes",
)
