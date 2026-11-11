from _curses import *
from _curses import window as window
from collections.abc import Callable
from typing import (
    Concatenate,
    Final,
    ParamSpec,
    TypeVar,
    final,
    type_check_only,
)

from _typeshed import structseq

_T = TypeVar("_T")
_P = ParamSpec("_P")
LINES: int
COLS: int
COLORS: Final[int]
COLOR_PAIRS: Final[int]

def wrapper(
    func: Callable[Concatenate[window, _P], _T],
    /,
    *arg: _P.args,
    **kwds: _P.kwargs,
) -> _T: ...
@final
@type_check_only
class _ncurses_version(structseq[int], tuple[int, int, int]):
    __match_args__: Final = ("major", "minor", "patch")
    @property
    def major(self) -> int: ...
    @property
    def minor(self) -> int: ...
    @property
    def patch(self) -> int: ...
