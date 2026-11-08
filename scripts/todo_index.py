"""Regenerate the dashboard block of ``docs/TODO.md``.

Usage::

    python scripts/todo_index.py docs/TODO.md

Every task in ``docs/TODO.md`` has this exact shape::

    ### F-17 — Title
    - **Status:** open
    - **Priority:** P0
    - **Area:** Backend
    - **Readiness:** ready

The script counts them per chapter and rewrites the text between
``<!-- dashboard:start -->`` and ``<!-- dashboard:end -->``, and the
linked task index between ``<!-- index:start -->`` and
``<!-- index:end -->``.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path
from re import MULTILINE, Match, Pattern
from re import compile as compile_pattern
from sys import argv, stdout
from typing import Final, final


@final
class Constants:
    """Constants for the TODO index script.

    Attributes:
        task: Pattern matching one task heading block.
        done_row: Pattern matching one dashboard table row.
        heading_line: Pattern matching one ATX heading line.
        start: Marker opening the generated dashboard section.
        end: Marker closing the generated dashboard section.
        index_start: Marker opening the generated task index.
        index_end: Marker closing the generated task index.
        priorities: Priority labels recognised in task headers.
        chapters: Chapter definitions: number, title, ID prefixes, scope.

    """

    task: Final[Pattern[str]] = compile_pattern(
        pattern=r"^### ([A-Z]+\d*-\d+(?:-\d+)?[a-z]?) — (.*)\n"
        r"- \*\*Status:\*\* (open|done)\n"
        r"- \*\*Priority:\*\* (\S+)\n"
        r"- \*\*Area:\*\* (.*)\n"
        r"- \*\*Readiness:\*\* (ready|needs recipe|done)$",
        flags=MULTILINE,
    )
    done_row: Final[Pattern[str]] = compile_pattern(
        pattern=r"^\| ([A-Z]+\d*-\d+(?:-\d+)?[a-z]?) \| "
        r"(.*) \| (P\d|Untriaged) \| "
        r"([^|]*) \|$",
        flags=MULTILINE,
    )
    heading_line: Final[Pattern[str]] = compile_pattern(
        pattern=r"^(#{1,6}) (.*)$",
    )
    start: Final[str] = "<!-- dashboard:start -->"
    end: Final[str] = "<!-- dashboard:end -->"
    index_start: Final[str] = "<!-- index:start -->"
    index_end: Final[str] = "<!-- index:end -->"
    priorities: Final[tuple[str, ...]] = ("P0", "P1", "P2", "P3", "Untriaged")

    # (number, title, ID prefixes, scope in one sentence)
    chapters: Final[tuple[tuple[int, str, tuple[str, ...], str], ...]] = (
        (
            1,
            "Foundations and measurement",
            ("M0", "M1"),
            "Checker oracle, benchmarks, gold sets: "
            "how we know a fix is right.",
        ),
        (
            2,
            "Object-oriented code",
            ("M2",),
            "Classes, methods, attributes, constructors and overrides.",
        ),
        (
            3,
            "Whole-project analysis",
            ("M3",),
            "Evidence that crosses module boundaries.",
        ),
        (
            4,
            "Precise types",
            ("M4",),
            "The hint lattice and the prover: which types can be proven.",
        ),
        (
            5,
            "Protocols and generics",
            ("M5",),
            "Synthesised Protocols, TypeVars, ParamSpec.",
        ),
        (
            6,
            "Keyword arguments",
            ("M6",),
            "Making `calls.add-keywords` sound and complete.",
        ),
        (
            7,
            "Speed and shipping",
            ("M7",),
            "Parallelism, reporters, config, packaging, editor integration.",
        ),
        (
            8,
            "Ontology and inference core",
            ("M8",),
            "Rule catalog, predicates, the `_graph` inference engine.",
        ),
        (
            9,
            "Cross-cutting engineering",
            ("CC", "EV"),
            "Calibration, determinism, error containment.",
        ),
        (
            10,
            "Contract negotiation",
            ("F",),
            "Two-way reconciliation of types (the ant farm).",
        ),
        (
            11,
            "Untyped to typed conversion",
            ("P", "T", "W"),
            "Converting `dev/untyped.py` into `dev/typed.py` automatically.",
        ),
        (
            12,
            "Typer and small tasks",
            ("Q", "X"),
            "Small self-contained tasks that need no design.",
        ),
        (
            13,
            "Handoff batch",
            ("H",),
            "Tasks pre-selected for a second agent.",
        ),
        (
            14,
            "Accuracy gaps",
            ("G",),
            "Work the accuracy contract needs that no other chapter owned.",
        ),
        (
            15,
            "Import and Constants style",
            ("S",),
            "TYPE_CHECKING merging, import deduplication, Constants tidying.",
        ),
        (
            16,
            "Inference logic",
            ("I",),
            "Every rule that lets the tool prove a type.",
        ),
        (
            17,
            "API completeness",
            ("API",),
            "Public library API, schemas, plugins, editor integration.",
        ),
        (
            18,
            "Automatic annotation and formatting",
            ("AF",),
            "What gets written and how it is laid out.",
        ),
        (
            21,
            "Risks and contingencies",
            ("R",),
            "Problems forecast in advance, each "
            "with detection and mitigation.",
        ),
        (
            22,
            "Algorithms and intelligence",
            ("AL",),
            "Algorithms that raise accuracy beyond the current special cases.",
        ),
    )


@dataclass(frozen=True, slots=True)
class Task:
    """One parsed task.

    Attributes:
        identifier: Stable ID.
        title: Heading title.
        done: Whether the task is finished.
        priority: ``P0``…``P3`` or ``Untriaged``.
        area: Category.
        readiness: ``ready``, ``needs recipe`` or ``done``.
        position: Offset of the task's heading or row in the document.

    """

    identifier: str
    title: str
    done: bool
    priority: str
    area: str
    readiness: str
    position: int


def prefix_of(*, identifier: str) -> str:
    """Return the group prefix of a task ID.

    Args:
        identifier: Task ID such as ``M4-06`` or ``F-12``.

    Returns:
        Prefix such as ``M4`` or ``F``.

    """
    return identifier.split(sep="-")[0]


def chapter_of(*, identifier: str) -> int:
    """Return the chapter number of a task ID.

    Args:
        identifier: Task ID.

    Returns:
        Chapter number, ``12`` for an unknown prefix.

    """
    prefix: str = prefix_of(identifier=identifier)
    for number, _title, prefixes, _scope in Constants.chapters:
        if prefix in prefixes:
            return number
    return 12


def parse(*, text: str) -> list[Task]:
    """Read every task from the document.

    Args:
        text: Document text.

    Returns:
        Tasks in document order.

    """
    found: list[Task] = [
        Task(
            identifier=m.group(1),
            title=m.group(2),
            done=m.group(3) == "done",
            priority=m.group(4),
            area=m.group(5),
            readiness=m.group(6),
            position=m.start(),
        )
        for m in Constants.task.finditer(string=text)
    ]
    found.extend(
        Task(
            identifier=m.group(1),
            title=m.group(2),
            done=True,
            priority=m.group(3),
            area=m.group(4),
            readiness="done",
            position=m.start(),
        )
        for m in Constants.done_row.finditer(string=text)
    )
    return found


def split_tasks(*, text: str) -> dict[str, str]:
    """Cut the document into the text of each task.

    Args:
        text: Document text.

    Returns:
        Task body text by ID (heading to the next ``## `` or ``### `` heading).

    """
    heads: list[tuple[int, str]] = [
        (m.start(), m.group(1)) for m in Constants.task.finditer(string=text)
    ]
    found: dict[str, str] = {}
    for position, identifier in heads:
        end: int = len(text)
        for marker in ("\n### ", "\n## "):
            nxt: int = text.find(marker, position + 1)
            if nxt != -1:
                end = min(end, nxt)
        found[identifier] = text[position:end]
    return found


def dashboard(*, tasks: list[Task], text_by_task: dict[str, str]) -> str:
    """Render the dashboard.

    Args:
        tasks: Parsed tasks.
        text_by_task: Task body text by ID.

    Returns:
        Markdown for the dashboard block.

    """
    done: int = sum(1 for task in tasks if task.done)
    full: int = 0
    for part in text_by_task.values():
        if all(
            f"**{label}:**" in part
            for label in (
                "Insights",
                "Architecture",
                "Algorithm",
                "Performance",
            )
        ):
            full += 1
    ready: int = sum(1 for t in tasks if t.readiness == "ready")
    lines: list[str] = [
        f"**{done} of {len(tasks)} tasks done "
        f"({100 * done / max(len(tasks), 1):.1f} %). "
        f"{ready} open tasks are ready to start; "
        f"{full} tasks are fully specified (insights, architecture, "
        "algorithm, performance); "
        f"{sum(1 for t in tasks if t.readiness == 'needs recipe')} "
        "still need a recipe.** "
        "Regenerate with `python scripts/todo_index.py docs/TODO.md`.",
        "",
        "| # | Chapter | Done | Open | Ready | P0 | P1 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for number, title, _prefixes, _scope in Constants.chapters:
        members: list[Task] = [
            t for t in tasks if chapter_of(identifier=t.identifier) == number
        ]
        opened: list[Task] = [t for t in members if not t.done]
        lines.append(
            f"| {number} | {title} | {len(members) - len(opened)} | "
            f"{len(opened)} | "
            f"{sum(1 for t in opened if t.readiness == 'ready')} | "
            f"{sum(1 for t in opened if t.priority == 'P0')} | "
            f"{sum(1 for t in opened if t.priority == 'P1')} |",
        )
    for level in ("P0", "P1"):
        lines.extend(
            (
                "",
                f"**Open {level}**",
                "",
                "| ID | Readiness | Task |",
                "| --- | --- | --- |",
            ),
        )
        lines.extend(
            f"| {t.identifier} | {t.readiness} | {t.title.replace('|', '/')} |"
            for t in tasks
            if not t.done and t.priority == level
        )
    return "\n".join(lines)


def slug(*, text: str) -> str:
    """Return the GitHub-style anchor slug of a heading text.

    Args:
        text: Heading text without the leading ``#`` marks.

    Returns:
        Lowercase slug: alphanumerics, ``_`` and ``-`` kept, spaces become
        ``-``, every other character dropped.

    """
    kept: str = "".join(
        character
        for character in text.lower()
        if character.isalnum() or character in " -_"
    )
    return kept.replace(" ", "-")


def anchors(*, text: str) -> list[tuple[int, str]]:
    """Map every heading to its deduplicated anchor slug.

    Args:
        text: Document text.

    Returns:
        ``(offset, slug)`` pairs in document order. Headings inside fenced
        code blocks are skipped, and repeated slugs get ``-1``, ``-2`` …
        suffixes like GitHub's renderer.

    """
    seen: dict[str, int] = {}
    found: list[tuple[int, str]] = []
    fenced: bool = False
    offset: int = 0
    for line in text.splitlines(keepends=True):
        stripped: str = line.strip()
        if stripped.startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            m: Match[str] | None = Constants.heading_line.match(string=line)
            if m is not None:
                base: str = slug(text=m.group(2))
                count: int = seen.get(base, 0)
                seen[base] = count + 1
                found.append(
                    (offset, base if count == 0 else f"{base}-{count}"),
                )
        offset += len(line)
    return found


def task_index(*, text: str, tasks: list[Task]) -> str:
    """Render the linked index of every task.

    Args:
        text: Document text, for heading anchors.
        tasks: Parsed tasks with document positions.

    Returns:
        Markdown table with one row per task: linked ID, title, priority
        and a done checkbox. Open tasks link to their own heading; done
        tasks only exist as ``Completed`` table rows and link to the
        ``### Completed`` section that holds them.

    """
    heads: list[tuple[int, str]] = anchors(text=text)
    positions: list[int] = [offset for offset, _anchor in heads]
    lines: list[str] = [
        "| ID | Task | Priority | Done |",
        "| --- | --- | --- | --- |",
    ]
    for task in sorted(tasks, key=attrgetter("position")):
        slot: int = bisect_right(a=positions, x=task.position) - 1
        anchor: str = heads[slot][1] if slot >= 0 else ""
        mark: str = "x" if task.done else " "
        lines.append(
            f"| [{task.identifier}](#{anchor}) | "
            f"{task.title.replace('|', '/')} | "
            f"{task.priority} | [{mark}] |",
        )
    return "\n".join(lines)


def missing_in_matrix(*, text: str) -> list[str]:
    """List task IDs cited in the Accuracy contract that do not exist.

    Args:
        text: Document text.

    Returns:
        Unknown IDs, sorted.

    """
    start: int = text.find("## Accuracy contract")
    end: int = text.find("## START HERE")
    if start < 0 or end < start:
        return []
    known: set[str] = {task.identifier for task in parse(text=text)}
    cited: set[str] = set(
        compile_pattern(pattern=r"\b([A-Z]{1,2}\d?-\d+)\b").findall(
            string=text[start:end],
        ),
    )
    return sorted(
        cited - known - {"A-" + str(object=n).zfill(2) for n in range(1, 12)},
    )


def main() -> int:
    """Rewrite the dashboard of the document given as the first argument.

    Returns:
        Zero on success, one when the markers are missing.

    """
    path: Path = Path(argv[1])
    text: str = path.read_text(encoding="utf-8")
    if Constants.start not in text or Constants.end not in text:
        stdout.write("dashboard markers not found")
        return 1
    head, _, rest = text.partition(Constants.start)
    _, _, tail = rest.partition(Constants.end)
    block: str = dashboard(
        tasks=parse(text=text),
        text_by_task=split_tasks(text=text),
    )
    updated: str = f"{head}{Constants.start}\n{block}\n{Constants.end}{tail}"
    index_marked: bool = Constants.index_start in updated
    if index_marked != (Constants.index_end in updated):
        stdout.write("index markers not found")
        return 1
    if index_marked:
        ihead, _, irest = updated.partition(Constants.index_start)
        _, _, itail = irest.partition(Constants.index_end)
        index_block: str = task_index(
            text=updated,
            tasks=parse(text=updated),
        )
        updated = (
            f"{ihead}{Constants.index_start}\n"
            f"{index_block}\n{Constants.index_end}{itail}"
        )
    _ = path.write_text(data=updated, encoding="utf-8")
    unknown: list[str] = missing_in_matrix(
        text=path.read_text(encoding="utf-8"),
    )
    if unknown:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
