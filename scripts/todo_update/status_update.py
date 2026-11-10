"""Keep the status ledger in docs/TODO.md up to date.

Usage (from the repository root)::

    python scripts/status_update.py render
    python scripts/status_update.py refresh
    python -m benchmarks.pair A B --engine --min-confidence 0.5 \
        | python scripts/status_update.py pair --label "after G-02"
    python scripts/status_update.py check semantic_run pass --note "15 of 15"
    python scripts/status_update.py item add "run the semantic equivalence run"
    python scripts/status_update.py item remove 2
    python scripts/status_update.py note "what is uncommitted"

Every command prints progress bars, the change since the previous update and
human-readable times (add ``--quiet`` to silence it). State lives in
docs/status.json; the block between the status markers in docs/TODO.md is
generated from it and must not be edited by hand.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from json import dumps, loads
from pathlib import Path
from sys import stdin, stdout
from typing import TYPE_CHECKING, Final, Protocol, final

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from scripts.todo_index import Task

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


class _ParserFactory(Protocol):
    """The ``add_parser`` slice of ``ArgumentParser.add_subparsers``."""

    def add_parser(self, name: str) -> ArgumentParser:
        """Register one subcommand parser.

        Args:
            name: Subcommand name.

        Returns:
            The new subcommand parser.

        """
        ...


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root: Repository root.
        start: Marker opening the generated block.
        end: Marker closing the generated block.
        statuses: Allowed check statuses.
        check_names: Checks shown first, in this order.
        target_share: Share of recoverable annotations the contract asks for.
        bar_width: Width of a progress bar in characters.
        measures: Label, value key, total key and whether lower is better.
        history_keys: Numbers copied from the latest history entry.
        just_now_seconds: Seconds counted as ``just now`` by :func:`ago`.
        minutes_in_hour: Minutes in one hour, an ``ago`` bucket boundary.
        two_days_in_hours: Hours in two days, the last ``ago`` hour bucket.

    """

    root: Final[Path] = Path(__file__).resolve().parent.parent
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


@final
@dataclass(frozen=True, slots=True)
class Row:
    """One line of the progress display.

    Attributes:
        label: What is measured.
        bar: Progress bar.
        percent: Share of the total, as text.
        now: Current value and total, as text.
        change: Change since the previous update, as text.

    """

    label: str
    bar: str
    percent: str
    now: str
    change: str


def number(*, value: Json) -> int | None:
    """Read a count from JSON.

    Args:
        value: A JSON value.

    Returns:
        The integer, or ``None`` when the value is not an integer.

    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def bar(*, value: int, total: int) -> str:
    """Draw a progress bar.

    Args:
        value: Amount done.
        total: Amount that means 100 %.

    Returns:
        A bar of ``Constants.bar_width`` characters, filled in proportion.

    """
    width: int = Constants.bar_width
    if total <= 0:
        return "░" * width
    filled: int = max(0, min(width, round(number=width * value / total)))
    return "█" * filled + "░" * (width - filled)


def percent(*, value: int, total: int) -> str:
    """Format a share as a percentage.

    Args:
        value: Amount done.
        total: Amount that means 100 %.

    Returns:
        For example ``"45.9 %"``, or ``"n/a"`` when the total is zero.

    """
    if total <= 0:
        return "n/a"
    return f"{100 * value / total:.1f} %"


def delta_text(*, now: int | None, before: int | None, lower: bool) -> str:
    """Describe a change between two updates.

    Args:
        now: Current value.
        before: Value at the previous update.
        lower: Whether a lower value is better (for example ``wrong``).

    Returns:
        ``"n/a"`` without a previous value, ``"no change"``, or a signed
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
        An ISO 8601 timestamp such as ``2026-11-08T18:37:12+00:00``.

    """
    return datetime.now().astimezone().isoformat(timespec="seconds")


def human_time(*, iso: str) -> str:
    """Format a timestamp for people.

    Args:
        iso: ISO 8601 timestamp.

    Returns:
        For example ``"Sun 08 Nov 2026, 18:37 WET"``.

    """
    moment: datetime = datetime.fromisoformat(iso)
    return moment.strftime(format="%a %d %b %Y, %H:%M %Z").strip()


def short_time(*, iso: str) -> str:
    """Format a timestamp compactly for table cells.

    Args:
        iso: ISO 8601 timestamp.

    Returns:
        For example ``"08 Nov 2026 18:37"``.

    """
    moment: datetime = datetime.fromisoformat(iso)
    return moment.strftime(format="%d %b %Y %H:%M")


def ago(*, iso: str, reference: datetime | None = None) -> str:
    """Say how long ago a timestamp was.

    Args:
        iso: ISO 8601 timestamp.
        reference: Time to measure from; now when omitted.

    Returns:
        ``"just now"``, ``"N minutes ago"``, ``"N hours ago"`` or
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


