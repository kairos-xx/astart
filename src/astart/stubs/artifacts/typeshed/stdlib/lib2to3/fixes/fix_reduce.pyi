from typing import ClassVar, Literal

from lib2to3 import fixer_base

class FixReduce(fixer_base.BaseFix):
    BM_compatible: ClassVar[Literal[True]]
    order: ClassVar[Literal["pre"]]
    PATTERN: ClassVar[str]
    def transform(self, node, results) -> None: ...
