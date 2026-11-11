from collections.abc import Callable, Iterable, Sequence
from types import GenericAlias
from typing import Any, AnyStr, Final, Literal

from _typeshed import GenericPath, StrOrBytesPath

__all__ = ["DEFAULT_IGNORES", "clear_cache", "cmp", "cmpfiles", "dircmp"]
DEFAULT_IGNORES: Final[list[str]]
BUFSIZE: Final = 8192

def cmp(
    f1: StrOrBytesPath,
    f2: StrOrBytesPath,
    shallow: bool | Literal[0, 1] = True,
) -> bool: ...
def cmpfiles(
    a: GenericPath[AnyStr],
    b: GenericPath[AnyStr],
    common: Iterable[GenericPath[AnyStr]],
    shallow: bool | Literal[0, 1] = True,
) -> tuple[list[AnyStr], list[AnyStr], list[AnyStr]]: ...

class dircmp[AnyStr: (bytes, str)]:
    def __init__(
        self,
        a: GenericPath[AnyStr],
        b: GenericPath[AnyStr],
        ignore: Sequence[AnyStr] | None = None,
        hide: Sequence[AnyStr] | None = None,
        *,
        shallow: bool = True,
    ) -> None: ...
    left: AnyStr
    right: AnyStr
    hide: Sequence[AnyStr]
    ignore: Sequence[AnyStr]
    subdirs: dict[AnyStr, dircmp[AnyStr]]
    same_files: list[AnyStr]
    diff_files: list[AnyStr]
    funny_files: list[AnyStr]
    common_dirs: list[AnyStr]
    common_files: list[AnyStr]
    common_funny: list[AnyStr]
    common: list[AnyStr]
    left_only: list[AnyStr]
    right_only: list[AnyStr]
    left_list: list[AnyStr]
    right_list: list[AnyStr]
    def report(self) -> None: ...
    def report_partial_closure(self) -> None: ...
    def report_full_closure(self) -> None: ...
    methodmap: dict[str, Callable[[], None]]
    def phase0(self) -> None: ...
    def phase1(self) -> None: ...
    def phase2(self) -> None: ...
    def phase3(self) -> None: ...
    def phase4(self) -> None: ...
    def phase4_closure(self) -> None: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

def clear_cache() -> None: ...
