"""Shared failures at the source-preservation boundary."""

from __future__ import annotations

from typing import final


@final
class FormatPreservationError(ValueError):
    """An AST mutation cannot be reconstructed without risking source loss.

    Attributes:
        recoverable: Whether an enclosing node may repair the failure by
            regenerating itself. Edits that would produce invalid Python
            when regenerated set this to ``False``.

    """

    def __init__(self, *args: str, recoverable: bool = True) -> None:
        """Create the error.

        Args:
            *args (str): Message parts.
            recoverable (bool): Whether an enclosing node may regenerate
                itself.

        """
        super().__init__(*args)
        self.recoverable: bool = recoverable
