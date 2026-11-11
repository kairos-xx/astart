import sys
from types import TracebackType
from typing import Final, Self, TypeVar, final, overload, type_check_only

from _typeshed import ReadOnlyBuffer, StrOrBytesPath

if sys.platform != "win32":
    _T = TypeVar("_T")
    type _KeyType = str | ReadOnlyBuffer
    type _ValueType = str | ReadOnlyBuffer

    class error(OSError): ...
    library: Final[str]

    # Actual typename dbm, not exposed by the implementation
    @final
    @type_check_only
    class _dbm:
        def close(self) -> None: ...
        def clear(self) -> None: ...
        def __getitem__(self, item: _KeyType) -> bytes: ...
        def __setitem__(self, key: _KeyType, value: _ValueType) -> None: ...
        def __delitem__(self, key: _KeyType) -> None: ...
        def __len__(self) -> int: ...
        def __enter__(self) -> Self: ...
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ) -> None: ...
        @overload
        def get(self, k: _KeyType, /) -> bytes | None: ...
        @overload
        def get(self, k: _KeyType, default: _T, /) -> bytes | _T: ...
        def keys(self) -> list[bytes]: ...
        def setdefault(
            self,
            k: _KeyType,
            default: _ValueType = b"",
            /,
        ) -> bytes: ...
        # This isn't true, but the class can't be instantiated. See #13024
        __new__: None  # type: ignore[assignment]
        __init__: None  # type: ignore[assignment]

    def open(
        filename: StrOrBytesPath,
        flags: str = "r",
        mode: int = 0o666,
        /,
    ) -> _dbm: ...
