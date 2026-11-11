import sys
from typing import Final

if sys.platform == "win32":
    type _SequenceType = list[tuple[str, str | None, int]]
    AdminExecuteSequence: Final[_SequenceType]
    AdminUISequence: Final[_SequenceType]
    AdvtExecuteSequence: Final[_SequenceType]
    InstallExecuteSequence: Final[_SequenceType]
    InstallUISequence: Final[_SequenceType]
    tables: Final[list[str]]
