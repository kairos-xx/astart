import sys
from types import CodeType

__all__ = ["CommandCompiler", "Compile", "compile_command"]
if sys.version_info >= (3, 14):
    def compile_command(
        source: str,
        filename: str = "<input>",
        symbol: str = "single",
        flags: int = 0,
    ) -> CodeType | None: ...
else:
    def compile_command(
        source: str,
        filename: str = "<input>",
        symbol: str = "single",
    ) -> CodeType | None: ...

class Compile:
    flags: int
    def __call__(
        self,
        source: str,
        filename: str,
        symbol: str,
        flags: int = 0,
    ) -> CodeType: ...

class CommandCompiler:
    compiler: Compile
    def __call__(
        self,
        source: str,
        filename: str = "<input>",
        symbol: str = "single",
    ) -> CodeType | None: ...
