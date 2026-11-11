from collections.abc import Callable, Iterable
from typing import Any, ParamSpec, Self, TypeVar

from gevent.greenlet import Greenlet
from gevent.queue import UnboundQueue
from typing_extensions import disjoint_base

_T = TypeVar("_T")
_P = ParamSpec("_P")

@disjoint_base
class IMapUnordered(Greenlet[_P, _T]):
    finished: bool
    queue: UnboundQueue[_T | object]
    def __init__(
        self,
        func: Callable[_P, _T],
        iterable: Iterable[Any],
        spawn: Callable[_P, Greenlet[_P, _T]],
    ) -> None: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class IMap(IMapUnordered[_P, _T]):
    index: int

__all__ = ["IMap", "IMapUnordered"]
