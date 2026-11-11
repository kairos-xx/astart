"""Tests and lint for the TODO tooling (R-25, R-26)."""

from __future__ import annotations

from argparse import Namespace
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from importlib import import_module
from io import StringIO
from json import dumps, loads
from os import utime
from pathlib import Path
from subprocess import CompletedProcess, run
from sys import executable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Final, cast, final

import pytest

from scripts.todo_update import status_update, todo_index, todo_lint
from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_true,
)

type DictListStr = dict[str, list[str]]

if TYPE_CHECKING:
    from types import ModuleType

    from scripts.todo_update.todo_index import Task


dispatcher: ModuleType = import_module(name="scripts.todo_update.__main__")


@final
class Constants:
    """Shared fixtures for the TODO-tooling tests.

    Attributes:
        blocks (Final[str]): Marker pairs the linter requires once each.
        open_task (Final[str]): One valid open task block.
        done_meta (Final[str]): Metadata lines of a done task.

    """

    blocks: Final[str] = "\n".join(
        f"<!-- {name}:start -->\n<!-- {name}:end -->"
        for name in ("dashboard", "status", "index", "progress", "conversion")
    )
    open_task: Final[str] = """\
### M1-01 — Sample open task
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · light

**Steps:**
1. First.
2. Second.

**Done when:** it works.
"""
    done_meta: Final[str] = (
        "- **Status:** done\n"
        "- **Priority:** P2\n"
        "- **Area:** tests\n"
        "- **Readiness:** done\n"
        "- **Effort:** S · light\n"
    )


def _doc(*, task: str) -> str:
    """Build a minimal TODO document around one task block.

    Args:
        task (str): Task text (may be several blocks or empty).

    Returns:
        str: Document text with a chapter heading and every block marker.

    """
    return f"## 1. Chapter one\n\n{task}\n{Constants.blocks}\n"


def _todo_file(*, tmp_path: Path, task: str = "") -> Path:
    """Write a minimal TODO file for ledger commands.

    Args:
        tmp_path (Path): Test directory.
        task (str): Optional task block.

    Returns:
        Path: Path of the written file.

    """
    todo: Path = tmp_path / "TODO.md"
    todo.write_text(data=_doc(task=task), encoding="utf-8")
    return todo


def _state(*, items: tuple[str, ...] = ()) -> dict[str, status_update.Json]:
    """Build a minimal valid ledger state.

    Args:
        items (tuple[str, ...]): Open items.

    Returns:
        dict[str, status_update.Json]: State object with the required keys.

    """
    open_items: list[status_update.Json] = list(items)
    return {"history": [], "checks": {}, "open_items": open_items}


def _state_file(
    *,
    tmp_path: Path,
    state: dict[str, status_update.Json],
) -> Path:
    """Write a ledger state file.

    Args:
        tmp_path (Path): Test directory.
        state (dict[str, status_update.Json]): State object.

    Returns:
        Path: Path of the written file.

    """
    path: Path = tmp_path / "status.json"
    path.write_text(data=dumps(obj=state, indent=2), encoding="utf-8")
    return path


def test_bar_empty_middle_and_full() -> None:
    """Progress bars handle zero, half and empty totals."""
    expect_equal(
        actual=status_update.bar(value=0, total=10),
        expected="░" * 20,
    )
    expect_equal(
        actual=status_update.bar(value=5, total=10),
        expected="█" * 10 + "░" * 10,
    )
    expect_equal(
        actual=status_update.bar(value=10, total=10),
        expected="█" * 20,
    )
    expect_equal(
        actual=status_update.bar(value=3, total=0),
        expected="░" * 20,
    )


