from typing import NoReturn, overload
from warnings import deprecated

from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.classes.multigraph import MultiGraph
from networkx.utils.backends import _dispatchable

__all__ = [
    "CurrentEdge",
    "GlobalRelabelThreshold",
    "Level",
    "build_flow_dict",
    "build_residual_network",
    "detect_unboundedness",
]

class CurrentEdge:
    __slots__ = ("_curr", "_edges", "_it")
    def __init__(self, edges) -> None: ...
    def get(self): ...
    def move_to_next(self) -> None: ...

class Level:
    __slots__ = ("active", "inactive")
    active: Incomplete
    inactive: Incomplete
    def __init__(self) -> None: ...

class GlobalRelabelThreshold:
    def __init__(self, n, m, freq) -> None: ...
    def add_work(self, work) -> None: ...
    def is_reached(self) -> bool: ...
    def clear_work(self) -> None: ...

@overload
@deprecated("MultiGraph and MultiDiGraph not supported (yet).")
def build_residual_network(
    G: MultiGraph[_Node],
    capacity,
    *,
    backend: str | None = None,
    **backend_kwargs,
) -> NoReturn: ...
@overload
def build_residual_network(
    G: Graph[_Node],
    capacity,
    *,
    backend: str | None = None,
    **backend_kwargs,
): ...
@_dispatchable
def detect_unboundedness(R, s, t) -> None: ...
@_dispatchable
def build_flow_dict(G: Graph[_Node], R): ...
