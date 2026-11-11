"""Resolver API for reasoned type inference."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    FunctionDef,
    Name,
    arg,
    expr,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Self, final

from astart.graph.graph.semantics import nodes_of_type
from astart.graph.graph.type_expressions import (
    TypeExpression,
    TypeExpressionCodec,
    TypeExpressionError,
    TypeName,
)
from astart.graph.inference.reasons import (
    Confidence,
    EvidenceKind,
    Reason,
    TypeHypothesis,
)

if TYPE_CHECKING:
    from astart.graph.graph.document import AstDocument
    from astart.graph.graph.usage import UsageGraph
    from astart.graph.stubs.index import LazyStubIndex


@final
class Constants:
    """Group module-level constants.

    Attributes:
        object_names (Final[frozenset[str]]): Grouped module constant.

    """

    object_names: Final[frozenset[str]] = frozenset({"object", "Any"})


@dataclass(frozen=True, slots=True)
class AnnotationPlan:
    """A planned annotation insertion for one graph symbol.

    Attributes:
        confidence (Confidence): Confidence assigned to this inference or
            observation.
        name (str): Identifier used to refer to the name.
        node_id (int): Node id retained as int by this instance.
        reasons (tuple[Reason, ...]): Reasons retained as tuple[Reason, ...] by
            this instance.
        scope_id (int): Scope id retained as int by this instance.
        type_expression (TypeExpression): Type expression retained as
            TypeExpression by this instance.

    """

    name: str
    scope_id: int
    node_id: int
    type_expression: TypeExpression
    confidence: Confidence
    reasons: tuple[Reason, ...] = ()

    def type_source(self) -> str:
        """Render the planned annotation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return TypeExpressionCodec.to_source(
            type_expression=self.type_expression,
        )


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Result returned by the inference resolver.

    Attributes:
        annotation_plans (tuple[AnnotationPlan, ...]): Annotation plans
            retained as tuple[AnnotationPlan,
            ...] by this instance.
        hypotheses (tuple[TypeHypothesis, ...]): Hypotheses retained as
            tuple[TypeHypothesis, ...] by this instance.
        warnings (tuple[str, ...]): Warnings retained as tuple[str, ...] by
            this instance.

    """

    hypotheses: tuple[TypeHypothesis, ...]
    annotation_plans: tuple[AnnotationPlan, ...]
    warnings: tuple[str, ...] = ()

    def annotation_count(self) -> int:
        """Return the number of planned annotations.

        Returns:
            int: int produced by this operation.

        """
        return len(self.annotation_plans)

    def hypothesis_sources(self) -> tuple[str, ...]:
        """Return rendered hypothesis type sources.

        Returns:
            tuple[str, ...]: tuple[str, ...] produced by this operation.

        """
        return tuple(hypothesis.to_source() for hypothesis in self.hypotheses)


def _default_threshold() -> Confidence:
    """Return the default annotation confidence threshold.

    Returns:
        Confidence: Confidence produced by this operation.

    """
    return Confidence(value=0.8)


@dataclass(frozen=True, slots=True)
class InferenceResolverConfig:
    """Configuration for inference resolution.

    Attributes:
        annotation_threshold (Confidence): Annotation threshold retained as
            Confidence by this instance.
        max_iterations (int): Max iterations retained as int by this instance.

    """

    annotation_threshold: Confidence = field(
        default_factory=_default_threshold,
    )
    max_iterations: int = 30


@dataclass(frozen=True, slots=True)
class _RecordRequest:
    """Inputs needed to record one annotation hypothesis and plan.

    Attributes:
        annotation (TypeExpression): Annotation retained as TypeExpression by
            this instance.
        evidence (EvidenceKind): Evidence retained as EvidenceKind by this
            instance.
        name (str): Identifier used to refer to the name.
        node_id (int): Node id retained as int by this instance.
        scope_id (int): Scope id retained as int by this instance.

    """

    name: str
    scope_id: int
    node_id: int
    annotation: TypeExpression
    evidence: EvidenceKind


@dataclass(slots=True)
class _ResolutionSink:
    """Mutable collections shared during one resolution pass.

    Attributes:
        baseline (frozenset[str]): Baseline retained as frozenset[str] by this
            instance.
        hypotheses (list[TypeHypothesis]): Hypotheses retained as
            list[TypeHypothesis] by this instance.
        plans (list[AnnotationPlan]): Plans retained as list[AnnotationPlan] by
            this instance.
        warnings (list[str]): Warnings retained as list[str] by this instance.

    """

    baseline: frozenset[str]
    hypotheses: list[TypeHypothesis] = field(default_factory=list)
    plans: list[AnnotationPlan] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _annotation_site_keys(*, document: AstDocument) -> frozenset[str]:
    """Return stable structural keys for annotated sites in a document.

    Keys are independent of node identity so a baseline document parsed
    separately from the converted document can still be compared.

    Args:
        document (AstDocument): Document supplied as AstDocument for this
            operation.

    Returns:
        frozenset[str]: frozenset[str] produced by this operation.

    """
    keys: set[str] = set()
    for node in nodes_of_type(
        root=document.tree,
        types=(FunctionDef, AsyncFunctionDef, AnnAssign),
    ):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            parameters: tuple[arg, ...] = _function_parameters(node=node)
            parameter: arg
            for parameter in parameters:
                if parameter.annotation is not None:
                    keys.add(f"param:{node.name}:{parameter.arg}")
            if node.returns is not None:
                keys.add(f"return:{node.name}")
        else:
            keys.add(f"var:{_annassign_name(node=node)}")
    return frozenset(keys)


@dataclass(slots=True)
class InferenceResolver:
    """Reasoned, graph-based inference resolver API shell.

    Attributes:
        config (InferenceResolverConfig): Config retained as
            InferenceResolverConfig by this instance.
        document (AstDocument): Document retained as AstDocument by this
            instance.
        stub_index (LazyStubIndex): Stub index retained as LazyStubIndex by
            this instance.
        usage_graph (UsageGraph): Usage graph retained as UsageGraph by this
            instance.

    """

    document: AstDocument
    usage_graph: UsageGraph
    stub_index: LazyStubIndex
    config: InferenceResolverConfig = field(
        default_factory=InferenceResolverConfig,
    )

    @classmethod
    def create(
        cls,
        *,
        document: AstDocument,
        usage_graph: UsageGraph,
        stub_index: LazyStubIndex,
        config: InferenceResolverConfig | None = None,
    ) -> Self:
        """Create a resolver with explicit graph dependencies.

        Args:
            config (InferenceResolverConfig | None): Config supplied as
                InferenceResolverConfig
                | None for this operation.
            document (AstDocument): Document supplied as AstDocument for this
                operation.
            stub_index (LazyStubIndex): Stub index supplied as LazyStubIndex
                for this operation.
            usage_graph (UsageGraph): Usage graph supplied as UsageGraph for
                this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return cls(
            document=document,
            usage_graph=usage_graph,
            stub_index=stub_index,
            config=config or InferenceResolverConfig(),
        )

    def resolve(
        self,
        *,
        baseline_document: AstDocument | None = None,
    ) -> InferenceResult:
        """Resolve hypotheses from the converted document graph.

        Every non-trivial annotation present in :attr:`document` becomes a
        :class:`TypeHypothesis` with a reason and confidence. When a baseline
        document is supplied, only sites absent from that baseline are
        reported.

        Args:
            baseline_document: Baseline document supplied as AstDocument | None
                for this operation.

        Returns:
            InferenceResult produced by this operation.

        """
        baseline: frozenset[str] = (
            _annotation_site_keys(document=baseline_document)
            if baseline_document is not None
            else frozenset()
        )
        sink: _ResolutionSink = _ResolutionSink(baseline=baseline)
        scope_id: int = id(self.document.tree)
        for node in nodes_of_type(
            root=self.document.tree,
            types=(FunctionDef, AsyncFunctionDef, AnnAssign),
        ):
            self._collect_from_node(node=node, scope_id=scope_id, sink=sink)
        return InferenceResult(
            hypotheses=tuple(sink.hypotheses),
            annotation_plans=tuple(sink.plans),
            warnings=tuple(sink.warnings),
        )

    def _collect_from_node(
        self,
        *,
        node: AST,
        scope_id: int,
        sink: _ResolutionSink,
    ) -> None:
        """Collect hypotheses and plans for one AST node.

        Args:
            node (AST): The node examined while collect
                hypotheses and plans for one AST node.
            scope_id (int): Scope id supplied as int for this operation.
            sink (_ResolutionSink): Sink supplied as _ResolutionSink for this
                operation.

        """
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            self._collect_from_function(
                node=node,
                scope_id=scope_id,
                sink=sink,
            )
        elif isinstance(node, AnnAssign):
            target_name: str = _annassign_name(node=node)
            site_key: str = f"var:{target_name}"
            if site_key in sink.baseline:
                return
            annotation: TypeExpression | None = _parse_annotation(
                annotation=node.annotation,
                warnings=sink.warnings,
            )
            if annotation is None:
                return
            self._record(
                request=_RecordRequest(
                    name=target_name,
                    scope_id=scope_id,
                    node_id=id(node),
                    annotation=annotation,
                    evidence=EvidenceKind.ANNOTATION,
                ),
                hypotheses=sink.hypotheses,
                plans=sink.plans,
            )

    def _collect_from_function(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        scope_id: int,
        sink: _ResolutionSink,
    ) -> None:
        """Collect hypotheses for a function's parameters and return.

        Args:
            node (FunctionDef | AsyncFunctionDef): The node examined while
                collect hypotheses
                for a function's parameters and return.
            scope_id (int): Scope id supplied as int for this operation.
            sink (_ResolutionSink): Sink supplied as _ResolutionSink for this
                operation.

        """
        parameter: arg
        for parameter in _function_parameters(node=node):
            if parameter.annotation is None:
                continue
            if f"param:{node.name}:{parameter.arg}" in sink.baseline:
                continue
            annotation: TypeExpression | None = _parse_annotation(
                annotation=parameter.annotation,
                warnings=sink.warnings,
            )
            if annotation is None:
                continue
            self._record(
                request=_RecordRequest(
                    name=parameter.arg,
                    scope_id=id(node),
                    node_id=id(parameter),
                    annotation=annotation,
                    evidence=EvidenceKind.CALL,
                ),
                hypotheses=sink.hypotheses,
                plans=sink.plans,
            )
        if node.returns is None or f"return:{node.name}" in sink.baseline:
            return
        annotation = _parse_annotation(
            annotation=node.returns,
            warnings=sink.warnings,
        )
        if annotation is None:
            return
        self._record(
            request=_RecordRequest(
                name=node.name,
                scope_id=scope_id,
                node_id=id(node),
                annotation=annotation,
                evidence=EvidenceKind.RETURN,
            ),
            hypotheses=sink.hypotheses,
            plans=sink.plans,
        )

    def _record(
        self,
        *,
        request: _RecordRequest,
        hypotheses: list[TypeHypothesis],
        plans: list[AnnotationPlan],
    ) -> None:
        """Record one annotation as a hypothesis and plan when meaningful.

        Args:
            hypotheses (list[TypeHypothesis]): Hypotheses supplied as
                list[TypeHypothesis] for this operation.
            plans (list[AnnotationPlan]): Plans supplied as
                list[AnnotationPlan] for this operation.
            request (_RecordRequest): Request supplied as _RecordRequest for
                this operation.

        """
        if _is_trivial_annotation(type_expression=request.annotation):
            return
        confidence: Confidence = Confidence.certain()
        annotation_source: str = TypeExpressionCodec.to_source(
            type_expression=request.annotation,
        )
        reason: Reason = Reason(
            kind=request.evidence,
            message=(
                f"graph inference annotated {request.name!r} "
                f"as {annotation_source}"
            ),
            confidence=confidence,
            node_id=request.node_id,
        )
        hypotheses.append(
            TypeHypothesis(
                type_expression=request.annotation,
                reasons=(reason,),
            ),
        )
        if confidence >= self.config.annotation_threshold:
            plans.append(
                AnnotationPlan(
                    name=request.name,
                    scope_id=request.scope_id,
                    node_id=request.node_id,
                    type_expression=request.annotation,
                    confidence=confidence,
                    reasons=(reason,),
                ),
            )


