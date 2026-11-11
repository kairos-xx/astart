__all__ = (
    "BrokenBarrierError",
    "CancelledError",
    "IncompleteReadError",
    "InvalidStateError",
    "LimitOverrunError",
    "SendfileNotAvailableError",
    "TimeoutError",
)

class CancelledError(BaseException): ...

from builtins import TimeoutError as TimeoutError

class InvalidStateError(Exception): ...
class SendfileNotAvailableError(RuntimeError): ...

class IncompleteReadError(EOFError):
    expected: int | None
    partial: bytes
    def __init__(self, partial: bytes, expected: int | None) -> None: ...

class LimitOverrunError(Exception):
    consumed: int
    def __init__(self, message: str, consumed: int) -> None: ...

class BrokenBarrierError(RuntimeError): ...
