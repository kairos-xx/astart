import sys
from collections.abc import Callable
from types import TracebackType
from typing import (
    Any,
    Literal,
    Protocol,
    TypeVarTuple,
    Unpack,
    overload,
    type_check_only,
)

from _typeshed import FileDescriptor, StrOrBytesPath

_Ts = TypeVarTuple("_Ts")

@type_check_only
class _Loop(Protocol):
    @property
    def approx_timer_resolution(self) -> float: ...
    @property
    def default(self) -> bool: ...
    @property
    def iteration(self) -> int: ...
    @property
    def depth(self) -> int: ...
    @property
    def backend_int(self) -> int: ...
    @property
    def backend(self) -> str | int: ...
    @property
    def pendingcnt(self) -> int: ...
    @property
    def activecnt(self) -> int: ...
    def handle_error(
        self,
        context: object | None,
        type: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    def run(self, nowait: bool = False, once: bool = False) -> None: ...
    def reinit(self) -> None: ...
    def ref(self) -> None: ...
    def unref(self) -> None: ...
    def break_(self, how: int | None = ...) -> None: ...
    def verify(self) -> None: ...
    def now(self) -> float: ...
    def update_now(self) -> None: ...
    def destroy(self) -> None: ...
    def io(
        self,
        fd: FileDescriptor,
        events: int,
        ref: bool = True,
        priority: int | None = None,
    ) -> _IoWatcher: ...
    def closing_fd(self, fd: FileDescriptor) -> bool: ...
    def timer(
        self,
        after: float,
        repeat: float = 0.0,
        ref: bool = True,
        priority: int | None = None,
    ) -> _TimerWatcher: ...
    def signal(
        self,
        signum: int,
        ref: bool = True,
        priority: int | None = None,
    ) -> _Watcher: ...
    def idle(
        self,
        ref: bool = True,
        priority: int | None = None,
    ) -> _Watcher: ...
    def prepare(
        self,
        ref: bool = True,
        priority: int | None = None,
    ) -> _Watcher: ...
    def check(
        self,
        ref: bool = True,
        priority: int | None = None,
    ) -> _Watcher: ...
    if sys.platform != "win32":
        def fork(
            self,
            ref: bool = True,
            priority: int | None = None,
        ) -> _Watcher: ...
        def child(
            self,
            pid: int,
            trace: int = 0,
            ref: bool = True,
        ) -> _ChildWatcher: ...
        def install_sigchld(self) -> None: ...
    def async_(
        self,
        ref: bool = True,
        priority: int | None = None,
    ) -> _AsyncWatcher: ...
    def stat(
        self,
        path: str,
        interval: float = 0.0,
        ref: bool = True,
        priority: bool | None = ...,
    ) -> _StatWatcher: ...
    def run_callback(
        self,
        func: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> _Callback: ...
    def run_callback_threadsafe(
        self,
        func: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> _Callback: ...
    def fileno(self) -> FileDescriptor | None: ...

@type_check_only
class _Watcher(Protocol):
    def start(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> None: ...
    def stop(self) -> None: ...
    def close(self) -> None: ...

@type_check_only
class _TimerWatcher(_Watcher, Protocol):
    @overload
    def start(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
        update: bool,
    ) -> None: ...
    @overload
    def start(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> None: ...
    @overload
    def again(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
        update: bool,
    ) -> None: ...
    @overload
    def again(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> None: ...

@type_check_only
class _IoWatcher(_Watcher, Protocol):
    EVENT_MASK: int
    @overload
    def start(
        self,
        callback: Callable[[int, Unpack[_Ts]], Any],
        *args: *_Ts,
        pass_events: Literal[True],
    ) -> None: ...
    @overload
    def start(
        self,
        callback: Callable[[Unpack[_Ts]], Any],
        *args: *_Ts,
    ) -> None: ...

@type_check_only
class _ChildWatcher(_Watcher, Protocol):
    @property
    def pid(self) -> int: ...
    @property
    def rpid(self) -> int | None: ...
    @property
    def rstatus(self) -> int: ...

@type_check_only
class _AsyncWatcher(_Watcher, Protocol):
    def send(self) -> None: ...
    def send_ignoring_arg(self, ignored: object, /) -> None: ...
    @property
    def pending(self) -> bool: ...

@type_check_only
class _StatResult(Protocol):
    @property
    def st_nlink(self) -> int: ...

@type_check_only
class _StatWatcher(_Watcher, Protocol):
    @property
    def path(self) -> StrOrBytesPath: ...
    @property
    def attr(self) -> _StatResult | None: ...
    @property
    def prev(self) -> _StatResult | None: ...
    @property
    def interval(self) -> float: ...

@type_check_only
class _Callback(Protocol):
    pending: bool
    def stop(self) -> None: ...
    def close(self) -> None: ...

type _FullSockAddr = tuple[str, int, int, int]
type _SockAddr = _FullSockAddr | tuple[str, int]
type _AddrinfoResult = list[tuple[int, int, int, str, _SockAddr]]
type _NameinfoResult = tuple[str, str]

@type_check_only
class _Resolver(Protocol):
    def close(self) -> None: ...
    def gethostbyname(self, hostname: str, family: int = 2) -> str: ...
    def gethostbyname_ex(
        self,
        hostname: str,
        family: int = 2,
    ) -> tuple[str, list[str], list[str]]: ...
    def getaddrinfo(
        self,
        host: str,
        port: int,
        family: int = 0,
        socktype: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> _AddrinfoResult: ...
    def gethostbyaddr(
        self,
        ip_address: str,
    ) -> tuple[str, list[str], list[str]]: ...
    def getnameinfo(
        self,
        sockaddr: _SockAddr,
        flags: int,
    ) -> _NameinfoResult: ...
