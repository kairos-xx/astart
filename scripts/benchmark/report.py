"""Benchmark report: per-module results, totals, JSON form and the gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from json import dumps, loads
from typing import TYPE_CHECKING, Final, NotRequired, Self, TypedDict, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        indent (Final[int]): JSON indentation.

    """

    indent: Final[int] = 2


@final
@dataclass(frozen=True, slots=True)
class KindScore:
    """Recovery counts for one annotation kind.

    Attributes:
        kind (str): ``function`` or ``method``.
        truth (int): Original annotations of this kind.
        correct (int): Recovered annotations equal to the original.
        wrong (int): Written annotations that contradict the original.
        compatible (int): Written annotations compatible with the original.

    """

    kind: str
    truth: int
    correct: int
    wrong: int
    compatible: int

    @property
    def precision(self) -> float:
        """Share of written annotations of this kind that do not contradict.

        Returns:
            float: ``1.0`` when none were written.

        """
        written: int = self.correct + self.compatible + self.wrong
        return 1.0 if written == 0 else 1 - self.wrong / written

    @property
    def recall(self) -> float:
        """Share of this kind's original annotations that were recovered.

        Returns:
            float: ``1.0`` when the originals had none.

        """
        return 1.0 if self.truth == 0 else self.correct / self.truth


