from typing import ClassVar, Literal

from lib2to3 import fixer_base

class FixLong(fixer_base.BaseFix):
    BM_compatible: ClassVar[Literal[True]]
    PATTERN: ClassVar[Literal["'long'"]]
    def transform(self, node, results) -> None: ...
