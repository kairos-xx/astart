import abc
import sys
from _io import (
    DEFAULT_BUFFER_SIZE as DEFAULT_BUFFER_SIZE,
)
from _io import (
    BlockingIOError as BlockingIOError,
)
from _io import (
    BufferedRandom as BufferedRandom,
)
from _io import (
    BufferedReader as BufferedReader,
)
from _io import (
    BufferedRWPair as BufferedRWPair,
)
from _io import (
    BufferedWriter as BufferedWriter,
)
from _io import (
    BytesIO as BytesIO,
)
from _io import (
    FileIO as FileIO,
)
from _io import (
    IncrementalNewlineDecoder as IncrementalNewlineDecoder,
)
from _io import (
    StringIO as StringIO,
)
from _io import (
    TextIOWrapper as TextIOWrapper,
)
from _io import (
    _BufferedIOBase,
    _IOBase,
    _RawIOBase,
    _TextIOBase,
)
from _io import (
    _WrappedBuffer as _WrappedBuffer,
)
from _io import (
    open as open,
)
from _io import (
    open_code as open_code,
)
from typing import Final, Protocol, TypeVar

__all__ = [
    "SEEK_CUR",
    "SEEK_END",
    "SEEK_SET",
    "BlockingIOError",
    "BufferedIOBase",
    "BufferedRWPair",
    "BufferedRandom",
    "BufferedReader",
    "BufferedWriter",
    "BytesIO",
    "FileIO",
    "IOBase",
    "RawIOBase",
    "StringIO",
    "TextIOBase",
    "TextIOWrapper",
    "UnsupportedOperation",
    "open",
    "open_code",
]
if sys.version_info >= (3, 14):
    __all__ += ["Reader", "Writer"]
from _io import text_encoding as text_encoding

__all__ += [
    "DEFAULT_BUFFER_SIZE",
    "IncrementalNewlineDecoder",
    "text_encoding",
]
_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)
SEEK_SET: Final = 0
SEEK_CUR: Final = 1
SEEK_END: Final = 2

class UnsupportedOperation(OSError, ValueError): ...
class IOBase(_IOBase, metaclass=abc.ABCMeta): ...
class RawIOBase(_RawIOBase, IOBase): ...
class BufferedIOBase(_BufferedIOBase, IOBase): ...
class TextIOBase(_TextIOBase, IOBase): ...

if sys.version_info >= (3, 14):
    class Reader(Protocol[_T_co]):
        __slots__ = ()
        def read(self, size: int = ..., /) -> _T_co: ...

    class Writer(Protocol[_T_contra]):
        __slots__ = ()
        def write(self, data: _T_contra, /) -> int: ...
