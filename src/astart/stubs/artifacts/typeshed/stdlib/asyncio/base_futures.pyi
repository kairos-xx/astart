from _asyncio import Future
from collections.abc import Callable, Sequence
from contextvars import Context
from typing import Any, Final, TypeIs

from . import futures

__all__ = ()
_PENDING: Final = "PENDING"
_CANCELLED: Final = "CANCELLED"
_FINISHED: Final = "FINISHED"

def isfuture(obj: object) -> TypeIs[Future[Any]]: ...
def _format_callbacks(
    cb: Sequence[tuple[Callable[[futures.Future[Any]], None], Context]],
) -> str: ...
def _future_repr_info(future: futures.Future[Any]) -> list[str]: ...
