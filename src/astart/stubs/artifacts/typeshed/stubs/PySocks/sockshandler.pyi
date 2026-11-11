import http.client
import ssl
import urllib.request
from typing import Any, TypeVar

import socks
from _typeshed import Incomplete, SupportsKeysAndGetItem

_K = TypeVar("_K")
_V = TypeVar("_V")

def merge_dict(
    a: dict[_K, _V],
    b: SupportsKeysAndGetItem[_K, _V],
) -> dict[_K, _V]: ...
def is_ip(s: str) -> bool: ...

socks4_no_rdns: set[str]

class SocksiPyConnection(http.client.HTTPConnection):
    proxyargs: tuple[int, str, int | None, bool, str | None, str | None]
    sock: socks.socksocket
    def __init__(
        self,
        proxytype: int,
        proxyaddr: str,
        proxyport: int | None = None,
        rdns: bool = True,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        timeout: float | None = ...,
        source_address: tuple[str, int] | None = None,
        blocksize: int = 8192,
    ) -> None: ...
    def connect(self) -> None: ...

class SocksiPyConnectionS(http.client.HTTPSConnection):
    proxyargs: tuple[int, str, int | None, bool, str | None, str | None]
    sock: socks.socksocket
    def __init__(
        self,
        proxytype: int,
        proxyaddr: str,
        proxyport: int | None = None,
        rdns: bool = True,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        *,
        timeout: float | None = ...,
        source_address: tuple[str, int] | None = None,
        context: ssl.SSLContext | None = None,
        blocksize: int = 8192,
    ) -> None: ...
    def connect(self) -> None: ...

class SocksiPyHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    args: tuple[Incomplete, ...]
    kw: dict[str, Incomplete]
    def __init__(
        self,
        proxytype: int,
        proxyaddr: str,
        proxyport: int | None = None,
        rdns: bool = True,
        username: str | None = None,
        password: str | None = None,
        *,
        source_address: tuple[str, int] | None = None,
        blocksize: int = 8192,
        **kwargs: Any,
    ) -> None: ...
    def http_open(
        self,
        req: urllib.request.Request,
    ) -> http.client.HTTPResponse: ...
    def https_open(
        self,
        req: urllib.request.Request,
    ) -> http.client.HTTPResponse: ...
