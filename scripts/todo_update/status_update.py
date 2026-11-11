"""Keep the status ledger in docs/planning/TODO.md up to date.

Usage (from the repository root)::

    python -m scripts.todo_update status render
    python -m scripts.todo_update status refresh
    python -m scripts.compare.pair A B --engine --min-confidence 0.5
    python -m scripts.todo_update status pair --label "after G-02"
    python -m scripts.todo_update status check semantic_run pass
        --note "15 of 15"
    python -m scripts.todo_update status item add "run the semantic run"
    python -m scripts.todo_update status item remove 2
    python -m scripts.todo_update status note "what is uncommitted"

Every command prints progress bars, the change since the previous update and
human-readable times (add ``--quiet`` to silence it). State lives in
docs/planning/status.json; the block between the status markers in
docs/planning/TODO.md is generated from it and must not be edited by hand.

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from json import dumps, loads
from os import fsync
from pathlib import Path
from shutil import copymode
from sys import stderr, stdin, stdout
from tempfile import NamedTemporaryFile
from time import sleep, time
from typing import TYPE_CHECKING, Final, Protocol, final

type ListStr = list[str]
type DictJson = dict[str, Json]

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import ModuleType

    from scripts.todo_update.todo_index import Task

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


class _ParserFactory(Protocol):
    """The ``add_parser`` slice of ``ArgumentParser.add_subparsers``."""

    def add_parser(self, name: str) -> ArgumentParser:
        """Register one subcommand parser.

        Args:
            name (str): Subcommand name.

        Returns:
            The new subcommand parser.

        """
        ...


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root.
        start (Final[str]): Marker opening the generated block.
        end (Final[str]): Marker closing the generated block.
        statuses (Final[tuple[str, ...]]): Allowed check statuses.
        check_names (Final[tuple[str, ...]]): Checks shown first, in this
            order.
        target_share (Final[float]): Share of recoverable annotations the
            contract asks for.
        bar_width (Final[int]): Width of a progress bar in characters.
        measures (Final[tuple[tuple[str, str, str, bool], ...]]): Label, value
            key, total key and whether lower is better.
        history_keys (Final[tuple[str, ...]]): Numbers copied from the latest
            history entry.
        just_now_seconds (Final[int]): Seconds counted as ``just now`` by
            :func:`ago`.
        minutes_in_hour (Final[int]): Minutes in one hour, an ``ago`` bucket
            boundary.
        two_days_in_hours (Final[int]): Hours in two days, the last ``ago``
            hour bucket.
        lock_attempts (Final[int]): Times lock acquisition is retried before
            failing.
        lock_delay_seconds (Final[float]): Seconds slept between lock retries.
        lock_stale_seconds (Final[int]): Age after which a lock file is taken
            over.

    """

    root: Final[Path] = Path(__file__).resolve().parent.parent.parent
    start: Final[str] = "<!-- status:start -->"
    end: Final[str] = "<!-- status:end -->"
    statuses: Final[tuple[str, ...]] = ("pass", "fail", "not run")
    check_names: Final[tuple[str, ...]] = (
        "fast_tier",
        "slow_tier",
        "stdlib_gate",
        "external_gate",
        "semantic_run",
        "lint",
    )
    target_share: Final[float] = 0.9
    bar_width: Final[int] = 20
    measures: Final[tuple[tuple[str, str, str, bool], ...]] = (
        ("Parameters and returns exact", "p_exact", "p_total", False),
        ("Parameters and returns wrong", "p_wrong", "p_total", True),
        ("Variables exact", "v_exact", "v_total", False),
        ("Variables wrong", "v_wrong", "v_total", True),
        ("Tasks done", "tasks_done", "tasks_total", False),
        ("Tasks missing", "tasks_open", "tasks_total", True),
    )
    history_keys: Final[tuple[str, ...]] = (
        "p_exact",
        "p_wrong",
        "p_total",
        "v_exact",
        "v_wrong",
        "v_total",
    )
    just_now_seconds: Final[int] = 45
    minutes_in_hour: Final[int] = 60
    two_days_in_hours: Final[int] = 48
    lock_attempts: Final[int] = 50
    lock_delay_seconds: Final[float] = 0.1
    lock_stale_seconds: Final[int] = 60


