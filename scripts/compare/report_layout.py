"""Layout of the conversion report: standard case blocks, groups, hierarchy.

Pure formatting. ``scripts/compare/conversion_report.py`` builds the
data (cases with their already-rendered parts); this module decides
how it is laid out:

* every issue is a *case* with a stable ID and the same block of metadata and
  components,
* cases are collected in *groups* that carry their own metadata block,
* the report is numbered (1 Summary, 2 Issues, 3 Opacity, ...), and every case
  is also written, in full, to a separate cases file.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, final

type ListStr = list[str]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        cases_file (Final[str]): Name of the file that holds every case in
            full.
        components (Final[tuple[str, ...]]): Names of the components of a case
            block, in order.

    """

    cases_file: Final[str] = "conversion-cases.md"
    components: Final[tuple[str, ...]] = (
        "Code",
        "Evidence path",
        "Reading",
        "Why astart",
    )


@final
@dataclass(frozen=True, slots=True)
class Case:
    """One issue, with every part already rendered.

    Attributes:
        ident (str): Stable case ID such as ``PR-017`` or ``VA-042``.
        key (str): Node path as the scorer names it.
        kind (str): ``parameter``, ``return`` or ``variable``.
        verdict (str): ``wrong``, ``missing``, ``narrower``, ...
        family (str): Shape of the author's annotation.
        hard (bool): Whether the family is partly an author choice or a policy.
        author (str): The author's annotation.
        written (str | None): What astart wrote, or ``None``.
        node_link (str): Link to the node in the untyped input.
        owner_link (str): The owning function or class, with a link.
        typed_link (str): Link to the author's line.
        converted_link (str): Link to the converted output's line.
        tasks (str): TODO tasks that close this kind of gap, already linked.
        blocker (str): Why astart left it unannotated, or ``-``.
        diff (ListStr): Lines of the code diff (links and a ``diff`` block).
        evidence (ListStr): Lines of the numbered evidence path.
        reading (str): What the evidence shows against the author's type.
        astart (str): Paragraph on why astart missed or changed the type.

    """

    ident: str
    key: str
    kind: str
    verdict: str
    family: str
    hard: bool
    author: str
    written: str | None
    node_link: str
    owner_link: str
    typed_link: str
    converted_link: str
    tasks: str
    blocker: str
    diff: ListStr
    evidence: ListStr
    reading: str
    astart: str


@final
@dataclass(frozen=True, slots=True)
class Group:
    """A set of cases with a title, a metadata block and optional subgroups.

    Attributes:
        section (str): Section number such as ``2.3.1``.
        title (str): Group title.
        facts (list[tuple[str, str]]): Rows of the group's metadata block.
        cases (list[Case]): Cases of the group.
        expand (int | None): How many cases are written in full (``None`` for
            all).
        children (list[Group]): Subgroups.

    """

    section: str
    title: str
    facts: list[tuple[str, str]]
    cases: list[Case] = field(default_factory=list)
    expand: int | None = None
    children: list[Group] = field(default_factory=list)


@final
@dataclass(frozen=True, slots=True)
class Sections:
    """Rendered lines of the report's content sections.

    Attributes:
        summary (ListStr): Lines of the totals (section 1.1).
        by_family (ListStr): Lines of the gap-by-family table (1.2).
        by_owner (ListStr): Lines of the gap-by-owner table (1.3).
        opacity (ListStr): Lines of section 3.
        annotated (ListStr): Lines of section 4.

    """

    summary: ListStr
    by_family: ListStr
    by_owner: ListStr
    opacity: ListStr
    annotated: ListStr


def table(
    *,
    rows: list[tuple[str, str]],
    head: tuple[str, str] = ("Field", "Value"),
) -> ListStr:
    """Render a two-column table.

    Args:
        rows (list[tuple[str, str]]): ``(field, value)`` pairs.
        head (tuple[str, str]): Column titles.

    Returns:
        ListStr: Markdown lines.

    """
    lines: ListStr = [f"| {head[0]} | {head[1]} |", "| --- | --- |"]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return lines