def _list(*, state: dict[str, Json], key: str) -> list[Json]:
    """Get a list from the state, creating it when absent.

    Args:
        state: The ledger state.
        key: Key of the list.

    Returns:
        The list stored under the key.

    Raises:
        SystemExit: When the stored value is not a JSON list.

    """
    value: Json = state.setdefault(key, [])
    if not isinstance(value, list):
        msg: str = f"{key}: expected a JSON list"
        raise SystemExit(msg)
    return value


def _dict(*, state: dict[str, Json], key: str) -> dict[str, Json]:
    """Get an object from the state, creating it when absent.

    Args:
        state: The ledger state.
        key: Key of the object.

    Returns:
        The object stored under the key.

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
        todo: Path of the TODO file.

    Returns:
        ``(done, total)``, or ``None`` when the sibling script cannot be
        imported or read.

    """
    for name in ("todo_index", "scripts.todo_index"):
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


def chapter_rows(*, todo: Path) -> list[str]:
    """Draw one progress bar per chapter: done tasks against all tasks.

    Args:
        todo: Path of the TODO file.

    Returns:
        One line per chapter that has tasks, or an empty list when the
        dashboard script cannot be imported.

    """
    for name in ("todo_index", "scripts.todo_index"):
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
    rows: list[str] = []
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


def take_snapshot(*, state: dict[str, Json], todo: Path) -> dict[str, Json]:
    """Record the numbers that updates are compared on.

    Args:
        state: The ledger state.
        todo: Path of the TODO file (for the task counts).

    Returns:
        The latest pair numbers, the task counts and the time.

    """
    history: list[Json] = _list(state=state, key="history")
    last: Json = history[-1] if history else None
    source: dict[str, Json] = last if isinstance(last, dict) else {}
    counts: tuple[int, int] | None = _task_counts(todo=todo)
    snapshot: dict[str, Json] = {"at": now_iso()}
    for key in Constants.history_keys:
        snapshot[key] = source.get(key)
    snapshot["tasks_done"] = None if counts is None else counts[0]
    snapshot["tasks_total"] = None if counts is None else counts[1]
    snapshot["tasks_open"] = None if counts is None else counts[1] - counts[0]
    return snapshot


