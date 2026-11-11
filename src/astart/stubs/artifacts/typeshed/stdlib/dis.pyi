import sys
import types
from collections.abc import Callable, Iterator
from opcode import *
from typing import IO, Any, Final, NamedTuple, Self, overload
from warnings import deprecated

__all__ = [
    "EXTENDED_ARG",
    "HAVE_ARGUMENT",
    "Bytecode",
    "Instruction",
    "cmp_op",
    "code_info",
    "dis",
    "disassemble",
    "disco",
    "distb",
    "findlabels",
    "findlinestarts",
    "get_instructions",
    "hascompare",
    "hasconst",
    "hasfree",
    "hasjabs",
    "hasjrel",
    "haslocal",
    "hasname",
    "opmap",
    "opname",
    "show_code",
    "stack_effect",
]
__all__ += ["hasjump"]
__all__ += ["hasarg", "hasexc"]
type _HaveCodeType = (
    types.MethodType
    | types.FunctionType
    | types.CodeType
    | type
    | Callable[..., Any]
)

class Positions(NamedTuple):
    lineno: int | None = None
    end_lineno: int | None = None
    col_offset: int | None = None
    end_col_offset: int | None = None

class _Instruction(NamedTuple):
    opname: str
    opcode: int
    arg: int | None
    argval: Any
    argrepr: str
    offset: int
    start_offset: int
    starts_line: bool
    line_number: int | None
    label: int | None = None
    positions: Positions | None = None
    cache_info: list[tuple[str, int, Any]] | None = None

class Instruction(_Instruction):
    @property
    def oparg(self) -> int: ...
    @property
    def baseopcode(self) -> int: ...
    @property
    def baseopname(self) -> str: ...
    @property
    def cache_offset(self) -> int: ...
    @property
    def end_offset(self) -> int: ...
    @property
    def jump_target(self) -> int: ...
    @property
    def is_jump_target(self) -> bool: ...
    if sys.version_info >= (3, 14):
        @staticmethod
        def make(
            opname: str,
            arg: int | None,
            argval: Any,
            argrepr: str,
            offset: int,
            start_offset: int,
            starts_line: bool,
            line_number: int | None,
            label: int | None = None,
            positions: Positions | None = None,
            cache_info: list[tuple[str, int, Any]] | None = None,
        ) -> Instruction: ...

class Bytecode:
    codeobj: types.CodeType
    first_line: int
    if sys.version_info >= (3, 14):
        show_positions: bool
        def __init__(
            self,
            x: _HaveCodeType | str,
            *,
            first_line: int | None = None,
            current_offset: int | None = None,
            show_caches: bool = False,
            adaptive: bool = False,
            show_offsets: bool = False,
            show_positions: bool = False,
        ) -> None: ...
    else:
        show_offsets: bool
        def __init__(
            self,
            x: _HaveCodeType | str,
            *,
            first_line: int | None = None,
            current_offset: int | None = None,
            show_caches: bool = False,
            adaptive: bool = False,
            show_offsets: bool = False,
        ) -> None: ...
    @classmethod
    def from_traceback(
        cls,
        tb: types.TracebackType,
        *,
        show_caches: bool = False,
        adaptive: bool = False,
    ) -> Self: ...
    def __iter__(self) -> Iterator[Instruction]: ...
    def info(self) -> str: ...
    def dis(self) -> str: ...

COMPILER_FLAG_NAMES: Final[dict[int, str]]

def findlabels(code: _HaveCodeType) -> list[int]: ...
def findlinestarts(code: _HaveCodeType) -> Iterator[tuple[int, int]]: ...
def pretty_flags(flags: int) -> str: ...
def code_info(x: _HaveCodeType | str) -> str: ...

if sys.version_info >= (3, 14):
    def dis(
        x: _HaveCodeType | str | bytes | bytearray | None = None,
        *,
        file: IO[str] | None = None,
        depth: int | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
        show_positions: bool = False,
    ) -> None: ...
    def disassemble(
        co: _HaveCodeType,
        lasti: int = -1,
        *,
        file: IO[str] | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
        show_positions: bool = False,
    ) -> None: ...
    def distb(
        tb: types.TracebackType | None = None,
        *,
        file: IO[str] | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
        show_positions: bool = False,
    ) -> None: ...
else:
    def dis(
        x: _HaveCodeType | str | bytes | bytearray | None = None,
        *,
        file: IO[str] | None = None,
        depth: int | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
    ) -> None: ...
    def disassemble(
        co: _HaveCodeType,
        lasti: int = -1,
        *,
        file: IO[str] | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
    ) -> None: ...
    def distb(
        tb: types.TracebackType | None = None,
        *,
        file: IO[str] | None = None,
        show_caches: bool = False,
        adaptive: bool = False,
        show_offsets: bool = False,
    ) -> None: ...

@overload
def get_instructions(
    x: _HaveCodeType,
    *,
    first_line: int | None = None,
    adaptive: bool = False,
) -> Iterator[Instruction]: ...
@overload
@deprecated(
    "The `show_caches` parameter is deprecated since Python 3.13. "
    "The iterator generates the `Instruction` instances with the `cache_info` field populated.",
)
def get_instructions(
    x: _HaveCodeType,
    *,
    first_line: int | None = None,
    show_caches: bool | None = None,
    adaptive: bool = False,
) -> Iterator[Instruction]: ...
def show_code(co: _HaveCodeType, *, file: IO[str] | None = None) -> None: ...

disco = disassemble
