"""Callable parameter kinds shared by contract and relation analysis."""

from __future__ import annotations

from enum import StrEnum


class ParameterKind(StrEnum):
    """All five Python callable parameter kinds.

    Attributes:
        KEYWORD_ONLY: Keyword only associated with this instance.
        POSITIONAL_ONLY: Positional only associated with this instance.
        POSITIONAL_OR_KEYWORD: Positional or keyword associated with this
            instance.
        VAR_KEYWORD: Var keyword associated with this instance.
        VAR_POSITIONAL: Var positional associated with this instance.

    """

    POSITIONAL_ONLY = "POSITIONAL_ONLY"
    POSITIONAL_OR_KEYWORD = "POSITIONAL_OR_KEYWORD"
    VAR_POSITIONAL = "VAR_POSITIONAL"
    KEYWORD_ONLY = "KEYWORD_ONLY"
    VAR_KEYWORD = "VAR_KEYWORD"
