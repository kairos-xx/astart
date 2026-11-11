from collections.abc import Iterable, Iterator
from importlib.readers import *
from typing import TypeVar

_T = TypeVar("_T")

def remove_duplicates[T](items: Iterable[_T]) -> Iterator[_T]: ...
