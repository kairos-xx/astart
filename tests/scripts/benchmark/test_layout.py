"""Benchmark ownership, artifact defaults and shared instrumentation."""

from __future__ import annotations

from io import StringIO
from json import loads
from os import utime
from typing import TYPE_CHECKING, cast

from astart.source.metrics import metrics

from scripts.benchmark import cli, sensors
from scripts.benchmark.paths import Paths, write_artifact
from scripts.benchmark.targets import collect
from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path
    from typing import TextIO

    import pytest

    from scripts.benchmark.activity import Activity


def test_artifacts_are_independent_of_working_directory(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default output uses the benchmark artifact directory.

    Args:
        tmp_path (Path): Isolated destinations.
        monkeypatch (pytest.MonkeyPatch): Temporary artifact configuration and
            working directory.

    """
    destination: Path = tmp_path / "artifacts"
    monkeypatch.setattr(target=Paths, name="results", value=destination)
    monkeypatch.chdir(path=tmp_path)
    actual: Path = write_artifact(
        name="sample.json",
        text="""\
{}
""",
    )
    expect_equal(actual=actual, expected=destination / "sample.json")
    explicit: Path = tmp_path / "explicit" / "chosen.json"
    expect_equal(
        actual=write_artifact(name="unused.json", text="{}", output=explicit),
        expected=explicit,
    )


def test_benchmark_and_cli_share_one_sensor_registry(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sensor artifacts serialize the same recorder used by the CLI.

    Args:
        tmp_path (Path): Isolated sensor artifacts.
        monkeypatch (pytest.MonkeyPatch): Enable scoped collection.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    metrics.reset()
    expect_true(condition=sensors.metrics is metrics)
    with sensors.timed(label="test.phase"):
        pass
    sensors.dump(directory=tmp_path)
    data: dict[str, object] = loads(
        s=(tmp_path / "sensors.json").read_text(encoding="utf-8"),
    )
    stats: dict[str, dict[str, dict[str, int]]] = cast(
        typ="dict[str, dict[str, dict[str, int]]]",
        val=data["stats"],
    )
    expect_equal(actual=stats["test.phase"]["calls"], expected=1)
    expect_true(condition=(tmp_path / "sensors.txt").is_file())
    metrics.reset()


def test_accepted_baseline_is_not_current_recovery_evidence(
    tmp_path: Path,
) -> None:
    """A newer baseline file must not replace a measured corpus report.

    Args:
        tmp_path (Path): Isolated report and baseline files.

    """
    report: Path = tmp_path / "recovery-ext.json"
    baseline: Path = tmp_path / "baseline_ext.json"
    report.write_text(data='{"summary": {"precision": 1.0}}', encoding="utf-8")
    baseline.write_text(
        data='{"summary": {"precision": 0.0}}',
        encoding="utf-8",
    )
    utime(path=report, times=(1, 1))
    utime(path=baseline, times=(2, 2))
    result: dict[str, float] = collect(
        report_dir=tmp_path,
        metrics={"recovery.ext.precision"},
    )
    expect_equal(actual=result["recovery.ext.precision"], expected=1.0)


def test_recovery_saves_default_artifact_and_preserves_stdout(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One small recovery run writes the report pair and keeps stdout.

    Args:
        tmp_path (Path): Isolated corpus and artifacts.
        monkeypatch (pytest.MonkeyPatch): Artifact destination and disabled
            instrumentation.

    """
    corpus: Path = tmp_path / "small"
    corpus.mkdir()
    (corpus / "example.py").write_text(
        data="""\
def value() -> int:
    return 1
""",
        encoding="utf-8",
    )
    output: Path = tmp_path / "artifacts"
    monkeypatch.setattr(target=Paths, name="results", value=output)
    monkeypatch.setenv(name="ASTART_SENSORS", value="0")
    stream: StringIO = StringIO()
    expect_equal(
        actual=cli.main(
            argv=["recovery", "--corpus", str(object=corpus)],
            out=stream,
        ),
        expected=0,
    )
    document: dict[str, object] = loads(
        s=(output / "report.json").read_text(encoding="utf-8"),
    )
    tools: dict[str, dict[str, object]] = cast(
        typ="dict[str, dict[str, object]]",
        val=document["tools"],
    )
    saved: dict[str, object] = tools["recovery.small"]
    expect_equal(actual=loads(s=stream.getvalue()), expected=saved)
    expect_true(condition=(output / "report.md").is_file())


def test_bare_invocation_dispatches_every_suite_tool(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bare run executes each self-contained tool under one activity.

    Args:
        tmp_path (Path): Isolated activity artifacts.
        monkeypatch (pytest.MonkeyPatch): Artifact destination and dispatch
            spy.

    """
    output: Path = tmp_path / "artifacts"
    monkeypatch.setattr(target=Paths, name="results", value=output)
    seen: list[str] = []

    def fake_dispatch(
        *,
        args: Namespace,
        out: TextIO,
        activity: Activity,
    ) -> int:
        """Record the dispatched command name.

        Args:
            args (Namespace): Parsed benchmark options.
            out (TextIO): Report output stream.
            activity (Activity): Live run progress.

        Returns:
            int: Zero.

        """
        _ = out, activity
        seen.append(args.command)
        return 0

    monkeypatch.setattr(target=cli, name="_dispatch", value=fake_dispatch)
    stream: StringIO = StringIO()
    expect_equal(actual=cli.main(argv=[], out=stream), expected=0)
    expect_equal(actual=seen, expected=list(cli.Constants.suite))
    expect_true(condition=(output / "@activity.json").is_file())
