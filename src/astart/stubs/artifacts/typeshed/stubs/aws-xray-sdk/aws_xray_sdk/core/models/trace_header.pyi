from logging import Logger
from typing import Final, Literal, Self

from _typeshed import Incomplete

type _SampledTrue = Literal[True, "1", 1]
type _SampledFalse = Literal[False, "0", 0]
type _SampledUnknown = Literal["?"]
type _Sampled = _SampledTrue | _SampledFalse | _SampledUnknown
log: Logger
ROOT: Final = "Root"
PARENT: Final = "Parent"
SAMPLE: Final = "Sampled"
SELF: Final = "Self"
HEADER_DELIMITER: Final = ";"

class TraceHeader:
    def __init__(
        self,
        root: str | None = None,
        parent: str | None = None,
        sampled: _Sampled | None = None,
        data: dict[str, Incomplete] | None = None,
    ) -> None: ...
    @classmethod
    def from_header_str(cls, header: str | None) -> Self: ...
    def to_header_str(self) -> str: ...
    @property
    def root(self) -> str | None: ...
    @property
    def parent(self) -> str | None: ...
    @property
    def sampled(self) -> Literal[1, 0, "?"] | None: ...
    @property
    def data(self) -> dict[str, Incomplete]: ...
