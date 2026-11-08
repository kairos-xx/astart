"""The contract graph: stable queries whatever the insertion order."""

from __future__ import annotations

from astart.rules.negotiation import (
    Candidate,
    Contract,
    ContractGraph,
    Origin,
    Polarity,
    Relation,
)

from tests.expectations import expect_equal


def _contract(
    *,
    source: str,
    target: str,
    confidence: float = 1.0,
) -> Contract:
    """Build an assignment contract.

    Args:
        source: Source path.
        target: Target path.
        confidence: Trust in the contract.

    Returns:
        The contract.

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
