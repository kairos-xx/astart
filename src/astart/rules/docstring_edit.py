"""Pure text edits for Google-style docstrings.

The functions work on the docstring *value* as the parser stores it: the
text between the quotes, with the body indented like the code around it and
the closing quotes on a line of their own. They add missing parameter
entries, remove entries for parameters that no longer exist, and tidy
whitespace. Nothing here touches the AST.
"""

from __future__ import annotations

from dataclasses import dataclass
from re import Match, Pattern
from re import compile as pattern
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        parameter_titles: Section titles that list parameters.
        entry_placeholder: Description written for an added entry.
        header: Pattern of a section header line.
        entry: Pattern of a parameter entry line.
        step: One indentation level.

    """

    parameter_titles: Final[frozenset[str]] = frozenset(
        {"Args", "Arguments", "Parameters"},
    )
    entry_placeholder: Final[str] = "Describe {name}."
    header: Final[Pattern[str]] = pattern(
        pattern=r"^(?P<pad>\s*)(?P<title>[A-Z][A-Za-z ]*):\s*$",
    )
    entry: Final[Pattern[str]] = pattern(
        pattern=r"^(?P<pad>\s*)(?P<name>\*{0,2}\w+)(?:\s*\([^)]*\))?\s*:",
    )
    step: Final[str] = "    "


@final
@dataclass(frozen=True, slots=True)
class _Entry:
    """One parameter entry.

    Attributes:
        name: Parameter name without stars.
        start: Index of its first line.
        end: Index after its last non-blank line.

    """

    name: str
    start: int
    end: int


@final
@dataclass(frozen=True, slots=True)
class _Section:
    """One parameter section.

    Attributes:
        header: Index of the header line.
        pad: Indentation of the header.
        end: Index after the last non-blank body line.
        entries: Its entries in order.

    """

    header: int
    pad: str
    end: int
    entries: tuple[_Entry, ...]


def _indent_of(*, line: str) -> int:
    """Count the leading whitespace characters of a line.

    Args:
        line: Any line.

    Returns:
        The width of its indentation.

    """
    return len(line) - len(line.lstrip())


def _entries(
    *,
    lines: Sequence[str],
    first: int,
    last: int,
) -> tuple[_Entry, ...]:
    """Split a section body into entries.

    Args:
        lines: All docstring lines.
        first: Index of the first body line.
        last: Index after the last non-blank body line.

    Returns:
        The entries; continuation lines belong to the entry above them.

    """
    body: list[int] = [i for i in range(first, last) if lines[i].strip()]
    if not body:
        return ()
    margin: int = _indent_of(line=lines[body[0]])
    starts: list[int] = []
    for index in body:
        found: Match[str] | None = Constants.entry.match(string=lines[index])
        if found is not None and _indent_of(line=lines[index]) == margin:
            starts.append(index)
    result: list[_Entry] = []
    for position, start in enumerate(iterable=starts):
        limit: int = (
            starts[position + 1] if position + 1 < len(starts) else last
        )
        end: int = limit
        while end > start + 1 and not lines[end - 1].strip():
            end -= 1
        head: Match[str] | None = Constants.entry.match(string=lines[start])
        name: str = "" if head is None else head.group("name").lstrip("*")
        result.append(_Entry(name=name, start=start, end=end))
    return tuple(result)


def _sections(*, lines: Sequence[str]) -> list[_Section]:
    """Find the parameter sections of a docstring.

    Args:
        lines: All docstring lines.

    Returns:
        Each section with its entries.

    """
    found: list[_Section] = []
    for index, line in enumerate(iterable=lines):
        match: Match[str] | None = Constants.header.match(string=line)
        if (
            match is None
            or match.group("title") not in Constants.parameter_titles
        ):
            continue
        margin: int = len(match.group("pad"))
        last: int = index + 1
        for cursor in range(index + 1, len(lines)):
            if not lines[cursor].strip():
                continue
            if _indent_of(line=lines[cursor]) <= margin:
                break
            last = cursor + 1
        found.append(
            _Section(
                header=index,
                pad=match.group("pad"),
                end=last,
                entries=_entries(lines=lines, first=index + 1, last=last),
            ),
        )
    return found


def _first_tail_header(*, lines: Sequence[str]) -> int | None:
    """Find the first section header after which a new section may not go.

    Args:
        lines: All docstring lines.

    Returns:
        The index of the first section header line, or ``None``.

    """
    for index, line in enumerate(iterable=lines):
        if index and Constants.header.match(string=line) is not None:
            return index
    return None


def _bare(*, name: str) -> str:
    """Strip the stars from a parameter name.

    Args:
        name: Name as written in a signature or entry.

    Returns:
        The name without stars.

    """
    return name.lstrip("*")


def entry_names(*, doc: str) -> frozenset[str]:
    """List the parameters a docstring's text already has entries for.

    Args:
        doc: Docstring value.

    Returns:
        Entry names without stars, from every parameter section.

    """
    lines: list[str] = doc.split(sep="\n")
    return frozenset(
        entry.name
        for section in _sections(lines=lines)
        for entry in section.entries
    )


def add_parameter_entries(
    *,
    doc: str,
    names: Sequence[str],
    order: Sequence[str],
    indent: str,
) -> str:
    """Add an entry for each name that the docstring does not document.

    Args:
        doc: Docstring value.
        names: Parameter names to add, with their stars, in signature order.
        order: All parameter names of the signature without stars, in order,
            used to place a new entry after its predecessor.
        indent: Indentation of the docstring body.

    Returns:
        The edited docstring value.

    """
    lines: list[str] = doc.split(sep="\n")
    if len(lines) == 1:
        lines = [doc, "", indent]
    for name in names:
        lines = _add_one(lines=lines, name=name, order=order, indent=indent)
    return "\n".join(lines)


def _add_one(
    *,
    lines: list[str],
    name: str,
    order: Sequence[str],
    indent: str,
) -> list[str]:
    """Add one entry, creating the section when it is missing.

    Args:
        lines: Docstring lines.
        name: Parameter name with its stars.
        order: Signature order without stars.
        indent: Indentation of the docstring body.

    Returns:
        The new lines.

    """
    bare: str = _bare(name=name)
    sections: list[_Section] = _sections(lines=lines)
    text: str = f"{name}: {Constants.entry_placeholder.format(name=bare)}"
    if not sections:
        return _new_section(lines=lines, text=text, indent=indent)
    section: _Section = sections[0]
    rank: dict[str, int] = {
        item: place for place, item in enumerate(iterable=order)
    }
    before: list[_Entry] = [
        entry
        for entry in section.entries
        if rank.get(entry.name, len(rank)) < rank.get(bare, len(rank))
    ]
    pad: str = (
        lines[section.entries[0].start][
            : _indent_of(line=lines[section.entries[0].start])
        ]
        if section.entries
        else section.pad + Constants.step
    )
    if before:
        position: int = before[-1].end
    elif section.entries:
        position = section.entries[0].start
    else:
        position = section.header + 1
    return [*lines[:position], pad + text, *lines[position:]]


def _new_section(*, lines: list[str], text: str, indent: str) -> list[str]:
    """Create an ``Args:`` section holding one entry.

    Args:
        lines: Docstring lines.
        text: The entry text without indentation.
        indent: Indentation of the docstring body.

    Returns:
        The new lines.

    """
    tail: int | None = _first_tail_header(lines=lines)
    pad: str = indent
    if tail is not None:
        pad = lines[tail][: _indent_of(line=lines[tail])]
    block: list[str] = [f"{pad}Args:", f"{pad}{Constants.step}{text}"]
    if tail is not None:
        return [*lines[:tail], *block, "", *lines[tail:]]
    closing: bool = len(lines) > 1 and not lines[-1].strip()
    cut: int = len(lines) - 1 if closing else len(lines)
    head: list[str] = lines[:cut]
    if head and head[-1].strip():
        head.append("")
    return [*head, *block, *lines[cut:]]


def parameter_entry_names(*, doc: str) -> tuple[str, ...]:
    """List parameter entry names in document order.

    Args:
        doc: Docstring value.

    Returns:
        Bare entry names across every parameter section.

    """
    lines: list[str] = doc.split(sep="\n")
    return tuple(
        entry.name
        for section in _sections(lines=lines)
        for entry in section.entries
    )


def rename_parameter_entry(*, doc: str, old: str, new: str) -> str:
    """Rename one parameter entry, keeping its description.

    Args:
        doc: Docstring value.
        old: Entry name to rename, with or without stars.
        new: Replacement name as written in the signature.

    Returns:
        The edited docstring value, or ``doc`` when no entry matches.

    """
    wanted: str = _bare(name=old)
    lines: list[str] = doc.split(sep="\n")
    for section in _sections(lines=lines):
        for entry in section.entries:
            if entry.name != wanted:
                continue
            head: Match[str] | None = Constants.entry.match(
                string=lines[entry.start],
            )
            if head is None:
                continue
            line: str = lines[entry.start]
            lines[entry.start] = (
                line[: head.start("name")] + new + line[head.end("name") :]
            )
            return "\n".join(lines)
    return doc


def remove_parameter_entries(*, doc: str, names: Sequence[str]) -> str:
    """Remove the entries of parameters that no longer exist.

    Args:
        doc: Docstring value.
        names: Parameter names to remove, with or without stars.

    Returns:
        The edited docstring value; an emptied section disappears too.

    """
    wanted: set[str] = {_bare(name=name) for name in names}
    lines: list[str] = doc.split(sep="\n")
    for section in reversed(_sections(lines=lines)):
        doomed: list[_Entry] = [
            entry for entry in section.entries if entry.name in wanted
        ]
        if not doomed:
            continue
        for entry in reversed(doomed):
            del lines[entry.start : entry.end]
        if len(doomed) == len(section.entries):
            end: int = section.end - sum(
                entry.end - entry.start for entry in doomed
            )
            del lines[section.header : end]
            _close_gap(lines=lines, at=section.header)
    return "\n".join(lines)


def _close_gap(*, lines: list[str], at: int) -> None:
    """Remove a doubled or dangling blank line left where a block was cut.

    Args:
        lines: Docstring lines, edited in place.
        at: Index where the block used to start.

    """
    after_blank: bool = at < len(lines) and not lines[at].strip()
    before_blank: bool = at > 0 and not lines[at - 1].strip()
    is_closing: bool = at == len(lines) - 1 and len(lines) > 1
    if before_blank and (after_blank or is_closing):
        del lines[at - 1]


def tidy_docstring(*, doc: str, indent: str) -> str:
    """Strip trailing space, collapse blank runs and align the body.

    Args:
        doc: Docstring value.
        indent: Indentation of the docstring body.

    Returns:
        The tidied value; a one-line docstring is returned as it is.

    """
    lines: list[str] = [line.rstrip() for line in doc.split(sep="\n")]
    if len(lines) == 1:
        return lines[0]
    closing: bool = not lines[-1].strip() and len(lines) > 1
    body: list[str] = lines[1:-1] if closing else lines[1:]
    aligned: list[str] = [
        (indent + line if line.strip() else "")
        for line in dedent(text="\n".join(body)).split(sep="\n")
    ]
    collapsed: list[str] = []
    for line in aligned:
        if line or not collapsed or collapsed[-1]:
            collapsed.append(line)
    while closing and collapsed and not collapsed[-1]:
        collapsed.pop()
    result: list[str] = [lines[0], *collapsed]
    if closing:
        result.append(indent)
    return "\n".join(result)
