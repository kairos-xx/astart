from collections.abc import Iterator, MutableMapping
from types import TracebackType
from typing import Literal, Self, type_check_only

from _typeshed import StrOrBytesPath

__all__ = ["error", "open", "whichdb"]
type _KeyType = str | bytes
type _ValueType = str | bytes | bytearray
type _TFlags = Literal[
    "r",
    "w",
    "c",
    "n",
    "rf",
    "wf",
    "cf",
    "nf",
    "rs",
    "ws",
    "cs",
    "ns",
    "ru",
    "wu",
    "cu",
    "nu",
    "rfs",
    "wfs",
    "cfs",
    "nfs",
    "rfu",
    "wfu",
    "cfu",
    "nfu",
    "rsf",
    "wsf",
    "csf",
    "nsf",
    "rsu",
    "wsu",
    "csu",
    "nsu",
    "ruf",
    "wuf",
    "cuf",
    "nuf",
    "rus",
    "wus",
    "cus",
    "nus",
    "rfsu",
    "wfsu",
    "cfsu",
    "nfsu",
    "rfus",
    "wfus",
    "cfus",
    "nfus",
    "rsfu",
    "wsfu",
    "csfu",
    "nsfu",
    "rsuf",
    "wsuf",
    "csuf",
    "nsuf",
    "rufs",
    "wufs",
    "cufs",
    "nufs",
    "rusf",
    "wusf",
    "cusf",
    "nusf",
]

@type_check_only
class _Database(MutableMapping[_KeyType, bytes]):
    def close(self) -> None: ...
    def __getitem__(self, key: _KeyType) -> bytes: ...
    def __setitem__(self, key: _KeyType, value: _ValueType) -> None: ...
    def __delitem__(self, key: _KeyType) -> None: ...
    def __iter__(self) -> Iterator[bytes]: ...
    def __len__(self) -> int: ...
    def __del__(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

@type_check_only
class _error(Exception): ...

error: tuple[type[_error], type[OSError]]

def whichdb(filename: StrOrBytesPath) -> str | None: ...
def open(
    file: StrOrBytesPath,
    flag: _TFlags = "r",
    mode: int = 0o666,
) -> _Database: ...
