from typing import TypeVar

_T = TypeVar("_T")

def asyncify[T](cls: type[_T]) -> type[_T]: ...