def count_cases(*, group: Group) -> int:
    """Count the cases of a group and its subgroups.

    Args:
        group (Group): A group.

    Returns:
        int: The total number of cases.

    """
    return len(group.cases) + sum(
        count_cases(group=child) for child in group.children
    )


def case_block(*, case: Case, level: int) -> ListStr:
    """Render one case as a standard block.

    Args:
        case (Case): The case.
        level (int): Heading level of the case (0 gives a bold title instead).

    Returns:
        ListStr: Markdown lines: anchor, title, metadata table, then the
            components Code, Evidence path, Reading and Why astart.

    """
    title: str = f"{case.ident} · {case.verdict} · {case.kind} · `{case.key}`"
    written: str = "—" if case.written is None else f"`{case.written}`"
    hard: str = (
        " *(hard: partly an author choice or policy)*" if case.hard else ""
    )
    rows: list[tuple[str, str]] = [
        ("Case", f"`{case.ident}`"),
        ("Node", f"`{case.key}` — {case.node_link}"),
        ("Kind", case.kind),
        ("Verdict", f"**{case.verdict}**"),
        ("Family", f"{case.family}{hard}"),
        ("Author's type", f"`{case.author}` — {case.typed_link}"),
        ("astart wrote", f"{written} — {case.converted_link}"),
        ("Owner", case.owner_link),
        ("Blocker", case.blocker),
        ("Tasks", case.tasks),
    ]
    return [
        f'<a id="{case.ident.lower()}"></a>',
        "",
        f"{'#' * level} {title}" if level else f"**{title}**",
        "",
        *table(rows=rows),
        "",
        "**Code** (`-` how it is, `+` how it should be)",
        "",
        *case.diff,
        "",
        "**Evidence path** (untyped source)",
        "",
        *case.evidence,
        "",
        f"**Reading.** {case.reading}",
        "",
        case.astart,
        "",
    ]


