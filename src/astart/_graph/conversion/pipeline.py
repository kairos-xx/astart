"""Composable graph-only conversion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from astart._graph.conversion.backends import CheckpointGraphBackend
from astart._graph.conversion.stages import (
    ApplyGraphRefinementsStage,
    BackendConversionStage,
    BuildExplanationReportStage,
    BuildInputDocumentStage,
    BuildInputUsageGraphStage,
    BuildOutputDocumentStage,
    BuildOutputUsageGraphStage,
    LoadStubIndexStage,
    RefineBackendSourceStage,
    ResolveInferenceReportStage,
    ValidateSyntaxStage,
)

if TYPE_CHECKING:
    from astart._graph.conversion.context import ConversionContext
    from astart._graph.conversion.interfaces import (
        ConversionBackend,
        ConversionStage,
    )


@dataclass(frozen=True, slots=True)
class ConversionPipeline:
    """Ordered set of API stages for one conversion run.

    Attributes:
        stages: Stages retained as tuple[ConversionStage, ...] by this
            instance.

    """

    stages: tuple[ConversionStage, ...]

    @classmethod
    def create(
        cls,
        *,
        backend: ConversionBackend | None = None,
        validate_syntax: bool = True,
    ) -> Self:
        """Create the standard full-API conversion pipeline.

        Args:
            backend: Backend supplied as ConversionBackend | None for this
                operation.
            validate_syntax: Validate syntax supplied as bool for this
                operation.

        Returns:
            Self produced by this operation.

        """
        selected_backend: ConversionBackend = (
            backend or CheckpointGraphBackend()
        )
        stages: list[ConversionStage] = [
            BuildInputDocumentStage(),
            BuildInputUsageGraphStage(),
            LoadStubIndexStage(),
            BackendConversionStage(backend=selected_backend),
            RefineBackendSourceStage(),
        ]
        stages.extend(
            [
                BuildOutputDocumentStage(),
                ApplyGraphRefinementsStage(),
                BuildOutputUsageGraphStage(),
                ResolveInferenceReportStage(),
                BuildExplanationReportStage(),
            ],
        )
        if validate_syntax:
            stages.append(ValidateSyntaxStage())
        return cls(stages=tuple(stages))

    def run(self, *, context: ConversionContext) -> ConversionContext:
        """Run all stages in order.

        Args:
            context: Context supplied as ConversionContext for this operation.

        Returns:
            ConversionContext produced by this operation.

        """
        current: ConversionContext = context
        stage: ConversionStage
        for stage in self.stages:
            current = stage.run(context=current).with_completed_stage(
                name=stage.name,
            )
        return current

    def stage_names(self) -> tuple[str, ...]:
        """Return the pipeline stage names in execution order.

        Returns:
            tuple[str, ...] produced by this operation.

        """
        return tuple(stage.name for stage in self.stages)
