from collections.abc import Callable
from typing import Any, TypeVar

_C = TypeVar("_C", bound=Callable[..., Any])

def initialised[C: Callable[..., Any]](func: _C) -> _C: ...
def trap(path_index: str | int) -> Callable[[_C], _C]: ...
def gen_password(length: int, symbols: bool = True) -> str: ...
def copy_move(
    src: str,
    dst: str,
    force: bool = False,
    move: bool = False,
    interactive: bool = False,
    verbose: bool = False,
) -> str | None: ...
