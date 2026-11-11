from codeop import CommandCompiler
from codeop import compile_command as compile_command
from collections.abc import Callable
from types import CodeType
from typing import Any

__all__ = [
    "InteractiveConsole",
    "InteractiveInterpreter",
    "compile_command",
    "interact",
]

class InteractiveInterpreter:
    locals: dict[str, Any]
    compile: CommandCompiler
    def __init__(self, locals: dict[str, Any] | None = None) -> None: ...
    def runsource(
        self,
        source: str,
        filename: str = "<input>",
        symbol: str = "single",
    ) -> bool: ...
    def runcode(self, code: CodeType) -> None: ...
    def showsyntaxerror(
        self,
        filename: str | None = None,
        *,
        source: str = "",
    ) -> None: ...
    def showtraceback(self) -> None: ...
    def write(self, data: str) -> None: ...

class InteractiveConsole(InteractiveInterpreter):
    buffer: list[str]
    filename: str
    local_exit: bool
    def __init__(
        self,
        locals: dict[str, Any] | None = None,
        filename: str = "<console>",
        *,
        local_exit: bool = False,
    ) -> None: ...
    def push(self, line: str, filename: str | None = None) -> bool: ...
    def interact(
        self,
        banner: str | None = None,
        exitmsg: str | None = None,
    ) -> None: ...
    def resetbuffer(self) -> None: ...
    def raw_input(self, prompt: str = "") -> str: ...

def interact(
    banner: str | None = None,
    readfunc: Callable[[str], str] | None = None,
    local: dict[str, Any] | None = None,
    exitmsg: str | None = None,
    local_exit: bool = False,
) -> None: ...
