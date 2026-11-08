"""Run the annotation-recovery benchmark over files and build a report."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from sys import stderr
from typing import TYPE_CHECKING, Final, final

from astart.rules.recovery import RecoveryOptions, RecoveryScore, recover

from benchmarks.report import ModuleResult, Report

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from astart.rules.checker import MypyChecker, PyrightChecker


@final
class Constants:
    """Group module-level constants.

    Attributes:
        crashes: Exception types reported as one module's crash instead of
            ending the whole run: any, since a harness that dies on the first
            bug loses every other measurement.

    """

    crashes: Final[tuple[type[Exception], ...]] = (Exception,)


@final
@dataclass(frozen=True, slots=True)
class Plan:
    """What to measure besides precision and recall.

    Attributes:
        attribute: Explain missed annotations (one more inference run).
        delta: Checker used for the new-error count, or ``None``.
        delta_limit: How many annotated modules get the checker delta.
        gated: Whether the delta checker also vetoes guarded fixes, as in
            a normal ``astart fix`` run.
        jobs: Worker processes; with more than one, the checker delta goes
            to the first ``delta_limit`` modules in the order given.
        negotiate: Whether negotiated hints supplement the hint index.
        variables: Whether local variables are annotated.
        engine: Conversion mode (the engine's own annotations).

    """

    attribute: bool = True
    delta: PyrightChecker | MypyChecker | None = None
    delta_limit: int = 20
    gated: bool = False
    jobs: int = 1
    negotiate: bool = True
    variables: bool = False
    engine: bool = False


def _measure(*, path: Path, plan: Plan, spent: int) -> ModuleResult:
    """Score one module, turning a crash into a result.

    Args:
        path: Typed module (``.py`` or ``.py.txt``).
        plan: What to measure.
        spent: How many modules already got the checker delta.

    Returns:
        The module's result.

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
    )


def _measure_at(job: tuple[Path, Plan, int]) -> ModuleResult:
    """Score one module in a worker process.

    Args:
        job: The module, the plan, and how many modules precede it (which
            decides whether it still gets the checker delta).

    Returns:
        The module's result.

    """
    path, plan, spent = job
    _ = stderr.write(f"{path.name}\n")
    return _measure(path=path, plan=plan, spent=spent)


def run_recovery(*, paths: Sequence[Path], plan: Plan) -> Report:
    """Measure annotation recovery over a set of modules.

    Args:
        paths: Typed modules to strip, fix and score.
        plan: What to measure besides precision and recall.

    Returns:
        The report, one entry per module in the order given.

    """
    if plan.jobs > 1:
        pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=plan.jobs)
        with pool:
            return Report.of(
                modules=list(
                    pool.map(
                        _measure_at,
                        [
                            (path, plan, position)
                            for position, path in enumerate(iterable=paths)
                        ],
                    ),
                ),
            )
    results: list[ModuleResult] = []
    spent: int = 0
    for position, path in enumerate(iterable=paths, start=1):
        _ = stderr.write(f"[{position}/{len(paths)}] {path.name}\n")
        result: ModuleResult = _measure(path=path, plan=plan, spent=spent)
        if result.new_errors is not None:
            spent += 1
        results.append(result)
    return Report.of(modules=results)
