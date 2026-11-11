from collections.abc import Generator

from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable

__all__ = [
    "eulerian_circuit",
    "eulerian_path",
    "eulerize",
    "has_eulerian_path",
    "is_eulerian",
    "is_semieulerian",
]

@_dispatchable
def is_eulerian(G: Graph[_Node]) -> bool: ...
@_dispatchable
def is_semieulerian(G: Graph[_Node]) -> bool: ...
@_dispatchable
def eulerian_circuit(
    G: Graph[_Node],
    source: _Node | None = None,
    keys: bool = False,
) -> Generator[Incomplete, Incomplete]: ...
@_dispatchable
def has_eulerian_path(
    G: Graph[_Node],
    source: _Node | None = None,
) -> bool: ...
@_dispatchable
def eulerian_path(
    G: Graph[_Node],
    source=None,
    keys: bool = False,
) -> Generator[Incomplete, Incomplete]: ...
@_dispatchable
def eulerize(G: Graph[_Node]): ...