def test_delta_text_directions() -> None:
    """Change text reports better, worse, equal and unknown deltas."""
    expect_equal(
        actual=status_update.delta_text(now=5, before=3, lower=False),
        expected="+2 better",
    )
    expect_equal(
        actual=status_update.delta_text(now=5, before=8, lower=False),
        expected="-3 worse",
    )
    expect_equal(
        actual=status_update.delta_text(now=5, before=8, lower=True),
        expected="-3 better",
    )
    expect_equal(
        actual=status_update.delta_text(now=4, before=4, lower=False),
        expected="no change",
    )
    expect_equal(
        actual=status_update.delta_text(now=None, before=4, lower=False),
        expected="n/a",
    )


def test_ago_and_human_time_fixed() -> None:
    """Time helpers format fixed instants deterministically."""
    iso: str = "2026-11-08T18:00:00+00:00"
    base: datetime = datetime(
        year=2026,
        month=11,
        day=8,
        hour=18,
        minute=0,
        second=44,
        tzinfo=UTC,
    )
    expect_equal(
        actual=status_update.ago(iso=iso, reference=base),
        expected="just now",
    )
    base = datetime(
        year=2026,
        month=11,
        day=8,
        hour=18,
        minute=5,
        second=0,
        tzinfo=UTC,
    )
    expect_equal(
        actual=status_update.ago(iso=iso, reference=base),
        expected="5 minutes ago",
    )
    base = datetime(
        year=2026,
        month=11,
        day=8,
        hour=20,
        minute=0,
        second=0,
        tzinfo=UTC,
    )
    expect_equal(
        actual=status_update.ago(iso=iso, reference=base),
        expected="2 hours ago",
    )
    base = datetime(
        year=2026,
        month=11,
        day=10,
        hour=19,
        minute=0,
        second=0,
        tzinfo=UTC,
    )
    expect_equal(
        actual=status_update.ago(iso=iso, reference=base),
        expected="2 days ago",
    )
    expect_equal(
        actual=status_update.human_time(iso=iso),
        expected="Sun 08 Nov 2026, 18:00 UTC",
    )


def test_render_minimal_state(tmp_path: Path) -> None:
    """The ledger shows the history row, the target row and each check.

    Args:
        tmp_path (Path): Test directory.

    """
    state: dict[str, status_update.Json] = _state()
    state["history"] = [
        {
            "at": "2026-11-08T18:00:00+00:00",
            "label": "sample",
            "p_exact": 50,
            "p_wrong": 1,
            "p_total": 100,
            "v_exact": 20,
            "v_wrong": 0,
            "v_total": 40,
        },
    ]
    state["checks"] = {
        "lint": {
            "status": "pass",
            "at": "2026-11-08T18:00:00+00:00",
            "note": "clean",
        },
    }
    text: str = status_update.render(
        state=state,
        todo=_todo_file(tmp_path=tmp_path),
    )
    expect_in(item="| sample |", container=text)
    expect_in(item="| target | 90 % exact, 0 wrong |", container=text)
    expect_in(item="| lint | pass |", container=text)
    expect_in(item="50 / 1 of 100", container=text)


def test_apply_changes_only_the_intended_field() -> None:
    """check, item add/remove and note touch exactly one field."""
    state: dict[str, status_update.Json] = _state(items=("first", "second"))
    changed: bool = status_update.apply(
        args=Namespace(command="check", name="lint", status="fail", note="n"),
        state=state,
    )
    expect_true(condition=changed)
    checks: dict[str, status_update.Json] = cast(
        typ="dict[str, status_update.Json]",
        val=state["checks"],
    )
    lint: dict[str, status_update.Json] = cast(
        typ="dict[str, status_update.Json]",
        val=checks["lint"],
    )
    expect_equal(actual=lint["status"], expected="fail")
    expect_equal(actual=state["open_items"], expected=["first", "second"])
    _ = status_update.apply(
        args=Namespace(command="item", action="add", value="third"),
        state=state,
    )
    expect_equal(
        actual=state["open_items"],
        expected=["first", "second", "third"],
    )
    _ = status_update.apply(
        args=Namespace(command="item", action="remove", value="1"),
        state=state,
    )
    expect_equal(actual=state["open_items"], expected=["second", "third"])
    _ = status_update.apply(
        args=Namespace(command="note", text="dirty tree"),
        state=state,
    )
    expect_equal(actual=state["working_tree"], expected="dirty tree")


