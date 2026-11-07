"""Human-readable inference explanation reports."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING, Self

from astart._graph.graph.type_expressions import TypeExpressionCodec

if TYPE_CHECKING:
    from astart._graph.graph.document import AstDocument, AstGraphNode
    from astart._graph.graph.positions import SourceSpan
    from astart._graph.graph.usage import UsageGraph
    from astart._graph.inference.reasons import Reason
    from astart._graph.inference.resolver import (
        AnnotationPlan,
        InferenceResult,
    )
type JsonScalar = str | int | float | bool | None
type JsonObject = dict[str, JsonValue]
type JsonArray = list[JsonValue]
type JsonValue = JsonScalar | JsonObject | JsonArray


@dataclass(frozen=True, slots=True)
class SpanExplanation:
    """Serializable source span attached to an explanation.

    Attributes:
        end_column: End column retained as int by this instance.
        end_line: End line retained as int by this instance.
        start_column: Start column retained as int by this instance.
        start_line: Start line retained as int by this instance.

    """

    start_line: int
    start_column: int
    end_line: int
    end_column: int

    @classmethod
    def from_span(cls, *, span: SourceSpan) -> Self:
        """Create an explanation span from a source span.

        Args:
            span: Span supplied as SourceSpan for this operation.

        Returns:
            Self produced by this operation.

        """
        return cls(
            start_line=span.start.line,
            start_column=span.start.column,
            end_line=span.end.line,
            end_column=span.end.column,
        )

    def to_json_data(self) -> JsonObject:
        """Return JSON-compatible span data.

        Returns:
            JsonObject produced by this operation.

        """
        return {
            "start_line": self.start_line,
            "start_column": self.start_column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }

    def to_compact_source(self) -> str:
        """Return a compact source-location string.

        Returns:
            Rendered source text produced by this operation.

        """
        return (
            f"L{self.start_line}:{self.start_column}"
            f"-L{self.end_line}:{self.end_column}"
        )


@dataclass(frozen=True, slots=True)
class EvidenceExplanation:
    """A human-readable reason supporting one annotation.

    Attributes:
        confidence: Confidence assigned to this inference or observation.
        kind: Kind retained as str by this instance.
        message: Explanation associated with this result.
        node_id: Node id retained as int | None by this instance.
        span: Span retained as SpanExplanation | None by this instance.

    """

    kind: str
    confidence: float
    message: str
    node_id: int | None
    span: SpanExplanation | None = None

    @classmethod
    def from_reason(
        cls,
        *,
        reason: Reason,
        document: AstDocument,
    ) -> Self:
        """Create an evidence explanation from a low-level reason.

        Args:
            document: Document supplied as AstDocument for this operation.
            reason: Reason supplied as Reason for this operation.

        Returns:
            Self produced by this operation.

        """
        span: SpanExplanation | None = _span_for_node_id(
            document=document,
            node_id=reason.node_id,
        )
        return cls(
            kind=reason.kind.value,
            confidence=reason.confidence.value,
            message=reason.message,
            node_id=reason.node_id,
            span=span,
        )

    def to_json_data(self) -> JsonObject:
        """Return JSON-compatible evidence data.

        Returns:
            JsonObject produced by this operation.

        """
        data: JsonObject = {
            "kind": self.kind,
            "confidence": self.confidence,
            "message": self.message,
            "node_id": self.node_id,
        }
        if self.span is not None:
            data["span"] = self.span.to_json_data()
        return data

    def to_markdown(self) -> str:
        """Render this evidence item as one markdown bullet.

        Returns:
            Rendered source text produced by this operation.

        """
        span_text: str = (
            f" at {self.span.to_compact_source()}"
            if self.span is not None
            else ""
        )
        return (
            f"  - `{self.kind}` confidence={self.confidence:.2f}"
            f"{span_text}: {self.message}"
        )


@dataclass(frozen=True, slots=True)
class AnnotationExplanation:
    """Explanation for one accepted annotation plan.

    Attributes:
        confidence: Confidence assigned to this inference or observation.
        evidence: Evidence retained as tuple[EvidenceExplanation, ...] by this
            instance.
        graph_context: Graph context retained as tuple[str, ...] by this
            instance.
        name: Identifier used to refer to the name.
        node_id: Node id retained as int by this instance.
        scope_id: Scope id retained as int by this instance.
        span: Span retained as SpanExplanation | None by this instance.
        type_source: Type source retained as str by this instance.

    """

    name: str
    type_source: str
    confidence: float
    scope_id: int
    node_id: int
    span: SpanExplanation | None
    evidence: tuple[EvidenceExplanation, ...]
    graph_context: tuple[str, ...] = ()

    @classmethod
    def from_plan(
        cls,
        *,
        plan: AnnotationPlan,
        document: AstDocument,
        usage_graph: UsageGraph,
    ) -> Self:
        """Build an explanation for one annotation plan.

        Args:
            document: Document supplied as AstDocument for this operation.
            plan: Plan supplied as AnnotationPlan for this operation.
            usage_graph: Usage graph supplied as UsageGraph for this operation.

        Returns:
            Self produced by this operation.

        """
        span: SpanExplanation | None = _span_for_node_id(
            document=document,
            node_id=plan.node_id,
        )
        evidence: tuple[EvidenceExplanation, ...] = tuple(
            EvidenceExplanation.from_reason(
                reason=reason,
                document=document,
            )
            for reason in plan.reasons
        )
        graph_context: tuple[str, ...] = _graph_context_for_plan(
            plan=plan,
            usage_graph=usage_graph,
        )
        return cls(
            name=plan.name,
            type_source=TypeExpressionCodec.to_source(
                type_expression=plan.type_expression,
            ),
            confidence=plan.confidence.value,
            scope_id=plan.scope_id,
            node_id=plan.node_id,
            span=span,
            evidence=evidence,
            graph_context=graph_context,
        )

    def to_json_data(self) -> JsonObject:
        """Return JSON-compatible annotation explanation data.

        Returns:
            JsonObject produced by this operation.

        """
        graph_context: JsonArray = []
        graph_context.extend(self.graph_context)
        data: JsonObject = {
            "name": self.name,
            "type_source": self.type_source,
            "confidence": self.confidence,
            "scope_id": self.scope_id,
            "node_id": self.node_id,
            "evidence": [item.to_json_data() for item in self.evidence],
            "graph_context": graph_context,
        }
        if self.span is not None:
            data["span"] = self.span.to_json_data()
        return data

    def to_markdown(self) -> str:
        """Render this annotation explanation as markdown.

        Returns:
            Rendered source text produced by this operation.

        """
        span_text: str = (
            f" `{self.span.to_compact_source()}`"
            if self.span is not None
            else ""
        )
        lines: list[str] = [
            (
                f"""\
