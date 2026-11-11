from collections.abc import Callable, Mapping
from typing import Any, Final, ParamSpec, Self, TypeVar, overload

from _typeshed import Incomplete

_P = ParamSpec("_P")
_R = TypeVar("_R")
__all__ = ["_dispatchable"]
FAILED_TO_CONVERT: Final[str]

class _dispatchable[**P, R]:
    __defaults__: Incomplete
    __kwdefaults__: Incomplete
    __module__: Incomplete
    __qualname__: Incomplete
    __wrapped__: Incomplete
    orig_func: Callable[_P, _R] | None
    name: str
    edge_attrs: dict[str, Any] | None
    node_attrs: dict[str, Any] | None
    preserve_edge_attrs: bool
    preserve_node_attrs: bool
    preserve_graph_attrs: bool
    mutates_input: bool
    optional_graphs: Incomplete
    list_graphs: Incomplete
    graphs: dict[str, int]
    backends: dict[str, Incomplete]
    def __new__(
        cls,
        func: Callable[_P, _R] | None = None,
        *,
        name: str | None = None,
        graphs: str | None | Mapping[str, int] = "G",
        edge_attrs: str | dict[str, Any] | None = None,
        node_attrs: str | dict[str, Any] | None = None,
        preserve_edge_attrs: bool = False,
        preserve_node_attrs: bool = False,
        preserve_graph_attrs: bool = False,
        preserve_all_attrs: bool = False,
        mutates_input: bool = False,
        returns_graph: bool = False,
        implemented_by_nx: bool = True,
    ) -> Self: ...
    @property
    def __doc__(self): ...
    @__doc__.setter
    def __doc__(self, val) -> None: ...
    @property
    def __signature__(self): ...
    @overload
    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R: ...
    @overload
    def __call__(
        self,
        *args: Any,
        backend: str,
        **backend_kwargs: Any,
    ) -> _R: ...
    def __reduce__(self): ...
