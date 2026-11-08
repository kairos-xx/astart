"""Fix runner: parse once, apply many fixes, write once."""

from __future__ import annotations

from ast import parse as ast_parse
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart import FormatPreservationError, parse, unparse
from astart.rules.appliers import Appliers
from astart.rules.docs_fixes import stub_missing_docstrings
from astart.rules.engine import (
    CheckOptions,
    check,
    preconditions_hold,
    subject_index,
)
from astart.rules.facts import FactsOptions, module_facts
from astart.rules.hints import HintCache
from astart.rules.reasons import SkipCode
from astart.rules.vocabulary import FixSafety
from astart.rules.whitespace_rules import (
    collapse_blank_lines,
    strip_trailing_space,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from astart import CommentedModule
    from astart.project.libraries import LibraryIndex
    from astart.project.versions import PythonTarget
    from astart.rules.checker import Checker
    from astart.rules.engine import CheckResult
    from astart.rules.facts import Applier, ModuleFacts, Subject
    from astart.rules.model import Catalog, Finding, Fix
    from astart.rules.project_bridge import ProjectView
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        safety_rank: Grouped module constant.
        allowed_ceilings: Grouped module constant.
        applier_errors: Grouped module constant.
        checker_reason: Why the external checker rejected a fix.
        write_back_reason: Grouped module constant.
        no_op_reason: Why a text fix found nothing safe to edit.
        docstring_prefix: Prefix of fix keys that rewrite only a docstring
            and so never conflict with edits to the same definition.

    """

    docstring_prefix: Final[str] = "docs."

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
    checker_reason: Final[str] = "the type checker reported a new error"
    write_back_reason: Final[str] = (
        "cannot write back without changing formatting"
    )
    no_op_reason: Final[str] = "no editable violations remain"


_TEXT_FIXES: Final[Mapping[str, Callable[[str], str]]] = {
    "whitespace.collapse-blank-lines": lambda source: collapse_blank_lines(
        source=source,
    ),
    "whitespace.strip-trailing-space": lambda source: strip_trailing_space(
        source=source,
    ),
}


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
        reason: Why it was skipped, with detail.
        code: Closed classification of the reason.

    """

    fix_key: str
    rule_key: str
    subject_path: str
    reason: str
    code: SkipCode


@final
@dataclass(frozen=True, slots=True)
class FixSettings:
    """Options of a fix run.

    Attributes:
        ceiling: Highest fix safety to apply (``proven`` or ``guarded``).
        stubs_path: Stub directory for type hints, or ``None``.
        max_rounds: Upper bound on repeat passes.
        appliers: Applier functions; ``None`` selects the built-in ones.
        create_constants: Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        stub_docstrings: Whether undocumented public definitions get a stub
            docstring.
        annotate_variables: Whether function-local variables get a type
            annotation.
        negotiate: Whether negotiated annotations supplement the hint
            index.
        engine: Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        min_confidence: Offers below this confidence are not applied, on top
            of each fix's own minimum.
        checker: External type checker that must not object to guarded
            fixes, or ``None`` to apply them on astart's evidence alone.
        project: Cross-module view of the project, or ``None`` for
            single-module analysis.
        libraries: External signature index for callees outside the
            project, or ``None``.
        target: Oldest Python version emitted code must run on, or
            ``None`` for the running interpreter.
        excluded_prefixes: Fix-key prefixes that are never applied, so a
            run can leave whole fix families (such as ``docs.``) off.

    """

    ceiling: FixSafety
    stubs_path: Path | None = None
    max_rounds: int = 3
    appliers: Mapping[str, Applier] | None = None
    create_constants: bool = False
    stub_docstrings: bool = False
    annotate_variables: bool = False
    negotiate: bool = True
    engine: bool = False
    min_confidence: float = 0.0
    checker: Checker | None = None
    project: ProjectView | None = None
    libraries: LibraryIndex | None = None
    target: PythonTarget | None = None
    excluded_prefixes: tuple[str, ...] = ()


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
        rounds: How many passes ran, including the final one that found
            nothing left to do.

    """

    source: str
    applied: tuple[AppliedFix, ...]
    skipped: tuple[SkippedFix, ...]
    remaining: tuple[Finding, ...]
    parse_error: str | None
    rounds: int = 0


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
    current: str = (
        stub_missing_docstrings(source=source)
        if settings.stub_docstrings
        else source
    )
    applied: list[AppliedFix] = []
    skipped: dict[tuple[str, str, str], SkippedFix] = {}
    parse_error: str | None = None
    settled: tuple[Finding, ...] | None = None
    rounds: int = 0
    for _round in range(settings.max_rounds):
        rounds += 1
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
        rounds=rounds,
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
        create_constants=job.settings.create_constants,
        stub_docstrings=job.settings.stub_docstrings,
        annotate_variables=job.settings.annotate_variables,
        negotiate=job.settings.negotiate,
        engine=job.settings.engine,
        project=job.settings.project,
        libraries=job.settings.libraries,
        target=job.settings.target,
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
    minimum: float,
    excluded: tuple[str, ...] = (),
) -> list[tuple[Finding, Fix]]:
    """Select offers within the ceiling, in application order.

    Args:
        findings: Findings of the current source.
        catalog: Rules and fixes.
        ceiling: Highest fix safety to apply.
        minimum: Offers with less confidence than this are left out, as are
            offers below their own fix's ``min_confidence``.
        excluded: Fix-key prefixes that are never applied.

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
        and offer.confidence
        >= max(minimum, catalog.fix(key=offer.fix_key).min_confidence)
        and not offer.fix_key.startswith(excluded)
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
        minimum=job.settings.min_confidence,
        excluded=job.settings.excluded_prefixes,
    )
    outcome: _Round = _degrade(source=source, pairs=pairs, job=job)
    return replace(outcome, findings=found.findings)