### `{self.name}: {self.type_source}`{span_text}
confidence: `{self.confidence:.2f}`"""
            ),
        ]
        if self.graph_context:
            lines.append("graph context:")
            lines.extend(f"  - {item}" for item in self.graph_context)
        if self.evidence:
            lines.append("evidence:")
            lines.extend(item.to_markdown() for item in self.evidence)
        return """\

""".join(lines)


@dataclass(frozen=True, slots=True)
class ExplanationSummary:
    """Aggregate counts for a report.

    Attributes:
        annotation_count: Annotation count retained as int by this instance.
        average_confidence: Average confidence retained as float by this
            instance.
        evidence_count: Evidence count retained as int by this instance.
        stage_count: Stage count retained as int by this instance.
        warning_count: Warning count retained as int by this instance.

    """

    annotation_count: int
    evidence_count: int
    average_confidence: float
    warning_count: int
    stage_count: int

    def to_json_data(self) -> JsonObject:
        """Return JSON-compatible summary data.

        Returns:
            JsonObject produced by this operation.

        """
        return {
            "annotation_count": self.annotation_count,
            "evidence_count": self.evidence_count,
            "average_confidence": self.average_confidence,
            "warning_count": self.warning_count,
            "stage_count": self.stage_count,
        }


@dataclass(frozen=True, slots=True)
class InferenceExplanationReport:
    """Human-readable report explaining inference output.

    Attributes:
        annotations: Annotations retained as tuple[AnnotationExplanation, ...]
            by this instance.
        stage_names: Stage names retained as tuple[str, ...] by this instance.
        summary: Summary retained as ExplanationSummary by this instance.
        validation_messages: Validation messages retained as tuple[str, ...] by
            this instance.
        warnings: Warnings retained as tuple[str, ...] by this instance.

    """

    summary: ExplanationSummary
    annotations: tuple[AnnotationExplanation, ...]
    warnings: tuple[str, ...] = ()
    stage_names: tuple[str, ...] = ()
    validation_messages: tuple[str, ...] = ()

    def to_json_data(self) -> JsonObject:
        """Return JSON-compatible report data.

        Returns:
            JsonObject produced by this operation.

        """
        stage_names: JsonArray = []
        stage_names.extend(self.stage_names)
        validation_messages: JsonArray = []
        validation_messages.extend(self.validation_messages)
        warnings: JsonArray = []
        warnings.extend(self.warnings)
        return {
            "summary": self.summary.to_json_data(),
            "stage_names": stage_names,
            "validation_messages": validation_messages,
            "warnings": warnings,
            "annotations": [
                annotation.to_json_data() for annotation in self.annotations
            ],
        }

    def to_markdown(self) -> str:
        """Render the explanation report as markdown.

        Returns:
            Rendered source text produced by this operation.

        """
        lines: list[str] = [
            "# Inference explanation report",
            "",
            "## Summary",
            "",
            f"- annotations explained: {self.summary.annotation_count}",
            f"- evidence items: {self.summary.evidence_count}",
            (f"- average confidence: {self.summary.average_confidence:.3f}"),
            f"- warnings: {self.summary.warning_count}",
            f"- pipeline stages: {self.summary.stage_count}",
        ]
        if self.stage_names:
            lines.extend(["", "## Pipeline stages", ""])
            lines.extend(f"1. `{name}`" for name in self.stage_names)
        if self.validation_messages:
            lines.extend(["", "## Validation messages", ""])
            lines.extend(
                f"- {message}" for message in self.validation_messages
            )
        if self.warnings:
            lines.extend(["", "## Warnings", ""])
            lines.extend(f"- {warning}" for warning in self.warnings)
        lines.extend(["", "## Annotation explanations", ""])
        lines.extend(
            annotation.to_markdown() for annotation in self.annotations
        )
        return (
            """\


