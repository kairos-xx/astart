"""Readable benchmark reports retain measurements and sensor evidence."""

from __future__ import annotations

from json import loads
from typing import TYPE_CHECKING, cast

from astart.source.metrics import metrics

from scripts.benchmark.paths import Paths
from scripts.benchmark.presentation import publish
from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_reports_include_sensor_evidence(*, tmp_path: Path) -> None:
    """Both report formats expose measurements and collected timings.

    Args:
        tmp_path (Path): Isolated artifact destination.

    """
    metrics.reset()
    metrics.record(
        label="phase|infer",
        wall_ns=2_000_000,
        cpu_ns=1_000_000,
        error=True,
    )
    destination: Path = tmp_path / "run.json"
    text: str = publish(
        name="unused.json",
        output=destination,
        text='{"summary": {"correct": 3}, "modules": []}',
    )
    expect_equal(actual=loads(s=text)["summary"]["correct"], expected=3)
    expect_equal(
        actual=loads(s=text)["sensors"]["stats"]["phase|infer"]["errors"],
        expected=1,
    )
    markdown: str = destination.with_suffix(suffix=".md").read_text()
    expect_in(item="phase\\|infer", container=markdown)
    expect_in(item="Measured call paths", container=markdown)
    expect_in(item="nested calls", container=markdown)
    expect_equal(actual=destination.read_text(), expected=text)
    metrics.reset()


def test_empty_sensors_are_explicit(*, tmp_path: Path) -> None:
    """An uninstrumented result does not invent timing evidence.

    Args:
        tmp_path (Path): Isolated artifact destination.

    """
    metrics.reset()
    destination: Path = tmp_path / "empty.json"
    _ = publish(name="empty.json", text="[]", output=destination)
    expect_in(
        item="No sensor samples",
        container=destination.with_suffix(suffix=".md").read_text(),
    )


def test_default_publish_merges_into_consolidated_report(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default publish accumulates ``tool[.variant]`` report sections.

    Args:
        tmp_path (Path): Isolated artifact destination.
        monkeypatch (pytest.MonkeyPatch): Artifact destination.

    """
    destination: Path = tmp_path / "artifacts"
    monkeypatch.setattr(target=Paths, name="results", value=destination)
    metrics.reset()
    text: str = publish(
        name="ignored.json",
        text='{"summary": {"correct": 3}}',
        tool="recovery",
        variant="small",
    )
    document: dict[str, object] = loads(
        s=(destination / "report.json").read_text(encoding="utf-8"),
    )
    tools: dict[str, dict[str, object]] = cast(
        typ="dict[str, dict[str, object]]",
        val=document["tools"],
    )
    expect_equal(actual=tools["recovery.small"], expected=loads(s=text))
    expect_equal(actual=document["schema_version"], expected=1)
    expect_true(condition=bool(document["tree"]))
    expect_true(condition=bool(document["generated"]))
    _ = publish(name="gate.json", text='{"passed": true}', tool="gate")
    refreshed: dict[str, object] = loads(
        s=(destination / "report.json").read_text(encoding="utf-8"),
    )
    merged: dict[str, dict[str, object]] = cast(
        typ="dict[str, dict[str, object]]",
        val=refreshed["tools"],
    )
    expect_equal(
        actual=sorted(merged),
        expected=["gate", "recovery.small"],
    )
    markdown: str = (destination / "report.md").read_text(encoding="utf-8")
    expect_in(item="Recovery — small", container=markdown)
    expect_in(item="Gate", container=markdown)
    expect_in(item="report.json", container=markdown)
    metrics.reset()


def test_explicit_output_stays_out_of_consolidated_report(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit ``--json`` destination never touches ``report.*``.

    Args:
        tmp_path (Path): Isolated artifact destination.
        monkeypatch (pytest.MonkeyPatch): Artifact destination.

    """
    destination: Path = tmp_path / "artifacts"
    monkeypatch.setattr(target=Paths, name="results", value=destination)
    metrics.reset()
    explicit: Path = tmp_path / "custom" / "chosen.json"
    _ = publish(
        name="ignored.json",
        text='{"ok": true}',
        output=explicit,
        tool="gate",
    )
    expect_true(condition=explicit.is_file())
    expect_true(condition=explicit.with_suffix(suffix=".md").is_file())
    expect_false(
        condition=(destination / "report.json").exists(),
    )
    metrics.reset()
