"""The benchmark harness end to end on a tiny corpus."""

from __future__ import annotations

from io import StringIO
from json import dumps, loads
from typing import TYPE_CHECKING, Final, TypedDict

from benchmarks.__main__ import main
from tests.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from pathlib import Path


class _SummaryJson(TypedDict):
    """The ``summary`` member of a serialized report.

    Attributes:
        modules: Number of measured modules.
        crashed: Names of modules that crashed.
        precision: Fraction of annotations recovered correctly.
        rounds: Fix-pass count histogram.

    """

    modules: int
    crashed: list[str]
    precision: float
    rounds: int


class _ModuleJson(TypedDict):
    """One module entry in a serialized report.

    Attributes:
        name: Module file name.
        correct: Annotations recovered equal to the original.
        truth: Annotations the original had.

    """

    name: str
    correct: int
    truth: int


class _ReportJson(TypedDict):
    """The parts of a serialized report the tests read.

    Attributes:
        summary: Aggregate metrics.
        modules: One entry per measured module.

    """

    summary: _SummaryJson
    modules: list[_ModuleJson]


TYPED: Final[str] = (
    "def total(items: list[int], scale: int = 2) -> int:\n"
    "    return sum(items) * scale\n\n\n"
    "def shout(name: str) -> str:\n    return name.upper()\n"
)


def _corpus(*, tmp_path: Path) -> Path:
    """Build a tiny two-module corpus under ``tmp_path``.

    Args:
        tmp_path: pytest temporary directory.

    Returns:
        The corpus directory.

    """
    corpus: Path = tmp_path / "corpus"
    corpus.mkdir()
    _ = (corpus / "mod_a.py.txt").write_text(data=TYPED, encoding="utf-8")
    _ = (corpus / "mod_b.py.txt").write_text(
        data="def one() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    return corpus


def test_recovery_writes_a_json_report(*, tmp_path: Path) -> None:
    """Check that recovery writes a json report.

    Args:
        tmp_path: pytest temporary directory.

    """
    report: Path = tmp_path / "report.json"
    code: int = main(
        argv=[
            "recovery",
            "--corpus",
            str(object=_corpus(tmp_path=tmp_path)),
            "--json",
            str(object=report),
        ],
    )
    expect_equal(actual=code, expected=0)
    data: _ReportJson = loads(s=report.read_text(encoding="utf-8"))
    expect_equal(actual=data["summary"]["modules"], expected=2)
    expect_equal(actual=data["summary"]["crashed"], expected=[])
    expect_equal(actual=data["summary"]["precision"], expected=1.0)
    expect_in(item="rounds", container=data["summary"])
    expect_equal(
        actual=[item["name"] for item in data["modules"]],
        expected=["mod_a.py.txt", "mod_b.py.txt"],
    )


def test_gate_passes_against_itself_and_fails_on_a_regression(
    *,
    tmp_path: Path,
) -> None:
    """Check that gate passes against itself and fails on a regression.

    Args:
        tmp_path: pytest temporary directory.

    """
    corpus: Path = _corpus(tmp_path=tmp_path)
    report: Path = tmp_path / "report.json"
    _ = main(
        argv=[
            "recovery",
            "--corpus",
            str(object=corpus),
            "--json",
            str(object=report),
        ],
    )
    baseline: Path = tmp_path / "baseline.json"
    expect_equal(
        actual=main(
            argv=[
                "baseline",
                "--report",
                str(object=report),
                "--out",
                str(object=baseline),
            ],
        ),
        expected=0,
    )
    gate: list[str] = ["gate", "--report", str(object=report)]
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[*gate, "--baseline", str(object=baseline)],
            out=out,
        ),
        expected=0,
    )
    expect_in(item="PASS", container=out.getvalue())
    worse: _ReportJson = loads(s=baseline.read_text(encoding="utf-8"))
    for item in worse["modules"]:
        item["correct"] += 5
        item["truth"] += 5
    strict: Path = tmp_path / "strict.json"
    _ = strict.write_text(data=dumps(obj=worse), encoding="utf-8")
    expect_equal(
        actual=main(
            argv=[*gate, "--baseline", str(object=strict)],
            out=out,
        ),
        expected=1,
    )
    expect_in(item="FAIL", container=out.getvalue())
