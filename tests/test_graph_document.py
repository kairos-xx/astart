"""Exercise graph documents, positions, usage graphs and the resolver."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart._graph import (
    AstDocument,
    InferenceResolver,
    LazyStubIndex,
    build_usage_graph,
)
from astart._graph.graph.document import AstGraphNode, TraversalOrder
from astart._graph.graph.positions import (
    LineIndex,
    PositionDelta,
    SourcePosition,
    SourceSpan,
)
from astart._graph.graph.type_expressions import TypeName
from astart._graph.graph.usage import EdgeKind, UsageGraph, UsageKind
from astart._graph.inference.explanations import (
    InferenceExplanationBuilder,
    InferenceExplanationReport,
)
from astart._graph.inference.reasons import (
    Confidence,
    EvidenceKind,
    Reason,
    TypeHypothesis,
)
from astart._graph.inference.resolver import (
    AnnotationPlan,
    InferenceResolverConfig,
    InferenceResult,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart._graph.graph.usage import Scope


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source: Grouped module constant.

    """

    source: Final[str] = dedent(
        text="""\
    import os
    from typing import Any

    value: int = 3
    other: Any = None
    bad: f(1) = 3
    table = {}
    table["k"]: int = 2

    def greet(name: str, *rest: int, flag: bool = False) -> str:
        '''Say hello.'''
        message = f"hi {name}"
        for part in rest:
            message += str(part)
        if flag:
            return message.upper()
        return message

    async def fetch(url: "list[int] | None") -> dict[str, int]:
        result = await greet(url)
        return {"a": len(result)}

    class Box(object):
        size: int = 0

        def __init__(self, v):
            self.v = v
            self.count: int = 0

        def get(self):
            return self.v

    box = Box(3)
    text = greet("x", 1, 2, flag=True)
    items = [greet(n) for n in ("a", "b")]
    with open("f") as handle:
        data = handle.read()
    """,
    )


def _document() -> AstDocument:
    """Build the sample document.

    Returns:
        Document wrapping the sample source.

    """
    return AstDocument.from_source(
        source=Constants.source,
        filename="sample.py",
    )


def test_position_validation_and_translation() -> None:
    """Reject invalid positions and translate or shift valid ones."""
    with pytest.raises(expected_exception=ValueError, match="one-based"):
        SourcePosition(line=0, column=0)
    with pytest.raises(expected_exception=ValueError, match="zero-based"):
        SourcePosition(line=1, column=-1)
    origin: SourcePosition = SourcePosition(line=2, column=4)
    target: SourcePosition = SourcePosition(line=5, column=8)
    point: SourcePosition = SourcePosition(line=3, column=6)
    expect_equal(
        actual=point.translated(origin=origin, target=target),
        expected=SourcePosition(line=6, column=10),
    )
    delta: PositionDelta = PositionDelta(
        pivot=SourcePosition(line=3, column=0),
        line_delta=2,
        column_delta=-9,
    )
    expect_equal(
        actual=point.shifted(delta=delta),
        expected=SourcePosition(line=5, column=0),
    )
    expect_equal(
        actual=SourcePosition(line=9, column=3).shifted(delta=delta),
        expected=SourcePosition(line=11, column=3),
    )


def test_span_construction_and_relations() -> None:
    """Build, compare and shift spans."""
    start: SourcePosition = SourcePosition(line=1, column=2)
    with pytest.raises(expected_exception=ValueError, match="inverted|before"):
        SourceSpan(start=SourcePosition(line=2, column=0), end=start)
    one: SourceSpan = SourceSpan.one_column_at(position=start)
    single: SourceSpan = SourceSpan.from_text(start=start, text="abc")
    multi: SourceSpan = SourceSpan.from_text(
        start=start,
        text="""\
ab
cde""",
    )
    expect_equal(actual=one.end.column, expected=3)
    expect_equal(actual=single.end.column, expected=5)
    expect_equal(actual=multi.end, expected=SourcePosition(line=2, column=3))
    outer: SourceSpan = SourceSpan.enclosing(spans=(one, single, multi))
    expect_true(condition=outer.contains_span(other=multi))
    expect_true(condition=outer.contains(position=start))
    expect_false(condition=outer.contains(position=outer.end))
    expect_true(condition=single.intersects(other=multi))
    far: SourceSpan = SourceSpan.one_column_at(
        position=SourcePosition(line=9, column=0),
    )
    expect_false(condition=single.intersects(other=far))
    with pytest.raises(expected_exception=ValueError, match="empty"):
        SourceSpan.enclosing(spans=())
    moved: SourceSpan = single.translated(
        origin=start,
        target=SourcePosition(line=4, column=0),
    )
    expect_equal(actual=moved.start, expected=SourcePosition(line=4, column=0))
    delta: PositionDelta = PositionDelta.from_replacement(
        old_span=single,
        new_span=multi,
    )
    expect_false(condition=delta.is_zero())
    expect_true(
        condition=PositionDelta.from_replacement(
            old_span=single,
            new_span=single,
        ).is_zero(),
    )
    expect_equal(
        actual=single.shifted(delta=delta).start,
        expected=SourcePosition(line=2, column=0),
    )


