import unittest.case
import unittest.suite
from collections.abc import Callable, Sequence
from re import Pattern
from types import ModuleType
from typing import Final

type _SortComparisonMethod = Callable[[str, str], int]
type _SuiteClass = Callable[
    [list[unittest.case.TestCase]],
    unittest.suite.TestSuite,
]
VALID_MODULE_NAME: Final[Pattern[str]]

class TestLoader:
    errors: list[type[BaseException]]
    testMethodPrefix: str
    sortTestMethodsUsing: _SortComparisonMethod
    testNamePatterns: list[str] | None
    suiteClass: _SuiteClass
    def loadTestsFromTestCase(
        self,
        testCaseClass: type[unittest.case.TestCase],
    ) -> unittest.suite.TestSuite: ...
    def loadTestsFromModule(
        self,
        module: ModuleType,
        *,
        pattern: str | None = None,
    ) -> unittest.suite.TestSuite: ...
    def loadTestsFromName(
        self,
        name: str,
        module: ModuleType | None = None,
    ) -> unittest.suite.TestSuite: ...
    def loadTestsFromNames(
        self,
        names: Sequence[str],
        module: ModuleType | None = None,
    ) -> unittest.suite.TestSuite: ...
    def getTestCaseNames(
        self,
        testCaseClass: type[unittest.case.TestCase],
    ) -> Sequence[str]: ...
    def discover(
        self,
        start_dir: str,
        pattern: str = "test*.py",
        top_level_dir: str | None = None,
    ) -> unittest.suite.TestSuite: ...
    def _match_path(self, path: str, full_path: str, pattern: str) -> bool: ...

defaultTestLoader: TestLoader
