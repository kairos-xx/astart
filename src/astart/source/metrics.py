"""Execution sensors: decorator-based timing for the conversion pipeline.

Decorating a function or wrapping a block records wall-clock and CPU
nanoseconds into a process-wide registry. Sensors activate only when
``ASTART_SENSORS`` names a truthy value, so production runs pay nothing but
an ``if`` check per call. ``instrument`` wraps every function in a module
for whole-pipeline coverage without editing each call site.

"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from functools import wraps
from inspect import isfunction
from json import dumps
from os import environ
from sys import stderr
from threading import local
from time import perf_counter_ns, process_time_ns
from typing import TYPE_CHECKING, Final, TextIO, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping
    from pathlib import Path
    from types import ModuleType

_MAX_TRACE_DEPTH: Final[int] = 64
_DEEP_LABEL: Final[str] = "<deep>"


@dataclass(slots=True)
class Stat:
    """Accumulated timing for one sensor label.

    Attributes:
        calls (int): How many times the sensor fired.
        wall_ns (int): Total wall-clock nanoseconds.
        cpu_ns (int): Total process CPU nanoseconds.
        errors (int): Calls that raised.
        max_wall_ns (int): Slowest single call.

    """

    calls: int = 0
    wall_ns: int = 0
    cpu_ns: int = 0
    errors: int = 0
    max_wall_ns: int = 0

    def add(self, *, wall_ns: int, cpu_ns: int, error: bool = False) -> None:
        """Fold one sample into the accumulation.

        Args:
            wall_ns (int): Wall-clock nanoseconds the call took.
            cpu_ns (int): CPU nanoseconds the call took.
            error (bool): Whether the call raised.

        """
        self.calls += 1
        self.wall_ns += wall_ns
        self.cpu_ns += cpu_ns
        self.errors += error
        self.max_wall_ns = max(self.max_wall_ns, wall_ns)


@dataclass(slots=True)
class TraceNode:
    """One call-path in the execution cascade.

    Attributes:
        label (str): Sensor name recorded at this point of the path.
        calls (int): How many times the path was entered.
        wall_ns (int): Total wall-clock nanoseconds inside the path.
        cpu_ns (int): Total process CPU nanoseconds inside the path.
        errors (int): Calls through the path that raised.
        max_wall_ns (int): Slowest single entry.
        children (dict[str, TraceNode]): Immediate callees keyed by sensor
            label.

    """

    label: str
    calls: int = 0
    wall_ns: int = 0
    cpu_ns: int = 0
    errors: int = 0
    max_wall_ns: int = 0
    children: dict[str, TraceNode] = field(default_factory=dict)

    @property
    def self_wall_ns(self) -> int:
        """Return wall time spent in this node excluding traced callees.

        Returns:
            int: Nanoseconds not attributed to any child node.

        """
        return max(
            0,
            self.wall_ns
            - sum(child.wall_ns for child in self.children.values()),
        )


class Metrics:
    """Process-wide sensor registry."""

    __slots__ = ("_local", "_stats", "root")

    def __init__(self) -> None:
        """Start an empty registry."""
        self._stats: dict[str, Stat] = {}
        self.root: TraceNode = TraceNode(label="<run>")
        self._local: local = local()

    def record(
        self,
        *,
        label: str,
        wall_ns: int,
        cpu_ns: int,
        error: bool = False,
    ) -> None:
        """Record one timing sample.

        Args:
            label (str): Sensor name.
            wall_ns (int): Wall-clock nanoseconds.
            cpu_ns (int): CPU nanoseconds.
            error (bool): Whether the call raised.

        """
        stat: Stat | None = self._stats.get(label)
        if stat is None:
            stat = Stat()
            self._stats[label] = stat
        stat.add(wall_ns=wall_ns, cpu_ns=cpu_ns, error=error)

    def push(self, *, label: str) -> TraceNode:
        """Enter one call-path and return its node.

        Args:
            label (str): Sensor name being entered.

        Returns:
            TraceNode: The ``TraceNode`` for ``label`` under the current
                caller. Past ``_MAX_TRACE_DEPTH`` the path folds into a
                shared ``<deep>`` node instead of growing without bound.

        """
        stack: list[TraceNode] | None = getattr(
            self._local,
            "stack",
            None,
        )
        if stack is None:
            stack = []
            self._local.stack = stack
        parent: TraceNode = stack[-1] if stack else self.root
        if len(stack) >= _MAX_TRACE_DEPTH and parent.label != _DEEP_LABEL:
            node: TraceNode | None = parent.children.get(_DEEP_LABEL)
            if node is None:
                node = TraceNode(label=_DEEP_LABEL)
                parent.children[_DEEP_LABEL] = node
        elif len(stack) >= _MAX_TRACE_DEPTH:
            node = parent
        else:
            node = parent.children.get(label)
            if node is None:
                node = TraceNode(label=label)
                parent.children[label] = node
        stack.append(node)
        return node

    def pop(
        self,
        *,
        node: TraceNode,
        label: str,
        wall_ns: int,
        cpu_ns: int,
        error: bool = False,
    ) -> None:
        """Leave a call-path, folding its timing into the node and stat.

        Args:
            node (TraceNode): The node ``push`` returned.
            label (str): Sensor name for the flat accumulation (a ``<deep>``
                node still records under the real label).
            wall_ns (int): Wall-clock nanoseconds inside the call.
            cpu_ns (int): CPU nanoseconds inside the call.
            error (bool): Whether the call raised.

        """
        self._local.stack.pop()
        node.calls += 1
        node.wall_ns += wall_ns
        node.cpu_ns += cpu_ns
        node.errors += error
        node.max_wall_ns = max(node.max_wall_ns, wall_ns)
        self.record(label=label, wall_ns=wall_ns, cpu_ns=cpu_ns, error=error)

    def snapshot(self) -> Mapping[str, Stat]:
        """Return the accumulated stats, sorted by total wall time.

        Returns:
            Mapping[str, Stat]: ``{label: Stat}`` ordered slowest first.

        """
        return dict(
            sorted(
                self._stats.items(),
                key=lambda item: item[1].wall_ns,
                reverse=True,
            ),
        )

    def merge(self, *, stats: Mapping[str, Stat], trace: TraceNode) -> None:
        """Merge one completed worker's measurements into this recorder.

        Args:
            stats (Mapping[str, Stat]): Per-module measurements from the worker
                process.
            trace (TraceNode): Completed call tree under a unique module label.

        """
        for label, sample in stats.items():
            target: Stat = self._stats.setdefault(label, Stat())
            target.calls += sample.calls
            target.wall_ns += sample.wall_ns
            target.cpu_ns += sample.cpu_ns
            target.errors += sample.errors
            target.max_wall_ns = max(target.max_wall_ns, sample.max_wall_ns)
        self.root.children[trace.label] = trace

    def reset(self) -> None:
        """Drop every accumulated sample and the recorded cascade."""
        self._stats.clear()
        self.root = TraceNode(label="<run>")
        self._local.stack = []


metrics: Final[Metrics] = Metrics()


def enabled() -> bool:
    """Tell whether sensors collect timings right now.

    Returns:
        bool: ``True`` when ``ASTART_SENSORS`` is set to a truthy value.

    """
    return environ.get("ASTART_SENSORS", "") not in ("", "0")


@contextmanager
def timed(label: str) -> Generator[None]:
    """Time a block under ``label`` when sensors are enabled.

    Args:
        label (str): Sensor name the block's duration is recorded under.

    Yields:
        None: Nothing.

    """
    if not enabled():
        yield
        return
    node: TraceNode = metrics.push(label=label)
    wall: int = perf_counter_ns()
    cpu: int = process_time_ns()
    error: bool = False
    try:
        yield
    except BaseException:
        error = True
        raise
    finally:
        metrics.pop(
            node=node,
            label=label,
            wall_ns=perf_counter_ns() - wall,
            cpu_ns=process_time_ns() - cpu,
            error=error,
        )


@overload
def sensor[**P, R](function: Callable[P, R]) -> Callable[P, R]: ...


@overload
def sensor[**P, R](
    function: Callable[P, R],
    *,
    label: str | None = None,
) -> Callable[P, R]: ...


@overload
def sensor[**P, R](
    function: None = None,
    *,
    label: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def sensor[**P, R](
    function: Callable[P, R] | None = None,
    *,
    label: str | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Time calls to a function under ``label`` when sensors are enabled.

    The decision is taken once, when the wrapper is created — the
    environment is process-start configuration, so wrapped calls pay a
    single boolean check instead of an ``environ`` lookup each time.

    Args:
        function (Callable[P, R] | None): The decorated callable (bare
            ``@sensor`` form).
        label (str | None): Sensor name; defaults to ``qualname``
            (``@sensor(label=...)``).

    Returns:
        Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]: The
            wrapped callable, or the decorator for the labelled form.

    """

    def _wrap(target: Callable[P, R]) -> Callable[P, R]:
        """Wrap one callable.

        Args:
            target (Callable[P, R]): Callable to time.

        Returns:
            Callable[P, R]: The timed callable.

        """
        name: str = label or f"{target.__module__}.{target.__qualname__}"
        armed: bool = enabled()

        @wraps(wrapped=target)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            """Call ``target`` under a sensor.

            Args:
                args (P.args): Positional arguments forwarded to ``target``.
                kwargs (P.kwargs): Keyword arguments forwarded to ``target``.

            Returns:
                R: Whatever ``target`` returns.

            """
            if not armed:
                return target(*args, **kwargs)
            node: TraceNode = metrics.push(label=name)
            wall: int = perf_counter_ns()
            cpu: int = process_time_ns()
            error: bool = False
            try:
                return target(*args, **kwargs)
            except BaseException:
                error = True
                raise
            finally:
                metrics.pop(
                    node=node,
                    label=name,
                    wall_ns=perf_counter_ns() - wall,
                    cpu_ns=process_time_ns() - cpu,
                    error=error,
                )

        return inner

    return _wrap if function is None else _wrap(target=function)


