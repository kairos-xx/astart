"""Audit docs/planning/TODO.md for consistency.

Checks structure, task format, references and generated blocks.

Usage (from the repository root)::

    python -m scripts.todo_update lint [--todo docs/planning/TODO.md]
        [--archive docs/planning/TODO-archive.md]

Prints a summary of problems by kind with the first examples. Exit code 0 when
there are no errors (warnings never fail the run), 1 otherwise.

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from sys import stdout
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root.
        priorities (Final[frozenset[str]]): Allowed priority values.
        statuses (Final[frozenset[str]]): Allowed status values.
        readiness (Final[frozenset[str]]): Allowed readiness values.
        meta_labels (Final[tuple[str, ...]]): Metadata labels in their required
            order.
        blocks (Final[tuple[str, ...]]): Names of generated blocks (marker
            names).
        placeholders (Final[tuple[str, ...]]): Text that must never remain.
        examples (Final[int]): Examples printed per problem kind.
        areas (Final[frozenset[str]]): Allowed Area values.

    """

    root: Final[Path] = Path(__file__).resolve().parent.parent.parent
    priorities: Final[frozenset[str]] = frozenset(
        {"P0", "P1", "P2", "P3", "Untriaged"},
    )
    statuses: Final[frozenset[str]] = frozenset({"open", "done"})
    readiness: Final[frozenset[str]] = frozenset(
        {"ready", "needs recipe", "done"},
    )
    meta_labels: Final[tuple[str, ...]] = (
        "Status",
        "Priority",
        "Area",
        "Readiness",
        "Effort",
    )
    blocks: Final[tuple[str, ...]] = (
        "dashboard",
        "status",
        "index",
        "progress",
        "conversion",
    )
    placeholders: Final[tuple[str, ...]] = ("_to be written_", "TBD", "FIXME")
    examples: Final[int] = 4
    areas: Final[frozenset[str]] = frozenset(
        {
            "ast",
            "inference",
            "negotiation",
            "types",
            "rules",
            "kwargs",
            "project",
            "stubs",
            "cli",
            "tests",
            "benchmarks",
            "performance",
            "docs",
            "release",
            "backend",
            "risk",
            "uncategorized",
        },
    )


@final
@dataclass(slots=True)
class Task:
    """One task block.

    Attributes:
        identifier (str): Task ID.
        title (str): Heading title.
        line (int): Line number of the heading (1-based).
        body (list[str]): Lines after the heading until the next heading.

    """

    identifier: str
    title: str
    line: int
    body: list[str] = field(default_factory=list)


@final
@dataclass(slots=True)
class Report:
    """Collected problems.

    Attributes:
        errors (dict[str, list[str]]): Error messages by kind.
        warnings (dict[str, list[str]]): Warning messages by kind.

    """

    errors: dict[str, list[str]] = field(default_factory=dict)
    warnings: dict[str, list[str]] = field(default_factory=dict)

    def error(self, *, kind: str, text: str) -> None:
        """Record an error.

        Args:
            kind (str): Problem kind.
            text (str): Message with the location.

        """
        self.errors.setdefault(kind, []).append(text)

    def warn(self, *, kind: str, text: str) -> None:
        """Record a warning.

        Args:
            kind (str): Problem kind.
            text (str): Message with the location.

        """
        self.warnings.setdefault(kind, []).append(text)


def parse_id(*, token: str) -> str | None:
    """Recognise a task ID such as ``M4-06``, ``F-07a`` or ``CC-08-01``.

    Args:
        token (str): A word.

    Returns:
        str | None: The ID, or ``None`` when the word is not shaped like one.

    """
    head, dash, tail = token.partition("-")
    if not dash:
        return None
    letters: str = head.rstrip("0123456789")
    digits: str = head[len(letters) :]
    if not letters or not letters.isalpha() or not letters.isupper():
        return None
    max_prefix_letters: int = 3
    if len(letters) > max_prefix_letters or len(digits) > 1:
        return None
    number, dash2, suffix = tail.partition("-")
    core: str = number[:-1] if number[-1:].islower() else number
    min_digits: int = 2
    if len(core) < min_digits or not core.isdigit():
        return None
    if dash2 and not suffix.isdigit():
        return None
    return token


