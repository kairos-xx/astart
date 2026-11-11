from collections.abc import Iterator
from typing import Any, ClassVar, Final, Protocol, Self, type_check_only

from _typeshed import ConvertibleToInt, Incomplete, SupportsIter
from openpyxl.descriptors import MetaSerialisable
from openpyxl.xml.functions import Element

from ..xml._functions_overloads import (
    _HasAttrib,
    _HasGet,
    _HasTagAndGet,
    _HasText,
    _SupportsFindChartLines,
)

@type_check_only
class _ChildSerialisableTreeElement(
    _HasAttrib,
    _HasText,
    SupportsIter[Incomplete],
    Protocol,
): ...

@type_check_only
class _SerialisableTreeElement(
    _HasGet[object],
    _SupportsFindChartLines,
    _ChildSerialisableTreeElement,
    Protocol,
): ...

KEYWORDS: Final[frozenset[str]]
seq_types: Final[tuple[type[list[Any]], type[tuple[Any, ...]]]]

class Serialisable(metaclass=MetaSerialisable):
    __attrs__: ClassVar[tuple[str, ...]]
    __nested__: ClassVar[tuple[str, ...]]
    __elements__: ClassVar[tuple[str, ...]]
    __namespaced__: ClassVar[tuple[tuple[str, str], ...]]
    idx_base: int
    @property
    def tagname(self) -> str: ...
    namespace: ClassVar[str | None]
    @classmethod
    def from_tree(cls, node: _SerialisableTreeElement) -> Self | None: ...
    def to_tree(
        self,
        tagname: str | None = None,
        idx: _HasTagAndGet[ConvertibleToInt] | ConvertibleToInt | None = None,
        namespace: str | None = None,
    ) -> Element: ...
    def __iter__(self) -> Iterator[tuple[str, str]]: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __add__(self, other): ...
    def __copy__(self): ...