def test_pair_reads_stdin_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pair command consumes the benchmarks JSON from stdin.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    report: str = dumps(
        obj={
            "parameters_and_returns": {
                "correct": 5,
                "wrong": 1,
                "to_recover": 50,
            },
            "variables": {"correct": 3, "wrong": 0, "to_recover": 20},
        },
    )
    monkeypatch.setattr(
        target=status_update,
        name="stdin",
        value=StringIO(initial_value=report),
    )
    state: dict[str, status_update.Json] = _state()
    changed: bool = status_update.apply(
        args=Namespace(command="pair", label="run"),
        state=state,
    )
    expect_true(condition=changed)
    history: list[status_update.Json] = cast(
        typ="list[status_update.Json]",
        val=state["history"],
    )
    entry: dict[str, status_update.Json] = cast(
        typ="dict[str, status_update.Json]",
        val=history[-1],
    )
    expect_equal(actual=entry["label"], expected="run")
    expect_equal(actual=entry["p_exact"], expected=5)
    expect_equal(actual=entry["p_wrong"], expected=1)
    expect_equal(actual=entry["p_total"], expected=50)
    expect_equal(actual=entry["v_exact"], expected=3)


def test_write_block_requires_status_markers(tmp_path: Path) -> None:
    """A missing status marker pair stops the update.

    Args:
        tmp_path (Path): Test directory.

    """
    todo: Path = tmp_path / "TODO.md"
    todo.write_text(
        data="""\
no markers here
""",
        encoding="utf-8",
    )
    with pytest.raises(
        expected_exception=SystemExit,
        match="markers not found",
    ):
        status_update.write_block(todo=todo, block="x")


def test_write_block_preserves_text_outside_markers(tmp_path: Path) -> None:
    """Only the region between the markers is replaced.

    Args:
        tmp_path (Path): Test directory.

    """
    todo: Path = tmp_path / "TODO.md"
    todo.write_text(
        data="""\
head
<!-- status:start -->
old
<!-- status:end -->
tail
""",
        encoding="utf-8",
    )
    status_update.write_block(todo=todo, block="new")
    expect_equal(
        actual=todo.read_text(encoding="utf-8"),
        expected="""\
head
<!-- status:start -->
new
<!-- status:end -->
tail
""",
    )


def test_missing_progress_markers_are_silent(tmp_path: Path) -> None:
    """The optional progress block is skipped when its markers are absent.

    Args:
        tmp_path (Path): Test directory.

    """
    todo: Path = tmp_path / "TODO.md"
    todo.write_text(
        data="""\
no markers here
""",
        encoding="utf-8",
    )
    status_update.write_block(todo=todo, block="x", name="progress")
    expect_equal(
        actual=todo.read_text(encoding="utf-8"),
        expected="""\
no markers here
""",
    )


def _seeded_state() -> dict[str, status_update.Json]:
    """Build a state whose snapshot, previous and history agree.

    Returns:
        dict[str, status_update.Json]: A state where a refresh changes nothing.

    """
    numbers: dict[str, status_update.Json] = {
        "p_exact": 10,
        "p_wrong": 1,
        "p_total": 100,
        "v_exact": 5,
        "v_wrong": 0,
        "v_total": 50,
    }
    snapshot: dict[str, status_update.Json] = {
        "at": "2026-11-08T18:00:00+00:00",
        **numbers,
        "tasks_done": 0,
        "tasks_total": 0,
        "tasks_open": 0,
    }
    state: dict[str, status_update.Json] = _state()
    state["history"] = [
        {"at": "2026-11-08T18:00:00+00:00", "label": "s", **numbers},
    ]
    state["snapshot"] = snapshot
    state["previous"] = {**snapshot}
    return state


