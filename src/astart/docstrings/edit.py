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

from astart.docstrings.prose import leading_fit, normalize_spacing
from astart.docstrings.type_layout import compact_type

type ListStr = list[str]

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        parameter_titles (Final[frozenset[str]]): Section titles that list
            parameters.
        entry_placeholder (Final[str]): Description written for an added entry.
        header (Final[Pattern[str]]): Pattern of a section header line.
        entry (Final[Pattern[str]]): Pattern of a parameter entry line.
        bare_label (Final[Pattern[str]]): Pattern of an entry line holding only
            ``name (type):``.
        typed_label (Final[Pattern[str]]): Pattern of a bare label capturing
            its ``name`` and ``type`` groups.
        step (Final[str]): One indentation level.
        line_length (Final[int]): Widest emitted docstring line.

    """

    parameter_titles: Final[frozenset[str]] = frozenset(
        {"Args", "Arguments", "Parameters"},
    )
    entry_placeholder: Final[str] = "Describe {name}."
    header: Final[Pattern[str]] = pattern(
        pattern=r"^(?P<pad>\s*)(?P<title>[A-Z][A-Za-z ]*):\s*$",
    )
    entry: Final[Pattern[str]] = pattern(
        pattern=(
            r"^(?P<pad>\s*)(?P<name>\*{0,2}\w+)"
            r"(?:\s*\((?:[^()]|\([^()]*\))*\))?\s*:"
        ),
    )
    bare_label: Final[Pattern[str]] = pattern(
        pattern=(
            r"^(?P<pad>\s*)(?P<name>\*{0,2}\w+)"
            r"(?:\s*[(\[][^\n:]*[)\]])?\s*:\s*$"
        ),
    )
    typed_label: Final[Pattern[str]] = pattern(
        pattern=(
            r"^(?P<pad>\s*)(?P<name>\*{0,2}\w+)"
            r"\s*\((?P<type>.*)\)\s*:\s*$"
        ),
    )
    step: Final[str] = "    "
    line_length: Final[int] = 79


@final
@dataclass(frozen=True, slots=True)
class _Entry:
    """One parameter entry.

    Attributes:
        name (str): Parameter name without stars.
        start (int): Index of its first line.
        end (int): Index after its last non-blank line.

    """

    name: str
    start: int
    end: int


@final
@dataclass(frozen=True, slots=True)
class _Section:
    """One parameter section.

    Attributes:
        header (int): Index of the header line.
        pad (str): Indentation of the header.
        end (int): Index after the last non-blank body line.
        entries (tuple[_Entry, ...]): Its entries in order.

    """

    header: int
    pad: str
    end: int
    entries: tuple[_Entry, ...]


def _indent_of(*, line: str) -> int:
    """Count the leading whitespace characters of a line.

    Args:
        line (str): Any line.

    Returns:
        int: The width of its indentation.

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
        lines (Sequence[str]): All docstring lines.
        first (int): Index of the first body line.
        last (int): Index after the last non-blank body line.

    Returns:
        tuple[_Entry, ...]: The entries; continuation lines belong to the entry
            above them.

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
        lines (Sequence[str]): All docstring lines.

    Returns:
        list[_Section]: Each section with its entries.

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
        lines (Sequence[str]): All docstring lines.

    Returns:
        int | None: The index of the first section header line, or ``None``.

    """
    for index, line in enumerate(iterable=lines):
        if index and Constants.header.match(string=line) is not None:
            return index
    return None


def _bare(*, name: str) -> str:
    """Strip the stars from a parameter name.

    Args:
        name (str): Name as written in a signature or entry.

    Returns:
        str: The name without stars.

    """
    return name.lstrip("*")


def entry_names(*, doc: str) -> frozenset[str]:
    """List the parameters a docstring's text already has entries for.

    Args:
        doc (str): Docstring value.

    Returns:
        frozenset[str]: Entry names without stars, from every parameter
            section.

    """
    lines: ListStr = doc.split(
        sep="\n",
    )
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
        doc (str): Docstring value.
        names (Sequence[str]): Parameter names to add, with their stars, in
            signature order.
        order (Sequence[str]): All parameter names of the signature without
            stars, in
            order, used to place a new entry after its predecessor.
        indent (str): Indentation of the docstring body.

    Returns:
        str: The edited docstring value.

    """
    lines: ListStr = doc.split(
        sep="\n",
    )
    if len(lines) == 1:
        lines = [doc, "", indent]
    for name in names:
        lines = _add_one(lines=lines, name=name, order=order, indent=indent)
    return "\n".join(lines)


