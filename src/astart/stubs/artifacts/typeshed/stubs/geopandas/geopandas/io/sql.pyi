import sqlite3
from collections.abc import Container, Iterator, Mapping
from contextlib import AbstractContextManager
from typing import Any, Protocol, Self, overload, type_check_only

from _typeshed import Incomplete, SupportsLenAndGetItem
from pandas._typing import Scalar

from ..base import _ConvertibleToCRS
from ..geodataframe import GeoDataFrame

@type_check_only
class _SqlalchemyTransactionLike(Protocol):
    def close(self) -> None: ...
    def rollback(self) -> None: ...
    def commit(self) -> None: ...

@type_check_only
class _SqlAlchemyEventTarget(Protocol):
    dispatch: Any

@type_check_only
class _SqlalchemyConnectionLike(_SqlAlchemyEventTarget, Protocol):
    engine: Any
    @property
    def closed(self) -> bool: ...
    @property
    def invalidated(self) -> bool: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, type_, value, traceback, /) -> None: ...
    @property
    def info(self) -> dict[Any, Any]: ...
    def invalidate(self, exception: BaseException | None = None) -> None: ...
    def detach(self) -> None: ...
    def begin(self) -> _SqlalchemyTransactionLike: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def recover_twophase(self) -> list[Any]: ...
    def rollback_prepared(self, xid: Any, recover: bool = ...) -> None: ...
    def commit_prepared(self, xid: Any, recover: bool = ...) -> None: ...
    def in_transaction(self) -> bool: ...
    def in_nested_transaction(self) -> bool: ...
    def close(self) -> None: ...

@type_check_only
class _SqlalchemyEngineLike(_SqlAlchemyEventTarget, Protocol):
    dialect: Any
    pool: Any
    url: Any
    hide_parameters: bool
    @property
    def engine(self) -> _SqlalchemyEngineLike: ...
    def clear_compiled_cache(self) -> None: ...
    def update_execution_options(self, **opt: Any) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def driver(self) -> str: ...
    def dispose(self, close: bool = True) -> None: ...
    def begin(self) -> AbstractContextManager[Any]: ...
    def connect(self) -> Any: ...

type _SqlalchemyConnectableLike = (
    _SqlalchemyConnectionLike | _SqlalchemyEngineLike
)
type _SQLConnection = str | _SqlalchemyConnectableLike | sqlite3.Connection

@overload
def _read_postgis(
    sql: str,
    con: _SQLConnection,
    geom_col: str = "geom",
    crs: _ConvertibleToCRS | None = None,
    index_col: str | Container[str] | None = None,
    coerce_float: bool = True,
    parse_dates: Container[str | Mapping[str, Incomplete]]
    | Mapping[str, str | Mapping[str, Incomplete]]
    | None = None,
    params: SupportsLenAndGetItem[Scalar] | Mapping[str, Scalar] | None = None,
    *,
    chunksize: int,
) -> Iterator[GeoDataFrame]: ...
@overload
def _read_postgis(
    sql: str,
    con: _SQLConnection,
    geom_col: str = "geom",
    crs: _ConvertibleToCRS | None = None,
    index_col: str | Container[str] | None = None,
    coerce_float: bool = True,
    parse_dates: Container[str | Mapping[str, Incomplete]]
    | Mapping[str, str | Mapping[str, Incomplete]]
    | None = None,
    params: SupportsLenAndGetItem[Scalar] | Mapping[str, Scalar] | None = None,
    chunksize: None = None,
) -> GeoDataFrame: ...
@overload
def _read_postgis(
    sql: str,
    con: _SQLConnection,
    geom_col: str = "geom",
    crs: _ConvertibleToCRS | None = None,
    index_col: str | Container[str] | None = None,
    coerce_float: bool = True,
    parse_dates: Container[str | Mapping[str, Incomplete]]
    | Mapping[str, str | Mapping[str, Incomplete]]
    | None = None,
    params: SupportsLenAndGetItem[Scalar] | Mapping[str, Scalar] | None = None,
    chunksize: int | None = None,
) -> GeoDataFrame | Iterator[GeoDataFrame]: ...
