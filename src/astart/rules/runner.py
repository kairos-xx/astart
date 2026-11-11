"""Fix runner: parse once, apply many fixes, write once."""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, walk
from ast import parse as ast_parse
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart.docstrings.core import Constants as DocstringConstants
from astart.docstrings.fixes import stub_missing_docstrings
from astart.rules.appliers import Appliers
from astart.rules.ddmin import ddmin
from astart.rules.engine import (
    CheckOptions,
    check,
    preconditions_hold,
    subject_index,
)
from astart.rules.facts import FactsOptions, module_facts
from astart.rules.hints import HintCache
from astart.rules.reasons import SkipCode
from astart.rules.strings_normalize import normalize_strings
from astart.rules.vocabulary import FixSafety
from astart.rules.whitespace_rules import (
    collapse_blank_lines,
    strip_trailing_space,
)
from astart.source.api import parse, unparse
from astart.source.formatting import FormatPreservationError
from astart.transforms.aliases import AliasOptimizer

type ListTupleFindingFix = list[tuple[Finding, Fix]]

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
        safety_rank (Final[dict[FixSafety, int]]): Grouped module constant.
        allowed_ceilings (Final[frozenset[FixSafety]]): Grouped module
            constant.
        applier_errors (Final[tuple[type[Exception], ...]]): Grouped module
            constant.
        checker_reason (Final[str]): Why the external checker rejected a fix.
        write_back_reason (Final[str]): Grouped module constant.
        no_op_reason (Final[str]): Why a text fix found nothing safe to edit.
        docstring_prefix (Final[str]): Prefix of fix keys that rewrite only a
            docstring and
            so never conflict with edits to the same definition.
        text_fixes (Final[Mapping[str, Callable[[str], str]]]): Grouped module
            constant.

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

    text_fixes: Final[Mapping[str, Callable[[str], str]]] = {
        "whitespace.collapse-blank-lines": lambda source: collapse_blank_lines(
            source=source,
        ),
        "whitespace.strip-trailing-space": lambda source: strip_trailing_space(
            source=source,
        ),
        "whitespace.split-long-strings": lambda source: normalize_strings(
            source=source,
            line_length=DocstringConstants.line_length,
        ).output,
    }


@final
@dataclass(frozen=True, slots=True)
class AppliedFix:
    """A fix that was applied.

    Attributes:
        fix_key (str): Fix that ran.
        rule_key (str): Rule whose finding it resolved.
        subject_path (str): Path of the subject it edited.

    """

    fix_key: str
    rule_key: str
    subject_path: str


@final
@dataclass(frozen=True, slots=True)
class SkippedFix:
    """A fix that was selected but not applied.

    Attributes:
        fix_key (str): Fix that was skipped.
        rule_key (str): Rule whose finding it would have resolved.
        subject_path (str): Path of the subject.
        reason (str): Why it was skipped, with detail.
        code (SkipCode): Closed classification of the reason.

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
        ceiling (FixSafety): Highest fix safety to apply (``proven`` or
            ``guarded``).
        stubs_path (Path | None): Stub directory for type hints, or ``None``.
        max_rounds (int): Upper bound on repeat passes.
        appliers (Mapping[str, Applier] | None): Applier functions; ``None``
            selects the built-in ones.
        create_constants (bool): Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        docstring_types (bool): Include annotation types in generated
            documentation.
        stub_docstrings (bool): Whether undocumented public definitions get a
            stub docstring.
        annotate_variables (bool): Whether function-local variables get a type
            annotation.
        negotiate (bool): Whether negotiated annotations supplement the hint
            index.
        engine (bool): Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        min_confidence (float): Offers below this confidence are not
            applied, on top of each fix's own minimum.
        checker (Checker | None): External type checker that must not object to
            guarded fixes,
            or ``None`` to apply them on astart's evidence alone.
        project (ProjectView | None): Cross-module view of the project, or
            ``None`` for single-module analysis.
        libraries (LibraryIndex | None): External signature index for callees
            outside the project, or ``None``.
        target (PythonTarget | None): Oldest Python version emitted code must
            run
            on, or ``None`` for the running interpreter.
        excluded_prefixes (tuple[str, ...]): Fix-key prefixes that are never
            applied, so a run can
            leave whole fix families (such as ``docs.``) off.
        runtime_protocols (bool): Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general (bool): Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement (str): Where synthesized protocols land:
            ``"module"`` (today's
            position, right before the enclosing top-level statement),
            ``"function"`` (directly above the def), or ``"type-checking"``
            (under ``if TYPE_CHECKING:`` with quoted annotations).
        optimize_aliases (bool): Whether repeated type patterns are extracted
            into
            PEP 695 ``type`` aliases after the fixes settle.
            Skipped when the target Python predates 3.12.

    """

    ceiling: FixSafety
    stubs_path: Path | None = None
    max_rounds: int = 8
    appliers: Mapping[str, Applier] | None = None
    create_constants: bool = False
    stub_docstrings: bool = False
    docstring_types: bool = True
    annotate_variables: bool = False
    negotiate: bool = True
    engine: bool = False
    min_confidence: float = 0.0
    checker: Checker | None = None
    project: ProjectView | None = None
    libraries: LibraryIndex | None = None
    target: PythonTarget | None = None
    excluded_prefixes: tuple[str, ...] = ()
    runtime_protocols: bool = False
    accept_general: bool = False
    protocol_placement: str = "module"
    optimize_aliases: bool = True


