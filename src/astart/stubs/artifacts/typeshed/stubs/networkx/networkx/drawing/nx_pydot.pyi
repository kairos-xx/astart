from os import PathLike
from typing import Any

from _typeshed import SupportsRead, SupportsWrite
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable
from pydot import (
    Dot,  # type: ignore[import-not-found]  # pyright: ignore[reportMissingImports]
)

__all__ = [
    "from_pydot",
    "graphviz_layout",
    "pydot_layout",
    "read_dot",
    "to_pydot",
    "write_dot",
]

def write_dot(
    G: Graph[_Node],
    path: str | PathLike[Any] | SupportsWrite[str],
) -> None: ...
@_dispatchable
def read_dot(path: str | PathLike[Any] | SupportsRead[str]) -> Graph[str]: ...
@_dispatchable
def from_pydot(P: Dot) -> Graph[str]: ...
def to_pydot(N: Graph[_Node]) -> Dot: ...
def graphviz_layout(
    G: Graph[_Node],
    prog: str = "neato",
    root: _Node | None = None,
) -> dict[_Node, tuple[float, float]]: ...
def pydot_layout(
    G: Graph[_Node],
    prog: str = "neato",
    root: _Node | None = None,
) -> dict[_Node, tuple[float, float]]: ...
