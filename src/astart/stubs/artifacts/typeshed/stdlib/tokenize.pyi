import sys
from collections.abc import Callable, Generator, Iterable, Sequence
from re import Pattern
from token import *
from typing import Any, Final, NamedTuple, TextIO, type_check_only

from _typeshed import FileDescriptorOrPath

__all__ = [
    "AMPER",
    "AMPEREQUAL",
    "AT",
    "ATEQUAL",
    "CIRCUMFLEX",
    "CIRCUMFLEXEQUAL",
    "COLON",
    "COLONEQUAL",
    "COMMA",
    "COMMENT",
    "DEDENT",
    "DOT",
    "DOUBLESLASH",
    "DOUBLESLASHEQUAL",
    "DOUBLESTAR",
    "DOUBLESTAREQUAL",
    "ELLIPSIS",
    "ENCODING",
    "ENDMARKER",
    "EQEQUAL",
    "EQUAL",
    "ERRORTOKEN",
    "GREATER",
    "GREATEREQUAL",
    "INDENT",
    "ISEOF",
    "ISNONTERMINAL",
    "ISTERMINAL",
    "LBRACE",
    "LEFTSHIFT",
    "LEFTSHIFTEQUAL",
    "LESS",
    "LESSEQUAL",
    "LPAR",
    "LSQB",
    "MINEQUAL",
    "MINUS",
    "NAME",
    "NEWLINE",
    "NL",
    "NOTEQUAL",
    "NT_OFFSET",
    "NUMBER",
    "N_TOKENS",
    "OP",
    "PERCENT",
    "PERCENTEQUAL",
    "PLUS",
    "PLUSEQUAL",
    "RARROW",
    "RBRACE",
    "RIGHTSHIFT",
    "RIGHTSHIFTEQUAL",
    "RPAR",
    "RSQB",
    "SEMI",
    "SLASH",
    "SLASHEQUAL",
    "SOFT_KEYWORD",
    "STAR",
    "STAREQUAL",
    "STRING",
    "TILDE",
    "TYPE_COMMENT",
    "TYPE_IGNORE",
    "VBAR",
    "VBAREQUAL",
    "TokenInfo",
    "detect_encoding",
    "generate_tokens",
    "tok_name",
    "tokenize",
    "untokenize",
]
__all__ += [
    "EXACT_TOKEN_TYPES",
    "EXCLAMATION",
    "FSTRING_END",
    "FSTRING_MIDDLE",
    "FSTRING_START",
]
__all__ += ["TokenError", "open"]
if sys.version_info >= (3, 14):
    __all__ += ["TSTRING_END", "TSTRING_MIDDLE", "TSTRING_START"]
cookie_re: Final[Pattern[str]]
blank_re: Final[Pattern[bytes]]
type _Position = tuple[int, int]

@type_check_only
class _TokenInfo(NamedTuple):
    type: int
    string: str
    start: _Position
    end: _Position
    line: str

class TokenInfo(_TokenInfo):
    @property
    def exact_type(self) -> int: ...

type _Token = TokenInfo | Sequence[int | str | _Position]

class TokenError(Exception): ...

class Untokenizer:
    tokens: list[str]
    prev_row: int
    prev_col: int
    encoding: str | None
    def add_whitespace(self, start: _Position) -> None: ...
    def add_backslash_continuation(self, start: _Position) -> None: ...
    def untokenize(self, iterable: Iterable[_Token]) -> str: ...
    def compat(
        self,
        token: Sequence[int | str],
        iterable: Iterable[_Token],
    ) -> None: ...
    def escape_brackets(self, token: str) -> str: ...

def untokenize(iterable: Iterable[_Token]) -> str | Any: ...
def detect_encoding(
    readline: Callable[[], bytes | bytearray],
) -> tuple[str, Sequence[bytes]]: ...
def tokenize(
    readline: Callable[[], bytes | bytearray],
) -> Generator[TokenInfo]: ...
def generate_tokens(readline: Callable[[], str]) -> Generator[TokenInfo]: ...
def open(filename: FileDescriptorOrPath) -> TextIO: ...
def group(*choices: str) -> str: ...
def any(*choices: str) -> str: ...
def maybe(*choices: str) -> str: ...

Whitespace: Final[str]
Comment: Final[str]
Ignore: Final[str]
Name: Final[str]
Hexnumber: Final[str]
Binnumber: Final[str]
Octnumber: Final[str]
Decnumber: Final[str]
Intnumber: Final[str]
Exponent: Final[str]
Pointfloat: Final[str]
Expfloat: Final[str]
Floatnumber: Final[str]
Imagnumber: Final[str]
Number: Final[str]

def _all_string_prefixes() -> set[str]: ...

StringPrefix: Final[str]
Single: Final[str]
Double: Final[str]
Single3: Final[str]
Double3: Final[str]
Triple: Final[str]
String: Final[str]
Special: Final[str]
Funny: Final[str]
PlainToken: Final[str]
Token: Final[str]
ContStr: Final[str]
PseudoExtras: Final[str]
PseudoToken: Final[str]
endpats: Final[dict[str, str]]
single_quoted: Final[set[str]]
triple_quoted: Final[set[str]]
tabsize: Final = 8
