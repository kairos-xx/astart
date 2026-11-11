import sys
from collections.abc import Awaitable, Callable, Coroutine
from contextvars import Context
from typing import Any, Self, TypeVar, final

from _typeshed import Unused

from .events import AbstractEventLoop

__all__ = ("Runner", "run")
_T = TypeVar("_T")

@final
class Runner:
    def __init__(
        self,
        *,
        debug: bool | None = None,
        loop_factory: Callable[[], AbstractEventLoop] | None = None,
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: Unused,
        exc_val: Unused,
        exc_tb: Unused,
    ) -> None: ...
    def close(self) -> None: ...
    def get_loop(self) -> AbstractEventLoop: ...
    if sys.version_info >= (3, 14):
        def run(
            self,
            coro: Awaitable[_T],
            *,
            context: Context | None = None,
        ) -> _T: ...
    else:
        def run(
            self,
            coro: Coroutine[Any, Any, _T],
            *,
            context: Context | None = None,
        ) -> _T: ...

if sys.version_info >= (3, 14):
    def run[T](
        main: Awaitable[_T],
        *,
        debug: bool | None = None,
        loop_factory: Callable[[], AbstractEventLoop] | None = None,
    ) -> _T: ...
else:
    def run[T](
        main: Coroutine[Any, Any, _T],
        *,
        debug: bool | None = None,
        loop_factory: Callable[[], AbstractEventLoop] | None = None,
    ) -> _T: ...
