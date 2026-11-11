r"""Whitespace rules: WSP001 blank runs through WSP005 string literals.

The first two rules read raw source lines: more than two consecutive blank
lines inside code, and trailing spaces or tabs on any line. WSP003 counts
the literals the split rewrite changes, WSP004 the comments the wrap
rewrite changes, and WSP005 the ``\\\\n`` escapes the triple-quote rewrite
expands. Docstring bodies
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
from astart.source.ast import Comment, SingleLineComment
from astart.source.comment_directives import control_kind

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from tokenize import TokenInfo


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_blank_run (Final[int]): Blank lines tolerated inside a file.
        evidence_count (str): Evidence key for the run length.
        evidence_line (str): Evidence key for the offending line.
        directive_heads (Final[frozenset[str]]): Grouped module constant.

    """

    max_blank_run: Final[int] = 2
    evidence_count: str = "blank_lines"
    evidence_line: str = "line"

    directive_heads: Final[frozenset[str]] = frozenset(
        {
            "noqa",
            "nosec",
            "type",
            "fmt",
            "isort",
            "autopep8",
            "pylint",
            "local-checker",
            "mypy",
            "pyright",
            "basedpyright",
            "ruff",
            "sourcery",
            "pragma",
            "coverswitch",
            "xenon",
            "noinspection",
        },
    )


