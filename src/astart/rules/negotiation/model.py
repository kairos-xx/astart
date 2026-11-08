"""Data model of the contract graph: relations, candidates, contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final


@final
class Relation(StrEnum):
    """What a contract says about how two nodes constrain each other.

    Attributes:
        assigns: The source value is assigned to the target.
        returns: The source is returned by the target function.
        argument: The source argument is passed to the target parameter.
        call_result: The source function's result is the target expression.
        element: The target is an element of the source container.
        key: The target is a key of the source mapping.
        mapping_value: The target is a value of the source mapping.
        item: The target is ``source[index]`` for a list, mapping or string.
        list_of: The target is a list whose elements are the source.
        set_of: The target is a set whose elements are the source.
        attribute: The target is an attribute of the source.
        instance_field: The target is an instance attribute of a class.
        class_field: The target is a class attribute.
        narrows: The source narrows the target inside a branch.
        requires: The source needs the target's capabilities.
        operator: The target is the result of an operator on the source.
        context_enter: The target is the ``__enter__`` result of the source.
        context_exit: The target is the ``__exit__`` result of the source.

    """

    assigns = "assigns"
    returns = "returns"
    argument = "argument"
    call_result = "call_result"
    element = "element"
    key = "key"
    mapping_value = "value"
    item = "item"
    list_of = "list_of"
    set_of = "set_of"
    attribute = "attribute"
    instance_field = "instance_field"
    class_field = "class_field"
    narrows = "narrows"
    requires = "requires"
    operator = "operator"
    context_enter = "context_enter"
    context_exit = "context_exit"


@final
class Polarity(StrEnum):
    """How a contract contributes to the target's belief.

    Attributes:
        union: The type joins the belief (assignments, returns, containers).
        intersection: The type narrows the belief (``isinstance`` and such).
        declaration: A written annotation; hard evidence.
        capability: A needed operation; informs but carries no type.
        conflict: Evidence that cannot hold together with the belief.

    """

    union = "union"
    intersection = "intersection"
    declaration = "declaration"
    capability = "capability"
    conflict = "conflict"


@final
class Origin(StrEnum):
    """Where a candidate's evidence comes from.

    Attributes:
        syntax: The expression's own syntax proves the type (E0).
        declared: An annotation, base signature or stub declares it (E1).
        call_sites: Syntax-proven argument types at call sites (E2/E3).
        default: The default value's literal type.
        protocol: A protocol dunder's declared result, with a body that fits.
        calibrated: A category measured against annotated code and found
            reliable (syntactically boolean returns); needs the engine too.
        inferred: The inference engine proposed it (E5); never sufficient
            alone.

    """

    syntax = "syntax"
    declared = "declared"
    call_sites = "call_sites"
    default = "default"
    protocol = "protocol"
    calibrated = "calibrated"
    inferred = "inferred"


@final
@dataclass(frozen=True, slots=True)
class Candidate:
    """One type proposal for a node.

    Attributes:
        type_text: The type as annotation source.
        confidence: Ordering and pruning weight in ``(0, 1]``; it never
            decides acceptance by itself.
        distance: Contracts travelled from the seed.
        origins: What supports the type.
        explanation: Why it was proposed.
        slot: Names the derived contract that produced it; a later candidate
            with the same slot replaces this one instead of joining it.

    """

    type_text: str
    confidence: float
    distance: int
    origins: frozenset[Origin]
    explanation: str
    slot: str = ""

    @property
    def independent(self) -> bool:
        """Tell whether something other than inference supports the type.

        Returns:
            ``True`` when any origin is not ``inferred``.

        """
        return bool(self.origins - {Origin.inferred})

    def decayed(self, *, decay: float) -> Candidate:
        """Return the candidate one contract further away.

        Args:
            decay: Factor applied to the confidence.

        Returns:
            A copy with lower confidence and larger distance.

        """
        return Candidate(
            type_text=self.type_text,
            confidence=self.confidence * decay,
            distance=self.distance + 1,
            origins=self.origins,
            explanation=self.explanation,
            slot=self.slot,
        )

    def retyped(self, *, type_text: str) -> Candidate:
        """Return the candidate with another type and the same support.

        Args:
            type_text: The new type.

        Returns:
            A copy carrying the new type.

        """
        return Candidate(
            type_text=type_text,
            confidence=self.confidence,
            distance=self.distance,
            origins=self.origins,
            explanation=self.explanation,
            slot=self.slot,
        )


@final
@dataclass(frozen=True, slots=True)
class Contract:
    """A directed constraint between two nodes.

    Attributes:
        source: Path text of the node the candidate leaves.
        target: Path text of the node it reaches.
        relation: What the contract states.
        polarity: How it contributes to the target.
        confidence: Trust in the contract itself.
        decay: Factor applied to candidates that cross it.
        explanation: Why the contract exists.

    """

    source: str
    target: str
    relation: Relation
    polarity: Polarity
    confidence: float
    decay: float
    explanation: str


@final
@dataclass(frozen=True, slots=True)
class Conflict:
    """Two types that cannot both hold for one node.

    Attributes:
        path: Path text of the node.
        left: The type already believed.
        right: The type that clashes with it.
        explanation: Why the clash was recorded.

    """

    path: str
    left: str
    right: str
    explanation: str
