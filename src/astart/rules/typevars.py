"""Detect parameters that only flow through to the return value.

A parameter whose every use is as (an element of) a returned value is generic:
its type is whatever the caller passes. :func:`passthrough_return` proves
that and spells the return annotation in terms of a type variable.
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Dict,
    FunctionDef,
    IfExp,
    List,
    Name,
    Return,
    Set,
    Tuple,
    Yield,
    YieldFrom,
    iter_child_nodes,
    parse,
    walk,
)
from typing import TYPE_CHECKING

from astart.rules.protocols import names_bound_by
from astart.rules.provable import provable_return

if TYPE_CHECKING:
    from collections.abc import Mapping

    type Function = FunctionDef | AsyncFunctionDef


def _is_pure(*, node: AST, parents: Mapping[AST, AST]) -> bool:
    """Tell whether a use only carries the value into a return.

    Args:
        node: The ``Name`` node of the parameter.
        parents: Parent of every node.

    Returns:
        ``True`` when the chain up to the ``return`` is only containers and
        conditional branches.

    """
    child: AST = node
    parent: AST | None = parents.get(child)
    while parent is not None and not isinstance(parent, Return):
        match parent:
            case List() | Tuple() | Set():
                pass
            case Dict(values=values) if any(child is v for v in values):
                pass
            case IfExp(body=body, orelse=orelse) if (
                child is body or child is orelse
            ):
                pass
            case _:
                return False
        child, parent = parent, parents.get(parent)
    return parent is not None


def passthrough_return(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> str | None:
    """Prove a parameter is generic and spell the matching return type.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter name.
        variable: Name of the type variable standing for the parameter.
        counts: Module binding counts.

    Returns:
        The return annotation source, or ``None`` when the parameter is
        rebound, used for anything but being returned, or the function is
        already annotated or is a generator.

    """
    if function.returns is not None:
        return None
    nodes: list[AST] = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(parameter in names_bound_by(node=node) for node in nodes):
        return None
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    parents: dict[AST, AST] = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    uses: list[AST] = [
        node
        for node in nodes
        if isinstance(node, Name) and node.id == parameter
    ]
    if not uses or not all(
        _is_pure(node=use, parents=parents) for use in uses
    ):
        return None
    result: str | None = provable_return(
        function=function,
        known_types={parameter: variable},
        counts=counts,
    )
    if result is None:
        return None
    mentioned: bool = any(
        isinstance(node, Name) and node.id == variable
        for node in walk(node=parse(source=result, mode="eval"))
    )
    return result if mentioned else None
