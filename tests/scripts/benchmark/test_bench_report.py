"""The benchmark report, its JSON form and the regression gate."""

from __future__ import annotations

from json import loads
from typing import TYPE_CHECKING, TypedDict

from scripts.benchmark.report import (
    ModuleResult,
    Report,
    Thresholds,
    compare,
    from_json,
    to_json,
)
from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


class _ModuleJson(TypedDict):
    """One module entry in a serialized report.

    Attributes:
        name (str): Module file name.

    """

    name: str


class _ReportJson(TypedDict):
    """The parts of a serialized report the tests read.

    Attributes:
        modules (list[_ModuleJson]): One entry per measured module.
        summary (dict[str, JsonValue]): Aggregate metrics.

    """

    summary: dict[str, JsonValue]
    modules: list[_ModuleJson]


def _module(
    *,
    name: str = "a.py",
    truth: int = 10,
    correct: int = 4,
    wrong: tuple[str, ...] = (),
    rounds: int = 2,
) -> ModuleResult:
    """Build a ``ModuleResult`` with the given counts.

    Args:
        name (str): Module file name.
        truth (int): Annotations the original had.
        correct (int): Annotations recovered equal to the original.
        wrong (tuple[str, ...]): Annotation names written that differ.
        rounds (int): Fix passes needed.

    Returns:
        ModuleResult: The module result.

    """
    return ModuleResult(
        name=name,
        truth=truth,
        correct=correct,
        wrong=wrong,
        synthesized=1,
        seconds=0.5,
        rounds=rounds,
        missed_reasons=(("uncorroborated", 3),),
        new_errors=None,
        crash=None,
    )


def test_report_totals_precision_and_recall() -> None:
    """Check that report totals precision and recall."""
    report: Report = Report.of(
        modules=[
            _module(name="a.py", truth=10, correct=4),
            _module(name="b.py", truth=10, correct=6, wrong=("b: x",)),
        ],
    )
    expect_equal(actual=report.truth, expected=20)
    expect_equal(actual=report.correct, expected=10)
    expect_equal(actual=report.precision, expected=10 / 11)
    expect_equal(actual=report.recall, expected=0.5)
    expect_equal(
        actual=dict(report.missed_reasons),
        expected={"uncorroborated": 6},
    )
    expect_equal(actual=report.rounds_histogram, expected=((2, 2),))


def test_json_round_trips() -> None:
    """Check that json round trips."""
    report: Report = Report.of(
        modules=[_module(), _module(name="c.py", rounds=3)],
    )
    text: str = to_json(report=report)
    data: _ReportJson = loads(s=text)
    expect_in(item="precision", container=data["summary"])
    expect_equal(actual=data["modules"][0]["name"], expected="a.py")
    expect_equal(actual=from_json(text=text), expected=report)


def test_gate_flags_every_breach() -> None:
    """Check that gate flags every breach."""
    good: Report = Report.of(modules=[_module(truth=10, correct=5)])
    expect_equal(
        actual=compare(report=good, baseline=good, limits=Thresholds()),
        expected=(),
    )
    bad: Report = Report.of(
        modules=[
            ModuleResult(
                name="a.py",
                truth=10,
                correct=3,
                wrong=("a: x",),
                synthesized=0,
                seconds=1.0,
                rounds=5,
                missed_reasons=(),
                new_errors=2,
                crash=None,
            ),
            ModuleResult(
                name="b.py",
                truth=0,
                correct=0,
                wrong=(),
                synthesized=0,
                seconds=0.1,
                rounds=1,
                missed_reasons=(),
                new_errors=None,
                crash="IndexError: boom",
            ),
        ],
    )
    problems: tuple[str, ...] = compare(
        report=bad,
        baseline=good,
        limits=Thresholds(),
    )
    text: str = " | ".join(problems)
    for needle in ("precision", "recall", "crash", "rounds", "new errors"):
        expect_true(condition=needle in text, message=f"{needle}: {text}")


def test_stamp_round_trips() -> None:
    """Check that the tree hash and corpus survive JSON."""
    report: Report = Report.of(
        modules=[_module()],
        tree_hash="abc123def456",
        corpus="corpus_ext",
    )
    data: _ReportJson = loads(s=to_json(report=report))
    expect_equal(actual=data["summary"]["tree_hash"], expected="abc123def456")
    expect_equal(actual=data["summary"]["corpus"], expected="corpus_ext")
    expect_equal(
        actual=from_json(text=to_json(report=report)),
        expected=report,
    )


def test_unstamped_reports_still_round_trip() -> None:
    """Check that pre-stamp JSON loads with empty provenance."""
    text: str = to_json(report=Report.of(modules=[_module()]))
    data: _ReportJson = loads(s=text)
    expect_equal(actual=data["summary"]["tree_hash"], expected="")
    expect_equal(actual=data["summary"]["corpus"], expected="")