def index_table(
    *,
    cases: list[Case],
    expanded: set[str],
    other_file: str,
) -> ListStr:
    """Render the index of a group: one row per case, linked.

    Args:
        cases (list[Case]): Cases of the group.
        expanded (set[str]): IDs written in full in the same file.
        other_file (str): File that holds every case, for the others.

    Returns:
        ListStr: Markdown lines.

    """
    lines: ListStr = [
        "| Case | Node | Author's type | astart | Blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        base: str = "" if case.ident in expanded else other_file
        written: str = "—" if case.written is None else f"`{case.written}`"
        lines.append(
            f"| [{case.ident}]({base}#{case.ident.lower()}) | "
            f"`{case.key}` | `{case.author}` | {written} | {case.blocker} |",
        )
    return lines


def render_group(
    *,
    group: Group,
    level: int,
    other_file: str,
) -> ListStr:
    """Render a group: heading, metadata, index and case blocks.

    Args:
        group (Group): The group.
        level (int): Heading level of the group.
        other_file (str): File that holds every case (empty inside that file).

    Returns:
        ListStr: Markdown lines.

    """
    total: int = count_cases(group=group)
    anchor: str = "g" + group.section.replace(".", "-")
    lines: ListStr = [
        f'<a id="{anchor}"></a>',
        "",
        f"{'#' * level} {group.section} {group.title} ({total})",
        "",
        *table(rows=[("Cases", str(object=total)), *group.facts]),
        "",
    ]
    if group.cases:
        shown: list[Case] = (
            group.cases
            if group.expand is None
            else group.cases[: group.expand]
        )
        expanded: set[str] = {case.ident for case in shown}
        lines.extend(
            (
                *index_table(
                    cases=group.cases,
                    expanded=expanded,
                    other_file=other_file,
                ),
                "",
            ),
        )
        if len(shown) < len(group.cases):
            lines.extend(
                (
                    f"*{len(shown)} of {len(group.cases)} cases are written "
                    f"in full below; every case is in "
                    f"[{other_file}]({other_file}).*",
                    "",
                ),
            )
        for case in shown:
            lines.extend(case_block(case=case, level=level + 1))
    for child in group.children:
        lines.extend(
            render_group(group=child, level=level + 1, other_file=other_file),
        )
    return lines


def report_document(
    *,
    title: str,
    meta_rows: list[tuple[str, str]],
    sections: Sections,
    groups: list[Group],
    reproduce: str,
) -> str:
    """Assemble the numbered report.

    Args:
        title (str): Document title.
        meta_rows (list[tuple[str, str]]): Run metadata.
        sections (Sections): Rendered lines of the content sections.
        groups (list[Group]): Top-level issue groups (section 2).
        reproduce (str): Command that reproduces the report.

    Returns:
        str: The report text.

    """
    lines: ListStr = [
        f"# {title}",
        "",
        *table(rows=meta_rows),
        "",
        "**How to read this report.** Every issue is a *case* with a stable "
        "ID (`PR-017` for a parameter or return, `VA-042` for a variable) "
        "and the same block of metadata and components: **Code** (the diff "
        "of how it is against how it should be), **Evidence path** (the "
        "facts in the untyped source that lead to the author's type, linked "
        "to their lines), **Reading** and **Why astart** (why it stopped "
        "short or wrote something else). Cases are grouped by outcome and "
        "family; each group has its own metadata block and an index. The "
        f"[complete list of cases]({Constants.cases_file}) holds every block.",
        "",
        "**Contents:** [1 Summary](#summary) · [2 Issues](#issues) · "
        "[3 Why nodes stay unannotated](#opacity) · "
        "[4 Annotated copy](#annotated) · [5 Reproduce](#reproduce)",
        "",
        '<a id="summary"></a>',
        "",
        "## 1. Summary",
        "",
        "### 1.1 Totals",
        "",
        *sections.summary,
        "",
        "### 1.2 Gap by the author's annotation",
        "",
        *sections.by_family,
        "",
        "### 1.3 Gap by owner",
        "",
        *sections.by_owner,
        "",
        '<a id="issues"></a>',
        "",
        "## 2. Issues",
        "",
    ]
    for group in groups:
        lines.extend(
            render_group(
                group=group,
                level=3,
                other_file=Constants.cases_file,
            ),
        )
    lines.extend(
        (
            '<a id="opacity"></a>',
            "",
            "## 3. Why nodes stay unannotated",
            "",
            *sections.opacity,
            '<a id="annotated"></a>',
            "",
            "## 4. Annotated copy of the converted code",
            "",
            *sections.annotated,
            '<a id="reproduce"></a>',
            "",
            "## 5. Reproduce",
            "",
            f"`{reproduce}`",
        ),
    )
    return "\n".join(lines) + "\n"


def cases_document(*, title: str, groups: list[Group]) -> str:
    """Assemble the file that holds every case in full.

    Args:
        title (str): Document title.
        groups (list[Group]): The same groups as the report, expanded in full.

    Returns:
        str: The document text.

    """
    contents: ListStr = []
    for group in groups:
        contents.append(
            f"- [{group.section} {group.title}]"
            f"(#g{group.section.replace('.', '-')}) "
            f"({count_cases(group=group)})",
        )
        contents.extend(
            f"  - [{child.section} {child.title}]"
            f"(#g{child.section.replace('.', '-')}) "
            f"({count_cases(group=child)})"
            for child in group.children
        )
    lines: ListStr = [
        f"# {title}",
        "",
        "Every issue of the latest conversion run as a standard block. See "
        "[conversion-report.md](conversion-report.md) for the summary and "
        "how to read a block. Generated by "
        "`scripts/compare/conversion_report.py`; do not edit.",
        "",
        "## Contents",
        "",
        *contents,
        "",
    ]
    for group in groups:
        full: Group = Group(
            section=group.section,
            title=group.title,
            facts=group.facts,
            cases=group.cases,
            expand=None,
            children=[
                Group(
                    section=child.section,
                    title=child.title,
                    facts=child.facts,
                    cases=child.cases,
                    expand=None,
                    children=child.children,
                )
                for child in group.children
            ],
        )
        lines.extend(render_group(group=full, level=2, other_file=""))
    return "\n".join(lines) + "\n"
