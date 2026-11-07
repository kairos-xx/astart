"""Verify the reference engine and the syntactic and scope facts."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart.rules.engine import CheckOptions, CheckResult, check
from astart.rules.facts import FactProvider, Subject, default_registries
from astart.rules.model import Catalog, Rule
from astart.rules.predicate import AllOf, Compare, CompareOp, Not
from astart.rules.vocabulary import Domain, Maturity, Owner, Severity

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_is,
    expect_not_equal,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart.rules.facts import ModuleFacts
    from astart.rules.predicate import FactValue
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        any_fact: Grouped module constant.
        global_facts: Grouped module constant.

    """

    any_fact: Final[str] = "annotation.uses_typing_any"
    global_facts: Final[tuple[str, ...]] = (
        "binding.is_module_global",
        "binding.name_is_uppercase",
        "binding.is_final",
    )


def _rule(
    *,
    key: str,
    subject: str,
    facts: tuple[str, ...],
    negate: tuple[str, ...] = (),
) -> Rule:
    """Build a rule that fires when every fact holds and negations do not.

    Args:
        key: Rule key, also used to derive the code.
        subject: Node kind to inspect.
        facts: Facts that must be true.
        negate: Facts that must be false.

    Returns:
        The rule.

    """
    items = tuple(
        Compare(fact=name, op=CompareOp.eq, value=True) for name in facts
    ) + tuple(
        Not(item=Compare(fact=name, op=CompareOp.eq, value=True))
        for name in negate
    )
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
        when=AllOf(items=items),
        requires=tuple(sorted({*facts, *negate})),
    )


def _catalog(*, rules: tuple[Rule, ...]) -> Catalog:
    """Wrap rules in a catalog.

    Args:
        rules: Rules to include.

    Returns:
        The catalog.

    """
    return Catalog(rules=rules, fixes=(), profiles=(), relations=())


def _any_rule() -> Rule:
    """Build the typing.Any rule used by several tests.

    Returns:
        The rule.

    """
    return _rule(key="any", subject="Annotation", facts=(Constants.any_fact,))


def _global_rule() -> Rule:
    """Build the uppercase-global rule used by several tests.

    Returns:
        The rule.

    """
    return _rule(
        key="glob",
        subject="Assign",
        facts=("binding.is_module_global", "binding.name_is_uppercase"),
        negate=("binding.is_final",),
    )


def _run(*, source: str, rules: tuple[Rule, ...]) -> CheckResult:
    """Run the engine on a snippet.

    Args:
        source: Python source.
        rules: Rules to apply.

    Returns:
        The check result.

    """
    return check(
        source=dedent(text=source),
        filename="sample.py",
        catalog=_catalog(rules=rules),
        registries=default_registries(),
    )


def test_unparsable_source_returns_parse_error() -> None:
    """Report a syntax error instead of raising."""
    result: CheckResult = _run(
        source="""\
def (:
""",
        rules=(_any_rule(),),
    )
    expect_not_none(value=result.parse_error)
    expect_equal(actual=result.findings, expected=())


def test_finding_span_and_subject_path() -> None:
    """Locate the finding and name its subject."""
    result: CheckResult = _run(
        source="""\
        from typing import Any


        class K:
            def run(self, value: Any) -> None:
                return None
        """,
        rules=(_any_rule(),),
    )
    expect_is(actual=result.parse_error, expected=None)
    expect_equal(actual=len(result.findings), expected=1)
    finding = result.findings[0]
    expect_equal(actual=finding.rule_key, expected="any")
    expect_equal(actual=finding.subject_path, expected="K.run.value")
    expect_equal(actual=finding.span.start_line, expected=5)
    expect_equal(actual=finding.span.start_column, expected=25)
    expect_equal(actual=finding.span.file, expected="sample.py")
    expect_equal(actual=dict(finding.evidence), expected={})


def test_only_required_facts_are_computed() -> None:
    """Never call a provider the enabled rules do not read."""
    calls: list[str] = []
    registries: Registries = default_registries()

    def counting(name: str) -> FactProvider:
        def provider(_subject: Subject, _facts: ModuleFacts) -> FactValue:
            calls.append(name)
            return False

        return provider

    providers = {name: counting(name=name) for name in registries.facts}
    check(
        source="""\
x: int = 1
""",
        filename="sample.py",
        catalog=_catalog(rules=(_any_rule(),)),
        registries=registries,
        options=CheckOptions(providers=providers),
    )
    expect_equal(actual=set(calls), expected={Constants.any_fact})


def test_fingerprint_survives_leading_blank_lines() -> None:
    """Keep a finding's identity when code moves."""
    body = """\
from typing import Any
x: Any = 1
"""
    first = _run(source=body, rules=(_any_rule(),)).findings[0]
    moved = _run(
        source="""\



"""
        + body,
        rules=(_any_rule(),),
    ).findings[0]
    expect_not_equal(
        actual=first.span.start_line,
        unexpected=moved.span.start_line,
    )
    expect_equal(actual=first.fingerprint, expected=moved.fingerprint)


def test_typing_any_detected_through_aliases() -> None:
    """Resolve Any through module aliases and import aliases."""
    result: CheckResult = _run(
        source="""\
        import typing as t
        from typing import Any as A
        from typing import Any

        a: t.Any = 1
        b: A = 1
        c: Any = 1
        d: list[Any] = []
        e: int = 1
        """,
        rules=(_any_rule(),),
    )
    expect_equal(
        actual=[f.subject_path for f in result.findings],
        expected=["a", "b", "c", "d"],
    )


def test_uppercase_global_without_final_detected() -> None:
    """Flag LIMIT but not lowercase names or non-module scopes."""
    result: CheckResult = _run(
        source="""\
        LIMIT = 3
        lower = 4


        class K:
            INNER = 5


        def f() -> None:
            LOCAL = 6
        """,
        rules=(_global_rule(),),
    )
    expect_equal(
        actual=[f.subject_path for f in result.findings],
        expected=["LIMIT"],
    )


def test_final_annotated_global_is_ignored() -> None:
    """Accept Final under every spelling."""
    result: CheckResult = _run(
        source="""\
        import typing as t
        from typing import Final as F
        from typing import Final

        A: Final[int] = 1
        B: F = 2
        C: t.Final[int] = 3
        D: int = 4
        """,
        rules=(_global_rule(),),
    )
    expect_equal(
        actual=[f.subject_path for f in result.findings],
        expected=["D"],
    )
    expect_false(condition=any(f.rule_key != "glob" for f in result.findings))
    expect_true(condition=True)