def _attempt(
    *,
    source: str,
    pairs: list[tuple[Finding, Fix]],
    job: _Job,
) -> _Round | SkipCode:
    """Apply fixes to one fresh tree and write it back once.

    Args:
        source: Source the findings were computed on.
        pairs: Findings and the fixes to apply to them.
        job: Fixed parameters of the run.

    Returns:
        The outcome, or the code saying why the tree was not accepted: it
        cannot be written back, or the external checker rejected it.

    """
    text_pairs: list[tuple[Finding, Fix]] = [
        pair for pair in pairs if pair[1].key in _TEXT_FIXES
    ]
    ast_pairs: list[tuple[Finding, Fix]] = [
        pair for pair in pairs if pair[1].key not in _TEXT_FIXES
    ]
    applied: list[AppliedFix] = []
    skipped: list[SkippedFix] = []
    edited: str = source
    seen: set[str] = set()
    for finding, fix in text_pairs:
        if fix.key in seen:
            continue
        seen.add(fix.key)
        update: Callable[[str], str] = _TEXT_FIXES[fix.key]
        updated: str = update(edited)
        if updated == edited:
            skipped.append(
                SkippedFix(
                    fix_key=fix.key,
                    rule_key=finding.rule_key,
                    subject_path=finding.subject_path,
                    reason=Constants.no_op_reason,
                    code=SkipCode.preconditions_changed,
                ),
            )
            continue
        edited = updated
        applied.append(
            AppliedFix(
                fix_key=fix.key,
                rule_key=finding.rule_key,
                subject_path=finding.subject_path,
            ),
        )
    module: CommentedModule = parse(source=edited, filename=job.filename)
    settings: FixSettings = job.settings
    state: _Pass = _Pass(
        index=subject_index(module=module),
        facts=module_facts(
            module=module,
            options=FactsOptions(
                stubs_path=settings.stubs_path,
                source=edited,
                cache=job.cache,
                create_constants=settings.create_constants,
                stub_docstrings=settings.stub_docstrings,
                annotate_variables=settings.annotate_variables,
                negotiate=settings.negotiate,
                engine=settings.engine,
                project=settings.project,
                libraries=settings.libraries,
                target=settings.target,
            ),
        ),
        table=Appliers.table
        if settings.appliers is None
        else settings.appliers,
        edited=set(),
    )
    for finding, fix in ast_pairs:
        refusal: tuple[SkipCode, str] | None = _apply_one(
            finding=finding,
            fix=fix,
            state=state,
        )
        if refusal is None:
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
                    reason=refusal[1],
                    code=refusal[0],
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
        return SkipCode.write_back
    checker: Checker | None = settings.checker
    guarded: bool = any(
        job.catalog.fix(key=item.fix_key).safety is FixSafety.guarded
        for item in applied
    )
    if (
        checker is not None
        and guarded
        and checker.regresses(
            filename=job.filename,
            before=source,
            after=text,
        )
    ):
        return SkipCode.checker_rejected
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
    attempt: _Round | SkipCode = _attempt(source=source, pairs=pairs, job=job)
    if isinstance(attempt, _Round):
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
                    reason=Constants.checker_reason
                    if attempt is SkipCode.checker_rejected
                    else Constants.write_back_reason,
                    code=attempt,
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


def _apply_one(
    *,
    finding: Finding,
    fix: Fix,
    state: _Pass,
) -> tuple[SkipCode, str] | None:
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
        return SkipCode.subject_missing, "subject not found"
    independent: bool = fix.key.startswith(Constants.docstring_prefix)
    if not independent and id(subject.node) in state.edited:
        return SkipCode.conflict, "conflict"
    if not preconditions_hold(fix=fix, subject=subject, facts=state.facts):
        return SkipCode.preconditions_changed, "preconditions no longer hold"
    try:
        for key in fix.edits:
            applier: Applier = state.table[key]
            applier(subject, state.facts)
    except Constants.applier_errors as error:
        return SkipCode.applier_failed, f"applier failed: {error}"
    if not independent:
        state.edited.add(id(subject.node))
    return None
