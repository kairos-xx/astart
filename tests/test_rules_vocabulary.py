"""Verify the closed vocabulary of the rule ontology."""

from __future__ import annotations

from astart.rules.jsonvalue import canonical_dumps
from astart.rules.vocabulary import (
    Cost,
    Domain,
    Expressible,
    FixSafety,
    Maturity,
    Owner,
    Phase,
    Severity,
)

from tests.expectations import expect_equal, expect_true


def test_cost_rank_orders_levels() -> None:
    """Rank costs from syntactic up to project."""
    ranks: list[int] = [
        Cost.syntactic.rank(),
        Cost.scope.rank(),
        Cost.semantic.rank(),
        Cost.project.rank(),
    ]
    expect_equal(actual=ranks, expected=[0, 1, 2, 3])
    expect_true(condition=Cost.syntactic.rank() < Cost.project.rank())


def test_enum_members_match_spec() -> None:
    """Keep every enum aligned with the design table."""
    expect_equal(
        actual={member.value for member in Domain},
        expected={
            "parsing",
            "suppression",
            "typing",
            "calls",
            "imports",
            "docs",
            "oop",
            "naming",
            "simplification",
            "whitespace",
            "structure",
            "config",
        },
    )
    expect_equal(
        actual={member.value for member in Severity},
        expected={"error", "warning", "info"},
    )
    expect_equal(
        actual=[member.value for member in Phase],
        expected=["facts", "check", "fix", "format"],
    )
    expect_equal(
        actual={member.value for member in FixSafety},
        expected={"proven", "guarded", "suggest", "none"},
    )
    expect_equal(
        actual={member.value for member in Owner},
        expected={"astart", "ruff"},
    )
    expect_equal(
        actual={member.value for member in Maturity},
        expected={"experimental", "stable", "deprecated"},
    )
    expect_equal(
        actual={member.value for member in Cost},
        expected={"syntactic", "scope", "semantic", "project"},
    )
    expect_equal(
        actual={member.value for member in Expressible},
        expected={"declarative", "procedural"},
    )


def test_canonical_dumps_sorts_keys_and_ends_with_newline() -> None:
    """Emit stable, readable JSON."""
    text: str = canonical_dumps(value={"b": 1, "a": ["é"]})
    expect_equal(
        actual=text,
        expected="""\
{
  "a": [
    "é"
  ],
  "b": 1
}
""",
    )
