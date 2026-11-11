from collections.abc import Callable, Iterator
from typing import Any, Final, TypeVar, type_check_only

from _typeshed import MaybeNone
from typing_extensions import disjoint_base

__all__ = [
    "LUA_MAXINTEGER",
    "LUA_MININTEGER",
    "LUA_VERSION",
    "LuaError",
    "LuaMemoryError",
    "LuaRuntime",
    "LuaSyntaxError",
    "as_attrgetter",
    "as_itemgetter",
    "lua_type",
    "unpacks_lua_table",
    "unpacks_lua_table_method",
]
LUA_MAXINTEGER: Final[int]
LUA_MININTEGER: Final[int]
LUA_VERSION: Final[tuple[int, int]]
as_attrgetter: Callable[[object], object]
as_itemgetter: Callable[[object], object]
lua_type: Callable[[object], str | MaybeNone]
unpacks_lua_table: Callable[[Callable[..., Any]], Callable[..., Any]]
unpacks_lua_table_method: Callable[[Callable[..., Any]], Callable[..., Any]]

@type_check_only
class _LuaIter:
    def __iter__(self) -> Iterator[object]: ...

@type_check_only
class _LuaTable:
    def keys(self) -> _LuaIter: ...
    def values(self) -> _LuaIter: ...
    def items(self) -> _LuaIter: ...

@type_check_only
class _LuaNoGC: ...

@type_check_only
class _LuaObject: ...

_bint = TypeVar("_bint", bool, int)

@disjoint_base
class FastRLock[bint: (bool, int)]:
    def acquire(self, blocking: _bint = ...) -> _bint: ...
    def release(self) -> None: ...
    def __enter__(self) -> _bint: ...
    def __exit__(self, t: object, v: object, tb: object) -> None: ...

class LuaError(Exception): ...
class LuaSyntaxError(LuaError): ...
class LuaMemoryError(LuaError, MemoryError): ...

@disjoint_base
class LuaRuntime:
    lua_implementation: Final[str]
    lua_version: Final[tuple[int, int]]
    def get_max_memory(self, total: bool = False) -> int | MaybeNone: ...
    def get_memory_used(self, total: bool = False) -> int | MaybeNone: ...
    def eval(
        self,
        lua_code: str,
        *args: Any,
        name: str | None = None,
        mode: str | None = None,
    ) -> object: ...
    def execute(
        self,
        lua_code: str,
        *args: Any,
        name: str | None = None,
        mode: str | None = None,
    ) -> object: ...
    def compile(
        self,
        lua_code: str,
        name: str | None = None,
        mode: str | None = None,
    ) -> Callable[..., object]: ...
    def require(self, modulename: str) -> object: ...
    def globals(self) -> _LuaTable: ...
    def table(self, *items: Any, **kwargs: Any) -> _LuaTable: ...
    def table_from(self, *args: Any, recursive: bool = ...) -> _LuaTable: ...
    def nogc(self) -> _LuaNoGC: ...
    def gccollect(self) -> None: ...
    def set_max_memory(self, max_memory: int, total: bool = False) -> None: ...
    def set_overflow_handler(
        self,
        overflow_handler: Callable[..., None],
    ) -> None: ...
