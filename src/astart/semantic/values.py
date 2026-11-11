"""Immutable abstract values, proof states, and bounded lattice operations."""

from __future__ import annotations

from dataclasses import dataclass
from types import EllipsisType
from typing import Literal, final

type Primitive = (
    None | bool | int | float | complex | str | bytes | EllipsisType
)
type AbstractValue = (
    LiteralValue
    | UnknownValue
    | UnboundValue
    | NeverValue
    | ErrorValue
    | SymbolicValue
    | UnionValue
    | SequenceValue
    | MappingValue
    | ObjectReference
    | FunctionValue
    | BuiltinValue
    | BoundMethodValue
    | CoroutineValue
    | GeneratorValue
)
type ProofStatus = Literal[
    "exact",
    "approximate",
    "unknown",
    "unreachable",
    "error",
]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LiteralValue:
    """Exactly established immutable built-in constant.

    Attributes:
        value (Primitive): Known primitive with no user-overridable methods.

    """

    value: Primitive


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UnknownValue:
    """Conservatively unknown abstract value.

    Attributes:
        reason (str): Why a precise result is not established.

    """

    reason: str = "not statically determined"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorValue:
    """Proven exceptional result rather than a normal program value.

    Attributes:
        exception_type (str): Exception type that necessarily arises on this
            path.
        reason (str): Explanation of the failing static operation.

    """

    exception_type: str
    reason: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UnboundValue:
    """The symbol may be unbound at the requested program point."""


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NeverValue:
    """Unreachable execution state."""


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SymbolicValue:
    """Unsupported expression preserved symbolically.

    Attributes:
        expression (str): Nonexecuted Python expression spelling.
        dependencies (tuple[int, ...]): Stable symbol identifiers used by the
            expression.

    """

    expression: str
    dependencies: tuple[int, ...] = ()


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class UnionValue:
    """Bounded set of possible abstract values.

    Attributes:
        options (tuple[AbstractValue, ...]): Each possible value; never an
            unbounded set.

    """

    options: tuple[AbstractValue, ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SequenceValue:
    """Known immutable sequence, including tuple or partially known sequence.

    Attributes:
        elements (tuple[AbstractValue, ...]): Values of individual elements.
        kind (Literal['tuple', 'list']): Python collection kind.

    """

    elements: tuple[AbstractValue, ...]
    kind: Literal["tuple", "list"] = "tuple"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MappingValue:
    """Statically modeled mapping with abstract entries.

    Attributes:
        entries (tuple[tuple[AbstractValue, AbstractValue], ...]): Key-value
            pairs in evaluation order.

    """

    entries: tuple[tuple[AbstractValue, AbstractValue], ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectReference:
    """Set of abstract object identities, representing may-aliasing.

    Attributes:
        object_ids (frozenset[int]): Nonempty possible allocation identities.

    """

    object_ids: frozenset[int]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FunctionValue:
    """Reference to a known Python function definition.

    Attributes:
        node_id (int): Persistent syntax identity of the definition.

    """

    node_id: int


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltinValue:
    """Recognized built-in function name, never invoked on unknown values.

    Attributes:
        name (str): Name of the explicitly modeled built-in.

    """

    name: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BoundMethodValue:
    """Method name and proven abstract receiver, not a callable runtime object.

    Attributes:
        receiver (ObjectReference): Possible receiver object identities.
        name (str): Attribute name of the modeled method.

    """

    receiver: ObjectReference
    name: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CoroutineValue:
    """Deferred invocation: a coroutine body has not yet been executed.

    Attributes:
        arguments (tuple[AbstractValue, ...]): Arguments retained as
            tuple[AbstractValue, ...] by this instance.
        caller_id (int): Caller id retained as int by this instance.
        function_id (int): Function id retained as int by this instance.
        keywords (tuple[tuple[str, AbstractValue], ...]): Keywords retained as
            tuple[tuple[str,
            AbstractValue], ...] by this instance.

    """

    function_id: int
    caller_id: int
    arguments: tuple[AbstractValue, ...]
    keywords: tuple[tuple[str, AbstractValue], ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GeneratorValue:
    """Deferred generator object; its body has not been iterated.

    Attributes:
        arguments (tuple[AbstractValue, ...]): Arguments retained as
            tuple[AbstractValue, ...] by this instance.
        caller_id (int): Caller id retained as int by this instance.
        function_id (int): Function id retained as int by this instance.
        keywords (tuple[tuple[str, AbstractValue], ...]): Keywords retained as
            tuple[tuple[str,
            AbstractValue], ...] by this instance.

    """

    function_id: int
    caller_id: int
    arguments: tuple[AbstractValue, ...]
    keywords: tuple[tuple[str, AbstractValue], ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ValueEvidence:
    """Immutable causal record for a statically inferred abstract value.

    Attributes:
        dependencies (tuple[int, ...]): Dependencies retained as tuple[int,
            ...] by this instance.
        description (str): Description retained as str by this instance.
        node_id (int): Node id retained as int by this instance.

    """

    node_id: int
    description: str
    dependencies: tuple[int, ...] = ()


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InferenceResult:
    """Static inference result with provenance and proof classification.

    Attributes:
        value (AbstractValue): Safe abstract interpretation of the expression.
        status (ProofStatus): Exact, approximate, unknown, unreachable or
            error.
        dependencies (tuple[int, ...]): Symbol identifiers relevant to the
            result.
        trace (tuple[str, ...]): Deterministic explanation generated during
            evaluation.
        possible_exceptions (tuple[str, ...]): Possible raised exception class
            names.

    """

    value: AbstractValue
    status: ProofStatus
    dependencies: tuple[int, ...] = ()
    trace: tuple[str, ...] = ()
    possible_exceptions: tuple[str, ...] = ()


def join_values(
    *,
    left: AbstractValue,
    right: AbstractValue,
    limit: int = 8,
) -> AbstractValue:
    """Return a bounded conservative least upper approximation.

    Args:
        left (AbstractValue): Value from the first path.
        right (AbstractValue): Value from the second path.
        limit (int): Maximum disjuncts before widening to unknown.

    Returns:
        AbstractValue: Conservative union of all possible values.

    """
    if left == right or isinstance(right, NeverValue):
        return left
    if isinstance(left, NeverValue):
        return right
    if isinstance(left, UnknownValue) or isinstance(right, UnknownValue):
        return UnknownValue(reason="joined with unknown alternative")
    if isinstance(left, ObjectReference) and isinstance(
        right,
        ObjectReference,
    ):
        return ObjectReference(object_ids=left.object_ids | right.object_ids)
    options: list[AbstractValue] = []
    for value in (left, right):
        candidates: tuple[AbstractValue, ...] = (
            value.options if isinstance(value, UnionValue) else (value,)
        )
        for candidate in candidates:
            if candidate not in options:
                options.append(candidate)
            if len(options) > limit:
                return UnknownValue(reason="abstract union exceeds budget")
    return UnionValue(options=tuple(options))


def truth_value(*, value: AbstractValue) -> bool | None:
    """Prove Boolean truth for safe built-in abstract values only.

    Args:
        value (AbstractValue): Value with a potential known truthiness.

    Returns:
        bool | None: True, False, or None if uncertain.

    """
    if isinstance(value, LiteralValue):
        return bool(value.value)
    if isinstance(value, SequenceValue):
        return bool(value.elements)
    if isinstance(value, MappingValue):
        return bool(value.entries)
    if isinstance(value, UnionValue):
        proofs: set[bool | None] = {
            truth_value(value=item) for item in value.options
        }
        return next(iter(proofs)) if len(proofs) == 1 else None
    return None


def proof_status(*, value: AbstractValue) -> ProofStatus:
    """Classify exact versus conservative abstract results.

    Args:
        value (AbstractValue): An abstract value.

    Returns:
        ProofStatus: Deterministic proof classification.

    """
    if isinstance(value, ErrorValue):
        return "error"
    if isinstance(value, NeverValue):
        return "unreachable"
    if isinstance(value, UnknownValue):
        return "unknown"
    if isinstance(value, (UnionValue, UnboundValue, SymbolicValue)):
        return "approximate"
    return "exact"
