from collections.abc import Generator

from networkx.classes.digraph import DiGraph
from networkx.classes.graph import _Node
from networkx.utils.backends import _dispatchable

__all__ = [
    "is_weakly_connected",
    "number_weakly_connected_components",
    "weakly_connected_components",
]

@_dispatchable
def weakly_connected_components(
    G: DiGraph[_Node],
) -> Generator[set[_Node]]: ...
@_dispatchable
def number_weakly_connected_components(G: DiGraph[_Node]) -> int: ...
@_dispatchable
def is_weakly_connected(G: DiGraph[_Node]) -> bool: ...
