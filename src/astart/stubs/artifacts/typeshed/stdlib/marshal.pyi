import builtins
import sys
import types
from typing import Any, Final

from _typeshed import ReadableBuffer, SupportsRead, SupportsWrite

version: Final[int]
type _Marshallable = (
    None
    | type[StopIteration]
    | builtins.ellipsis
    | bool
    | int
    | float
    | complex
    | bytes
    | str
    | tuple[_Marshallable, ...]
    | list[Any]
    | dict[Any, Any]
    | set[Any]
    | frozenset[_Marshallable]
    | types.CodeType
    | ReadableBuffer
)
if sys.version_info >= (3, 15):
    def dump(
        value: _Marshallable,
        file: SupportsWrite[bytes],
        version: int = 6,
        /,
        *,
        allow_code: bool = True,
    ) -> None: ...
    def dumps(
        value: _Marshallable,
        version: int = 6,
        /,
        *,
        allow_code: bool = True,
    ) -> bytes: ...
elif sys.version_info >= (3, 14):
    def dump(
        value: _Marshallable,
        file: SupportsWrite[bytes],
        version: int = 5,
        /,
        *,
        allow_code: bool = True,
    ) -> None: ...
    def dumps(
        value: _Marshallable,
        version: int = 5,
        /,
        *,
        allow_code: bool = True,
    ) -> bytes: ...
else:
    def dump(
        value: _Marshallable,
        file: SupportsWrite[bytes],
        version: int = 4,
        /,
        *,
        allow_code: bool = True,
    ) -> None: ...
    def dumps(
        value: _Marshallable,
        version: int = 4,
        /,
        *,
        allow_code: bool = True,
    ) -> bytes: ...

def load(file: SupportsRead[bytes], /, *, allow_code: bool = True) -> Any: ...
def loads(bytes: ReadableBuffer, /, *, allow_code: bool = True) -> Any: ...
