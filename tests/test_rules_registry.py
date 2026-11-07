"""Verify the registries of node kinds, facts and procedures."""

from __future__ import annotations

import pytest
from astart.rules.registry import FactSpec, Registries, rule_cost
from astart.rules.vocabulary import Cost

from tests.expectations import expect_equal


def _registries() -> Registries:
    """Build a small registry.

    Returns:
        Registries with one fact per cost level.

    """
    return Registries(
        node_kinds=frozenset({"Call"}),
        facts={
            "a": FactSpec(name="a", value_type="bool", cost=Cost.syntactic),
            "b": FactSpec(name="b", value_type="int", cost=Cost.semantic),
            "c": FactSpec(name="c", value_type="bool", cost=Cost.scope),
        },
        procedures=frozenset(),
        appliers=frozenset(),
    )


def test_rule_cost_is_highest_required_fact() -> None:
    """Take the maximum cost over the required facts."""
    expect_equal(
        actual=rule_cost(registries=_registries(), requires=("a", "c", "b")),
        expected=Cost.semantic,
    )
    expect_equal(
        actual=rule_cost(registries=_registries(), requires=("a", "c")),
        expected=Cost.scope,
    )


def test_rule_cost_defaults_to_syntactic() -> None:
    """Cost nothing when nothing is required."""
    expect_equal(
        actual=rule_cost(registries=_registries(), requires=()),
        expected=Cost.syntactic,
    )


def test_unknown_fact_lists_known_names() -> None:
    """Name the facts that do exist."""
    with pytest.raises(
        expected_exception=KeyError,
        match="known facts: a, b, c",
    ):
        _registries().fact(name="zzz")
