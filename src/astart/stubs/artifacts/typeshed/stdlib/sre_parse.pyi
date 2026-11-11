from collections.abc import Iterable
from re import Pattern as _Pattern
from sre_constants import *
from sre_constants import _NamedIntConstant as _NIC
from sre_constants import error as _Error
from typing import Any, Final, overload

SPECIAL_CHARS: Final = ".\\[{()*+?^$|"
REPEAT_CHARS: Final = "*+?{"
DIGITS: Final[frozenset[str]]
OCTDIGITS: Final[frozenset[str]]
HEXDIGITS: Final[frozenset[str]]
ASCIILETTERS: Final[frozenset[str]]
WHITESPACE: Final[frozenset[str]]
ESCAPES: Final[dict[str, tuple[_NIC, int]]]
CATEGORIES: Final[
    dict[str, tuple[_NIC, _NIC] | tuple[_NIC, list[tuple[_NIC, _NIC]]]]
]
FLAGS: Final[dict[str, int]]
TYPE_FLAGS: Final[int]
GLOBAL_FLAGS: Final[int]
MAXWIDTH: Final[int]
type _OpSubpatternType = tuple[int | None, int, int, SubPattern]
type _OpGroupRefExistsType = tuple[int, SubPattern, SubPattern]
type _OpInType = list[tuple[_NIC, int]]
type _OpBranchType = tuple[None, list[SubPattern]]
type _AvType = (
    _OpInType
    | _OpBranchType
    | Iterable[SubPattern]
    | _OpGroupRefExistsType
    | _OpSubpatternType
)
type _CodeType = tuple[_NIC, _AvType]

class State:
    flags: int
    groupdict: dict[str, int]
    groupwidths: list[int | None]
    lookbehindgroups: int | None
    @property
    def groups(self) -> int: ...
    def opengroup(self, name: str | None = None) -> int: ...
    def closegroup(self, gid: int, p: SubPattern) -> None: ...
    def checkgroup(self, gid: int) -> bool: ...
    def checklookbehindgroup(self, gid: int, source: Tokenizer) -> None: ...

class SubPattern:
    data: list[_CodeType]
    width: int | None
    state: State
    def __init__(
        self,
        state: State,
        data: list[_CodeType] | None = None,
    ) -> None: ...
    def dump(self, level: int = 0) -> None: ...
    def __len__(self) -> int: ...
    def __delitem__(self, index: int | slice) -> None: ...
    def __getitem__(self, index: int | slice) -> SubPattern | _CodeType: ...
    def __setitem__(self, index: int | slice, code: _CodeType) -> None: ...
    def insert(self, index: int, code: _CodeType) -> None: ...
    def append(self, code: _CodeType) -> None: ...
    def getwidth(self) -> tuple[int, int]: ...

class Tokenizer:
    istext: bool
    string: Any
    decoded_string: str
    index: int
    next: str | None
    def __init__(self, string: Any) -> None: ...
    def match(self, char: str) -> bool: ...
    def get(self) -> str | None: ...
    def getwhile(self, n: int, charset: Iterable[str]) -> str: ...
    def getuntil(self, terminator: str, name: str) -> str: ...
    @property
    def pos(self) -> int: ...
    def tell(self) -> int: ...
    def seek(self, index: int) -> None: ...
    def error(self, msg: str, offset: int = 0) -> _Error: ...
    def checkgroupname(self, name: str, offset: int) -> None: ...

def fix_flags(src: str | bytes, flags: int) -> int: ...

type _TemplateType = tuple[list[tuple[int, int]], list[str | None]]
type _TemplateByteType = tuple[list[tuple[int, int]], list[bytes | None]]

@overload
def parse_template(source: str, pattern: _Pattern[Any]) -> _TemplateType: ...
@overload
def parse_template(
    source: bytes,
    pattern: _Pattern[Any],
) -> _TemplateByteType: ...
def parse(
    str: str,
    flags: int = 0,
    state: State | None = None,
) -> SubPattern: ...
