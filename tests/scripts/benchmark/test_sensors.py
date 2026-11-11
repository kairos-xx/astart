"""Verify the decorator-based execution sensors."""

from __future__ import annotations

from io import StringIO
from types import ModuleType
from typing import TYPE_CHECKING, Final

from astart.source import metrics as sensors
from astart.source.metrics import (
    Stat,
    TraceNode,
    instrument,
    report,
    sensor,
    timed,
    trace_report,
)

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    import pytest


def test_sensor_records_calls_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that a wrapped function's calls are timed.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()

    @sensor
    def work() -> int:
        """Return a constant.

        Returns:
            int: The constant 42.

        """
        return 42

    result1: int = work()
    result2: int = work()
    expect_equal(actual=result1, expected=42)
    expect_equal(actual=result2, expected=42)
    label: str = (
        f"{test_sensor_records_calls_when_enabled.__module__}"
        ".test_sensor_records_calls_when_enabled.<locals>.work"
    )
    expect_equal(actual=sensors.metrics.snapshot()[label].calls, expected=2)


def test_sensor_uses_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that an explicit label names the sensor.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()

    @sensor(label="labelled.work")
    def work() -> int:
        """Return a constant.

        Returns:
            int: The constant 42.

        """
        return 42

    work()
    stat: Stat = sensors.metrics.snapshot()["labelled.work"]
    expect_equal(actual=stat.calls, expected=1)
    expect_true(condition=stat.wall_ns >= 0)


def test_disabled_sensor_skips_recording(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that a disabled sensor records nothing.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.delenv(name="ASTART_SENSORS", raising=False)
    sensors.metrics.reset()

    @sensor(label="off.work")
    def work() -> int:
        """Return a constant.

        Returns:
            int: The constant 42.

        """
        return 42

    work()
    expect_equal(actual=dict(sensors.metrics.snapshot()), expected={})


def test_timed_block_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that a timed block is recorded.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()
    with timed(label="block.phase"):
        total: int = sum(range(1000))
    expect_true(condition=total > 0)
    expect_equal(
        actual=sensors.metrics.snapshot()["block.phase"].calls,
        expected=1,
    )


def test_instrument_wraps_module_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that instrument wraps every function on a module.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()
    module: ModuleType = ModuleType(name="fake_mod")
    helper_name: str = "helper"

    def helper() -> int:
        """Return a constant.

        Returns:
            int: The constant 7.

        """
        return 7

    setattr(module, helper_name, helper)
    expect_equal(actual=instrument(module=module), expected=1)
    module.helper()
    expect_equal(
        actual=sensors.metrics.snapshot()["fake_mod.helper"].calls,
        expected=1,
    )


def test_report_renders_sorted_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that report renders slowest-first rows.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()
    sensors.metrics.record(label="fast", wall_ns=10, cpu_ns=10)
    sensors.metrics.record(label="slow", wall_ns=100, cpu_ns=80)
    out: StringIO = StringIO()
    text: str = report(stream=out)
    expect_true(condition=text.index("slow") < text.index("fast"))
    expect_in(item="wall s", container=text)


def test_cascade_nests_callee_under_caller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that a sensed call inside another becomes a child node.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()

    @sensor(label="inner.work")
    def inner() -> int:
        """Return a constant.

        Returns:
            int: The constant 1.

        """
        return 1

    @sensor(label="outer.work")
    def outer() -> int:
        """Call ``inner`` and add one.

        Returns:
            int: The inner result plus one.

        """
        return inner() + 1

    expect_equal(actual=outer(), expected=2)
    root: TraceNode = sensors.metrics.root
    parent: TraceNode = root.children["outer.work"]
    child: TraceNode = parent.children["inner.work"]
    expect_equal(actual=parent.calls, expected=1)
    expect_equal(actual=child.calls, expected=1)
    expect_true(condition=parent.wall_ns >= child.wall_ns)
    expect_true(condition=parent.self_wall_ns <= parent.wall_ns)


def test_cascade_records_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that a raising call is counted on its path and stat.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()

    @sensor(label="boom.work")
    def boom() -> None:
        """Raise unconditionally.

        Raises:
            RuntimeError: Always.

        """
        msg: str = "boom"
        raise RuntimeError(msg)

    caught: bool = False
    try:
        boom()
    except RuntimeError:
        caught = True
    expect_true(condition=caught)
    expect_equal(
        actual=sensors.metrics.snapshot()["boom.work"].errors,
        expected=1,
    )
    expect_equal(
        actual=sensors.metrics.root.children["boom.work"].errors,
        expected=1,
    )


def test_cascade_folds_past_the_depth_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that recursion deeper than the cap lands in ``<deep>``.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()

    @sensor(label="recurse.work")
    def recurse(*, left: int) -> int:
        """Recurse until ``left`` runs out.

        Args:
            left (int): Remaining depth.

        Returns:
            int: Zero once the recursion ends.

        """
        return 0 if left <= 0 else recurse(left=left - 1)

    expect_equal(actual=recurse(left=80), expected=0)
    node: TraceNode = sensors.metrics.root.children["recurse.work"]
    depth: int = 0
    while "recurse.work" in node.children:
        node = node.children["recurse.work"]
        depth += 1
    fold_floor: Final[int] = 60
    expect_in(item="<deep>", container=node.children)
    expect_true(condition=depth >= fold_floor)


def test_trace_report_renders_indented_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that the cascade renders caller rows before callee rows.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setenv(name="ASTART_SENSORS", value="1")
    sensors.metrics.reset()
    with timed(label="phase.outer"), timed(label="phase.inner"):
        total: int = sum(range(10))
    expect_true(condition=total >= 0)
    out: StringIO = StringIO()
    text: str = trace_report(stream=out)
    expect_true(
        condition=text.index("phase.outer") < text.index("phase.inner"),
    )
    expect_in(item="self s", container=text)
    expect_in(item="avg us", container=text)
    expect_in(item="err", container=text)
