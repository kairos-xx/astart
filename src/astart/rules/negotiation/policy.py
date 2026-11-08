"""When a settled belief is good enough to write as an annotation.

Confidence never decides this. A type is accepted only when every member of
it has independent support, nothing it depends on is opaque, and no conflict
is open. The inference engine counts only as corroboration of a type other
evidence already supports, never as a source of types.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Final, final

from astart.rules.negotiation.algebra import TypeAlgebra
from astart.rules.negotiation.model import Origin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart.rules.negotiation.beliefs import Belief
    from astart.rules.negotiation.builders import Built
    from astart.rules.negotiation.graph import ContractGraph
    from astart.rules.negotiation.model import Candidate
    from astart.rules.negotiation.negotiator import Negotiation


@final
class Constants:
    """Group module-level constants.

    Attributes:
        proofs: Origins that justify a type on their own.
        pair: Two soft signals that support each other.
        soft: Origins that need the engine's agreement or a partner.
        unspellable: Types that are never written.
        mutable: Container types whose element type a mutation can change.

    """

    proofs: Final[frozenset[Origin]] = frozenset(
        {Origin.syntax, Origin.declared, Origin.protocol},
    )
    pair: Final[frozenset[Origin]] = frozenset(
        {Origin.call_sites, Origin.default},
    )
    soft: Final[frozenset[Origin]] = frozenset(
        {Origin.call_sites, Origin.default, Origin.calibrated},
    )
    unspellable: Final[frozenset[str]] = frozenset({"object", "Any"})
    mutable: Final[frozenset[str]] = frozenset(
        {
            "list",
            "set",
            "dict",
            "deque",
            "defaultdict",
            "OrderedDict",
            "Counter",
            "bytearray",
            "MutableSequence",
            "MutableMapping",
            "MutableSet",
        },
    )


def opaque_closure(
    *,
    graph: ContractGraph,
    opaque: frozenset[str],
) -> frozenset[str]:
    """Spread opacity to everything that depends on an opaque node.

    Args:
        graph: The contract graph.
        opaque: Nodes with incomplete evidence.

    Returns:
        The opaque nodes and every node reachable from them.

    """
    reached: set[str] = set(opaque)
    pending: deque[str] = deque(iterable=sorted(opaque))
    while pending:
        current: str = pending.popleft()
        following: list[str] = [
            contract.target for contract in graph.outgoing(path=current)
        ]
        following.extend(
            item.target for item in graph.derived_from(path=current)
        )
        for target in following:
            if target not in reached:
                reached.add(target)
                pending.append(target)
    return frozenset(reached)


def _supported(*, candidate: Candidate, corroborated: bool) -> bool:
    """Tell whether one member of a type has enough independent support.

    Args:
        candidate: A candidate of the belief.
        corroborated: Whether the inference engine proposed the whole type.

    Returns:
        ``True`` for a proof, for two different soft signals, or for one soft
        signal plus the engine.

    """
    origins: frozenset[Origin] = candidate.origins
    if origins & Constants.proofs:
        return True
    if Constants.pair <= origins:
        return True
    return corroborated and bool(origins & Constants.soft)


def accept(
    *,
    belief: Belief,
    kind: str,
    opaque: frozenset[str],
    corroboration: Mapping[str, str],
) -> str | None:
    """Decide the annotation a belief justifies.

    Args:
        belief: The node's final belief.
        kind: ``"parameter"``, ``"return"``, ``"variable"`` or
            ``"attribute"``.
        opaque: Opaque nodes including everything downstream of them.
        corroboration: The inference engine's proposal by node path.

    Returns:
        The annotation source, or ``None`` when the evidence is not enough.

    """
    if belief.path in opaque or belief.declared is not None:
        return None
    settled: str | None = belief.settle()
    if settled is None:
        return None
    algebra: TypeAlgebra = TypeAlgebra()
    members: tuple[str, ...] = algebra.members(source=settled)
    if Constants.unspellable & set(members):
        return None
    if members == ("None",) and (
        kind in ("parameter", "variable")
        or not all(
            item.origins & Constants.proofs for item in belief.support()
        )
    ):
        return None
    proposal: str | None = corroboration.get(belief.path)
    corroborated: bool = proposal is not None and frozenset(
        algebra.members(source=proposal),
    ) == frozenset(members)
    if all(
        _supported(candidate=item, corroborated=corroborated)
        for item in belief.support()
    ):
        return settled
    return None


def container_risks(
    *,
    risky: frozenset[str],
    beliefs: Mapping[str, Belief],
) -> frozenset[str]:
    """Find risky nodes that settled to a mutable container.

    Args:
        risky: Nodes used in a way that could change a container's elements.
        beliefs: Final beliefs by path.

    Returns:
        The risky nodes whose settled type has a mutable container member.

    """
    algebra: TypeAlgebra = TypeAlgebra()
    found: set[str] = set()
    for path in risky:
        belief: Belief | None = beliefs.get(path)
        settled: str | None = None if belief is None else belief.settle()
        if settled is not None and any(
            member.partition("[")[0] in Constants.mutable
            for member in algebra.members(source=settled)
        ):
            found.add(path)
    return frozenset(found)


def blocked_nodes(
    *,
    built: Built,
    result: Negotiation,
) -> frozenset[str]:
    """Find every node whose evidence is incomplete.

    Args:
        built: The module's contract graph.
        result: The solved negotiation.

    Returns:
        Nodes marked opaque while building, risky containers that settled,
        nodes that lost a contribution while solving, and everything
        downstream of them.

    """
    return opaque_closure(
        graph=built.graph,
        opaque=built.opaque
        | container_risks(risky=built.risky, beliefs=result.beliefs)
        | result.lost,
    )
