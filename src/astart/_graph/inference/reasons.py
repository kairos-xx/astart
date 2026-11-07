"""Reason, confidence, and evidence models for type inference."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from astart._graph.graph.type_expressions import (
    TypeExpression,
    TypeExpressionCodec,
)


class EvidenceKind(StrEnum):
    """Kinds of evidence that can support a type hypothesis.

    Attributes:
        ANNOTATION: Annotation associated with this instance.
        CALL: Call associated with this instance.
        CONDITION: Condition associated with this instance.
        IMPORT_STUB: Import stub associated with this instance.
        LITERAL: Literal associated with this instance.
        OPERATOR: Operator associated with this instance.
        RETURN: Return associated with this instance.
        SUBSCRIPT: Subscript associated with this instance.
        TYPE_FLOW: Type flow associated with this instance.

    """

    ANNOTATION = "annotation"
    CALL = "call"
    CONDITION = "condition"
    IMPORT_STUB = "import_stub"
    LITERAL = "literal"
    OPERATOR = "operator"
    RETURN = "return"
    SUBSCRIPT = "subscript"
    TYPE_FLOW = "type_flow"


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """A bounded confidence value.

    Attributes:
        value: Value retained as float by this instance.

    """

    value: float

    @classmethod
    def certain(cls) -> Self:
        """Return maximum confidence.

        Returns:
            Self produced by this operation.

        """
        return cls(value=1.0)

    @classmethod
    def strong(cls) -> Self:
        """Return strong non-annotation confidence.

        Returns:
            Self produced by this operation.

        """
        return cls(value=0.85)

    @classmethod
    def weak(cls) -> Self:
        """Return weak confidence.

        Returns:
            Self produced by this operation.

        """
        return cls(value=0.35)

    def combine(self, *, other: Confidence) -> Self:
        """Combine independent confidence values conservatively.

        Args:
            other: Other supplied as Confidence for this operation.

        Returns:
            Self produced by this operation.

        """
        combined: float = 1.0 - ((1.0 - self.value) * (1.0 - other.value))
        return self.__class__(value=min(1.0, combined))

    def __post_init__(self) -> None:
        """Validate confidence range."""
        if not 0.0 <= self.value <= 1.0:
            msg: str = "confidence must be between 0.0 and 1.0."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Reason:
    """A single explanation for an inferred type fact.

    Attributes:
        confidence: Confidence assigned to this inference or observation.
        kind: Kind retained as EvidenceKind by this instance.
        message: Explanation associated with this result.
        node_id: Node id retained as int | None by this instance.

    """

    kind: EvidenceKind
    message: str
    confidence: Confidence
    node_id: int | None = None


@dataclass(frozen=True, slots=True)
class TypeHypothesis:
    """A type expression supported by one or more reasons.

    Attributes:
        reasons: Reasons retained as tuple[Reason, ...] by this instance.
        type_expression: Type expression retained as TypeExpression by this
            instance.

    """

    type_expression: TypeExpression
    reasons: tuple[Reason, ...]

    @property
    def confidence(self) -> Confidence:
        """Return the strongest reason confidence.

        Returns:
            Confidence produced by this operation.

        """
        if not self.reasons:
            return Confidence(value=0.0)
        confidence: Confidence = Confidence(value=0.0)
        reason: Reason
        for reason in self.reasons:
            confidence = confidence.combine(other=reason.confidence)
        return confidence

    def to_source(self) -> str:
        """Render the hypothesis type expression.

        Returns:
            Rendered source text produced by this operation.

        """
        return TypeExpressionCodec.to_source(
            type_expression=self.type_expression,
        )
