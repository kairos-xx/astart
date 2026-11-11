import sys
from abc import abstractmethod
from collections.abc import AsyncGenerator as AsyncGenerator
from collections.abc import AsyncIterable as AsyncIterable
from collections.abc import AsyncIterator as AsyncIterator
from collections.abc import Awaitable as Awaitable
from collections.abc import ByteString as ByteString
from collections.abc import Callable as Callable
from collections.abc import Collection as Collection
from collections.abc import Container as Container
from collections.abc import Coroutine as Coroutine
from collections.abc import Generator as Generator
from collections.abc import Hashable as Hashable
from collections.abc import ItemsView as ItemsView
from collections.abc import Iterable as Iterable
from collections.abc import Iterator as Iterator
from collections.abc import KeysView as KeysView
from collections.abc import Mapping as Mapping
from collections.abc import MappingView as MappingView
from collections.abc import MutableMapping as MutableMapping
from collections.abc import MutableSequence as MutableSequence
from collections.abc import MutableSet as MutableSet
from collections.abc import Reversible as Reversible
from collections.abc import Sequence as Sequence
from collections.abc import Sized as Sized
from collections.abc import ValuesView as ValuesView
from types import MappingProxyType
from typing import (  # noqa: UP035
    AbstractSet as Set,
)
from typing import (
    ClassVar,
    Protocol,
    TypeVar,
    final,
    runtime_checkable,
)

__all__ = [
    "AsyncGenerator",
    "AsyncIterable",
    "AsyncIterator",
    "Awaitable",
    "Callable",
    "Collection",
    "Container",
    "Coroutine",
    "Generator",
    "Hashable",
    "ItemsView",
    "Iterable",
    "Iterator",
    "KeysView",
    "Mapping",
    "MappingView",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Reversible",
    "Sequence",
    "Set",
    "Sized",
    "ValuesView",
]
if sys.version_info < (3, 15):
    __all__ += ["ByteString"]
__all__ += ["Buffer"]

_KT_co = TypeVar("_KT_co", covariant=True)  # Key type covariant containers.
_VT_co = TypeVar("_VT_co", covariant=True)  # Value type covariant containers.

@final
class dict_keys[KT_co, VT_co](KeysView[KT_co]):  # undocumented
    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> Iterator[_KT_co]: ...
    __hash__: ClassVar[None]  # type: ignore[assignment]
    def isdisjoint(self, other: Iterable[_KT_co], /) -> bool: ...
    @property
    def mapping(self) -> MappingProxyType[_KT_co, _VT_co]: ...

@final
class dict_values[KT_co, VT_co](ValuesView[VT_co]):  # undocumented
    def __reversed__(self) -> Iterator[_VT_co]: ...
    @property
    def mapping(self) -> MappingProxyType[_KT_co, _VT_co]: ...

@final
class dict_items(ItemsView[_KT_co, _VT_co]):  # undocumented
    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> Iterator[tuple[_KT_co, _VT_co]]: ...
    __hash__: ClassVar[None]  # type: ignore[assignment]
    def isdisjoint(
        self,
        other: Iterable[tuple[_KT_co, _VT_co]],
        /,
    ) -> bool: ...
    @property
    def mapping(self) -> MappingProxyType[_KT_co, _VT_co]: ...

@runtime_checkable
class Buffer(Protocol):
    __slots__ = ()
    @abstractmethod
    def __buffer__(self, flags: int, /) -> memoryview: ...
