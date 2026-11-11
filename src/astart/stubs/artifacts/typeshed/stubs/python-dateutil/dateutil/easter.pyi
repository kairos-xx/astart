from datetime import date
from typing import Final, Literal

__all__ = ["EASTER_JULIAN", "EASTER_ORTHODOX", "EASTER_WESTERN", "easter"]
EASTER_JULIAN: Final = 1
EASTER_ORTHODOX: Final = 2
EASTER_WESTERN: Final = 3

def easter(year: int, method: Literal[1, 2, 3] = 3) -> date: ...
