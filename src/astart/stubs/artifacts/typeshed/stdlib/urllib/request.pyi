import ssl
import sys
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from email.message import Message
from http.client import HTTPConnection, HTTPMessage, HTTPResponse
from http.cookiejar import CookieJar
from re import Pattern
from typing import (
    IO,
    Any,
    ClassVar,
    NoReturn,
    Protocol,
    TypeVar,
    overload,
    type_check_only,
)
from urllib.error import HTTPError as HTTPError
from urllib.response import addclosehook, addinfourl
from warnings import deprecated

from _typeshed import ReadableBuffer, StrOrBytesPath, SupportsRead

__all__ = [
    "AbstractBasicAuthHandler",
    "AbstractDigestAuthHandler",
    "BaseHandler",
    "CacheFTPHandler",
    "DataHandler",
    "FTPHandler",
    "FileHandler",
    "HTTPBasicAuthHandler",
    "HTTPCookieProcessor",
    "HTTPDefaultErrorHandler",
    "HTTPDigestAuthHandler",
    "HTTPErrorProcessor",
    "HTTPHandler",
    "HTTPPasswordMgr",
    "HTTPPasswordMgrWithDefaultRealm",
    "HTTPPasswordMgrWithPriorAuth",
    "HTTPRedirectHandler",
    "HTTPSHandler",
    "OpenerDirector",
    "ProxyBasicAuthHandler",
    "ProxyDigestAuthHandler",
    "ProxyHandler",
    "Request",
    "UnknownHandler",
    "build_opener",
    "getproxies",
    "install_opener",
    "pathname2url",
    "url2pathname",
    "urlcleanup",
    "urlopen",
    "urlretrieve",
]
if sys.version_info < (3, 14):
    __all__ += ["FancyURLopener", "URLopener"]
_T = TypeVar("_T")
type _UrlopenRet = Any
type _DataType = ReadableBuffer | SupportsRead[bytes] | Iterable[bytes] | None

def urlopen(
    url: str | Request,
    data: _DataType | None = None,
    timeout: float | None = ...,
    *,
    context: ssl.SSLContext | None = None,
) -> _UrlopenRet: ...
def install_opener(opener: OpenerDirector | None) -> None: ...
def build_opener(
    *handlers: BaseHandler | Callable[[], BaseHandler],
) -> OpenerDirector: ...

if sys.version_info >= (3, 14):
    def url2pathname(
        url: str,
        *,
        require_scheme: bool = False,
        resolve_host: bool = False,
    ) -> str: ...
    def pathname2url(pathname: str, *, add_scheme: bool = False) -> str: ...
elif sys.platform == "win32":
    from nturl2path import pathname2url as pathname2url
    from nturl2path import url2pathname as url2pathname
else:
    def url2pathname(pathname: str) -> str: ...
    def pathname2url(pathname: str) -> str: ...

def getproxies() -> dict[str, str]: ...
def getproxies_environment() -> dict[str, str]: ...
def parse_http_list(s: str) -> list[str]: ...
def parse_keqv_list(l: list[str]) -> dict[str, str]: ...

if sys.platform == "win32" or sys.platform == "darwin":
    def proxy_bypass(host: str) -> Any: ...
else:
    def proxy_bypass(
        host: str,
        proxies: Mapping[str, str] | None = None,
    ) -> Any: ...

class Request:
    @property
    def full_url(self) -> str: ...
    @full_url.setter
    def full_url(self, value: str) -> None: ...
    @full_url.deleter
    def full_url(self) -> None: ...
    type: str
    host: str
    origin_req_host: str
    selector: str
    data: _DataType
    headers: MutableMapping[str, str]
    unredirected_hdrs: dict[str, str]
    unverifiable: bool
    method: str | None
    timeout: float | None
    def __init__(
        self,
        url: str,
        data: _DataType = None,
        headers: MutableMapping[str, str] = {},
        origin_req_host: str | None = None,
        unverifiable: bool = False,
        method: str | None = None,
    ) -> None: ...
    def get_method(self) -> str: ...
    def add_header(self, key: str, val: str) -> None: ...
    def add_unredirected_header(self, key: str, val: str) -> None: ...
    def has_header(self, header_name: str) -> bool: ...
    def remove_header(self, header_name: str) -> None: ...
    def get_full_url(self) -> str: ...
    def set_proxy(self, host: str, type: str) -> None: ...
    @overload
    def get_header(self, header_name: str) -> str | None: ...
    @overload
    def get_header(self, header_name: str, default: _T) -> str | _T: ...
    def header_items(self) -> list[tuple[str, str]]: ...
    def has_proxy(self) -> bool: ...

