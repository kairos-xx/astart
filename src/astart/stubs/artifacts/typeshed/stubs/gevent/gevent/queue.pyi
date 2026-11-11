import types
from collections import deque
from collections.abc import Iterable
from queue import Empty as Empty
from queue import Full as Full
from typing import Any, Literal, Self, TypeVar, final, overload

from gevent._waiter import Waiter
from gevent.hub import Hub

__all__ = [
    "Channel",
    "Empty",
    "Full",
    "JoinableQueue",
    "LifoQueue",
    "PriorityQueue",
    "Queue",
    "ShutDown",
    "SimpleQueue",
]
from queue import ShutDown as ShutDown

_T = TypeVar("_T")

class SimpleQueue[T]:
    __slots__ = (
        "__weakref__",
        "_event_unlock",
        "_maxsize",
        "getters",
        "hub",
        "is_shutdown",
        "putters",
        "queue",
    )
    @property
    def hub(self) -> Hub: ...
    @property
    def queue(self) -> deque[_T]: ...
    maxsize: int | None
    is_shutdown: bool
    @classmethod
    def __class_getitem__(cls, item: Any, /) -> types.GenericAlias: ...
    @overload
    def __init__(self, maxsize: int | None = None) -> None: ...
    @overload
    def __init__(self, maxsize: int | None, items: Iterable[_T]) -> None: ...
    @overload
    def __init__(
        self,
        maxsize: int | None = None,
        *,
        items: Iterable[_T],
    ) -> None: ...
    def copy(self) -> Self: ...
    def empty(self) -> bool: ...
    def full(self) -> bool: ...
    def get(self, block: bool = True, timeout: float | None = None) -> _T: ...
    def get_nowait(self) -> _T: ...
    def peek(self, block: bool = True, timeout: float | None = None) -> _T: ...
    def peek_nowait(self) -> _T: ...
    def put(
        self,
        item: _T,
        block: bool = True,
        timeout: float | None = None,
    ) -> None: ...
    def put_nowait(self, item: _T) -> None: ...
    def qsize(self) -> int: ...
    def __bool__(self) -> bool: ...
    def __iter__(self) -> Self: ...
    def __len__(self) -> int: ...
    def __next__(self) -> _T: ...
    next = __next__

class Queue(SimpleQueue[_T]):
    __slots__ = ("_cond", "unfinished_tasks")
    @property
    def unfinished_tasks(self) -> int: ...
    @overload
    def __init__(
        self,
        maxsize: int | None = None,
        *,
        unfinished_tasks: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        maxsize: int | None,
        items: Iterable[_T],
        unfinished_tasks: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        maxsize: int | None = None,
        *,
        items: Iterable[_T],
        unfinished_tasks: int | None = None,
    ) -> None: ...
    def join(self, timeout: float | None = None) -> bool: ...
    def task_done(self) -> None: ...
    def shutdown(self, immediate: bool = False) -> None: ...

JoinableQueue = Queue

@final
class UnboundQueue(Queue[_T]):
    __slots__ = ()
    @overload
    def __init__(self, maxsize: None = None) -> None: ...
    @overload
    def __init__(self, maxsize: None, items: Iterable[_T]) -> None: ...
    @overload
    def __init__(
        self,
        maxsize: None = None,
        *,
        items: Iterable[_T],
    ) -> None: ...

class PriorityQueue(Queue[_T]):
    __slots__ = ()

class LifoQueue(Queue[_T]):
    __slots__ = ()

class Channel[T]:
    __slots__ = ("__weakref__", "_event_unlock", "getters", "hub", "putters")
    @property
    def getters(self) -> deque[Waiter[Any]]: ...
    @property
    def putters(self) -> deque[tuple[_T, Waiter[Any]]]: ...
    @property
    def hub(self) -> Hub: ...
    def __init__(self, maxsize: Literal[1] = 1) -> None: ...
    @classmethod
    def __class_getitem__(cls, item: Any, /) -> types.GenericAlias: ...
    @property
    def balance(self) -> int: ...
    def qsize(self) -> Literal[0]: ...
    def empty(self) -> Literal[True]: ...
    def full(self) -> Literal[True]: ...
    def put(
        self,
        item: _T,
        block: bool = True,
        timeout: float | None = None,
    ) -> None: ...
    def put_nowait(self, item: _T) -> None: ...
    def get(self, block: bool = True, timeout: float | None = None) -> _T: ...
    def get_nowait(self) -> _T: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...
    next = __next__
