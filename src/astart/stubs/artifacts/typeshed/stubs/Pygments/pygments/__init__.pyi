from collections.abc import Iterable, Iterator
from typing import Final, TypeVar, overload

from _typeshed import SupportsWrite
from pygments.formatter import Formatter
from pygments.lexer import Lexer
from pygments.token import _TokenType

_T = TypeVar("_T", str, bytes)
__version__: Final[str]
__docformat__: Final = "restructuredtext"
__all__ = ["format", "highlight", "lex"]

def lex(code: str, lexer: Lexer) -> Iterator[tuple[_TokenType, str]]: ...
@overload
def format(
    tokens: Iterable[tuple[_TokenType, str]],
    formatter: Formatter[_T],
    outfile: SupportsWrite[_T],
) -> None: ...
@overload
def format[T: (str, bytes)](
    tokens: Iterable[tuple[_TokenType, str]],
    formatter: Formatter[_T],
    outfile: None = None,
) -> _T: ...
@overload
def highlight(
    code: str,
    lexer: Lexer,
    formatter: Formatter[_T],
    outfile: SupportsWrite[_T],
) -> None: ...
@overload
def highlight[T: (str, bytes)](
    code: str,
    lexer: Lexer,
    formatter: Formatter[_T],
    outfile: None = None,
) -> _T: ...
