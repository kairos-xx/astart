import threading
from collections.abc import Callable
from queue import Queue
from types import ModuleType, TracebackType
from typing import (
    Any,
    ClassVar,
    ParamSpec,
    Self,
    TypedDict,
    TypeVar,
    type_check_only,
)

from _typeshed import OptExcInfo

_T = TypeVar("_T")
_AbstractListenerT = TypeVar("_AbstractListenerT", bound=AbstractListener)
_P = ParamSpec("_P")

@type_check_only
class _RESOLUTIONS(TypedDict):
    darwin: str
    uinput: str
    xorg: str

RESOLUTIONS: _RESOLUTIONS

def backend(package: str) -> ModuleType: ...
def prefix(
    base: type | tuple[type | tuple[Any, ...], ...],
    cls: type,
) -> str | None: ...

class AbstractListener(threading.Thread):
    class StopException(Exception): ...
    _HANDLED_EXCEPTIONS: ClassVar[tuple[type | tuple[Any, ...], ...]]
    _suppress: bool
    _running: bool
    _thread: threading.Thread
    _condition: threading.Condition
    _ready: bool
    _queue: Queue[OptExcInfo | None]
    daemon: bool
    def __init__(
        self,
        suppress: bool = False,
        **kwargs: Callable[..., bool | None] | None,
    ) -> None: ...
    @property
    def suppress(self) -> bool: ...
    @property
    def running(self) -> bool: ...
    def stop(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def wait(self) -> None: ...
    def run(self) -> None: ...
    @classmethod
    def _emitter(cls, f: Callable[_P, _T]) -> Callable[_P, _T]: ...
    def _mark_ready(self) -> None: ...
    def _run(self) -> None: ...
    def _stop_platform(self) -> None: ...
    def join(self, timeout: float | None = None, *args: Any) -> None: ...

class Events[T, AbstractListenerT: AbstractListener]:
    _Listener: type[_AbstractListenerT] | None
    class Event:
        def __eq__(self, other: object) -> bool: ...

    _event_queue: Queue[_T]
    _sentinel: object
    _listener: _AbstractListenerT
    start: Callable[[], None]
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...
    def get(self, timeout: float | None = None) -> _T | None: ...
    def _event_mapper(
        self,
        event: Callable[_P, object],
    ) -> Callable[_P, None]: ...

class NotifierMixin: ...
