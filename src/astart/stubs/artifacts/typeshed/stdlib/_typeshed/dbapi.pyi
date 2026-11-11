from collections.abc import Mapping, Sequence
from typing import Any, Protocol

type DBAPITypeCode = Any | None
type DBAPIColumnDescription = tuple[
    str,
    DBAPITypeCode,
    int | None,
    int | None,
    int | None,
    int | None,
    bool | None,
]

class DBAPIConnection(Protocol):
    def close(self) -> object: ...
    def commit(self) -> object: ...
    def cursor(self) -> DBAPICursor: ...

class DBAPICursor(Protocol):
    @property
    def description(self) -> Sequence[DBAPIColumnDescription] | None: ...
    @property
    def rowcount(self) -> int: ...
    def close(self) -> object: ...
    def execute(
        self,
        operation: str,
        parameters: Sequence[Any] | Mapping[str, Any] = ...,
        /,
    ) -> object: ...
    def executemany(
        self,
        operation: str,
        seq_of_parameters: Sequence[Sequence[Any]],
        /,
    ) -> object: ...
    def fetchone(self) -> Sequence[Any] | None: ...
    def fetchmany(self, size: int = ..., /) -> Sequence[Sequence[Any]]: ...
    def fetchall(self) -> Sequence[Sequence[Any]]: ...
    arraysize: int
    def setinputsizes(
        self,
        sizes: Sequence[DBAPITypeCode | int | None],
        /,
    ) -> object: ...
    def setoutputsize(self, size: int, column: int = ..., /) -> object: ...
