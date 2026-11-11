from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable

__all__ = ["find_asteroidal_triple", "is_at_free"]

@_dispatchable
def find_asteroidal_triple(G: Graph[_Node]) -> list[Incomplete] | None: ...
@_dispatchable
def is_at_free(G: Graph[_Node]) -> bool: ...
@_dispatchable
def create_component_structure(
    G: Graph[_Node],
) -> dict[Incomplete, Incomplete]: ...
