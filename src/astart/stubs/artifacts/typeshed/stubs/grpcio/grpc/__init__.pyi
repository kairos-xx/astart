import abc
import enum
import threading
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent import futures
from types import ModuleType, TracebackType
from typing import (
    Any,
    Generic,
    NoReturn,
    Protocol,
    Self,
    TypeVar,
    type_check_only,
)

from . import aio as aio

__version__: str
type _OptionKeyValue = tuple[str, Any]
type _Options = Sequence[_OptionKeyValue]

class Compression(enum.IntEnum):
    NoCompression = 0
    Deflate = 1
    Gzip = 2

@enum.unique
class LocalConnectionType(enum.Enum):
    UDS = 0
    LOCAL_TCP = 1

type _Metadata = tuple[tuple[str, str | bytes], ...]
_TRequest = TypeVar("_TRequest")
_TResponse = TypeVar("_TResponse")
type _Serializer[_T] = Callable[[_T], bytes]
type _Deserializer[_T] = Callable[[bytes], _T]

class FutureTimeoutError(Exception): ...
class FutureCancelledError(Exception): ...

_TFutureValue = TypeVar("_TFutureValue")

class Future[TFutureValue](abc.ABC):
    @abc.abstractmethod
    def add_done_callback(
        self,
        fn: Callable[[Future[_TFutureValue]], None],
    ) -> None: ...
    @abc.abstractmethod
    def cancel(self) -> bool: ...
    @abc.abstractmethod
    def cancelled(self) -> bool: ...
    @abc.abstractmethod
    def done(self) -> bool: ...
    @abc.abstractmethod
    def exception(self, timeout: float | None = None) -> Exception | None: ...
    @abc.abstractmethod
    def result(self, timeout: float | None = None) -> _TFutureValue: ...
    @abc.abstractmethod
    def running(self) -> bool: ...
    @abc.abstractmethod
    def traceback(self, timeout: float | None = None): ...

def insecure_channel(
    target: str,
    options: _Options | None = None,
    compression: Compression | None = None,
) -> Channel: ...
def secure_channel(
    target: str,
    credentials: ChannelCredentials,
    options: _Options | None = None,
    compression: Compression | None = None,
) -> Channel: ...

type _Interceptor = (
    UnaryUnaryClientInterceptor
    | UnaryStreamClientInterceptor
    | StreamUnaryClientInterceptor
    | StreamStreamClientInterceptor
)

def intercept_channel(
    channel: Channel,
    *interceptors: _Interceptor,
) -> Channel: ...
def ssl_channel_credentials(
    root_certificates: bytes | None = None,
    private_key: bytes | None = None,
    certificate_chain: bytes | None = None,
) -> ChannelCredentials: ...
def local_channel_credentials(
    local_connect_type: LocalConnectionType = ...,
) -> ChannelCredentials: ...
def metadata_call_credentials(
    metadata_plugin: AuthMetadataPlugin,
    name: str | None = None,
) -> CallCredentials: ...
def access_token_call_credentials(access_token: str) -> CallCredentials: ...
def alts_channel_credentials(
    service_accounts: Sequence[str] | None = None,
) -> ChannelCredentials: ...
def compute_engine_channel_credentials(
    call_credentials: CallCredentials,
) -> ChannelCredentials: ...
def xds_channel_credentials(
    fallback_credentials: ChannelCredentials | None = None,
) -> ChannelCredentials: ...
def composite_call_credentials(
    creds1: CallCredentials,
    creds2: CallCredentials,
    *rest: CallCredentials,
) -> CallCredentials: ...
def composite_channel_credentials(
    channel_credentials: ChannelCredentials,
    call_credentials: CallCredentials,
    *rest: CallCredentials,
) -> ChannelCredentials: ...
def server(
    thread_pool: futures.ThreadPoolExecutor,
    handlers: list[GenericRpcHandler] | None = None,
    interceptors: list[ServerInterceptor] | None = None,
    options: _Options | None = None,
    maximum_concurrent_rpcs: int | None = None,
    compression: Compression | None = None,
    xds: bool = False,
) -> Server: ...

type _CertificateChainPair = tuple[bytes, bytes]

