"""Heartbeat lifecycle, idle liveness and CPU-default benchmark execution."""

from __future__ import annotations

from json import loads
from threading import Event
from threading import enumerate as enumerate_threads
from time import monotonic
from typing import TYPE_CHECKING, cast

import pytest
from astart.source.metrics import metrics

from scripts.benchmark import cli
from scripts.benchmark.activity import Activity
from scripts.benchmark.cli import parser
from scripts.benchmark.runner import Plan, run_recovery
from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.benchmark.report import Report


def test_heartbeat_updates_while_command_is_idle(
    *,
    tmp_path: Path,
) -> None:
    """An independent beat advances even without module completions.

    Args:
        tmp_path (Path): Isolated activity artifacts.

    """
    beat: Event = Event()
    with Activity(
        directory=tmp_path,
        command="recovery",
        interval=0.01,
    ) as activity:
        activity.progress(completed=1, total=3, current="example.py")
        initial: str = loads(s=(tmp_path / "@activity.json").read_text())[
            "updated_at"
        ]
        deadline: float = monotonic() + 2.0
        data: dict[str, object] = loads(
            s=(tmp_path / "@activity.json").read_text(),
        )
        while data["updated_at"] == initial and monotonic() < deadline:
            _ = beat.wait(timeout=0.01)
            data = loads(s=(tmp_path / "@activity.json").read_text())
        heartbeat: dict[str, object] = cast(
            typ="dict[str, object]",
            val=data["heartbeat"],
        )
        progress: dict[str, object] = cast(
            typ="dict[str, object]",
            val=data["progress"],
        )
        expect_true(condition=data["updated_at"] != initial)
        expect_equal(actual=heartbeat["alive"], expected=True)
        expect_equal(actual=progress["completed"], expected=1)
    data = loads(s=(tmp_path / "@activity.json").read_text())
    last_heartbeat: dict[str, object] = cast(
        typ="dict[str, object]",
        val=data["heartbeat"],
    )
    expect_equal(actual=data["status"], expected="completed")
    expect_equal(actual=last_heartbeat["alive"], expected=False)
    expect_true(
        condition=all(
            thread.name != "benchmark-heartbeat"
            for thread in enumerate_threads()
        ),
    )


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_failed_activity_closes_heartbeat(
    *,
    tmp_path: Path,
    failure: type[RuntimeError | KeyboardInterrupt],
) -> None:
    """Errors and cancellation preserve final status and stop the thread.

    Args:
        tmp_path (Path): Isolated activity artifacts.
        failure (type[RuntimeError | KeyboardInterrupt]): Failure or
            cancellation to propagate.

    Raises:
        failure: TODO.

    """
    with (
        pytest.raises(expected_exception=failure),
        Activity(directory=tmp_path, command="test"),
    ):
        raise failure
    data: dict[str, object] = loads(
        s=(tmp_path / "@activity.json").read_text(),
    )
    heartbeat: dict[str, object] = cast(
        typ="dict[str, object]",
        val=data["heartbeat"],
    )
    expect_equal(
        actual=data["status"],
        expected=("interrupted" if failure is KeyboardInterrupt else "failed"),
    )
    expect_equal(actual=heartbeat["alive"], expected=False)
    expect_true(condition=data["finished_at"] is not None)


def test_jobs_default_to_available_cpu_count(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CPU default remains overridable for reproducible serial runs.

    Args:
        monkeypatch (pytest.MonkeyPatch): Deterministic available CPU count.

    """
    monkeypatch.setattr(
        target=cli,
        name="process_cpu_count",
        value=lambda: 3,
    )
    expect_equal(
        actual=parser().parse_args(args=["recovery"]).jobs,
        expected=3,
    )
    expect_equal(
        actual=parser().parse_args(args=["recovery", "--jobs", "1"]).jobs,
        expected=1,
    )


def test_parallel_recovery_preserves_order_and_worker_sensors(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parallel measurements match serial scores and retain worker evidence.

    Args:
        tmp_path (Path): Isolated tiny corpus.
        monkeypatch (pytest.MonkeyPatch): Enable worker sensor collection.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    paths: list[Path] = [tmp_path / "b.py", tmp_path / "a.py"]
    for path in paths:
        _ = path.write_text(
            data="""\
def value() -> int:
    return 1
""",
        )
    metrics.reset()
    serial: Report = run_recovery(
        paths=paths,
        plan=Plan(jobs=1, attribute=False, negotiate=False),
    )
    parallel: Report = run_recovery(
        paths=paths,
        plan=Plan(jobs=2, attribute=False, negotiate=False),
    )
    expect_equal(
        actual=[item.name for item in parallel.modules],
        expected=[item.name for item in serial.modules],
    )
    expect_equal(actual=parallel.correct, expected=serial.correct)
    expect_equal(actual=parallel.wrong, expected=serial.wrong)
    expect_equal(actual=parallel.truth, expected=serial.truth)
    expect_true(
        condition=all(
            f"worker:{path.name}" in metrics.root.children for path in paths
        ),
    )
    expect_true(condition=bool(metrics.snapshot()))
    metrics.reset()
