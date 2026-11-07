"""Inference-layer models and resolvers."""

from __future__ import annotations

from astart._graph.inference.explanations import (
    AnnotationExplanation,
    InferenceExplanationBuilder,
    InferenceExplanationReport,
)
from astart._graph.inference.reasons import (
    Confidence,
    EvidenceKind,
    Reason,
)
from astart._graph.inference.resolver import (
    InferenceResolver,
    InferenceResult,
)

__all__: list[str] = [
    "AnnotationExplanation",
    "Confidence",
    "EvidenceKind",
    "InferenceExplanationBuilder",
    "InferenceExplanationReport",
    "InferenceResolver",
    "InferenceResult",
    "Reason",
]
