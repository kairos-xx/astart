import types
from collections.abc import Iterable, Sequence
from typing import Any, ClassVar, TypeVar, overload

from _typeshed import SupportsWrite
from pygments.style import Style
from pygments.token import _TokenType

_T = TypeVar("_T", str, bytes)
__all__ = ["Formatter"]

class Formatter[T: (str, bytes)]:
    name: ClassVar[str]
    aliases: ClassVar[Sequence[str]]
    filenames: ClassVar[Sequence[str]]
    unicodeoutput: ClassVar[bool]
    style: type[Style]
    full: bool
    title: str
    encoding: str | None
    options: dict[str, Any]
    @overload
    def __init__(
        self: Formatter[str],
        *,
        style: type[Style] | str = "default",
        full: bool = False,
        title: str = "",
        encoding: None = None,
        outencoding: None = None,
        **options: Any,
    ) -> None: ...
    @overload
    def __init__(
        self: Formatter[bytes],
        *,
        style: type[Style] | str = "default",
        full: bool = False,
        title: str = "",
        encoding: str,
        outencoding: None = None,
        **options: Any,
    ) -> None: ...
    @overload
    def __init__(
        self: Formatter[bytes],
        *,
        style: type[Style] | str = "default",
        full: bool = False,
        title: str = "",
        encoding: None = None,
        outencoding: str,
        **options: Any,
    ) -> None: ...
    def __class_getitem__(cls, name: Any) -> types.GenericAlias: ...
    def get_style_defs(self, arg: str = "") -> str: ...
    def format(
        self,
        tokensource: Iterable[tuple[_TokenType, str]],
        outfile: SupportsWrite[_T],
    ) -> None: ...
