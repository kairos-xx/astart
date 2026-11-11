from typing import Protocol

class _Readable(Protocol):
    def read(self, size: int = ..., /) -> bytes: ...

from wsgiref.types import *
