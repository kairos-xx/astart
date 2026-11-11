import abc
import pathlib
import sys
import types
from collections.abc import Iterable, Mapping
from importlib.abc import MetaPathFinder
from importlib.metadata._meta import (
    PackageMetadata as PackageMetadata,
)
from importlib.metadata._meta import (
    SimplePath,
)
from os import PathLike
from re import Pattern
from typing import (
    Any,
    ClassVar,
    overload,
)

from _typeshed import StrPath

__all__ = [
    "Distribution",
    "DistributionFinder",
    "PackageMetadata",
    "PackageNotFoundError",
    "distribution",
    "distributions",
    "entry_points",
    "files",
    "metadata",
    "packages_distributions",
    "requires",
    "version",
]

if sys.version_info >= (3, 15):
    __all__ += ["MetadataNotFound", "PackagePath", "SimplePath"]

type _SimplePath = SimplePath

def packages_distributions() -> Mapping[str, list[str]]: ...

class PackageNotFoundError(ModuleNotFoundError):
    @property
    def name(self) -> str: ...  # type: ignore[override]

if sys.version_info >= (3, 15):
    class MetadataNotFound(FileNotFoundError): ...

_EntryPointBase = object

class EntryPoint(_EntryPointBase):
    pattern: ClassVar[Pattern[str]]
    name: str
    value: str
    group: str

    def __init__(self, name: str, value: str, group: str) -> None: ...
    def load(self) -> Any: ...  # Callable[[], Any] or an importable module
    @property
    def extras(self) -> list[str]: ...
    @property
    def module(self) -> str: ...
    @property
    def attr(self) -> str: ...
    dist: ClassVar[Distribution | None]
    def matches(
        self,
        *,
        name: str = ...,
        value: str = ...,
        group: str = ...,
        module: str = ...,
        attr: str = ...,
        extras: list[str] = ...,
    ) -> bool: ...  # undocumented
    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...
    def __lt__(self, other: object) -> bool: ...

class EntryPoints(tuple[EntryPoint, ...]):
    __slots__ = ()
    def __getitem__(self, name: str) -> EntryPoint: ...  # type: ignore[override]
    def select(
        self,
        *,
        name: str = ...,
        value: str = ...,
        group: str = ...,
        module: str = ...,
        attr: str = ...,
        extras: list[str] = ...,
    ) -> EntryPoints: ...
    @property
    def names(self) -> set[str]: ...
    @property
    def groups(self) -> set[str]: ...

class PackagePath(pathlib.PurePosixPath):
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def read_binary(self) -> bytes: ...
    def locate(self) -> PathLike[str]: ...
    # The following attributes are not defined on PackagePath, but are dynamically added by Distribution.files:
    hash: FileHash | None
    size: int | None
    dist: Distribution

class FileHash:
    mode: str
    value: str
    def __init__(self, spec: str) -> None: ...

if sys.version_info >= (3, 15):
    _distribution_parent = abc.ABC
else:
    class DeprecatedNonAbstract: ...
    _distribution_parent = DeprecatedNonAbstract

class Distribution(_distribution_parent):
    @abc.abstractmethod
    def read_text(self, filename: str) -> str | None: ...
    @abc.abstractmethod
    def locate_file(self, path: StrPath) -> _SimplePath: ...
    @classmethod
    def from_name(cls, name: str) -> Distribution: ...
    @overload
    @classmethod
    def discover(
        cls,
        *,
        context: DistributionFinder.Context,
    ) -> Iterable[Distribution]: ...
    @overload
    @classmethod
    def discover(
        cls,
        *,
        context: None = None,
        name: str | None = ...,
        path: list[str] = ...,
        **kwargs: Any,
    ) -> Iterable[Distribution]: ...
    @staticmethod
    def at(path: StrPath) -> PathDistribution: ...
    @property
    def metadata(self) -> PackageMetadata: ...
    @property
    def entry_points(self) -> EntryPoints: ...
    @property
    def version(self) -> str: ...
    @property
    def files(self) -> list[PackagePath] | None: ...
    @property
    def requires(self) -> list[str] | None: ...
    @property
    def name(self) -> str: ...
    @property
    def origin(self) -> types.SimpleNamespace | None: ...

class DistributionFinder(MetaPathFinder):
    class Context:
        name: str | None
        def __init__(
            self,
            *,
            name: str | None = ...,
            path: list[str] = ...,
            **kwargs: Any,
        ) -> None: ...
        @property
        def path(self) -> list[str]: ...

    @abc.abstractmethod
    def find_distributions(
        self,
        context: DistributionFinder.Context = ...,
    ) -> Iterable[Distribution]: ...

class MetadataPathFinder(DistributionFinder):
    @classmethod
    def find_distributions(
        cls,
        context: DistributionFinder.Context = ...,
    ) -> Iterable[PathDistribution]: ...
    @classmethod
    def invalidate_caches(cls) -> None: ...

class PathDistribution(Distribution):
    _path: _SimplePath
    def __init__(self, path: _SimplePath) -> None: ...
    def read_text(self, filename: StrPath) -> str | None: ...
    def locate_file(self, path: StrPath) -> _SimplePath: ...

def distribution(distribution_name: str) -> Distribution: ...
@overload
def distributions(
    *,
    context: DistributionFinder.Context,
) -> Iterable[Distribution]: ...
@overload
def distributions(
    *,
    context: None = None,
    name: str | None = ...,
    path: list[str] = ...,
    **kwargs: Any,
) -> Iterable[Distribution]: ...
def metadata(distribution_name: str) -> PackageMetadata: ...
def entry_points(
    *,
    name: str = ...,
    value: str = ...,
    group: str = ...,
    module: str = ...,
    attr: str = ...,
    extras: list[str] = ...,
) -> EntryPoints: ...
def version(distribution_name: str) -> str: ...
def files(distribution_name: str) -> list[PackagePath] | None: ...
def requires(distribution_name: str) -> list[str] | None: ...
