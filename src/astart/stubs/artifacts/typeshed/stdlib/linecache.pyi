from collections.abc import Callable
from typing import Any

__all__ = ["checkcache", "clearcache", "getline", "lazycache"]
type _ModuleGlobals = dict[str, Any]
type _ModuleMetadata = tuple[int, float | None, list[str], str]
type _SourceLoader = tuple[Callable[[], str | None]]
cache: dict[str, _SourceLoader | _ModuleMetadata]

def getline(
    filename: str,
    lineno: int,
    module_globals: _ModuleGlobals | None = None,
) -> str: ...
def clearcache() -> None: ...
def getlines(
    filename: str,
    module_globals: _ModuleGlobals | None = None,
) -> list[str]: ...
def checkcache(filename: str | None = None) -> None: ...
def updatecache(
    filename: str,
    module_globals: _ModuleGlobals | None = None,
) -> list[str]: ...
def lazycache(filename: str, module_globals: _ModuleGlobals) -> bool: ...
