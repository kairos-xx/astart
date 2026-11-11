import unittest.case
import unittest.result
import unittest.suite
from collections.abc import Callable, Iterable
from typing import (
    Any,
    Generic,
    Never,
    Protocol,
    TypeVar,
    type_check_only,
)
from warnings import _ActionKind

from _typeshed import SupportsFlush, SupportsWrite

type _ResultClassType = Callable[
    [_TextTestStream, bool, int],
    TextTestResult[Any],
]

@type_check_only
class _SupportsWriteAndFlush(SupportsWrite[str], SupportsFlush, Protocol): ...

@type_check_only
class _TextTestStream(_SupportsWriteAndFlush, Protocol):
    def writeln(self, arg: str | None = None, /) -> None: ...

class _WritelnDecorator:
    def __init__(self, stream: _SupportsWriteAndFlush) -> None: ...
    def writeln(self, arg: str | None = None) -> None: ...
    def __getattr__(self, attr: str) -> Any: ...
    stream: Never
    __getstate__: Never
    def flush(self) -> object: ...
    def write(self, s: str, /) -> object: ...

_StreamT = TypeVar(
    "_StreamT",
    bound=_TextTestStream,
    default=_WritelnDecorator,
)

class TextTestResult(unittest.result.TestResult, Generic[_StreamT]):
    descriptions: bool
    dots: bool
    separator1: str
    separator2: str
    showAll: bool
    stream: _StreamT
    durations: int | None
    def __init__(
        self,
        stream: _StreamT,
        descriptions: bool,
        verbosity: int,
        *,
        durations: int | None = None,
    ) -> None: ...
    def getDescription(self, test: unittest.case.TestCase) -> str: ...
    def printErrorList(
        self,
        flavour: str,
        errors: Iterable[tuple[unittest.case.TestCase, str]],
    ) -> None: ...

class TextTestRunner:
    resultclass: _ResultClassType
    stream: _WritelnDecorator
    descriptions: bool
    verbosity: int
    failfast: bool
    buffer: bool
    warnings: _ActionKind | None
    tb_locals: bool
    durations: int | None
    def __init__(
        self,
        stream: _SupportsWriteAndFlush | None = None,
        descriptions: bool = True,
        verbosity: int = 1,
        failfast: bool = False,
        buffer: bool = False,
        resultclass: _ResultClassType | None = None,
        warnings: _ActionKind | None = None,
        *,
        tb_locals: bool = False,
        durations: int | None = None,
    ) -> None: ...
    def _makeResult(self) -> TextTestResult: ...
    def run(
        self,
        test: unittest.suite.TestSuite | unittest.case.TestCase,
    ) -> TextTestResult: ...