def progress_rows(
    *,
    snapshot: dict[str, Json],
    previous: dict[str, Json] | None,
) -> list[Row]:
    """Build the progress display.

    Args:
        snapshot: Current numbers.
        previous: Numbers at the previous update, or ``None``.

    Returns:
        One row per measure.

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
    state: dict[str, Json],
    todo: Path,
) -> tuple[dict[str, Json], dict[str, Json] | None]:
    """Pick the current and previous snapshots to display.

    Args:
        state: The ledger state.
        todo: Path of the TODO file.

    Returns:
        The stored snapshot (or a live one before the first update) and the
        previous snapshot, if any.

    """
    stored: Json = state.get("snapshot")
    current: dict[str, Json] = (
        stored
        if isinstance(stored, dict)
        else take_snapshot(state=state, todo=todo)
    )
    before: Json = state.get("previous")
    return current, before if isinstance(before, dict) else None


def _when(*, entry: dict[str, Json]) -> str:
    """Show when a history or check entry happened.

    Args:
        entry: An entry with ``at`` (preferred) or ``date``.

    Returns:
        A compact time, or the plain date for older entries.

    """
    at: Json = entry.get("at")
    if isinstance(at, str):
        return short_time(iso=at)
    return str(object=entry.get("date", "?"))


def render(*, state: dict[str, Json], todo: Path) -> str:
    """Render the ledger as Markdown.

    Args:
        state: The ledger state.
        todo: Path of the TODO file.

    Returns:
        Markdown for the block between the status markers.

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
            "change since the previous update on "
            f"{human_time(iso=previous_at)}"
        )
    lines: list[str] = [
        f"**Updated {stamp}.** {state.get('working_tree', '')}",
        "",
        f"**Progress** ({compared}):",
        "",
        "| Measure | Progress | Now | Change |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {row.label} | `{row.bar}` {row.percent} | {row.now} | "
        f"{row.change} |"
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
    last: dict[str, Json] | None = None
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
    checks: dict[str, Json] = _dict(state=state, key="checks")
    ordered: list[str] = [n for n in Constants.check_names if n in checks]
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


def summary(*, state: dict[str, Json], todo: Path) -> str:
    """Render the terminal summary: bars, deltas and human times.

    Args:
        state: The ledger state.
        todo: Path of the TODO file.

    Returns:
        Plain text for the terminal.

    """
    current, before = _views(state=state, todo=todo)
    rows: list[Row] = progress_rows(snapshot=current, previous=before)
    width: int = max(len(row.label) for row in rows)
    updated: Json = state.get("updated_at")
    lines: list[str] = []
    if isinstance(updated, str):
        lines.append(
            f"Status ledger updated {human_time(iso=updated)} "
            f"({ago(iso=updated)})",
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
    chapters: list[str] = chapter_rows(todo=todo)
    if chapters:
        lines.extend(
            ("", "  Tasks by chapter:", *(f"  {row}" for row in chapters)),
        )
    checks: dict[str, Json] = _dict(state=state, key="checks")
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
        todo: Path of the TODO file.
        block: New block text.
        name: Marker name of the block (``status`` or ``progress``).

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


def render_progress(*, state: dict[str, Json], todo: Path) -> str:
    """Render the compact progress block shown at the top of the file.

    Args:
        state: The ledger state.
        todo: Path of the TODO file.

    Returns:
        Markdown with the progress bars inside a fenced text block, so the
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
    lines: list[str] = [
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
    chapters: list[str] = chapter_rows(todo=todo)
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


def same_numbers(*, left: dict[str, Json], right: dict[str, Json]) -> bool:
    """Tell whether two snapshots hold the same measured numbers.

    Args:
        left: One snapshot.
        right: Another snapshot.

    Returns:
        ``True`` when every measured number is equal (times are ignored), so
        an update that changed nothing does not hide the last real change.

    """
    keys: tuple[str, ...] = (
        *Constants.history_keys,
        "tasks_done",
        "tasks_total",
        "tasks_open",
    )
    return all(left.get(key) == right.get(key) for key in keys)


def apply(*, args: Namespace, state: dict[str, Json]) -> bool:
    """Apply one command to the state.

    Args:
        args: Parsed arguments.
        state: The ledger state, changed in place.

    Returns:
        Whether the state changed (``refresh`` counts as a change).

    Raises:
        SystemExit: When ``pair`` stdin is not the expected benchmarks JSON.

    """
    moment: str = now_iso()
    if args.command == "pair":
        report: Json = loads(s=stdin.read())
        if not isinstance(report, dict):
            msg: str = "stdin: expected the JSON from benchmarks.pair"
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


def main() -> int:
    """Run one ledger command.

    Returns:
        Zero.

    Raises:
        SystemExit: When the state file does not hold a JSON object.

    """
    parser: ArgumentParser = ArgumentParser(prog="status_update")
    parser.add_argument(
        "--state",
        type=Path,
        default=Constants.root / "docs" / "status.json",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Constants.root / "docs" / "TODO.md",
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
    state_loaded: Json = loads(s=state_path.read_text(encoding="utf-8"))
    if not isinstance(state_loaded, dict):
        msg: str = f"{state_path}: expected a JSON object"
        raise SystemExit(msg)
    state: dict[str, Json] = state_loaded
    if apply(args=args, state=state):
        stored: Json = state.get("snapshot")
        fresh: dict[str, Json] = take_snapshot(state=state, todo=args.todo)
        if not (
            isinstance(stored, dict) and same_numbers(left=stored, right=fresh)
        ):
            state["previous"] = stored if isinstance(stored, dict) else None
            state["snapshot"] = fresh
        state["updated_at"] = now_iso()
        state["updated"] = datetime.now().astimezone().date().isoformat()
        _ = state_path.write_text(
            data=dumps(obj=state, indent=2) + "\n",
            encoding="utf-8",
        )
    write_block(todo=args.todo, block=render(state=state, todo=args.todo))
    write_block(
        todo=args.todo,
        block=render_progress(state=state, todo=args.todo),
        name="progress",
    )
    if not args.quiet:
        _ = stdout.write(summary(state=state, todo=args.todo) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
