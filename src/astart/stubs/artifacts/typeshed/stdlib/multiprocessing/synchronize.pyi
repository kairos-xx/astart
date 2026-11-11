import sys
import threading
from collections.abc import Callable
from multiprocessing.context import BaseContext
from types import TracebackType

__all__ = [
    "BoundedSemaphore",
    "Condition",
    "Event",
    "Lock",
    "RLock",
    "Semaphore",
]
type _LockLike = Lock | RLock

class Barrier(threading.Barrier):
    def __init__(
        self,
        parties: int,
        action: Callable[[], object] | None = None,
        timeout: float | None = None,
        *,
        ctx: BaseContext,
    ) -> None: ...

class Condition:
    def __init__(
        self,
        lock: _LockLike | None = None,
        *,
        ctx: BaseContext,
    ) -> None: ...
    def notify(self, n: int = 1) -> None: ...
    def notify_all(self) -> None: ...
    def wait(self, timeout: float | None = None) -> bool: ...
    def wait_for(
        self,
        predicate: Callable[[], bool],
        timeout: float | None = None,
    ) -> bool: ...
    def __enter__(self) -> bool: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
        /,
    ) -> None: ...
    def acquire(
        self,
        block: bool = True,
        timeout: float | None = None,
    ) -> bool: ...
    def release(self) -> None: ...

class Event:
    def __init__(self, *, ctx: BaseContext) -> None: ...
    def is_set(self) -> bool: ...
    def set(self) -> None: ...
    def clear(self) -> None: ...
    def wait(self, timeout: float | None = None) -> bool: ...

class SemLock:
    def __init__(
        self,
        kind: int,
        value: int,
        maxvalue: int,
        *,
        ctx: BaseContext | None,
    ) -> None: ...
    def __enter__(self) -> bool: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
        /,
    ) -> None: ...
    def acquire(
        self,
        block: bool = True,
        timeout: float | None = None,
    ) -> bool: ...
    def release(self) -> None: ...
    if sys.version_info >= (3, 14):
        def locked(self) -> bool: ...

class Lock(SemLock):
    def __init__(self, *, ctx: BaseContext) -> None: ...

class RLock(SemLock):
    def __init__(self, *, ctx: BaseContext) -> None: ...

class Semaphore(SemLock):
    def __init__(self, value: int = 1, *, ctx: BaseContext) -> None: ...
    def get_value(self) -> int: ...

class BoundedSemaphore(Semaphore):
    def __init__(self, value: int = 1, *, ctx: BaseContext) -> None: ...
