from collections.abc import Callable

from Xlib.error import XError
from Xlib.protocol.rq import Request

type ErrorHandler[_T] = Callable[[XError, Request | None], _T]
