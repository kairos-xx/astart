"""Benchmark report: per-module results, totals, JSON form and the gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from json import dumps, loads
from typing import TYPE_CHECKING, Final, Self, TypedDict, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        indent: JSON indentation.

    """

    indent: Final[int] = 2


@final
@dataclass(frozen=True, slots=True)
class ModuleResult:
    """What the recovery benchmark measured for one module.

    Attributes:
        name: Module file name.
        truth: Annotations the original had.
        correct: Recovered annotations equal to the original.
        wrong: Annotations written that differ from the original.
        synthesized: Annotations that are synthesized Protocols/TypeVars.
        seconds: Time of the fix run.
        rounds: Passes the fix run needed.
        missed_reasons: ``(reason, count)`` pairs for the missed annotations.
        new_errors: New type-checker errors the fixes introduced, or
            ``None`` when the checker did not run.
        crash: ``Type: message`` when the module crashed, else ``None``.

    """

    name: str
    truth: int
    correct: int
    wrong: tuple[str, ...]
    synthesized: int
    seconds: float
    rounds: int
    missed_reasons: tuple[tuple[str, int], ...]
    new_errors: int | None
    crash: str | None


@final
@dataclass(frozen=True, slots=True)
class Thresholds:
    """Limits the gate enforces.

    Attributes:
        min_precision: Least acceptable precision over the whole run.
        recall_slack: How far total recall may fall below the baseline.
        max_rounds: Most passes any module may need.
        max_crashes: Most modules that may crash.
        max_new_errors: Most new checker errors the fixes may introduce.

    """

    min_precision: float = 0.995
    recall_slack: float = 0.005
    max_rounds: int = 3
    max_crashes: int = 0
    max_new_errors: int = 0


@final
@dataclass(frozen=True, slots=True)
class Report:
    """A whole benchmark run.

    Attributes:
        modules: One result per module, in the order they were run.

    """

    modules: tuple[ModuleResult, ...]

    @classmethod
    def of(cls, *, modules: Sequence[ModuleResult]) -> Self:
        """Build a report.

        Args:
            modules: Per-module results.

        Returns:
            The report.

        """
        return cls(modules=tuple(modules))

    @property
    def truth(self) -> int:
        """Annotations the originals had.

        Returns:
            The total over scored modules.

        """
        return sum(item.truth for item in self.modules)

    @property
    def correct(self) -> int:
        """Annotations recovered equal to the original.

        Returns:
            The total over scored modules.

        """
        return sum(item.correct for item in self.modules)

    @property
    def wrong(self) -> int:
        """Annotations written that differ from the original.

        Returns:
            The total over scored modules.

        """
        return sum(len(item.wrong) for item in self.modules)

    @property
    def precision(self) -> float:
        """Share of written annotations that match the original.

        Returns:
            ``1.0`` when nothing was written.

        """
        written: int = self.correct + self.wrong
        return 1.0 if written == 0 else self.correct / written

    @property
    def recall(self) -> float:
        """Share of original annotations that were recovered.

        Returns:
            ``1.0`` when the originals had none.

        """
        return 1.0 if self.truth == 0 else self.correct / self.truth

    @property
    def crashed(self) -> tuple[str, ...]:
        """Names of the modules that crashed.

        Returns:
            File names, in run order.

        """
        return tuple(item.name for item in self.modules if item.crash)

    @property
    def seconds(self) -> float:
        """Total time of the fix runs.

        Returns:
            Seconds.

        """
        return sum(item.seconds for item in self.modules)

    @property
    def new_errors(self) -> int:
        """New checker errors introduced, over the modules that were checked.

        Returns:
            The total.

        """
        return sum(item.new_errors or 0 for item in self.modules)

    @property
    def rounds_histogram(self) -> tuple[tuple[int, int], ...]:
        """How many modules needed each number of passes.

        Returns:
            ``(rounds, modules)`` pairs, fewest rounds first.

        """
        counts: Counter[int] = Counter(
            item.rounds for item in self.modules if not item.crash
        )
        return tuple(sorted(counts.items()))

    @property
    def missed_reasons(self) -> tuple[tuple[str, int], ...]:
        """Why annotations were missed, over all modules.

        Returns:
            ``(reason, count)`` pairs, most frequent first.

        """
        counts: Counter[str] = Counter()
        for item in self.modules:
            for reason, count in item.missed_reasons:
                counts[reason] += count
        return tuple(
            sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])),
        )


