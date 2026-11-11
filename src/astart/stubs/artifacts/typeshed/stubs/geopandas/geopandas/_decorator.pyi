from collections.abc import Callable
from typing import TypeVar, overload

type _AnyCallable = Callable[..., object]
_Func = TypeVar("_Func", bound=_AnyCallable)

@overload
def doc[Func: _AnyCallable](
    func: _Func,
    /,
    **params: object,
) -> Callable[[_AnyCallable], _Func]: ...
@overload
def doc(
    docstring: str,
    /,
    *docstrings: str | _AnyCallable,
    **params: object,
) -> Callable[[_Func], _Func]: ...
@overload
def doc(
    docstring1: str | _AnyCallable,
    docstring2: str | _AnyCallable,
    /,
    *docstrings: str | _AnyCallable,
    **params: object,
) -> Callable[[_Func], _Func]: ...
