from collections.abc import Container
from typing import Any

from _typeshed import Unused
from peewee import Database, ModelBase, Proxy

type _Flask = Any

class FlaskDB:
    database: Database | Proxy
    def __init__(
        self,
        app: _Flask | None = None,
        database: Database | Proxy | None = None,
        model_class=...,
        excluded_routes: Container[str] | None = None,
    ) -> None: ...
    def init_app(self, app: _Flask) -> None: ...
    def get_model_class(self) -> type[ModelBase]: ...
    @property
    def Model(self) -> type[ModelBase]: ...
    def connect_db(self) -> None: ...
    def close_db(self, exc: Unused) -> None: ...
