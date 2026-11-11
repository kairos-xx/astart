import sys

from ._base import (
    ALL_COMPLETED as ALL_COMPLETED,
)
from ._base import (
    FIRST_COMPLETED as FIRST_COMPLETED,
)
from ._base import (
    FIRST_EXCEPTION as FIRST_EXCEPTION,
)
from ._base import (
    BrokenExecutor as BrokenExecutor,
)
from ._base import (
    CancelledError as CancelledError,
)
from ._base import (
    Executor as Executor,
)
from ._base import (
    Future as Future,
)
from ._base import (
    InvalidStateError as InvalidStateError,
)
from ._base import (
    TimeoutError as TimeoutError,
)
from ._base import (
    as_completed as as_completed,
)
from ._base import (
    wait as wait,
)
from .process import ProcessPoolExecutor as ProcessPoolExecutor
from .thread import ThreadPoolExecutor as ThreadPoolExecutor

if sys.version_info >= (3, 14):
    from .interpreter import InterpreterPoolExecutor as InterpreterPoolExecutor

    __all__ = [
        "ALL_COMPLETED",
        "FIRST_COMPLETED",
        "FIRST_EXCEPTION",
        "BrokenExecutor",
        "CancelledError",
        "Executor",
        "Future",
        "InterpreterPoolExecutor",
        "InvalidStateError",
        "ProcessPoolExecutor",
        "ThreadPoolExecutor",
        "TimeoutError",
        "as_completed",
        "wait",
    ]
else:
    __all__ = (
        "ALL_COMPLETED",
        "FIRST_COMPLETED",
        "FIRST_EXCEPTION",
        "BrokenExecutor",
        "CancelledError",
        "Executor",
        "Future",
        "InvalidStateError",
        "ProcessPoolExecutor",
        "ThreadPoolExecutor",
        "TimeoutError",
        "as_completed",
        "wait",
    )

def __dir__() -> tuple[str, ...]: ...
