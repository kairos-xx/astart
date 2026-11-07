"""Exercise conversion contexts, pipeline order and the checkpoint backend."""

from __future__ import annotations

from ast import parse
from typing import TYPE_CHECKING, Final
from typing import final as _group_final_final

import pytest
from astart._graph import AstDocument, LazyStubIndex, build_usage_graph
from astart._graph.backend.checkpoint import CheckpointBackend
from astart._graph.conversion.context import (
    ConversionContext,
    ConversionOptions,
    ConversionPipelineError,
)
from astart._graph.conversion.pipeline import ConversionPipeline
from astart._graph.inference.explanations import (
    ExplanationSummary,
    InferenceExplanationReport,
)
from astart._graph.inference.resolver import InferenceResult

from tests.expectations import expect_equal, expect_in, expect_is, expect_true

if TYPE_CHECKING:
    from ast import Module
    from pathlib import Path

    from astart._graph.graph.usage import UsageGraph


@_group_final_final
class Constants:
    """Group module-level constants.

    Attributes:
        min_statements: Grouped module constant.
        source: Grouped module constant.

    """

    min_statements: Final[int] = 2
    source: Final[str] = """\
def f(x):
    return x + 1

value = f(2)
"""


def _context(*, tmp_path: Path) -> ConversionContext:
    """Create an empty conversion context.

    Args:
        tmp_path: Directory used as the stub root.

    Returns:
        Initial context for the sample source.

    """
    return ConversionContext.create(
        source=Constants.source,
        options=ConversionOptions(
            source_path=None,
            stubs_path=tmp_path,
            filename="sample.py",
        ),
    )


def test_unset_context_fields_raise_pipeline_errors(*, tmp_path: Path) -> None:
    """Fail loudly when a stage reads data that was never produced.

    Args:
        tmp_path: Directory used as the stub root.

    """
    context: ConversionContext = _context(tmp_path=tmp_path)
    for getter in (
        context.require_backend_module,
        context.require_backend_source,
        context.require_input_document,
        context.require_stub_index,
        context.require_output_document,
        context.require_output_usage_graph,
        context.require_inference,
        context.require_explanation,
    ):
        with pytest.raises(expected_exception=ConversionPipelineError):
            getter()


def test_context_updates_return_new_instances(*, tmp_path: Path) -> None:
    """Attach every artifact and read it back through the require methods.

    Args:
        tmp_path: Directory used as the stub root.

    """
    context: ConversionContext = _context(tmp_path=tmp_path)
    document: AstDocument = AstDocument.from_source(
        source=Constants.source,
        filename="sample.py",
    )
    graph: UsageGraph = build_usage_graph(document=document)
    index: LazyStubIndex = LazyStubIndex.from_path(path=tmp_path)
    module: Module = parse(source=Constants.source)
    inference: InferenceResult = InferenceResult(
        hypotheses=(),
        annotation_plans=(),
    )
    report: InferenceExplanationReport = InferenceExplanationReport(
        summary=ExplanationSummary(
            annotation_count=0,
            evidence_count=0,
            average_confidence=0.0,
            warning_count=0,
            stage_count=0,
        ),
        annotations=(),
    )
    updated: ConversionContext = (
        context.with_input_document(document=document)
        .with_input_usage_graph(usage_graph=graph)
        .with_stub_index(stub_index=index)
        .with_backend_module(module=module)
        .with_backend_source(source=Constants.source)
        .with_output_document(document=document)
        .with_output_usage_graph(usage_graph=graph)
        .with_inference(inference=inference)
        .with_explanation(explanation=report)
        .with_validation_message(message="note")
        .with_completed_stage(name="stage")
    )
    expect_is(actual=updated.require_input_document(), expected=document)
    expect_is(actual=updated.require_stub_index(), expected=index)
    expect_is(actual=updated.require_backend_module(), expected=module)
    expect_equal(
        actual=updated.require_backend_source(),
        expected=Constants.source,
    )
    expect_is(actual=updated.require_output_document(), expected=document)
    expect_is(actual=updated.require_output_usage_graph(), expected=graph)
    expect_is(actual=updated.require_inference(), expected=inference)
    expect_is(actual=updated.require_explanation(), expected=report)
    expect_equal(actual=updated.validation_messages, expected=("note",))
    expect_equal(actual=updated.completed_stage_names, expected=("stage",))
    expect_is(actual=context.input_document, expected=None)


def test_pipeline_variants_and_stage_names(*, tmp_path: Path) -> None:
    """Create pipelines with and without syntax validation.

    Args:
        tmp_path: Directory used as the stub root.

    """
    full: ConversionPipeline = ConversionPipeline.create()
    lean: ConversionPipeline = ConversionPipeline.create(validate_syntax=False)
    expect_true(condition=len(full.stage_names()) > len(lean.stage_names()))
    final: ConversionContext = lean.run(context=_context(tmp_path=tmp_path))
    expect_equal(
        actual=final.completed_stage_names,
        expected=lean.stage_names(),
    )
    expect_true(
        condition=len(final.require_backend_module().body)
        >= Constants.min_statements,
    )


def test_checkpoint_backend_converts_source_and_modules() -> None:
    """Convert from source text and from a pre-parsed module."""
    backend: CheckpointBackend = CheckpointBackend()
    expect_equal(actual=backend.name, expected="checkpoint-graph-backend")
    from_source: str = backend.convert(source=Constants.source)
    from_module: str = backend.convert(
        source=Constants.source,
        module=parse(source=Constants.source),
    )
    expect_in(item="def f", container=from_source)
    expect_equal(actual=from_source, expected=from_module)
    module: Module = backend.convert_module(source=Constants.source)
    again: Module = backend.convert_module(
        source=Constants.source,
        module=parse(source=Constants.source),
    )
    expect_equal(actual=len(again.body), expected=len(module.body))