def test_two_refreshes_show_no_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Consecutive refresh runs keep the delta at ``no change``.

    Args:
        tmp_path (Path): Test directory.
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    state_path: Path = _state_file(tmp_path=tmp_path, state=_seeded_state())
    todo: Path = _todo_file(tmp_path=tmp_path)
    argv: list[str] = [
        "status_update",
        "--state",
        str(object=state_path),
        "--todo",
        str(object=todo),
        "--quiet",
        "refresh",
    ]
    monkeypatch.setattr(target="sys.argv", name=argv)
    expect_equal(actual=status_update.main(), expected=0)
    monkeypatch.setattr(target="sys.argv", name=argv)
    expect_equal(actual=status_update.main(), expected=0)
    rendered: str = status_update.render(
        state=loads(s=state_path.read_text(encoding="utf-8")),
        todo=todo,
    )
    expect_in(item="no change", container=rendered)


def test_validate_state_reports_shape() -> None:
    """Validation names the missing key and the unknown status."""
    bad: dict[str, status_update.Json] = {
        "checks": {"lint": {"status": "banana"}},
        "open_items": [3],
        "snapshot": "oops",
    }
    problems: list[str] = status_update.validate_state(state=bad)
    expect_in(item="missing key: history", container=problems)
    expect_in(
        item="checks.lint.status: unknown status 'banana'",
        container=problems,
    )
    expect_in(item="open_items[0]: expected a string", container=problems)
    expect_in(
        item="snapshot: expected a JSON object or null",
        container=problems,
    )
    expect_equal(
        actual=status_update.validate_state(state=_state()),
        expected=[],
    )


def test_corrupted_state_exits_naming_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A corrupted file exits with code 2 and names the broken key.

    Args:
        tmp_path (Path): Test directory.
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    state_path: Path = _state_file(
        tmp_path=tmp_path,
        state={
            "history": [],
            "checks": {"lint": {"status": "x"}},
            "open_items": [],
        },
    )
    todo: Path = _todo_file(tmp_path=tmp_path)
    errors: StringIO = StringIO()
    monkeypatch.setattr(target=status_update, name="stderr", value=errors)
    monkeypatch.setattr(
        target="sys.argv",
        name=[
            "status_update",
            "--state",
            str(object=state_path),
            "--todo",
            str(object=todo),
            "--quiet",
            "item",
            "add",
            "x",
        ],
    )
    with pytest.raises(expected_exception=SystemExit) as caught:
        _ = status_update.main()
    expect_equal(actual=caught.value.code, expected=2)
    expect_in(item="checks.lint.status", container=errors.getvalue())


def test_stale_lock_is_taken_over(tmp_path: Path) -> None:
    """A lock older than the stale threshold is removed and retried.

    Args:
        tmp_path (Path): Test directory.

    """
    state_path: Path = _state_file(tmp_path=tmp_path, state=_state())
    lock: Path = state_path.with_name(name=f"{state_path.name}.lock")
    lock.touch()
    utime(path=lock, times=(0, 0))
    with status_update.locked(path=state_path):
        expect_true(condition=lock.exists())
    expect_true(condition=not lock.exists())


def test_fresh_lock_blocks_until_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A live lock stops a second run after the retry budget.

    Args:
        tmp_path (Path): Test directory.
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    state_path: Path = _state_file(tmp_path=tmp_path, state=_state())
    lock: Path = state_path.with_name(name=f"{state_path.name}.lock")
    lock.touch()
    monkeypatch.setattr(
        target=status_update.Constants,
        name="lock_attempts",
        value=1,
    )
    try:
        with (
            pytest.raises(expected_exception=SystemExit, match="lock"),
            status_update.locked(path=state_path),
        ):
            pass
    finally:
        lock.unlink(missing_ok=True)


