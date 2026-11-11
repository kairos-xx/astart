"""Benchmark profiling over the same recorder used by the installed CLI."""

from __future__ import annotations

from atexit import register
from sys import modules

from astart.source.metrics import (
    Metrics,
    Stat,
    TraceNode,
    dump,
    enabled,
    instrument,
    metrics,
    report,
    sensor,
    timed,
    trace_report,
)

from scripts.benchmark.paths import Paths


def arm(*, register_exit: bool = True) -> None:
    """Enable benchmark instrumentation and optional exit-time artifacts.

    Args:
        register_exit (bool): Whether this process owns the shared sensor dump.

    """
    if not enabled():
        return
    for module in tuple(modules.values()):
        name: str = getattr(module, "__name__", "")
        if name.startswith(("astart.", "scripts.benchmark.")) and name not in {
            "astart.source.metrics",
            "scripts.benchmark.presentation",
            "scripts.benchmark.cli",
            "scripts.benchmark.activity",
            "scripts.benchmark.runner",
            "scripts.benchmark.profile_perf",
            __name__,
        }:
            instrument(module=module, skip_private=False)

    def emit() -> None:
        """Persist the shared recorder after the benchmark exits."""
        dump(directory=Paths.results)

    if register_exit:
        register(emit)


__all__ = (
    "Metrics",
    "Stat",
    "TraceNode",
    "arm",
    "dump",
    "enabled",
    "instrument",
    "metrics",
    "report",
    "sensor",
    "timed",
    "trace_report",
)
