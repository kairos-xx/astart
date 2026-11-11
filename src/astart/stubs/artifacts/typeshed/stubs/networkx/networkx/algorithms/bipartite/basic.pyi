from collections.abc import Iterable

from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable

__all__ = [
    "color",
    "degrees",
    "density",
    "is_bipartite",
    "is_bipartite_node_set",
    "sets",
]

@_dispatchable
def color(G: Graph[_Node]) -> dict[Incomplete, Incomplete]: ...
@_dispatchable
def is_bipartite(G: Graph[_Node]) -> bool: ...
@_dispatchable
def is_bipartite_node_set(
    G: Graph[_Node],
    nodes: Iterable[Incomplete],
) -> bool: ...
@_dispatchable
def sets(
    G: Graph[_Node],
    top_nodes: Iterable[Incomplete] | None = None,
) -> tuple[set[Incomplete], set[Incomplete]]: ...
@_dispatchable
def density(B: Graph[_Node], nodes) -> float: ...
@_dispatchable
def degrees(
    B: Graph[_Node],
    nodes,
    weight: str | None = None,
) -> tuple[Incomplete, Incomplete]: ...