@final
@dataclass(frozen=True, slots=True)
class FixResult:
    """Outcome of fixing one source file.

    Attributes:
        source (str): The final source text.
        applied (tuple[AppliedFix, ...]): Fixes that were applied.
        skipped (tuple[SkippedFix, ...]): Fixes that were selected but not
            applied.
        remaining (tuple[Finding, ...]): Findings still present in the final
            source.
        parse_error (str | None): Why the source could not be analysed, if it
            could not.
        rounds (int): How many passes ran, including the final one that found
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
        index (dict[tuple[str, int, int], Subject]): Subjects of the module by
            path and position.
        facts (ModuleFacts): Resolved imports and lazily computed hints.
        table (Mapping[str, Applier]): Applier functions.
        edited (set[int]): Identities of nodes already edited, extended in
            place.

    """

    index: dict[tuple[str, int, int], Subject]
    facts: ModuleFacts
    table: Mapping[str, Applier]
    edited: set[int]


@final
@dataclass(frozen=True, slots=True)
class Job:
    """What stays fixed while one file is fixed.

    Attributes:
        filename (str): Name used for parsing and spans.
        catalog (Catalog): Rules and fixes.
        registries (Registries): Declared vocabulary.
        settings (FixSettings): Safety ceiling and options.
        cache (HintCache): Type-hint inference shared by every pass over the
            same text.

    """

    filename: str
    catalog: Catalog
    registries: Registries
    settings: FixSettings
    cache: HintCache


@final
@dataclass(frozen=True, slots=True)
class Round:
    """Outcome of one pass.

    Attributes:
        source (str): Source after the pass.
        applied (tuple[AppliedFix, ...]): Fixes applied in the pass.
        skipped (tuple[SkippedFix, ...]): Fixes skipped in the pass.
        parse_error (str | None): Parse error, if any.
        findings (tuple[Finding, ...]): Findings of the pass's input text.

    """

    source: str
    applied: tuple[AppliedFix, ...]
    skipped: tuple[SkippedFix, ...]
    parse_error: str | None
    findings: tuple[Finding, ...] = ()