def test_line_index_converts_offsets() -> None:
    """Convert positions to offsets, clamping outside the text."""
    index: LineIndex = LineIndex.from_source(
        source="""\
ab
cd
""",
    )
    expect_equal(
        actual=index.position_to_offset(
            position=SourcePosition(line=2, column=1),
        ),
        expected=4,
    )
    expect_equal(
        actual=index.position_to_offset(
            position=SourcePosition(line=99, column=99),
        ),
        expected=6,
    )
    expect_equal(
        actual=index.span_text(
            span=SourceSpan(
                start=SourcePosition(line=1, column=1),
                end=SourcePosition(line=2, column=1),
            ),
        ),
        expected="""\
b
c""",
    )
    empty: LineIndex = LineIndex.from_source(source="")
    expect_equal(
        actual=empty.position_to_offset(
            position=SourcePosition(line=1, column=0),
        ),
        expected=0,
    )


def test_document_navigation() -> None:
    """Navigate parents, children, ancestors, tokens and traversals."""
    document: AstDocument = _document()
    functions: tuple[AstGraphNode, ...] = document.nodes_of_kind(
        kind="FunctionDef",
    )
    expect_true(condition=len(functions) >= 1)
    function: AstGraphNode = functions[0]
    expect_true(condition=function.has_parent())
    parent: AstGraphNode = expect_not_none(
        value=document.parent_of(node=function),
    )
    expect_false(condition=parent.has_parent())
    expect_is(actual=document.parent_of(node=parent), expected=None)
    expect_true(condition=len(document.children_of(node=function)) > 0)
    expect_equal(actual=len(document.ancestors_of(node=function)), expected=1)
    expect_is(actual=document.node_by_id(node_id=-1), expected=None)
    expect_in(
        item="def greet",
        container=str(object=document.source_for_node(node=function)),
    )
    span: SourceSpan = expect_not_none(value=function.span)
    expect_true(condition=len(document.tokens_for_span(span=span)) > 0)
    preorder: tuple[AstGraphNode, ...] = document.walk_nodes()
    ast_walk: tuple[AstGraphNode, ...] = document.walk_nodes(
        order=TraversalOrder.AST_WALK,
    )
    expect_true(condition=len(preorder) > 0)
    expect_true(condition=len(ast_walk) > 0)
    expect_is(actual=document.nodes_of_kind(kind="Nope"), expected=())
    spanless: AstGraphNode = document.nodes_of_kind(kind="Load")[0]
    expect_is(actual=document.source_for_node(node=spanless), expected=None)


def test_usage_graph_indexes_symbols_events_and_edges() -> None:
    """Query every index exposed by the usage graph."""
    document: AstDocument = _document()
    graph: UsageGraph = build_usage_graph(document=document)
    expect_true(condition=len(graph.scopes) > 0)
    expect_true(condition=len(graph.symbols) > 0)
    expect_true(condition=len(graph.events) > 0)
    expect_true(condition=len(graph.call_sites) > 0)
    scope: Scope = graph.scopes[0]
    expect_not_none(value=graph.scope_by_id(scope_id=scope.scope_id))
    expect_is(actual=graph.scope_by_id(scope_id=-5), expected=None)
    expect_true(condition=len(graph.symbols_named(name="message")) > 0)
    expect_equal(actual=graph.symbols_named(name="absent"), expected=())
    expect_true(condition=len(graph.calls_named(name="greet")) > 0)
    expect_equal(actual=graph.calls_named(name="absent"), expected=())
    for kind in UsageKind:
        graph.events_of_kind(kind=kind)
    for symbol_scope in graph.scopes:
        graph.symbols_in_scope(scope_id=symbol_scope.scope_id)
    for event in graph.events:
        graph.events_for_node(node_id=event.node_id)
    for edge in graph.edges:
        graph.outgoing_edges(node_id=edge.source_node_id)
        graph.incoming_edges(node_id=edge.target_node_id)
        for direction in (None, *EdgeKind):
            graph.reachable(
                start_node_id=edge.source_node_id,
                direction=direction,
                max_depth=3,
            )
    expect_equal(actual=graph.reachable(start_node_id=-1), expected=())


