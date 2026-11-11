import ssl
from collections import deque
from enum import Enum
from typing import Any, ClassVar, Literal

from . import constants, events, futures, protocols, transports

def _create_transport_context(
    server_side: bool,
    server_hostname: str | None,
) -> ssl.SSLContext: ...

SSLAgainErrors: tuple[type[ssl.SSLWantReadError], type[ssl.SSLSyscallError]]

class SSLProtocolState(Enum):
    UNWRAPPED = "UNWRAPPED"
    DO_HANDSHAKE = "DO_HANDSHAKE"
    WRAPPED = "WRAPPED"
    FLUSHING = "FLUSHING"
    SHUTDOWN = "SHUTDOWN"

class AppProtocolState(Enum):
    STATE_INIT = "STATE_INIT"
    STATE_CON_MADE = "STATE_CON_MADE"
    STATE_EOF = "STATE_EOF"
    STATE_CON_LOST = "STATE_CON_LOST"

def add_flowcontrol_defaults(
    high: int | None,
    low: int | None,
    kb: int,
) -> tuple[int, int]: ...

class _SSLProtocolTransport(
    transports._FlowControlMixin,
    transports.Transport,
):
    _sendfile_compatible: ClassVar[constants._SendfileMode]
    _loop: events.AbstractEventLoop
    _ssl_protocol: SSLProtocol | None
    _closed: bool
    def __init__(
        self,
        loop: events.AbstractEventLoop,
        ssl_protocol: SSLProtocol,
    ) -> None: ...
    def get_extra_info(
        self,
        name: str,
        default: Any | None = None,
    ) -> dict[str, Any]: ...
    @property
    def _protocol_paused(self) -> bool: ...
    def write(self, data: bytes | bytearray | memoryview[Any]) -> None: ...
    def can_write_eof(self) -> Literal[False]: ...
    def get_write_buffer_limits(self) -> tuple[int, int]: ...
    def get_read_buffer_limits(self) -> tuple[int, int]: ...
    def set_read_buffer_limits(
        self,
        high: int | None = None,
        low: int | None = None,
    ) -> None: ...
    def get_read_buffer_size(self) -> int: ...
    def __del__(self) -> None: ...

type _SSLProtocolBase = protocols.BufferedProtocol

class SSLProtocol(_SSLProtocolBase):
    _server_side: bool
    _server_hostname: str | None
    _sslcontext: ssl.SSLContext
    _extra: dict[str, Any]
    _write_backlog: deque[tuple[bytes, int]]
    _write_buffer_size: int
    _waiter: futures.Future[Any]
    _loop: events.AbstractEventLoop
    _app_transport: _SSLProtocolTransport
    _transport: transports.BaseTransport | None
    _ssl_handshake_timeout: int | None
    _app_protocol: protocols.BaseProtocol
    _app_protocol_is_buffer: bool
    max_size: ClassVar[int]
    def __init__(
        self,
        loop: events.AbstractEventLoop,
        app_protocol: protocols.BaseProtocol,
        sslcontext: ssl.SSLContext,
        waiter: futures.Future[Any],
        server_side: bool = False,
        server_hostname: str | None = None,
        call_connection_made: bool = True,
        ssl_handshake_timeout: int | None = None,
        ssl_shutdown_timeout: float | None = None,
    ) -> None: ...
    def _set_app_protocol(
        self,
        app_protocol: protocols.BaseProtocol,
    ) -> None: ...
    def _wakeup_waiter(self, exc: BaseException | None = None) -> None: ...
    def connection_lost(self, exc: BaseException | None) -> None: ...
    def eof_received(self) -> None: ...
    def _get_extra_info(
        self,
        name: str,
        default: Any | None = None,
    ) -> Any: ...
    def _start_shutdown(self) -> None: ...
    def _write_appdata(self, list_of_data: list[bytes]) -> None: ...
    def _start_handshake(self) -> None: ...
    def _check_handshake_timeout(self) -> None: ...
    def _on_handshake_complete(
        self,
        handshake_exc: BaseException | None,
    ) -> None: ...
    def _fatal_error(
        self,
        exc: BaseException,
        message: str = "Fatal error on transport",
    ) -> None: ...
    def _abort(self, exc: BaseException | None) -> None: ...
    def get_buffer(self, n: int) -> memoryview: ...
