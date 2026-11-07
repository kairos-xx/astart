"""Pipeline context objects for graph-only conversion."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ast import Module
    from pathlib import Path

    from astart._graph.graph.document import AstDocument
    from astart._graph.graph.usage import UsageGraph
    from astart._graph.inference.explanations import (
        InferenceExplanationReport,
    )
    from astart._graph.inference.resolver import InferenceResult
    from astart._graph.stubs.index import LazyStubIndex


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    """Options controlling one conversion run.

    Attributes:
        filename: Filename retained as str by this instance.
        output_path: Path to the output used by this instance.
        source_path: Path to the source used by this instance.
        stubs_path: Path to the stubs used by this instance.
        validate_output: Validate output retained as bool by this instance.

    """

    source_path: Path | None
    stubs_path: Path
    filename: str
    output_path: Path | None = None
    validate_output: bool = True


@dataclass(frozen=True, slots=True)
class ConversionContext:
    """Immutable state passed between conversion pipeline stages.

    Attributes:
        backend_module: Backend module retained as Module | None by this
            instance.
        backend_source: Backend source retained as str | None by this instance.
        completed_stage_names: Completed stage names retained as tuple[str,
            ...] by this instance.
        explanation: Explanation retained as InferenceExplanationReport | None
            by this instance.
        inference: Inference retained as InferenceResult | None by this
            instance.
        input_document: Input document retained as AstDocument | None by this
            instance.
        input_usage_graph: Input usage graph retained as UsageGraph | None by
            this instance.
        options: Options retained as ConversionOptions by this instance.
        output_document: Output document retained as AstDocument | None by this
            instance.
        output_usage_graph: Output usage graph retained as UsageGraph | None by
            this instance.
        source: Original source text retained for parsing and reconstruction.
        stub_index: Stub index retained as LazyStubIndex | None by this
            instance.
        validation_messages: Validation messages retained as tuple[str, ...] by
            this instance.

    """

    options: ConversionOptions
    source: str
    input_document: AstDocument | None = None
    input_usage_graph: UsageGraph | None = None
    stub_index: LazyStubIndex | None = None
    backend_source: str | None = None
    backend_module: Module | None = None
    output_document: AstDocument | None = None
    output_usage_graph: UsageGraph | None = None
    inference: InferenceResult | None = None
    explanation: InferenceExplanationReport | None = None
    validation_messages: tuple[str, ...] = ()
    completed_stage_names: tuple[str, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        source: str,
        options: ConversionOptions,
    ) -> Self:
        """Create the initial context for a conversion run.

        Args:
            options: Options supplied as ConversionOptions for this operation.
            source: The source examined while create the initial context for a
                conversion run.

        Returns:
            Self produced by this operation.

        """
        return cls(source=source, options=options)

    def with_input_document(self, *, document: AstDocument) -> Self:
        """Return a copy with the input document graph attached.

        Args:
            document: Document supplied as AstDocument for this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, input_document=document)

    def with_input_usage_graph(self, *, usage_graph: UsageGraph) -> Self:
        """Return a copy with the input usage graph attached.

        Args:
            usage_graph: Usage graph supplied as UsageGraph for this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, input_usage_graph=usage_graph)

    def with_stub_index(self, *, stub_index: LazyStubIndex) -> Self:
        """Return a copy with the lazy stub index attached.

        Args:
            stub_index: Stub index supplied as LazyStubIndex for this
                operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, stub_index=stub_index)

    def with_backend_module(self, *, module: Module) -> Self:
        """Return a copy with the converted AST module attached.

        Args:
            module: The module examined while return a copy with the converted
                AST module attached.

        Returns:
            Self produced by this operation.

        """
        return replace(self, backend_module=module)

    def with_backend_source(self, *, source: str) -> Self:
        """Return a copy with converted source from the inference backend.

        Args:
            source: The source examined while return a copy with converted
                source from the inference backend.

        Returns:
            Self produced by this operation.

        """
        return replace(self, backend_source=source)

    def with_output_document(self, *, document: AstDocument) -> Self:
        """Return a copy with the output document graph attached.

        Args:
            document: Document supplied as AstDocument for this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, output_document=document)

    def with_output_usage_graph(self, *, usage_graph: UsageGraph) -> Self:
        """Return a copy with the output usage graph attached.

        Args:
            usage_graph: Usage graph supplied as UsageGraph for this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, output_usage_graph=usage_graph)

    def with_inference(self, *, inference: InferenceResult) -> Self:
        """Return a copy with the structured inference report attached.

        Args:
            inference: Inference supplied as InferenceResult for this
                operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, inference=inference)

    def with_explanation(
        self,
        *,
        explanation: InferenceExplanationReport,
    ) -> Self:
        """Return a copy with the explanation report attached.

        Args:
            explanation: Explanation supplied as InferenceExplanationReport for
                this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(self, explanation=explanation)

    def with_validation_message(self, *, message: str) -> Self:
        """Return a copy with one extra validation message.

        Args:
            message: Message supplied as str for this operation.

        Returns:
            Self produced by this operation.

        """
        return replace(
            self,
            validation_messages=(*self.validation_messages, message),
        )

    def with_completed_stage(self, *, name: str) -> Self:
        """Return a copy with one extra completed stage name.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Self produced by this operation.

        """
        return replace(
            self,
            completed_stage_names=(*self.completed_stage_names, name),
        )

    def require_backend_module(self) -> Module:
        """Return the converted AST module or raise a stage-order error.

        Returns:
            Module produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.backend_module is None:
            raise ConversionPipelineError
        return self.backend_module

    def require_backend_source(self) -> str:
        """Return converted source or raise a stage-order error.

        Returns:
            Rendered source text produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.backend_source is None:
            raise ConversionPipelineError
        return self.backend_source

    def require_input_document(self) -> AstDocument:
        """Return the input document graph or raise a stage-order error.

        Returns:
            AstDocument produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.input_document is None:
            raise ConversionPipelineError
        return self.input_document

    def require_stub_index(self) -> LazyStubIndex:
        """Return the stub index or raise a stage-order error.

        Returns:
            LazyStubIndex produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.stub_index is None:
            raise ConversionPipelineError
        return self.stub_index

    def require_output_document(self) -> AstDocument:
        """Return the output document graph or raise a stage-order error.

        Returns:
            AstDocument produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.output_document is None:
            raise ConversionPipelineError
        return self.output_document

    def require_output_usage_graph(self) -> UsageGraph:
        """Return the output usage graph or raise a stage-order error.

        Returns:
            UsageGraph produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.output_usage_graph is None:
            raise ConversionPipelineError
        return self.output_usage_graph

    def require_inference(self) -> InferenceResult:
        """Return the inference result or raise a stage-order error.

        Returns:
            InferenceResult produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.inference is None:
            raise ConversionPipelineError
        return self.inference

    def require_explanation(self) -> InferenceExplanationReport:
        """Return the explanation report or raise a stage-order error.

        Returns:
            InferenceExplanationReport produced by this operation.

        Raises:
            ConversionPipelineError: If this operation cannot satisfy its
                documented contract.

        """
        if self.explanation is None:
            raise ConversionPipelineError
        return self.explanation


class ConversionPipelineError(RuntimeError):
    """Raised when conversion stages are run in an invalid order."""
