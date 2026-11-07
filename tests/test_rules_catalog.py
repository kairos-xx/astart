"""Verify catalog loading and the data invariants."""

from __future__ import annotations

from dataclasses import replace
from typing import TypedDict, Unpack

import pytest
from astart.rules.catalog import (
    CatalogError,
    dump_catalog,
    load_catalog,
    validate_catalog,
)
from astart.rules.model import (
    Catalog,
    Example,
    Fix,
    Profile,
    Relation,
    RelationKind,
    Rule,
)
from astart.rules.predicate import Compare, CompareOp
from astart.rules.registry import FactSpec, Registries
from astart.rules.vocabulary import (
    Cost,
    Domain,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

from tests.expectations import expect_equal, expect_true


def _registries() -> Registries:
    """Build the registries used by every test.

    Returns:
        Registries with one fact per cost level and one applier.

    """
    return Registries(
        node_kinds=frozenset({"Call", "Module"}),
        facts={
            "a": FactSpec(name="a", value_type="bool", cost=Cost.syntactic),
            "s": FactSpec(name="s", value_type="bool", cost=Cost.scope),
            "m": FactSpec(name="m", value_type="bool", cost=Cost.semantic),
        },
        procedures=frozenset({"docs.check"}),
        appliers=frozenset({"apply.one"}),
    )


class _RuleOptions(TypedDict, total=False):
    """Optional overrides accepted by :func:`_rule`.

    Attributes:
        subject: Node kinds.
        fact: Fact the trigger reads.
        requires: Declared requirements.
        fixes: Fix keys.
        aliases: External ids.
        procedure: Procedural trigger instead of a predicate.

    """

    subject: tuple[str, ...]
    fact: str
    requires: tuple[str, ...]
    fixes: tuple[str, ...]
    aliases: dict[str, str]
    procedure: str


def _rule(
    *,
    key: str = "r.one",
    code: str = "AAA001",
    **options: Unpack[_RuleOptions],
) -> Rule:
    """Build a rule that reads one fact.

    Args:
        key: Rule key.
        code: Rule code.
        **options: Optional overrides.

    Returns:
        The rule.

    """
    fact: str = options.get("fact", "a")
    procedure: str | None = options.get("procedure")
    trigger: Compare | None = (
        None
        if procedure is not None
        else Compare(fact=fact, op=CompareOp.eq, value=True)
    )
    return Rule(
        key=key,
        code=code,
        title="t",
        rationale="r",
        domain=Domain.typing,
        severity=Severity.error,
        maturity=Maturity.stable,
        owner=Owner.astart,
        subject=options.get("subject", ("Call",)),
        message="m",
        when=trigger,
        procedure=procedure,
        requires=options.get("requires", (fact,)),
        fixes=options.get("fixes", ()),
        examples=(
            Example(
                source="""\
x = 1
""",
                triggers=True,
            ),
            Example(
                source="""\
y = 1
""",
                triggers=False,
            ),
        ),
        aliases=options.get("aliases", {}),
    )


def _fix(
    *,
    key: str = "f.one",
    safety: FixSafety = FixSafety.guarded,
    fact: str = "a",
    edits: tuple[str, ...] = ("apply.one",),
) -> Fix:
    """Build a fix with one precondition.

    Args:
        key: Fix key.
        safety: Safety class.
        fact: Fact the precondition reads.
        edits: Applier keys.

    Returns:
        The fix.

    """
    return Fix(
        key=key,
        rules=("r.one",),
        safety=safety,
        min_confidence=0.9,
        edits=edits,
        preconditions=Compare(fact=fact, op=CompareOp.eq, value=True),
        idempotent=True,
    )


def _catalog(
    *,
    rules: tuple[Rule, ...] = (),
    fixes: tuple[Fix, ...] = (),
    profiles: tuple[Profile, ...] = (),
    relations: tuple[Relation, ...] = (),
) -> Catalog:
    """Assemble a catalog.

    Args:
        rules: Rules.
        fixes: Fixes.
        profiles: Profiles.
        relations: Relations.

    Returns:
        The catalog.

    """
    return Catalog(
        rules=rules,
        fixes=fixes,
        profiles=profiles,
        relations=relations,
    )


def _problems(*, catalog: Catalog) -> tuple[str, ...]:
    """Validate and return the reported problems.

    Args:
        catalog: Catalog to validate.

    Returns:
        The problems, empty when valid.

    """
    try:
        validate_catalog(catalog=catalog, registries=_registries())
    except CatalogError as error:
        return error.problems
    return ()


def _mentions(*, problems: tuple[str, ...], text: str) -> None:
    """Assert some problem mentions the text.

    Args:
        problems: Reported problems.
        text: Expected fragment.

    """
    expect_true(
        condition=any(text in problem for problem in problems),
        message=f"no problem mentions {text!r}: {problems}",
    )


def test_duplicate_code_is_reported() -> None:
    """Reject two rules sharing a code."""
    problems = _problems(
        catalog=_catalog(rules=(_rule(), _rule(key="r.two"))),
    )
    _mentions(problems=problems, text="duplicate rule code 'AAA001'")


def test_duplicate_key_is_reported() -> None:
    """Reject two rules sharing a key."""
    problems = _problems(
        catalog=_catalog(rules=(_rule(), _rule(code="AAA002"))),
    )
    _mentions(problems=problems, text="duplicate rule key 'r.one'")


def test_unknown_subject_is_reported() -> None:
    """Reject a node kind the engine does not know."""
    _mentions(
        problems=(
            _problems(catalog=_catalog(rules=(_rule(subject=("Nope",)),)))
        ),
        text="unknown node kind 'Nope'",
    )


def test_unknown_fact_is_reported() -> None:
    """Reject a fact that is not declared."""
    _mentions(
        problems=(_problems(catalog=_catalog(rules=(_rule(fact="zzz"),)))),
        text="unknown fact 'zzz'",
    )


def test_unknown_fix_and_applier_and_procedure_are_reported() -> None:
    """Reject dangling references."""
    problems = _problems(
        catalog=_catalog(
            rules=(
                _rule(fixes=("f.missing",)),
                _rule(
                    key="r.proc",
                    code="AAA002",
                    procedure="nope.proc",
                    requires=(),
                ),
            ),
            fixes=(_fix(edits=("apply.missing",)),),
        ),
    )
    _mentions(problems=problems, text="unknown fix 'f.missing'")
    _mentions(problems=problems, text="unknown applier 'apply.missing'")
    _mentions(problems=problems, text="unknown procedure 'nope.proc'")


def test_ordered_before_cycle_is_reported() -> None:
    """Reject circular ordering."""
    problems = _problems(
        catalog=_catalog(
            relations=(
                Relation(
                    kind=RelationKind.ordered_before,
                    source="a",
                    target="b",
                ),
                Relation(
                    kind=RelationKind.ordered_before,
                    source="b",
                    target="a",
                ),
            ),
        ),
    )
    _mentions(problems=problems, text="ordering cycle")


def test_conflicting_rules_in_one_profile_are_reported() -> None:
    """Reject a profile enabling two conflicting rules."""
    problems = _problems(
        catalog=_catalog(
            rules=(_rule(), _rule(key="r.two", code="AAA002")),
            profiles=(
                Profile(
                    key="p",
                    rules=("r.one", "r.two"),
                    severities={},
                    params={},
                    safety_ceiling=FixSafety.proven,
                ),
            ),
            relations=(
                Relation(
                    kind=RelationKind.conflicts_with,
                    source="r.one",
                    target="r.two",
                ),
            ),
        ),
    )
    _mentions(problems=problems, text="profile 'p' enables conflicting")


def test_proven_fix_cannot_need_semantic_fact() -> None:
    """Keep proven fixes independent of inference."""
    problems = _problems(
        catalog=_catalog(
            rules=(_rule(fixes=("f.one",)),),
            fixes=(_fix(safety=FixSafety.proven, fact="m"),),
        ),
    )
    _mentions(problems=problems, text="proven fix 'f.one'")
    clean = _problems(
        catalog=_catalog(
            rules=(_rule(fixes=("f.one",)),),
            fixes=(_fix(safety=FixSafety.proven, fact="s"),),
        ),
    )
    expect_equal(actual=clean, expected=())


def test_declared_requires_must_match_predicate_facts() -> None:
    """Derive cost from what the trigger reads."""
    problems = _problems(
        catalog=_catalog(rules=(_rule(fact="a", requires=("a", "m")),)),
    )
    _mentions(problems=problems, text="requires must equal")


def test_duplicate_alias_per_system_is_reported() -> None:
    """Reject one external id mapped to two rules."""
    problems = _problems(
        catalog=_catalog(
            rules=(
                _rule(aliases={"exactus": "CMP002"}),
                _rule(
                    key="r.two",
                    code="AAA002",
                    aliases={"exactus": "CMP002"},
                ),
            ),
        ),
    )
    _mentions(problems=problems, text="duplicate alias 'CMP002'")


def test_all_problems_are_collected_in_one_error() -> None:
    """Report everything wrong at once."""
    problems = _problems(
        catalog=_catalog(
            rules=(_rule(subject=("Nope",), fact="zzz"), _rule()),
        ),
    )
    _mentions(problems=problems, text="duplicate rule key 'r.one'")
    _mentions(problems=problems, text="unknown node kind 'Nope'")
    _mentions(problems=problems, text="unknown fact 'zzz'")


def test_valid_catalog_has_no_problems() -> None:
    """Accept a consistent catalog, including procedural rules."""
    catalog = _catalog(
        rules=(
            _rule(fixes=("f.one",)),
            _rule(
                key="r.proc",
                code="AAA002",
                procedure="docs.check",
                requires=(),
            ),
        ),
        fixes=(_fix(),),
    )
    expect_equal(actual=_problems(catalog=catalog), expected=())


def test_empty_catalog_round_trips() -> None:
    """Load and dump a catalog with no entities."""
    text = dump_catalog(catalog=_catalog())
    loaded = load_catalog(text=text, registries=_registries())
    expect_equal(actual=loaded, expected=_catalog())
    expect_equal(actual=dump_catalog(catalog=loaded), expected=text)


def test_dump_load_is_idempotent() -> None:
    """Reach a fixed point after one dump."""
    first = dump_catalog(
        catalog=(_catalog(rules=(_rule(fixes=("f.one",)),), fixes=(_fix(),))),
    )
    second = dump_catalog(
        catalog=load_catalog(text=first, registries=_registries()),
    )
    expect_equal(actual=second, expected=first)


def test_load_rejects_invalid_json_and_invalid_catalog() -> None:
    """Surface parse and validation failures."""
    with pytest.raises(expected_exception=ValueError, match="Expecting"):
        load_catalog(text="{", registries=_registries())
    bad = dump_catalog(catalog=_catalog(rules=(_rule(fact="zzz"),)))
    with pytest.raises(expected_exception=CatalogError, match="unknown fact"):
        load_catalog(text=bad, registries=_registries())


def test_rule_needs_both_kinds_of_example() -> None:
    """Report rules with no examples or one-sided examples."""
    base = _rule()
    for examples in (
        (),
        (
            Example(
                source="""\
x = 1
""",
                triggers=True,
            ),
        ),
        (
            Example(
                source="""\
x = 1
""",
                triggers=False,
            ),
        ),
    ):
        problems = _problems(
            catalog=_catalog(rules=(replace(base, examples=examples),)),
        )
        _mentions(
            problems=problems,
            text="needs at least one triggering and one non-triggering",
        )
