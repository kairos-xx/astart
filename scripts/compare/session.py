"""Own the three shared source trees of one integrated comparison run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.source.api import parse

if TYPE_CHECKING:
    from astart import CommentedModule


@final
@dataclass(frozen=True, slots=True)
class SourceView:
    """Source text and its single authoritative parsed module.

    Attributes:
        source (str): Original source text.
        tree (CommentedModule): Shared native module and semantic graph.

    """

    source: str
    tree: CommentedModule


@final
@dataclass(frozen=True, slots=True)
class ComparisonSession:
    """Shared inputs for annotation, artifact, evidence and opacity analysis.

    Attributes:
        input (SourceView): Untyped baseline.
        reference (SourceView): Curated reference.
        output (SourceView): Actual conversion output.

    """

    input: SourceView
    reference: SourceView
    output: SourceView

    @classmethod
    def create(
        cls,
        *,
        untyped: str,
        typed: str,
        converted: str,
    ) -> ComparisonSession:
        """Parse each comparison input exactly once.

        Args:
            untyped (str): Input baseline source.
            typed (str): Curated reference source.
            converted (str): Actual output source.

        Returns:
            ComparisonSession:
                A session whose trees are reused by every report phase.

        """
        return cls(
            input=SourceView(source=untyped, tree=parse(source=untyped)),
            reference=SourceView(source=typed, tree=parse(source=typed)),
            output=SourceView(source=converted, tree=parse(source=converted)),
        )
