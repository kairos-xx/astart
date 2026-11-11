"""The benchmark harness end to end on a tiny corpus."""

from __future__ import annotations

from io import StringIO
from json import dumps, loads
from typing import TYPE_CHECKING, Final, TypedDict, cast

import pytest

from scripts.benchmark import paths as benchmark_paths
from scripts.benchmark.cli import main, provenance_stamp
from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from pathlib import Path


class _SummaryJson(TypedDict):
    """The ``summary`` member of a serialized report.

    Attributes:
        modules (int): Number of measured modules.
        crashed (list[str]): Names of modules that crashed.
        precision (float): Fraction of annotations recovered correctly.
        rounds (int): Fix-pass count histogram.

    """

    modules: int
    crashed: list[str]
    precision: float
    rounds: int


class _ModuleJson(TypedDict):
    """One module entry in a serialized report.

    Attributes:
        name (str): Module file name.
        correct (int): Annotations recovered equal to the original.
        truth (int): Annotations the original had.

    """

    name: str
    correct: int
    truth: int


class _ReportJson(TypedDict):
    """The parts of a serialized report the tests read.

    Attributes:
        summary (_SummaryJson): Aggregate metrics.
        modules (list[_ModuleJson]): One entry per measured module.

    """

    summary: _SummaryJson
    modules: list[_ModuleJson]


TYPED: Final[str] = """\
def total(items: list[int], scale: int = 2) -> int:
    return sum(items) * scale


def shout(name: str) -> str:
    return name.upper()
"""

STAMP_HEX_LEN: Final[int] = 12


def _corpus(*, tmp_path: Path) -> Path:
    """Build a tiny two-module corpus under ``tmp_path``.

    Args:
        tmp_path (Path): pytest temporary directory.

    Returns:
        Path: The corpus directory.

    """
    corpus: Path = tmp_path / "corpus"
    corpus.mkdir()
    _ = (corpus / "mod_a.py").write_text(data=TYPED, encoding="utf-8")
    _ = (corpus / "mod_b.py").write_text(
        data="""\
def one() -> int:
    return 1
""",
        encoding="utf-8",
    )
    return corpus


@pytest.fixture(autouse=True)
def isolated_artifacts(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Redirect benchmark artifacts away from the repository.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): pytest fixture patching artifact
            locations.

    """
    monkeypatch.setattr(
        target=benchmark_paths.Paths,
        name="results",
        value=tmp_path / "artifacts",
    )


def test_recovery_writes_a_json_report(*, tmp_path: Path) -> None:
    """Check that recovery writes a json report.

    Args:
        tmp_path (Path): pytest temporary directory.

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
        expected=["mod_a.py", "mod_b.py"],
    )


def test_gate_passes_against_itself_and_fails_on_a_regression(
    *,
    tmp_path: Path,
) -> None:
    """Check that gate passes against itself and fails on a regression.

    Args:
        tmp_path (Path): pytest temporary directory.

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
    log: Path = tmp_path / "baseline_log.md"
    expect_equal(
        actual=main(
            argv=[
                "baseline",
                "--report",
                str(object=report),
                "--out",
                str(object=baseline),
                "--reason",
                "test accept",
                "--log",
                str(object=log),
            ],
        ),
        expected=0,
    )
    expect_in(item="test accept", container=log.read_text(encoding="utf-8"))
    gate: list[str] = [
        "gate",
        "--report",
        str(object=report),
        "--log",
        str(object=log),
    ]
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


def test_baseline_requires_a_reason(*, tmp_path: Path) -> None:
    """Check that ``baseline`` refuses to run without ``--reason``.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    report: Path = tmp_path / "report.json"
    _ = report.write_text(data="{}", encoding="utf-8")
    with pytest.raises(expected_exception=SystemExit) as caught:
        _ = main(
            argv=[
                "baseline",
                "--report",
                str(object=report),
                "--out",
                str(object=tmp_path / "baseline.json"),
            ],
        )
    expect_equal(actual=caught.value.code, expected=2)


def test_gate_prints_the_last_baseline_entry_on_failure(
    *,
    tmp_path: Path,
) -> None:
    """Check that a failing gate echoes the latest logged change.

    Args:
        tmp_path (Path): pytest temporary directory.

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
    log: Path = tmp_path / "baseline_log.md"
    _ = main(
        argv=[
            "baseline",
            "--report",
            str(object=report),
            "--out",
            str(object=baseline),
            "--reason",
            "first accept",
            "--log",
            str(object=log),
        ],
    )
    worse: _ReportJson = loads(s=baseline.read_text(encoding="utf-8"))
    for item in worse["modules"]:
        item["correct"] += 5
        item["truth"] += 5
    strict: Path = tmp_path / "strict.json"
    _ = strict.write_text(data=dumps(obj=worse), encoding="utf-8")
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=report),
                "--baseline",
                str(object=strict),
                "--log",
                str(object=log),
            ],
            out=out,
        ),
        expected=1,
    )
    expect_in(item="FAIL", container=out.getvalue())
    expect_in(item="last baseline change:", container=out.getvalue())
    expect_in(item="first accept", container=out.getvalue())


def test_recovery_stamps_tree_hash_and_corpus(*, tmp_path: Path) -> None:
    """Check that recovery reports carry provenance.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    report: Path = tmp_path / "report.json"
    expect_equal(
        actual=main(
            argv=[
                "recovery",
                "--corpus",
                str(object=_corpus(tmp_path=tmp_path)),
                "--json",
                str(object=report),
            ],
        ),
        expected=0,
    )
    summary: dict[str, object] = loads(
        s=report.read_text(encoding="utf-8"),
    )["summary"]
    stamp: object = summary["tree_hash"]
    expect_true(
        condition=isinstance(stamp, str) and len(stamp) == STAMP_HEX_LEN,
        message=f"tree_hash: {stamp!r}",
    )
    expect_equal(actual=summary["corpus"], expected="corpus")


def test_gate_rejects_a_stale_report(*, tmp_path: Path) -> None:
    """Check that a report from another tree never prints PASS.

    Args:
        tmp_path (Path): pytest temporary directory.

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
    document: dict[str, object] = loads(
        s=report.read_text(encoding="utf-8"),
    )
    summary: dict[str, object] = cast(
        typ="dict[str, object]",
        val=document["summary"],
    )
    summary["tree_hash"] = "deadbeef0000"
    _ = report.write_text(data=dumps(obj=document), encoding="utf-8")
    baseline: Path = tmp_path / "baseline.json"
    _ = baseline.write_text(
        data=report.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    out: StringIO = StringIO()
    expect_equal(
        actual=main(
            argv=[
                "gate",
                "--report",
                str(object=report),
                "--baseline",
                str(object=baseline),
                "--log",
                str(object=tmp_path / "log.md"),
            ],
            out=out,
        ),
        expected=1,
    )
    expect_in(item="stale report", container=out.getvalue())
    expect_in(item="FAIL", container=out.getvalue())


def test_targets_stamp_names_tree_corpus_and_date(
    *,
    tmp_path: Path,
) -> None:
    """Check the provenance stamp identifies tree, corpus and day.

    Args:
        tmp_path (Path): pytest temporary directory holding fake reports.

    """
    reports: Path = tmp_path / "reports"
    reports.mkdir()
    for name in ("recovery_std_x.json", "recovery_ext_y.json"):
        _ = (reports / name).write_text(data="{}", encoding="utf-8")
    stamp: str = provenance_stamp(report_dir=reports)
    expect_in(item="tree ", container=stamp)
    expect_in(item="corpus stdlib+external", container=stamp)
    expect_in(item="· 20", container=stamp)
