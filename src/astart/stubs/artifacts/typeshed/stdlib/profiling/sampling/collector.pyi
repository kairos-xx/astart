from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from _remote_debugging import (
    AwaitedInfo,
    FrameInfo,
    InterpreterInfo,
    LocationInfo,
)
from _typeshed import StrOrBytesPath

type _Location = int | tuple[int, int, int, int] | LocationInfo | None
type _Frame = FrameInfo | tuple[str, _Location, str, int | None]
type _Timestamps = Sequence[int] | None

def normalize_location(location: _Location) -> tuple[int, int, int, int]: ...
def extract_lineno(location: _Location) -> int: ...
def filter_internal_frames(frames: Sequence[_Frame]) -> list[_Frame]: ...
def iter_async_frames(awaited_info_list: Sequence[AwaitedInfo]) -> object: ...

class Collector(ABC):
    aggregating: ClassVar[bool]
    @abstractmethod
    def collect(
        self,
        stack_frames: Sequence[InterpreterInfo] | Sequence[AwaitedInfo],
        timestamps_us: _Timestamps = None,
    ) -> None: ...
    def collect_failed_sample(self) -> None: ...
    @abstractmethod
    def export(self, filename: StrOrBytesPath) -> None: ...
