from typing import Any, Protocol, TypeVar, type_check_only

__all__ = ["Error", "copy", "deepcopy"]
_T = TypeVar("_T")
_RT_co = TypeVar("_RT_co", covariant=True)

@type_check_only
class _SupportsReplace(Protocol[_RT_co]):
    def __replace__(self, /, *_: Any, **changes: Any) -> _RT_co: ...

PyStringMap: Any

def deepcopy[T](
    x: _T,
    memo: dict[int, Any] | None = None,
    _nil: Any = [],
) -> _T: ...
def copy[T](x: _T) -> _T: ...

__all__ += ["replace"]

def replace[RT_co](
    obj: _SupportsReplace[_RT_co],
    /,
    **changes: Any,
) -> _RT_co: ...

class Error(Exception): ...

error = Error