def words(*, text: str) -> list[str]:
    """Split text into words made of letters, digits and hyphens.

    Args:
        text (str): Any text.

    Returns:
        list[str]: The words, with leading and trailing hyphens removed.

    """
    found: list[str] = []
    current: list[str] = []
    for char in text + " ":
        if char.isalnum() or char == "-":
            current.append(char)
        elif current:
            found.append("".join(current).strip("-"))
            current.clear()
    return [word for word in found if word]


def slug(*, heading: str) -> str:
    """Compute the GitHub anchor of a heading.

    Args:
        heading (str): Heading text without the leading ``#``.

    Returns:
        str: Lower-case text with punctuation removed and spaces as hyphens.

    """
    kept: list[str] = [
        char for char in heading.lower() if char.isalnum() or char in " -_"
    ]
    return "".join(kept).replace(" ", "-")


def split_tasks(*, lines: list[str]) -> tuple[list[Task], list[str]]:
    """Cut the document into task blocks and list all headings.

    Args:
        lines (list[str]): Document lines.

    Returns:
        tuple[list[Task], list[str]]: The task blocks and every heading line
            outside code fences.

    """
    tasks: list[Task] = []
    headings: list[str] = []
    fenced: bool = False
    current: Task | None = None
    for number, line in enumerate(iterable=lines, start=1):
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("#"):
            headings.append(line)
        is_head: bool = not fenced and line.startswith(("## ", "### "))
        if is_head:
            current = None
            if line.startswith("### ") and " — " in line:
                ident, _, title = line[4:].partition(" — ")
                if parse_id(token=ident) is not None:
                    current = Task(identifier=ident, title=title, line=number)
                    tasks.append(current)
            continue
        if current is not None:
            current.body.append(line)
    return tasks, headings


def check_markers(*, text: str, report: Report) -> None:
    """Check each generated block has exactly one start and one end marker.

    Args:
        text (str): Document text.
        report (Report): Where problems go.

    """
    for name in Constants.blocks:
        start: int = text.count(f"<!-- {name}:start -->")
        end: int = text.count(f"<!-- {name}:end -->")
        if start != 1 or end != 1:
            report.error(
                kind="generated block markers",
                text=f"{name}: {start} start / {end} end (need 1 / 1)",
            )
        elif text.find(f"<!-- {name}:start -->") > text.find(
            f"<!-- {name}:end -->",
        ):
            report.error(
                kind="generated block markers",
                text=f"{name}: end before start",
            )


def _meta_of(*, task: Task) -> dict[str, str]:
    """Read the ``- **Label:** value`` lines at the top of a task body.

    Args:
        task (Task): The task block.

    Returns:
        dict[str, str]: Metadata label to value for the first lines that carry
            one.

    """
    meta: dict[str, str] = {}
    for line in task.body[:6]:
        if line.startswith("- **") and ":** " in line:
            label, _, value = line[4:].partition(":** ")
            meta[label] = value.strip()
    return meta


def _check_values(*, meta: dict[str, str], where: str, report: Report) -> bool:
    """Check the status, priority, readiness and effort values.

    Args:
        meta (dict[str, str]): Metadata label to value.
        where (str): Location text for messages.
        report (Report): Where problems go.

    Returns:
        bool: Whether the task is marked done.

    """
    for label, allowed, kind in (
        ("Status", Constants.statuses, "bad status"),
        ("Priority", Constants.priorities, "bad priority"),
        ("Readiness", Constants.readiness, "bad readiness"),
    ):
        if meta[label] not in allowed:
            report.error(kind=kind, text=f"{where}: {meta[label]}")
    done: bool = meta["Status"] == "done"
    if done != (meta["Readiness"] == "done"):
        report.error(
            kind="status and readiness disagree",
            text=f"{where}: {meta['Status']} / {meta['Readiness']}",
        )
    size, _, tier = meta["Effort"].partition(" · ")
    if size not in {"S", "M", "L", "XL", "unsized"} or tier not in {
        "light",
        "standard",
        "deep",
    }:
        report.error(kind="bad effort", text=f"{where}: {meta['Effort']}")
    return done