class OpenerDirector:
    addheaders: list[tuple[str, str]]
    def add_handler(self, handler: BaseHandler) -> None: ...
    def open(
        self,
        fullurl: str | Request,
        data: _DataType = None,
        timeout: float | None = ...,
    ) -> _UrlopenRet: ...
    def error(self, proto: str, *args: Any) -> _UrlopenRet: ...
    def close(self) -> None: ...

class BaseHandler:
    handler_order: ClassVar[int]
    parent: OpenerDirector
    def add_parent(self, parent: OpenerDirector) -> None: ...
    def close(self) -> None: ...
    def __lt__(self, other: object) -> bool: ...

class HTTPDefaultErrorHandler(BaseHandler):
    def http_error_default(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        hdrs: HTTPMessage,
    ) -> HTTPError: ...

class HTTPRedirectHandler(BaseHandler):
    max_redirections: ClassVar[int]
    max_repeats: ClassVar[int]
    inf_msg: ClassVar[str]
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
        newurl: str,
    ) -> Request | None: ...
    def http_error_301(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...
    def http_error_302(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...
    def http_error_303(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...
    def http_error_307(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...
    def http_error_308(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...

class HTTPCookieProcessor(BaseHandler):
    cookiejar: CookieJar
    def __init__(self, cookiejar: CookieJar | None = None) -> None: ...
    def http_request(self, request: Request) -> Request: ...
    def http_response(
        self,
        request: Request,
        response: HTTPResponse,
    ) -> HTTPResponse: ...
    def https_request(self, request: Request) -> Request: ...
    def https_response(
        self,
        request: Request,
        response: HTTPResponse,
    ) -> HTTPResponse: ...

class ProxyHandler(BaseHandler):
    def __init__(self, proxies: dict[str, str] | None = None) -> None: ...
    def proxy_open(
        self,
        req: Request,
        proxy: str,
        type: str,
    ) -> _UrlopenRet | None: ...

class HTTPPasswordMgr:
    def add_password(
        self,
        realm: str,
        uri: str | Sequence[str],
        user: str,
        passwd: str,
    ) -> None: ...
    def find_user_password(
        self,
        realm: str,
        authuri: str,
    ) -> tuple[str | None, str | None]: ...
    def is_suburi(self, base: str, test: str) -> bool: ...
    def reduce_uri(
        self,
        uri: str,
        default_port: bool = True,
    ) -> tuple[str, str]: ...

class HTTPPasswordMgrWithDefaultRealm(HTTPPasswordMgr):
    def add_password(
        self,
        realm: str | None,
        uri: str | Sequence[str],
        user: str,
        passwd: str,
    ) -> None: ...
    def find_user_password(
        self,
        realm: str | None,
        authuri: str,
    ) -> tuple[str | None, str | None]: ...

class HTTPPasswordMgrWithPriorAuth(HTTPPasswordMgrWithDefaultRealm):
    def add_password(
        self,
        realm: str | None,
        uri: str | Sequence[str],
        user: str,
        passwd: str,
        is_authenticated: bool = False,
    ) -> None: ...
    def update_authenticated(
        self,
        uri: str | Sequence[str],
        is_authenticated: bool = False,
    ) -> None: ...
    def is_authenticated(self, authuri: str) -> bool | None: ...

class AbstractBasicAuthHandler:
    rx: ClassVar[Pattern[str]]
    passwd: HTTPPasswordMgr
    add_password: Callable[[str, str | Sequence[str], str, str], None]
    def __init__(
        self,
        password_mgr: HTTPPasswordMgr | None = None,
    ) -> None: ...
    def http_error_auth_reqed(
        self,
        authreq: str,
        host: str,
        req: Request,
        headers: HTTPMessage,
    ) -> None: ...
    def http_request(self, req: Request) -> Request: ...
    def http_response(
        self,
        req: Request,
        response: HTTPResponse,
    ) -> HTTPResponse: ...
    def https_request(self, req: Request) -> Request: ...
    def https_response(
        self,
        req: Request,
        response: HTTPResponse,
    ) -> HTTPResponse: ...
    def retry_http_basic_auth(
        self,
        host: str,
        req: Request,
        realm: str,
    ) -> _UrlopenRet | None: ...

class HTTPBasicAuthHandler(AbstractBasicAuthHandler, BaseHandler):
    auth_header: ClassVar[str]
    def http_error_401(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...

class ProxyBasicAuthHandler(AbstractBasicAuthHandler, BaseHandler):
    auth_header: ClassVar[str]
    def http_error_407(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...

class AbstractDigestAuthHandler:
    def __init__(self, passwd: HTTPPasswordMgr | None = None) -> None: ...
    def reset_retry_count(self) -> None: ...
    def http_error_auth_reqed(
        self,
        auth_header: str,
        host: str,
        req: Request,
        headers: HTTPMessage,
    ) -> None: ...
    def retry_http_digest_auth(
        self,
        req: Request,
        auth: str,
    ) -> _UrlopenRet | None: ...
    def get_cnonce(self, nonce: str) -> str: ...
    def get_authorization(
        self,
        req: Request,
        chal: Mapping[str, str],
    ) -> str | None: ...
    def get_algorithm_impls(
        self,
        algorithm: str,
    ) -> tuple[Callable[[str], str], Callable[[str, str], str]]: ...
    def get_entity_digest(
        self,
        data: ReadableBuffer | None,
        chal: Mapping[str, str],
    ) -> str | None: ...

class HTTPDigestAuthHandler(BaseHandler, AbstractDigestAuthHandler):
    auth_header: ClassVar[str]
    def http_error_401(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...

class ProxyDigestAuthHandler(BaseHandler, AbstractDigestAuthHandler):
    auth_header: ClassVar[str]
    def http_error_407(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> _UrlopenRet | None: ...

@type_check_only
class _HTTPConnectionProtocol(Protocol):
    def __call__(
        self,
        host: str,
        /,
        *,
        port: int | None = ...,
        timeout: float = ...,
        source_address: tuple[str, int] | None = ...,
        blocksize: int = ...,
    ) -> HTTPConnection: ...

class AbstractHTTPHandler(BaseHandler):
    def __init__(self, debuglevel: int | None = None) -> None: ...
    def set_http_debuglevel(self, level: int) -> None: ...
    def do_request_(self, request: Request) -> Request: ...
    def do_open(
        self,
        http_class: _HTTPConnectionProtocol,
        req: Request,
        **http_conn_args: Any,
    ) -> HTTPResponse: ...

class HTTPHandler(AbstractHTTPHandler):
    def http_open(self, req: Request) -> HTTPResponse: ...
    def http_request(self, request: Request) -> Request: ...

class HTTPSHandler(AbstractHTTPHandler):
    def __init__(
        self,
        debuglevel: int | None = None,
        context: ssl.SSLContext | None = None,
        check_hostname: bool | None = None,
    ) -> None: ...
    def https_open(self, req: Request) -> HTTPResponse: ...
    def https_request(self, request: Request) -> Request: ...

class FileHandler(BaseHandler):
    names: ClassVar[tuple[str, ...] | None]
    def file_open(self, req: Request) -> addinfourl: ...
    def get_names(self) -> tuple[str, ...]: ...
    def open_local_file(self, req: Request) -> addinfourl: ...

class DataHandler(BaseHandler):
    def data_open(self, req: Request) -> addinfourl: ...

class ftpwrapper:
    def __init__(
        self,
        user: str,
        passwd: str,
        host: str,
        port: int,
        dirs: str,
        timeout: float | None = None,
        persistent: bool = True,
    ) -> None: ...
    def close(self) -> None: ...
    def endtransfer(self) -> None: ...
    def file_close(self) -> None: ...
    def init(self) -> None: ...
    def real_close(self) -> None: ...
    def retrfile(
        self,
        file: str,
        type: str,
    ) -> tuple[addclosehook, int | None]: ...

class FTPHandler(BaseHandler):
    def ftp_open(self, req: Request) -> addinfourl: ...
    def connect_ftp(
        self,
        user: str,
        passwd: str,
        host: str,
        port: int,
        dirs: str,
        timeout: float,
    ) -> ftpwrapper: ...

class CacheFTPHandler(FTPHandler):
    def setTimeout(self, t: float) -> None: ...
    def setMaxConns(self, m: int) -> None: ...
    def check_cache(self) -> None: ...
    def clear_cache(self) -> None: ...

class UnknownHandler(BaseHandler):
    def unknown_open(self, req: Request) -> NoReturn: ...

class HTTPErrorProcessor(BaseHandler):
    def http_response(
        self,
        request: Request,
        response: HTTPResponse,
    ) -> _UrlopenRet: ...
    def https_response(
        self,
        request: Request,
        response: HTTPResponse,
    ) -> _UrlopenRet: ...

def urlretrieve(
    url: str,
    filename: StrOrBytesPath | None = None,
    reporthook: Callable[[int, int, int], object] | None = None,
    data: _DataType = None,
) -> tuple[str, HTTPMessage]: ...
def urlcleanup() -> None: ...

if sys.version_info < (3, 14):
    @deprecated(
        "Deprecated since Python 3.3; removed in Python 3.14. Use newer `urlopen` functions and methods.",
    )
    class URLopener:
        version: ClassVar[str]
        def __init__(
            self,
            proxies: dict[str, str] | None = None,
            **x509: str,
        ) -> None: ...
        def open(
            self,
            fullurl: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet: ...
        def open_unknown(
            self,
            fullurl: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet: ...
        def retrieve(
            self,
            url: str,
            filename: str | None = None,
            reporthook: Callable[[int, int, int], object] | None = None,
            data: ReadableBuffer | None = None,
        ) -> tuple[str, Message | None]: ...
        def addheader(self, *args: tuple[str, str]) -> None: ...
        def cleanup(self) -> None: ...
        def close(self) -> None: ...
        def http_error(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: bytes | None = None,
        ) -> _UrlopenRet: ...
        def http_error_default(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
        ) -> _UrlopenRet: ...
        def open_data(
            self,
            url: str,
            data: ReadableBuffer | None = None,
        ) -> addinfourl: ...
        def open_file(self, url: str) -> addinfourl: ...
        def open_ftp(self, url: str) -> addinfourl: ...
        def open_http(
            self,
            url: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet: ...
        def open_https(
            self,
            url: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet: ...
        def open_local_file(self, url: str) -> addinfourl: ...
        def open_unknown_proxy(
            self,
            proxy: str,
            fullurl: str,
            data: ReadableBuffer | None = None,
        ) -> None: ...
        def __del__(self) -> None: ...

    @deprecated(
        "Deprecated since Python 3.3; removed in Python 3.14. Use newer `urlopen` functions and methods.",
    )
    class FancyURLopener(URLopener):
        def prompt_user_passwd(
            self,
            host: str,
            realm: str,
        ) -> tuple[str, str]: ...
        def get_user_passwd(
            self,
            host: str,
            realm: str,
            clear_cache: int = 0,
        ) -> tuple[str, str]: ...
        def http_error_301(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | addinfourl | None: ...
        def http_error_302(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | addinfourl | None: ...
        def http_error_303(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | addinfourl | None: ...
        def http_error_307(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | addinfourl | None: ...
        def http_error_308(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | addinfourl | None: ...
        def http_error_401(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
            retry: bool = False,
        ) -> _UrlopenRet | None: ...
        def http_error_407(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None = None,
            retry: bool = False,
        ) -> _UrlopenRet | None: ...
        def http_error_default(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
        ) -> addinfourl: ...
        def redirect_internal(
            self,
            url: str,
            fp: IO[bytes],
            errcode: int,
            errmsg: str,
            headers: HTTPMessage,
            data: ReadableBuffer | None,
        ) -> _UrlopenRet | None: ...
        def retry_http_basic_auth(
            self,
            url: str,
            realm: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | None: ...
        def retry_https_basic_auth(
            self,
            url: str,
            realm: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | None: ...
        def retry_proxy_http_basic_auth(
            self,
            url: str,
            realm: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | None: ...
        def retry_proxy_https_basic_auth(
            self,
            url: str,
            realm: str,
            data: ReadableBuffer | None = None,
        ) -> _UrlopenRet | None: ...
