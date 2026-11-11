from collections.abc import Callable, Iterable, Mapping
from typing import Any, Self

from _typeshed import SupportsRichComparison

__tracebackhide__: bool

class ExtractingMixin:
    def extracting(
        self,
        *names: str,
        filter: str | Mapping[str, Any] | Callable[[Any], bool] = ...,
        sort: str
        | Iterable[str]
        | Callable[[Any], SupportsRichComparison] = ...,
    ) -> Self: ...