@final
@dataclass(frozen=True, slots=True)
class ModuleResult:
    """What the recovery benchmark measured for one module.

    Attributes:
        name (str): Module file name.
        truth (int): Annotations the original had.
        correct (int): Recovered annotations equal to the original.
        wrong (tuple[str, ...]): Annotations written that contradict the
            original.
        synthesized (int): Annotations that are synthesized Protocols/TypeVars.
        seconds (float): Time of the fix run.
        rounds (int): Passes the fix run needed.
        missed_reasons (tuple[tuple[str, int], ...]): ``(reason, count)`` pairs
            for the missed annotations.
        new_errors (int | None): New type-checker errors the fixes introduced,
            or ``None`` when the checker did not run.
        crash (str | None): ``Type: message`` when the module crashed, else
            ``None``.
        compatible (tuple[str, ...]): Annotations written that are a subtype or
            supertype
            of the original (neither correct nor wrong).
        by_kind (tuple[KindScore, ...]): Recovery counts per annotation kind.
        by_basis (tuple[tuple[str, int], ...]): ``(basis, count)`` pairs over
            the recorded written annotations.
        basis_outcomes: ``(basis, outcome, count)`` triples over the recorded
            written annotations; outcome is ``correct``,
            ``wrong``, ``compatible`` or ``synthesized``.

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
    compatible: tuple[str, ...] = ()
    by_kind: tuple[KindScore, ...] = ()
    by_basis: tuple[tuple[str, int], ...] = ()
    basis_outcomes: tuple[tuple[str, str, int], ...] = ()


@final
@dataclass(frozen=True, slots=True)
class Thresholds:
    """Limits the gate enforces.

    Attributes:
        min_precision (float): Least acceptable precision over the whole run.
        recall_slack (float): How far total recall may fall below the baseline.
        max_rounds (int): Most passes any module may need.
        max_crashes (int): Most modules that may crash.
        max_new_errors (int): Most new checker errors the fixes may introduce.
        method_recall_factor (float): Least method recall as a multiple of the
            baseline's, enforced only when both reports record ``by_kind``.
        method_precision_slack (float): How far method precision may fall below
            the baseline's,
            enforced only when both reports record ``by_kind``.

    """

    min_precision: float = 0.995
    recall_slack: float = 0.005
    max_rounds: int = 3
    max_crashes: int = 0
    max_new_errors: int = 0
    method_recall_factor: float = 3.0
    method_precision_slack: float = 0.001


@final
@dataclass(frozen=True, slots=True)
class Report:
    """A whole benchmark run.

    Attributes:
        modules (tuple[ModuleResult, ...]): One result per module, in the order
            they were run.
        tree_hash (str): ``treehash.tree_hash`` of the source tree that
            produced the
            run; empty for reports written before stamping existed.
        corpus (str): Name of the corpus the modules came from.

    """

    modules: tuple[ModuleResult, ...]
    tree_hash: str = ""
    corpus: str = ""

    @classmethod
    def of(
        cls,
        *,
        modules: Sequence[ModuleResult],
        tree_hash: str = "",
        corpus: str = "",
    ) -> Self:
        """Build a report.

        Args:
            modules (Sequence[ModuleResult]): Per-module results.
            tree_hash (str): Source-tree stamp of the producing run.
            corpus (str): Corpus label of the measured modules.

        Returns:
            Self: The report.

        """
        return cls(
            modules=tuple(modules),
            tree_hash=tree_hash,
            corpus=corpus,
        )

    @property
    def truth(self) -> int:
        """Annotations the originals had.

        Returns:
            int: The total over scored modules.

        """
        return sum(item.truth for item in self.modules)

    @property
    def correct(self) -> int:
        """Annotations recovered equal to the original.

        Returns:
            int: The total over scored modules.

        """
        return sum(item.correct for item in self.modules)

    @property
    def wrong(self) -> int:
        """Annotations written that differ from the original.

        Returns:
            int: The total over scored modules.

        """
        return sum(len(item.wrong) for item in self.modules)

    @property
    def compatible(self) -> int:
        """Annotations that differ from the original but do not contradict it.

        Returns:
            int: The total over scored modules.

        """
        return sum(len(item.compatible) for item in self.modules)

    @property
    def precision(self) -> float:
        """Share of written annotations that do not contradict the original.

        Returns:
            float: ``1.0`` when nothing was written.

        """
        written: int = self.correct + self.compatible + self.wrong
        return 1.0 if written == 0 else 1 - self.wrong / written

    @property
    def recall(self) -> float:
        """Share of original annotations that were recovered.

        Returns:
            float: ``1.0`` when the originals had none.

        """
        return 1.0 if self.truth == 0 else self.correct / self.truth

    @property
    def crashed(self) -> tuple[str, ...]:
        """Names of the modules that crashed.

        Returns:
            tuple[str, ...]: File names, in run order.

        """
        return tuple(item.name for item in self.modules if item.crash)

    @property
    def seconds(self) -> float:
        """Total time of the fix runs.

        Returns:
            float: Seconds.

        """
        return sum(item.seconds for item in self.modules)

    @property
    def new_errors(self) -> int:
        """New checker errors introduced, over the modules that were checked.

        Returns:
            int: The total.

        """
        return sum(item.new_errors or 0 for item in self.modules)

    @property
    def rounds_histogram(self) -> tuple[tuple[int, int], ...]:
        """How many modules needed each number of passes.

        Returns:
            tuple[tuple[int, int], ...]: ``(rounds, modules)`` pairs, fewest
                rounds first.

        """
        counts: Counter[int] = Counter(
            item.rounds for item in self.modules if not item.crash
        )
        return tuple(sorted(counts.items()))

    @property
    def missed_reasons(self) -> tuple[tuple[str, int], ...]:
        """Why annotations were missed, over all modules.

        Returns:
            tuple[tuple[str, int], ...]: ``(reason, count)`` pairs, most
                frequent first.

        """
        counts: Counter[str] = Counter()
        for item in self.modules:
            for reason, count in item.missed_reasons:
                counts[reason] += count
        return tuple(
            sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])),
        )

    @property
    def by_kind(self) -> dict[str, KindScore]:
        """Recovery counts per annotation kind over all modules.

        Returns:
            dict[str, KindScore]: Summed counts keyed by ``function`` and
                ``method``.

        """
        totals: dict[str, Counter[str]] = {}
        for item in self.modules:
            for score in item.by_kind:
                bucket: Counter[str] = totals.setdefault(
                    score.kind,
                    Counter(),
                )
                bucket["truth"] += score.truth
                bucket["correct"] += score.correct
                bucket["wrong"] += score.wrong
                bucket["compatible"] += score.compatible
        return {
            kind: KindScore(
                kind=kind,
                truth=counts["truth"],
                correct=counts["correct"],
                wrong=counts["wrong"],
                compatible=counts["compatible"],
            )
            for kind, counts in totals.items()
        }

    @property
    def by_basis(self) -> dict[str, int]:
        """Written-annotation counts per hint basis over all modules.

        Returns:
            dict[str, int]: ``basis: count`` pairs, sorted by basis name.

        """
        counts: Counter[str] = Counter()
        for item in self.modules:
            for basis, count in item.by_basis:
                counts[basis] += count
        return dict(sorted(counts.items()))


def _basis_outcome_map(*, item: ModuleResult) -> dict[str, dict[str, int]]:
    """Group one module's ``basis_outcomes`` triples for JSON output.

    Args:
        item (ModuleResult): The module result to group.

    Returns:
        dict[str, dict[str, int]]: ``basis: outcome: count`` nested mapping.

    """
    grouped: dict[str, dict[str, int]] = {}
    for basis, outcome, count in item.basis_outcomes:
        grouped.setdefault(basis, {})[outcome] = count
    return grouped


def to_json(*, report: Report) -> str:
    """Render a report as JSON.

    Args:
        report (Report): The run to render.

    Returns:
        str: A JSON document with the summary and every module.

    """
    return dumps(
        obj={
            "summary": {
                "modules": len(report.modules),
                "truth": report.truth,
                "correct": report.correct,
                "wrong": report.wrong,
                "compatible": report.compatible,
                "precision": round(number=report.precision, ndigits=6),
                "recall": round(number=report.recall, ndigits=6),
                "crashed": list(report.crashed),
                "seconds": round(number=report.seconds, ndigits=1),
                "new_errors": report.new_errors,
                "rounds": [list(pair) for pair in report.rounds_histogram],
                "missed_reasons": dict(report.missed_reasons),
                "by_kind": {
                    kind: {
                        "truth": score.truth,
                        "correct": score.correct,
                        "wrong": score.wrong,
                        "compatible": score.compatible,
                        "precision": round(
                            number=score.precision,
                            ndigits=6,
                        ),
                        "recall": round(number=score.recall, ndigits=6),
                    }
                    for kind, score in sorted(report.by_kind.items())
                },
                "by_basis": report.by_basis,
                "tree_hash": report.tree_hash,
                "corpus": report.corpus,
            },
            "modules": [
                {
                    "name": item.name,
                    "truth": item.truth,
                    "correct": item.correct,
                    "wrong": list(item.wrong),
                    "compatible": list(item.compatible),
                    "synthesized": item.synthesized,
                    "seconds": item.seconds,
                    "rounds": item.rounds,
                    "missed_reasons": [list(p) for p in item.missed_reasons],
                    "new_errors": item.new_errors,
                    "crash": item.crash,
                    "by_kind": {
                        score.kind: {
                            "truth": score.truth,
                            "correct": score.correct,
                            "wrong": score.wrong,
                            "compatible": score.compatible,
                        }
                        for score in item.by_kind
                    },
                    "by_basis": dict(item.by_basis),
                    "basis_outcomes": _basis_outcome_map(item=item),
                }
                for item in report.modules
            ],
        },
        indent=Constants.indent,
    )


class _ModuleJson(TypedDict):
    """Serialized form of one :class:`ModuleResult`.

    Attributes:
        name (str): Module file name.
        truth (int): Annotations the original had.
        correct (int): Recovered annotations equal to the original.
        wrong (list[str]): Annotations written that differ from the original.
        compatible (NotRequired[list[str]]): Annotations compatible with but
            not equal to the original.
        synthesized (int): Annotations that are synthesized Protocols/TypeVars.
        seconds (float): Time of the fix run.
        rounds (int): Passes the fix run needed.
        missed_reasons (list[tuple[str, int]]): ``(reason, count)`` pairs for
            missed annotations.
        new_errors (int | None): New checker errors, or ``None`` when
            unchecked.
        crash (str | None): ``Type: message`` when the module crashed, else
            ``None``.
        by_kind (NotRequired[dict[str, dict[str, int]]]): Per-kind recovery
            counts, or empty when unrecorded.
        by_basis (NotRequired[dict[str, int]]): ``basis: count`` pairs over the
            written annotations.
        basis_outcomes: ``basis: outcome: count`` pairs over the written
            annotations.

    """

    name: str
    truth: int
    correct: int
    wrong: list[str]
    compatible: NotRequired[list[str]]
    synthesized: int
    seconds: float
    rounds: int
    missed_reasons: list[tuple[str, int]]
    new_errors: int | None
    crash: str | None
    by_kind: NotRequired[dict[str, dict[str, int]]]
    by_basis: NotRequired[dict[str, int]]
    basis_outcomes: NotRequired[dict[str, dict[str, int]]]


class _ReportJson(TypedDict):
    """The ``modules`` member of a serialized report.

    Attributes:
        modules (list[_ModuleJson]): One entry per measured module.
        summary (NotRequired[dict[str, object]]): Optional provenance stamp
            written by ``to_json``.

    """

    modules: list[_ModuleJson]
    summary: NotRequired[dict[str, object]]


def from_json(*, text: str) -> Report:
    """Read a report written by :func:`to_json`.

    Args:
        text (str): The JSON document.

    Returns:
        Report: The report; derived summary fields are recomputed.

    """
    data: _ReportJson = loads(s=text)
    summary: dict[str, object] = data.get("summary", {})
    return Report.of(
        tree_hash=str(object=summary.get("tree_hash", "")),
        corpus=str(object=summary.get("corpus", "")),
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
                compatible=tuple(item.get("compatible", [])),
                by_kind=tuple(
                    KindScore(
                        kind=kind,
                        truth=counts["truth"],
                        correct=counts["correct"],
                        wrong=counts["wrong"],
                        compatible=counts["compatible"],
                    )
                    for kind, counts in item.get("by_kind", {}).items()
                ),
                by_basis=tuple(item.get("by_basis", {}).items()),
                basis_outcomes=tuple(
                    (basis, outcome, count)
                    for basis, outcomes in item.get(
                        "basis_outcomes",
                        {},
                    ).items()
                    for outcome, count in outcomes.items()
                ),
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
        report (Report): The run under test.
        baseline (Report): The accepted earlier run.
        limits (Thresholds): Thresholds to enforce.

    Returns:
        tuple[str, ...]: One sentence per breach; empty when the run passes.

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
    earlier_method: KindScore | None = baseline.by_kind.get("method")
    method: KindScore | None = report.by_kind.get("method")
    if earlier_method is not None and method is not None:
        floor: float = limits.method_recall_factor * earlier_method.recall
        if method.recall < floor:
            problems.append(
                f"method recall {method.recall:.4f} is below "
                f"{limits.method_recall_factor}x the baseline "
                f"{earlier_method.recall:.4f}",
            )
        slack_floor: float = (
            earlier_method.precision - limits.method_precision_slack
        )
        if method.precision < slack_floor:
            problems.append(
                f"method precision {method.precision:.4f} fell below the "
                f"baseline {earlier_method.precision:.4f} by more than "
                f"{limits.method_precision_slack:.4f}",
            )
    return tuple(problems)
