"""API-first AST graph inference package."""

from __future__ import annotations

from astart._graph import aprint
from astart._graph.application import CommandLineApplication
from astart._graph.conversion.artifacts import (
    ConversionArtifactPaths,
    ConversionArtifactWriter,
    ConversionRunSummary,
)
from astart._graph.conversion.engine import (
    ConversionResult,
    GraphOnlyConverter,
)
from astart._graph.conversion.pipeline import ConversionPipeline
from astart._graph.graph.document import AstDocument
from astart._graph.graph.type_expressions import TypeExpressionCodec
from astart._graph.graph.usage import UsageGraph, build_usage_graph
from astart._graph.inference.explanations import (
    InferenceExplanationReport,
)
from astart._graph.inference.resolver import (
    InferenceResolver,
    InferenceResult,
)
from astart._graph.stubs.index import LazyStubIndex

__all__: list[str] = [
    "AstDocument",
    "CommandLineApplication",
    "ConversionArtifactPaths",
    "ConversionArtifactWriter",
    "ConversionPipeline",
    "ConversionResult",
    "ConversionRunSummary",
    "GraphOnlyConverter",
    "InferenceExplanationReport",
    "InferenceResolver",
    "InferenceResult",
    "LazyStubIndex",
    "TypeExpressionCodec",
    "UsageGraph",
    "aprint",
    "build_usage_graph",
]
