"""API-first AST graph inference package."""

from __future__ import annotations

from astart.graph import aprint
from astart.graph.application import CommandLineApplication
from astart.graph.conversion.artifacts import (
    ConversionArtifactPaths,
    ConversionArtifactWriter,
    ConversionRunSummary,
)
from astart.graph.conversion.engine import (
    ConversionResult,
    GraphOnlyConverter,
)
from astart.graph.conversion.pipeline import ConversionPipeline
from astart.graph.graph.document import AstDocument
from astart.graph.graph.type_expressions import TypeExpressionCodec
from astart.graph.graph.usage import UsageGraph, build_usage_graph
from astart.graph.inference.explanations import (
    InferenceExplanationReport,
)
from astart.graph.inference.resolver import (
    InferenceResolver,
    InferenceResult,
)
from astart.graph.stubs.index import LazyStubIndex

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
