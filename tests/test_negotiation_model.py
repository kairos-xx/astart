"""Candidates, provenance and contracts of the negotiation model."""

from __future__ import annotations

from astart.rules.negotiation import Candidate, Origin

from tests.expectations import expect_equal, expect_false, expect_true


def _candidate(*, origins: frozenset[Origin]) -> Candidate:
    """Build a candidate with the given support.

    Args:
        origins: What supports the type.

    Returns:
        A candidate for ``int``.

    """
    return Candidate(
        type_text="int",
        confidence=1.0,
        distance=0,
        origins=origins,
        explanation="seed",
    )


def test_inference_alone_is_not_independent() -> None:
    """Check that an engine-only candidate lacks independent support."""
    expect_false(
        condition=_candidate(origins=frozenset({Origin.inferred})).independent,
    )


def test_any_other_origin_is_independent() -> None:
    """Check that syntax, call sites, defaults and declarations count."""
    for origin in (
        Origin.syntax,
        Origin.declared,
        Origin.call_sites,
        Origin.default,
    ):
        expect_true(
            condition=_candidate(
                origins=frozenset({Origin.inferred, origin}),
            ).independent,
        )


def test_decay_lowers_confidence_and_extends_distance() -> None:
    """Check that crossing a contract weakens a candidate."""
    moved: Candidate = _candidate(origins=frozenset({Origin.syntax})).decayed(
        decay=0.5,
    )
    expect_equal(actual=moved.confidence, expected=0.5)
    expect_equal(actual=moved.distance, expected=1)


def test_retyping_keeps_the_support() -> None:
    """Check that a transferred type keeps its origins."""
    moved: Candidate = _candidate(origins=frozenset({Origin.syntax})).retyped(
        type_text="str",
    )
    expect_equal(actual=moved.type_text, expected="str")
    expect_equal(actual=moved.origins, expected=frozenset({Origin.syntax}))
