"""The contract graph: stable queries whatever the insertion order."""

from __future__ import annotations

from astart.rules.negotiation import (
    Candidate,
    Contract,
    ContractGraph,
    Negotiator,
    Origin,
    Polarity,
    Relation,
)

from scripts.benchmark.ablation import SeedMeasurement, measure_seed_origins
from tests.support.expectations import expect_equal


def _contract(
    *,
    source: str,
    target: str,
    confidence: float = 1.0,
) -> Contract:
    """Build an assignment contract.

    Args:
        source (str): Source path.
        target (str): Target path.
        confidence (float): Trust in the contract.

    Returns:
        Contract: The contract.

    """
    return Contract(
        source=source,
        target=target,
        relation=Relation.assigns,
        polarity=Polarity.union,
        confidence=confidence,
        decay=1.0,
        explanation=f"{source} -> {target}",
    )


def test_adding_contracts_creates_nodes() -> None:
    """Check that both ends of a contract become nodes."""
    graph: ContractGraph = ContractGraph()
    graph.add_contract(contract=_contract(source="b", target="a"))
    expect_equal(actual=graph.nodes, expected=("a", "b"))


def test_adjacency_is_sorted_not_insertion_ordered() -> None:
    """Check that outgoing contracts come out in the same order."""
    names: tuple[str, ...] = ("z", "m", "a")
    first: ContractGraph = ContractGraph()
    second: ContractGraph = ContractGraph()
    for name in names:
        first.add_contract(contract=_contract(source="s", target=name))
    for name in reversed(names):
        second.add_contract(contract=_contract(source="s", target=name))
    expect_equal(
        actual=first.outgoing(path="s"),
        expected=second.outgoing(path="s"),
    )
    expect_equal(
        actual=[c.target for c in first.outgoing(path="s")],
        expected=["a", "m", "z"],
    )


def test_duplicate_contract_keeps_the_stronger() -> None:
    """Check that the same contract twice is stored once, strongest wins."""
    graph: ContractGraph = ContractGraph()
    graph.add_contract(
        contract=_contract(source="a", target="b", confidence=0.4),
    )
    graph.add_contract(
        contract=_contract(source="a", target="b", confidence=0.9),
    )
    found: tuple[Contract, ...] = graph.outgoing(path="a")
    expect_equal(actual=len(found), expected=1)
    expect_equal(actual=found[0].confidence, expected=0.9)


def test_incoming_lists_the_sources() -> None:
    """Check that incoming mirrors outgoing."""
    graph: ContractGraph = ContractGraph()
    graph.add_contract(contract=_contract(source="a", target="t"))
    graph.add_contract(contract=_contract(source="b", target="t"))
    expect_equal(
        actual=[c.source for c in graph.incoming(path="t")],
        expected=["a", "b"],
    )
    expect_equal(actual=graph.incoming(path="a"), expected=())


def test_seeds_are_sorted() -> None:
    """Check that seeds do not depend on the order they were added."""
    one: Candidate = Candidate(
        type_text="int",
        confidence=1.0,
        distance=0,
        origins=frozenset({Origin.syntax}),
        explanation="one",
    )
    two: Candidate = Candidate(
        type_text="str",
        confidence=1.0,
        distance=0,
        origins=frozenset({Origin.syntax}),
        explanation="two",
    )
    first: ContractGraph = ContractGraph()
    first.seed(path="y", candidate=two)
    first.seed(path="x", candidate=one)
    second: ContractGraph = ContractGraph()
    second.seed(path="x", candidate=one)
    second.seed(path="y", candidate=two)
    expect_equal(actual=first.seeds(), expected=second.seeds())


def test_seed_ablation_retracts_support_without_mutating_original() -> None:
    """Remove evidence before solving, preserving the original experiment."""
    graph: ContractGraph = ContractGraph()
    graph.add_contract(contract=_contract(source="a", target="b"))
    graph.seed(
        path="a",
        candidate=Candidate(
            type_text="int",
            confidence=1.0,
            distance=0,
            origins=frozenset({Origin.syntax}),
            explanation="literal",
        ),
    )
    filtered: ContractGraph = graph.seed_ablation(
        excluded=frozenset({Origin.syntax}),
    )
    expect_equal(
        actual=Negotiator().solve(graph=graph).settled(path="b"),
        expected="int",
    )
    expect_equal(
        actual=Negotiator().solve(graph=filtered).settled(path="b"),
        expected=None,
    )
    expect_equal(actual=len(graph.seeds()), expected=1)
    expect_equal(actual=filtered.has_input(path="a"), expected=False)
    filtered.add_node(path="new-experiment-only")
    expect_equal(actual=graph.nodes, expected=("a", "b"))
    measured: tuple[SeedMeasurement, ...] = measure_seed_origins(graph=graph)
    expect_equal(actual=measured[0].settled_nodes, expected=2)
    removed: SeedMeasurement = next(
        item for item in measured if item.variant == "without:syntax"
    )
    expect_equal(actual=removed.removed_seeds, expected=1)
    expect_equal(actual=removed.settled_nodes, expected=0)
