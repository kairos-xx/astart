from typing import TypeVar

_T = TypeVar("_T")

def Experimental[T](cls: _T) -> _T: ...