def to_json(*, report: Report) -> str:
    """Render a report as JSON.

    Args:
        report: The run to render.

    Returns:
        A JSON document with the summary and every module.

    """
    return dumps(
        obj={
            "summary": {
                "modules": len(report.modules),
                "truth": report.truth,
                "correct": report.correct,
                "wrong": report.wrong,
                "precision": round(number=report.precision, ndigits=6),
                "recall": round(number=report.recall, ndigits=6),
                "crashed": list(report.crashed),
                "seconds": round(number=report.seconds, ndigits=1),
                "new_errors": report.new_errors,
                "rounds": [list(pair) for pair in report.rounds_histogram],
                "missed_reasons": dict(report.missed_reasons),
            },
            "modules": [
                {
                    "name": item.name,
                    "truth": item.truth,
                    "correct": item.correct,
                    "wrong": list(item.wrong),
                    "synthesized": item.synthesized,
                    "seconds": item.seconds,
                    "rounds": item.rounds,
                    "missed_reasons": [list(p) for p in item.missed_reasons],
                    "new_errors": item.new_errors,
                    "crash": item.crash,
                }
                for item in report.modules
            ],
        },
        indent=Constants.indent,
    )


class _ModuleJson(TypedDict):
    """Serialized form of one :class:`ModuleResult`.

    Attributes:
        name: Module file name.
        truth: Annotations the original had.
        correct: Recovered annotations equal to the original.
        wrong: Annotations written that differ from the original.
        synthesized: Annotations that are synthesized Protocols/TypeVars.
        seconds: Time of the fix run.
        rounds: Passes the fix run needed.
        missed_reasons: ``(reason, count)`` pairs for missed annotations.
        new_errors: New checker errors, or ``None`` when unchecked.
        crash: ``Type: message`` when the module crashed, else ``None``.

    """

    name: str
    truth: int
    correct: int
    wrong: list[str]
    synthesized: int
    seconds: float
    rounds: int
    missed_reasons: list[tuple[str, int]]
    new_errors: int | None
    crash: str | None


class _ReportJson(TypedDict):
    """The ``modules`` member of a serialized report.

    Attributes:
        modules: One entry per measured module.

    """

    modules: list[_ModuleJson]


def from_json(*, text: str) -> Report:
    """Read a report written by :func:`to_json`.

    Args:
        text: The JSON document.

    Returns:
        The report; derived summary fields are recomputed.

    """
    data: _ReportJson = loads(s=text)
    return Report.of(
        modules=[
            ModuleResult(
                name=item["name"],
                truth=item["truth"],
                correct=item["correct"],
                wrong=tuple(item["wrong"]),
                synthesized=item["synthesized"],
                seconds=item["seconds"],
                rounds=item["rounds"],
                missed_reasons=tuple(
                    (reason, count) for reason, count in item["missed_reasons"]
                ),
                new_errors=item["new_errors"],
                crash=item["crash"],
            )
            for item in data["modules"]
        ],
    )


def compare(
    *,
    report: Report,
    baseline: Report,
    limits: Thresholds,
) -> tuple[str, ...]:
    """List every way a run is worse than the limits and the baseline allow.

    Args:
        report: The run under test.
        baseline: The accepted earlier run.
        limits: Thresholds to enforce.

    Returns:
        One sentence per breach; empty when the run passes.

    """
    problems: list[str] = []
    if report.precision < limits.min_precision:
        problems.append(
            f"precision {report.precision:.4f} is below "
            f"{limits.min_precision:.4f} ({report.wrong} wrong annotations)",
        )
    if report.recall < baseline.recall - limits.recall_slack:
        problems.append(
            f"recall {report.recall:.4f} fell below the baseline "
            f"{baseline.recall:.4f} by more than {limits.recall_slack:.4f}",
        )
    earlier: dict[str, int] = {m.name: m.correct for m in baseline.modules}
    problems.extend(
        f"module {item.name} recovers {item.correct} annotations, "
        f"the baseline {earlier[item.name]}"
        for item in report.modules
        if item.name in earlier and item.correct < earlier[item.name]
    )
    if len(report.crashed) > limits.max_crashes:
        problems.append(f"crash in modules: {', '.join(report.crashed)}")
    slow: list[str] = [
        item.name for item in report.modules if item.rounds > limits.max_rounds
    ]
    if slow:
        problems.append(
            f"rounds above {limits.max_rounds} in: {', '.join(slow)}",
        )
    if report.new_errors > limits.max_new_errors:
        problems.append(
            f"the checker reports {report.new_errors} new errors after fixing",
        )
    return tuple(problems)