def _check_open(
    *,
    task: Task,
    body: str,
    size: str,
    where: str,
    report: Report,
) -> None:
    """Check the steps and done-when requirements of an open task.

    Args:
        task (Task): The task block.
        body (str): The task body joined into one string.
        size (str): The effort size token.
        where (str): Location text for messages.
        report (Report): Where problems go.

    """
    if size == "unsized":
        report.warn(kind="open task unsized", text=where)
    numbered: int = sum(
        1
        for line in task.body
        if line.lstrip()[:1].isdigit() and ". " in line.lstrip()[:5]
    )
    if "**Steps:**" not in body and numbered <= 1:
        report.error(kind="open task without steps", text=where)
    if "Done when" not in body and "Acceptance" not in body:
        report.error(kind="open task without done-when", text=where)


def _check_done(*, body: str, where: str, report: Report) -> None:
    """Check the evidence requirement of a done task.

    Args:
        body (str): The task body joined into one string.
        where (str): Location text for messages.
        report (Report): Where problems go.

    """
    if "Evidence" not in body:
        report.warn(kind="done task without evidence", text=where)


def _check_text(*, body: str, title: str, where: str, report: Report) -> None:
    """Check the body for placeholders and the title for truncation.

    Args:
        body (str): The task body joined into one string.
        title (str): The task heading title.
        where (str): Location text for messages.
        report (Report): Where problems go.

    """
    for marker in Constants.placeholders:
        if marker in body:
            report.error(kind="placeholder left", text=f"{where}: {marker}")
    suspicious: bool = (
        title in Constants.priorities
        or title.endswith(("…", "(", ",", ":"))
        or title.count("`") % 2 == 1
        or title.count("(") != title.count(")")
    )
    if suspicious:
        report.warn(kind="broken or truncated title", text=f"{where}: {title}")


def check_task(*, task: Task, report: Report) -> None:
    """Check one task block.

    Args:
        task (Task): The task.
        report (Report): Where problems go.

    """
    where: str = f"{task.identifier} (line {task.line})"
    meta: dict[str, str] = _meta_of(task=task)
    missing: list[str] = [m for m in Constants.meta_labels if m not in meta]
    if missing:
        report.error(
            kind="task metadata missing",
            text=f"{where}: {', '.join(missing)}",
        )
        return
    done: bool = _check_values(meta=meta, where=where, report=report)
    size: str = meta["Effort"].partition(" · ")[0]
    body: str = "\n".join(task.body)
    if done:
        _check_done(body=body, where=where, report=report)
    else:
        _check_open(
            task=task,
            body=body,
            size=size,
            where=where,
            report=report,
        )
    _check_text(body=body, title=task.title, where=where, report=report)


def _line_id(*, line: str) -> str | None:
    """Pull the task ID a table row or ``###`` heading defines, if any.

    Args:
        line (str): One document line.

    Returns:
        str | None: The ID when the line defines one, else ``None``.

    """
    if line.startswith("| ") and " | " in line:
        first: str = line[2:].partition(" |")[0].strip()
        if parse_id(token=first) is not None:
            return first
    if line.startswith("### ") and " — " in line:
        ident: str = line.lstrip("# ").partition(" — ")[0]
        if parse_id(token=ident) is not None:
            return ident
    return None


def _cited_ids(*, text: str, defined: set[str]) -> Counter[str]:
    """Count in-text ID citations that no definition covers.

    Args:
        text (str): Document text.
        defined (set[str]): Every defined task ID.

    Returns:
        Counter[str]: Citation counts by undefined ID.

    """
    prefixes: set[str] = {i.partition("-")[0] for i in defined}
    cited: Counter[str] = Counter()
    for word in words(text=text):
        ident: str = parse_id(token=word) or ""
        if (
            ident
            and ident.partition("-")[0] in prefixes
            and ident not in defined
        ):
            cited[ident] += 1
    return cited


def check_references(
    *,
    text: str,
    archive: str,
    tasks: list[Task],
    report: Report,
) -> None:
    """Check duplicate IDs and cited IDs that are defined nowhere.

    Args:
        text (str): Document text.
        archive (str): Archive text (may be empty).
        tasks (list[Task]): Task blocks of the document.
        report (Report): Where problems go.

    """
    counts: Counter[str] = Counter(task.identifier for task in tasks)
    for ident, count in counts.items():
        if count > 1:
            report.error(kind="duplicate task id", text=f"{ident} x{count}")
    defined: set[str] = set(counts)
    for source in (text, archive):
        for line in source.split(
            sep="\n",
        ):
            found_id: str | None = _line_id(line=line)
            if found_id is not None:
                defined.add(found_id)
    for ident, count in sorted(
        _cited_ids(text=text, defined=defined).items(),
    ):
        report.warn(
            kind="cited id defined nowhere",
            text=f"{ident} (cited {count}x)",
        )