def find_blank_line_runs(
    *,
    source: str,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag runs of more than two consecutive blank lines.

    Args:
        source (str): Python source text.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: One candidate per excessive run, at its first
            extra line.

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
        source (str): Python source text.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: One candidate per trailing-whitespace line.

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
        source (str): Python source text.

    Returns:
        int: The number of excessive runs outside string literals.

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
        source (str): Python source text.

    Returns:
        int: The number of editable lines with trailing whitespace.

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
        source (str): Python source text.

    Returns:
        str: The source with excessive blank runs shortened.

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
        source (str): Python source text.

    Returns:
        str: The source without trailing horizontal whitespace.

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
        body: str = line.rstrip("""\
\r
""")
        ending: str = line[len(body) :]
        out.append(body.rstrip(" \t") + ending)
    return "".join(out)


def _blank_keep(*, lines: list[str], end: int) -> int:
    """Return how many blank lines a run may keep.

    Args:
        lines (list[str]): Source lines with endings.
        end (int): Index of the first non-blank line after the run.

    Returns:
        int: ``max_blank_run`` at module level, one inside a block, zero at
            end of file.

    """
    if end == len(lines):
        return 0
    indent: int = len(lines[end]) - len(lines[end].lstrip())
    return Constants.max_blank_run if indent == 0 else 1


def _eol(*, line: str) -> str:
    r"""Return the line ending of a source line.

    Args:
        line (str): Source line, possibly with its ending.

    Returns:
        str: ``"\\\\r\\\\n"``, ``"\\\\n"`` or ``""``.

    """
    if line.endswith("""\
\r
"""):
        return """\
\r
"""
    if line.endswith("\n"):
        return "\n"
    return ""


def _string_rows(*, source: str) -> frozenset[int]:
    """Return the 1-based rows covered by multi-line string tokens.

    Args:
        source (str): Python source text.

    Returns:
        frozenset[int]: Rows that hold string-literal content;
            empty when the source does not tokenize.

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


def _directive_comment(*, text: str) -> bool:
    """Tell whether comment text carries single-line directive semantics.

    Ordinary comments that survived classification as
    :class:`~astart.source.ast.SingleLineComment` can still be tool
    directives the parser does not model, such as ``# type: int`` or
    ``# mypy: ...``; their meaning depends on staying on one line.

    Args:
        text (str): Comment token text, including its hash marker.

    Returns:
        bool: ``True`` for recognized tool directive heads.

    """
    body: str = text[1:].lstrip()
    if control_kind(body=body) is not None:
        return True
    parts: list[str] = body.split(maxsplit=1)
    if not parts:
        return False
    head: str = parts[0].split(sep=":", maxsplit=1)[0]
    return head.casefold() in Constants.directive_heads


def _list_like(*, body: str) -> bool:
    """Tell whether comment text opens like a list item or rule.

    Args:
        body (str): Comment text without its hash marker.

    Returns:
        bool: ``True`` for ``-``/``*``/``+`` bullets, ``1.`` enumerations
            and box-drawing fillers whose line structure must survive.

    """
    head: str = body[:1]
    if head in "-*+•|_":
        return True
    return head.isdigit() and len(body) > 1 and body[1] in ".)"


def _wrap_comment_body(*, body: str, width: int) -> list[str]:
    """Break comment text into word-boundary chunks inside ``width``.

    Args:
        body (str): Comment text without its hash marker.
        width (int): Maximum characters per emitted chunk.

    Returns:
        list[str]: Chunks in order; a word wider than ``width`` occupies
            its own chunk and overflows rather than being split.

    """
    chunks: list[str] = []
    current: str = ""
    for word in body.split():
        candidate: str = word if not current else f"{current} {word}"
        if len(candidate) <= width or not current:
            current = candidate
        else:
            chunks.append(current)
            current = word
    chunks.append(current)
    return chunks


def _comment_hashes(*, text: str) -> str:
    """Return the leading run of hash characters of a comment.

    Args:
        text (str): Comment text including its hash marker.

    Returns:
        str: The ``#`` run, e.g. ``"##"`` for ``## note``.

    """
    return text[: len(text) - len(text.lstrip("#"))]


def comment_wrap_plans(
    *,
    comments: Iterable[Comment],
    source_lines: list[str],
    line_length: int,
) -> list[tuple[tuple[SingleLineComment, ...], tuple[str, ...]]]:
    """Plan comment-node replacements for overlong comment paragraphs.

    Adjacent standalone :class:`SingleLineComment` nodes sharing
    indentation and hash marker form a paragraph. A paragraph reflows
    only when one of its physical lines exceeds ``line_length`` and no
    member reads as a list item, filler rule or directive. The returned
    texts carry hash markers but no indentation; the writer supplies it.

    Args:
        comments (Iterable[Comment]): Module comment nodes in source
            order.
        source_lines (list[str]): Source split into lines.
        line_length (int): Maximum allowed line length.

    Returns:
        list[tuple[tuple[SingleLineComment, ...], tuple[str, ...]]]:
            ``(members, replacement texts)`` pairs for
            ``replace_comment_lines``.

    """
    plans: list[tuple[tuple[SingleLineComment, ...], tuple[str, ...]]] = []
    paragraphs: list[list[SingleLineComment]] = []
    current: list[SingleLineComment] = []
    for comment in comments:
        member: bool = (
            isinstance(comment, SingleLineComment)
            and not comment.inline
            and comment.lineno <= len(source_lines)
            and bool(
                comment.text[
                    len(_comment_hashes(text=comment.text)) :
                ].strip(),
            )
            and not _directive_comment(text=comment.text)
        )
        if not member or not isinstance(comment, SingleLineComment):
            if current:
                paragraphs.append(current)
                current = []
            continue
        if current and (
            comment.lineno != current[-1].lineno + 1
            or comment.col_offset != current[-1].col_offset
            or _comment_hashes(text=comment.text)
            != _comment_hashes(text=current[-1].text)
        ):
            paragraphs.append(current)
            current = []
        current.append(comment)
    if current:
        paragraphs.append(current)
    for paragraph in paragraphs:
        overlong: list[SingleLineComment] = [
            comment
            for comment in paragraph
            if len(source_lines[comment.lineno - 1]) > line_length
        ]
        if not overlong or any(
            _list_like(
                body=comment.text[
                    len(_comment_hashes(text=comment.text)) :
                ].strip(),
            )
            for comment in paragraph
        ):
            continue
        first: SingleLineComment = paragraph[0]
        indent: str = source_lines[first.lineno - 1][: first.col_offset]
        hashes: str = _comment_hashes(text=first.text)
        width: int = line_length - len(indent) - len(hashes) - 1
        if width <= 0:
            continue
        joined: str = " ".join(
            comment.text[len(_comment_hashes(text=comment.text)) :].strip()
            for comment in paragraph
        )
        chunks: list[str] = _wrap_comment_body(body=joined, width=width)
        if len(chunks) <= 1:
            continue
        plans.append(
            (
                tuple(paragraph),
                tuple(f"{hashes} {chunk}" for chunk in chunks),
            ),
        )
    return plans