def _add_one(
    *,
    lines: ListStr,
    name: str,
    order: Sequence[str],
    indent: str,
) -> ListStr:
    """Add one entry, creating the section when it is missing.

    Args:
        lines (ListStr): Docstring lines.
        name (str): Parameter name with its stars.
        order (Sequence[str]): Signature order without stars.
        indent (str): Indentation of the docstring body.

    Returns:
        ListStr: The new lines.

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


def _new_section(*, lines: ListStr, text: str, indent: str) -> ListStr:
    """Create an ``Args:`` section holding one entry.

    Args:
        lines (ListStr): Docstring lines.
        text (str): The entry text without indentation.
        indent (str): Indentation of the docstring body.

    Returns:
        ListStr: The new lines.

    """
    tail: int | None = _first_tail_header(lines=lines)
    pad: str = indent
    if tail is not None:
        pad = lines[tail][: _indent_of(line=lines[tail])]
    block: ListStr = [f"{pad}Args:", f"{pad}{Constants.step}{text}"]
    if tail is not None:
        return [*lines[:tail], *block, "", *lines[tail:]]
    closing: bool = len(lines) > 1 and not lines[-1].strip()
    cut: int = len(lines) - 1 if closing else len(lines)
    head: ListStr = lines[:cut]
    if head and head[-1].strip():
        head.append("")
    return [*head, *block, *lines[cut:]]


def parameter_entry_names(*, doc: str) -> tuple[str, ...]:
    """List parameter entry names in document order.

    Args:
        doc (str): Docstring value.

    Returns:
        tuple[str, ...]: Bare entry names across every parameter section.

    """
    lines: ListStr = doc.split(
        sep="\n",
    )
    return tuple(
        entry.name
        for section in _sections(lines=lines)
        for entry in section.entries
    )


def rename_parameter_entry(*, doc: str, old: str, new: str) -> str:
    """Rename one parameter entry, keeping its description.

    Args:
        doc (str): Docstring value.
        old (str): Entry name to rename, with or without stars.
        new (str): Replacement name as written in the signature.

    Returns:
        str: The edited docstring value, or ``doc`` when no entry matches.

    """
    wanted: str = _bare(name=old)
    lines: ListStr = doc.split(
        sep="\n",
    )
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
        doc (str): Docstring value.
        names (Sequence[str]): Parameter names to remove, with or without
            stars.

    Returns:
        str: The edited docstring value; an emptied section disappears too.

    """
    wanted: set[str] = {_bare(name=name) for name in names}
    lines: ListStr = doc.split(
        sep="\n",
    )
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


def _close_gap(*, lines: ListStr, at: int) -> None:
    """Remove a doubled or dangling blank line left where a block was cut.

    Args:
        lines (ListStr): Docstring lines, edited in place.
        at (int): Index where the block used to start.

    """
    after_blank: bool = at < len(lines) and not lines[at].strip()
    before_blank: bool = at > 0 and not lines[at - 1].strip()
    is_closing: bool = at == len(lines) - 1 and len(lines) > 1
    if before_blank and (after_blank or is_closing):
        del lines[at - 1]


def _split_point(*, rest: str, margin: int, width: int) -> int:
    """Find the best word-break position within ``width`` columns.

    Prefers the last space at bracket depth zero; falls back to any
    space inside the window. Returns -1 when no break exists.

    Args:
        rest (str): Remaining line content, indentation included.
        margin (int): First column eligible for a break.
        width (int): Widest allowed line length.

    Returns:
        int: Break offset, or -1.

    """
    depth: int = 0
    cut: int = -1
    for pos in range(margin, min(width + 1, len(rest))):
        char: str = rest[pos]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == " " and depth == 0:
            cut = pos
    if cut < 0:
        cut = rest.rfind(" ", margin, width + 1)
    return cut


