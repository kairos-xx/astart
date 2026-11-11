import threading
from collections.abc import Callable
from pdb import Pdb
from types import FrameType
from typing import Any, Literal, Protocol, TypeVar, type_check_only

from _typeshed import SupportsWrite, TraceFunction

from .watch_element import WatchElement

_T = TypeVar("_T")
type _Identifier = str

class Watch:
    custom_printer: Callable[[Any], None] | None
    enable: bool
    file: str | SupportsWrite[str] | None
    pdb: Pdb | None
    pdb_enable: bool
    set_lock: threading.Lock
    stack_limit: int | None
    tracefunc_lock: threading.Lock
    tracefunc_stack: list[TraceFunction | None]
    watch_list: list[WatchElement]
    def __init__(self) -> None: ...
    def __call__(
        self,
        *args: object,
        alias: str = ...,
        callback: Callable[
            [FrameType, WatchElement, tuple[str, str, int | None]],
            None,
        ] = ...,
        cmp: Callable[[Any, Any], bool] = ...,
        copy: Callable[[_T], _T] = ...,
        custom_printer: Callable[[Any], None] = ...,
        deepcopy: bool = False,
        file: str | SupportsWrite[str] = ...,
        stack_limit: int | None = 5,
        track: Literal["object", "variable"] = ...,
        when: Callable[[Any], bool] = ...,
    ) -> None: ...
    def config(
        self,
        *,
        callback: Callable[
            [FrameType, WatchElement, tuple[str, str, int | None]],
            None,
        ] = ...,
        pdb: Literal[True] = True,
        file: str | SupportsWrite[str] = ...,
        stack_limit: int | None = 5,
        custom_printer: Callable[[Any], None] = ...,
    ) -> None: ...
    def install(self, func: _Identifier = "watch") -> None: ...
    def restore(self) -> None: ...
    def start_trace(self, frame: FrameType) -> None: ...
    def stop_trace(self, frame: FrameType) -> None: ...
    def tracefunc(
        self,
        frame: FrameType,
        event: str,
        arg: object,
    ) -> _TraceFunc: ...
    def uninstall(self, func: _Identifier = "watch") -> None: ...
    def unwatch(self, *args: object) -> None: ...

@type_check_only
class _TraceFunc(Protocol):
    def __call__(
        self,
        frame: FrameType,
        event: str,
        arg: object,
    ) -> _TraceFunc: ...
