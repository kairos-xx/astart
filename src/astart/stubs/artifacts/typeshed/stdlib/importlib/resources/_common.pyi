import types
from collections.abc import Callable
from contextlib import AbstractContextManager
from importlib.resources.abc import ResourceReader, Traversable
from pathlib import Path
from typing import Literal, overload
from warnings import deprecated

type Package = str | types.ModuleType
type Anchor = Package

def package_to_anchor(
    func: Callable[[Anchor | None], Traversable],
) -> Callable[[Anchor | None, Anchor | None], Traversable]: ...
@overload
def files(anchor: Anchor | None = None) -> Traversable: ...
@overload
@deprecated(
    "Deprecated since Python 3.12; will be removed in Python 3.15. Use `anchor` parameter instead.",
)
def files(package: Anchor | None = None) -> Traversable: ...
def get_resource_reader(
    package: types.ModuleType,
) -> ResourceReader | None: ...
def resolve(cand: Anchor | None) -> types.ModuleType: ...
def from_package(package: types.ModuleType) -> Traversable: ...
def as_file(
    path: Traversable,
) -> AbstractContextManager[Path, Literal[False]]: ...
