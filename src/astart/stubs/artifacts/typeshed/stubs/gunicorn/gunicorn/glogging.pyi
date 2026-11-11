import logging
import threading
from collections.abc import Mapping
from datetime import timedelta
from logging.config import _DictConfigArgs
from socket import SocketKind
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    TypedDict,
    type_check_only,
)

from gunicorn.http import Request
from gunicorn.http.wsgi import Response

from ._types import _EnvironType
from .config import Config

SYSLOG_FACILITIES: dict[str, int]

@type_check_only
class _AtomsDict(TypedDict, total=False):
    h: str
    l: str
    u: str
    t: str
    r: str
    s: str
    m: str | None
    U: str | None
    q: str | None
    H: str | None
    b: str
    B: int | None
    f: str
    a: str
    T: int
    D: int
    M: int
    L: str
    p: str

type _CriticalIntType = Annotated[int, "50"]
type _ErrorIntType = Annotated[int, "40"]
type _WarningIntType = Annotated[int, "30"]
type _InfoIntType = Annotated[int, "20"]
type _DebugIntType = Annotated[int, "10"]
type _LogLevelIntType = (
    _CriticalIntType
    | _ErrorIntType
    | _WarningIntType
    | _InfoIntType
    | _DebugIntType
)
type _LogLevelStrType = Literal[
    "critical",
    "error",
    "warning",
    "info",
    "debug",
]
type _LogLevelType = _LogLevelIntType | _LogLevelStrType
CONFIG_DEFAULTS: _DictConfigArgs

def loggers() -> list[logging.Logger]: ...

class SafeAtoms(dict[str, Any]):
    def __init__(self, atoms: dict[str, Any]) -> None: ...
    def __getitem__(self, k: str) -> str: ...

type _SyslogAddressType = (
    tuple[Literal[SocketKind.SOCK_DGRAM] | None, str]
    | tuple[
        Literal[SocketKind.SOCK_DGRAM, SocketKind.SOCK_STREAM],
        tuple[str, int],
    ]
)

def parse_syslog_address(addr: str) -> _SyslogAddressType: ...
@type_check_only
class _LogLevels(TypedDict):
    critical: _CriticalIntType
    error: _ErrorIntType
    warning: _WarningIntType
    info: _InfoIntType
    debug: _DebugIntType

class Logger:
    LOG_LEVELS: ClassVar[_LogLevels]
    loglevel: ClassVar[_LogLevelIntType]
    error_fmt: ClassVar[str]
    datefmt: ClassVar[str]
    access_fmt: ClassVar[str]
    syslog_fmt: ClassVar[str]
    atoms_wrapper_class: ClassVar[type[SafeAtoms]]
    error_log: logging.Logger
    access_log: logging.Logger
    error_handlers: list[logging.Handler]
    access_handlers: list[logging.Handler]
    logfile: Any | None
    lock: threading.Lock
    cfg: Config
    def __init__(self, cfg: Config) -> None: ...
    def setup(self, cfg: Config) -> None: ...
    def critical(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def error(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def warning(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def info(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def debug(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def exception(
        self,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType = True,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def log(
        self,
        lvl: _LogLevelType,
        msg: object,
        *args: object,
        exc_info: logging._ExcInfoType | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
    ) -> None: ...
    def atoms(
        self,
        resp: Response,
        req: Request,
        environ: _EnvironType,
        request_time: timedelta,
    ) -> _AtomsDict: ...
    @property
    def access_log_enabled(self) -> bool: ...
    def access(
        self,
        resp: Response,
        req: Request,
        environ: _EnvironType,
        request_time: timedelta,
    ) -> None: ...
    def now(self) -> str: ...
    def reopen_files(self) -> None: ...
    def close_on_exec(self) -> None: ...
