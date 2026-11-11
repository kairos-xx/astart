"""Run the annotation-recovery benchmark over files and build a report."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import (
    Future,
    ProcessPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
from multiprocessing import get_context
from sys import stderr
from typing import TYPE_CHECKING, Final, final

from astart import parse as parse_module
from astart.rules.hints import (
    Hint,
    HintIndex,
    escaped_function_names,
)
from astart.rules.negotiation.builders import walk_functions
from astart.rules.negotiation.run import (
    Verdicts,
    function_nodes,
    function_paths,
    negotiate_module,
)
from astart.rules.recovery import (
    RecoveryOptions,
    RecoveryScore,
    annotation_map,
    recover,
    strip_annotations,
)

from scripts.benchmark.report import KindScore, ModuleResult, Report
from scripts.benchmark.sensors import Stat, TraceNode, arm, metrics, timed

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from astart import CommentedModule
    from astart.rules.checker import MypyChecker, PyrightChecker
    from astart.rules.hints import Key

    from scripts.benchmark.activity import Activity


@final
class Constants:
    """Group module-level constants.

    Attributes:
        crashes (Final[tuple[type[Exception], ...]]): Exception types reported
            as one module's crash instead
            of ending the whole run: any, since a harness that
            dies on the first bug loses every other measurement.
        kinds (Final[tuple[str, str]]): The annotation kinds the per-kind
            metrics split
            on: module functions and class-owned methods.

    """

    crashes: Final[tuple[type[Exception], ...]] = (Exception,)
    kinds: Final[tuple[str, str]] = ("function", "method")


@final
@dataclass(frozen=True, slots=True)
class Plan:
    """What to measure besides precision and recall.

    Attributes:
        attribute (bool): Explain missed annotations (one more inference run).
        delta (PyrightChecker | MypyChecker | None): Checker used for the
            new-error count, or ``None``.
        delta_limit (int): How many annotated modules get the checker delta.
        gated (bool): Whether the delta checker also vetoes guarded
            fixes, as in a normal ``astart fix`` run.
        jobs (int): Worker processes; with more than one, the checker delta
            goes
            to the first ``delta_limit`` modules in the order given.
        negotiate (bool): Whether negotiated hints supplement the hint index.
        variables (bool): Whether local variables are annotated.
        engine (bool): Conversion mode (the engine's own annotations).

    """

    attribute: bool = True
    delta: PyrightChecker | MypyChecker | None = None
    delta_limit: int = 20
    gated: bool = False
    jobs: int = 1
    negotiate: bool = True
    variables: bool = False
    engine: bool = False


def _function_path(*, key: str) -> str:
    """Recover the owning function's qualified name from a scored key.

    Args:
        key (str): A ``func.param`` or ``func->`` annotation key.

    Returns:
        str: The qualified function name the key belongs to.

    """
    return key[:-2] if key.endswith("->") else key.rpartition(".")[0]


def _entry_key(*, entry: str) -> str:
    """Read the annotation key at the start of a score entry.

    Args:
        entry (str): A ``wrong`` or ``compatible`` string of the form
            ``key: wrote ...``.

    Returns:
        str: The annotation key.

    """
    return entry.partition(": ")[0]


def _hint_bases(
    *,
    module: CommentedModule,
    plan: Plan,
) -> dict[str, str]:
    """Map annotation paths to the basis that produced them.

    Rebuilds the same hint sources ``fix_source`` consults — the hint index,
    then negotiated hints, then engine proposals — and overlays them in the
    same precedence order (index wins, engine fills gaps).

    Args:
        module (CommentedModule): Parsed stripped module.
        plan (Plan): The benchmark plan (negotiation and
            engine flags decide which layers apply).

    Returns:
        dict[str, str]: ``path: basis`` for every parameter and return a hint
            exists for.

    """
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    paths: dict[Key, str] = function_paths(module=module)
    nodes: dict[str, AST] = function_nodes(module=module)
    bases: dict[str, str] = {}
    if plan.engine:
        for node_key in index.proposals:
            path: str | None = paths.get(node_key)
            if path is not None:
                bases[path] = "engine"
    if plan.negotiate:
        verdicts: Verdicts = negotiate_module(
            module=module,
            corroboration={
                paths[key]: text
                for key, text in index.proposals.items()
                if key in paths
            },
            escaped=escaped_function_names(module=module),
        )
        for path in verdicts.accepted:
            bases[path] = "negotiated"
    for path, node in nodes.items():
        hint: Hint | None = index.hint_for(node=node)
        if hint is not None:
            bases[path] = hint.basis.value
    return bases


def _classify(
    *,
    source: str,
    score: RecoveryScore,
    plan: Plan,
) -> tuple[
    tuple[KindScore, ...],
    tuple[tuple[str, int], ...],
    tuple[tuple[str, str, int], ...],
]:
    """Break one module's score down by kind, basis and basis outcome.

    Args:
        source (str): The original (typed) module source.
        score (RecoveryScore): The recovery score for the module.
        plan (Plan): The benchmark plan that produced the score.

    Returns:
        tuple[
                tuple[KindScore, ...],
                tuple[tuple[str, int], ...],
                tuple[tuple[str, str, int], ...]
            ]:
            ``(by_kind, by_basis, basis_outcomes)`` for the module.

    """
    truth: Mapping[str, str] = annotation_map(source=source)
    module: CommentedModule = parse_module(
        source=strip_annotations(source=source),
    )
    kinds: dict[str, str] = {
        qual: "method" if in_class else "function"
        for qual, _function, in_class in walk_functions(
            node=module,
            trail=(),
            in_class=False,
        )
    }

    def kind_of(*, key: str) -> str:
        """Classify one scored key as ``function`` or ``method``.

        Args:
            key (str): Scored entry key.

        Returns:
            str: ``"method"`` for class-owned paths, else ``"function"``.

        """
        return kinds.get(_function_path(key=key), "function")

    wrong_keys: set[str] = {_entry_key(entry=item) for item in score.wrong}
    compatible_keys: set[str] = {
        _entry_key(entry=item) for item in score.compatible
    }
    correct_keys: set[str] = (
        set(truth)
        - set(score.missed)
        - wrong_keys
        - compatible_keys
        - set(score.synthesized)
    )
    counts: dict[str, Counter[str]] = {
        kind: Counter() for kind in Constants.kinds
    }
    for key in truth:
        bucket: Counter[str] = counts[kind_of(key=key)]
        bucket["truth"] += 1
        if key in correct_keys:
            bucket["correct"] += 1
        elif key in wrong_keys:
            bucket["wrong"] += 1
        elif key in compatible_keys:
            bucket["compatible"] += 1
    by_kind: tuple[KindScore, ...] = tuple(
        KindScore(
            kind=kind,
            truth=counts[kind]["truth"],
            correct=counts[kind]["correct"],
            wrong=counts[kind]["wrong"],
            compatible=counts[kind]["compatible"],
        )
        for kind in Constants.kinds
        if counts[kind]["truth"]
    )
    bases: dict[str, str] = _hint_bases(module=module, plan=plan)
    synthesized: set[str] = set(score.synthesized)
    written: set[str] = correct_keys | wrong_keys | compatible_keys
    by_basis: Counter[str] = Counter()
    outcomes: Counter[tuple[str, str]] = Counter()
    for path in written | synthesized:
        basis: str = bases.get(
            path,
            "synthesized" if path in synthesized else "unattributed",
        )
        by_basis[basis] += 1
        if path in synthesized:
            outcome: str = "synthesized"
        elif path in correct_keys:
            outcome = "correct"
        elif path in wrong_keys:
            outcome = "wrong"
        else:
            outcome = "compatible"
        outcomes[(basis, outcome)] += 1
    basis_outcomes: tuple[tuple[str, str, int], ...] = tuple(
        sorted(
            (basis, outcome, count)
            for (basis, outcome), count in outcomes.items()
        ),
    )
    return by_kind, tuple(sorted(by_basis.items())), basis_outcomes


def _measure(*, path: Path, plan: Plan, spent: int) -> ModuleResult:
    """Score one module, turning a crash into a result.

    Args:
        path (Path): Typed module (``.py`` or ``.py``).
        plan (Plan): What to measure.
        spent (int): How many modules already got the checker delta.

    Returns:
        ModuleResult:
            The module result, independent sensor totals and call tree.

    """
    source: str = path.read_text(encoding="utf-8")
    use_delta: bool = plan.delta is not None and spent < plan.delta_limit
    try:
        score: RecoveryScore = recover(
            source=source,
            filename=path.name,
            options=RecoveryOptions(
                attribute=plan.attribute,
                delta=plan.delta if use_delta else None,
                checker=plan.delta if use_delta and plan.gated else None,
                negotiate=plan.negotiate,
                annotate_variables=plan.variables,
                engine=plan.engine,
            ),
        )
    except Constants.crashes as error:
        return ModuleResult(
            name=path.name,
            truth=0,
            correct=0,
            wrong=(),
            synthesized=0,
            seconds=0.0,
            rounds=0,
            missed_reasons=(),
            new_errors=None,
            crash=f"{type(error).__name__}: {error}",
        )
    by_kind, by_basis, basis_outcomes = _classify(
        source=source,
        score=score,
        plan=plan,
    )
    return ModuleResult(
        name=path.name,
        truth=score.truth,
        correct=score.correct,
        wrong=score.wrong,
        synthesized=len(score.synthesized),
        seconds=round(number=score.seconds, ndigits=3),
        rounds=score.rounds,
        missed_reasons=score.missed_reasons,
        new_errors=score.new_errors,
        crash=None,
        compatible=score.compatible,
        by_kind=by_kind,
        by_basis=by_basis,
        basis_outcomes=basis_outcomes,
    )


def _measure_at(
    job: tuple[Path, Plan, int],
    /,
) -> tuple[ModuleResult, dict[str, Stat], TraceNode]:
    """Score one module in a worker process.

    Args:
        job (tuple[Path, Plan, int]): The module, the plan, and how many
            modules precede it
            (which decides whether it still gets the checker delta).

    Returns:
        tuple[ModuleResult, dict[str, Stat], TraceNode]: The module result,
            independent sensor totals and call tree.

    """
    path, plan, spent = job
    _ = stderr.write(f"{path.name}\n")
    metrics.reset()
    arm(register_exit=False)
    with timed(label=f"module:{path.name}"):
        result: ModuleResult = _measure(path=path, plan=plan, spent=spent)
    trace: TraceNode = metrics.root
    trace.label = f"worker:{path.name}"
    trace.wall_ns = sum(child.wall_ns for child in trace.children.values())
    trace.cpu_ns = sum(child.cpu_ns for child in trace.children.values())
    return result, dict(metrics.snapshot()), trace


def run_recovery(
    *,
    paths: Sequence[Path],
    plan: Plan,
    activity: Activity | None = None,
) -> Report:
    """Measure annotation recovery over a set of modules.

    Args:
        paths (Sequence[Path]): Typed modules to strip, fix and score.
        plan (Plan): What to measure besides precision and recall.
        activity (Activity | None): Optional heartbeat and module-progress
            recorder.

    Returns:
        Report: The report, one entry per module in the order given.

    """
    if activity is not None:
        activity.progress(completed=0, total=len(paths), current="starting")
    if plan.jobs > 1:
        with ProcessPoolExecutor(
            max_workers=min(plan.jobs, len(paths) or 1),
            mp_context=get_context(method="spawn"),
        ) as pool:
            futures: dict[
                Future[tuple[ModuleResult, dict[str, Stat], TraceNode]],
                int,
            ] = {
                pool.submit(_measure_at, (path, plan, position)): position
                for position, path in enumerate(iterable=paths)
            }
            ordered: dict[int, ModuleResult] = {}
            for future in as_completed(fs=futures):
                position: int = futures[future]
                result, stats, trace = future.result()
                ordered[position] = result
                metrics.merge(stats=stats, trace=trace)
                if activity is not None:
                    activity.progress(
                        completed=len(ordered),
                        total=len(paths),
                        current=paths[position].name,
                    )
            return Report.of(modules=[ordered[i] for i in range(len(paths))])
    results: list[ModuleResult] = []
    spent: int = 0
    for position, path in enumerate(iterable=paths, start=1):
        _ = stderr.write(f"[{position}/{len(paths)}] {path.name}\n")
        if activity is not None:
            activity.progress(
                completed=position - 1,
                total=len(paths),
                current=path.name,
            )
        result: ModuleResult = _measure(path=path, plan=plan, spent=spent)
        if result.new_errors is not None:
            spent += 1
        results.append(result)
        if activity is not None:
            activity.progress(
                completed=position,
                total=len(paths),
                current=path.name,
            )
    return Report.of(modules=results)
