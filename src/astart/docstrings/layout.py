"""Preserve exact documentation prose around native field edits."""

from __future__ import annotations

from astart.source.errors import FormatPreservationError


def preserve_docstring_content(
    *,
    original: str,
    old_summary: str,
    new_summary: str,
    old_description: str,
    new_description: str,
) -> str:
    """Apply PEP 257 prose edits without normalizing original indentation.

    Args:
        original (str): Exact string value before structured edits.
        old_summary (str): Originally parsed one-line summary.
        new_summary (str): Current edited summary.
        old_description (str): Originally parsed normalized prose.
        new_description (str): Edited prose to interpolate into original
            layout.

    Returns:
        str: Updated raw docstring value retaining layout outside changed
            prose.

    Raises:
        FormatPreservationError: If text locations are ambiguous.

    """
    if "\n" in new_summary or "\r" in new_summary:
        msg: str = "Docstring summary must occupy one physical line."
        raise FormatPreservationError(msg)
    lines: list[str] = original.splitlines(keepends=True)
    if not lines:
        if old_summary:
            msg = "Original summary text has no lexical representation."
            raise FormatPreservationError(msg)
        return new_summary
    first: int = next(
        (index for index, line in enumerate(iterable=lines) if line.strip()),
        -1,
    )
    if first < 0 or lines[first].strip() != old_summary:
        msg = "Original docstring summary has no unique source location."
        raise FormatPreservationError(msg)
    previous: str = lines[first]
    content: str = previous.rstrip("""\
\r
""")
    left: str = content[: len(content) - len(content.lstrip(" \t"))]
    right: str = previous[len(content) :]
    lines[first] = left + new_summary + right
    if old_description == new_description:
        return "".join(lines)
    if not old_description:
        msg = "Inserting new prose without a source anchor is ambiguous."
        raise FormatPreservationError(msg)
    description: list[str] = old_description.splitlines()
    matches: list[int] = [
        index
        for index in range(first + 1, len(lines) - len(description) + 1)
        if all(
            lines[index + offset].strip() == raw.strip()
            for offset, raw in enumerate(iterable=description)
        )
    ]
    if len(matches) != 1:
        msg = "Original docstring description does not have a unique span."
        raise FormatPreservationError(msg)
    begin: int = matches[0]
    sample: str = lines[begin]
    indent: str = sample[: len(sample) - len(sample.lstrip(" \t"))]
    ending: str = (
        """\
\r
"""
        if """\
\r
"""
        in sample
        else "\n"
        if "\n" in sample
        else ""
    )
    replacement: list[str] = [
        indent + text + ending if text else ending
        for text in new_description.splitlines()
    ]
    lines[begin : begin + len(description)] = replacement
    return "".join(lines)