@final
class _CheckerBatch:
    """Own cached, original-source probes for one rejected checker batch."""

    def __init__(
        self,
        *,
        source: str,
        pairs: ListTupleFindingFix,
        job: Job,
    ) -> None:
        """Keep stable IDs and scope the cache to one recovery operation.

        Args:
            source (str): Original source of every probe.
            pairs (ListTupleFindingFix): Findings and fixes in application
                order.
            job (Job): Unchanged run configuration.

        """
        self._source: str = source
        self._pairs: ListTupleFindingFix = pairs
        self._job: Job = job
        self._outcomes: dict[frozenset[int], Round | SkipCode] = {
            frozenset(range(len(pairs))): SkipCode.checker_rejected,
        }
        self._groups: tuple[tuple[int, ...], ...] = _function_groups(
            source=source,
            pairs=pairs,
        )

    def recover(self) -> Round:
        """Remove minimal failing cores until the remaining batch passes.

        Returns:
            Round: Verified remaining edits and
                explicit refusals for removed cores.

        """
        remaining: tuple[int, ...] = tuple(range(len(self._pairs)))
        skipped: list[SkippedFix] = []
        while not isinstance(
            outcome := self._probe(changes=remaining),
            Round,
        ):
            core: tuple[int, ...] = self._core(remaining=remaining)
            # The empty subset always yields an unchanged Round, so a failed
            # nonempty batch necessarily has an attributable nonempty core.
            if not core:
                core = remaining
            reason: Round | SkipCode = self._probe(changes=core)
            code: SkipCode = (
                reason if isinstance(reason, SkipCode) else outcome
            )
            for index in core:
                finding, fix = self._pairs[index]
                skipped.append(_refused(finding=finding, fix=fix, code=code))
            removed: frozenset[int] = frozenset(core)
            remaining = tuple(
                item for item in remaining if item not in removed
            )
        return replace(outcome, skipped=(*outcome.skipped, *skipped))

    def __call__(self, *, changes: tuple[int, ...]) -> bool:
        """Tell whether an original-source subset can be accepted.

        Args:
            changes (tuple[int, ...]): Stable fix IDs in application order.

        Returns:
            bool: Whether application, write-back and checker validation pass.

        """
        return isinstance(self._probe(changes=changes), Round)

    def _core(self, *, remaining: tuple[int, ...]) -> tuple[int, ...]:
        """Minimize function groups, then their individual edits.

        Args:
            remaining (tuple[int, ...]): Active fixes in original application
                order.

        Returns:
            tuple[int, ...]: A 1-minimal failing fix subset.

        """
        active: frozenset[int] = frozenset(remaining)
        groups: tuple[int, ...] = tuple(
            index
            for index, group in enumerate(iterable=self._groups)
            if active.intersection(group)
        )

        def grouped_test(*, changes: tuple[int, ...]) -> bool:
            """Test whole function groups before individual edits.

            Args:
                changes (tuple[int, ...]): Function-group identifiers.

            Returns:
                bool: Whether the active fixes in the groups pass.

            """
            selected: frozenset[int] = frozenset(
                item for index in changes for item in self._groups[index]
            )
            return self(
                changes=tuple(item for item in remaining if item in selected),
            )

        coarse: tuple[int, ...] = ddmin(
            changes=groups,
            test=grouped_test,
        )
        selected: frozenset[int] = frozenset(
            item for index in coarse for item in self._groups[index]
        )
        return ddmin(
            changes=tuple(item for item in remaining if item in selected),
            test=self,
        )

    def _probe(self, *, changes: tuple[int, ...]) -> Round | SkipCode:
        """Evaluate each subset at most once within this batch.

        Args:
            changes (tuple[int, ...]): Stable fix IDs in application order.

        Returns:
            Round | SkipCode: Cached output or the explicit refusal code.

        """
        key: frozenset[int] = frozenset(changes)
        if key not in self._outcomes:
            self._outcomes[key] = attempt(
                source=self._source,
                pairs=[self._pairs[index] for index in changes],
                job=self._job,
            )
        return self._outcomes[key]


