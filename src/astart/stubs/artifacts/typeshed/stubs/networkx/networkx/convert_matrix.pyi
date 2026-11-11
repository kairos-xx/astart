from collections.abc import Callable, Collection, Hashable, Iterable
from typing import Literal, TypeVar, overload

import numpy as np
from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable

type _DataFrame = Incomplete
type _ExtensionDtype = Incomplete
type _Axes = Collection[_Node]
_G = TypeVar("_G", bound=Graph[Hashable])
__all__ = [
    "from_numpy_array",
    "from_pandas_adjacency",
    "from_pandas_edgelist",
    "from_scipy_sparse_array",
    "to_numpy_array",
    "to_pandas_adjacency",
    "to_pandas_edgelist",
    "to_scipy_sparse_array",
]

@_dispatchable
def to_pandas_adjacency(
    G: Graph[_Node],
    nodelist: _Axes[_Node] | None = None,
    dtype: np.dtype[Incomplete] | None = None,
    order: np._OrderCF = None,
    multigraph_weight: Callable[[list[float]], float] = ...,
    weight: str = "weight",
    nonedge: float = 0.0,
) -> _DataFrame: ...
@overload
def from_pandas_adjacency[G: Graph[Hashable]](
    df: _DataFrame,
    create_using: type[_G],
) -> _G: ...
@overload
def from_pandas_adjacency(
    df: _DataFrame,
    create_using: None = None,
) -> Graph[Incomplete]: ...
@_dispatchable
def to_pandas_edgelist(
    G: Graph[_Node],
    source: str | int = "source",
    target: str | int = "target",
    nodelist: Iterable[_Node] | None = None,
    dtype: _ExtensionDtype | None = None,
    edge_key: str | int | None = None,
) -> _DataFrame: ...
@overload
def from_pandas_edgelist[G: Graph[Hashable]](
    df: _DataFrame,
    source: str | int,
    target: str | int,
    edge_attr: str
    | int
    | list[str | int]
    | tuple[str | int]
    | Literal[True]
    | None,
    create_using: type[_G],
    edge_key: str | None = None,
) -> _G: ...
@overload
def from_pandas_edgelist[G: Graph[Hashable]](
    df: _DataFrame,
    source: str | int = "source",
    target: str | int = "target",
    edge_attr: str
    | int
    | list[str | int]
    | tuple[str | int]
    | Literal[True]
    | None = None,
    *,
    create_using: type[_G],
    edge_key: str | None = None,
) -> _G: ...
@overload
def from_pandas_edgelist(
    df: _DataFrame,
    source: str | int = "source",
    target: str | int = "target",
    edge_attr: str
    | int
    | list[str | int]
    | tuple[str | int]
    | Literal[True]
    | None = None,
    create_using: None = None,
    edge_key: str | None = None,
) -> Graph[Incomplete]: ...
@_dispatchable
def to_scipy_sparse_array(
    G: Graph[_Node],
    nodelist=None,
    dtype=None,
    weight="weight",
    format="csr",
): ...
@_dispatchable
def from_scipy_sparse_array(
    A,
    parallel_edges=False,
    create_using=None,
    edge_attribute="weight",
): ...
@_dispatchable
def to_numpy_array(
    G: Graph[_Node],
    nodelist: Collection[_Node] | None = None,
    dtype: np.dtype[Incomplete] | None = None,
    order: np._OrderCF = None,
    multigraph_weight: Callable[[list[float]], float] = ...,
    weight: str = "weight",
    nonedge: float = 0.0,
) -> np.ndarray[Incomplete, np.dtype[Incomplete]]: ...
@overload
def from_numpy_array(
    A: np.ndarray[Incomplete, Incomplete],
    parallel_edges: bool = False,
    create_using: None = None,
) -> Graph[Incomplete]: ...
@overload
def from_numpy_array[G: Graph[Hashable]](
    A: np.ndarray[Incomplete, Incomplete],
    parallel_edges: bool = False,
    *,
    create_using: type[_G],
) -> _G: ...
@overload
def from_numpy_array[G: Graph[Hashable]](
    A: np.ndarray[Incomplete, Incomplete],
    parallel_edges: bool,
    create_using: type[_G],
) -> _G: ...