def test_parallel_item_adds_lose_nothing(tmp_path: Path) -> None:
    """Ten parallel ``item add`` runs merge; none is lost.

    Args:
        tmp_path (Path): Test directory.

    """
    state_path: Path = _state_file(tmp_path=tmp_path, state=_state())
    todo: Path = _todo_file(tmp_path=tmp_path)
    script: Path = Path(status_update.__file__ or "")
    command: list[str] = [
        executable,
        str(object=script),
        "--state",
        str(object=state_path),
        "--todo",
        str(object=todo),
        "--quiet",
        "item",
        "add",
    ]

    def spawn(index: int) -> CompletedProcess[str]:
        """Run one ``item add`` subprocess.

        Args:
            index (int): Item number appended to the command.

        Returns:
            CompletedProcess[str]: The finished process.

        """
        return run(
            args=[*command, f"item {index}"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=10)
    with pool:
        futures: list[Future[CompletedProcess[str]]] = [
            pool.submit(spawn, index) for index in range(10)
        ]
        results: list[CompletedProcess[str]] = [
            future.result() for future in futures
        ]
    for result in results:
        expect_equal(
            actual=result.returncode,
            expected=0,
            message=result.stderr,
        )
    items: list[str] = loads(s=state_path.read_text(encoding="utf-8"))[
        "open_items"
    ]
    expect_equal(
        actual=sorted(items),
        expected=[f"item {i}" for i in range(10)],
    )


def test_parse_open_done_and_fenced() -> None:
    """Parse finds tasks, done rows and skips fenced examples."""
    text: str = """\
### M1-01 — Open task
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready

```text
### ZZ-99 — Fenced example
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
```

| M1-03 | Completed row | P2 | tests |
"""
    tasks: list[Task] = todo_index.parse(text=text)
    expect_equal(
        actual=[task.identifier for task in tasks],
        expected=["M1-01", "M1-03"],
    )
    expect_true(condition=not tasks[0].done)
    expect_true(condition=tasks[1].done)
    expect_equal(actual=tasks[1].priority, expected="P2")


def test_dashboard_counts_match_parse() -> None:
    """Done and total counts from parse drive the dashboard numbers."""
    text: str = (
        Constants.open_task + "### M1-02 — Done task\n" + Constants.done_meta
    )
    tasks: list[Task] = todo_index.parse(text=text)
    expect_equal(actual=len(tasks), expected=2)
    expect_equal(
        actual=sum(1 for task in tasks if task.done),
        expected=1,
    )
    body: dict[str, str] = todo_index.split_tasks(text=text)
    expect_equal(actual=sorted(body), expected=["M1-01", "M1-02"])


def test_missing_in_matrix_reports_unknown() -> None:
    """Contract citations of unknown IDs are reported; known ones pass."""
    text: str = (
        """\
## Accuracy contract

- A-01 exact numbers; M1-01 delivers them; X9-99 does not exist.

## START HERE
"""
        + Constants.open_task
    )
    expect_equal(
        actual=todo_index.missing_in_matrix(text=text),
        expected=["X9-99"],
    )


def test_chapter_of_and_chapter_rows(tmp_path: Path) -> None:
    """IDs map to chapters and each chapter gets a bar.

    Args:
        tmp_path (Path): Test directory.

    """
    expect_equal(actual=todo_index.chapter_of(identifier="M1-01"), expected=1)
    expect_equal(actual=todo_index.chapter_of(identifier="R-26"), expected=21)
    expect_equal(actual=todo_index.chapter_of(identifier="ZZ-1"), expected=12)
    task: str = Constants.open_task + (
        "### M2-01 — Done task\n" + Constants.done_meta
    )
    rows: list[str] = status_update.chapter_rows(
        todo=_todo_file(tmp_path=tmp_path, task=task),
    )
    expect_equal(actual=len(rows), expected=2)
    expect_in(item="Foundations", container=rows[0])
    expect_in(item="1 done", container=rows[1])


def test_lint_parse_id_and_slug() -> None:
    """ID and anchor helpers handle the documented shapes."""
    accepted: dict[str, str] = {
        "M4-06": "M4-06",
        "CC-08-01": "CC-08-01",
        "AL-06": "AL-06",
        "API-01": "API-01",
        "F-07a": "F-07a",
    }
    for token, expected in accepted.items():
        expect_equal(
            actual=todo_lint.parse_id(token=token),
            expected=expected,
        )
    rejected: tuple[str, ...] = ("hello", "m4-06", "ABCD-01", "M4-6")
    for token in rejected:
        expect_true(condition=todo_lint.parse_id(token=token) is None)
    expect_equal(
        actual=todo_lint.slug(heading="Typer and small tasks!"),
        expected="typer-and-small-tasks",
    )


def _errors(*, text: str) -> DictListStr:
    """Lint a document and return its errors by kind.

    Args:
        text (str): Document text.

    Returns:
        DictListStr: The error mapping.

    """
    return todo_lint.lint(text=text, archive="").errors


def test_lint_accepts_minimal_document() -> None:
    """A well-formed small document produces no errors."""
    expect_equal(
        actual=_errors(text=_doc(task=Constants.open_task)),
        expected={},
    )


def test_lint_catches_duplicate_id() -> None:
    """Two tasks with the same ID are an error."""
    errors: DictListStr = _errors(
        text=_doc(task=Constants.open_task + Constants.open_task),
    )
    expect_in(item="duplicate task id", container=errors)


def test_lint_catches_missing_done_when() -> None:
    """An open task without a done-when line is an error."""
    task: str = Constants.open_task.replace(
        """\
**Done when:** it works.
""",
        "",
    )
    errors: DictListStr = _errors(text=_doc(task=task))
    expect_in(item="open task without done-when", container=errors)


def test_lint_catches_missing_block_markers() -> None:
    """A missing generated-block marker pair is an error."""
    text: str = _doc(task=Constants.open_task).replace(
        """\
<!-- conversion:start -->
<!-- conversion:end -->""",
        "",
    )
    errors: DictListStr = _errors(text=text)
    expect_in(item="generated block markers", container=errors)


def test_lint_catches_bad_status() -> None:
    """A status outside the vocabulary is an error."""
    errors: DictListStr = _errors(
        text=_doc(
            task=Constants.open_task.replace(
                "- **Status:** open",
                "- **Status:** maybe",
            ),
        ),
    )
    expect_in(item="bad status", container=errors)


def test_lint_catches_chapter_numbering() -> None:
    """Chapters that do not run 1..N are an error."""
    text: str = _doc(task=Constants.open_task).replace(
        "## 1. Chapter one",
        "## 2. Chapter two",
    )
    errors: DictListStr = _errors(text=text)
    expect_in(item="chapter numbering", container=errors)


def test_dispatcher_bare_run_executes_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bare ``python -m scripts.todo_update`` runs every pipeline step.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_invoke(*, module: str, arguments: tuple[str, ...]) -> int:
        """Record one pipeline invocation.

        Args:
            module (str): Dotted module path the dispatcher imports.
            arguments (tuple[str, ...]): Command-line arguments forwarded to
                the module.

        Returns:
            int: Always zero, simulating a successful stage.

        """
        calls.append((module, arguments))
        return 0

    monkeypatch.setattr(target=dispatcher, name="argv", value=["todo_update"])
    monkeypatch.setattr(target=dispatcher, name="_invoke", value=fake_invoke)
    expect_equal(actual=dispatcher.main(), expected=0)
    expected: list[tuple[str, tuple[str, ...]]] = [
        ("scripts.todo_update.todo_index", ("docs/planning/TODO.md",)),
        ("scripts.todo_update.status_update", ("render",)),
        ("scripts.compare.conversion_report", ()),
        ("scripts.todo_update.todo_lint", ()),
    ]
    expect_equal(actual=calls, expected=expected)


def test_dispatcher_no_compare_skips_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--no-compare`` drops only the comparison step.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_invoke(*, module: str, arguments: tuple[str, ...]) -> int:
        """Record one pipeline invocation.

        Args:
            module (str): Dotted module path the dispatcher imports.
            arguments (tuple[str, ...]): Command-line arguments forwarded to
                the module.

        Returns:
            int: Always zero, simulating a successful stage.

        """
        calls.append((module, arguments))
        return 0

    monkeypatch.setattr(
        target=dispatcher,
        name="argv",
        value=["todo_update", "--no-compare"],
    )
    monkeypatch.setattr(target=dispatcher, name="_invoke", value=fake_invoke)
    expect_equal(actual=dispatcher.main(), expected=0)
    expected: list[tuple[str, tuple[str, ...]]] = [
        ("scripts.todo_update.todo_index", ("docs/planning/TODO.md",)),
        ("scripts.todo_update.status_update", ("render",)),
        ("scripts.todo_update.todo_lint", ()),
    ]
    expect_equal(actual=calls, expected=expected)


def test_dispatcher_failed_stage_still_runs_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing step does not stop the pipeline and yields exit 1.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_invoke(*, module: str, arguments: tuple[str, ...]) -> int:
        """Record one pipeline invocation.

        Args:
            module (str): Dotted module path the dispatcher imports.
            arguments (tuple[str, ...]): Command-line arguments forwarded to
                the module.

        Returns:
            int: One for the index stage, zero for every other stage.

        """
        calls.append((module, arguments))
        return 1 if module.endswith("todo_index") else 0

    monkeypatch.setattr(target=dispatcher, name="argv", value=["todo_update"])
    monkeypatch.setattr(target=dispatcher, name="_invoke", value=fake_invoke)
    expect_equal(actual=dispatcher.main(), expected=1)
    expected: list[tuple[str, tuple[str, ...]]] = [
        ("scripts.todo_update.todo_index", ("docs/planning/TODO.md",)),
        ("scripts.todo_update.status_update", ("render",)),
        ("scripts.compare.conversion_report", ()),
        ("scripts.todo_update.todo_lint", ()),
    ]
    expect_equal(actual=calls, expected=expected)


def test_dispatcher_routes_subcommand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit tool name imports its module and forwards argv.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    fake_argv: list[str] = ["todo_update", "lint", "--state", "x"]
    seen: list[str] = []

    def fake_import(*, name: str) -> ModuleType:
        """Record the requested module and return a stub.

        Args:
            name (str): Dotted module path the dispatcher imports.

        Returns:
            ModuleType: A namespace whose ``main`` returns zero.

        """
        seen.append(name)
        return cast(typ="ModuleType", val=SimpleNamespace(main=lambda: 0))

    monkeypatch.setattr(target=dispatcher, name="argv", value=fake_argv)
    monkeypatch.setattr(
        target=dispatcher,
        name="import_module",
        value=fake_import,
    )
    expect_equal(actual=dispatcher.main(), expected=0)
    expect_equal(actual=seen, expected=["scripts.todo_update.todo_lint"])
    expect_equal(actual=fake_argv, expected=["todo_update", "--state", "x"])


def test_dispatcher_rejects_unknown_subcommand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown tool prints usage and exits 2.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    errors: StringIO = StringIO()
    monkeypatch.setattr(
        target=dispatcher,
        name="argv",
        value=["todo_update", "bogus"],
    )
    monkeypatch.setattr(target=dispatcher, name="stderr", value=errors)
    expect_equal(actual=dispatcher.main(), expected=2)
    expect_in(
        item="usage: python -m scripts.todo_update",
        container=errors.getvalue(),
    )