def check_chapters(*, headings: list[str], report: Report) -> None:
    """Check numbered chapters run 1..N once each and in order.

    Args:
        headings (list[str]): All heading lines.
        report (Report): Where problems go.

    """
    numbers: list[int] = []
    for line in headings:
        if line.startswith("## "):
            head: str = line[3:].partition(". ")[0]
            if head.isdigit():
                numbers.append(int(head))
    if numbers != list(range(1, len(numbers) + 1)):
        report.error(kind="chapter numbering", text=f"found {numbers}")
    dup: list[str] = [
        h
        for h, c in Counter(headings).items()
        if c > 1 and h.startswith("## ")
    ]
    for heading in dup:
        report.error(kind="duplicate chapter heading", text=heading)


def check_anchors(*, text: str, headings: list[str], report: Report) -> None:
    """Check that every link in the task index resolves to a heading.

    Args:
        text (str): Document text.
        headings (list[str]): All heading lines.
        report (Report): Where problems go.

    """
    seen: Counter[str] = Counter()
    anchors: set[str] = set()
    for line in headings:
        base: str = slug(heading=line.lstrip("# "))
        anchors.add(base if seen[base] == 0 else f"{base}-{seen[base]}")
        seen[base] += 1
    start: int = text.find("<!-- index:start -->")
    end: int = text.find("<!-- index:end -->")
    bad: int = 0
    for line in text[start:end].split(
        sep="\n",
    ):
        if line.startswith("| [") and "](#" in line:
            anchor: str = line.partition("](#")[2].partition(")")[0]
            if anchor not in anchors:
                bad += 1
                if bad <= Constants.examples:
                    report.warn(
                        kind="index link does not resolve",
                        text=anchor,
                    )
    if bad > Constants.examples:
        report.warn(
            kind="index link does not resolve",
            text=f"... {bad} in total",
        )


def lint(*, text: str, archive: str) -> Report:
    """Run every check.

    Args:
        text (str): Document text.
        archive (str): Archive text (may be empty).

    Returns:
        Report: The collected problems.

    """
    report: Report = Report()
    tasks, headings = split_tasks(
        lines=text.split(
            sep="\n",
        ),
    )
    check_markers(text=text, report=report)
    for task in tasks:
        check_task(task=task, report=report)
    check_references(text=text, archive=archive, tasks=tasks, report=report)
    check_chapters(headings=headings, report=report)
    check_anchors(text=text, headings=headings, report=report)
    areas: Counter[str] = Counter()
    for task in tasks:
        for line in task.body[:6]:
            if line.startswith("- **Area:** "):
                areas[line.partition(":** ")[2].strip()] += 1
    unknown: dict[str, int] = {
        name: count
        for name, count in areas.items()
        if name not in Constants.areas
    }
    if unknown:
        report.warn(
            kind="area outside the vocabulary",
            text=str(object=unknown),
        )
    return report


def main() -> int:
    """Lint the TODO file and print the report.

    Returns:
        int: 1 when there are errors, otherwise 0.

    """
    parser: ArgumentParser = ArgumentParser(prog="todo_update lint")
    parser.add_argument(
        "--todo",
        type=Path,
        default=Constants.root / "docs" / "planning" / "TODO.md",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Constants.root / "docs" / "planning" / "TODO-archive.md",
    )
    args: Namespace = parser.parse_args()
    text: str = args.todo.read_text(encoding="utf-8")
    archive: str = (
        args.archive.read_text(encoding="utf-8")
        if args.archive.exists()
        else ""
    )
    report: Report = lint(text=text, archive=archive)
    for label, group in (
        ("ERROR", report.errors),
        ("warning", report.warnings),
    ):
        for kind, items in sorted(group.items()):
            _ = stdout.write(f"{label}: {kind}: {len(items)}\n")
            for item in items[: Constants.examples]:
                _ = stdout.write(f"    {item}\n")
    total_errors: int = sum(len(v) for v in report.errors.values())
    total_warnings: int = sum(len(v) for v in report.warnings.values())
    _ = stdout.write(f"\n{total_errors} errors, {total_warnings} warnings\n")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