def _function_parameters(
    *,
    node: FunctionDef | AsyncFunctionDef,
) -> tuple[arg, ...]:
    """Return all regular function parameters.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while return
            all regular function parameters.

    Returns:
        tuple[arg, ...]: tuple[arg, ...] produced by this operation.

    """
    return (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)


def _annassign_name(*, node: AnnAssign) -> str:
    """Return the simple name of an annotated assignment target.

    Args:
        node (AnnAssign): The node examined while return the simple
            name of an annotated assignment target.

    Returns:
        str: str produced by this operation.

    """
    target: expr = node.target
    if isinstance(target, Name):
        return target.id
    if isinstance(target, Attribute):
        return target.attr
    return "<target>"


def _parse_annotation(
    *,
    annotation: expr,
    warnings: list[str],
) -> TypeExpression | None:
    """Parse one annotation AST expression.

    Args:
        annotation (expr): The annotation examined while parse one annotation
            AST expression.
        warnings (list[str]): Warnings supplied as list[str] for this
            operation.

    Returns:
        TypeExpression | None:
            TypeExpression | None produced by this operation.

    """
    try:
        return TypeExpressionCodec.from_ast(node=annotation)
    except TypeExpressionError as error:
        warnings.append(str(object=error))
        return None


def _is_trivial_annotation(*, type_expression: TypeExpression) -> bool:
    """Return whether an annotation is too weak to report.

    Args:
        type_expression (TypeExpression): Type expression supplied as
            TypeExpression for this operation.

    Returns:
        bool: Whether the requested condition holds.

    """
    return (
        isinstance(type_expression, TypeName)
        and type_expression.name in Constants.object_names
    )
