from collections.abc import Callable
from typing import Any, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])

def type_check[F: Callable[..., Any]](func: _F) -> _F: ...
