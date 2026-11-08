"""Negotiate the annotations of a whole module."""

from __future__ import annotations

from ast import AST, arg, walk
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.rules.hints import node_key
from astart.rules.negotiation.builders import build_contracts, walk_functions
from astart.rules.negotiation.negotiator import Negotiation, Negotiator
from astart.rules.negotiation.policy import accept, blocked_nodes
from astart.stubs import host_resolver

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import CommentedModule
    from astart.rules.hints import Key
    from astart.rules.negotiation.beliefs import Belief
    from astart.rules.negotiation.builders import Built, Function
    from astart.rules.negotiation.model import Conflict
    from astart.stubs import Resolver


@final
@dataclass(frozen=True, slots=True)
class Verdicts:
    """What negotiation concluded for a module.

    Attributes:
        accepted: Annotation source by ``function.parameter`` or
            ``function->``, the key format of the recovery benchmark.
        conflicts: Every conflict found, including on unreported nodes.
        exhausted: ``True`` when a bound stopped the solver early.

    """

    accepted: dict[str, str]
    conflicts: tuple[Conflict, ...]
    exhausted: bool


def negotiate_module(
    *,
    module: CommentedModule,
    corroboration: Mapping[str, str],
    escaped: frozenset[str],
    library: Resolver | None = None,
) -> Verdicts:
    """Build, solve and judge the contracts of a module.

    Args:
        module: Parsed module.
        corroboration: The inference engine's proposal by node path
            (``function.parameter`` or ``function->``).
        escaped: Names read as values, whose callers are unknown.
        library: Resolver over typeshed for calls into the standard library;
            the host's by default, ``None`` is replaced by it.

    Returns:
        The annotations the evidence justifies.

    """
    built: Built = build_contracts(
        module=module,
        escaped=escaped,
        library=library if library is not None else host_resolver(),
    )
    result: Negotiation = Negotiator().solve(graph=built.graph)
    blocked: frozenset[str] = blocked_nodes(built=built, result=result)
    accepted: dict[str, str] = {}
    for path in sorted(built.kinds):
        belief: Belief | None = result.beliefs.get(path)
        if belief is None:
            continue
        verdict: str | None = accept(
            belief=belief,
            kind=built.kinds[path],
            opaque=blocked,
            corroboration=corroboration,
        )
        if verdict is not None:
            accepted[path] = verdict
    return Verdicts(
        accepted=accepted,
        conflicts=result.conflicts,
        exhausted=result.exhausted,
    )


def function_nodes(*, module: CommentedModule) -> dict[str, AST]:
    """Find every parameter and function node by the benchmark's name for it.

    Args:
        module: Parsed module.

    Returns:
        Node by path (``function.parameter`` or ``function->``); functions
        whose qualified name is not unique are left out.

    """
    entries: list[tuple[str, Function, bool]] = list(
        walk_functions(node=module, trail=(), in_class=False),
    )
    seen: Counter[str] = Counter(qual for qual, _function, _cls in entries)
    nodes: dict[str, AST] = {}
    for qual, function, _cls in entries:
        if seen[qual] != 1:
            continue
        nodes[f"{qual}->"] = function
        for parameter in walk(node=function.args):
            if isinstance(parameter, arg):
                nodes[f"{qual}.{parameter.arg}"] = parameter
    return nodes


def function_paths(*, module: CommentedModule) -> dict[Key, str]:
    """Name every parameter and function by the identity the hint index uses.

    Args:
        module: Parsed module.

    Returns:
        Node path by :func:`~astart.rules.hints.node_key`.

    """
    return {
        node_key(node=node): path
        for path, node in function_nodes(module=module).items()
    }
