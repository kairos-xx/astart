import sys
from _heapq import *
from collections.abc import Callable, Generator, Iterable
from typing import Final, TypeVar, overload

from _typeshed import SupportsRichComparison
from _typeshed import SupportsRichComparisonT as _T

__all__ = [
    "heapify",
    "heappop",
    "heappush",
    "heappushpop",
    "heapreplace",
    "merge",
    "nlargest",
    "nsmallest",
]
if sys.version_info >= (3, 14):
    __all__ += [
        "heapify_max",
        "heappop_max",
        "heappush_max",
        "heappushpop_max",
        "heapreplace_max",
    ]
_S = TypeVar("_S")
__about__: Final[str]

@overload
def merge(
    *iterables: Iterable[_S],
    key: Callable[[_S], SupportsRichComparison],
    reverse: bool = False,
) -> Generator[_S]: ...
@overload
def merge(
    *iterables: Iterable[_T],
    key: None = None,
    reverse: bool = False,
) -> Generator[_T]: ...
@overload
def nlargest(
    n: int,
    iterable: Iterable[_S],
    key: Callable[[_S], SupportsRichComparison],
) -> list[_S]: ...
@overload
def nlargest(n: int, iterable: Iterable[_T], key: None = None) -> list[_T]: ...
@overload
def nsmallest(
    n: int,
    iterable: Iterable[_S],
    key: Callable[[_S], SupportsRichComparison],
) -> list[_S]: ...
@overload
def nsmallest(
    n: int,
    iterable: Iterable[_T],
    key: None = None,
) -> list[_T]: ...
def _heapify_max(heap: list[SupportsRichComparison], /) -> None: ...
