from collections.abc import Callable
from typing import Self

__tracebackhide__: bool

class DynamicMixin:
    def __getattr__(self, attr: str) -> Callable[[object], Self]: ...
