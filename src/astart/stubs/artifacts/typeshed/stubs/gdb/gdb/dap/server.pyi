import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, TypeVar, type_check_only

from _typeshed import Incomplete, SupportsReadline, Unused

from .io import _SupportsReadAndReadlineBytes, _SupportsWriteAndFlushBytes
from .startup import DAPQueue

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])
type _RequestID = int
type _EventBody = Any
type _JSONValue = Any

class NotStoppedException(Exception): ...

class CancellationHandler:
    lock: threading.Lock
    reqs: list[_RequestID]
    in_flight_dap_thread: _RequestID | None
    in_flight_gdb_thread: _RequestID | None
    def starting(self, req: _RequestID) -> None: ...
    def done(self, req: _RequestID) -> None: ...
    def cancel(self, req: _RequestID) -> None: ...
    def interruptable_region(
        self,
        req: _RequestID | None,
    ) -> AbstractContextManager[None]: ...

class Server:
    in_stream: _SupportsReadAndReadlineBytes
    out_stream: _SupportsWriteAndFlushBytes
    child_stream: SupportsReadline[str]
    delay_events: list[tuple[str, _EventBody]]
    write_queue: DAPQueue[_JSONValue | None]
    read_queue: DAPQueue[_JSONValue | None]
    done: bool
    canceller: CancellationHandler
    config: dict[str, Incomplete]
    def __init__(
        self,
        in_stream: _SupportsReadAndReadlineBytes,
        out_stream: _SupportsWriteAndFlushBytes,
        child_stream: SupportsReadline[str],
    ) -> None: ...
    def main_loop(self) -> None: ...
    def send_event(
        self,
        event: str,
        body: _EventBody | None = None,
    ) -> None: ...
    def send_event_later(
        self,
        event: str,
        body: _EventBody | None = None,
    ) -> None: ...
    def shutdown(self) -> None: ...

def send_event(event: str, body: _EventBody | None = None) -> None: ...
@type_check_only
class _Wrapper:
    def __call__(self, func: _F) -> _F: ...

def request(
    name: str,
    *,
    response: bool = True,
    on_dap_thread: bool = False,
    expect_stopped: bool = True,
) -> _Wrapper: ...
def capability(name: str, value: bool = True) -> _Wrapper: ...
def client_bool_capability(name: str) -> bool: ...
def initialize(**args) -> dict[str, bool]: ...
def terminate(**args: Unused) -> None: ...
def disconnect(*, terminateDebuggee: bool = False, **args: Unused): ...
def cancel(**args: Unused) -> None: ...

class Invoker:
    cmd: str
    def __init__(self, cmd: str) -> None: ...
    def __call__(self) -> None: ...

class Cancellable[T]:
    fn: Callable[[], _T]
    result_q: DAPQueue[_T] | None
    req: _RequestID
    def __init__(
        self,
        fn: Callable[[], _T],
        result_q: DAPQueue[_T] | None = None,
    ) -> None: ...
    def __call__(self) -> None: ...

def send_gdb(cmd: str | Callable[[], object]) -> None: ...
def send_gdb_with_response[T](fn: str | Callable[[], _T]) -> _T: ...
