"""The negotiator: forward and backward propagation to a fixpoint."""

from __future__ import annotations

from itertools import islice, permutations

from astart.rules.negotiation import (
    Candidate,
    Contract,
    ContractGraph,
    Negotiation,
    Negotiator,
    NegotiatorConfig,
    Origin,
    Polarity,
    Relation,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_true,
)


def _seed(
    *,
    graph: ContractGraph,
    path: str,
    type_text: str,
    origin: Origin = Origin.syntax,
    polarity: Polarity = Polarity.union,
) -> None:
    """Start a candidate at a node.

    Args:
        graph: The graph.
        path: The node.
        type_text: The seed type.
        origin: What supports it.
        polarity: How it contributes.

    """
    graph.seed(
        path=path,
        candidate=Candidate(
            type_text=type_text,
            confidence=1.0,
            distance=0,
            origins=frozenset({origin}),
            explanation=f"{path}: {type_text}",
        ),
        polarity=polarity,
    )


def _link(
    *,
    graph: ContractGraph,
    source: str,
    target: str,
    relation: Relation = Relation.assigns,
    polarity: Polarity = Polarity.union,
) -> None:
    """Add a contract with full trust.

    Args:
        graph: The graph.
        source: Source path.
        target: Target path.
        relation: What it states.
        polarity: How it contributes.

    """
    graph.add_contract(
        contract=Contract(
            source=source,
            target=target,
            relation=relation,
            polarity=polarity,
            confidence=1.0,
            decay=1.0,
            explanation=f"{source} {relation.value} {target}",
        ),
    )


def test_assignment_chain_carries_a_type_forward() -> None:
    """Check that ``a = 1; b = a; c = b`` types all three."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="a", type_text="int")
    _link(graph=graph, source="a", target="b")
    _link(graph=graph, source="b", target="c")
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="c"), expected="int")
    expect_false(condition=result.exhausted)


def test_two_assignments_join_into_a_union() -> None:
    """Check that ``x = 1`` and ``x = 'a'`` give ``int | str``."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="one", type_text="int")
    _seed(graph=graph, path="two", type_text="str")
    _link(graph=graph, source="one", target="x")
    _link(graph=graph, source="two", target="x")
    expect_equal(
        actual=Negotiator().solve(graph=graph).settled(path="x"),
        expected="int | str",
    )


def test_declared_type_travels_back_to_the_source() -> None:
    """Check that a declared parameter constrains the argument it receives."""
    graph: ContractGraph = ContractGraph()
    _link(
        graph=graph,
        source="caller.arg",
        target="callee.p",
        relation=Relation.argument,
        polarity=Polarity.declaration,
    )
    _seed(
        graph=graph,
        path="callee.p",
        type_text="int",
        origin=Origin.declared,
        polarity=Polarity.declaration,
    )
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="caller.arg"), expected="int")


def test_a_union_assignment_is_not_pushed_back() -> None:
    """Check that ``x = y; x = 1`` does not make ``y`` an ``int``."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="lit", type_text="int")
    _link(graph=graph, source="lit", target="x")
    _link(graph=graph, source="y", target="x")
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="y"), expected=None)


def test_element_of_a_container_is_extracted() -> None:
    """Check that iterating a ``list[int]`` gives ``int`` elements."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="xs", type_text="list[int]")
    _link(graph=graph, source="xs", target="item", relation=Relation.element)
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="item"), expected="int")


def test_mapping_key_and_value() -> None:
    """Check that ``dict[str, int]`` gives ``str`` keys and ``int`` values."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="d", type_text="dict[str, int]")
    _link(graph=graph, source="d", target="k", relation=Relation.key)
    _link(graph=graph, source="d", target="v", relation=Relation.mapping_value)
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="k"), expected="str")
    expect_equal(actual=result.settled(path="v"), expected="int")


def test_an_unknown_container_gives_no_element() -> None:
    """Check that a user class is not guessed to be iterable."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="box", type_text="Box")
    _link(graph=graph, source="box", target="item", relation=Relation.element)
    expect_equal(
        actual=Negotiator().solve(graph=graph).settled(path="item"),
        expected=None,
    )


def test_a_copy_cycle_terminates() -> None:
    """Check that ``x = y; y = x`` does not run away."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="x", type_text="int")
    _link(graph=graph, source="x", target="y")
    _link(graph=graph, source="y", target="x")
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="y"), expected="int")
    expect_false(condition=result.exhausted)


def test_a_self_containing_list_terminates() -> None:
    """Check that ``x = []; x.append(x)`` stays bounded."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="x", type_text="list[int]")
    _link(graph=graph, source="x", target="x", relation=Relation.element)
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_true(
        condition=len(result.snapshots) <= NegotiatorConfig().max_iterations,
    )


def test_conflicting_declaration_is_reported_not_resolved() -> None:
    """Check that an ``int`` flowing into ``str`` declares a conflict."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="n", type_text="int")
    _link(graph=graph, source="n", target="s")
    _seed(
        graph=graph,
        path="s",
        type_text="str",
        origin=Origin.declared,
        polarity=Polarity.declaration,
    )
    result: Negotiation = Negotiator().solve(graph=graph)
    expect_equal(actual=result.settled(path="s"), expected=None)
    expect_equal(actual=len(result.conflicts), expected=1)


def test_weak_candidates_are_pruned() -> None:
    """Check that decay below the floor stops propagation."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="a", type_text="int")
    for left, right in (("a", "b"), ("b", "c"), ("c", "d")):
        _link(graph=graph, source=left, target=right)
    config: NegotiatorConfig = NegotiatorConfig(
        forward_decay=0.1,
        minimum_confidence=0.05,
    )
    result: Negotiation = Negotiator(config=config).solve(graph=graph)
    expect_equal(actual=result.settled(path="b"), expected="int")
    expect_equal(actual=result.settled(path="d"), expected=None)


def test_event_cap_marks_the_run_exhausted() -> None:
    """Check that hitting the event bound is reported."""
    graph: ContractGraph = ContractGraph()
    _seed(graph=graph, path="n0", type_text="int")
    for index in range(20):
        _link(graph=graph, source=f"n{index}", target=f"n{index + 1}")
    result: Negotiation = Negotiator(
        config=NegotiatorConfig(max_events=3),
    ).solve(
        graph=graph,
    )
    expect_true(condition=result.exhausted)


def test_result_does_not_depend_on_edge_insertion_order() -> None:
    """Check that permuting the construction gives identical beliefs."""
    edges: list[tuple[str, str]] = [
        ("a", "b"),
        ("b", "c"),
        ("a", "c"),
        ("c", "d"),
        ("x", "d"),
    ]
    outcomes: list[dict[str, str | None]] = []
    for order in islice(permutations(iterable=edges), 0, None, 7):
        graph: ContractGraph = ContractGraph()
        _seed(graph=graph, path="a", type_text="int")
        _seed(graph=graph, path="x", type_text="str")
        for left, right in order:
            _link(graph=graph, source=left, target=right)
        result: Negotiation = Negotiator().solve(graph=graph)
        outcomes.append(
            {path: result.settled(path=path) for path in graph.nodes},
        )
    expect_true(condition=len(outcomes) > len(edges))
    expect_true(condition=all(item == outcomes[0] for item in outcomes))
    expect_equal(actual=outcomes[0]["d"], expected="int | str")
