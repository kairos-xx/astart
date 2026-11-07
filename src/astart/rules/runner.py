"""Fix runner: parse once, apply many fixes, write once."""

from __future__ import annotations

from ast import parse as ast_parse
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart import FormatPreservationError, parse, unparse
from astart.rules.appliers import Appliers
from astart.rules.engine import (
    CheckOptions,
    check,
    preconditions_hold,
    subject_index,
)
from astart.rules.facts import module_facts
from astart.rules.hints import HintCache
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from astart import CommentedModule
    from astart.rules.engine import CheckResult
    from astart.rules.facts import Applier, ModuleFacts, Subject
    from astart.rules.model import Catalog, Finding, Fix
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        safety_rank: Grouped module constant.
        allowed_ceilings: Grouped module constant.
        applier_errors: Grouped module constant.
        write_back_reason: Grouped module constant.

    """

    safety_rank: Final[dict[FixSafety, int]] = {
        FixSafety.proven: 0,
        FixSafety.guarded: 1,
        FixSafety.suggest: 2,
        FixSafety.none: 3,
    }
    allowed_ceilings: Final[frozenset[FixSafety]] = frozenset(
        {FixSafety.proven, FixSafety.guarded},
    )
    applier_errors: Final[tuple[type[Exception], ...]] = (
        AttributeError,
        IndexError,
        KeyError,
        SyntaxError,
        TypeError,
        ValueError,
    )
    write_back_reason: Final[str] = (
        "cannot write back without changing formatting"
    )


@final
@dataclass(frozen=True, slots=True)
class AppliedFix:
    """A fix that was applied.

    Attributes:
        fix_key: Fix that ran.
        rule_key: Rule whose finding it resolved.
        subject_path: Path of the subject it edited.

    """

    fix_key: str
    rule_key: str
    subject_path: str


@final
@dataclass(frozen=True, slots=True)
class SkippedFix:
    """A fix that was selected but not applied.

    Attributes:
        fix_key: Fix that was skipped.
        rule_key: Rule whose finding it would have resolved.
        subject_path: Path of the subject.
        reason: Why it was skipped.

    """

    fix_key: str
    rule_key: str
    subject_path: str
    reason: str


@final
@dataclass(frozen=True, slots=True)
class FixSettings:
    """Options of a fix run.

    Attributes:
        ceiling: Highest fix safety to apply (``proven`` or ``guarded``).
        stubs_path: Stub directory for type hints, or ``None``.
        max_rounds: Upper bound on repeat passes.
        appliers: Applier functions; ``None`` selects the built-in ones.

    """

    ceiling: FixSafety
    stubs_path: Path | None = None
    max_rounds: int = 3
    appliers: Mapping[str, Applier] | None = None


@final
@dataclass(frozen=True, slots=True)
class FixResult:
    """Outcome of fixing one source file.

    Attributes:
        source: The final source text.
        applied: Fixes that were applied.
        skipped: Fixes that were selected but not applied.
        remaining: Findings still present in the final source.
        parse_error: Why the source could not be analysed, if it could not.

    """

    source: str
    applied: tuple[AppliedFix, ...]
    skipped: tuple[SkippedFix, ...]
    remaining: tuple[Finding, ...]
    parse_error: str | None


@final
@dataclass(frozen=True, slots=True)
class _Pass:
    """Everything the fixes of one pass share.

    Attributes:
        index: Subjects of the module by path and position.
        facts: Resolved imports and lazily computed hints.
        table: Applier functions.
        edited: Identities of nodes already edited, extended in place.

    """

    index: dict[tuple[str, int, int], Subject]
    facts: ModuleFacts
    table: Mapping[str, Applier]
    edited: set[int]


@final
@dataclass(frozen=True, slots=True)
class _Job:
    """What stays fixed while one file is fixed.

    Attributes:
        filename: Name used for parsing and spans.
        catalog: Rules and fixes.
        registries: Declared vocabulary.
        settings: Safety ceiling and options.
        cache: Type-hint inference shared by every pass over the same text.

    """

    filename: str
    catalog: Catalog
    registries: Registries
    settings: FixSettings
    cache: HintCache


@final
@dataclass(frozen=True, slots=True)
class _Round:
    """Outcome of one pass.

    Attributes:
        source: Source after the pass.
        applied: Fixes applied in the pass.
        skipped: Fixes skipped in the pass.
        parse_error: Parse error, if any.
        findings: Findings of the pass's input text.

    """

    source: str
    applied: tuple[AppliedFix, ...]
    skipped: tuple[SkippedFix, ...]
    parse_error: str | None
    findings: tuple[Finding, ...] = ()


def fix_source(
    *,
    source: str,
    filename: str,
    catalog: Catalog,
    registries: Registries,
    settings: FixSettings,
) -> FixResult:
    """Apply every selected fix to a source file.

    The source is parsed once per pass, all fixes edit the same tree, and the
    tree is written back once. Failures are reported, never raised.

    Args:
        source: Python source text.
        filename: Name used for parsing and spans.
        catalog: Rules and fixes.
        registries: Declared vocabulary.
        settings: Safety ceiling and options.

    Returns:
        The final source, what was applied and skipped, and what remains.

    Raises:
        ValueError: If the ceiling is not ``proven`` or ``guarded``.

    """
    if settings.ceiling not in Constants.allowed_ceilings:
        msg: str = "ceiling must be FixSafety.proven or FixSafety.guarded"
        raise ValueError(msg)
    if settings.max_rounds < 1:
        msg = "max_rounds must be at least 1"
        raise ValueError(msg)
    job: _Job = _Job(
        filename=filename,
        catalog=catalog,
        registries=registries,
        settings=settings,
        cache=HintCache(),
    )
    current: str = source
    applied: list[AppliedFix] = []
    skipped: dict[tuple[str, str, str], SkippedFix] = {}
    parse_error: str | None = None
    settled: tuple[Finding, ...] | None = None
    for _round in range(settings.max_rounds):
        outcome: _Round = _run_round(source=current, job=job)
        if outcome.parse_error is not None:
            parse_error = outcome.parse_error
            settled = ()
            break
        applied.extend(outcome.applied)
        for item in outcome.skipped:
            skipped[item.fix_key, item.rule_key, item.subject_path] = item
        for done in outcome.applied:
            _ = skipped.pop(
                (done.fix_key, done.rule_key, done.subject_path),
                None,
            )
        stable: bool = not outcome.applied or outcome.source == current
        current = outcome.source
        if stable:
            settled = outcome.findings
            break
    if settled is None:
        final: CheckResult = check(
            source=current,
            filename=filename,
            catalog=catalog,
            registries=registries,
            options=_options(job=job),
        )
        settled = final.findings
        parse_error = parse_error or final.parse_error
    return FixResult(
        source=current,
        applied=tuple(applied),
        skipped=tuple(skipped.values()),
        remaining=settled,
        parse_error=parse_error,
    )


def _options(*, job: _Job) -> CheckOptions:
    """Build the check options of a job.

    Args:
        job: Fixed parameters of the run.

    Returns:
        Options carrying the stub directory and the shared hint cache.

    """
    return CheckOptions(
        stubs_path=job.settings.stubs_path,
        hint_cache=job.cache,
    )


def _fix_order(*, catalog: Catalog) -> dict[str, int]:
    """Rank fixes so that ``before`` and ``after`` relations hold.

    Args:
        catalog: Rules and fixes.

    Returns:
        A position for every fix key; ties are broken by key.

    """
    keys: list[str] = sorted(fix.key for fix in catalog.fixes)
    edges: dict[str, set[str]] = {key: set() for key in keys}
    for fix in catalog.fixes:
        for later in fix.before:
            if later in edges:
                edges[fix.key].add(later)
        for earlier in fix.after:
            if earlier in edges:
                edges[earlier].add(fix.key)
    waiting: dict[str, int] = dict.fromkeys(keys, 0)
    for targets in edges.values():
        for target in targets:
            waiting[target] += 1
    order: list[str] = []
    pending: list[str] = list(keys)
    while pending:
        ready: list[str] = [key for key in pending if waiting[key] == 0]
        chosen: str = ready[0] if ready else pending[0]
        pending.remove(chosen)
        order.append(chosen)
        for target in edges[chosen]:
            waiting[target] -= 1
    return {key: position for position, key in enumerate(iterable=order)}


def _eligible(
    *,
    findings: tuple[Finding, ...],
    catalog: Catalog,
    ceiling: FixSafety,
) -> list[tuple[Finding, Fix]]:
    """Select offers within the ceiling, in application order.

    Args:
        findings: Findings of the current source.
        catalog: Rules and fixes.
        ceiling: Highest fix safety to apply.

    Returns:
        (finding, fix) pairs ordered by fix relations, then position.

    """
    limit: int = Constants.safety_rank[ceiling]
    order: dict[str, int] = _fix_order(catalog=catalog)
    pairs: list[tuple[Finding, Fix]] = [
        (finding, catalog.fix(key=offer.fix_key))
        for finding in findings
        for offer in finding.fix_offers
        if Constants.safety_rank[offer.safety] <= limit
    ]
    pairs.sort(
        key=lambda pair: (
            order.get(pair[1].key, len(order)),
            pair[0].span.start_line,
            pair[0].span.start_column,
        ),
    )
    return pairs


def _run_round(*, source: str, job: _Job) -> _Round:
    """Run one pass: check, apply, write back, degrading if needed.

    Args:
        source: Current source text.
        job: Fixed parameters of the run.

    Returns:
        The pass outcome.

    """
    found: CheckResult = check(
        source=source,
        filename=job.filename,
        catalog=job.catalog,
        registries=job.registries,
        options=_options(job=job),
    )
    if found.parse_error is not None:
        return _Round(
            source=source,
            applied=(),
            skipped=(),
            parse_error=found.parse_error,
        )
    pairs: list[tuple[Finding, Fix]] = _eligible(
        findings=found.findings,
        catalog=job.catalog,
        ceiling=job.settings.ceiling,
    )
    outcome: _Round = _degrade(source=source, pairs=pairs, job=job)
    return replace(outcome, findings=found.findings)


def _attempt(
    *,
    source: str,
    pairs: list[tuple[Finding, Fix]],
    job: _Job,
) -> _Round | None:
    """Apply fixes to one fresh tree and write it back once.

    Args:
        source: Source the findings were computed on.
        pairs: Findings and the fixes to apply to them.
        job: Fixed parameters of the run.

    Returns:
        The outcome, or ``None`` when the tree cannot be written back.

    """
    module: CommentedModule = parse(source=source, filename=job.filename)
    settings: FixSettings = job.settings
    state: _Pass = _Pass(
        index=subject_index(module=module),
        facts=module_facts(
            module=module,
            stubs_path=settings.stubs_path,
            source=source,
            cache=job.cache,
        ),
        table=Appliers.table
        if settings.appliers is None
        else settings.appliers,
        edited=set(),
    )
    applied: list[AppliedFix] = []
    skipped: list[SkippedFix] = []
    for finding, fix in pairs:
        reason: str | None = _apply_one(finding=finding, fix=fix, state=state)
        if reason is None:
            applied.append(
                AppliedFix(
                    fix_key=fix.key,
                    rule_key=finding.rule_key,
                    subject_path=finding.subject_path,
                ),
            )
        else:
            skipped.append(
                SkippedFix(
                    fix_key=fix.key,
                    rule_key=finding.rule_key,
                    subject_path=finding.subject_path,
                    reason=reason,
                ),
            )
    if not applied:
        return _Round(
            source=source,
            applied=(),
            skipped=tuple(skipped),
            parse_error=None,
        )
    try:
        text: str = unparse(tree=module, preserve_formatting=True)
        _ = ast_parse(source=text)
    except (FormatPreservationError, SyntaxError):
        return None
    return _Round(
        source=text,
        applied=tuple(applied),
        skipped=tuple(skipped),
        parse_error=None,
    )


def _degrade(
    *,
    source: str,
    pairs: list[tuple[Finding, Fix]],
    job: _Job,
) -> _Round:
    """Apply as many fixes as can be written back, by halving.

    Tries all fixes at once. When the combined write-back fails, the first
    half is applied on its own, the second half is re-matched against the
    resulting text by fingerprint, and the process recurses. A single fix that
    cannot be written back is skipped.

    Args:
        source: Source the findings were computed on.
        pairs: Findings and the fixes to apply to them.
        job: Fixed parameters of the run.

    Returns:
        The combined outcome.

    """
    if not pairs:
        return _Round(source=source, applied=(), skipped=(), parse_error=None)
    attempt: _Round | None = _attempt(source=source, pairs=pairs, job=job)
    if attempt is not None:
        return attempt
    if len(pairs) == 1:
        finding, fix = pairs[0]
        return _Round(
            source=source,
            applied=(),
            skipped=(
                SkippedFix(
                    fix_key=fix.key,
                    rule_key=finding.rule_key,
                    subject_path=finding.subject_path,
                    reason=Constants.write_back_reason,
                ),
            ),
            parse_error=None,
        )
    middle: int = len(pairs) // 2
    first: _Round = _degrade(source=source, pairs=pairs[:middle], job=job)
    rest: list[tuple[Finding, Fix]] = _rematch(
        previous=source,
        current=first.source,
        pairs=pairs[middle:],
        job=job,
    )
    second: _Round = _degrade(source=first.source, pairs=rest, job=job)
    return _Round(
        source=second.source,
        applied=(*first.applied, *second.applied),
        skipped=(*first.skipped, *second.skipped),
        parse_error=None,
    )


def _rematch(
    *,
    previous: str,
    current: str,
    pairs: list[tuple[Finding, Fix]],
    job: _Job,
) -> list[tuple[Finding, Fix]]:
    """Re-locate findings in edited text through their fingerprints.

    Args:
        previous: Source the pairs were computed on.
        current: Source after earlier fixes.
        pairs: Findings and fixes to carry over.
        job: Fixed parameters of the run.

    Returns:
        Pairs valid for ``current``; findings an earlier fix resolved, or
        that no longer offer the fix, are dropped.

    """
    if current == previous:
        return pairs
    found: CheckResult = check(
        source=current,
        filename=job.filename,
        catalog=job.catalog,
        registries=job.registries,
        options=_options(job=job),
    )
    by_print: dict[str, Finding] = {f.fingerprint: f for f in found.findings}
    carried: list[tuple[Finding, Fix]] = []
    for finding, fix in pairs:
        match: Finding | None = by_print.get(finding.fingerprint)
        if match is not None and any(
            offer.fix_key == fix.key for offer in match.fix_offers
        ):
            carried.append((match, fix))
    return carried


def _apply_one(*, finding: Finding, fix: Fix, state: _Pass) -> str | None:
    """Apply one fix to one finding's subject.

    Args:
        finding: Finding being fixed.
        fix: Fix to apply.
        state: Shared state of the pass.

    Returns:
        ``None`` when applied, otherwise the reason it was skipped.

    """
    subject: Subject | None = state.index.get(
        (
            finding.subject_path,
            finding.span.start_line,
            finding.span.start_column,
        ),
    )
    if subject is None:
        return "subject not found"
    if id(subject.node) in state.edited:
        return "conflict"
    if not preconditions_hold(fix=fix, subject=subject, facts=state.facts):
        return "preconditions no longer hold"
    try:
        for key in fix.edits:
            applier: Applier = state.table[key]
            applier(subject, state.facts)
    except Constants.applier_errors as error:
        return f"applier failed: {error}"
    state.edited.add(id(subject.node))
    return None
