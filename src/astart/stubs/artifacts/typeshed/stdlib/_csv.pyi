import csv
from collections.abc import Iterable
from typing import Any, Final, Literal, Self

from _typeshed import SupportsWrite
from typing_extensions import disjoint_base

__version__: Final[str]
QUOTE_ALL: Final = 1
QUOTE_MINIMAL: Final = 0
QUOTE_NONE: Final = 3
QUOTE_NONNUMERIC: Final = 2
QUOTE_STRINGS: Final = 4
QUOTE_NOTNULL: Final = 5
type _QuotingType = Literal[0, 1, 2, 3, 4, 5]

class Error(Exception): ...

type _DialectLike = str | Dialect | csv.Dialect | type[Dialect | csv.Dialect]

@disjoint_base
class Dialect:
    delimiter: str
    quotechar: str | None
    escapechar: str | None
    doublequote: bool
    skipinitialspace: bool
    lineterminator: str
    quoting: _QuotingType
    strict: bool
    def __new__(
        cls,
        dialect: _DialectLike | None = None,
        delimiter: str = ",",
        doublequote: bool = True,
        escapechar: str | None = None,
        lineterminator: str = "\r\n",
        quotechar: str | None = '"',
        quoting: _QuotingType = 0,
        skipinitialspace: bool = False,
        strict: bool = False,
    ) -> Self: ...

@disjoint_base
class Reader:
    @property
    def dialect(self) -> Dialect: ...
    line_num: int
    def __iter__(self) -> Self: ...
    def __next__(self) -> list[str]: ...

@disjoint_base
class Writer:
    @property
    def dialect(self) -> Dialect: ...
    def writerow(self, row: Iterable[Any], /) -> Any: ...
    def writerows(self, rows: Iterable[Iterable[Any]], /) -> None: ...

def writer(
    fileobj: SupportsWrite[str],
    /,
    dialect: _DialectLike = "excel",
    *,
    delimiter: str = ",",
    quotechar: str | None = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    skipinitialspace: bool = False,
    lineterminator: str = "\r\n",
    quoting: _QuotingType = 0,
    strict: bool = False,
) -> Writer: ...
def reader(
    iterable: Iterable[str],
    /,
    dialect: _DialectLike = "excel",
    *,
    delimiter: str = ",",
    quotechar: str | None = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    skipinitialspace: bool = False,
    lineterminator: str = "\r\n",
    quoting: _QuotingType = 0,
    strict: bool = False,
) -> Reader: ...
def register_dialect(
    name: str,
    /,
    dialect: type[Dialect | csv.Dialect] | str = "excel",
    *,
    delimiter: str = ",",
    quotechar: str | None = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    skipinitialspace: bool = False,
    lineterminator: str = "\r\n",
    quoting: _QuotingType = 0,
    strict: bool = False,
) -> None: ...
def unregister_dialect(name: str) -> None: ...
def get_dialect(name: str) -> Dialect: ...
def list_dialects() -> list[str]: ...
def field_size_limit(new_limit: int = ...) -> int: ...
