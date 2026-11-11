from collections.abc import Hashable
from typing import TypeVar

from _typeshed import Incomplete
from networkx.classes.graph import Graph, _Node
from networkx.utils.backends import _dispatchable

_X = TypeVar("_X", bound=Hashable)
_Y = TypeVar("_Y", bound=Hashable)
__all__ = [
    "cartesian_product",
    "corona_product",
    "lexicographic_product",
    "modular_product",
    "power",
    "rooted_product",
    "strong_product",
    "tensor_product",
]

@_dispatchable
def tensor_product[X: Hashable, Y: Hashable](
    G: Graph[_X],
    H: Graph[_Y],
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def cartesian_product[X: Hashable, Y: Hashable](
    G: Graph[_X],
    H: Graph[_Y],
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def lexicographic_product[X: Hashable, Y: Hashable](
    G: Graph[_X],
    H: Graph[_Y],
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def strong_product[X: Hashable, Y: Hashable](
    G: Graph[_X],
    H: Graph[_Y],
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def power(G: Graph[_Node], k): ...
@_dispatchable
def rooted_product(
    G: Graph[_X],
    H: Graph[_Y],
    root: _Y,
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def corona_product[X: Hashable, Y: Hashable](
    G: Graph[_X],
    H: Graph[_Y],
) -> Graph[tuple[_X, _Y]]: ...
@_dispatchable
def modular_product(G: Graph[_Node], H) -> Graph[Incomplete]: ...
