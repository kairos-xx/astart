from socket import *

from gevent._hub_primitives import (
    wait_on_watcher,
)
from gevent._hub_primitives import (
    wait_read as wait_read,
)
from gevent._hub_primitives import (
    wait_readwrite as wait_readwrite,
)
from gevent._hub_primitives import (
    wait_write as wait_write,
)
from gevent._types import _Watcher

wait = wait_on_watcher

def cancel_wait(
    watcher: _Watcher,
    error: type[BaseException] | BaseException,
) -> None: ...
