from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ParamSpec, TypeGuard, TypeIs, TypeVar, overload
from warnings import deprecated

__all__ = ("iscoroutine", "iscoroutinefunction")
_T = TypeVar("_T")
_P = ParamSpec("_P")

def iscoroutine(obj: object) -> TypeIs[Coroutine[Any, Any, Any]]: ...
@overload
@deprecated(
    "Deprecated since Python 3.14. Use `inspect.iscoroutinefunction()` instead.",
)
def iscoroutinefunction(
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> bool: ...
@overload
@deprecated(
    "Deprecated since Python 3.14. Use `inspect.iscoroutinefunction()` instead.",
)
def iscoroutinefunction[**P, T](
    func: Callable[_P, Awaitable[_T]],
) -> TypeGuard[Callable[_P, Coroutine[Any, Any, _T]]]: ...
@overload
@deprecated(
    "Deprecated since Python 3.14. Use `inspect.iscoroutinefunction()` instead.",
)
def iscoroutinefunction[**P](
    func: Callable[_P, object],
) -> TypeGuard[Callable[_P, Coroutine[Any, Any, Any]]]: ...
@overload
@deprecated(
    "Deprecated since Python 3.14. Use `inspect.iscoroutinefunction()` instead.",
)
def iscoroutinefunction(
    func: object,
) -> TypeGuard[Callable[..., Coroutine[Any, Any, Any]]]: ...
