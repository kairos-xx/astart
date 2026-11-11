import asyncio
from asyncio import BaseEventLoop
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, ParamSpec, TypeVar

from _typeshed import OptExcInfo
from asgiref.sync import SyncToAsync

_P = ParamSpec("_P")
_R = TypeVar("_R")

class DatabaseSyncToAsync(SyncToAsync[_P, _R]):
    def thread_handler(
        self,
        loop: BaseEventLoop,
        exc_info: OptExcInfo,
        task_context: list[asyncio.Task[Any]] | None,
        func: Callable[_P, _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _R: ...

def database_sync_to_async[**P, R](
    func: Callable[_P, _R],
    thread_sensitive: bool = True,
    executor: ThreadPoolExecutor | None = None,
) -> Callable[_P, Coroutine[Any, Any, _R]]: ...
async def aclose_old_connections() -> None: ...
