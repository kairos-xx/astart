from ssl import *

import gevent.socket
from _typeshed import StrOrBytesPath

def wrap_socket(
    sock: gevent.socket.socket,
    keyfile: StrOrBytesPath | None = None,
    certfile: StrOrBytesPath | None = None,
    server_side: bool = False,
    cert_reqs: int = ...,
    ssl_version: int = ...,
    ca_certs: str | None = None,
    do_handshake_on_connect: bool = True,
    suppress_ragged_eofs: bool = True,
    ciphers: str | None = None,
) -> SSLSocket: ...
