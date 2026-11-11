from collections.abc import Callable
from typing import ParamSpec, TypeVar

__all__ = ("to_thread",)
_P = ParamSpec("_P")
_R = TypeVar("_R")

async def to_thread(
    func: Callable[_P, _R],
    /,
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> _R: ...