""".join(lines).rstrip()
            + """\

"""
        )


@dataclass(frozen=True, slots=True)
class InferenceExplanationBuilder:
    """Build explainability reports from pipeline graph artifacts."""

    @staticmethod
    def build(
        *,
        document: AstDocument,
        usage_graph: UsageGraph,
        inference: InferenceResult,
        stage_names: tuple[str, ...] = (),
        validation_messages: tuple[str, ...] = (),
    ) -> InferenceExplanationReport:
        """Build a complete explanation report.

        Args:
            document: Document supplied as AstDocument for this operation.
            inference: Inference supplied as InferenceResult for this
                operation.
            stage_names: Stage names supplied as tuple[str, ...] for this
                operation.
            usage_graph: Usage graph supplied as UsageGraph for this operation.
            validation_messages: Validation messages supplied as tuple[str,
                ...] for this operation.

        Returns:
            InferenceExplanationReport produced by this operation.

        """
        annotations: tuple[AnnotationExplanation, ...] = tuple(
            AnnotationExplanation.from_plan(
                plan=plan,
                document=document,
                usage_graph=usage_graph,
            )
            for plan in inference.annotation_plans
        )
        evidence_count: int = sum(
            len(annotation.evidence) for annotation in annotations
        )
        confidence_values: tuple[float, ...] = tuple(
            annotation.confidence for annotation in annotations
        )
        average_confidence: float = (
            mean(data=confidence_values) if confidence_values else 0.0
        )
        summary: ExplanationSummary = ExplanationSummary(
            annotation_count=len(annotations),
            evidence_count=evidence_count,
            average_confidence=average_confidence,
            warning_count=len(inference.warnings),
            stage_count=len(stage_names),
        )
        return InferenceExplanationReport(
            summary=summary,
            annotations=annotations,
            warnings=inference.warnings,
            stage_names=stage_names,
            validation_messages=validation_messages,
        )


def _span_for_node_id(
    *,
    document: AstDocument,
    node_id: int | None,
) -> SpanExplanation | None:
    """Return explanation span for a document node id.

    Args:
        document: Document supplied as AstDocument for this operation.
        node_id: Node id supplied as int | None for this operation.

    Returns:
        SpanExplanation | None produced by this operation.

    """
    if node_id is None:
        return None
    graph_node: AstGraphNode | None = document.node_by_id(node_id=node_id)
    if graph_node is None or graph_node.span is None:
        return None
    return SpanExplanation.from_span(span=graph_node.span)


def _graph_context_for_plan(
    *,
    plan: AnnotationPlan,
    usage_graph: UsageGraph,
) -> tuple[str, ...]:
    """Return concise graph context for one plan.

    Args:
        plan: Plan supplied as AnnotationPlan for this operation.
        usage_graph: Usage graph supplied as UsageGraph for this operation.

    Returns:
        tuple[str, ...] produced by this operation.

    """
    context: list[str] = []
    symbol_count: int = len(usage_graph.symbols_named(name=plan.name))
    if symbol_count:
        context.append(f"symbols named {plan.name!r}: {symbol_count}")
    event_count: int = len(usage_graph.events_for_node(node_id=plan.node_id))
    if event_count:
        context.append(f"events on annotated node: {event_count}")
    incoming_count: int = len(usage_graph.incoming_edges(node_id=plan.node_id))
    outgoing_count: int = len(usage_graph.outgoing_edges(node_id=plan.node_id))
    if incoming_count or outgoing_count:
        context.append(
            "graph edges: "
            f"incoming={incoming_count}, outgoing={outgoing_count}",
        )
    return tuple(context)
