import sys
from signal import _HANDLER, _SIGNUM

if sys.platform != "win32":
    def getsignal(signalnum: _SIGNUM) -> _HANDLER: ...
    def signal(signalnum: _SIGNUM, handler: _HANDLER) -> _HANDLER: ...
    def set_wakeup_fd(
        fd: int,
        /,
        *,
        warn_on_full_buffer: bool = True,
    ) -> int: ...
    __all__ = ["getsignal", "set_wakeup_fd", "signal"]
