"""The untyped-to-typed conversion benchmark keeps its accepted baseline."""

from __future__ import annotations

from json import dumps
from sys import modules
from types import ModuleType
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules.recovery import variable_map

from scripts.compare.pair import (
    ACCEPTED_DEVIATIONS_PATH,
    Mode,
    baseline_drift,
    compare,
    gate,
    load_accepted_deviations,
)
from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

type DictDictInt = dict[str, dict[str, int]]

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Constants used in the test_bench_pair module.

    Attributes:
        pairs (Final[Path]): Directory holding the typed/untyped fixture pairs.
        baseline_correct (Final[int]): Correct annotations the stored baseline
            records.
        most_contradictions (Final[int]): Most contradictions tolerated before
            failing.

    """

    pairs: Final[Path] = Paths.fixtures
    baseline_correct: Final[int] = 71
    most_contradictions: Final[int] = 2


def _read(*, name: str) -> str:
    """Read one half of the pair.

    Args:
        name (str): File name inside ``fixtures``.

    Returns:
        str: The file text.

    """
    return (Constants.pairs / name).read_text(encoding="utf-8")


def test_variable_map_reads_annotated_names_by_scope() -> None:
    """Check that variable annotations are keyed by their scope."""
    found: dict[str, str] = variable_map(
        source=(
            """\
x: int = 1
def f():
    y: str = ''
class C:
    z: float
"""
        ),
    )
    expect_equal(
        actual=found,
        expected={"x": "int", "f.y": "str", "C.z": "float"},
    )


@pytest.mark.slow
def test_conversion_never_regresses_and_never_contradicts() -> None:
    """Check recall stays at the baseline and nothing contradicts the twin."""
    result: DictDictInt = compare(
        untyped=_read(name="untyped.py"),
        typed=_read(name="typed.py"),
        mode=Mode(floor=0.8),
    )
    recovered: dict[str, int] = result["parameters_and_returns"]
    expect_true(condition=recovered["correct"] >= Constants.baseline_correct)
    expect_true(
        condition=recovered.get("wrong", 0) <= Constants.most_contradictions,
    )


def test_an_accepted_deviation_counts_as_accepted() -> None:
    """Check a reviewer-approved difference scores ``accepted``, not wrong."""
    result: DictDictInt = compare(
        untyped="""\
def f(x):
    return x + 1
""",
        typed="""\
def f(x: float) -> float:
    return x + 1
""",
        mode=Mode(floor=0.5, engine=True),
        accepted=[
            {
                "pair": "test",
                "node": "f.x",
                "wrote": "SupportsAddition",
                "author": "float",
                "reason": (
                    "the fixer synthesizes a structural protocol for ``x``; "
                    "float is the author's wider spelling"
                ),
            },
        ],
    )
    recovered: dict[str, int] = result["parameters_and_returns"]
    expect_equal(actual=recovered["accepted"], expected=1)
    expect_equal(actual=recovered.get("narrower", 0), expected=1)


def test_accepted_deviations_require_a_reason() -> None:
    """Check entries without a reviewer reason are rejected."""
    path: Path = Constants.pairs / "_tmp_accepted.json"
    path.write_text(
        data='[{"pair": "t", "node": "f.x", "wrote": "int", '
        '"author": "float", "reason": "  "}]\n',
        encoding="utf-8",
    )
    try:
        with pytest.raises(
            expected_exception=ValueError,
            match="empty reason",
        ):
            _ = load_accepted_deviations(path=path)
    finally:
        path.unlink()


def test_shipped_accepted_deviations_all_have_reasons() -> None:
    """Check the checked-in deviation list loads cleanly."""
    entries: list[dict[str, str]] = load_accepted_deviations(
        path=ACCEPTED_DEVIATIONS_PATH,
    )
    expect_true(condition=all(entry["reason"].strip() for entry in entries))


def test_baseline_drift_flags_lower_recall_and_new_contradictions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check the gate fails on dropped scores or missing buckets.

    Args:
        capsys (pytest.CaptureFixture[str]): pytest stream capture.

    """
    stored: dict[str, DictDictInt] = {
        "dev": {"parameters_and_returns": {"correct": 10, "wrong": 0}},
    }
    same: dict[str, DictDictInt] = {
        "dev": {"parameters_and_returns": {"correct": 10, "wrong": 0}},
    }
    expect_equal(
        actual=baseline_drift(results=same, stored=stored),
        expected=False,
    )
    worse: dict[str, DictDictInt] = {
        "dev": {"parameters_and_returns": {"correct": 9, "wrong": 1}},
    }
    expect_equal(
        actual=baseline_drift(results=worse, stored=stored),
        expected=True,
    )
    missing_bucket: dict[str, DictDictInt] = {
        "dev": {"parameters_and_returns": {"correct": 10}},
    }
    expect_equal(
        actual=baseline_drift(results=missing_bucket, stored=stored),
        expected=True,
    )
    _ = capsys.readouterr()


@pytest.mark.slow
def test_gate_writes_then_enforces_the_pair_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check ``--gate`` accepts stored numbers and fails on drift.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): pytest monkeypatch fixture.

    """

    def _untype_identity(*, source: str) -> str:
        """Stand in for ``untype_source`` returning its input unchanged.

        Args:
            source (str): Module source text.

        Returns:
            str: The source, unmodified.

        """
        return source

    fake: ModuleType = ModuleType(name="astart.rules.untype")
    untype_source_name: str = "untype_source"
    setattr(fake, untype_source_name, _untype_identity)
    monkeypatch.setitem(dic=modules, name="astart.rules.untype", value=fake)
    baseline: Path = tmp_path / "baseline_pair.json"
    expect_equal(
        actual=gate(baseline=baseline, mode=Mode(floor=0.8)),
        expected=0,
    )
    expect_true(condition=baseline.is_file())
    expect_equal(
        actual=gate(baseline=baseline, mode=Mode(floor=0.8)),
        expected=0,
    )
    _ = baseline.write_text(
        data=dumps(obj={"dev": {"variables": {"correct": -1}}}) + "\n",
        encoding="utf-8",
    )
    expect_equal(
        actual=gate(baseline=baseline, mode=Mode(floor=0.8)),
        expected=1,
    )
