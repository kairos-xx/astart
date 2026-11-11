from collections.abc import Mapping
from typing import Any

from yaml.emitter import Emitter
from yaml.representer import BaseRepresenter, Representer, SafeRepresenter
from yaml.resolver import BaseResolver, Resolver
from yaml.serializer import Serializer

from .emitter import _WriteStream

type _Inf = float

class BaseDumper(Emitter, Serializer, BaseRepresenter, BaseResolver):
    def __init__(
        self,
        stream: _WriteStream[Any],
        default_style: str | None = None,
        default_flow_style: bool | None = False,
        canonical: bool | None = None,
        indent: int | None = None,
        width: int | _Inf | None = None,
        allow_unicode: bool | None = None,
        line_break: str | None = None,
        encoding: str | None = None,
        explicit_start: bool | None = None,
        explicit_end: bool | None = None,
        version: tuple[int, int] | None = None,
        tags: Mapping[str, str] | None = None,
        sort_keys: bool = True,
    ) -> None: ...

class SafeDumper(Emitter, Serializer, SafeRepresenter, Resolver):
    def __init__(
        self,
        stream: _WriteStream[Any],
        default_style: str | None = None,
        default_flow_style: bool | None = False,
        canonical: bool | None = None,
        indent: int | None = None,
        width: int | _Inf | None = None,
        allow_unicode: bool | None = None,
        line_break: str | None = None,
        encoding: str | None = None,
        explicit_start: bool | None = None,
        explicit_end: bool | None = None,
        version: tuple[int, int] | None = None,
        tags: Mapping[str, str] | None = None,
        sort_keys: bool = True,
    ) -> None: ...

class Dumper(Emitter, Serializer, Representer, Resolver):
    def __init__(
        self,
        stream: _WriteStream[Any],
        default_style: str | None = None,
        default_flow_style: bool | None = False,
        canonical: bool | None = None,
        indent: int | None = None,
        width: int | _Inf | None = None,
        allow_unicode: bool | None = None,
        line_break: str | None = None,
        encoding: str | None = None,
        explicit_start: bool | None = None,
        explicit_end: bool | None = None,
        version: tuple[int, int] | None = None,
        tags: Mapping[str, str] | None = None,
        sort_keys: bool = True,
    ) -> None: ...

__all__ = ["BaseDumper", "Dumper", "SafeDumper"]
