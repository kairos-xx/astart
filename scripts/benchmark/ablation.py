"""Measure seed-origin sensitivity without reparsing or editing source."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, final

from astart.rules.negotiation import Negotiation, Negotiator, Origin

if TYPE_CHECKING:
    from astart.rules.negotiation.graph import ContractGraph


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SeedMeasurement:
    """One solver experiment, not an annotation-accuracy score.

    Attributes:
        variant (str): All seeds or one excluded seed origin.
        removed_seeds (int): Candidates excluded before solving.
        settled_nodes (int): Nodes with a settled result.
        conflicts (int): Solver conflicts.
        exhausted (bool): Whether solver limits stopped the experiment.
        seconds (float): Measured solver time, excluding graph construction.

    """

    variant: str
    removed_seeds: int
    settled_nodes: int
    conflicts: int
    exhausted: bool
    seconds: float


def measure_seed_origins(
    *,
    graph: ContractGraph,
) -> tuple[SeedMeasurement, ...]:
    """Compare baseline and leave-one-origin-out with isolated solver state.

    Derived rules and fixed declaration inputs remain unchanged. This is
    deliberately a seed-only diagnostic; full accepted-annotation ablation
    must also instrument those producers and score the reference pair.

    Args:
        graph (ContractGraph): Existing contracts over the authoritative
            module's AST nodes.

    Returns:
        tuple[SeedMeasurement, ...]: Baseline followed by one experiment per
            origin, in enum order.

    """
    count: int = len(graph.seeds())
    measurements: list[SeedMeasurement] = []
    for origin in (None, *Origin):
        excluded: frozenset[Origin] = (
            frozenset() if origin is None else frozenset({origin})
        )
        experiment: ContractGraph = graph.seed_ablation(excluded=excluded)
        start: float = perf_counter()
        result: Negotiation = Negotiator().solve(graph=experiment)
        elapsed: float = perf_counter() - start
        measurements.append(
            SeedMeasurement(
                variant="all" if origin is None else f"without:{origin.value}",
                removed_seeds=count - len(experiment.seeds()),
                settled_nodes=sum(
                    belief.settle() is not None
                    for belief in result.beliefs.values()
                ),
                conflicts=len(result.conflicts),
                exhausted=result.exhausted,
                seconds=elapsed,
            ),
        )
    return tuple(measurements)
