import sys
import threading
from collections.abc import Callable, Iterable
from re import Pattern
from typing import Final, NoReturn, TypedDict, type_check_only

COMPILED_EXT_RE: Final[Pattern[str]]

class ReloaderBase(threading.Thread):
    daemon: bool
    def __init__(
        self,
        extra_files: Iterable[str] | None = None,
        interval: int = 1,
        callback: Callable[[str], None] | None = None,
    ) -> None: ...
    def add_extra_file(self, filename: str) -> None: ...
    def get_files(self) -> list[str]: ...

class Reloader(ReloaderBase):
    def run(self) -> None: ...

has_inotify: bool
if sys.platform == "linux":
    class InotifyReloader(ReloaderBase):
        event_mask: int
        daemon: bool
        def __init__(
            self,
            extra_files: Iterable[str] | None = None,
            callback: Callable[[str], None] | None = None,
        ) -> None: ...
        def add_extra_file(self, filename: str) -> None: ...
        def get_dirs(self) -> set[str]: ...
        def refresh_dirs(self) -> None: ...
        def run(self) -> None: ...

else:
    class InotifyReloader:
        def __init__(
            self,
            extra_files: Iterable[str] | None = None,
            callback: Callable[[str], None] | None = None,
        ) -> NoReturn: ...

type _PreferredReloaderType = type[InotifyReloader | Reloader]
type _ReloaderType = InotifyReloader | Reloader

@type_check_only
class _ReloadedEngines(TypedDict):
    auto: _PreferredReloaderType
    pool: type[Reloader]
    inotify: type[InotifyReloader]

preferred_reloader: _PreferredReloaderType
reloader_engines: _ReloadedEngines
