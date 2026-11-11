from collections.abc import Callable
from io import DEFAULT_BUFFER_SIZE, BufferedIOBase, RawIOBase
from typing import Any, Protocol, type_check_only

from _typeshed import ReadableBuffer, WriteableBuffer

BUFFER_SIZE = DEFAULT_BUFFER_SIZE

@type_check_only
class _Reader(Protocol):
    def read(self, n: int, /) -> bytes: ...
    def seekable(self) -> bool: ...
    def seek(self, n: int, /) -> Any: ...

@type_check_only
class _Decompressor(Protocol):
    def decompress(
        self,
        data: ReadableBuffer,
        /,
        max_length: int = ...,
    ) -> bytes: ...
    @property
    def unused_data(self) -> bytes: ...
    @property
    def eof(self) -> bool: ...

class BaseStream(BufferedIOBase): ...

class DecompressReader(RawIOBase):
    def __init__(
        self,
        fp: _Reader,
        decomp_factory: Callable[..., _Decompressor],
        trailing_error: type[Exception] | tuple[type[Exception], ...] = (),
        **decomp_args: Any,
    ) -> None: ...
    def readinto(self, b: WriteableBuffer) -> int: ...
    def read(self, size: int = -1) -> bytes: ...
    def seek(self, offset: int, whence: int = 0) -> int: ...
