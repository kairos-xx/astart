from typing import NotRequired, TypedDict, type_check_only

from _typeshed import Unused

from .sources import Source

@type_check_only
class _Instruction(TypedDict):
    address: str
    instruction: str
    instructionBytes: str
    symbol: NotRequired[str]
    line: NotRequired[int]
    location: NotRequired[Source]

@type_check_only
class _DisassembleResult(TypedDict):
    instructions: list[_Instruction]

def disassemble(
    *,
    memoryReference: str,
    offset: int = 0,
    instructionOffset: int = 0,
    instructionCount: int,
    **extra: Unused,
) -> _DisassembleResult: ...
