import _thread
import sys
from _thread import _ExceptHookArgs
from _thread import get_native_id as get_native_id
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextvars import Context
from types import TracebackType
from typing import Any, Final, Self, TypeVar, final
from warnings import deprecated

from _typeshed import ProfileFunction, TraceFunction

_T = TypeVar("_T")
__all__ = [
    "TIMEOUT_MAX",
    "Barrier",
    "BoundedSemaphore",
    "BrokenBarrierError",
    "Condition",
    "Event",
    "ExceptHookArgs",
    "Lock",
    "RLock",
    "Semaphore",
    "Thread",
    "ThreadError",
    "Timer",
    "active_count",
    "current_thread",
    "enumerate",
    "excepthook",
    "get_ident",
    "get_native_id",
    "getprofile",
    "gettrace",
    "local",
    "main_thread",
    "setprofile",
    "settrace",
    "stack_size",
]
__all__ += ["setprofile_all_threads", "settrace_all_threads"]
if sys.version_info >= (3, 15):
    __all__ += [
        "concurrent_tee",
        "serialize_iterator",
        "synchronized_iterator",
    ]
_profile_hook: ProfileFunction | None

def active_count() -> int: ...
@deprecated("Deprecated since Python 3.10. Use `active_count()` instead.")
def activeCount() -> int: ...
def current_thread() -> Thread: ...
@deprecated("Deprecated since Python 3.10. Use `current_thread()` instead.")
def currentThread() -> Thread: ...
def get_ident() -> int: ...
def enumerate() -> list[Thread]: ...
def main_thread() -> Thread: ...
def settrace(func: TraceFunction | None) -> None: ...
def setprofile(func: ProfileFunction | None) -> None: ...
def setprofile_all_threads(func: ProfileFunction | None) -> None: ...
def settrace_all_threads(func: TraceFunction | None) -> None: ...
def gettrace() -> TraceFunction | None: ...
def getprofile() -> ProfileFunction | None: ...

if sys.version_info >= (3, 15):
    @final
    class serialize_iterator(Iterator[_T]):
        def __init__(self, iterable: Iterable[_T]) -> None: ...
        def __iter__(self) -> Self: ...
        def __next__(self) -> _T: ...
        def send(self, value: Any, /) -> _T: ...
        def throw(
            self,
            typ: type[BaseException],
            val: BaseException | object = ...,
            tb: TracebackType | None = ...,
        ) -> _T: ...
        def close(self) -> None: ...

    def synchronized_iterator[T](
        func: Callable[..., Iterable[_T]],
    ) -> Callable[..., Iterator[_T]]: ...
    def concurrent_tee[T](
        iterable: Iterable[_T],
        n: int = 2,
    ) -> tuple[Iterator[_T], ...]: ...

def stack_size(size: int = 0, /) -> int: ...

TIMEOUT_MAX: Final[float]
ThreadError = _thread.error
local = _thread._local

class Thread:
    name: str
    @property
    def ident(self) -> int | None: ...
    daemon: bool
    if sys.version_info >= (3, 14):
        def __init__(
            self,
            group: None = None,
            target: Callable[..., object] | None = None,
            name: str | None = None,
            args: Iterable[Any] = (),
            kwargs: Mapping[str, Any] | None = None,
            *,
            daemon: bool | None = None,
            context: Context | None = None,
        ) -> None: ...
    else:
        def __init__(
            self,
            group: None = None,
            target: Callable[..., object] | None = None,
            name: str | None = None,
            args: Iterable[Any] = (),
            kwargs: Mapping[str, Any] | None = None,
            *,
            daemon: bool | None = None,
        ) -> None: ...
    def start(self) -> None: ...
    def run(self) -> None: ...
    def join(self, timeout: float | None = None) -> None: ...
    @property
    def native_id(self) -> int | None: ...
    def is_alive(self) -> bool: ...
    @deprecated(
        "Deprecated since Python 3.10. Read the `daemon` attribute instead.",
    )
    def isDaemon(self) -> bool: ...
    @deprecated(
        "Deprecated since Python 3.10. Set the `daemon` attribute instead.",
    )
    def setDaemon(self, daemonic: bool) -> None: ...
    @deprecated(
        "Deprecated since Python 3.10. Read the `name` attribute instead.",
    )
    def getName(self) -> str: ...
    @deprecated(
        "Deprecated since Python 3.10. Set the `name` attribute instead.",
    )
    def setName(self, name: str) -> None: ...

class _DummyThread(Thread):
    def __init__(self) -> None: ...

Lock = _thread.LockType

@final
class _RLock:
    _count: int
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool: ...
    def release(self) -> None: ...
    __enter__ = acquire
    def __exit__(
        self,
        t: type[BaseException] | None,
        v: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    if sys.version_info >= (3, 14):
        def locked(self) -> bool: ...

RLock = _thread.RLock

class Condition:
    def __init__(self, lock: Lock | _RLock | RLock | None = None) -> None: ...
    def __enter__(self) -> bool: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool: ...
    def release(self) -> None: ...
    if sys.version_info >= (3, 14):
        def locked(self) -> bool: ...
    def wait(self, timeout: float | None = None) -> bool: ...
    def wait_for(
        self,
        predicate: Callable[[], _T],
        timeout: float | None = None,
    ) -> _T: ...
    def notify(self, n: int = 1) -> None: ...
    def notify_all(self) -> None: ...
    @deprecated("Deprecated since Python 3.10. Use `notify_all()` instead.")
    def notifyAll(self) -> None: ...

class Semaphore:
    _value: int
    def __init__(self, value: int = 1) -> None: ...
    def __exit__(
        self,
        t: type[BaseException] | None,
        v: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    def acquire(
        self,
        blocking: bool = True,
        timeout: float | None = None,
    ) -> bool: ...
    def __enter__(
        self,
        blocking: bool = True,
        timeout: float | None = None,
    ) -> bool: ...
    def release(self, n: int = 1) -> None: ...

class BoundedSemaphore(Semaphore): ...

class Event:
    def is_set(self) -> bool: ...
    @deprecated("Deprecated since Python 3.10. Use `is_set()` instead.")
    def isSet(self) -> bool: ...
    def set(self) -> None: ...
    def clear(self) -> None: ...
    def wait(self, timeout: float | None = None) -> bool: ...

excepthook: Callable[[_ExceptHookArgs], object]
__excepthook__: Callable[[_ExceptHookArgs], object]
ExceptHookArgs = _ExceptHookArgs

class Timer(Thread):
    args: Iterable[Any]
    finished: Event
    function: Callable[..., Any]
    interval: float
    kwargs: Mapping[str, Any]
    def __init__(
        self,
        interval: float,
        function: Callable[..., object],
        args: Iterable[Any] | None = None,
        kwargs: Mapping[str, Any] | None = None,
    ) -> None: ...
    def cancel(self) -> None: ...

class Barrier:
    @property
    def parties(self) -> int: ...
    @property
    def n_waiting(self) -> int: ...
    @property
    def broken(self) -> bool: ...
    def __init__(
        self,
        parties: int,
        action: Callable[[], None] | None = None,
        timeout: float | None = None,
    ) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...
    def reset(self) -> None: ...
    def abort(self) -> None: ...

class BrokenBarrierError(RuntimeError): ...
