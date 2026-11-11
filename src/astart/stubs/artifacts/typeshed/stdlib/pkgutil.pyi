import sys
from collections.abc import Callable, Iterable, Iterator
from typing import Any, NamedTuple, TypeVar
from warnings import deprecated

from _typeshed import StrOrBytesPath, SupportsRead
from _typeshed.importlib import (
    LoaderProtocol,
    MetaPathFinderProtocol,
    PathEntryFinderProtocol,
)

__all__ = [
    "ModuleInfo",
    "extend_path",
    "get_data",
    "get_importer",
    "iter_importers",
    "iter_modules",
    "read_code",
    "walk_packages",
]
if sys.version_info < (3, 14):
    __all__ += ["find_loader", "get_loader"]
_PathT = TypeVar("_PathT", bound=Iterable[str])

class ModuleInfo(NamedTuple):
    module_finder: MetaPathFinderProtocol | PathEntryFinderProtocol
    name: str
    ispkg: bool

def extend_path[PathT: Iterable[str]](path: _PathT, name: str) -> _PathT: ...

if sys.version_info < (3, 14):
    @deprecated(
        "Deprecated since Python 3.12; removed in Python 3.14. Use `importlib.util.find_spec()` instead.",
    )
    def find_loader(fullname: str) -> LoaderProtocol | None: ...
    @deprecated(
        "Deprecated since Python 3.12; removed in Python 3.14. Use `importlib.util.find_spec()` instead.",
    )
    def get_loader(module_or_name: str) -> LoaderProtocol | None: ...

def get_importer(
    path_item: StrOrBytesPath,
) -> PathEntryFinderProtocol | None: ...
def iter_importers(
    fullname: str = "",
) -> Iterator[MetaPathFinderProtocol | PathEntryFinderProtocol]: ...
def iter_modules(
    path: Iterable[StrOrBytesPath] | None = None,
    prefix: str = "",
) -> Iterator[ModuleInfo]: ...
def read_code(stream: SupportsRead[bytes]) -> Any: ...
def walk_packages(
    path: Iterable[StrOrBytesPath] | None = None,
    prefix: str = "",
    onerror: Callable[[str], object] | None = None,
) -> Iterator[ModuleInfo]: ...
def get_data(package: str, resource: str) -> bytes | None: ...

if sys.version_info >= (3, 15):
    def resolve_name(name: str, *, strict: bool = False) -> Any: ...
else:
    def resolve_name(name: str) -> Any: ...
