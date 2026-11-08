"""Whitespace rules: WSP001 blank-line runs and WSP002 trailing space.

Both rules read raw source lines: more than two consecutive blank lines
inside code, and trailing spaces or tabs on any line.  Docstring bodies
are source text too — the WSP002 fix trims them like any other line,
so the detectors report spans and leave rewrite policy to the fix.
"""

from __future__ import annotations

from typing import Final, final

from astart.rules.model import Span
from astart.rules.procedural import Candidate


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
