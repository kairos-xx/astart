"""Core source operations independent of the rule-catalog API."""

from __future__ import annotations

from typing import Literal

from astart.source.ast import CommentedModule


def parse(*, source: str, filename: str = "<memory>") -> CommentedModule:
    """Parse Python source into an editable annotated module.

    Args:
        source (str): Python source text.
        filename (str): Source identity for Python's syntax diagnostics.

    Returns:
        CommentedModule:
            Editable module retaining lexical and semantic information.

    """
    return CommentedModule.parse(source=source, filename=filename)


def unparse(
    *,
    tree: CommentedModule,
    preserve_formatting: bool = True,
    on_format_conflict: Literal["raise", "fallback"] = "raise",
) -> str:
    """Serialize an editable module, preserving original formatting by default.

    Args:
        tree (CommentedModule): Editable module to serialize.
        preserve_formatting (bool): Retain concrete source formatting where
            possible.
        on_format_conflict (Literal['raise', 'fallback']): Strategy for edits
            without safe lexical patches.

    Returns:
        str: Updated Python source.

    """
    return tree.unparse(
        preserve_formatting=preserve_formatting,
        on_format_conflict=on_format_conflict,
    )
