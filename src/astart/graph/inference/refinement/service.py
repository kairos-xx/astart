"""Service object around generic inferred-source refinements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from astart.graph.inference.post_refinements import (
    RefinementResult,
    refine_inferred_module,
)

if TYPE_CHECKING:
    from ast import Module


@dataclass(frozen=True, slots=True)
class PostRefinementService:
    """Apply generic refinements and format stage messages."""

    @classmethod
    def create(cls) -> Self:
        """Create the standard refinement service.

        Returns:
            Self: Self produced by this operation.

        """
        return cls()

    @staticmethod
    def refine(*, module: Module) -> RefinementResult:
        """Return refined inferred source and refinement statistics.

        Args:
            module (Module): The module examined while return refined
                inferred source and refinement statistics.

        Returns:
            RefinementResult: RefinementResult produced by this operation.

        """
        return refine_inferred_module(module=module)

    @staticmethod
    def message_for(*, result: RefinementResult) -> str:
        """Render a pipeline validation message for a refinement result.

        Args:
            result (RefinementResult): The result examined while render a
                pipeline
                validation message for a refinement result.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return (
            "generic-refinements: "
            f"annotations={result.stats.changed_annotations}, "
            f"returns={result.stats.changed_returns}, "
            f"calls={result.stats.changed_calls}"
        )
