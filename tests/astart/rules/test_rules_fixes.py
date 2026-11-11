"""Verify the fixes and the behavioural catalog invariants."""

from __future__ import annotations

from ast import Pass
from dataclasses import replace
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.rules.catalog import CatalogError
from astart.rules.engine import (
    CheckResult,
    apply_fix,
    check,
    validate_behavior,
)
from astart.rules.facts import default_registries
from astart.rules.model import Catalog, Example, Finding, Fix, Rule
from astart.rules.predicate import AllOf, Compare, CompareOp, Not, Predicate
from astart.rules.vocabulary import (
    Domain,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

from tests.support.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from astart.rules.facts import ModuleFacts, Subject
    from astart.rules.registry import Registries


def _flag(*, name: str, value: bool = True) -> Compare:
    """Build a boolean comparison.

    Args:
        name (str): Fact name.
        value (bool): Expected value.

    Returns:
        Compare: The comparison.

    """
    return Compare(fact=name, op=CompareOp.eq, value=value)


def _final_fix(*, edits: tuple[str, ...] = ("typing.add-final",)) -> Fix:
    """Build the proven Final fix.

    Args:
        edits (tuple[str, ...]): Applier keys.

    Returns:
        Fix: The fix.

    """
    return Fix(
        key="typing.add-final",
        rules=("glob",),
        safety=FixSafety.proven,
        min_confidence=1.0,
        edits=edits,
        preconditions=_flag(name="binding.value_is_immutable_literal"),
        idempotent=True,
    )


def _keyword_fix() -> Fix:
    """Build the guarded keyword fix.

    Returns:
        Fix: The fix.

    """
    return Fix(
        key="calls.add-keywords",
        rules=("kw",),
        safety=FixSafety.guarded,
        min_confidence=0.9,
        edits=("calls.add-keywords",),
        preconditions=_flag(name="call.is_resolved_in_module"),
        idempotent=True,
    )


def _rule(
    *,
    key: str,
    subject: str,
    when: Predicate,
    requires: tuple[str, ...],
    fix: str,
) -> Rule:
    """Build a rule offering one fix.

    Args:
        key (str): Rule key; the code is derived from it.
        subject (str): Node kind to inspect.
        when (Predicate): Declarative trigger.
        requires (tuple[str, ...]): Facts the trigger reads.
        fix (str): Fix key.

    Returns:
        Rule: The rule.

    """
    return Rule(
        key=key,
        code=key.upper(),
        title=key,
        rationale="test",
        domain=Domain.typing,
        severity=Severity.error,
        maturity=Maturity.stable,
        owner=Owner.astart,
        subject=(subject,),
        message="m",
        when=when,
        requires=requires,
        fixes=(fix,),
    )


def _catalog(
    *,
    final_examples: tuple[Example, ...] = (),
    keyword_examples: tuple[Example, ...] = (),
    final_fix: Fix | None = None,
) -> Catalog:
    """Build a catalog with the Final and keyword rules.

    Args:
        final_examples (tuple[Example, ...]): Examples of the Final rule.
        keyword_examples (tuple[Example, ...]): Examples of the keyword rule.
        final_fix (Fix | None): Replacement for the Final fix.

    Returns:
        Catalog: The catalog.

    """
    glob: Rule = _rule(
        key="glob",
        subject="Assign",
        when=AllOf(
            items=(
                _flag(name="binding.is_module_global"),
                _flag(name="binding.name_is_uppercase"),
                Not(item=_flag(name="binding.is_final")),
            ),
        ),
        requires=(
            "binding.is_final",
            "binding.is_module_global",
            "binding.name_is_uppercase",
        ),
        fix="typing.add-final",
    )
    keyword: Rule = _rule(
        key="kw",
        subject="Call",
        when=Compare(
            fact="call.positional_keyword_candidates",
            op=CompareOp.gt,
            value=0,
        ),
        requires=("call.positional_keyword_candidates",),
        fix="calls.add-keywords",
    )
    return Catalog(
        rules=(
            replace(glob, examples=final_examples),
            replace(keyword, examples=keyword_examples),
        ),
        fixes=(final_fix or _final_fix(), _keyword_fix()),
        profiles=(),
        relations=(),
    )


def _fix_all(*, source: str, catalog: Catalog, key: str) -> tuple[str, int]:
    """Apply a fix to the first finding that offers it.

    Args:
        source (str): Python source.
        catalog (Catalog): Catalog under test.
        key (str): Fix key.

    Returns:
        tuple[str, int]: The new source and the number of findings that offered
            the fix.

    """
    registries: Registries = default_registries()
    result: CheckResult = check(
        source=source,
        filename="s.py",
        catalog=catalog,
        registries=registries,
    )
    offering: list[Finding] = [
        f
        for f in result.findings
        if any(o.fix_key == key for o in f.fix_offers)
    ]
    if not offering:
        return source, 0
    fixed: str = apply_fix(
        source=source,
        finding=offering[0],
        fix=catalog.fix(key=key),
        registries=registries,
    )
    return fixed, len(offering)


def test_add_final_rewrites_literal_global() -> None:
    """Annotate the literal and import Final, keeping comments."""
    source: str = dedent(
        text='''\
        """Doc."""
        from __future__ import annotations

        # keep
        LIMIT = 3  # trailing
        ''',
    )
    fixed, offered = _fix_all(
        source=source,
        catalog=_catalog(),
        key="typing.add-final",
    )
    expect_equal(actual=offered, expected=1)
    expect_in(item="LIMIT: Final[int] = 3  # trailing", container=fixed)
    expect_in(item="from typing import Final", container=fixed)
    expect_in(item="# keep", container=fixed)


def test_add_final_reuses_existing_final_alias() -> None:
    """Use the module's own spelling of Final."""
    source: str = """\
from typing import Final as F

NAME = 'x'
"""
    fixed, _ = _fix_all(
        source=source,
        catalog=_catalog(),
        key="typing.add-final",
    )
    expect_in(item="NAME: F[str] = 'x'", container=fixed)
    expect_equal(actual=fixed.count("import"), expected=1)
    aliased: str = """\
import typing as t

NAME = 1.5
"""
    fixed_alias, _ = _fix_all(
        source=aliased,
        catalog=_catalog(),
        key="typing.add-final",
    )
    expect_in(item="NAME: t.Final[float] = 1.5", container=fixed_alias)


def test_add_final_skips_non_literal_value() -> None:
    """Leave computed values alone."""
    source: str = """\
LIMIT = compute()
"""
    fixed, offered = _fix_all(
        source=source,
        catalog=_catalog(),
        key="typing.add-final",
    )
    expect_equal(actual=offered, expected=0)
    expect_equal(actual=fixed, expected=source)


def test_add_keywords_rewrites_resolved_call() -> None:
    """Pass the keyword-capable arguments by name."""
    source: str = """\
def f(a, /, b, c): ...


f(1, 2, 3)  # call
"""
    fixed, offered = _fix_all(
        source=source,
        catalog=_catalog(),
        key="calls.add-keywords",
    )
    expect_equal(actual=offered, expected=1)
    expect_in(item="f(1, b=2, c=3)  # call", container=fixed)


def test_add_keywords_leaves_unsafe_calls() -> None:
    """Report nothing for positional-only and absorbed arguments."""
    source: str = """\
def f(a, /): ...
def g(a, *rest): ...
f(1)
g(1, 2)
"""
    result: CheckResult = check(
        source=source,
        filename="s.py",
        catalog=_catalog(),
        registries=default_registries(),
    )
    expect_equal(
        actual=[f for f in result.findings if f.rule_key == "kw"],
        expected=[],
    )


def test_fixes_are_idempotent() -> None:
    """Applying a fix again changes nothing."""
    catalog: Catalog = _catalog()
    for source, key in (
        (
            """\
LIMIT = 3
""",
            "typing.add-final",
        ),
        (
            """\
def f(a, b): ...


f(1, 2)
""",
            "calls.add-keywords",
        ),
    ):
        once, _ = _fix_all(source=source, catalog=catalog, key=key)
        twice, _ = _fix_all(source=once, catalog=catalog, key=key)
        expect_equal(actual=twice, expected=once)


def test_validate_behavior_accepts_correct_examples() -> None:
    """Accept examples that trigger exactly their rule."""
    catalog: Catalog = _catalog(
        final_examples=(
            Example(
                source="""\
LIMIT = 3
""",
                triggers=True,
            ),
            Example(
                source="""\
limit = 3
""",
                triggers=False,
            ),
        ),
        keyword_examples=(
            Example(
                source="""\
def f(a): ...
f(1)
""",
                triggers=True,
            ),
            Example(
                source="""\
def f(a): ...
f(a=1)
""",
                triggers=False,
            ),
        ),
    )
    validate_behavior(catalog=catalog, registries=default_registries())


def test_validate_behavior_reports_wrong_example() -> None:
    """Report an example that does not trigger its rule."""
    catalog: Catalog = _catalog(
        final_examples=(
            Example(
                source="""\
limit = 3
""",
                triggers=True,
            ),
        ),
    )
    with pytest.raises(expected_exception=CatalogError) as raised:
        validate_behavior(catalog=catalog, registries=default_registries())
    expect_in(
        item="rule 'glob': example 1 should trigger",
        container=raised.value.problems[0],
    )


def test_validate_behavior_reports_non_idempotent_fix() -> None:
    """Report a fix that changes its own output again."""

    def growing(_subject: Subject, facts: ModuleFacts) -> None:
        """Append a statement so the fix never stabilises.

        Args:
            _subject (Subject): Unused subject.
            facts (ModuleFacts): Resolved imports and the parsed module.

        """
        facts.module.body.append(Pass())

    catalog: Catalog = _catalog(
        final_examples=(
            Example(
                source="""\
LIMIT = 3
""",
                triggers=True,
            ),
        ),
    )
    with pytest.raises(expected_exception=CatalogError) as raised:
        validate_behavior(
            catalog=catalog,
            registries=default_registries(),
            appliers={"typing.add-final": growing},
        )
    expect_in(
        item="fix 'typing.add-final' is not idempotent",
        container=raised.value.problems[0],
    )


def test_apply_fix_rejects_unknown_applier() -> None:
    """Name the missing applier."""
    catalog: Catalog = _catalog(final_fix=_final_fix(edits=("nope",)))
    result: CheckResult = check(
        source="""\
LIMIT = 3
""",
        filename="s.py",
        catalog=catalog,
        registries=default_registries(),
    )
    with pytest.raises(expected_exception=KeyError, match="nope"):
        apply_fix(
            source="""\
LIMIT = 3
""",
            finding=result.findings[0],
            fix=catalog.fix(key="typing.add-final"),
            registries=default_registries(),
        )