def _wrap_line(*, line: str, width: int) -> ListStr:
    """Split one overlong line at word boundaries.

    Continuations indent one level past the line's own indentation so
    they stay inside any literal block the line belongs to. A line with
    no usable break is returned unchanged.

    Args:
        line (str): Docstring body line, indentation included.
        width (int): Widest allowed line length.

    Returns:
        ListStr: The line, or its wrapped fragments.

    """
    pad: str = line[: len(line) - len(line.lstrip())]
    hanging: str = pad + Constants.step
    margin: int = len(pad)
    out: ListStr = []
    rest: str = line
    while len(rest) > width:
        cut: int = _split_point(rest=rest, margin=margin, width=width)
        if cut < 0:
            break
        head: str = rest[:cut].rstrip()
        tail: str = rest[cut:].lstrip()
        if not tail:
            break
        out.append(head)
        rest = hanging + tail
        margin = len(hanging)
    out.append(rest)
    return _merge_widow(lines=out, width=width)


def _merge_widow(*, lines: ListStr, width: int) -> ListStr:
    """Merge a single-word last line back into its predecessor.

    Args:
        lines (ListStr): Wrapped fragments produced by ``_wrap_line``.
        width (int): Widest allowed line length.

    Returns:
        ListStr: ``lines`` with a lone-word tail folded upward when it fits.

    """
    if len(lines) <= 1:
        return lines
    last_words: ListStr = lines[-1].split()
    if len(last_words) != 1:
        return lines
    merged: str = lines[-2].rstrip() + " " + last_words[0]
    if len(merged) > width:
        return lines
    return [*lines[:-2], merged]


def tidy_docstring(*, doc: str, indent: str) -> str:
    """Strip trailing space, collapse blank runs and align the body.

    Args:
        doc (str): Docstring value.
        indent (str): Indentation of the docstring body.

    Returns:
        str: The tidied value; a one-line docstring is returned as it is.

    """
    lines: ListStr = [
        line.rstrip()
        for line in doc.split(
            sep="\n",
        )
    ]
    if len(lines) == 1:
        return lines[0]

    closing: bool = not lines[-1].strip() and len(lines) > 1
    body: ListStr = lines[1:-1] if closing else lines[1:]
    aligned: ListStr = [
        (indent + line if line.strip() else "")
        for line in dedent(
            text="\n".join(body),
        ).split(
            sep="\n",
        )
    ]
    collapsed: ListStr = _collapse_blanks(lines=aligned, closing=closing)

    return "\n".join(
        [
            lines[0],
            *_wrap_body(collapsed=collapsed),
            *([indent] if closing else []),
        ],
    )


def _collapse_blanks(*, lines: ListStr, closing: bool) -> ListStr:
    """Drop blank runs and restore the closing-quote spacer.

    Args:
        lines (ListStr): Indent-aligned body lines.
        closing (bool): Whether the docstring ends with a quote-only line.

    Returns:
        ListStr: Lines with at most single blank separators and the
            trailing blank preserved when ``closing``.

    """
    collapsed: ListStr = []
    for line in lines:
        if line or not collapsed or collapsed[-1]:
            collapsed.append(line)

    while closing and collapsed and not collapsed[-1]:
        collapsed.pop()

    collapsed.extend([""] if closing and collapsed and collapsed[-1] else [])
    return collapsed


def _wrap_body(*, collapsed: ListStr) -> ListStr:
    """Wrap each collapsed line, leaving literal blocks verbatim.

    A line ending in ``::`` opens a literal block; following lines that
    are blank or indented deeper than the marker pass through unwrapped.

    Args:
        collapsed (ListStr): Blank-collapsed, indent-aligned body lines.

    Returns:
        ListStr: Wrapped lines with literal blocks preserved.

    """
    wrapped: ListStr = []
    literal_indent: int | None = None
    pending: str | None = None
    index: int = 0
    while index < len(collapsed):
        line: str = pending if pending is not None else collapsed[index]
        pending = None
        index += 1
        stripped: str = line.lstrip()
        indent_level: int = len(line) - len(stripped)
        protected: bool = (
            Constants.entry.match(string=line) is not None
            or Constants.bare_label.match(string=line) is not None
            or stripped.startswith((">>>", "...", "|"))
        )
        literal: bool = literal_indent is not None and (
            not stripped or indent_level > literal_indent
        )
        if literal_indent is not None and not literal:
            literal_indent = None
        if stripped.endswith("::"):
            literal_indent = indent_level
        if not line.strip() or protected:
            if (
                protected
                and not literal
                and not stripped.endswith("::")
                and (
                    pulled := _pull_entry_description(
                        lines=collapsed,
                        index=index,
                    )
                )
                is not None
            ):
                wrapped.append(pulled[0])
                if pulled[1] is not None:
                    pending = pulled[1]
                else:
                    index += 1
                continue
            wrapped.append(line)
            continue
        normalized: str = line if literal else normalize_spacing(line=line)
        wrapped.extend(
            _wrap_line(line=normalized, width=Constants.line_length),
        )
    return wrapped


