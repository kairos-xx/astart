"""PRS001 ``parsing.module-does-not-parse``: a file Python rejects.

No other rule can run when the module does not parse, so this detector
stands alone: it takes raw source and returns one candidate carrying the
syntax diagnostic, or nothing when the source parses cleanly.

"""

from __future__ import annotations

from ast import parse
from typing import final

from astart.rules.model import Span
from astart.rules.procedural import Candidate


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_message (str): Evidence key for the parser's message.
        evidence_offset (str): Evidence key for the byte offset, when known.

    """

    evidence_message: str = "message"
    evidence_offset: str = "offset"


def find_parse_error(*, source: str, filename: str) -> Candidate | None:
    """Report the first syntax error in a source file.

    Args:
        source (str): Python source text.
        filename (str): Name used in the span and diagnostic.

    Returns:
        Candidate | None: One candidate for the syntax error, or ``None``.

    """
    try:
        _ = parse(source=source, filename=filename)
    except SyntaxError as error:
        return Candidate(
            span=Span(
                file=filename,
                start_line=error.lineno or 1,
                start_column=(error.offset or 1) - 1,
                end_line=error.end_lineno or error.lineno or 1,
                end_column=(error.end_offset or error.offset or 1) - 1,
            ),
            evidence={
                Constants.evidence_message: error.msg,
                Constants.evidence_offset: error.offset or 0,
            },
        )
    return None
