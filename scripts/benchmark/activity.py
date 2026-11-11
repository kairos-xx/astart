"""Atomic benchmark activity snapshots with an independent live heartbeat."""

from __future__ import annotations

from datetime import UTC, datetime
from json import dumps
from os import getpid
from threading import Event, RLock, Thread
from time import monotonic
from typing import TYPE_CHECKING, Self
from uuid import uuid4

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType

    from astart.rules.jsonvalue import JsonValue


class Activity:
    """Own one benchmark run's heartbeat thread and progress document.

    Attributes:
        exit_code: Command result, assigned before leaving the context.

    """

    def __init__(
        self,
        *,
        directory: Path,
        command: str,
        interval: float = 1.0,
        jobs: int = 1,
    ) -> None:
        """Prepare a run without starting background work.

        Args:
            directory (Path): Destination for ``@activity.json``.
            command (str): Benchmark command being executed.
            interval (float): Seconds between heartbeats.
            jobs (int): Configured worker process count.

        """
        self.exit_code: int = 0
        self._directory: Path = directory
        self._command: str = command
        self._interval: float = interval
        self._jobs: int = jobs
        self._run_id: str = uuid4().hex
        self._started: str = datetime.now(tz=UTC).isoformat()
        self._clock: float = monotonic()
        self._status: str = "running"
        self._finished: str | None = None
        self._completed: int = 0
        self._total: int = 0
        self._current: str = ""
        self._error: OSError | None = None
        self._lock: RLock = RLock()
        self._stop: Event = Event()
        self._thread: Thread = Thread(
            target=self._heartbeat,
            name="benchmark-heartbeat",
            daemon=True,
        )

    def __enter__(self) -> Self:
        """Start the heartbeat after publishing the initial snapshot.

        Returns:
            Self: This run's progress recorder.

        """
        self._directory.mkdir(parents=True, exist_ok=True)
        self._write()
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None:
        """Stop the worker and publish the final lifecycle state.

        Args:
            exc_type (type[BaseException] | None): Exception class, when
                execution failed.
            exc (BaseException | None): Exception raised by the command.
            traceback (TracebackType | None): Command traceback, when present.

        Raises:
            self._error: TODO.

        """
        self._stop.set()
        self._thread.join(timeout=max(2.0, self._interval * 2))
        self._status = (
            "interrupted"
            if isinstance(exc, KeyboardInterrupt)
            else "failed"
            if exc is not None or self.exit_code or self._error is not None
            else "completed"
        )
        self._finished = datetime.now(tz=UTC).isoformat()
        self._write()
        if self._error is not None and exc is None:
            raise self._error

    def progress(self, *, completed: int, total: int, current: str) -> None:
        """Update completed work without waiting for the next heartbeat.

        Args:
            completed (int): Number of modules whose measurements finished.
            total (int): Number of scheduled modules.
            current (str): Current or most recently completed module.

        """
        with self._lock:
            self._completed = completed
            self._total = total
            self._current = current
            self._write()

    def _heartbeat(self) -> None:
        """Publish beats until stopped, retaining any filesystem failure."""
        while not self._stop.wait(timeout=self._interval):
            try:
                self._write()
            except OSError as error:
                self._error = error
                return

    def _write(self) -> None:
        """Atomically replace the document while holding the progress lock."""
        with self._lock:
            now: str = datetime.now(tz=UTC).isoformat()
            fraction: float = (
                self._completed / self._total if self._total else 0.0
            )
            data: dict[str, JsonValue] = {
                "schema": "astart/benchmark/activity/v1",
                "kind": "tool",
                "name": self._command,
                "run_id": self._run_id,
                "pipeline_run_id": None,
                "status": self._status,
                "started_at": self._started,
                "updated_at": now,
                "finished_at": self._finished,
                "elapsed_seconds": round(
                    number=monotonic() - self._clock,
                    ndigits=3,
                ),
                "heartbeat": {
                    "pid": getpid(),
                    "alive": self._status == "running",
                    "last_beat": now,
                    "phase": self._status,
                    "interval_seconds": self._interval,
                },
                "progress": {
                    "completed": self._completed,
                    "total": self._total,
                    "fraction": fraction,
                    "percent": fraction * 100,
                    "step": self._command,
                    "current": self._current,
                },
                "activity": {"events": [], "limit": 50, "dropped": 0},
                "items": [],
                "extra": {
                    "jobs": self._jobs,
                    "exit_code": self.exit_code if self._finished else None,
                },
            }
            temporary: Path = (
                self._directory / f".@activity.{self._run_id}.tmp"
            )
            try:
                _ = temporary.write_text(
                    data=dumps(obj=data, indent=2) + "\n",
                    encoding="utf-8",
                )
                _ = temporary.replace(
                    target=self._directory / "@activity.json",
                )
            finally:
                temporary.unlink(missing_ok=True)