def _pull_entry_description(
    *,
    lines: ListStr,
    index: int,
) -> tuple[str, str | None] | None:
    """Pull leading description words onto a bare entry label line.

    Google-style entries written as ``name (type):`` followed by an
    indented description line keep the label and prose on one line when
    the leading words still fit the width budget.

    Args:
        lines (ListStr): Collapsed docstring body lines.
        index (int): Position after the candidate entry line.

    Returns:
        tuple[str, str | None] | None:
            The merged label line and the remaining description line, or
            ``None`` when the entry is not a bare label or nothing fits.

    """
    entry_line: str = lines[index - 1]
    if (
        Constants.header.match(string=entry_line) is not None
        or Constants.bare_label.match(string=entry_line) is None
    ):
        return None
    if index >= len(lines):
        return None
    following: str = lines[index]
    fstripped: str = following.strip()
    fpad: int = len(following) - len(following.lstrip())
    epad: int = len(entry_line) - len(entry_line.lstrip())
    if (
        not fstripped
        or fpad <= epad
        or fstripped.startswith((">>>", "...", "|"))
        or Constants.entry.match(string=following) is not None
        or Constants.bare_label.match(string=following) is not None
        or _header_like(lines=lines, index=index, fpad=fpad)
    ):
        return None
    head, rest = leading_fit(
        text=fstripped,
        room=Constants.line_length - len(entry_line) - 1,
    )
    if head:
        remainder: str | None = f"{' ' * fpad}{rest}" if rest else None
        return f"{entry_line} {head}", remainder
    for label in _fallback_labels(line=entry_line):
        fhead, frest = leading_fit(
            text=fstripped,
            room=Constants.line_length - len(label) - 1,
        )
        if not fhead:
            continue
        remainder = f"{' ' * fpad}{frest}" if frest else None
        return f"{label} {fhead}", remainder
    return None


def _header_like(*, lines: ListStr, index: int, fpad: int) -> bool:
    """Tell whether ``lines[index]`` opens a deeper-indented block.

    A ``Title:`` line is structural only when later content sits deeper
    than the candidate; same-indent text marks it as prose that happens
    to end in a colon.

    Args:
        lines (ListStr): Collapsed docstring body lines.
        index (int): Position of the candidate line.
        fpad (int): Indentation of the candidate line.

    Returns:
        bool: Whether the candidate behaves as a section header.

    """
    if Constants.header.match(string=lines[index]) is None:
        return False
    for following in lines[index + 1 :]:
        if not following.strip():
            continue
        return _indent_of(line=following) > fpad
    return True


def _fallback_labels(*, line: str) -> ListStr:
    """Alternative bare-label lines preserving entry parseability.

    Compact type spacing shortens ``name (type):`` labels; dropping the
    type keeps the entry valid when even that admits no description word.

    Args:
        line (str): Bare ``name (type):`` entry line.

    Returns:
        ListStr: Candidate label lines in preference order.

    """
    typed: Match[str] | None = Constants.typed_label.match(string=line)
    if typed is None:
        return []
    pad: str = typed.group("pad")
    name: str = typed.group("name")
    labels: ListStr = []
    compact: str | None = compact_type(type_text=typed.group("type"))
    if compact:
        candidate: str = f"{pad}{name} ({compact}):"
        if candidate != line:
            labels.append(candidate)
    labels.append(f"{pad}{name}:")
    return labels
