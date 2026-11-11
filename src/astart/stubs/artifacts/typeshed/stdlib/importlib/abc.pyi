import _ast
import sys
import types
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence
from importlib import _bootstrap_external
from importlib._abc import Loader as Loader
from importlib.machinery import ModuleSpec
from typing import Any
from warnings import deprecated

from _typeshed import ReadableBuffer, StrPath

__all__ = [
    "ExecutionLoader",
    "FileLoader",
    "InspectLoader",
    "Loader",
    "MetaPathFinder",
    "PathEntryFinder",
    "ResourceLoader",
    "SourceLoader",
]

@deprecated(
    "Deprecated since Python 3.7. Use `importlib.resources.abc.TraversableResources` instead.",
)
class ResourceLoader(Loader):
    @abstractmethod
    def get_data(self, path: str) -> bytes: ...

class InspectLoader(Loader):
    def is_package(self, fullname: str) -> bool: ...
    def get_code(self, fullname: str) -> types.CodeType | None: ...
    @abstractmethod
    def get_source(self, fullname: str) -> str | None: ...
    def exec_module(self, module: types.ModuleType) -> None: ...
    @staticmethod
    def source_to_code(
        data: ReadableBuffer
        | str
        | _ast.Module
        | _ast.Expression
        | _ast.Interactive,
        path: bytes | StrPath = "<string>",
    ) -> types.CodeType: ...

class ExecutionLoader(InspectLoader):
    @abstractmethod
    def get_filename(self, fullname: str) -> str: ...

class SourceLoader(
    _bootstrap_external.SourceLoader,
    ResourceLoader,
    ExecutionLoader,
    metaclass=ABCMeta,
):  # type: ignore[misc]  # incompatible definitions of source_to_code in the base classes
    @deprecated(
        "Deprecated since Python 3.3. Use `importlib.resources.abc.SourceLoader.path_stats` instead.",
    )
    def path_mtime(self, path: str) -> float: ...
    def set_data(self, path: str, data: bytes) -> None: ...
    def get_source(self, fullname: str) -> str | None: ...
    def path_stats(self, path: str) -> Mapping[str, Any]: ...

# Please keep in sync with _typeshed.importlib.MetaPathFinderProtocol
class MetaPathFinder(metaclass=ABCMeta):
    def invalidate_caches(self) -> None: ...
    # Not defined on the actual class, but expected to exist.
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = ...,
        /,
    ) -> ModuleSpec | None: ...

class PathEntryFinder(metaclass=ABCMeta):
    def invalidate_caches(self) -> None: ...
    # Not defined on the actual class, but expected to exist.
    def find_spec(
        self,
        fullname: str,
        target: types.ModuleType | None = ...,
    ) -> ModuleSpec | None: ...

class FileLoader(
    _bootstrap_external.FileLoader,
    ResourceLoader,
    ExecutionLoader,
    metaclass=ABCMeta,
):
    name: str
    path: str
    def __init__(self, fullname: str, path: str) -> None: ...
    def get_data(self, path: str) -> bytes: ...
    def get_filename(self, fullname: str | None = None) -> str: ...
    def load_module(self, fullname: str | None = None) -> types.ModuleType: ...

if sys.version_info < (3, 14):
    from importlib.resources.abc import (
        ResourceReader as ResourceReader,
    )
    from importlib.resources.abc import (
        Traversable as Traversable,
    )
    from importlib.resources.abc import (
        TraversableResources as TraversableResources,
    )
