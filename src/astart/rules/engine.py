"""Reference engine: parse once, evaluate rules, report findings."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart import FormatPreservationError, parse, unparse
from astart.rules.appliers import Appliers
from astart.rules.catalog import CatalogError, validate_catalog
from astart.rules.facts import (
    Constants,
    Registry,
    collect_subjects,
    module_facts,
)
from astart.rules.model import Finding, FixOffer, Span, make_fingerprint
from astart.rules.predicate import FactValue, evaluate, predicate_facts
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from astart import CommentedModule as Module
    from astart.rules.facts import (
        Applier,
        FactProvider,
        ModuleFacts,
        Subject,
    )
    from astart.rules.hints import HintCache
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.model import Catalog, Fix, Rule
    from astart.rules.registry import Registries


@final
@dataclass(frozen=True, slots=True)
class CheckResult:
    """Outcome of checking one source file.

    Attributes:
        findings: Findings in source order.
        parse_error: Why the source could not be analysed (a syntax error
            or a parser limit), or ``None`` when it was.

    """

    findings: tuple[Finding, ...]
    parse_error: str | None


@final
@dataclass(frozen=True, slots=True)
class CheckOptions:
    """Optional seams of :func:`check`.

    Attributes:
        providers: Fact providers; ``None`` selects the built-in ones.
        stubs_path: Stub directory for type hints, or ``None`` for an empty
            temporary one.
        hint_cache: Cache shared between runs on the same text, or ``None``.

    """

    providers: Mapping[str, FactProvider] | None = None
    stubs_path: Path | None = None
    hint_cache: HintCache | None = None


@final
@dataclass(frozen=True, slots=True)
class _Context:
    """Everything shared by the evaluation of one source file.

    Attributes:
        filename: Name used in finding spans.
        catalog: Catalog holding rules and fixes.
        table: Fact providers.
        facts: Resolved imports.

    """

    filename: str
    catalog: Catalog
    table: Mapping[str, FactProvider]
    facts: ModuleFacts


def check(
    *,
    source: str,
    filename: str,
    catalog: Catalog,
    registries: Registries,
    options: CheckOptions | None = None,
) -> CheckResult:
    """Check one source file against every rule of a catalog.

    The source is parsed once. Only the facts that the rules' predicates
    read are computed.

    Args:
        source: Python source text.
        filename: Name used in finding spans.
        catalog: Rules to apply.
        registries: Declared vocabulary; every fact a rule reads must be
            declared in it.
        options: Optional fact providers and stub directory.

    Returns:
        Findings, or the parse error when the source is invalid.

    """
    for rule in catalog.rules:
        if rule.when is not None:
            for name in predicate_facts(predicate=rule.when):
                _ = registries.fact(name=name)
    chosen: CheckOptions = options or CheckOptions()
    try:
        module = parse(source=source, filename=filename)
        context: _Context = _Context(
            filename=filename,
            catalog=catalog,
            table=(
                Registry.providers
                if chosen.providers is None
                else chosen.providers
            ),
            facts=module_facts(
                module=module,
                stubs_path=chosen.stubs_path,
                source=source,
                cache=chosen.hint_cache,
            ),
        )
        findings = _evaluate(
            module=module,
            catalog=catalog,
            context=context,
        )
    except (SyntaxError, RecursionError, MemoryError, ValueError) as error:
        return CheckResult(findings=(), parse_error=str(object=error))
    return CheckResult(findings=findings, parse_error=None)


def _evaluate(
    *,
    module: Module,
    catalog: Catalog,
    context: _Context,
) -> tuple[Finding, ...]:
    """Evaluate every rule against a parsed module.

    Args:
        module: Parsed module.
        catalog: Rules to apply.
        context: Shared evaluation context.

    Returns:
        Findings in source order.

    """
    findings: list[Finding] = []
    for rule in catalog.rules:
        wanted: frozenset[str] = frozenset(rule.subject)
        for subject in collect_subjects(module=module, kinds=wanted):
            values: dict[str, FactValue] = {}
            if subject.kind in wanted and _holds(
                rule=rule,
                subject=subject,
                values=values,
                context=context,
            ):
                findings.append(
                    _finding(
                        rule=rule,
                        subject=subject,
                        values=values,
                        context=context,
                    ),
                )
    findings.sort(
        key=lambda item: (item.span.start_line, item.span.start_column),
    )
    return tuple(findings)


def _compute(
    *,
    names: frozenset[str],
    subject: Subject,
    values: dict[str, FactValue],
    context: _Context,
) -> None:
    """Compute the named facts that are not cached yet.

    Args:
        names: Fact names needed.
        subject: Subject under test.
        values: Cache of fact values, filled in place.
        context: Shared evaluation context.

    """
    for name in sorted(names):
        if name not in values:
            values[name] = context.table[name](subject, context.facts)


def _holds(
    *,
    rule: Rule,
    subject: Subject,
    values: dict[str, FactValue],
    context: _Context,
) -> bool:
    """Evaluate a rule's trigger for one subject.

    Args:
        rule: Rule under test.
        subject: Subject under test.
        values: Cache of computed fact values, filled in place.
        context: Shared evaluation context.

    Returns:
        Whether the declarative trigger holds.

    """
    if rule.when is None:
        return False
    _compute(
        names=predicate_facts(predicate=rule.when),
        subject=subject,
        values=values,
        context=context,
    )
    return evaluate(predicate=rule.when, facts=values)


def _span(*, subject: Subject, filename: str) -> Span:
    """Locate a subject in the source.

    Args:
        subject: Subject being reported.
        filename: Name used in the span.

    Returns:
        The span of the subject's node.

    """
    node = subject.node
    line: int = getattr(node, "lineno", 1)
    return Span(
        file=filename,
        start_line=line,
        start_column=getattr(node, "col_offset", 0),
        end_line=getattr(node, "end_lineno", None) or line,
        end_column=getattr(node, "end_col_offset", None) or 0,
    )


def _finding(
    *,
    rule: Rule,
    subject: Subject,
    values: dict[str, FactValue],
    context: _Context,
) -> Finding:
    """Build the finding for a firing rule.

    Args:
        rule: Rule that fired.
        subject: Subject it fired on.
        values: Fact values already computed for the subject.
        context: Shared evaluation context.

    Returns:
        The finding.

    """
    evidence: dict[str, JsonValue] = {
        slot.name: Registry.evidence[slot.name](subject, context.facts)
        for slot in rule.evidence
    }
    offers: tuple[FixOffer, ...] = tuple(
        FixOffer(fix_key=fix.key, safety=fix.safety, confidence=1.0)
        for fix in (context.catalog.fix(key=key) for key in rule.fixes)
        if _applicable(
            fix=fix,
            subject=subject,
            values=values,
            context=context,
        )
    )
    return Finding(
        rule_key=rule.key,
        severity=rule.severity,
        span=_span(subject=subject, filename=context.filename),
        subject_path=subject.path,
        evidence=evidence,
        fix_offers=offers,
        fingerprint=make_fingerprint(
            rule_key=rule.key,
            subject_path=subject.path,
            evidence=evidence,
        ),
    )


def _applicable(
    *,
    fix: Fix,
    subject: Subject,
    values: dict[str, FactValue],
    context: _Context,
) -> bool:
    """Decide whether a fix's preconditions hold for a subject.

    Args:
        fix: Candidate fix.
        subject: Subject of the finding.
        values: Fact values already computed, extended in place.
        context: Shared evaluation context.

    Returns:
        Whether the fix can be offered.

    """
    if fix.safety is FixSafety.none:
        return False
    if fix.preconditions is None:
        return True
    _compute(
        names=predicate_facts(predicate=fix.preconditions),
        subject=subject,
        values=values,
        context=context,
    )
    return evaluate(predicate=fix.preconditions, facts=values)


def subject_index(*, module: Module) -> dict[tuple[str, int, int], Subject]:
    """Index every subject of a module by path and start position.

    Args:
        module: Parsed module.

    Returns:
        Subjects keyed by (path, start line, start column).

    """
    index: dict[tuple[str, int, int], Subject] = {}
    for subject in collect_subjects(module=module, kinds=Constants.node_kinds):
        span: Span = _span(subject=subject, filename="")
        index.setdefault(
            (subject.path, span.start_line, span.start_column),
            subject,
        )
    return index


def locate_subject(*, module: Module, finding: Finding) -> Subject | None:
    """Find the subject a finding was reported on.

    Args:
        module: Parsed module.
        finding: Finding to locate.

    Returns:
        The subject, or ``None`` when the source no longer matches.

    """
    return subject_index(module=module).get(
        (
            finding.subject_path,
            finding.span.start_line,
            finding.span.start_column,
        ),
    )


def preconditions_hold(
    *,
    fix: Fix,
    subject: Subject,
    facts: ModuleFacts,
) -> bool:
    """Evaluate a fix's preconditions on the current tree.

    Args:
        fix: Candidate fix.
        subject: Subject of the finding.
        facts: Resolved imports and lazily computed hints.

    Returns:
        Whether the fix may be applied.

    """
    if fix.preconditions is None:
        return True
    values: dict[str, FactValue] = {
        name: Registry.providers[name](subject, facts)
        for name in predicate_facts(predicate=fix.preconditions)
    }
    return evaluate(predicate=fix.preconditions, facts=values)


def apply_fix(
    *,
    source: str,
    finding: Finding,
    fix: Fix,
    registries: Registries,
    appliers: Mapping[str, Applier] | None = None,
) -> str:
    """Apply a fix to the subject of a finding.

    Args:
        source: Python source the finding was reported on.
        finding: Finding to fix; its span names the file.
        fix: Fix to apply.
        registries: Declared appliers.
        appliers: Applier functions; defaults to the built-in ones.

    Returns:
        The new source, or the original when the subject is gone, the
        fix's preconditions no longer hold, or the edit cannot be written
        back without changing the surrounding formatting or comments.

    Raises:
        KeyError: If an applier of the fix is not registered.

    """
    table: Mapping[str, Applier] = (
        Appliers.table if appliers is None else appliers
    )
    for key in fix.edits:
        if key not in registries.appliers or key not in table:
            msg: str = f"applier {key!r} is not registered"
            raise KeyError(msg)
    module = parse(source=source, filename=finding.span.file)
    facts: ModuleFacts = module_facts(module=module)
    subject: Subject | None = locate_subject(module=module, finding=finding)
    if subject is None or not preconditions_hold(
        fix=fix,
        subject=subject,
        facts=facts,
    ):
        return source
    for key in fix.edits:
        table[key](subject, facts)
    try:
        result: str = unparse(tree=module, preserve_formatting=True)
        _ = ast.parse(source=result)
    except (FormatPreservationError, SyntaxError):
        return source
    return result


def validate_behavior(
    *,
    catalog: Catalog,
    registries: Registries,
    appliers: Mapping[str, Applier] | None = None,
) -> None:
    """Check the behavioural invariants against the examples.

    Every example that triggers must produce exactly one finding, for its
    own rule; every example that does not trigger must produce none for its
    rule; and every fix offered on a triggering example must be idempotent.

    Args:
        catalog: Catalog to check.
        registries: Declared vocabulary.
        appliers: Applier functions; defaults to the built-in ones.

    Raises:
        CatalogError: With every problem found.

    """
    problems: list[str] = []
    for rule in catalog.rules:
        for index, example in enumerate(iterable=rule.examples, start=1):
            result: CheckResult = check(
                source=example.source,
                filename="example.py",
                catalog=catalog,
                registries=registries,
            )
            own: list[Finding] = [
                f for f in result.findings if f.rule_key == rule.key
            ]
            if not example.triggers:
                if own:
                    problems.append(
                        f"rule {rule.key!r}: example {index} should not "
                        "trigger",
                    )
                continue
            if len(own) != 1 or len(result.findings) != 1:
                reported: list[str] = sorted(
                    f.rule_key for f in result.findings
                )
                problems.append(
                    f"rule {rule.key!r}: example {index} should trigger "
                    f"exactly this rule once, got {reported}",
                )
                continue
            problems.extend(
                _idempotence_problems(
                    label=f"example {index} of rule {rule.key!r}",
                    source=example.source,
                    finding=own[0],
                    env=_Env(
                        catalog=catalog,
                        registries=registries,
                        appliers=appliers,
                    ),
                ),
            )
    if problems:
        raise CatalogError(problems=tuple(problems))


@final
@dataclass(frozen=True, slots=True)
class _Env:
    """Catalog and registries shared by the behavioural checks.

    Attributes:
        catalog: Catalog holding rules and fixes.
        registries: Declared vocabulary.
        appliers: Applier functions, or ``None`` for the built-in ones.

    """

    catalog: Catalog
    registries: Registries
    appliers: Mapping[str, Applier] | None


def _idempotence_problems(
    *,
    label: str,
    source: str,
    finding: Finding,
    env: _Env,
) -> list[str]:
    """Check that every offered fix converges after one application.

    Args:
        label: Description of the example, used in messages.
        source: Example source.
        finding: The example's finding.
        env: Catalog, registries and appliers.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    for offer in finding.fix_offers:
        fix: Fix = env.catalog.fix(key=offer.fix_key)
        once: str = apply_fix(
            source=source,
            finding=finding,
            fix=fix,
            registries=env.registries,
            appliers=env.appliers,
        )
        twice: str = apply_fix(
            source=once,
            finding=finding,
            fix=fix,
            registries=env.registries,
            appliers=env.appliers,
        )
        if twice != once:
            problems.append(
                f"fix {fix.key!r} is not idempotent on {label}",
            )
    return problems


def verify_catalog(
    *,
    catalog: Catalog,
    registries: Registries,
    appliers: Mapping[str, Applier] | None = None,
) -> None:
    """Run every catalog invariant: data checks, then behavioural checks.

    The data invariants need only the registries; the behavioural ones need
    the engine, so this is the single entry point that enforces all eight.

    Args:
        catalog: Catalog to verify.
        registries: Declared vocabulary.
        appliers: Applier functions; defaults to the built-in ones.

    Raises:
        CatalogError: With every problem found.

    """
    validate_catalog(catalog=catalog, registries=registries)
    validate_behavior(
        catalog=catalog,
        registries=registries,
        appliers=appliers,
    )
