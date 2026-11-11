import socket
import sys
from collections.abc import Iterable
from types import TracebackType
from typing import Any, Generic, Self, SupportsIndex, TypeVar

from _typeshed import Incomplete, ReadableBuffer

__all__ = ["Client", "Listener", "Pipe", "wait"]
type _Address = str | tuple[str, int]
_SendT_contra = TypeVar("_SendT_contra", contravariant=True, default=Any)
_RecvT_co = TypeVar("_RecvT_co", covariant=True, default=Any)

class _ConnectionBase(Generic[_SendT_contra, _RecvT_co]):
    def __init__(
        self,
        handle: SupportsIndex,
        readable: bool = True,
        writable: bool = True,
    ) -> None: ...
    @property
    def closed(self) -> bool: ...
    @property
    def readable(self) -> bool: ...
    @property
    def writable(self) -> bool: ...
    def fileno(self) -> int: ...
    def close(self) -> None: ...
    def send_bytes(
        self,
        buf: ReadableBuffer,
        offset: int = 0,
        size: int | None = None,
    ) -> None: ...
    def send(self, obj: _SendT_contra) -> None: ...
    def recv_bytes(self, maxlength: int | None = None) -> bytes: ...
    def recv_bytes_into(self, buf: Any, offset: int = 0) -> int: ...
    def recv(self) -> _RecvT_co: ...
    def poll(self, timeout: float | None = 0.0) -> bool: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def __del__(self) -> None: ...

class Connection(_ConnectionBase[_SendT_contra, _RecvT_co]): ...

if sys.platform == "win32":
    class PipeConnection(_ConnectionBase[_SendT_contra, _RecvT_co]): ...

class Listener:
    def __init__(
        self,
        address: _Address | None = None,
        family: str | None = None,
        backlog: int = 1,
        authkey: bytes | None = None,
    ) -> None: ...
    if sys.platform != "win32":
        def accept(self) -> Connection[Incomplete, Incomplete]: ...
    else:
        def accept(
            self,
        ) -> (
            Connection[Incomplete, Incomplete]
            | PipeConnection[Incomplete, Incomplete]
        ): ...
    def close(self) -> None: ...
    @property
    def address(self) -> _Address: ...
    @property
    def last_accepted(self) -> _Address | None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

def deliver_challenge(
    connection: _ConnectionBase[Any, Any],
    authkey: bytes,
    digest_name: str = "sha256",
) -> None: ...
def answer_challenge(
    connection: _ConnectionBase[Any, Any],
    authkey: bytes,
) -> None: ...
def wait(
    object_list: Iterable[
        _ConnectionBase[_SendT_contra, _RecvT_co] | socket.socket | int
    ],
    timeout: float | None = None,
) -> list[_ConnectionBase[_SendT_contra, _RecvT_co] | socket.socket | int]: ...

if sys.platform != "win32":
    def Client(
        address: _Address,
        family: str | None = None,
        authkey: bytes | None = None,
    ) -> Connection[Any, Any]: ...
else:
    def Client(
        address: _Address,
        family: str | None = None,
        authkey: bytes | None = None,
    ) -> Connection[Any, Any] | PipeConnection[Any, Any]: ...

if sys.platform != "win32":
    def Pipe(
        duplex: bool = True,
    ) -> tuple[Connection[Any, Any], Connection[Any, Any]]: ...
else:
    def Pipe(
        duplex: bool = True,
    ) -> tuple[PipeConnection[Any, Any], PipeConnection[Any, Any]]: ...
