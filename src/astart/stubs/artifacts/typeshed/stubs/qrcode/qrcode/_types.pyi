from typing import Any, Protocol, type_check_only

from _typeshed import SupportsWrite

type Box = tuple[tuple[int, int], tuple[int, int]]
type Ink = tuple[int, int, int] | tuple[int, int, int, int]
type ErrorCorrect = int
type MaskPattern = int

@type_check_only
class Writeable(SupportsWrite[bytes], Protocol):
    def seek(self, offset: int, /) -> Any: ...
