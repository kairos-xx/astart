"""Whitespace rules: WSP001 blank-line runs and WSP002 trailing space.

Both rules read raw source lines: more than two consecutive blank lines
inside code, and trailing spaces or tabs on any line.  Docstring bodies
are source text too — the WSP002 fix trims them like any other line,
so the detectors report spans and leave rewrite policy to the fix.
"""

from __future__ import annotations

from io import StringIO
from tokenize import (
    FSTRING_MIDDLE,
    STRING,
    TokenError,
    generate_tokens,
)
from typing import TYPE_CHECKING, Final, final

from astart.rules.model import Span
from astart.rules.procedural import Candidate

if TYPE_CHECKING:
    from collections.abc import Iterator
    from tokenize import TokenInfo


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_blank_run: Blank lines tolerated inside a file.
        evidence_count: Evidence key for the run length.
        evidence_line: Evidence key for the offending line.

    """

    max_blank_run: Final[int] = 2
    evidence_count: str = "blank_lines"
    evidence_line: str = "line"


def find_blank_line_runs(
    *,
    source: str,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag runs of more than two consecutive blank lines.

    Args:
        source: Python source text.
        filename: Name used in spans.

    Returns:
        One candidate per excessive run, at its first extra line.

    """
    candidates: list[Candidate] = []
    run: int = 0
    for lineno, line in enumerate(iterable=source.splitlines(), start=1):
        if line.strip():
            run = 0
            continue
        run += 1
        if run == Constants.max_blank_run + 1:
            candidates.append(
                Candidate(
                    span=Span(
                        file=filename,
                        start_line=lineno,
                        start_column=0,
                        end_line=lineno,
                        end_column=0,
                    ),
                    evidence={Constants.evidence_count: run},
                ),
            )
    return tuple(candidates)


def find_trailing_space(
    *,
    source: str,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag lines ending in spaces or tabs.

    Args:
        source: Python source text.
        filename: Name used in spans.

    Returns:
        One candidate per trailing-whitespace line.

    """
    candidates: list[Candidate] = []
    for lineno, line in enumerate(iterable=source.splitlines(), start=1):
        stripped: str = line.rstrip()
        if len(stripped) == len(line):
            continue
        candidates.append(
            Candidate(
                span=Span(
                    file=filename,
                    start_line=lineno,
                    start_column=len(stripped),
                    end_line=lineno,
                    end_column=len(line),
                ),
                evidence={Constants.evidence_line: lineno},
            ),
        )
    return tuple(candidates)


def count_blank_line_runs(*, source: str) -> int:
    """Count blank-line runs the collapse fix can rewrite.

    Runs inside multi-line string literals are string content and do not
    count, so the catalog rule stays quiet where only the docstring rules
    apply.

    Args:
        source: Python source text.

    Returns:
        The number of excessive runs outside string literals.

    """
    protected: frozenset[int] = _string_rows(source=source)
    return sum(
        1
        for hit in find_blank_line_runs(source=source, filename="")
        if hit.span.start_line not in protected
    )


def count_trailing_space_lines(*, source: str) -> int:
    """Count trailing-whitespace lines the strip fix can rewrite.

    Lines inside multi-line string literals are string content and do not
    count.

    Args:
        source: Python source text.

    Returns:
        The number of editable lines with trailing whitespace.

    """
    protected: frozenset[int] = _string_rows(source=source)
    return sum(
        1
        for hit in find_trailing_space(source=source, filename="")
        if hit.span.start_line not in protected
    )


def collapse_blank_lines(*, source: str) -> str:
    """Collapse runs of blank lines to the tolerated maximum.

    Two blank lines are kept before module-level code, one inside an
    indented block, and none at end of file. Lines inside multi-line
    string literals are string content and are left untouched.

    Args:
        source: Python source text.

    Returns:
        The source with excessive blank runs shortened.

    """
    protected: frozenset[int] = _string_rows(source=source)
    lines: list[str] = source.splitlines(keepends=True)
    out: list[str] = []
    index: int = 0
    while index < len(lines):
        line: str = lines[index]
        if line.strip():
            out.append(line)
            index += 1
            continue
        end: int = index
        while end < len(lines) and not lines[end].strip():
            end += 1
        rows: range = range(index + 1, end + 1)
        if any(row in protected for row in rows):
            out.extend(lines[index:end])
        else:
            keep: int = _blank_keep(lines=lines, end=end)
            ending: str = _eol(line=line)
            out.extend(ending for _ in range(min(end - index, keep)))
        index = end
    return "".join(out)


def strip_trailing_space(*, source: str) -> str:
    """Remove trailing spaces and tabs from every editable line.

    Lines inside multi-line string literals are string content and keep
    their whitespace.

    Args:
        source: Python source text.

    Returns:
        The source without trailing horizontal whitespace.

    """
    protected: frozenset[int] = _string_rows(source=source)
    out: list[str] = []
    for lineno, line in enumerate(
        iterable=source.splitlines(keepends=True),
        start=1,
    ):
        if lineno in protected:
            out.append(line)
            continue
        body: str = line.rstrip("\r\n")
        ending: str = line[len(body) :]
        out.append(body.rstrip(" \t") + ending)
    return "".join(out)


def _blank_keep(*, lines: list[str], end: int) -> int:
    """Return how many blank lines a run may keep.

    Args:
        lines: Source lines with endings.
        end: Index of the first non-blank line after the run.

    Returns:
        ``max_blank_run`` at module level, one inside a block, zero at
        end of file.

    """
    if end == len(lines):
        return 0
    indent: int = len(lines[end]) - len(lines[end].lstrip())
    return Constants.max_blank_run if indent == 0 else 1


def _eol(*, line: str) -> str:
    r"""Return the line ending of a source line.

    Args:
        line: Source line, possibly with its ending.

    Returns:
        ``"\\r\\n"``, ``"\\n"`` or ``""``.

    """
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def _string_rows(*, source: str) -> frozenset[int]:
    """Return the 1-based rows covered by multi-line string tokens.

    Args:
        source: Python source text.

    Returns:
        Rows that hold string-literal content; empty when the source
        does not tokenize.

    """
    rows: set[int] = set()
    try:
        tokens: Iterator[TokenInfo] = generate_tokens(
            readline=StringIO(initial_value=source).readline,
        )
        for token in tokens:
            if token.type not in (STRING, FSTRING_MIDDLE):
                continue
            if token.end[0] <= token.start[0]:
                continue
            rows.update(range(token.start[0], token.end[0] + 1))
    except (TokenError, SyntaxError):
        return frozenset()
    return frozenset(rows)
