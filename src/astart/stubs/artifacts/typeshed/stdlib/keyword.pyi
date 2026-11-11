from collections.abc import Sequence
from typing import Final

__all__ = ["iskeyword", "issoftkeyword", "kwlist", "softkwlist"]

def iskeyword(s: str, /) -> bool: ...

kwlist: Final[Sequence[str]]

def issoftkeyword(s: str, /) -> bool: ...

softkwlist: Final[Sequence[str]]
