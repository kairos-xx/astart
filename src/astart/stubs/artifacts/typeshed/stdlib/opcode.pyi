import sys
from typing import Final, Literal

if sys.version_info >= (3, 15):
    from builtins import frozendict
__all__ = [
    "EXTENDED_ARG",
    "HAVE_ARGUMENT",
    "cmp_op",
    "hascompare",
    "hasconst",
    "hasfree",
    "hasjabs",
    "hasjrel",
    "haslocal",
    "hasname",
    "opmap",
    "opname",
    "stack_effect",
]
__all__ += ["hasarg", "hasexc"]
__all__ += ["hasjump"]
cmp_op: tuple[
    Literal["<"],
    Literal["<="],
    Literal["=="],
    Literal["!="],
    Literal[">"],
    Literal[">="],
]
hasconst: Final[list[int]]
hasname: Final[list[int]]
hasjrel: Final[list[int]]
hasjabs: Final[list[int]]
haslocal: Final[list[int]]
hascompare: Final[list[int]]
hasfree: Final[list[int]]
hasarg: Final[list[int]]
hasexc: Final[list[int]]
hasjump: Final[list[int]]
opname: Final[list[str]]
if sys.version_info >= (3, 15):
    opmap: Final[frozendict[str, int]]
else:
    opmap: Final[dict[str, int]]
HAVE_ARGUMENT: Final[int]
EXTENDED_ARG: Final[int]

def stack_effect(
    opcode: int,
    oparg: int | None = None,
    /,
    *,
    jump: bool | None = None,
) -> int: ...
