from typing import ClassVar, Literal

from lib2to3 import fixer_base

class FixItertoolsImports(fixer_base.BaseFix):
    BM_compatible: ClassVar[Literal[True]]
    PATTERN: ClassVar[str]
    def transform(self, node, results): ...
