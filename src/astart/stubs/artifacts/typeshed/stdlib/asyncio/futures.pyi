import sys
from _asyncio import Future as Future
from concurrent.futures._base import Future as _ConcurrentFuture
from typing import TypeVar

from .base_futures import isfuture as isfuture
from .events import AbstractEventLoop

if sys.version_info >= (3, 14):
    from _asyncio import (
        future_add_to_awaited_by,
        future_discard_from_awaited_by,
    )

    __all__ = (
        "Future",
        "future_add_to_awaited_by",
        "future_discard_from_awaited_by",
        "isfuture",
        "wrap_future",
    )
else:
    __all__ = ("Future", "isfuture", "wrap_future")
_T = TypeVar("_T")

def wrap_future(
    future: _ConcurrentFuture[_T] | Future[_T],
    *,
    loop: AbstractEventLoop | None = None,
) -> Future[_T]: ...
