from collections.abc import Generator

from networkx.classes.digraph import DiGraph
from networkx.classes.graph import _Node
from networkx.utils.backends import _dispatchable

__all__ = [
    "attracting_components",
    "is_attracting_component",
    "number_attracting_components",
]

@_dispatchable
def attracting_components(G: DiGraph[_Node]) -> Generator[set[_Node]]: ...
@_dispatchable
def number_attracting_components(G: DiGraph[_Node]) -> int: ...
@_dispatchable
def is_attracting_component(G: DiGraph[_Node]) -> bool: ...