def ssl_server_credentials(
    private_key_certificate_chain_pairs: list[_CertificateChainPair],
    root_certificates: bytes | None = None,
    require_client_auth: bool = False,
) -> ServerCredentials: ...
def local_server_credentials(
    local_connect_type: LocalConnectionType = ...,
) -> ServerCredentials: ...
def ssl_server_certificate_configuration(
    private_key_certificate_chain_pairs: list[_CertificateChainPair],
    root_certificates: bytes | None = None,
) -> ServerCertificateConfiguration: ...
def dynamic_ssl_server_credentials(
    initial_certificate_configuration: ServerCertificateConfiguration,
    certificate_configuration_fetcher: Callable[
        [],
        ServerCertificateConfiguration,
    ],
    require_client_authentication: bool = False,
) -> ServerCredentials: ...
def alts_server_credentials() -> ServerCredentials: ...
def insecure_server_credentials() -> ServerCredentials: ...
def xds_server_credentials(
    fallback_credentials: ServerCredentials,
) -> ServerCredentials: ...
@type_check_only
class _Behaviour(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

def unary_unary_rpc_method_handler[TRequest, TResponse](
    behavior: _Behaviour,
    request_deserializer: _Deserializer[_TRequest] | None = None,
    response_serializer: _Serializer[_TResponse] | None = None,
) -> RpcMethodHandler[_TRequest, _TResponse]: ...
def unary_stream_rpc_method_handler[TRequest, TResponse](
    behavior: _Behaviour,
    request_deserializer: _Deserializer[_TRequest] | None = None,
    response_serializer: _Serializer[_TResponse] | None = None,
) -> RpcMethodHandler[_TRequest, _TResponse]: ...
def stream_unary_rpc_method_handler[TRequest, TResponse](
    behavior: _Behaviour,
    request_deserializer: _Deserializer[_TRequest] | None = None,
    response_serializer: _Serializer[_TResponse] | None = None,
) -> RpcMethodHandler[_TRequest, _TResponse]: ...
def stream_stream_rpc_method_handler[TRequest, TResponse](
    behavior: _Behaviour,
    request_deserializer: _Deserializer[_TRequest] | None = None,
    response_serializer: _Serializer[_TResponse] | None = None,
) -> RpcMethodHandler[_TRequest, _TResponse]: ...
def method_handlers_generic_handler(
    service: str,
    method_handlers: dict[str, RpcMethodHandler[Any, Any]],
) -> GenericRpcHandler: ...
def channel_ready_future(channel: Channel) -> Future[None]: ...

class ChannelConnectivity(enum.Enum):
    IDLE = (0, "idle")
    CONNECTING = (1, "connecting")
    READY = (2, "ready")
    TRANSIENT_FAILURE = (3, "transient failure")
    SHUTDOWN = (4, "shutdown")

class Status(abc.ABC):
    code: StatusCode
    details: str
    trailing_metadata: _Metadata

class StatusCode(enum.Enum):
    OK = (0, "ok")
    CANCELLED = (1, "cancelled")
    UNKNOWN = (2, "unknown")
    INVALID_ARGUMENT = (3, "invalid argument")
    DEADLINE_EXCEEDED = (4, "deadline exceeded")
    NOT_FOUND = (5, "not found")
    ALREADY_EXISTS = (6, "already exists")
    PERMISSION_DENIED = (7, "permission denied")
    RESOURCE_EXHAUSTED = (8, "resource exhausted")
    FAILED_PRECONDITION = (9, "failed precondition")
    ABORTED = (10, "aborted")
    OUT_OF_RANGE = (11, "out of range")
    UNIMPLEMENTED = (12, "unimplemented")
    INTERNAL = (13, "internal")
    UNAVAILABLE = (14, "unavailable")
    DATA_LOSS = (15, "data loss")
    UNAUTHENTICATED = (16, "unauthenticated")

class Channel(abc.ABC):
    @abc.abstractmethod
    def close(self) -> None: ...
    @abc.abstractmethod
    def stream_stream(
        self,
        method: str,
        request_serializer: _Serializer[_TRequest] | None = None,
        response_deserializer: _Deserializer[_TResponse] | None = None,
    ) -> StreamStreamMultiCallable[_TRequest, _TResponse]: ...
    @abc.abstractmethod
    def stream_unary(
        self,
        method: str,
        request_serializer: _Serializer[_TRequest] | None = None,
        response_deserializer: _Deserializer[_TResponse] | None = None,
    ) -> StreamUnaryMultiCallable[_TRequest, _TResponse]: ...
    @abc.abstractmethod
    def subscribe(
        self,
        callback: Callable[[ChannelConnectivity], None],
        try_to_connect: bool = False,
    ) -> None: ...
    @abc.abstractmethod
    def unary_stream(
        self,
        method: str,
        request_serializer: _Serializer[_TRequest] | None = None,
        response_deserializer: _Deserializer[_TResponse] | None = None,
    ) -> UnaryStreamMultiCallable[_TRequest, _TResponse]: ...
    @abc.abstractmethod
    def unary_unary(
        self,
        method: str,
        request_serializer: _Serializer[_TRequest] | None = None,
        response_deserializer: _Deserializer[_TResponse] | None = None,
    ) -> UnaryUnaryMultiCallable[_TRequest, _TResponse]: ...
    @abc.abstractmethod
    def unsubscribe(
        self,
        callback: Callable[[ChannelConnectivity], None],
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

class Server(abc.ABC):
    @abc.abstractmethod
    def add_generic_rpc_handlers(
        self,
        generic_rpc_handlers: Iterable[GenericRpcHandler],
    ) -> None: ...
    @abc.abstractmethod
    def add_insecure_port(self, address: str) -> int: ...
    @abc.abstractmethod
    def add_secure_port(
        self,
        address: str,
        server_credentials: ServerCredentials,
    ) -> int: ...
    @abc.abstractmethod
    def start(self) -> None: ...
    @abc.abstractmethod
    def stop(self, grace: float | None) -> threading.Event: ...
    def wait_for_termination(self, timeout: float | None = None) -> bool: ...

class ChannelCredentials:
    def __init__(self, credentials) -> None: ...

class CallCredentials:
    def __init__(self, credentials) -> None: ...

class AuthMetadataContext(abc.ABC):
    service_url: str
    method_name: str

class AuthMetadataPluginCallback(abc.ABC):
    def __call__(
        self,
        metadata: _Metadata,
        error: Exception | None,
    ) -> None: ...

class AuthMetadataPlugin(abc.ABC):
    def __call__(
        self,
        context: AuthMetadataContext,
        callback: AuthMetadataPluginCallback,
    ) -> None: ...

class ServerCredentials:
    def __init__(self, credentials) -> None: ...

class ServerCertificateConfiguration:
    def __init__(self, certificate_configuration) -> None: ...

@type_check_only
class _Metadatum:
    key: str
    value: bytes

class RpcError(Exception):
    def code(self) -> StatusCode: ...
    def details(self) -> str | None: ...
    def trailing_metadata(self) -> tuple[_Metadatum, ...]: ...

class RpcContext(abc.ABC):
    @abc.abstractmethod
    def add_callback(self, callback: Callable[[], None]) -> bool: ...
    @abc.abstractmethod
    def cancel(self) -> bool: ...
    @abc.abstractmethod
    def is_active(self) -> bool: ...
    @abc.abstractmethod
    def time_remaining(self) -> float: ...

class Call(RpcContext, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def code(self) -> StatusCode: ...
    @abc.abstractmethod
    def details(self) -> str: ...
    @abc.abstractmethod
    def initial_metadata(self) -> _Metadata: ...
    @abc.abstractmethod
    def trailing_metadata(self) -> _Metadata: ...

class ClientCallDetails(abc.ABC):
    method: str
    timeout: float | None
    metadata: _Metadata | None
    credentials: CallCredentials | None
    wait_for_ready: bool | None
    compression: Compression | None

@type_check_only
class _CallFuture(Call, Future[_TResponse], metaclass=abc.ABCMeta): ...

class UnaryUnaryClientInterceptor(abc.ABC):
    @abc.abstractmethod
    def intercept_unary_unary(
        self,
        continuation: Callable[
            [ClientCallDetails, _TRequest],
            _CallFuture[_TResponse],
        ],
        client_call_details: ClientCallDetails,
        request: _TRequest,
    ) -> _CallFuture[_TResponse]: ...

@type_check_only
class _CallIterator(Call, Generic[_TResponse], metaclass=abc.ABCMeta):
    def __iter__(self) -> Iterator[_TResponse]: ...
    def __next__(self) -> _TResponse: ...

class UnaryStreamClientInterceptor(abc.ABC):
    @abc.abstractmethod
    def intercept_unary_stream(
        self,
        continuation: Callable[
            [ClientCallDetails, _TRequest],
            _CallIterator[_TResponse],
        ],
        client_call_details: ClientCallDetails,
        request: _TRequest,
    ) -> _CallIterator[_TResponse]: ...

class StreamUnaryClientInterceptor(abc.ABC):
    @abc.abstractmethod
    def intercept_stream_unary(
        self,
        continuation: Callable[
            [ClientCallDetails, Iterator[_TRequest]],
            _CallFuture[_TResponse],
        ],
        client_call_details: ClientCallDetails,
        request_iterator: Iterator[_TRequest],
    ) -> _CallFuture[_TResponse]: ...

class StreamStreamClientInterceptor(abc.ABC):
    @abc.abstractmethod
    def intercept_stream_stream(
        self,
        continuation: Callable[
            [ClientCallDetails, Iterator[_TRequest]],
            _CallIterator[_TResponse],
        ],
        client_call_details: ClientCallDetails,
        request_iterator: Iterator[_TRequest],
    ) -> _CallIterator[_TResponse]: ...

class ServicerContext(RpcContext, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def abort(self, code: StatusCode, details: str) -> NoReturn: ...
    @abc.abstractmethod
    def abort_with_status(self, status: Status) -> NoReturn: ...
    @abc.abstractmethod
    def auth_context(self) -> Mapping[str, bytes]: ...
    def disable_next_message_compression(self) -> None: ...
    @abc.abstractmethod
    def invocation_metadata(self) -> _Metadata: ...
    @abc.abstractmethod
    def peer(self) -> str: ...
    @abc.abstractmethod
    def peer_identities(self) -> Iterable[bytes] | None: ...
    @abc.abstractmethod
    def peer_identity_key(self) -> str | None: ...
    @abc.abstractmethod
    def send_initial_metadata(self, initial_metadata: _Metadata) -> None: ...
    @abc.abstractmethod
    def set_code(self, code: StatusCode) -> None: ...
    def set_compression(self, compression: Compression) -> None: ...
    @abc.abstractmethod
    def set_trailing_metadata(self, trailing_metadata: _Metadata) -> None: ...
    @abc.abstractmethod
    def set_details(self, details: str) -> None: ...
    def trailing_metadata(self) -> _Metadata: ...

class RpcMethodHandler[TRequest, TResponse](abc.ABC):
    request_streaming: bool
    response_streaming: bool
    request_deserializer: _Deserializer[_TRequest] | None
    response_serializer: _Serializer[_TResponse] | None
    unary_unary: Callable[[_TRequest, ServicerContext], _TResponse] | None
    unary_stream: (
        Callable[[_TRequest, ServicerContext], Iterator[_TResponse]] | None
    )
    stream_unary: (
        Callable[[Iterator[_TRequest], ServicerContext], _TResponse] | None
    )
    stream_stream: (
        Callable[[Iterator[_TRequest], ServicerContext], Iterator[_TResponse]]
        | None
    )

class HandlerCallDetails(abc.ABC):
    method: str
    invocation_metadata: _Metadata

class GenericRpcHandler(abc.ABC):
    @abc.abstractmethod
    def service(
        self,
        handler_call_details: HandlerCallDetails,
    ) -> RpcMethodHandler[Any, Any] | None: ...

class ServiceRpcHandler(GenericRpcHandler, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def service_name(self) -> str: ...

class ServerInterceptor(abc.ABC):
    @abc.abstractmethod
    def intercept_service(
        self,
        continuation: Callable[
            [HandlerCallDetails],
            RpcMethodHandler[_TRequest, _TResponse] | None,
        ],
        handler_call_details: HandlerCallDetails,
    ) -> RpcMethodHandler[_TRequest, _TResponse] | None: ...

class UnaryUnaryMultiCallable[TRequest, TResponse](abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        request: _TRequest,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _TResponse: ...
    @abc.abstractmethod
    def future(
        self,
        request: _TRequest,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _CallFuture[_TResponse]: ...
    @abc.abstractmethod
    def with_call(
        self,
        request: _TRequest,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> tuple[_TResponse, Call]: ...

class UnaryStreamMultiCallable[TRequest, TResponse](abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        request: _TRequest,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _CallIterator[_TResponse]: ...

class StreamUnaryMultiCallable[TRequest, TResponse](abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        request_iterator: Iterator[_TRequest],
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _TResponse: ...
    @abc.abstractmethod
    def future(
        self,
        request_iterator: Iterator[_TRequest],
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _CallFuture[_TResponse]: ...
    @abc.abstractmethod
    def with_call(
        self,
        request_iterator: Iterator[_TRequest],
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> tuple[_TResponse, Call]: ...

class StreamStreamMultiCallable[TRequest, TResponse](abc.ABC):
    @abc.abstractmethod
    def __call__(
        self,
        request_iterator: Iterator[_TRequest],
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: Compression | None = None,
    ) -> _CallIterator[_TResponse]: ...

def protos(protobuf_path: str) -> ModuleType: ...
def services(protobuf_path: str) -> ModuleType: ...
def protos_and_services(
    protobuf_path: str,
) -> tuple[ModuleType, ModuleType]: ...
