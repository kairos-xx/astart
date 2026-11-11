import unittest.case
import unittest.loader
import unittest.result
import unittest.suite
from collections.abc import Iterable
from types import ModuleType
from typing import Final, Protocol, type_check_only

MAIN_EXAMPLES: Final[str]
MODULE_EXAMPLES: Final[str]

@type_check_only
class _TestRunner(Protocol):
    def run(
        self,
        test: unittest.suite.TestSuite | unittest.case.TestCase,
        /,
    ) -> unittest.result.TestResult: ...

class TestProgram:
    result: unittest.result.TestResult
    module: ModuleType | None
    verbosity: int
    failfast: bool | None
    catchbreak: bool | None
    buffer: bool | None
    progName: str | None
    warnings: str | None
    testNamePatterns: list[str] | None
    durations: unittest.result._DurationsType | None
    def __init__(
        self,
        module: ModuleType | str | None = "__main__",
        defaultTest: str | Iterable[str] | None = None,
        argv: list[str] | None = None,
        testRunner: type[_TestRunner] | _TestRunner | None = None,
        testLoader: unittest.loader.TestLoader = ...,
        exit: bool = True,
        verbosity: int = 1,
        failfast: bool | None = None,
        catchbreak: bool | None = None,
        buffer: bool | None = None,
        warnings: str | None = None,
        *,
        tb_locals: bool = False,
        durations: unittest.result._DurationsType | None = None,
    ) -> None: ...
    def parseArgs(self, argv: list[str]) -> None: ...
    def createTests(
        self,
        from_discovery: bool = False,
        Loader: unittest.loader.TestLoader | None = None,
    ) -> None: ...
    def runTests(self) -> None: ...

main = TestProgram