def instrument(
    *,
    module: ModuleType,
    prefix: str | None = None,
    skip_private: bool = True,
) -> int:
    """Wrap every function defined directly on a module.

    Args:
        module (ModuleType): Module whose callables are wrapped in place.
        prefix (str | None): Label prefix; defaults to the module name.
        skip_private (bool): Whether names starting with ``_`` are left alone.

    Returns:
        int: How many callables were wrapped.

    """
    base: str = prefix or module.__name__
    wrapped: int = 0
    for name, member in vars(module).items():
        if skip_private and name.startswith("_"):
            continue
        if not isfunction(object=member) or getattr(
            member,
            "__wrapped__",
            None,
        ):
            continue
        setattr(
            module,
            name,
            sensor(function=member, label=f"{base}.{name}"),
        )
        wrapped += 1
    return wrapped


def report(*, stream: TextIO = stderr, limit: int | None = None) -> str:
    """Format the accumulated timings as a table.

    Args:
        stream (TextIO): Where the table is also written.
        limit (int | None): Maximum rows; ``None`` prints all.

    Returns:
        str: The rendered table.

    """
    rows: list[str] = [
        f"{'sensor':<70} {'calls':>7} {'wall s':>10} "
        f"{'cpu s':>10} {'max ms':>9} {'err':>4}",
    ]
    snapshot: Mapping[str, Stat] = metrics.snapshot()
    items: list[tuple[str, Stat]] = list(snapshot.items())[
        : limit if limit is not None else len(snapshot)
    ]
    for label, stat in items:
        rows.append(
            f"{label:<70} {stat.calls:>7} {stat.wall_ns / 1e9:>10.3f}"
            f" {stat.cpu_ns / 1e9:>10.3f} {stat.max_wall_ns / 1e6:>9.1f}"
            f" {stat.errors:>4}",
        )
    text: str = "\n".join(rows)
    print(text, file=stream)
    return text


