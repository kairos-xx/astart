"""Pipeline context objects for graph-only conversion."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ast import Module
    from pathlib import Path

    from astart.graph.graph.document import AstDocument
    from astart.graph.graph.usage import UsageGraph
    from astart.graph.inference.explanations import (
        InferenceExplanationReport,
    )
    from astart.graph.inference.resolver import InferenceResult
    from astart.graph.stubs.index import LazyStubIndex


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    """Options controlling one conversion run.

    Attributes:
        filename (str): Filename retained as str by this instance.
        output_path (Path | None): Path to the output used by this instance.
        source_path (Path | None): Path to the source used by this instance.
        stubs_path (Path): Path to the stubs used by this instance.
        validate_output (bool): Validate output retained as bool by this
            instance.

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
        backend_module (Module | None): Backend module retained as Module |
            None by this instance.
        backend_source (str | None): Backend source retained as str | None by
            this instance.
        completed_stage_names (tuple[str, ...]): Completed stage names retained
            as tuple[str,
            ...] by this instance.
        explanation (InferenceExplanationReport | None): Explanation retained
            as InferenceExplanationReport
            | None by this instance.
        inference (InferenceResult | None): Inference retained as
            InferenceResult | None by this instance.
        input_document (AstDocument | None): Input document retained as
            AstDocument | None by this instance.
        input_usage_graph (UsageGraph | None): Input usage graph retained as
            UsageGraph | None by this instance.
        options (ConversionOptions): Options retained as ConversionOptions by
            this instance.
        output_document (AstDocument | None): Output document retained as
            AstDocument | None by this instance.
        output_usage_graph (UsageGraph | None): Output usage graph retained as
            UsageGraph | None by this instance.
        source (str): Original source text retained for parsing and
            reconstruction.
        stub_index (LazyStubIndex | None): Stub index retained as LazyStubIndex
            | None by this instance.
        validation_messages (tuple[str, ...]): Validation messages retained as
            tuple[str, ...] by this instance.

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
            options (ConversionOptions): Options supplied as ConversionOptions
                for this operation.
            source (str): The source examined while create the
                initial context for a conversion run.

        Returns:
            Self: Self produced by this operation.

        """
        return cls(source=source, options=options)

    def with_input_document(self, *, document: AstDocument) -> Self:
        """Return a copy with the input document graph attached.

        Args:
            document (AstDocument): Document supplied as AstDocument for this
                operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, input_document=document)

    def with_input_usage_graph(self, *, usage_graph: UsageGraph) -> Self:
        """Return a copy with the input usage graph attached.

        Args:
            usage_graph (UsageGraph): Usage graph supplied as UsageGraph for
                this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, input_usage_graph=usage_graph)

    def with_stub_index(self, *, stub_index: LazyStubIndex) -> Self:
        """Return a copy with the lazy stub index attached.

        Args:
            stub_index (LazyStubIndex): Stub index supplied as LazyStubIndex
                for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, stub_index=stub_index)

    def with_backend_module(self, *, module: Module) -> Self:
        """Return a copy with the converted AST module attached.

        Args:
            module (Module): The module examined while return a copy
                with the converted AST module attached.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, backend_module=module)

    def with_backend_source(self, *, source: str) -> Self:
        """Return a copy with converted source from the inference backend.

        Args:
            source (str): The source examined while return a copy with
                converted source from the inference backend.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, backend_source=source)

    def with_output_document(self, *, document: AstDocument) -> Self:
        """Return a copy with the output document graph attached.

        Args:
            document (AstDocument): Document supplied as AstDocument for this
                operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, output_document=document)

    def with_output_usage_graph(self, *, usage_graph: UsageGraph) -> Self:
        """Return a copy with the output usage graph attached.

        Args:
            usage_graph (UsageGraph): Usage graph supplied as UsageGraph for
                this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, output_usage_graph=usage_graph)

    def with_inference(self, *, inference: InferenceResult) -> Self:
        """Return a copy with the structured inference report attached.

        Args:
            inference (InferenceResult): Inference supplied as InferenceResult
                for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, inference=inference)

    def with_explanation(
        self,
        *,
        explanation: InferenceExplanationReport,
    ) -> Self:
        """Return a copy with the explanation report attached.

        Args:
            explanation (InferenceExplanationReport): Explanation supplied as
                InferenceExplanationReport for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(self, explanation=explanation)

    def with_validation_message(self, *, message: str) -> Self:
        """Return a copy with one extra validation message.

        Args:
            message (str): Message supplied as str for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(
            self,
            validation_messages=(*self.validation_messages, message),
        )

    def with_completed_stage(self, *, name: str) -> Self:
        """Return a copy with one extra completed stage name.

        Args:
            name (str): Identifier of the name being resolved.

        Returns:
            Self: Self produced by this operation.

        """
        return replace(
            self,
            completed_stage_names=(*self.completed_stage_names, name),
        )

    def require_backend_module(self) -> Module:
        """Return the converted AST module or raise a stage-order error.

        Returns:
            Module: Module produced by this operation.

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
            str: Rendered source text produced by this operation.

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
            AstDocument: AstDocument produced by this operation.

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
            LazyStubIndex: LazyStubIndex produced by this operation.

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
            AstDocument: AstDocument produced by this operation.

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
            UsageGraph: UsageGraph produced by this operation.

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
            InferenceResult: InferenceResult produced by this operation.

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
            InferenceExplanationReport:
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
