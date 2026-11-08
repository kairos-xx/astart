"""Beliefs: how candidates combine and when a node settles."""

from __future__ import annotations

from astart.rules.negotiation import Belief, Candidate, Origin, Polarity

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)


def _c(
    *,
    type_text: str,
    confidence: float = 1.0,
    origin: Origin = Origin.syntax,
) -> Candidate:
    """Build a candidate.

    Args:
        type_text: The type.
        confidence: Its weight.
        origin: What supports it.

    Returns:
        The candidate.

    """
    return Candidate(
        type_text=type_text,
        confidence=confidence,
        distance=0,
        origins=frozenset({origin}),
        explanation=f"{type_text} from {origin.value}",
    )


def test_empty_belief_settles_to_nothing() -> None:
    """Check that no evidence gives no type."""
    expect_equal(actual=Belief(path="m.f.x").settle(), expected=None)


def test_unions_join_into_one_type() -> None:
    """Check that assignments of different types make a union."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="int"), polarity=Polarity.union)
    belief.add(candidate=_c(type_text="str"), polarity=Polarity.union)
    expect_equal(actual=belief.settle(), expected="int | str")


def test_too_many_members_do_not_settle() -> None:
    """Check that four distinct types exceed the limit."""
    belief: Belief = Belief(path="m.f.x")
    for name in ("int", "str", "bytes", "float"):
        belief.add(candidate=_c(type_text=name), polarity=Polarity.union)
    expect_equal(actual=belief.settle(), expected=None)


def test_same_type_merges_origins_and_keeps_best_confidence() -> None:
    """Check that equal types pool their support."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(
        candidate=_c(type_text="int", confidence=0.4, origin=Origin.inferred),
        polarity=Polarity.union,
    )
    changed: bool = belief.add(
        candidate=_c(type_text="int", confidence=0.9, origin=Origin.default),
        polarity=Polarity.union,
    )
    expect_true(condition=changed)
    expect_equal(
        actual=belief.origins(),
        expected=frozenset({Origin.inferred, Origin.default}),
    )
    expect_equal(actual=belief.candidates["int"].confidence, expected=0.9)


def test_repeating_a_candidate_changes_nothing() -> None:
    """Check that a duplicate reports no change."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="int"), polarity=Polarity.union)
    expect_false(
        condition=belief.add(
            candidate=_c(type_text="int"),
            polarity=Polarity.union,
        ),
    )


def test_intersection_narrows_a_union() -> None:
    """Check that ``isinstance`` style narrowing keeps the matching member."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="int | str"), polarity=Polarity.union)
    belief.add(
        candidate=_c(type_text="str"),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=belief.settle(), expected="str")


def test_empty_intersection_is_a_conflict() -> None:
    """Check that disjoint narrowing is recorded, not guessed."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="int"), polarity=Polarity.union)
    belief.add(
        candidate=_c(type_text="str"),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=len(belief.conflicts), expected=1)
    expect_equal(actual=belief.settle(), expected=None)


def test_undecided_intersection_leaves_the_type_alone() -> None:
    """Check that unknown classes do not change what settles."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="Foo"), polarity=Polarity.union)
    belief.add(
        candidate=_c(type_text="Bar"),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=belief.settle(), expected="Foo")
    expect_equal(actual=belief.conflicts, expected=[])


def test_narrowing_does_not_depend_on_arrival_order() -> None:
    """Check that a constraint before or after the union settles the same."""
    early: Belief = Belief(path="a")
    early.add(
        candidate=_c(type_text="str"),
        polarity=Polarity.intersection,
    )
    early.add(candidate=_c(type_text="int | str"), polarity=Polarity.union)
    late: Belief = Belief(path="b")
    late.add(candidate=_c(type_text="int | str"), polarity=Polarity.union)
    late.add(
        candidate=_c(type_text="str"),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=early.settle(), expected="str")
    expect_equal(actual=late.settle(), expected="str")


def test_not_none_constraint_removes_none() -> None:
    """Check that ``is not None`` strips ``None`` from the union."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="int | None"), polarity=Polarity.union)
    belief.add(
        candidate=_c(type_text="!None"),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=belief.settle(), expected="int")


def test_constraint_alone_is_an_upper_bound() -> None:
    """Check that a declared bound travelling back settles an empty node."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(
        candidate=_c(type_text="int", origin=Origin.declared),
        polarity=Polarity.intersection,
    )
    expect_equal(actual=belief.settle(), expected="int")
    expect_equal(actual=belief.origins(), expected=frozenset())
    expect_equal(
        actual=[item.type_text for item in belief.support()],
        expected=["int"],
    )


def test_declaration_is_hard() -> None:
    """Check that a disagreeing candidate conflicts with a declaration."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(
        candidate=_c(type_text="int", origin=Origin.declared),
        polarity=Polarity.declaration,
    )
    belief.add(candidate=_c(type_text="str"), polarity=Polarity.union)
    expect_equal(actual=len(belief.conflicts), expected=1)
    expect_equal(actual=belief.settle(), expected=None)


def test_narrower_candidate_agrees_with_a_declaration() -> None:
    """Check that ``bool`` is fine where ``int`` is declared."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(
        candidate=_c(type_text="int", origin=Origin.declared),
        polarity=Polarity.declaration,
    )
    belief.add(candidate=_c(type_text="bool"), polarity=Polarity.union)
    expect_equal(actual=belief.conflicts, expected=[])
    expect_equal(actual=belief.settle(), expected="int")


def test_late_declaration_checks_earlier_candidates() -> None:
    """Check that a declaration arriving last still catches a clash."""
    belief: Belief = Belief(path="m.f.x")
    belief.add(candidate=_c(type_text="str"), polarity=Polarity.union)
    belief.add(
        candidate=_c(type_text="int", origin=Origin.declared),
        polarity=Polarity.declaration,
    )
    expect_in(
        item="str",
        container=[conflict.right for conflict in belief.conflicts],
    )


def test_capability_carries_no_type() -> None:
    """Check that a capability contract adds no candidate."""
    belief: Belief = Belief(path="m.f.x")
    expect_false(
        condition=belief.add(
            candidate=_c(type_text="int"),
            polarity=Polarity.capability,
        ),
    )
    expect_equal(actual=belief.candidates, expected={})


def test_entropy_grows_with_competing_candidates() -> None:
    """Check that two equal candidates are less certain than one."""
    one: Belief = Belief(path="a")
    one.add(candidate=_c(type_text="int"), polarity=Polarity.union)
    two: Belief = Belief(path="b")
    two.add(candidate=_c(type_text="int"), polarity=Polarity.union)
    two.add(candidate=_c(type_text="str"), polarity=Polarity.union)
    expect_equal(actual=one.entropy(), expected=0.0)
    expect_true(condition=two.entropy() > one.entropy())
