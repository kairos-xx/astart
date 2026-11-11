from collections.abc import Hashable

import psycopg2
from _typeshed import ConvertibleToInt
from psycopg2.extensions import connection

class PoolError(psycopg2.Error): ...

class AbstractConnectionPool:
    minconn: int
    maxconn: int
    closed: bool
    def __init__(
        self,
        minconn: ConvertibleToInt,
        maxconn: ConvertibleToInt,
        *args,
        **kwargs,
    ) -> None: ...
    def getconn(self, key: Hashable | None = None) -> connection: ...
    def putconn(
        self,
        conn: connection,
        key: Hashable | None = None,
        close: bool = False,
    ) -> None: ...
    def closeall(self) -> None: ...

class SimpleConnectionPool(AbstractConnectionPool): ...

class ThreadedConnectionPool(AbstractConnectionPool):
    def putconn(
        self,
        conn: connection | None = None,
        key: Hashable | None = None,
        close: bool = False,
    ) -> None: ...