def test_resolver_plans_annotations_and_baselines() -> None:
    """Plan annotations and skip sites present in a baseline document."""
    document: AstDocument = _document()
    graph: UsageGraph = build_usage_graph(document=document)
    index: LazyStubIndex = LazyStubIndex.from_path(path=document_path())
    resolver: InferenceResolver = InferenceResolver.create(
        document=document,
        usage_graph=graph,
        stub_index=index,
    )
    result: InferenceResult = resolver.resolve()
    expect_true(condition=result.annotation_count() > 0)
    expect_true(condition=len(result.hypothesis_sources()) > 0)
    expect_true(condition=len(result.warnings) > 0)
    plan: AnnotationPlan = result.annotation_plans[0]
    expect_true(condition=len(plan.type_source()) > 0)
    baseline: AstDocument = AstDocument.from_source(
        source=dedent(
            text="""\
    def greet(name: str) -> str:
        return name
    value: int = 1
    """,
        ),
        filename="base.py",
    )
    reduced: InferenceResult = resolver.resolve(baseline_document=baseline)
    expect_true(
        condition=reduced.annotation_count() < result.annotation_count(),
    )
    strict: InferenceResolver = InferenceResolver.create(
        document=document,
        usage_graph=graph,
        stub_index=index,
        config=InferenceResolverConfig(
            annotation_threshold=Confidence(value=1.0),
        ),
    )
    expect_true(condition=strict.resolve().annotation_count() > 0)


def document_path() -> Path:
    """Return a path that never holds stubs.

    Returns:
        Non-existent path used for an empty stub index.

    """
    return Path("/nonexistent-stubs")


def test_explanations_describe_plans_without_spans() -> None:
    """Describe plans for nodes with and without document spans."""
    document: AstDocument = _document()
    graph: UsageGraph = build_usage_graph(document=document)
    resolver: InferenceResolver = InferenceResolver.create(
        document=document,
        usage_graph=graph,
        stub_index=LazyStubIndex.from_path(path=document_path()),
    )
    result: InferenceResult = resolver.resolve()
    report: InferenceExplanationReport = InferenceExplanationBuilder.build(
        document=document,
        usage_graph=graph,
        inference=result,
        stage_names=("a", "b"),
        validation_messages=("ok",),
    )
    expect_true(condition=report.summary.annotation_count > 0)
    markdown: str = report.to_markdown()
    expect_in(item="1. `a`", container=markdown)
    expect_in(item="confidence=", container=markdown)
    expect_true(condition=len(str(object=report.to_json_data())) > 0)
    orphan: AnnotationPlan = AnnotationPlan(
        name="ghost",
        scope_id=0,
        node_id=-1,
        type_expression=result.annotation_plans[0].type_expression,
        confidence=Confidence.strong(),
        reasons=(
            Reason(
                kind=EvidenceKind.LITERAL,
                message="m",
                confidence=Confidence.weak(),
                node_id=None,
            ),
        ),
    )
    empty: InferenceExplanationReport = InferenceExplanationBuilder.build(
        document=document,
        usage_graph=graph,
        inference=InferenceResult(hypotheses=(), annotation_plans=(orphan,)),
    )
    expect_is(actual=empty.annotations[0].span, expected=None)
    expect_in(item="ghost", container=empty.to_markdown())
    none_report: InferenceExplanationReport = (
        InferenceExplanationBuilder.build(
            document=document,
            usage_graph=graph,
            inference=InferenceResult(hypotheses=(), annotation_plans=()),
        )
    )
    expect_equal(actual=none_report.summary.average_confidence, expected=0.0)


def test_reasons_combine_confidence() -> None:
    """Validate and combine confidence values and hypotheses."""
    with pytest.raises(expected_exception=ValueError, match="between"):
        Confidence(value=1.5)
    combined: Confidence = Confidence.weak().combine(other=Confidence.strong())
    expect_true(condition=combined.value > Confidence.strong().value)
    hypothesis: TypeHypothesis = TypeHypothesis(
        type_expression=TypeName(name="int"),
        reasons=(),
    )
    expect_equal(actual=hypothesis.confidence.value, expected=0.0)
    expect_equal(actual=hypothesis.to_source(), expected="int")
    with_reasons: TypeHypothesis = TypeHypothesis(
        type_expression=TypeName(name="int"),
        reasons=(
            Reason(
                kind=EvidenceKind.CALL,
                message="x",
                confidence=Confidence.weak(),
            ),
            Reason(
                kind=EvidenceKind.RETURN,
                message="y",
                confidence=Confidence.weak(),
            ),
        ),
    )
    expect_true(
        condition=with_reasons.confidence.value > Confidence.weak().value,
    )
