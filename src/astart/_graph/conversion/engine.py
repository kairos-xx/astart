"""Graph-only conversion orchestration API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from astart._graph.backend.engine import custom_unparse
from astart._graph.conversion.context import (
    ConversionContext,
    ConversionOptions,
)
from astart._graph.conversion.pipeline import ConversionPipeline

if TYPE_CHECKING:
    from ast import Module
    from pathlib import Path

    from astart._graph.inference.explanations import (
        InferenceExplanationReport,
    )
    from astart._graph.inference.resolver import InferenceResult


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Output of a graph-only conversion run.

    Attributes:
        explanation: Explanation retained as InferenceExplanationReport by this
            instance.
        inference: Inference retained as InferenceResult by this instance.
        output_source: Output source retained as str by this instance.
        source_path: Path to the source used by this instance.
        stage_names: Stage names retained as tuple[str, ...] by this instance.
        validation_messages: Validation messages retained as tuple[str, ...] by
            this instance.

    """

    source_path: Path | None
    output_source: str
    inference: InferenceResult
    explanation: InferenceExplanationReport
    validation_messages: tuple[str, ...]
    stage_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphOnlyConverter:
    """Orchestrate graph-based type annotation conversion.

    Attributes:
        pipeline: Pipeline retained as ConversionPipeline by this instance.
        stubs_path: Path to the stubs used by this instance.

    """

    stubs_path: Path
    pipeline: ConversionPipeline

    @classmethod
    def create(cls, *, stubs_path: Path) -> Self:
        """Create a converter using the standard full-API pipeline.

        Args:
            stubs_path: Filesystem path identifying the stubs.

        Returns:
            Self produced by this operation.

        """
        pipeline: ConversionPipeline = ConversionPipeline.create()
        return cls(stubs_path=stubs_path, pipeline=pipeline)

    def convert_source(
        self,
        *,
        source: str,
        filename: str = "<source>",
    ) -> str:
        """Convert untyped source text into annotated source text.

        Args:
            filename: Filename supplied as str for this operation.
            source: The source examined while convert untyped source text into
                annotated source text.

        Returns:
            Rendered source text produced by this operation.

        """
        result: ConversionResult = self.convert_text(
            source=source,
            filename=filename,
        )
        return result.output_source

    def convert_text(
        self,
        *,
        source: str,
        filename: str = "<source>",
    ) -> ConversionResult:
        """Convert source text and return the complete API result.

        Args:
            filename: Filename supplied as str for this operation.
            source: The source examined while convert source text and return
                the complete API result.

        Returns:
            ConversionResult produced by this operation.

        """
        options: ConversionOptions = ConversionOptions(
            source_path=None,
            stubs_path=self.stubs_path,
            filename=filename,
        )
        context: ConversionContext = ConversionContext.create(
            source=source,
            options=options,
        )
        final_context: ConversionContext = self.pipeline.run(context=context)
        return _result_from_context(
            context=final_context,
            stage_names=self.pipeline.stage_names(),
        )

    def convert_file(self, *, source_path: Path) -> ConversionResult:
        """Convert one file using the full graph API pipeline.

        Args:
            source_path: Filesystem path identifying the source.

        Returns:
            ConversionResult produced by this operation.

        """
        source: str = source_path.read_text(encoding="utf-8")
        options: ConversionOptions = ConversionOptions(
            source_path=source_path,
            stubs_path=self.stubs_path,
            filename=str(object=source_path),
        )
        context: ConversionContext = ConversionContext.create(
            source=source,
            options=options,
        )
        final_context: ConversionContext = self.pipeline.run(context=context)
        return _result_from_context(
            context=final_context,
            stage_names=self.pipeline.stage_names(),
        )


def _result_from_context(
    *,
    context: ConversionContext,
    stage_names: tuple[str, ...],
) -> ConversionResult:
    """Build a public conversion result from a final context.

    Args:
        context: Context supplied as ConversionContext for this operation.
        stage_names: Stage names supplied as tuple[str, ...] for this
            operation.

    Returns:
        ConversionResult produced by this operation.

    """
    module: Module = context.require_backend_module()
    output_source: str = (
        custom_unparse(node=module)
        + """\

"""
    )
    return ConversionResult(
        source_path=context.options.source_path,
        output_source=output_source,
        inference=context.require_inference(),
        explanation=context.require_explanation(),
        validation_messages=context.validation_messages,
        stage_names=stage_names,
    )
