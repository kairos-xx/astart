from threading import RLock
from typing import Any, Self
from weakref import ReferenceType

__all__ = ["local"]
type _LocalDict = dict[Any, Any]

class _localimpl:
    __slots__ = ("__weakref__", "dicts", "key", "localargs", "locallock")
    key: str
    dicts: dict[int, tuple[ReferenceType[Any], _LocalDict]]
    localargs: tuple[list[Any], dict[str, Any]]
    locallock: RLock
    def get_dict(self) -> _LocalDict: ...
    def create_dict(self) -> _LocalDict: ...

class local:
    __slots__ = ("__dict__", "_local__impl")
    def __new__(cls, /, *args: Any, **kw: Any) -> Self: ...
    def __getattribute__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def __delattr__(self, name: str) -> None: ...