def trace_report(
    *,
    stream: TextIO = stderr,
    min_wall_ns: int = 0,
    max_rows: int | None = None,
) -> str:
    """Format the recorded cascade as an indented call-path tree.

    Every row is one ``(caller, callee)`` position in the cascade:
    call count, total wall and CPU time, self time (excluding traced
    callees), share of the whole run, slowest single call, and errors.
    Children sort slowest-first; paths deeper than the cap fold into
    ``<deep>`` placeholders.

    Args:
        stream (TextIO): Where the tree is also written.
        min_wall_ns (int): Branches below this total wall time collapse into a
            ``<N branches hidden>`` count rather than a row each.
        max_rows (int | None): Maximum rendered rows; ``None`` renders
            everything.

    Returns:
        str: The rendered tree.

    """
    total: int = max(
        1,
        sum(child.wall_ns for child in metrics.root.children.values()),
    )
    rows: list[str] = [
        f"cascade · depth ≤ {_MAX_TRACE_DEPTH} · "
        f"{_DEEP_LABEL} folds deeper calls",
        (
            f"{'sensor':<64} {'calls':>7} {'wall s':>10} {'%run':>6}"
            f" {'cpu s':>10} {'self s':>10} {'avg us':>9} {'max ms':>9}"
            f" {'err':>4}"
        ),
    ]
    hidden: list[int] = [0]
    emitted: list[int] = [0]

    def _walk(*, node: TraceNode, depth: int) -> None:
        """Render one node's children, slowest first.

        Args:
            node (TraceNode): Parent whose children become rows.
            depth (int): Indentation level for the children.

        """
        for child in sorted(
            node.children.values(),
            key=lambda item: item.wall_ns,
            reverse=True,
        ):
            if child.wall_ns < min_wall_ns:
                hidden[0] += 1
                continue
            if max_rows is not None and emitted[0] >= max_rows:
                hidden[0] += 1
                continue
            emitted[0] += 1
            label: str = child.label
            indent: str = "  " * depth
            rows.append(
                f"{indent + label:<64.64} {child.calls:>7}"
                f" {child.wall_ns / 1e9:>10.3f}"
                f" {child.wall_ns * 100 / total:>5.1f}%"
                f" {child.cpu_ns / 1e9:>10.3f}"
                f" {child.self_wall_ns / 1e9:>10.3f}"
                f" {child.wall_ns / 1e3 / max(1, child.calls):>9.1f}"
                f" {child.max_wall_ns / 1e6:>9.1f}"
                f" {child.errors:>4}",
            )
            _walk(node=child, depth=depth + 1)

    _walk(node=metrics.root, depth=0)
    if hidden[0]:
        rows.append(f"<{hidden[0]} branches hidden>")
    text: str = "\n".join(rows)
    print(text, file=stream)
    return text


def dump(*, directory: Path) -> None:
    """Write the current recorder as readable and structured artifacts.

    Args:
        directory (Path): Explicit artifact destination owned by the caller.

    """
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "sensors.txt").open(
        mode="w",
        encoding="utf-8",
    ) as stream:
        report(stream=stream)
        trace_report(stream=stream, min_wall_ns=1_000_000)
    data: dict[str, object] = {
        "stats": {
            label: asdict(obj=value)
            for label, value in metrics.snapshot().items()
        },
        "trace": asdict(obj=metrics.root),
    }
    _ = (directory / "sensors.json").write_text(
        data=dumps(obj=data, indent=2) + "\n",
        encoding="utf-8",
    )
