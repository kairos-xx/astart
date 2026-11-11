from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from typing import Any, LiteralString

from _typeshed import FileDescriptor

type _StatusType = str
type _HeadersType = Iterable[tuple[str, str]]
type _EnvironType = MutableMapping[str, Any]
type _StartResponseType = Callable[[_StatusType, _HeadersType], None]
type _ResponseBodyType = Iterable[bytes]
type _WSGIAppType = Callable[
    [_EnvironType, _StartResponseType],
    _ResponseBodyType,
]
type _ScopeType = MutableMapping[str, Any]
type _MessageType = MutableMapping[str, Any]
type _ReceiveType = Callable[[], Awaitable[_MessageType]]
type _SendType = Callable[[_MessageType], Awaitable[None]]
type _ASGIAppType = Callable[
    [_ScopeType, _ReceiveType, _SendType],
    Awaitable[None],
]
type _UnixSocketPathType = str
type _TcpAddressType = tuple[LiteralString, int]
type _AddressType = _UnixSocketPathType | FileDescriptor | _TcpAddressType