@final
@dataclass(frozen=True, slots=True)
class Row:
    """One line of the progress display.

    Attributes:
        label (str): What is measured.
        bar (str): Progress bar.
        percent (str): Share of the total, as text.
        now (str): Current value and total, as text.
        change (str): Change since the previous update, as text.

    """

    label: str
    bar: str
    percent: str
    now: str
    change: str


def number(*, value: Json) -> int | None:
    """Read a count from JSON.

    Args:
        value (Json): A JSON value.

    Returns:
        int | None: The integer, or ``None`` when the value is not an integer.

    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def bar(*, value: int, total: int) -> str:
    """Draw a progress bar.

    Args:
        value (int): Amount done.
        total (int): Amount that means 100 %.

    Returns:
        str: A bar of ``Constants.bar_width`` characters, filled in proportion.

    """
    width: int = Constants.bar_width
    if total <= 0:
        return "░" * width
    filled: int = max(0, min(width, round(number=width * value / total)))
    return "█" * filled + "░" * (width - filled)


def percent(*, value: int, total: int) -> str:
    """Format a share as a percentage.

    Args:
        value (int): Amount done.
        total (int): Amount that means 100 %.

    Returns:
        str: For example ``"45.9 %"``, or ``"n/a"`` when the total is zero.

    """
    if total <= 0:
        return "n/a"
    return f"{100 * value / total:.1f} %"


def delta_text(*, now: int | None, before: int | None, lower: bool) -> str:
    """Describe a change between two updates.

    Args:
        now (int | None): Current value.
        before (int | None): Value at the previous update.
        lower (bool): Whether a lower value is better (for example ``wrong``).

    Returns:
        str: ``"n/a"`` without a previous value, ``"no change"``, or a signed
            difference followed by ``better`` or ``worse``.

    """
    if now is None or before is None:
        return "n/a"
    diff: int = now - before
    if diff == 0:
        return "no change"
    good: bool = diff < 0 if lower else diff > 0
    sign: str = "+" if diff > 0 else "-"
    return f"{sign}{abs(diff)} {'better' if good else 'worse'}"


def now_iso() -> str:
    """Give the current local time with its offset.

    Returns:
        str: An ISO 8601 timestamp such as ``2026-11-08T18:37:12+00:00``.

    """
    return datetime.now().astimezone().isoformat(timespec="seconds")


def human_time(*, iso: str) -> str:
    """Format a timestamp for people.

    Args:
        iso (str): ISO 8601 timestamp.

    Returns:
        str: For example ``"Sun 08 Nov 2026, 18:37 WET"``.

    """
    moment: datetime = datetime.fromisoformat(iso)
    return moment.strftime(format="%a %d %b %Y, %H:%M %Z").strip()


def short_time(*, iso: str) -> str:
    """Format a timestamp compactly for table cells.

    Args:
        iso (str): ISO 8601 timestamp.

    Returns:
        str: For example ``"08 Nov 2026 18:37"``.

    """
    moment: datetime = datetime.fromisoformat(iso)
    return moment.strftime(format="%d %b %Y %H:%M")


def ago(*, iso: str, reference: datetime | None = None) -> str:
    """Say how long ago a timestamp was.

    Args:
        iso (str): ISO 8601 timestamp.
        reference (datetime | None): Time to measure from; now when omitted.

    Returns:
        str: ``"just now"``, ``"N minutes ago"``, ``"N hours ago"`` or
            ``"N days ago"``.

    """
    when: datetime = datetime.fromisoformat(iso)
    base: datetime = reference or datetime.now(tz=when.tzinfo)
    seconds: int = int((base - when).total_seconds())
    if seconds < Constants.just_now_seconds:
        return "just now"
    minutes: int = round(number=seconds / 60)
    if minutes < Constants.minutes_in_hour:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours: int = round(number=minutes / 60)
    if hours < Constants.two_days_in_hours:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    return f"{round(number=hours / 24)} days ago"


def _list(*, state: DictJson, key: str) -> list[Json]:
    """Get a list from the state, creating it when absent.

    Args:
        state (DictJson): The ledger state.
        key (str): Key of the list.

    Returns:
        list[Json]: The list stored under the key.

    Raises:
        SystemExit: When the stored value is not a JSON list.

    """
    value: Json = state.setdefault(key, [])
    if not isinstance(value, list):
        msg: str = f"{key}: expected a JSON list"
        raise SystemExit(msg)
    return value


def _dict(*, state: DictJson, key: str) -> DictJson:
    """Get an object from the state, creating it when absent.

    Args:
        state (DictJson): The ledger state.
        key (str): Key of the object.

    Returns:
        DictJson: The object stored under the key.

    Raises:
        SystemExit: When the stored value is not a JSON object.

    """
    value: Json = state.setdefault(key, {})
    if not isinstance(value, dict):
        msg: str = f"{key}: expected a JSON object"
        raise SystemExit(msg)
    return value


def _task_counts(*, todo: Path) -> tuple[int, int] | None:
    """Count done and total tasks with the dashboard script's parser.

    Args:
        todo (Path): Path of the TODO file.

    Returns:
        tuple[int, int] | None: ``(done, total)``, or ``None`` when the
            sibling script cannot be imported or read.

    """
    for name in ("todo_index", "scripts.todo_update.todo_index"):
        try:
            parse_tasks: Callable[..., list[Task]] = import_module(
                name=name,
            ).parse
            tasks: list[Task] = parse_tasks(
                text=todo.read_text(encoding="utf-8"),
            )
        except (ImportError, AttributeError, TypeError, OSError):
            continue
        return sum(1 for task in tasks if task.done), len(tasks)
    return None


def chapter_rows(*, todo: Path) -> ListStr:
    """Draw one progress bar per chapter: done tasks against all tasks.

    Args:
        todo (Path): Path of the TODO file.

    Returns:
        ListStr: One line per chapter that has tasks, or an empty
            list when the dashboard script cannot be imported.

    """
    for name in ("todo_index", "scripts.todo_update.todo_index"):
        try:
            module: ModuleType = import_module(name=name)
            tasks: list[Task] = module.parse(
                text=todo.read_text(encoding="utf-8"),
            )
            chapters: tuple[tuple[int, str, tuple[str, ...], str], ...] = (
                module.Constants.chapters
            )
            chapter_of: Callable[..., int] = module.chapter_of
        except (ImportError, AttributeError, TypeError, OSError):
            continue
        break
    else:
        return []
    totals: dict[int, int] = {}
    dones: dict[int, int] = {}
    for task in tasks:
        number: int = chapter_of(identifier=task.identifier)
        totals[number] = totals.get(number, 0) + 1
        if task.done:
            dones[number] = dones.get(number, 0) + 1
    width: int = max(len(title) for _n, title, _p, _s in chapters)
    rows: ListStr = []
    for chapter in chapters:
        number = chapter[0]
        title: str = chapter[1]
        total: int = totals.get(number, 0)
        if total == 0:
            continue
        done: int = dones.get(number, 0)
        rows.append(
            f"{number:>2} {title.ljust(width)}  "
            f"{bar(value=done, total=total)}  "
            f"{done:>3} done, {total - done:>3} missing",
        )
    return rows


def take_snapshot(*, state: DictJson, todo: Path) -> DictJson:
    """Record the numbers that updates are compared on.

    Args:
        state (DictJson): The ledger state.
        todo (Path): Path of the TODO file (for the task counts).

    Returns:
        DictJson: The latest pair numbers, the task counts and the time.

    """
    history: list[Json] = _list(state=state, key="history")
    last: Json = history[-1] if history else None
    source: DictJson = last if isinstance(last, dict) else {}
    counts: tuple[int, int] | None = _task_counts(todo=todo)
    snapshot: DictJson = {"at": now_iso()}
    for key in Constants.history_keys:
        snapshot[key] = source.get(key)
    snapshot["tasks_done"] = None if counts is None else counts[0]
    snapshot["tasks_total"] = None if counts is None else counts[1]
    snapshot["tasks_open"] = None if counts is None else counts[1] - counts[0]
    return snapshot


def progress_rows(
    *,
    snapshot: DictJson,
    previous: DictJson | None,
) -> list[Row]:
    """Build the progress display.

    Args:
        snapshot (DictJson): Current numbers.
        previous (DictJson | None): Numbers at the previous update, or ``None``
            .

    Returns:
        list[Row]: One row per measure.

    """
    rows: list[Row] = []
    for label, value_key, total_key, lower in Constants.measures:
        value: int | None = number(value=snapshot.get(value_key))
        total: int | None = number(value=snapshot.get(total_key))
        if value is None or total is None:
            rows.append(
                Row(
                    label=label,
                    bar=bar(value=0, total=0),
                    percent="n/a",
                    now="n/a",
                    change="n/a",
                ),
            )
            continue
        before: int | None = (
            None if previous is None else number(value=previous.get(value_key))
        )
        rows.append(
            Row(
                label=label,
                bar=bar(value=value, total=total),
                percent=percent(value=value, total=total),
                now=f"{value} of {total}",
                change=delta_text(now=value, before=before, lower=lower),
            ),
        )
    return rows


def _views(
    *,
    state: DictJson,
    todo: Path,
) -> tuple[DictJson, DictJson | None]:
    """Pick the current and previous snapshots to display.

    Args:
        state (DictJson): The ledger state.
        todo (Path): Path of the TODO file.

    Returns:
        tuple[DictJson, DictJson | None]: The stored snapshot (or a live one
            before the
            first update) and the previous snapshot, if any.

    """
    stored: Json = state.get("snapshot")
    current: DictJson = (
        stored
        if isinstance(stored, dict)
        else take_snapshot(state=state, todo=todo)
    )
    before: Json = state.get("previous")
    return current, before if isinstance(before, dict) else None


def _when(*, entry: DictJson) -> str:
    """Show when a history or check entry happened.

    Args:
        entry (DictJson): An entry with ``at`` (preferred) or ``date``.

    Returns:
        str: A compact time, or the plain date for older entries.

    """
    at: Json = entry.get("at")
    if isinstance(at, str):
        return short_time(iso=at)
    return str(object=entry.get("date", "?"))


def render(*, state: DictJson, todo: Path) -> str:
    """Render the ledger as Markdown.

    Args:
        state (DictJson): The ledger state.
        todo (Path): Path of the TODO file.

    Returns:
        str: Markdown for the block between the status markers.

    """
    current, before = _views(state=state, todo=todo)
    updated: Json = state.get("updated_at")
    stamp: str = (
        human_time(iso=updated)
        if isinstance(updated, str)
        else str(object=state.get("updated", "?"))
    )
    compared: str = "first update, nothing to compare with"
    previous_at: Json = None if before is None else before.get("at")
    if isinstance(previous_at, str):
        compared = (
            f"change since the previous update on "
            f"{human_time(iso=previous_at)}"
        )
    lines: ListStr = [
        f"**Updated {stamp}.** {state.get('working_tree', '')}",
        "",
        f"**Progress** ({compared}):",
        "",
        "| Measure | Progress | Now | Change |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        (
            f"| {row.label} | `{row.bar}` {row.percent} | {row.now} | "
            f"{row.change} |"
        )
        for row in progress_rows(snapshot=current, previous=before)
    )
    lines.extend(
        (
            "",
            "| When | Moment | Parameters and returns: exact / wrong | "
            "Variables: exact / wrong |",
            "| --- | --- | --- | --- |",
        ),
    )
    last: DictJson | None = None
    for entry in _list(state=state, key="history"):
        if not isinstance(entry, dict):
            continue
        last = entry
        lines.append(
            f"| {_when(entry=entry)} | {entry.get('label')} | "
            f"{entry.get('p_exact')} / {entry.get('p_wrong')} of "
            f"{entry.get('p_total')} | {entry.get('v_exact')} / "
            f"{entry.get('v_wrong')} of {entry.get('v_total')} |",
        )
    if last is not None:
        goal_p: int = round(
            number=Constants.target_share
            * (number(value=last.get("p_total")) or 0),
        )
        goal_v: int = round(
            number=Constants.target_share
            * (number(value=last.get("v_total")) or 0),
        )
        lines.append(
            f"| target | 90 % exact, 0 wrong | about {goal_p} / 0 | "
            f"about {goal_v} / 0 |",
        )
    checks: DictJson = _dict(state=state, key="checks")
    ordered: ListStr = [n for n in Constants.check_names if n in checks]
    ordered.extend(sorted(n for n in checks if n not in ordered))
    lines.extend(
        ("", "| Check | Status | When | Note |", "| --- | --- | --- | --- |"),
    )
    for name in ordered:
        info: Json = checks[name]
        if isinstance(info, dict):
            lines.append(
                f"| {name} | {info.get('status')} | {_when(entry=info)} | "
                f"{info.get('note', '')} |",
            )
    lines.extend(("", "**Open items**", ""))
    for position, item in enumerate(
        iterable=_list(state=state, key="open_items"),
        start=1,
    ):
        lines.append(f"{position}. {item}")
    return "\n".join(lines)


def summary(*, state: DictJson, todo: Path) -> str:
    """Render the terminal summary: bars, deltas and human times.

    Args:
        state (DictJson): The ledger state.
        todo (Path): Path of the TODO file.

    Returns:
        str: Plain text for the terminal.

    """
    current, before = _views(state=state, todo=todo)
    rows: list[Row] = progress_rows(snapshot=current, previous=before)
    width: int = max(len(row.label) for row in rows)
    updated: Json = state.get("updated_at")
    lines: ListStr = []
    if isinstance(updated, str):
        lines.append(
            (
                f"Status ledger updated {human_time(iso=updated)} ("
                f"{ago(iso=updated)})"
            ),
        )
    previous_at: Json = None if before is None else before.get("at")
    if isinstance(previous_at, str):
        lines.append(
            f"Compared with the previous update on "
            f"{human_time(iso=previous_at)} ({ago(iso=previous_at)})",
        )
    else:
        lines.append("First update: nothing to compare with yet")
    lines.append("")
    for row in rows:
        label: str = row.label
        lines.append(
            f"  {label.ljust(width)}  {row.bar}  {row.percent:>7}  "
            f"{row.now:>12}  {row.change}",
        )
    chapters: ListStr = chapter_rows(todo=todo)
    if chapters:
        lines.extend(
            ("", "  Tasks by chapter:", *(f"  {row}" for row in chapters)),
        )
    checks: DictJson = _dict(state=state, key="checks")
    tally: dict[str, int] = dict.fromkeys(Constants.statuses, 0)
    for info in checks.values():
        if not isinstance(info, dict):
            continue
        status: Json = info.get("status")
        if isinstance(status, str) and status in tally:
            tally[status] += 1
    lines.extend(
        (
            "",
            "  Checks: "
            + ", ".join(
                f"{count} {status}" for status, count in tally.items()
            ),
            f"  Open items: {len(_list(state=state, key='open_items'))}",
        ),
    )
    return "\n".join(lines)


def write_block(*, todo: Path, block: str, name: str = "status") -> None:
    """Replace one generated block in the TODO file.

    Args:
        todo (Path): Path of the TODO file.
        block (str): New block text.
        name (str): Marker name of the block (``status`` or ``progress``).

    Raises:
        SystemExit: When the ``status`` markers are absent from the file.

    """
    start: str = f"<!-- {name}:start -->"
    end: str = f"<!-- {name}:end -->"
    text: str = todo.read_text(encoding="utf-8")
    head, found_start, rest = text.partition(start)
    _, found_end, tail = rest.partition(end)
    if not found_start or not found_end:
        if name == "status":
            msg: str = f"{todo}: {name} markers not found"
            raise SystemExit(msg)
        return
    _ = todo.write_text(
        data=f"{head}{start}\n{block}\n{end}{tail}",
        encoding="utf-8",
    )


def render_progress(*, state: DictJson, todo: Path) -> str:
    """Render the compact progress block shown at the top of the file.

    Args:
        state (DictJson): The ledger state.
        todo (Path): Path of the TODO file.

    Returns:
        str: Markdown with the progress bars inside a fenced text block, so the
            bar characters render in a monospace font in every viewer.

    """
    current, before = _views(state=state, todo=todo)
    rows: list[Row] = progress_rows(snapshot=current, previous=before)
    width: int = max(len(row.label) for row in rows)
    updated: Json = state.get("updated_at")
    stamp: str = (
        human_time(iso=updated)
        if isinstance(updated, str)
        else str(object=state.get("updated", "?"))
    )
    lines: ListStr = [
        f"Updated {stamp}. The last column is the change since the previous "
        "update; details are in the Status ledger below.",
        "",
        "```text",
    ]
    for row in rows:
        label: str = row.label
        lines.append(
            f"{label.ljust(width)}  {row.bar}  {row.percent:>7}  "
            f"{row.now:>12}  {row.change}",
        )
    chapters: ListStr = chapter_rows(todo=todo)
    if chapters:
        lines.extend(
            (
                "",
                "Tasks by chapter (bar = done, missing = still open):",
                *chapters,
            ),
        )
    lines.append("```")
    return "\n".join(lines)


def same_numbers(*, left: DictJson, right: DictJson) -> bool:
    """Tell whether two snapshots hold the same measured numbers.

    Args:
        left (DictJson): One snapshot.
        right (DictJson): Another snapshot.

    Returns:
        bool: ``True`` when every measured number is equal
            (times are ignored), so an update that changed
            nothing does not hide the last real change.

    """
    keys: tuple[str, ...] = (
        *Constants.history_keys,
        "tasks_done",
        "tasks_total",
        "tasks_open",
    )
    return all(left.get(key) == right.get(key) for key in keys)


def apply(*, args: Namespace, state: DictJson) -> bool:
    """Apply one command to the state.

    Args:
        args (Namespace): Parsed arguments.
        state (DictJson): The ledger state, changed in place.

    Returns:
        bool: Whether the state changed (``refresh`` counts as a change).

    Raises:
        SystemExit: When ``pair`` stdin is not the expected benchmarks JSON.

    """
    moment: str = now_iso()
    if args.command == "pair":
        report: Json = loads(s=stdin.read())
        if not isinstance(report, dict):
            msg: str = "stdin: expected the JSON from scripts.compare.pair"
            raise SystemExit(msg)
        params: Json = report.get("parameters_and_returns")
        variables: Json = report.get("variables")
        if not isinstance(params, dict) or not isinstance(variables, dict):
            msg = "stdin: missing parameters_and_returns/variables"
            raise SystemExit(msg)
        _list(state=state, key="history").append(
            {
                "date": moment[:10],
                "at": moment,
                "label": args.label,
                "p_exact": number(value=params.get("correct")) or 0,
                "p_wrong": number(value=params.get("wrong")) or 0,
                "p_total": number(value=params.get("to_recover")) or 0,
                "v_exact": number(value=variables.get("correct")) or 0,
                "v_wrong": number(value=variables.get("wrong")) or 0,
                "v_total": number(value=variables.get("to_recover")) or 0,
            },
        )
        return True
    if args.command == "check":
        _dict(state=state, key="checks")[args.name] = {
            "status": args.status,
            "date": moment[:10],
            "at": moment,
            "note": args.note,
        }
        return True
    if args.command == "item":
        items: list[Json] = _list(state=state, key="open_items")
        if args.action == "add":
            items.append(args.value)
        else:
            del items[int(args.value) - 1]
        return True
    if args.command == "note":
        state["working_tree"] = args.text
        return True
    return args.command == "refresh"


def _history_problems(*, value: Json) -> ListStr:
    """Check the ``history`` list shape.

    Args:
        value (Json): The stored value.

    Returns:
        ListStr: Readable problems.

    """
    if value is not None and not isinstance(value, list):
        return ["history: expected a JSON list"]
    if not isinstance(value, list):
        return []
    return [
        f"history[{position}]: expected a JSON object"
        for position, entry in enumerate(iterable=value)
        if not isinstance(entry, dict)
    ]


def _checks_problems(*, value: Json) -> ListStr:
    """Check the ``checks`` object shape and status vocabulary.

    Args:
        value (Json): The stored value.

    Returns:
        ListStr: Readable problems.

    """
    if value is not None and not isinstance(value, dict):
        return ["checks: expected a JSON object"]
    if not isinstance(value, dict):
        return []
    problems: ListStr = []
    for name, info in value.items():
        if not isinstance(info, dict):
            problems.append(f"checks.{name}: expected a JSON object")
            continue
        status: Json = info.get("status")
        if status not in Constants.statuses:
            problems.append(
                f"checks.{name}.status: unknown status {status!r}",
            )
    return problems


def _items_problems(*, value: Json) -> ListStr:
    """Check the ``open_items`` list shape.

    Args:
        value (Json): The stored value.

    Returns:
        ListStr: Readable problems.

    """
    if value is not None and not isinstance(value, list):
        return ["open_items: expected a JSON list"]
    if not isinstance(value, list):
        return []
    return [
        f"open_items[{position}]: expected a string"
        for position, item in enumerate(iterable=value)
        if not isinstance(item, str)
    ]


def _scalar_problems(*, state: DictJson) -> ListStr:
    """Check snapshot objects and timestamp strings.

    Args:
        state (DictJson): The ledger state.

    Returns:
        ListStr: Readable problems.

    """
    problems: ListStr = []
    for key in ("snapshot", "previous"):
        value: Json = state.get(key)
        if value is not None and not isinstance(value, dict):
            problems.append(f"{key}: expected a JSON object or null")
    for key in ("updated", "updated_at", "working_tree"):
        value = state.get(key)
        if value is not None and not isinstance(value, str):
            problems.append(f"{key}: expected a string")
    return problems


def validate_state(*, state: DictJson) -> ListStr:
    """Check that the ledger state has the expected shape.

    Args:
        state (DictJson): Parsed ``docs/planning/status.json``.

    Returns:
        ListStr: Readable problems; empty when the state is trustworthy.

    """
    return [
        *(
            f"missing key: {key}"
            for key in ("history", "checks", "open_items")
            if key not in state
        ),
        *_history_problems(value=state.get("history")),
        *_checks_problems(value=state.get("checks")),
        *_items_problems(value=state.get("open_items")),
        *_scalar_problems(state=state),
    ]


def _fail_on(*, path: Path, problems: ListStr) -> None:
    """Stop with exit code 2 when the state file is invalid.

    Args:
        path (Path): State file, for the message.
        problems (ListStr): Problems from :func:`validate_state`.

    Raises:
        SystemExit: Always, when the list is not empty.

    """
    if not problems:
        return
    _ = stderr.write(f"{path}: invalid state\n")
    for problem in problems:
        _ = stderr.write(f"  - {problem}\n")
    raise SystemExit(2)


def _load_state(*, path: Path) -> DictJson:
    """Read and validate the ledger state.

    Args:
        path (Path): State file.

    Returns:
        DictJson: The state as a mutable object.

    Raises:
        SystemExit: When the file is not a valid ledger object.

    """
    loaded: Json = loads(s=path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        msg: str = f"{path}: expected a JSON object"
        raise SystemExit(msg)
    _fail_on(path=path, problems=validate_state(state=loaded))
    return loaded


def _save_state(*, path: Path, state: DictJson) -> None:
    """Validate and atomically replace the state file.

    The text lands in a sibling temporary file and is moved over the target
    with :meth:`Path.replace`, so a reader never sees a half-written file.

    Args:
        path (Path): State file.
        state (DictJson): State to persist.

    Raises:
        SystemExit: When the new state is invalid.

    """
    _fail_on(path=path, problems=validate_state(state=state))
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            _ = handle.write(
                (dumps(obj=state, indent=2) + "\n").encode(encoding="utf-8"),
            )
            handle.flush()
            fsync(fd=handle.fileno())
        if path.exists():
            copymode(src=path, dst=temporary)
        _ = temporary.replace(target=path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _lock_stale(*, path: Path) -> bool:
    """Tell whether a lock file is old enough to take over.

    Args:
        path (Path): Lock file.

    Returns:
        bool: Whether the lock is older than ``Constants.lock_stale_seconds``
            , or ``False`` when it no longer exists.

    """
    try:
        return time() - path.stat().st_mtime > Constants.lock_stale_seconds
    except FileNotFoundError:
        return False


@contextmanager
def locked(*, path: Path) -> Generator[None]:
    """Hold an exclusive lock file around one state update.

    The lock is ``<state name>.lock`` created with ``O_CREAT | O_EXCL``
    semantics (``Path.touch(exist_ok=False)``); two overlapping runs merge
    instead of overwriting each other.

    Args:
        path (Path): State file the lock protects.

    Yields:
        None: Nothing; the lock is held inside the ``with`` body.

    Raises:
        SystemExit: When the lock cannot be taken in time.

    """
    lock: Path = path.with_name(name=f"{path.name}.lock")
    for _attempt in range(Constants.lock_attempts):
        try:
            lock.touch(exist_ok=False)
        except FileExistsError:
            if _lock_stale(path=lock):
                _ = stderr.write(f"{lock}: taking over a stale lock\n")
                lock.unlink(missing_ok=True)
            else:
                sleep(Constants.lock_delay_seconds)
        else:
            break
    else:
        msg: str = f"{lock}: could not take the lock"
        raise SystemExit(msg)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def main() -> int:
    """Run one ledger command.

    Returns:
        int: Zero.

    Raises:
        SystemExit: When the state file does not hold a JSON object.

    """
    parser: ArgumentParser = ArgumentParser(prog="todo_update status")
    parser.add_argument(
        "--state",
        type=Path,
        default=Constants.root / "docs" / "planning" / "status.json",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Constants.root / "docs" / "planning" / "TODO.md",
    )
    parser.add_argument("--quiet", action="store_true")
    commands: _ParserFactory = parser.add_subparsers(
        dest="command",
        required=True,
    )
    _ = commands.add_parser(name="render")
    _ = commands.add_parser(name="refresh")
    pair: ArgumentParser = commands.add_parser(name="pair")
    pair.add_argument("--label", required=True)
    check: ArgumentParser = commands.add_parser(name="check")
    check.add_argument("name")
    check.add_argument("status", choices=Constants.statuses)
    check.add_argument("--note", default="")
    item: ArgumentParser = commands.add_parser(name="item")
    item.add_argument("action", choices=("add", "remove"))
    item.add_argument("value")
    note: ArgumentParser = commands.add_parser(name="note")
    note.add_argument("text")
    args: Namespace = parser.parse_args()
    state_path: Path = args.state
    with locked(path=state_path):
        state: DictJson = _load_state(path=state_path)
        if apply(args=args, state=state):
            stored: Json = state.get("snapshot")
            fresh: DictJson = take_snapshot(
                state=state,
                todo=args.todo,
            )
            if not (
                isinstance(stored, dict)
                and same_numbers(left=stored, right=fresh)
            ):
                state["previous"] = (
                    stored if isinstance(stored, dict) else None
                )
                state["snapshot"] = fresh
            state["updated_at"] = now_iso()
            state["updated"] = datetime.now().astimezone().date().isoformat()
            _save_state(path=state_path, state=state)
    write_block(todo=args.todo, block=render(state=state, todo=args.todo))
    write_block(
        todo=args.todo,
        block=render_progress(state=state, todo=args.todo),
        name="progress",
    )
    if not args.quiet:
        _ = stdout.write(
            summary(state=state, todo=args.todo) + "\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
