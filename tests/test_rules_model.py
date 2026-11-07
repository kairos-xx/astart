"""Verify the entity model of the rule ontology."""

from __future__ import annotations

import pytest
from astart.rules.model import (
    Catalog,
    EvidenceSlot,
    Example,
    Fix,
    Profile,
    Relation,
    RelationKind,
    Rule,
    catalog_from_json,
    make_fingerprint,
    to_json,
)
from astart.rules.predicate import Compare, CompareOp
from astart.rules.vocabulary import (
    Domain,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_not_equal,
    expect_true,
)


def _rule(
    *,
    key: str = "typing.no-any",
    when: Compare | None = None,
    procedure: str | None = None,
) -> Rule:
    """Build a rule with the given trigger.

    Args:
        key: Rule key.
        when: Declarative trigger.
        procedure: Procedural trigger.

    Returns:
        The rule.

    """
    return Rule(
        key=key,
        code="TYP001",
        title="typing.Any usage",
        rationale="Any hides types.",
        domain=Domain.typing,
        severity=Severity.error,
        maturity=Maturity.stable,
        owner=Owner.astart,
        subject=("Annotation",),
        when=when,
        procedure=procedure,
        requires=("annotation.uses_typing_any",),
        message="`Any` used in `{name}`.",
        evidence=(EvidenceSlot(name="name", type="str"),),
        fixes=("typing.add-final",),
        examples=(
            Example(
                source="""\
x: Any = 1
""",
                triggers=True,
            ),
        ),
        aliases={"exactus": "CMP002"},
        params={"limit": 3},
    )


def _trigger() -> Compare:
    """Build a simple declarative trigger.

    Returns:
        The comparison.

    """
    return Compare(
        fact="annotation.uses_typing_any",
        op=CompareOp.eq,
        value=True,
    )


def test_rule_requires_exactly_one_trigger() -> None:
    """Reject a rule with no trigger or two triggers."""
    with pytest.raises(expected_exception=ValueError, match="exactly one"):
        _rule()
    with pytest.raises(expected_exception=ValueError, match="exactly one"):
        _rule(when=_trigger(), procedure="docs.check")


def test_rule_expressible_is_derived() -> None:
    """Derive expressibility from the trigger."""
    expect_equal(
        actual=_rule(when=_trigger()).expressible.value,
        expected="declarative",
    )
    expect_equal(
        actual=_rule(procedure="docs.check").expressible.value,
        expected="procedural",
    )


def test_catalog_round_trip_every_entity() -> None:
    """Serialize and restore a catalog holding every entity kind."""
    catalog: Catalog = Catalog(
        rules=(
            _rule(when=_trigger()),
            _rule(key="docs.other", procedure="docs.check"),
        ),
        fixes=(
            Fix(
                key="typing.add-final",
                rules=("typing.no-any",),
                safety=FixSafety.guarded,
                min_confidence=0.9,
                edits=("typing.add-final",),
                preconditions=_trigger(),
                idempotent=True,
                before=("a",),
                after=("b",),
            ),
        ),
        profiles=(
            Profile(
                key="strict",
                rules=("typing.no-any",),
                severities={"typing.no-any": Severity.warning},
                params={"limit": 1},
                safety_ceiling=FixSafety.proven,
            ),
        ),
        relations=(
            Relation(
                kind=RelationKind.ordered_before,
                source="a",
                target="b",
            ),
        ),
    )
    expect_equal(
        actual=catalog_from_json(value=to_json(item=catalog)),
        expected=catalog,
    )


def test_catalog_lookup_unknown_key_raises() -> None:
    """Report an unknown rule or fix."""
    catalog: Catalog = Catalog(
        rules=(_rule(when=_trigger()),),
        fixes=(),
        profiles=(),
        relations=(),
    )
    expect_equal(
        actual=catalog.rule(key="typing.no-any").code,
        expected="TYP001",
    )
    with pytest.raises(expected_exception=KeyError, match="missing"):
        catalog.rule(key="missing")
    with pytest.raises(expected_exception=KeyError, match="missing"):
        catalog.fix(key="missing")


def test_fingerprint_is_stable_and_evidence_sensitive() -> None:
    """Hash identity without any line numbers."""
    first: str = make_fingerprint(
        rule_key="r",
        subject_path="m.f",
        evidence={"name": "x"},
    )
    again: str = make_fingerprint(
        rule_key="r",
        subject_path="m.f",
        evidence={"name": "x"},
    )
    other: str = make_fingerprint(
        rule_key="r",
        subject_path="m.f",
        evidence={"name": "y"},
    )
    expect_equal(actual=first, expected=again)
    expect_not_equal(actual=first, unexpected=other)
    expect_equal(actual=len(first), expected=16)
    expect_true(condition=all(c in "0123456789abcdef" for c in first))
    expect_false(condition=first == "")


def test_from_json_rejects_malformed_catalog() -> None:
    """Name the offending key."""
    with pytest.raises(expected_exception=ValueError, match="rules"):
        catalog_from_json(value={"fixes": [], "profiles": [], "relations": []})
    with pytest.raises(expected_exception=ValueError, match="object"):
        catalog_from_json(value=[])