def _function_groups(
    *,
    source: str,
    pairs: ListTupleFindingFix,
) -> tuple[tuple[int, ...], ...]:
    """Group edits by their innermost function, preserving fix order.

    Args:
        source (str): Original Python source.
        pairs (ListTupleFindingFix): Findings and fixes to group.

    Returns:
        tuple[tuple[int, ...], ...]: Ordered change IDs per function;
            module-level edits share a group.

    """
    functions: list[FunctionDef | AsyncFunctionDef] = [
        node
        for node in walk(node=ast_parse(source=source))
        if isinstance(node, (FunctionDef, AsyncFunctionDef))
    ]
    grouped: dict[int, list[int]] = {}
    for index, (finding, _) in enumerate(iterable=pairs):
        enclosing: FunctionDef | AsyncFunctionDef | None = next(
            (
                node
                for node in reversed(functions)
                if node.lineno
                <= finding.span.start_line
                <= (node.end_lineno or node.lineno)
            ),
            None,
        )
        owner: int = enclosing.lineno if enclosing is not None else 0
        grouped.setdefault(owner, []).append(index)
    return tuple(tuple(group) for group in grouped.values())


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
        source (str): Python source text.
        filename (str): Name used for parsing and spans.
        catalog (Catalog): Rules and fixes.
        registries (Registries): Declared vocabulary.
        settings (FixSettings): Safety ceiling and options.

    Returns:
        FixResult:
            The final source, what was applied and skipped, and what remains.

    Raises:
        ValueError: If settings contain an invalid ceiling or round count.

    """
    if (
        settings.ceiling not in Constants.allowed_ceilings
        or settings.max_rounds < 1
    ):
        msg: str = (
            "ceiling must be FixSafety.proven or FixSafety.guarded"
            if settings.ceiling not in Constants.allowed_ceilings
            else "max_rounds must be at least 1"
        )
        raise ValueError(msg)

    job: Job = Job(
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
        outcome: Round = _run_round(source=current, job=job)
        if outcome.parse_error is not None:
            parse_error = outcome.parse_error
            settled = ()
            break

        applied.extend(outcome.applied)
        for item in outcome.skipped:
            skipped[item.fix_key, item.rule_key, item.subject_path] = item
        for done in outcome.applied:
            skipped.pop(
                (done.fix_key, done.rule_key, done.subject_path),
                None,
            )

        stable: bool = not outcome.applied or outcome.source == current
        current = outcome.source
        if stable:
            settled = outcome.findings
            break

    if settings.optimize_aliases and parse_error is None:
        aliased: str | None = _optimize_aliases(
            source=current,
            filename=filename,
            target=settings.target,
        )
        if aliased is not None and aliased != current:
            current = aliased
            settled = None

    if settled is None:
        final: CheckResult = check(
            source=current,
            filename=filename,
            catalog=catalog,
            registries=registries,
            options=options(job=job),
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


def _optimize_aliases(
    *,
    source: str,
    filename: str,
    target: PythonTarget | None,
) -> str | None:
    """Extract repeated type patterns into PEP 695 aliases.

    Args:
        source (str): Final fixed source text.
        filename (str): Name used for parsing and alias evidence identifiers.
        target (PythonTarget | None): Oldest Python version emitted code must
            run on, or ``None`` when unconstrained.

    Returns:
        str | None:
            The aliased source, or ``None`` when the target predates the
            ``type`` statement or the pass cannot preserve a parseable
            module; the caller keeps the pre-alias source either way.

    """
    if target is not None and not target.type_statement:
        return None
    try:
        module: CommentedModule = parse(source=source, filename=filename)
        AliasOptimizer(tree=module, module_id=filename).optimize()
        text: str = unparse(tree=module, preserve_formatting=True)
        _ = ast_parse(source=text)
    except (SyntaxError, ValueError, TypeError, AttributeError):
        return None
    return text


def options(*, job: Job) -> CheckOptions:
    """Build the check options of a job.

    Args:
        job (Job): Fixed parameters of the run.

    Returns:
        CheckOptions:
            Options carrying the stub directory and the shared hint cache.

    """
    return CheckOptions(
        stubs_path=job.settings.stubs_path,
        hint_cache=job.cache,
        create_constants=job.settings.create_constants,
        stub_docstrings=job.settings.stub_docstrings,
        docstring_types=job.settings.docstring_types,
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
        catalog (Catalog): Rules and fixes.

    Returns:
        dict[str, int]: A position for every fix key; ties are broken by key.

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


def eligible(
    *,
    findings: tuple[Finding, ...],
    catalog: Catalog,
    ceiling: FixSafety,
    minimum: float,
    excluded: tuple[str, ...] = (),
) -> ListTupleFindingFix:
    """Select offers within the ceiling, in application order.

    Args:
        findings (tuple[Finding, ...]): Findings of the current source.
        catalog (Catalog): Rules and fixes.
        ceiling (FixSafety): Highest fix safety to apply.
        minimum (float): Offers with less confidence than this are left out, as
            are offers below their own fix's ``min_confidence``.
        excluded (tuple[str, ...]): Fix-key prefixes that are never applied.

    Returns:
        ListTupleFindingFix:
            (finding, fix) pairs ordered by fix relations, then position.

    """
    limit: int = Constants.safety_rank[ceiling]
    order: dict[str, int] = _fix_order(catalog=catalog)
    pairs: ListTupleFindingFix = [
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


def _run_round(*, source: str, job: Job) -> Round:
    """Run one pass: check, apply, write back, degrading if needed.

    Args:
        source (str): Current source text.
        job (Job): Fixed parameters of the run.

    Returns:
        Round: The pass outcome.

    """
    found: CheckResult = check(
        source=source,
        filename=job.filename,
        catalog=job.catalog,
        registries=job.registries,
        options=options(job=job),
    )
    if found.parse_error is not None:
        return Round(
            source=source,
            applied=(),
            skipped=(),
            parse_error=found.parse_error,
        )
    pairs: ListTupleFindingFix = eligible(
        findings=found.findings,
        catalog=job.catalog,
        ceiling=job.settings.ceiling,
        minimum=job.settings.min_confidence,
        excluded=job.settings.excluded_prefixes,
    )
    outcome: Round = _degrade(source=source, pairs=pairs, job=job)
    return replace(outcome, findings=found.findings)


def attempt(
    *,
    source: str,
    pairs: ListTupleFindingFix,
    job: Job,
) -> Round | SkipCode:
    """Apply fixes to one fresh tree and write it back once.

    Args:
        source (str): Source the findings were computed on.
        pairs (ListTupleFindingFix): Findings and the fixes to apply to them.
        job (Job): Fixed parameters of the run.

    Returns:
        Round | SkipCode:
            The outcome, or the code saying why the tree was not accepted:
            it cannot be written back, or the external checker rejected it.

    """
    text_pairs: ListTupleFindingFix = [
        pair for pair in pairs if pair[1].key in Constants.text_fixes
    ]
    ast_pairs: ListTupleFindingFix = [
        pair for pair in pairs if pair[1].key not in Constants.text_fixes
    ]
    applied: list[AppliedFix] = []
    skipped: list[SkippedFix] = []
    edited: str = source
    seen: set[str] = set()
    for finding, fix in text_pairs:
        if fix.key in seen:
            continue
        seen.add(fix.key)
        update: Callable[[str], str] = Constants.text_fixes[fix.key]
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
                docstring_types=settings.docstring_types,
                annotate_variables=settings.annotate_variables,
                negotiate=settings.negotiate,
                engine=settings.engine,
                project=settings.project,
                libraries=settings.libraries,
                target=settings.target,
                runtime_protocols=settings.runtime_protocols,
                accept_general=settings.accept_general,
                protocol_placement=settings.protocol_placement,
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
        return Round(
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
    return Round(
        source=text,
        applied=tuple(applied),
        skipped=tuple(skipped),
        parse_error=None,
    )


def _degrade(
    *,
    source: str,
    pairs: ListTupleFindingFix,
    job: Job,
) -> Round:
    """Recover checker failures by delta debugging, write failures by halving.

    Tries all fixes at once. When the combined write-back fails, the first
    half is applied on its own, the second half is re-matched against the
    resulting text by fingerprint, and the process recurses. Checker failures
    instead remove minimal failing cores against the original source.

    Args:
        source (str): Source the findings were computed on.
        pairs (ListTupleFindingFix): Findings and the fixes to apply to them.
        job (Job): Fixed parameters of the run.

    Returns:
        Round: The combined outcome.

    """
    if not pairs:
        return Round(source=source, applied=(), skipped=(), parse_error=None)
    outcome: Round | SkipCode = attempt(source=source, pairs=pairs, job=job)
    if isinstance(outcome, Round):
        return outcome
    if outcome is SkipCode.checker_rejected and len(pairs) > 1:
        return _CheckerBatch(source=source, pairs=pairs, job=job).recover()
    if len(pairs) == 1:
        finding, fix = pairs[0]
        return Round(
            source=source,
            applied=(),
            skipped=(_refused(finding=finding, fix=fix, code=outcome),),
            parse_error=None,
        )
    middle: int = len(pairs) // 2
    first: Round = _degrade(source=source, pairs=pairs[:middle], job=job)
    rest: ListTupleFindingFix = _rematch(
        previous=source,
        current=first.source,
        pairs=pairs[middle:],
        job=job,
    )
    second: Round = _degrade(source=first.source, pairs=rest, job=job)
    return Round(
        source=second.source,
        applied=(*first.applied, *second.applied),
        skipped=(*first.skipped, *second.skipped),
        parse_error=None,
    )


def _refused(*, finding: Finding, fix: Fix, code: SkipCode) -> SkippedFix:
    """Describe an edit rejected during batch recovery.

    Args:
        finding (Finding): Finding whose edit was refused.
        fix (Fix): Selected fix.
        code (SkipCode): Checker or write-back refusal.

    Returns:
        SkippedFix: Structured refusal retaining the original subject identity.

    """
    return SkippedFix(
        fix_key=fix.key,
        rule_key=finding.rule_key,
        subject_path=finding.subject_path,
        reason=Constants.checker_reason
        if code is SkipCode.checker_rejected
        else Constants.write_back_reason,
        code=code,
    )


def _rematch(
    *,
    previous: str,
    current: str,
    pairs: ListTupleFindingFix,
    job: Job,
) -> ListTupleFindingFix:
    """Re-locate findings in edited text through their fingerprints.

    Args:
        previous (str): Source the pairs were computed on.
        current (str): Source after earlier fixes.
        pairs (ListTupleFindingFix): Findings and fixes to carry over.
        job (Job): Fixed parameters of the run.

    Returns:
        ListTupleFindingFix:
            Pairs valid for ``current``; findings an earlier fix
            resolved, or that no longer offer the fix, are dropped.

    """
    if current == previous:
        return pairs
    found: CheckResult = check(
        source=current,
        filename=job.filename,
        catalog=job.catalog,
        registries=job.registries,
        options=options(job=job),
    )
    by_print: dict[str, Finding] = {f.fingerprint: f for f in found.findings}
    carried: ListTupleFindingFix = []
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
        finding (Finding): Finding being fixed.
        fix (Fix): Fix to apply.
        state (_Pass): Shared state of the pass.

    Returns:
        tuple[SkipCode, str] | None:
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
