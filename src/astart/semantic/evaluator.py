"""Bounded, side-effect-aware abstract interpreter for mutable Python ASTs.

Analyzed source is never executed. All supported operations are modeled through
explicit transfer functions over known immutable Python built-in values.
"""

from __future__ import annotations

import operator
from ast import (
    AST,
    Add,
    And,
    AnnAssign,
    Assert,
    Assign,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    Attribute,
    AugAssign,
    Await,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    BoolOp,
    Break,
    Call,
    ClassDef,
    Compare,
    Constant,
    Continue,
    Delete,
    Dict,
    Div,
    Eq,
    ExceptHandler,
    Expr,
    FloorDiv,
    For,
    FormattedValue,
    FunctionDef,
    GeneratorExp,
    Global,
    Gt,
    GtE,
    If,
    IfExp,
    Import,
    ImportFrom,
    In,
    Invert,
    Is,
    IsNot,
    JoinedStr,
    Lambda,
    List,
    ListComp,
    Load,
    LShift,
    Lt,
    LtE,
    Match,
    MatchAs,
    MatchClass,
    MatchMapping,
    MatchOr,
    MatchSequence,
    MatchSingleton,
    MatchStar,
    MatchValue,
    Mod,
    Mult,
    Name,
    NamedExpr,
    Nonlocal,
    Not,
    NotEq,
    NotIn,
    Or,
    Pass,
    Pow,
    Raise,
    Return,
    RShift,
    Set,
    Starred,
    Sub,
    Subscript,
    Try,
    TryStar,
    Tuple,
    TypeAlias,
    UAdd,
    UnaryOp,
    USub,
    While,
    With,
    Yield,
    YieldFrom,
    arg,
    expr,
    iter_child_nodes,
    stmt,
)
from collections import deque
from dataclasses import dataclass, field
from time import monotonic
from typing import TYPE_CHECKING, Final, Literal, final

from astart._graph.dispatch import handler_names
from astart.node_attributes import (
    clear_attribute,
    read_attribute,
    write_attribute,
)
from astart.semantic.functions import CallSummaryCache, FunctionSummary
from astart.semantic.heap import AbstractHeap, HeapObject
from astart.semantic.values import (
    AbstractValue,
    BoundMethodValue,
    BuiltinValue,
    CoroutineValue,
    ErrorValue,
    FunctionValue,
    GeneratorValue,
    InferenceResult,
    LiteralValue,
    NeverValue,
    ObjectReference,
    Primitive,
    SequenceValue,
    UnboundValue,
    UnionValue,
    UnknownValue,
    ValueEvidence,
    join_values,
    proof_status,
    truth_value,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from astart.semantic.identities import (
        EdgeKind,
        IdentityIndex,
        Occurrence,
        Symbol,
    )
    from astart.semantic.scopes import ScopeGraph
type Control = Literal["normal", "return", "break", "continue", "raise"]


def arithmetic_function(
    *,
    name: str,
) -> Callable[[Primitive, Primitive], Primitive]:
    """Return the ``operator`` function called ``name`` for two primitives.

    Args:
        name: Attribute of the :mod:`operator` module, such as ``"add"``.

    Returns:
        The binary arithmetic function.

    """
    handler: Callable[[Primitive, Primitive], Primitive] = getattr(
        operator,
        name,
    )
    return handler


def comparison_function(
    *,
    name: str,
) -> Callable[[Primitive, Primitive], bool]:
    """Return the ``operator`` comparison called ``name``.

    Args:
        name: Attribute of the :mod:`operator` module, such as ``"lt"``.

    Returns:
        The binary comparison function.

    """
    handler: Callable[[Primitive, Primitive], bool] = getattr(operator, name)
    return handler


def unary_function(*, name: str) -> Callable[[Primitive], Primitive]:
    """Return the ``operator`` unary function called ``name``.

    Args:
        name: Attribute of the :mod:`operator` module, such as ``"neg"``.

    Returns:
        The unary function.

    """
    handler: Callable[[Primitive], Primitive] = getattr(operator, name)
    return handler


@final
class Constants:
    """Group module-level constants.

    Attributes:
        arithmetic: Grouped module constant.
        orderings: Grouped module constant.
        power: Grouped module constant.
        left_shift: Grouped module constant.
        right_shift: Grouped module constant.
        contains: Grouped module constant.
        positive: Grouped module constant.
        negative: Grouped module constant.
        invert: Grouped module constant.
        conversion_repr: Grouped module constant.
        conversion_str: Grouped module constant.
        conversion_ascii: Grouped module constant.
        max_integer_bits: Grouped module constant.
        max_sequence_size: Grouped module constant.
        max_range_arguments: Grouped module constant.
        max_materialized_items: Grouped module constant.
        max_exponent: Grouped module constant.
        max_shift: Grouped module constant.
        known_exceptions: Grouped module constant.

    """

    arithmetic: Final[
        dict[type[AST], Callable[[Primitive, Primitive], Primitive]]
    ] = {
        Add: arithmetic_function(name="add"),
        Sub: arithmetic_function(name="sub"),
        Mult: arithmetic_function(name="mul"),
        Div: arithmetic_function(name="truediv"),
        FloorDiv: arithmetic_function(name="floordiv"),
        Mod: arithmetic_function(name="mod"),
        BitAnd: arithmetic_function(name="and_"),
        BitOr: arithmetic_function(name="or_"),
        BitXor: arithmetic_function(name="xor"),
    }
    orderings: Final[
        dict[type[AST], Callable[[Primitive, Primitive], bool]]
    ] = {
        Lt: comparison_function(name="lt"),
        LtE: comparison_function(name="le"),
        Gt: comparison_function(name="gt"),
        GtE: comparison_function(name="ge"),
    }
    power: Final[Callable[[Primitive, Primitive], Primitive]] = (
        arithmetic_function(name="pow")
    )
    left_shift: Final[Callable[[Primitive, Primitive], Primitive]] = (
        arithmetic_function(name="lshift")
    )
    right_shift: Final[Callable[[Primitive, Primitive], Primitive]] = (
        arithmetic_function(name="rshift")
    )
    contains: Final[Callable[[Primitive, Primitive], bool]] = (
        comparison_function(name="contains")
    )
    positive: Final[Callable[[Primitive], Primitive]] = unary_function(
        name="pos",
    )
    negative: Final[Callable[[Primitive], Primitive]] = unary_function(
        name="neg",
    )
    invert: Final[Callable[[Primitive], Primitive]] = unary_function(
        name="invert",
    )
    conversion_repr: Final[int] = ord("r")
    conversion_str: Final[int] = ord("s")
    conversion_ascii: Final[int] = ord("a")
    max_integer_bits: Final[int] = 4096
    max_sequence_size: Final[int] = 100000
    max_range_arguments: Final[int] = 3
    max_materialized_items: Final[int] = 256
    max_exponent: Final[int] = 256
    max_shift: Final[int] = 1024
    known_exceptions: Final[frozenset[str]] = frozenset(
        (
            "ArithmeticError",
            "ZeroDivisionError",
            "TypeError",
            "ValueError",
            "IndexError",
            "KeyError",
            "LookupError",
            "OSError",
            "RuntimeError",
            "AssertionError",
            "NameError",
            "AttributeError",
            "StopIteration",
            "Exception",
            "BaseException",
        ),
    )


def operation_for[T](*, table: dict[type[AST], T], op: AST) -> T | None:
    """Return the handler registered for ``op`` or one of its base classes.

    Args:
        table: Operator classes mapped to their handlers.
        op: Operator node being evaluated.

    Returns:
        The matching handler, or ``None`` when ``op`` is unsupported.

    """
    for kind, handler in table.items():
        if isinstance(op, kind):
            return handler
    return None


def _arithmetic_refusal(
    *,
    op: AST,
    a: Primitive,
    b: Primitive,
) -> UnknownValue | None:
    """Explain why exact arithmetic is not attempted, if it is not.

    Args:
        a: A supplied as Primitive for this operation.
        b: B supplied as Primitive for this operation.
        op: Op supplied as AST for this operation.

    Returns:
        UnknownValue | None produced by this operation.

    """
    kinds: tuple[
        type[int],
        type[float],
        type[complex],
        type[str],
        type[bytes],
        type[bool],
    ] = (int, float, complex, str, bytes, bool)
    if type(a) not in kinds or type(b) not in kinds:
        return UnknownValue(reason="unsupported arithmetic operand kind")
    if any(
        isinstance(number, int)
        and number.bit_length() > Constants.max_integer_bits
        for number in (a, b)
    ) or any(
        isinstance(text, (str, bytes))
        and len(text) > Constants.max_sequence_size
        for text in (a, b)
    ):
        return UnknownValue(
            reason="primitive exceeds abstract evaluation size limit",
        )
    if isinstance(op, Mult) and (
        (
            isinstance(a, (str, bytes))
            and isinstance(b, int)
            and (len(a) * max(0, b) > Constants.max_sequence_size)
        )
        or (
            isinstance(b, (str, bytes))
            and isinstance(a, int)
            and (len(b) * max(0, a) > Constants.max_sequence_size)
        )
    ):
        return UnknownValue(
            reason="sequence multiplication exceeds output budget",
        )
    return None


def _arithmetic_handler(
    *,
    op: AST,
    b: Primitive,
) -> Callable[[Primitive, Primitive], Primitive] | None:
    """Pick the operator function for ``op`` within the resource limits.

    Args:
        b: B supplied as Primitive for this operation.
        op: Op supplied as AST for this operation.

    Returns:
        Callable[[Primitive, Primitive], Primitive] | None produced by this
        operation.

    """
    handler: Callable[[Primitive, Primitive], Primitive] | None = (
        operation_for(table=Constants.arithmetic, op=op)
    )
    if handler is not None:
        return handler
    if (
        isinstance(op, Pow)
        and isinstance(b, (int, float))
        and (abs(b) <= Constants.max_exponent)
    ):
        return Constants.power
    if (
        isinstance(op, (LShift, RShift))
        and type(b) is int
        and (0 <= b <= Constants.max_shift)
    ):
        return (
            Constants.left_shift
            if isinstance(op, LShift)
            else Constants.right_shift
        )
    return None


def _arithmetic_failure(*, error: Exception) -> AbstractValue:
    """Model the abstract outcome of a failed built-in operation.

    Args:
        error: Error supplied as Exception for this operation.

    Returns:
        AbstractValue produced by this operation.

    """
    if isinstance(error, ZeroDivisionError):
        return ErrorValue(
            exception_type="ZeroDivisionError",
            reason="division by zero",
        )
    if isinstance(error, (TypeError, ValueError)):
        return ErrorValue(
            exception_type="TypeError",
            reason="incompatible built-in operands",
        )
    return UnknownValue(reason="operation may exceed static resource budget")


def _exception_name_match(
    *,
    raised: str,
    names: tuple[str, ...],
) -> bool | None:
    """Decide whether a raised built-in is caught by the listed names.

    Args:
        names: Names supplied as tuple[str, ...] for this operation.
        raised: Raised supplied as str for this operation.

    Returns:
        bool | None produced by this operation.

    """
    if raised in names or "BaseException" in names:
        return True
    if "Exception" in names:
        return (
            True
            if raised in Constants.known_exceptions - {"BaseException"}
            else None
        )
    if (raised == "ZeroDivisionError" and "ArithmeticError" in names) or (
        raised in ("IndexError", "KeyError") and "LookupError" in names
    ):
        return True
    if (
        raised in Constants.known_exceptions
        and set(names) <= Constants.known_exceptions
    ):
        return False
    return None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ActualArguments:
    """Abstract positional and named arguments of one call.

    Attributes:
        named: Named retained as dict[str, AbstractValue] by this instance.
        positional: Positional retained as tuple[AbstractValue, ...] by this
            instance.

    """

    positional: tuple[AbstractValue, ...]
    named: dict[str, AbstractValue]


@final
@dataclass(slots=True, kw_only=True)
class State:
    """Path-local mutable analysis state, not mutable program objects.

    Attributes:
        values: Abstract values currently bound to lexical symbols.
        heap: Immutable heap-object snapshots indexed by object identity.

    """

    values: dict[int, AbstractValue] = field(default_factory=dict)
    heap: dict[int, HeapObject] = field(default_factory=dict)

    def clone(self) -> State:
        """Isolate a potential control-flow path.

        Returns:
            State produced by this operation.

        """
        return State(values=dict(self.values), heap=dict(self.heap))

    def merge(self, *, other: State, limit: int) -> State:
        """Compute conservative union of two possible execution states.

        Args:
            other: Alternative execution state.
            limit: Maximum abstract-value alternatives.

        Returns:
            Conservatively merged symbolic environment and heap.

        """
        values: dict[int, AbstractValue] = {
            identity: join_values(
                left=self.values.get(identity, UnboundValue()),
                right=other.values.get(identity, UnboundValue()),
                limit=limit,
            )
            for identity in self.values.keys() | other.values.keys()
        }
        heap: dict[int, HeapObject] = {}
        for identity in self.heap.keys() | other.heap.keys():
            first: HeapObject | None = self.heap.get(identity)
            second: HeapObject | None = other.heap.get(identity)
            if first is None or second is None:
                kind: Literal["list", "dict", "set", "object"] = (
                    first.kind
                    if first is not None
                    else second.kind
                    if second is not None
                    else "object"
                )
                heap[identity] = HeapObject(
                    id=identity,
                    kind=kind,
                    unknown_content=True,
                    summary=True,
                    allocation_node_id=(
                        first.allocation_node_id
                        if first is not None
                        else second.allocation_node_id
                        if second is not None
                        else 0
                    ),
                )
                continue
            if first == second:
                heap[identity] = first
            else:
                heap[identity] = HeapObject(
                    id=identity,
                    kind=first.kind,
                    elements=tuple(
                        (
                            join_values(left=a, right=b, limit=limit)
                            for a, b in zip(
                                first.elements,
                                second.elements,
                                strict=False,
                            )
                        ),
                    )
                    if len(first.elements) == len(second.elements)
                    else (),
                    attributes=tuple(
                        (
                            (
                                key,
                                join_values(
                                    left=value,
                                    right=dict(second.attributes)[key],
                                    limit=limit,
                                ),
                            )
                            for key, value in first.attributes
                            if key in dict(second.attributes)
                        ),
                    ),
                    unknown_content=first.unknown_content
                    or second.unknown_content
                    or len(first.elements) != len(second.elements)
                    or (set(first.attributes) != set(second.attributes)),
                    summary=first.summary or second.summary,
                    allocation_node_id=first.allocation_node_id,
                )
        return State(values=values, heap=heap)


@final
@dataclass(slots=True, kw_only=True)
class Flow:
    """One possible normal, return, loop-control, or exceptional path.

    Attributes:
        state: Resulting environment and heap snapshot.
        control: How this path exits the last executed statement.
        value: Return value or raised object approximation.

    """

    state: State
    control: Control = "normal"
    value: AbstractValue = field(
        default_factory=lambda: LiteralValue(value=None),
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisBudgets:
    """Upper bounds protecting analysis from unbounded specialization.

    Attributes:
        context_sensitivity: Call-context keying policy: ``full`` keys on
            function, caller, and argument values; ``caller`` shares one
            context per call site; ``none`` shares one per function.
        max_recursion: Maximum nested source-defined function calls.
        max_contexts: Maximum distinct evaluated call contexts.
        max_union: Maximum alternatives in a joined abstract value.
        max_iterations: Maximum loop unrolling/fixed-point steps.
        max_paths: Maximum independently tracked control-flow paths.
        max_operations: Maximum total interpreter operations.
        max_symbolic_operations: Maximum composite expression operations.
        max_heap_objects: Maximum distinct abstract heap allocations.
        max_seconds: Wall-clock analysis deadline; 0 disables it.

    """

    context_sensitivity: Literal["full", "caller", "none"] = "full"
    max_recursion: int = 12
    max_contexts: int = 128
    max_union: int = 8
    max_iterations: int = 8
    max_paths: int = 16
    max_operations: int = 100000
    max_symbolic_operations: int = 20000
    max_heap_objects: int = 10000
    max_seconds: float = 0.0


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StepFrame:
    """Locals shared by the ``step_`` handlers of ``_step``.

    Attributes:
        context_id: Context id retained as int by this instance.
        identity: Identity retained as int by this instance.
        state: State retained as State by this instance.

    """

    context_id: int
    identity: int
    state: State


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MatchPatternFrame:
    """Locals shared by the ``match_pattern_`` handlers.

    Attributes:
        context_id: Context id retained as int by this instance.
        state: State retained as State by this instance.
        subject: Subject retained as AbstractValue by this instance.

    """

    context_id: int
    state: State
    subject: AbstractValue


@final
class AbstractInterpreter:
    """Safe bounded interpreter with context-specific function execution."""

    def __init__(
        self,
        *,
        root: AST,
        scopes: ScopeGraph,
        budgets: AnalysisBudgets | None = None,
    ) -> None:
        """Create a fresh analysis without executing Python source.

        Args:
            root: Mutable Python module tree.
            scopes: Lexically resolved symbol index.
            budgets: Explicit configurable analysis budgets.

        """
        self.root: AST = root
        self.scopes: ScopeGraph = scopes
        self.identities: IdentityIndex = scopes.identities
        self.budgets: AnalysisBudgets = budgets or AnalysisBudgets()
        self.heap: AbstractHeap = AbstractHeap(
            max_objects=self.budgets.max_heap_objects,
        )
        self.summaries: CallSummaryCache = CallSummaryCache()
        self.node_results: dict[int, InferenceResult] = {}
        self.at: dict[int, State] = {}
        self.call_results: dict[int, InferenceResult] = {}
        self.function_nodes: dict[
            int,
            FunctionDef | AsyncFunctionDef | Lambda,
        ] = {}
        self.function_defaults: dict[int, tuple[AbstractValue, ...]] = {}
        self.contexts: dict[
            tuple[int, int, tuple[AbstractValue, ...]],
            int,
        ] = {}
        self._next_context: int = 1
        self._active_calls: set[tuple[int, int, tuple[AbstractValue, ...]]] = (
            set()
        )
        self._operations: int = 0
        self._symbolic_operations: int = 0
        self._deadline: float | None = (
            monotonic() + self.budgets.max_seconds
            if self.budgets.max_seconds > 0
            else None
        )
        self._current_call_depth: int = 0
        self.exceptions: dict[int, set[str]] = {}
        self.heap_readers: dict[int, set[int]] = {}
        self.heap_writers: dict[int, set[int]] = {}
        self._module_outputs: list[tuple[Flow, ...]] = []
        self._module_inputs: list[tuple[Flow, ...]] = []
        self._module_statement_ids: tuple[int, ...] = tuple(
            self.identities.node_id(node=item)
            for item in getattr(root, "body", [])
        )
        self.incremental_reexecuted: tuple[int, ...] = ()
        self.incremental_reused: tuple[int, ...] = ()
        body: list[stmt] = getattr(root, "body", [])
        results: list[Flow] = self._execute_suite(
            body=body,
            paths=[Flow(state=State())],
            context_id=0,
        )
        final: State | None = None
        for path in results:
            final = (
                path.state
                if final is None
                else final.merge(
                    other=path.state,
                    limit=self.budgets.max_union,
                )
            )
        self.final_state: State = final or State()
        self.heap.objects.update(self.final_state.heap)

    @classmethod
    def eval_yieldfrom(
        cls,
        node: Yield | YieldFrom | GeneratorExp | ListComp,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_yield`` for YieldFrom.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_yield`` for
                YieldFrom.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return cls.eval_yield(node, state, context_id, identity)

    @classmethod
    def eval_generatorexp(
        cls,
        node: Yield | YieldFrom | GeneratorExp | ListComp,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_yield`` for GeneratorExp.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_yield`` for
                GeneratorExp.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return cls.eval_yield(node, state, context_id, identity)

    @classmethod
    def eval_listcomp(
        cls,
        node: Yield | YieldFrom | GeneratorExp | ListComp,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_yield`` for ListComp.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_yield`` for ListComp.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return cls.eval_yield(node, state, context_id, identity)

    @classmethod
    def builtin_int(
        cls,
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Model ``int`` of a known primitive.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        return cls._convert(name="int", args=args)

    @classmethod
    def builtin_str(
        cls,
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Model ``str`` of a known primitive.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        return cls._convert(name="str", args=args)

    @classmethod
    def builtin_bool(
        cls,
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Model ``bool`` of a known primitive.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        return cls._convert(name="bool", args=args)

    @classmethod
    def builtin_sum(
        cls,
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Fold a known sequence with exact addition.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        if len(args) != 1 or not isinstance(args[0], SequenceValue):
            return None
        result: AbstractValue = LiteralValue(value=0)
        for item in args[0].elements:
            result = cls._binary(op=Add(), left=result, right=item)
        return result

    @classmethod
    def step_global(
        cls,
        node: Pass | Global | Nonlocal,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_pass`` for Global.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_pass`` for Global.

        Returns:
            list[Flow] produced by this operation.

        """
        return cls.step_pass(node, frame)

    @classmethod
    def step_nonlocal(
        cls,
        node: Pass | Global | Nonlocal,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_pass`` for Nonlocal.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_pass`` for Nonlocal.

        Returns:
            list[Flow] produced by this operation.

        """
        return cls.step_pass(node, frame)

    @staticmethod
    def eval_constant(
        node: Constant,
        _state: State,
        _context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Constant for ``_eval``.

        Args:
            _context_id: Context id supplied as int for this operation.
            _identity: Identity supplied as int for this operation.
            _state: State supplied as State for this operation.
            node: The node examined while infer Constant for ``_eval``.

        Returns:
            AbstractValue produced by this operation.

        """
        UnknownValue(reason=f"unsupported {type(node).__name__}")
        constant: Primitive = node.value
        return LiteralValue(value=constant)

    @staticmethod
    def eval_yield(
        node: Yield | YieldFrom | GeneratorExp | ListComp,
        _state: State,
        _context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Yield (and kin) for ``_eval``.

        Args:
            _context_id: Context id supplied as int for this operation.
            _identity: Identity supplied as int for this operation.
            _state: State supplied as State for this operation.
            node: The node examined while infer Yield (and kin) for ``_eval``.

        Returns:
            AbstractValue produced by this operation.

        """
        UnknownValue(reason=f"unsupported {type(node).__name__}")
        return UnknownValue(reason="generator or comprehension effects")

    @staticmethod
    def builtin_len(
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Model ``len`` of a known sequence or string.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        if len(args) != 1:
            return None
        arg: AbstractValue = args[0]
        if isinstance(arg, SequenceValue):
            return LiteralValue(value=len(arg.elements))
        if isinstance(arg, LiteralValue) and isinstance(
            arg.value,
            (str, bytes),
        ):
            return LiteralValue(value=len(arg.value))
        return None

    @staticmethod
    def builtin_abs(
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Model ``abs`` of a known number.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        if (
            len(args) == 1
            and isinstance((first := args[0]), LiteralValue)
            and isinstance(first.value, (int, float, complex))
            and (not isinstance(first.value, bool))
        ):
            return LiteralValue(value=abs(first.value))
        return None

    @staticmethod
    def builtin_range(
        args: tuple[AbstractValue, ...],
        /,
    ) -> AbstractValue | None:
        """Materialize a small ``range`` of known integers.

        Args:
            args: Collection of args supplied for this operation.

        Returns:
            AbstractValue | None produced by this operation.

        """
        if not (
            1 <= len(args) <= Constants.max_range_arguments
            and all(
                isinstance(arg, LiteralValue) and type(arg.value) is int
                for arg in args
            )
        ):
            return None
        values: tuple[int, ...] = tuple(
            arg.value
            for arg in args
            if isinstance(arg, LiteralValue) and type(arg.value) is int
        )
        try:
            sequence: range = range(*values)
            if len(sequence) <= Constants.max_materialized_items:
                return SequenceValue(
                    elements=tuple(
                        LiteralValue(value=item) for item in sequence
                    ),
                )
        except (ValueError, OverflowError):
            return None
        return None

    @staticmethod
    def step_break(_node: Break, frame: StepFrame, /) -> list[Flow]:
        """Handle Break in ``_step``.

        Args:
            _node: Node supplied as Break for this operation.
            frame: Frame supplied as StepFrame for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        return [Flow(state=frame.state, control="break")]

    @staticmethod
    def step_continue(_node: Continue, frame: StepFrame, /) -> list[Flow]:
        """Handle Continue in ``_step``.

        Args:
            _node: Node supplied as Continue for this operation.
            frame: Frame supplied as StepFrame for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        return [Flow(state=frame.state, control="continue")]

    @staticmethod
    def step_pass(
        _node: Pass | Global | Nonlocal,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle Pass or Global or Nonlocal in ``_step``.

        Args:
            _node: Node supplied as Pass | Global | Nonlocal for this
                operation.
            frame: Frame supplied as StepFrame for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        return [Flow(state=frame.state)]

    @staticmethod
    def match_pattern_matchsingleton(
        pattern: MatchSingleton,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchSingleton in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchSingleton for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if isinstance(frame.subject, LiteralValue):
            return frame.subject.value is pattern.value
        return None

    @staticmethod
    def match_pattern_matchclass(
        _pattern: MatchClass,
        _frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchClass in ``_match_pattern``.

        Args:
            _frame: Frame supplied as MatchPatternFrame for this operation.
            _pattern: Pattern supplied as MatchClass for this operation.

        Returns:
            bool | None produced by this operation.

        """
        return None

    def eval_name(
        self,
        node: Name,
        state: State,
        _context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Infer Name for ``_eval``.

        Args:
            _context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while infer Name for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        occurrence: Occurrence | None = self.scopes.occurrences.get(identity)
        symbol_id: int | None = occurrence.symbol_id if occurrence else None
        if symbol_id is None:
            result = (
                BuiltinValue(name=node.id)
                if node.id
                in {
                    "len",
                    "abs",
                    "sum",
                    "min",
                    "max",
                    "int",
                    "str",
                    "bool",
                    "range",
                }
                else UnknownValue(
                    reason=(f"unresolved external name {node.id}"),
                )
            )
        else:
            result = state.values.get(symbol_id, UnboundValue())
        return result

    def eval_list(
        self,
        node: List | Set,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Infer List or Set for ``_eval``.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while infer List or Set for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        elements: tuple[AbstractValue, ...] = tuple(
            self._eval(node=item, state=state, context_id=context_id)
            for item in node.elts
        )
        result = self.heap.allocate(
            node_id=identity,
            context_id=context_id,
            kind="list" if isinstance(node, List) else "set",
            elements=elements,
        )
        for allocated in result.object_ids:
            state.heap[allocated] = self.heap.objects[allocated]
        return result

    def eval_set(
        self,
        node: List | Set,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_list`` for Set.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_list`` for Set.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return self.eval_list(node, state, context_id, identity)

    def eval_tuple(
        self,
        node: Tuple,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Tuple for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer Tuple for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        UnknownValue(reason=f"unsupported {type(node).__name__}")
        return SequenceValue(
            elements=tuple(
                self._eval(node=item, state=state, context_id=context_id)
                for item in node.elts
            ),
        )

    def eval_dict(
        self,
        node: Dict,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Infer Dict for ``_eval``.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while infer Dict for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        entries: tuple[tuple[AbstractValue, AbstractValue], ...] = tuple(
            (
                (
                    self._eval(node=key, state=state, context_id=context_id)
                    if key is not None
                    else UnknownValue(reason="dictionary expansion"),
                    self._eval(node=value, state=state, context_id=context_id),
                )
                for key, value in zip(node.keys, node.values, strict=True)
            ),
        )
        result = self.heap.allocate(
            node_id=identity,
            context_id=context_id,
            kind="dict",
            attributes=entries,
        )
        for allocated in result.object_ids:
            state.heap[allocated] = self.heap.objects[allocated]
        return result

    def eval_binop(
        self,
        node: BinOp | UnaryOp,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer BinOp or UnaryOp for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer BinOp or UnaryOp for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        if isinstance(node, BinOp):
            left: AbstractValue = self._eval(
                node=node.left,
                state=state,
                context_id=context_id,
            )
            right: AbstractValue = self._eval(
                node=node.right,
                state=state,
                context_id=context_id,
            )
            result = (
                left
                if isinstance(left, ErrorValue)
                else right
                if isinstance(right, ErrorValue)
                else self._binary(op=node.op, left=left, right=right)
                if self._symbolic()
                else UnknownValue(
                    reason="symbolic operation budget exceeded",
                )
            )
        else:
            operand: AbstractValue = self._eval(
                node=node.operand,
                state=state,
                context_id=context_id,
            )
            result = (
                self._unary(op=node.op, value=operand)
                if self._symbolic()
                else UnknownValue(
                    reason="symbolic operation budget exceeded",
                )
            )
        return result

    def eval_unaryop(
        self,
        node: BinOp | UnaryOp,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_binop`` for UnaryOp.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_binop`` for UnaryOp.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return self.eval_binop(node, state, context_id, identity)

    def eval_boolop(
        self,
        node: BoolOp,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer BoolOp for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer BoolOp for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        result = self._eval(
            node=node.values[0],
            state=state,
            context_id=context_id,
        )
        for item in node.values[1:]:
            truth: bool | None = truth_value(value=result)
            if truth is not None and (
                (isinstance(node.op, And) and (not truth))
                or (isinstance(node.op, Or) and truth)
            ):
                break
            following: AbstractValue = self._eval(
                node=item,
                state=state,
                context_id=context_id,
            )
            if truth is None:
                result = (
                    join_values(
                        left=result,
                        right=following,
                        limit=self.budgets.max_union,
                    )
                    if self._symbolic()
                    else UnknownValue(
                        reason="symbolic operation budget exceeded",
                    )
                )
            else:
                result = following
        return result

    def eval_ifexp(
        self,
        node: IfExp,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer IfExp for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer IfExp for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        condition: AbstractValue = self._eval(
            node=node.test,
            state=state,
            context_id=context_id,
        )
        known: bool | None = truth_value(value=condition)
        if known is not None:
            result = self._eval(
                node=node.body if known else node.orelse,
                state=state,
                context_id=context_id,
            )
        else:
            first: State = state.clone()
            second: State = state.clone()
            first_value: AbstractValue = self._eval(
                node=node.body,
                state=first,
                context_id=context_id,
            )
            second_value: AbstractValue = self._eval(
                node=node.orelse,
                state=second,
                context_id=context_id,
            )
            joined: State = first.merge(
                other=second,
                limit=self.budgets.max_union,
            )
            state.values = joined.values
            state.heap = joined.heap
            result = join_values(
                left=first_value,
                right=second_value,
                limit=self.budgets.max_union,
            )
        return result

    def eval_compare(
        self,
        node: Compare,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Compare for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer Compare for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        UnknownValue(reason=f"unsupported {type(node).__name__}")
        previous: AbstractValue = self._eval(
            node=node.left,
            state=state,
            context_id=context_id,
        )
        comparisons: list[bool | None] = []
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            following: AbstractValue = self._eval(
                node=comparator,
                state=state,
                context_id=context_id,
            )
            comparisons.append(
                self._compare(op=op, left=previous, right=following)
                if self._symbolic()
                else None,
            )
            previous = following
        return (
            LiteralValue(value=False)
            if False in comparisons
            else LiteralValue(value=True)
            if all(flag is True for flag in comparisons)
            else UnknownValue(reason="comparison operands not precisely known")
        )

    def eval_subscript(
        self,
        node: Subscript,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Subscript for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer Subscript for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        base: AbstractValue = self._eval(
            node=node.value,
            state=state,
            context_id=context_id,
        )
        key: AbstractValue = self._eval(
            node=node.slice,
            state=state,
            context_id=context_id,
        )
        if isinstance(base, ObjectReference):
            self._touch_heap(node=node, reference=base, write=False)
            result = self.heap.read_index(
                reference=base,
                index=key,
                objects=state.heap,
            )
        elif (
            isinstance(base, SequenceValue)
            and isinstance(key, LiteralValue)
            and (type(key.value) is int)
        ):
            index: int = key.value
            if -len(base.elements) <= index < len(base.elements):
                result = base.elements[index]
            else:
                result = ErrorValue(
                    exception_type="IndexError",
                    reason="known sequence index out of range",
                )
        elif (
            isinstance(base, LiteralValue)
            and isinstance(key, LiteralValue)
            and (
                isinstance(base.value, (str, bytes)) and type(key.value) is int
            )
        ):
            try:
                result = LiteralValue(value=base.value[key.value])
            except IndexError:
                result = ErrorValue(
                    exception_type="IndexError",
                    reason="known string index out of range",
                )
        return result

    def eval_attribute(
        self,
        node: Attribute,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Attribute for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer Attribute for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        base: AbstractValue = self._eval(
            node=node.value,
            state=state,
            context_id=context_id,
        )
        if isinstance(base, ObjectReference):
            if node.attr in {
                "append",
                "extend",
                "pop",
                "clear",
                "insert",
                "update",
            }:
                result = BoundMethodValue(receiver=base, name=node.attr)
            elif len(base.object_ids) == 1:
                self._touch_heap(node=node, reference=base, write=False)
                result = self.heap.read_index(
                    reference=base,
                    index=LiteralValue(value=node.attr),
                    objects=state.heap,
                )
        return result

    def eval_call(
        self,
        node: Call,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Infer Call for ``_eval``.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while infer Call for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        result = self._call(node=node, state=state, context_id=context_id)
        self.call_results[identity] = InferenceResult(
            value=result,
            status=proof_status(value=result),
            trace=((f"Call at node {identity} returned {result!r}"),),
        )
        return result

    def eval_namedexpr(
        self,
        node: NamedExpr,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer NamedExpr for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer NamedExpr for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        result = self._eval(
            node=node.value,
            state=state,
            context_id=context_id,
        )
        self._assign(
            target=node.target,
            value=result,
            state=state,
            context_id=context_id,
        )
        return result

    def eval_joinedstr(
        self,
        node: JoinedStr | FormattedValue,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer JoinedStr or FormattedValue for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer JoinedStr or FormattedValue for
                ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        if isinstance(node, JoinedStr):
            fragments: list[str] = []
            for part in node.values:
                fragment: AbstractValue = self._eval(
                    node=part,
                    state=state,
                    context_id=context_id,
                )
                if not isinstance(fragment, LiteralValue) or not isinstance(
                    fragment.value,
                    str,
                ):
                    break
                fragments.append(fragment.value)
            else:
                result = LiteralValue(value="".join(fragments))
        else:
            inner: AbstractValue = self._eval(
                node=node.value,
                state=state,
                context_id=context_id,
            )
            specification: AbstractValue = (
                self._eval(
                    node=node.format_spec,
                    state=state,
                    context_id=context_id,
                )
                if node.format_spec is not None
                else LiteralValue(value="")
            )
            if (
                isinstance(inner, LiteralValue)
                and isinstance(specification, LiteralValue)
                and isinstance(specification.value, str)
            ):
                try:
                    converted: Primitive = (
                        repr(inner.value)
                        if node.conversion == Constants.conversion_repr
                        else str(object=inner.value)
                        if node.conversion == Constants.conversion_str
                        else ascii(inner.value)
                        if node.conversion == Constants.conversion_ascii
                        else inner.value
                    )
                    result = LiteralValue(
                        value=format(converted, specification.value),
                    )
                except (ValueError, TypeError, OverflowError):
                    result = UnknownValue(
                        reason="invalid or unsupported f-string format",
                    )
        return result

    def eval_formattedvalue(
        self,
        node: JoinedStr | FormattedValue,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_joinedstr`` for FormattedValue.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_joinedstr`` for
                FormattedValue.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return self.eval_joinedstr(node, state, context_id, identity)

    def eval_lambda(
        self,
        node: Lambda | FunctionDef | AsyncFunctionDef,
        _state: State,
        _context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Infer Lambda (and kin) for ``_eval``.

        Args:
            _context_id: Context id supplied as int for this operation.
            _state: State supplied as State for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while infer Lambda (and kin) for ``_eval``.

        Returns:
            AbstractValue produced by this operation.

        """
        UnknownValue(reason=f"unsupported {type(node).__name__}")
        self.function_nodes[identity] = node
        return FunctionValue(node_id=identity)

    def eval_functiondef(
        self,
        node: Lambda | FunctionDef | AsyncFunctionDef,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_lambda`` for FunctionDef.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_lambda`` for
                FunctionDef.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return self.eval_lambda(node, state, context_id, identity)

    def eval_asyncfunctiondef(
        self,
        node: Lambda | FunctionDef | AsyncFunctionDef,
        state: State,
        context_id: int,
        identity: int,
        /,
    ) -> AbstractValue:
        """Alias of ``eval_lambda`` for AsyncFunctionDef.

        Args:
            context_id: Context id supplied as int for this operation.
            identity: Identity supplied as int for this operation.
            node: The node examined while alias of ``eval_lambda`` for
                AsyncFunctionDef.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        return self.eval_lambda(node, state, context_id, identity)

    def eval_await(
        self,
        node: Await,
        state: State,
        context_id: int,
        _identity: int,
        /,
    ) -> AbstractValue:
        """Infer Await for ``_eval``.

        Args:
            _identity: Identity supplied as int for this operation.
            context_id: Context id supplied as int for this operation.
            node: The node examined while infer Await for ``_eval``.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        deferred: AbstractValue = self._eval(
            node=node.value,
            state=state,
            context_id=context_id,
        )
        if isinstance(deferred, CoroutineValue):
            result = self.function_call(
                function_id=deferred.function_id,
                arguments=ActualArguments(
                    positional=deferred.arguments,
                    named=dict(deferred.keywords),
                ),
                state=state,
                caller_id=deferred.caller_id,
                awaited=True,
            )
        else:
            result = UnknownValue(
                reason="unknown awaitable may suspend and mutate state",
            )
            for value in state.values.values():
                if isinstance(value, ObjectReference):
                    self._touch_heap(node=node, reference=value, write=True)
                    self.heap.havoc(reference=value, objects=state.heap)
        return result

    def function_call(
        self,
        *,
        function_id: int,
        arguments: ActualArguments,
        state: State,
        caller_id: int,
        awaited: bool = False,
    ) -> AbstractValue:
        """Analyze an internal call in isolation and propagate effects.

        Args:
            arguments: Collection of arguments supplied for this operation.
            awaited: Awaited supplied as bool for this operation.
            caller_id: Caller id supplied as int for this operation.
            function_id: Function id supplied as int for this operation.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        args: tuple[AbstractValue, ...] = arguments.positional
        function: FunctionDef | AsyncFunctionDef | Lambda | None = (
            self.function_nodes.get(function_id)
        )
        if function is None or (
            isinstance(function, AsyncFunctionDef) and (not awaited)
        ):
            return UnknownValue(
                reason="unknown function or unawaited coroutine",
            )
        key: tuple[int, int, tuple[AbstractValue, ...]] = (
            function_id,
            caller_id,
            args,
        )
        if self.budgets.context_sensitivity == "caller":
            key = (function_id, caller_id, ())
        elif self.budgets.context_sensitivity == "none":
            key = (function_id, 0, ())
        call_context: int | UnknownValue = self._call_context(key=key)
        if isinstance(call_context, UnknownValue):
            return call_context
        existing: FunctionSummary | None = self.summaries.get(
            function_id=function_id,
            caller_id=caller_id,
            args=args,
            values=state.values,
            heap=state.heap,
        )
        if existing is not None:
            state.values.update(existing.value_updates)
            state.heap.update(
                {entry.id: entry for entry in existing.heap_updates},
            )
            return existing.result
        input_state: State = state.clone()
        if (
            len(args) > len((*function.args.posonlyargs, *function.args.args))
            and function.args.vararg is None
        ):
            return UnknownValue(reason="too many positional arguments")
        environment: State = state.clone()
        self._bind_parameters(
            function=function,
            function_id=function_id,
            arguments=arguments,
            caller_id=caller_id,
            environment=environment,
        )
        paths: list[Flow] = self._execute_call(
            function=function,
            environment=environment,
            call_context=call_context,
            key=key,
        )
        result, merged_state = self._join_paths(paths=paths)
        function_scope_id: int = self.identities.node_id(node=function)
        if merged_state is not None:
            self._publish_effects(
                state=state,
                merged_state=merged_state,
                input_state=input_state,
                function_scope_id=function_scope_id,
            )
        self.summaries.add(
            caller_id=caller_id,
            args=args,
            values=input_state.values,
            heap=input_state.heap,
            summary=FunctionSummary(
                function_id=function_id,
                context_id=call_context,
                result=result,
                value_updates=tuple(
                    sorted(
                        (
                            (symbol_id, value)
                            for symbol_id, value in state.values.items()
                            if input_state.values.get(symbol_id) != value
                        ),
                    ),
                ),
                heap_updates=tuple(
                    (
                        entry
                        for identity, entry in sorted(state.heap.items())
                        if input_state.heap.get(identity) != entry
                    ),
                ),
                dependencies=(function_scope_id,),
            ),
        )
        return result

    def recompute_module(
        self,
        *,
        dirty: frozenset[int],
        scopes: ScopeGraph,
    ) -> tuple[int, ...] | None:
        """Reexecute changed module statements until abstract states stabilize.

        Only existing top-level statement identities are supported here.  The
        caller must request a full rebuild for altered lexical scopes, changed
        function/class bodies, or any changed statement ordering.

        Returns:
            Statement IDs actually reexecuted, or None if a full rebuild is
            required for a structural change.



        Args:
            dirty: Dirty supplied as frozenset[int] for this operation.
            scopes: Collection of scopes supplied for this operation.

        """
        body: list[stmt] = getattr(self.root, "body", [])
        identities: tuple[int, ...] = tuple(
            self.identities.node_id(node=item) for item in body
        )
        if identities != self._module_statement_ids or len(
            self._module_outputs,
        ) != len(body):
            return None
        self.scopes = scopes
        self._operations = 0
        self.summaries = CallSummaryCache()
        self._invalidate_definition_results(body=body)
        pending: deque[int] = deque(iterable=sorted(dirty))
        queued: set[int] = set(pending)
        visited: list[int] = []
        reused: list[int] = []
        while pending:
            index: int = pending.popleft()
            queued.remove(index)
            if not 0 <= index < len(body):
                return None
            statement: stmt = body[index]
            inputs: list[Flow] = (
                [Flow(state=State())]
                if index == 0
                else list(
                    self._clone_paths(
                        paths=list(self._module_outputs[index - 1]),
                    ),
                )
            )
            changed_symbols: set[int] | None = self._reusable_changes(
                statement=statement,
                index=index,
                dirty=dirty,
                inputs=inputs,
            )
            if changed_symbols is not None:
                snapshot: tuple[Flow, ...] = self._reuse_output(
                    index=index,
                    inputs=inputs,
                    changed_symbols=changed_symbols,
                )
                reused.append(identities[index])
            else:
                snapshot = self._reexecute_statement(
                    statement=statement,
                    inputs=inputs,
                )
                visited.append(identities[index])
            self._module_inputs[index] = self._clone_paths(paths=inputs)
            changed: bool = snapshot != self._module_outputs[index]
            self._module_outputs[index] = snapshot
            if changed and index + 1 < len(body) and (index + 1 not in queued):
                pending.append(index + 1)
                queued.add(index + 1)
        self.final_state = self._final_module_state()
        self.heap.objects.update(self.final_state.heap)
        self.incremental_reexecuted = tuple(visited)
        self.incremental_reused = tuple(reused)
        return self.incremental_reexecuted

    def step_functiondef(
        self,
        node: FunctionDef | AsyncFunctionDef,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle FunctionDef or AsyncFunctionDef in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle FunctionDef or
                AsyncFunctionDef in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        self.function_nodes[frame.identity] = node
        self.function_defaults[frame.identity] = tuple(
            self._eval(
                node=default,
                state=frame.state,
                context_id=frame.context_id,
            )
            for default in node.args.defaults
        )
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            frame.identity,
        )
        if occurrence is not None and occurrence.symbol_id is not None:
            frame.state.values[occurrence.symbol_id] = FunctionValue(
                node_id=frame.identity,
            )
        return [Flow(state=frame.state)]

    def step_asyncfunctiondef(
        self,
        node: FunctionDef | AsyncFunctionDef,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_functiondef`` for AsyncFunctionDef.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_functiondef`` for
                AsyncFunctionDef.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_functiondef(node, frame)

    def step_assign(
        self,
        node: Assign | AnnAssign,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle Assign or AnnAssign in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Assign or AnnAssign in
                ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        expression: AST | None = node.value
        if expression is not None:
            value: AbstractValue = self._eval(
                node=expression,
                state=frame.state,
                context_id=frame.context_id,
            )
            if isinstance(value, ErrorValue):
                return [Flow(state=frame.state, control="raise", value=value)]
            targets: tuple[AST, ...] = (
                tuple(node.targets)
                if isinstance(node, Assign)
                else (node.target,)
            )
            for target in targets:
                self._assign(
                    target=target,
                    value=value,
                    state=frame.state,
                    context_id=frame.context_id,
                )
        return [Flow(state=frame.state)]

    def step_annassign(
        self,
        node: Assign | AnnAssign,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_assign`` for AnnAssign.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_assign`` for
                AnnAssign.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_assign(node, frame)

    def step_augassign(
        self,
        node: AugAssign,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle AugAssign in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle AugAssign in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        previous: AbstractValue = self._eval(
            node=node.target,
            state=frame.state,
            context_id=frame.context_id,
        )
        increment: AbstractValue = self._eval(
            node=node.value,
            state=frame.state,
            context_id=frame.context_id,
        )
        value: AbstractValue = self._binary(
            op=node.op,
            left=previous,
            right=increment,
        )
        if isinstance(value, ErrorValue):
            return [Flow(state=frame.state, control="raise", value=value)]
        self._assign(
            target=node.target,
            value=value,
            state=frame.state,
            context_id=frame.context_id,
        )
        return [Flow(state=frame.state)]

    def step_expr(self, node: Expr, frame: StepFrame, /) -> list[Flow]:
        """Handle Expr in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Expr in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        value: AbstractValue = self._eval(
            node=node.value,
            state=frame.state,
            context_id=frame.context_id,
        )
        return [
            Flow(
                state=frame.state,
                control="raise" if isinstance(value, ErrorValue) else "normal",
                value=value,
            ),
        ]

    def step_return(self, node: Return, frame: StepFrame, /) -> list[Flow]:
        """Handle Return in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Return in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        value: AbstractValue = self._eval(
            node=node.value,
            state=frame.state,
            context_id=frame.context_id,
        )
        return [
            Flow(
                state=frame.state,
                control="raise" if isinstance(value, ErrorValue) else "return",
                value=value,
            ),
        ]

    def step_raise(self, node: Raise, frame: StepFrame, /) -> list[Flow]:
        """Handle Raise in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Raise in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        if isinstance(node.exc, Call) and isinstance(node.exc.func, Name):
            name: str = node.exc.func.id
            for argument in node.exc.args:
                self._eval(
                    node=argument,
                    state=frame.state,
                    context_id=frame.context_id,
                )
            return [
                Flow(
                    state=frame.state,
                    control="raise",
                    value=ErrorValue(
                        exception_type=name,
                        reason="explicit exception constructor",
                    ),
                ),
            ]
        if isinstance(node.exc, Name):
            return [
                Flow(
                    state=frame.state,
                    control="raise",
                    value=ErrorValue(
                        exception_type=node.exc.id,
                        reason="explicit raised exception",
                    ),
                ),
            ]
        self._eval(
            node=node.exc,
            state=frame.state,
            context_id=frame.context_id,
        )
        return [
            Flow(
                state=frame.state,
                control="raise",
                value=UnknownValue(reason="raised exception"),
            ),
        ]

    def step_if(self, node: If, frame: StepFrame, /) -> list[Flow]:
        """Handle If in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle If in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        condition: AbstractValue = self._eval(
            node=node.test,
            state=frame.state,
            context_id=frame.context_id,
        )
        truth: bool | None = truth_value(value=condition)
        paths: list[Flow] = []
        if truth is not False:
            paths.extend(
                self._execute_suite(
                    body=node.body,
                    paths=[Flow(state=frame.state.clone())],
                    context_id=frame.context_id,
                ),
            )
        if truth is not True:
            paths.extend(
                self._execute_suite(
                    body=node.orelse,
                    paths=[Flow(state=frame.state.clone())],
                    context_id=frame.context_id,
                ),
            )
        return paths

    def step_while(
        self,
        node: While | For | AsyncFor,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle While or For or AsyncFor in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle While or For or AsyncFor in
                ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        return self._loop(
            node=node,
            state=frame.state,
            context_id=frame.context_id,
        )

    def step_for(
        self,
        node: While | For | AsyncFor,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_while`` for For.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_while`` for For.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_while(node, frame)

    def step_asyncfor(
        self,
        node: While | For | AsyncFor,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_while`` for AsyncFor.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_while`` for AsyncFor.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_while(node, frame)

    def step_try(self, node: Try | TryStar, frame: StepFrame, /) -> list[Flow]:
        """Handle Try or TryStar in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Try or TryStar in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        return self._try(
            node=node,
            state=frame.state,
            context_id=frame.context_id,
        )

    def step_trystar(
        self,
        node: Try | TryStar,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_try`` for TryStar.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_try`` for TryStar.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_try(node, frame)

    def step_with(
        self,
        node: With | AsyncWith,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle With or AsyncWith in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle With or AsyncWith in
                ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        for item in node.items:
            receiver: AbstractValue = self._eval(
                node=item.context_expr,
                state=frame.state,
                context_id=frame.context_id,
            )
            if item.optional_vars is not None:
                self._assign(
                    target=item.optional_vars,
                    value=UnknownValue(reason="context manager entry"),
                    state=frame.state,
                    context_id=frame.context_id,
                )
            if isinstance(receiver, ObjectReference):
                self._touch_heap(
                    node=item.context_expr,
                    reference=receiver,
                    write=True,
                )
                self.heap.havoc(reference=receiver, objects=frame.state.heap)
        result: list[Flow] = self._execute_suite(
            body=node.body,
            paths=[Flow(state=frame.state)],
            context_id=frame.context_id,
        )
        return [*result, Flow(state=frame.state.clone(), control="raise")]

    def step_asyncwith(
        self,
        node: With | AsyncWith,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_with`` for AsyncWith.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_with`` for AsyncWith.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_with(node, frame)

    def step_delete(self, node: Delete, frame: StepFrame, /) -> list[Flow]:
        """Handle Delete in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Delete in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        for target in node.targets:
            if isinstance(target, Name):
                occurrence: Occurrence | None = self.scopes.occurrences.get(
                    self.identities.node_id(node=target),
                )
                if occurrence is not None and occurrence.symbol_id is not None:
                    frame.state.values[occurrence.symbol_id] = UnboundValue()
            else:
                self._assign(
                    target=target,
                    value=UnknownValue(reason="deleted location"),
                    state=frame.state,
                    context_id=frame.context_id,
                )
        return [Flow(state=frame.state)]

    def step_import(
        self,
        node: Import | ImportFrom,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle Import or ImportFrom in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Import or ImportFrom in
                ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        for part in node.names:
            occurrence: Occurrence | None = self.scopes.occurrences.get(
                self.identities.node_id(node=part),
            )
            if occurrence is not None and occurrence.symbol_id is not None:
                frame.state.values[occurrence.symbol_id] = UnknownValue(
                    reason="external import",
                )
        return [Flow(state=frame.state)]

    def step_importfrom(
        self,
        node: Import | ImportFrom,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Alias of ``step_import`` for ImportFrom.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while alias of ``step_import`` for
                ImportFrom.

        Returns:
            list[Flow] produced by this operation.

        """
        return self.step_import(node, frame)

    def step_assert(self, node: Assert, frame: StepFrame, /) -> list[Flow]:
        """Handle Assert in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Assert in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        condition: AbstractValue = self._eval(
            node=node.test,
            state=frame.state,
            context_id=frame.context_id,
        )
        if truth_value(value=condition) is False:
            return [Flow(state=frame.state, control="raise")]
        if truth_value(value=condition) is None:
            return [
                Flow(state=frame.state),
                Flow(state=frame.state.clone(), control="raise"),
            ]
        return [Flow(state=frame.state)]

    def step_match(self, node: Match, frame: StepFrame, /) -> list[Flow]:
        """Handle Match in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle Match in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        subject: AbstractValue = self._eval(
            node=node.subject,
            state=frame.state,
            context_id=frame.context_id,
        )
        remaining: list[Flow] = [Flow(state=frame.state.clone())]
        matched: list[Flow] = []
        for case in node.cases:
            next_remaining: list[Flow] = []
            for path in remaining:
                branch_state: State = path.state.clone()
                decision: bool | None = self._match_pattern(
                    pattern=case.pattern,
                    subject=subject,
                    state=branch_state,
                    context_id=frame.context_id,
                )
                if decision is not False:
                    guard: bool | None = (
                        truth_value(
                            value=self._eval(
                                node=case.guard,
                                state=branch_state,
                                context_id=frame.context_id,
                            ),
                        )
                        if case.guard is not None
                        else True
                    )
                    if guard is not False:
                        matched.extend(
                            self._execute_suite(
                                body=case.body,
                                paths=[Flow(state=branch_state)],
                                context_id=frame.context_id,
                            ),
                        )
                    if guard is not True:
                        next_remaining.append(path)
                if decision is not True:
                    next_remaining.append(path)
            remaining = self._limit_paths(paths=next_remaining)
        return self._limit_paths(paths=[*matched, *remaining])

    def step_typealias(
        self,
        node: TypeAlias,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle TypeAlias in ``_step``.

        Args:
            frame: Frame supplied as StepFrame for this operation.
            node: The node examined while handle TypeAlias in ``_step``.

        Returns:
            list[Flow] produced by this operation.

        """
        self._assign(
            target=node.name,
            value=UnknownValue(reason="lazy type alias expression"),
            state=frame.state,
            context_id=frame.context_id,
        )
        return [Flow(state=frame.state)]

    def step_classdef(
        self,
        _node: ClassDef,
        frame: StepFrame,
        /,
    ) -> list[Flow]:
        """Handle ClassDef in ``_step``.

        Args:
            _node: Node supplied as ClassDef for this operation.
            frame: Frame supplied as StepFrame for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            frame.identity,
        )
        if occurrence is not None and occurrence.symbol_id is not None:
            frame.state.values[occurrence.symbol_id] = UnknownValue(
                reason="class body and metaclass effects",
            )
        return [Flow(state=frame.state)]

    def match_pattern_matchas(
        self,
        pattern: MatchAs,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchAs in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchAs for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if pattern.pattern is not None:
            decision: bool | None = self._match_pattern(
                pattern=pattern.pattern,
                subject=frame.subject,
                state=frame.state,
                context_id=frame.context_id,
            )
        else:
            decision = True
        if decision is not False and pattern.name is not None:
            self._write_pattern_binding(
                pattern=pattern,
                value=frame.subject,
                state=frame.state,
            )
        return decision

    def match_pattern_matchstar(
        self,
        pattern: MatchStar,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchStar in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchStar for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if pattern.name is not None:
            self._write_pattern_binding(
                pattern=pattern,
                value=frame.subject,
                state=frame.state,
            )
        return True

    def match_pattern_matchvalue(
        self,
        pattern: MatchValue,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchValue in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchValue for this operation.

        Returns:
            bool | None produced by this operation.

        """
        expected: AbstractValue = self._eval(
            node=pattern.value,
            state=frame.state,
            context_id=frame.context_id,
        )
        return self._compare(op=Eq(), left=frame.subject, right=expected)

    def match_pattern_matchsequence(
        self,
        pattern: MatchSequence,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchSequence in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchSequence for this operation.

        Returns:
            bool | None produced by this operation.

        """
        elements: tuple[AbstractValue, ...] | None = self._sequence_elements(
            subject=frame.subject,
            state=frame.state,
        )
        if elements is None:
            for item in pattern.patterns:
                self._match_pattern(
                    pattern=item,
                    subject=UnknownValue(reason="unknown sequence member"),
                    state=frame.state,
                    context_id=frame.context_id,
                )
            return None
        stars: list[int] = [
            index
            for index, item in enumerate(iterable=pattern.patterns)
            if isinstance(item, MatchStar)
        ]
        required: int = len(pattern.patterns) - len(stars)
        if len(elements) < required or (
            not stars and len(elements) != required
        ):
            return False
        result: bool | None = True
        for index, item in enumerate(iterable=pattern.patterns):
            if isinstance(item, MatchStar):
                value: AbstractValue = SequenceValue(
                    elements=elements[
                        index : len(elements) - (required - index)
                    ],
                    kind="list",
                )
            elif stars and index > stars[0]:
                value = elements[index + len(elements) - len(pattern.patterns)]
            else:
                value = elements[index]
            decision: bool | None = self._match_pattern(
                pattern=item,
                subject=value,
                state=frame.state,
                context_id=frame.context_id,
            )
            if decision is False:
                return False
            if decision is None:
                result = None
        return result

    def match_pattern_matchor(
        self,
        pattern: MatchOr,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchOr in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchOr for this operation.

        Returns:
            bool | None produced by this operation.

        """
        possibilities: list[State] = []
        unknown: bool = False
        for item in pattern.patterns:
            alternative: State = frame.state.clone()
            decision: bool | None = self._match_pattern(
                pattern=item,
                subject=frame.subject,
                state=alternative,
                context_id=frame.context_id,
            )
            if decision is not False:
                possibilities.append(alternative)
                unknown = unknown or decision is None
        if not possibilities:
            return False
        combined: State = possibilities[0]
        for alternative in possibilities[1:]:
            combined = combined.merge(
                other=alternative,
                limit=self.budgets.max_union,
            )
        frame.state.values = combined.values
        frame.state.heap = combined.heap
        return None if unknown else True

    def match_pattern_matchmapping(
        self,
        pattern: MatchMapping,
        frame: MatchPatternFrame,
        /,
    ) -> bool | None:
        """Handle MatchMapping in ``_match_pattern``.

        Args:
            frame: Frame supplied as MatchPatternFrame for this operation.
            pattern: Pattern supplied as MatchMapping for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if isinstance(frame.subject, ObjectReference):
            self._touch_heap(
                node=pattern,
                reference=frame.subject,
                write=False,
            )
        for key, item in zip(pattern.keys, pattern.patterns, strict=True):
            key_index: AbstractValue = self._eval(
                node=key,
                state=frame.state,
                context_id=frame.context_id,
            )
            value: AbstractValue = (
                self.heap.read_index(
                    reference=frame.subject,
                    index=key_index,
                    objects=frame.state.heap,
                )
                if isinstance(frame.subject, ObjectReference)
                else UnknownValue(reason="unknown mapping subject")
            )
            self._match_pattern(
                pattern=item,
                subject=value,
                state=frame.state,
                context_id=frame.context_id,
            )
        if pattern.rest is not None:
            self._write_pattern_binding(
                pattern=pattern,
                value=UnknownValue(reason="remaining mapping fields"),
                state=frame.state,
            )
        return None

    @classmethod
    def _compare(
        cls,
        *,
        op: AST,
        left: AbstractValue,
        right: AbstractValue,
    ) -> bool | None:
        """Compare safe immutable built-ins without unsafe identity claims.

        Args:
            left: Left supplied as AbstractValue for this operation.
            op: Op supplied as AST for this operation.
            right: Right supplied as AbstractValue for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if not isinstance(left, LiteralValue) or not isinstance(
            right,
            LiteralValue,
        ):
            return None
        a: Primitive = left.value
        b: Primitive = right.value
        try:
            if isinstance(op, Eq):
                return a == b
            if isinstance(op, NotEq):
                return a != b
            if isinstance(op, (Is, IsNot)):
                return cls._none_identity(op=op, a=a, b=b)
            return cls._ordered_or_member(op=op, a=a, b=b)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _builtin(
        cls,
        *,
        name: str,
        args: tuple[AbstractValue, ...],
    ) -> AbstractValue:
        """Evaluate a small built-in whitelist on trusted abstract inputs.

        Args:
            args: Collection of args supplied for this operation.
            name: Identifier of the name being resolved.

        Returns:
            AbstractValue produced by this operation.

        """
        handler: Callable[..., AbstractValue | None] | None = getattr(
            cls,
            (f"builtin_{name}"),
            None,
        )
        modelled: AbstractValue | None = (
            handler(args) if handler is not None else None
        )
        if modelled is not None:
            return modelled
        return UnknownValue(
            reason=(f"builtin {name} not safely modelled for these arguments"),
        )

    @classmethod
    def _handler_matches(
        cls,
        *,
        handler: ExceptHandler,
        exception: AbstractValue,
    ) -> bool | None:
        """Match only known built-in exception names; never run handlers.

        Args:
            exception: Exception supplied as AbstractValue for this operation.
            handler: Handler supplied as ExceptHandler for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if handler.type is None:
            return True
        names: tuple[str, ...] = cls._handler_names(handler=handler)
        if not names or not isinstance(exception, ErrorValue):
            return None
        return _exception_name_match(
            raised=exception.exception_type,
            names=names,
        )

    @staticmethod
    def _binary(
        *,
        op: AST,
        left: AbstractValue,
        right: AbstractValue,
    ) -> AbstractValue:
        """Compute exact arithmetic only for approved primitive operands.

        Args:
            left: Left supplied as AbstractValue for this operation.
            op: Op supplied as AST for this operation.
            right: Right supplied as AbstractValue for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        if not isinstance(left, LiteralValue) or not isinstance(
            right,
            LiteralValue,
        ):
            return UnknownValue(
                reason="arithmetic depends on unknown operands",
            )
        a: Primitive = left.value
        b: Primitive = right.value
        refusal: UnknownValue | None = _arithmetic_refusal(op=op, a=a, b=b)
        if refusal is not None:
            return refusal
        handler: Callable[[Primitive, Primitive], Primitive] | None = (
            _arithmetic_handler(op=op, b=b)
        )
        if handler is None:
            return UnknownValue(
                reason="operator unsupported or budget-limited",
            )
        try:
            return LiteralValue(value=handler(a, b))
        except (ArithmeticError, TypeError, ValueError, MemoryError) as error:
            return _arithmetic_failure(error=error)

    @staticmethod
    def _unary(*, op: AST, value: AbstractValue) -> AbstractValue:
        """Perform safe known built-in unary operations.

        Args:
            op: Op supplied as AST for this operation.
            value: The value examined while perform safe known built-in unary
                operations.

        Returns:
            AbstractValue produced by this operation.

        """
        if isinstance(op, Not):
            truth: bool | None = truth_value(value=value)
            return (
                LiteralValue(value=not truth)
                if truth is not None
                else UnknownValue(reason="unknown truthiness")
            )
        if isinstance(value, LiteralValue) and type(value.value) in (
            int,
            float,
            complex,
            bool,
        ):
            if isinstance(op, UAdd):
                return LiteralValue(value=Constants.positive(value.value))
            if isinstance(op, USub):
                return LiteralValue(value=Constants.negative(value.value))
            if isinstance(op, Invert) and isinstance(value.value, int):
                return LiteralValue(value=Constants.invert(int(value.value)))
        return UnknownValue(reason="unsupported unary operation")

    @staticmethod
    def _none_identity(*, op: AST, a: Primitive, b: Primitive) -> bool | None:
        """Decide ``is`` / ``is not`` only when ``None`` is involved.

        Args:
            a: A supplied as Primitive for this operation.
            b: B supplied as Primitive for this operation.
            op: Op supplied as AST for this operation.

        Returns:
            bool | None produced by this operation.

        """
        if a is None or b is None:
            same: bool = (a is None) == (b is None)
            return same if isinstance(op, Is) else not same
        return None

    @staticmethod
    def _ordered_or_member(
        *,
        op: AST,
        a: Primitive,
        b: Primitive,
    ) -> bool | None:
        """Decide ordering and ``in`` / ``not in`` for primitive operands.

        Args:
            a: A supplied as Primitive for this operation.
            b: B supplied as Primitive for this operation.
            op: Op supplied as AST for this operation.

        Returns:
            bool | None produced by this operation.

        """
        ordering: Callable[[Primitive, Primitive], bool] | None = (
            operation_for(table=Constants.orderings, op=op)
        )
        if ordering is not None:
            return ordering(a, b)
        if isinstance(op, In) and isinstance(b, (str, bytes)):
            return Constants.contains(b, a)
        if isinstance(op, NotIn) and isinstance(b, (str, bytes)):
            return not Constants.contains(b, a)
        return None

    @staticmethod
    def _convert(
        name: str,
        args: tuple[AbstractValue, ...],
    ) -> AbstractValue | None:
        """Model ``int``, ``str`` and ``bool`` of one known primitive.

        Args:
            args: Collection of args supplied for this operation.
            name: Identifier of the name being resolved.

        Returns:
            AbstractValue | None produced by this operation.

        """
        if len(args) != 1 or not isinstance(args[0], LiteralValue):
            return None
        primitive: Primitive = args[0].value
        try:
            if name == "int" and isinstance(
                primitive,
                (int, float, str, bool),
            ):
                return LiteralValue(value=int(primitive))
            if name == "str":
                return LiteralValue(value=str(object=primitive))
            if name == "bool":
                return LiteralValue(value=bool(primitive))
        except (TypeError, ValueError, OverflowError):
            return None
        return None

    @staticmethod
    def _is_generator(*, function: FunctionDef | AsyncFunctionDef) -> bool:
        """Detect suspension in this function, excluding nested scopes.

        Args:
            function: The function examined while detect suspension in this
                function, excluding nested scopes.

        Returns:
            Whether the requested condition holds.

        """
        pending: list[AST] = list(function.body)
        while pending:
            node: AST = pending.pop()
            if isinstance(node, (Yield, YieldFrom)):
                return True
            if not isinstance(
                node,
                (FunctionDef, AsyncFunctionDef, Lambda, ClassDef),
            ):
                pending.extend(iter_child_nodes(node=node))
        return False

    @staticmethod
    def _clone_paths(*, paths: list[Flow]) -> tuple[Flow, ...]:
        """Snapshot each path independently for incremental reuse.

        Args:
            paths: Paths supplied as list[Flow] for this operation.

        Returns:
            tuple[Flow, ...] produced by this operation.

        """
        return tuple(
            Flow(
                state=path.state.clone(),
                control=path.control,
                value=path.value,
            )
            for path in paths
        )

    @staticmethod
    def _sequence_elements(
        *,
        subject: AbstractValue,
        state: State,
    ) -> tuple[AbstractValue, ...] | None:
        """Known elements of a sequence or an unmodified abstract list.

        Args:
            state: State supplied as State for this operation.
            subject: Subject supplied as AbstractValue for this operation.

        Returns:
            tuple[AbstractValue, ...] | None produced by this operation.

        """
        if isinstance(subject, SequenceValue):
            return subject.elements
        if (
            isinstance(subject, ObjectReference)
            and len(subject.object_ids) == 1
        ):
            found: HeapObject | None = state.heap.get(
                next(iter(subject.object_ids)),
            )
            if (
                found is not None
                and found.kind == "list"
                and (not found.unknown_content)
            ):
                return found.elements
        return None

    @staticmethod
    def _handler_names(*, handler: ExceptHandler) -> tuple[str, ...]:
        """Plain exception class names an ``except`` clause lists.

        Args:
            handler: Handler supplied as ExceptHandler for this operation.

        Returns:
            tuple[str, ...] produced by this operation.

        """
        if isinstance(handler.type, Tuple):
            return tuple(
                item.id for item in handler.type.elts if isinstance(item, Name)
            )
        if isinstance(handler.type, Name):
            return (handler.type.id,)
        return ()

    @staticmethod
    def _referenced_ids(*, value: AbstractValue) -> frozenset[int]:
        """Collect abstract object identities an inferred value may denote.

        Args:
            value: Inferred value inspected for object references.

        Returns:
            Possible allocation identities reachable without heap reads.

        """
        pending: list[AbstractValue] = [value]
        found: set[int] = set()
        while pending:
            item: AbstractValue = pending.pop()
            if isinstance(item, ObjectReference):
                found.update(item.object_ids)
            elif isinstance(item, BoundMethodValue):
                found.update(item.receiver.object_ids)
            elif isinstance(item, UnionValue):
                pending.extend(item.options)
        return frozenset(found)

    def _record(
        self,
        *,
        node: AST,
        value: AbstractValue,
        trace: tuple[str, ...] = (),
        exceptions: tuple[str, ...] = (),
    ) -> AbstractValue:
        """Store a proof and node-level value dependencies.

        Args:
            exceptions: Exceptions supplied as tuple[str, ...] for this
                operation.
            node: The node examined while store a proof and node-level value
                dependencies.
            trace: Trace supplied as tuple[str, ...] for this operation.
            value: The value examined while store a proof and node-level value
                dependencies.

        Returns:
            AbstractValue produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        child_symbols: set[int] = set()
        for child in iter_child_nodes(node=node):
            symbol: int | None = read_attribute(
                node=child,
                name="symbol_id",
                kind=int,
            )
            if symbol is not None:
                child_symbols.add(symbol)
        dependencies: tuple[int, ...] = tuple(sorted(child_symbols))
        previous: InferenceResult | None = self.node_results.get(identity)
        aggregated: AbstractValue = (
            join_values(
                left=previous.value,
                right=value,
                limit=self.budgets.max_union,
            )
            if previous is not None
            else value
        )
        failure: tuple[str, ...] = (
            (value.exception_type,)
            if isinstance(value, ErrorValue)
            else exceptions
        )
        result: InferenceResult = InferenceResult(
            value=aggregated,
            status=proof_status(value=aggregated),
            dependencies=dependencies,
            trace=trace or ((f"{type(node).__name__}: {value!r}"),),
            possible_exceptions=failure,
        )
        self.node_results[identity] = result
        write_attribute(node=node, name="inferred_value", value=aggregated)
        write_attribute(
            node=node,
            name="value_evidence",
            value=tuple(
                ValueEvidence(
                    node_id=identity,
                    description=item,
                    dependencies=dependencies,
                )
                for item in result.trace
            ),
        )
        write_attribute(
            node=node,
            name="inferred_type",
            value=type(aggregated).__name__,
        )
        if (
            isinstance(aggregated, ObjectReference)
            and len(aggregated.object_ids) == 1
        ):
            write_attribute(
                node=node,
                name="object_id",
                value=next(iter(aggregated.object_ids)),
            )
        for object_id in sorted(self._referenced_ids(value=aggregated)):
            site: int | None = self.heap.allocation_node(
                object_id=object_id,
            )
            if site is not None:
                self.scopes.graph.add(
                    consumer=identity,
                    producer=site,
                    kind="REFERENCES_OBJECT",
                )
        for child in iter_child_nodes(node=node):
            self.scopes.graph.add(
                consumer=identity,
                producer=self.identities.node_id(node=child),
                kind="DEPENDS_ON_VALUE",
            )
        if failure:
            self.exceptions.setdefault(identity, set()).update(failure)
        return value

    def _budget(self) -> bool:
        """Check the global operation budget before an expression.

        Returns:
            Whether the requested condition holds.

        """
        self._operations += 1
        return self._operations <= self.budgets.max_operations and (
            self._deadline is None or monotonic() <= self._deadline
        )

    def _symbolic(self) -> bool:
        """Check the composite expression-operation budget.

        Returns:
            Whether the requested condition holds.

        """
        self._symbolic_operations += 1
        return (
            self._symbolic_operations <= self.budgets.max_symbolic_operations
        )

    def _eval(
        self,
        *,
        node: AST | None,
        state: State,
        context_id: int,
    ) -> AbstractValue:
        """Evaluate supported AST syntax using safe explicit transfer rules.

        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while evaluate supported AST syntax using
                safe explicit transfer rules.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        if node is None:
            return LiteralValue(value=None)
        identity: int = self.identities.node_id(node=node)
        self.at[identity] = state.clone()
        if not self._budget():
            return self._record(
                node=node,
                value=UnknownValue(
                    reason="analysis operation budget exceeded",
                ),
            )
        result: AbstractValue = UnknownValue(
            reason=(f"unsupported {type(node).__name__}"),
        )
        for handler_name in handler_names(node=node, prefix="eval_"):
            handler: Callable[..., AbstractValue] | None = getattr(
                self,
                handler_name,
                None,
            )
            if handler is not None:
                result = handler(node, state, context_id, identity)
                break
        self._record(node=node, value=result)
        return result

    def _assign_name(
        self,
        *,
        target: Name,
        value: AbstractValue,
        state: State,
    ) -> None:
        """Bind a resolved name and annotate its target node.

        Args:
            state: State supplied as State for this operation.
            target: The target examined while bind a resolved name and annotate
                its target node.
            value: The value examined while bind a resolved name and annotate
                its target node.

        """
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            self.identities.node_id(node=target),
        )
        if occurrence is None or occurrence.symbol_id is None:
            return
        state.values[occurrence.symbol_id] = value
        write_attribute(node=target, name="inferred_value", value=value)
        if isinstance(value, ObjectReference) and len(value.object_ids) == 1:
            write_attribute(
                node=target,
                name="object_id",
                value=next(iter(value.object_ids)),
            )

    def _assign_sequence(
        self,
        *,
        target: Tuple | List,
        value: AbstractValue,
        state: State,
        context_id: int,
    ) -> None:
        """Unpack a known sequence value into a tuple or list target.

        Args:
            context_id: Context id supplied as int for this operation.
            state: State supplied as State for this operation.
            target: The target examined while unpack a known sequence value
                into a tuple or list target.
            value: The value examined while unpack a known sequence value into
                a tuple or list target.

        """
        items: tuple[AbstractValue, ...] = ()
        if isinstance(value, SequenceValue):
            items = value.elements
        elif isinstance(value, ObjectReference) and len(value.object_ids) == 1:
            found: HeapObject | None = state.heap.get(
                next(iter(value.object_ids)),
            )
            if found is not None and (not found.unknown_content):
                items = found.elements
        for index, item in enumerate(iterable=target.elts):
            self._assign(
                target=item,
                value=items[index]
                if index < len(items)
                else UnknownValue(reason="unpack target"),
                state=state,
                context_id=context_id,
            )

    def _assign_heap(
        self,
        *,
        target: Subscript | Attribute,
        value: AbstractValue,
        state: State,
        context_id: int,
    ) -> None:
        """Write through a subscript or attribute into an abstract object.

        Args:
            context_id: Context id supplied as int for this operation.
            state: State supplied as State for this operation.
            target: The target examined while write through a subscript or
                attribute into an abstract object.
            value: The value examined while write through a subscript or
                attribute into an abstract object.

        """
        receiver: AbstractValue = self._eval(
            node=target.value,
            state=state,
            context_id=context_id,
        )
        index: AbstractValue = (
            self._eval(node=target.slice, state=state, context_id=context_id)
            if isinstance(target, Subscript)
            else LiteralValue(value=target.attr)
        )
        if isinstance(receiver, ObjectReference):
            self._touch_heap(node=target, reference=receiver, write=True)
            self.heap.write_index(
                reference=receiver,
                index=index,
                value=value,
                objects=state.heap,
            )

    def _assign(
        self,
        *,
        target: AST,
        value: AbstractValue,
        state: State,
        context_id: int,
    ) -> None:
        """Bind a lexical symbol or safely update an abstract heap location.

        Args:
            context_id: Context id supplied as int for this operation.
            state: State supplied as State for this operation.
            target: The target examined while bind a lexical symbol or safely
                update an abstract heap location.
            value: The value examined while bind a lexical symbol or safely
                update an abstract heap location.

        """
        if isinstance(target, Name):
            self._assign_name(target=target, value=value, state=state)
        elif isinstance(target, (Tuple, List)):
            self._assign_sequence(
                target=target,
                value=value,
                state=state,
                context_id=context_id,
            )
        elif isinstance(target, (Subscript, Attribute)):
            self._assign_heap(
                target=target,
                value=value,
                state=state,
                context_id=context_id,
            )
        elif isinstance(target, Starred):
            self._assign(
                target=target.value,
                value=value,
                state=state,
                context_id=context_id,
            )

    def _call_function(
        self,
        *,
        node: Call,
        callee: FunctionValue,
        arguments: tuple[AbstractValue, ...],
        keywords: dict[str, AbstractValue],
        state: State,
    ) -> AbstractValue:
        """Interpret a call of a known local function or lambda.

        Args:
            arguments: Collection of arguments supplied for this operation.
            callee: Callee supplied as FunctionValue for this operation.
            keywords: Keywords supplied as dict[str, AbstractValue] for this
                operation.
            node: The node examined while interpret a call of a known local
                function or lambda.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        caller_id: int = self.identities.node_id(node=node)
        self.scopes.graph.add(
            consumer=caller_id,
            producer=callee.node_id,
            kind="CALLS_FUNCTION",
        )
        function: FunctionDef | AsyncFunctionDef | Lambda | None = (
            self.function_nodes.get(callee.node_id)
        )
        if isinstance(
            function,
            (FunctionDef, AsyncFunctionDef),
        ) and self._is_generator(function=function):
            return GeneratorValue(
                function_id=callee.node_id,
                caller_id=caller_id,
                arguments=arguments,
                keywords=tuple(sorted(keywords.items())),
            )
        if isinstance(function, AsyncFunctionDef):
            return CoroutineValue(
                function_id=callee.node_id,
                caller_id=caller_id,
                arguments=arguments,
                keywords=tuple(sorted(keywords.items())),
            )
        return self.function_call(
            function_id=callee.node_id,
            arguments=ActualArguments(positional=arguments, named=keywords),
            state=state,
            caller_id=caller_id,
        )

    def _touch_heap(
        self,
        *,
        node: AST,
        reference: ObjectReference,
        write: bool,
    ) -> None:
        """Record a heap-location dependency edge for an accessing node.

        Args:
            node: Syntax node performing the heap access.
            reference: Abstract objects the access may reach.
            write: True for mutations, False for reads.

        """
        identity: int = self.identities.node_id(node=node)
        touched: dict[int, set[int]] = (
            self.heap_writers if write else self.heap_readers
        )
        kind: EdgeKind = (
            "WRITES_HEAP_LOCATION" if write else "READS_HEAP_LOCATION"
        )
        for object_id in sorted(reference.object_ids):
            touched.setdefault(object_id, set()).add(identity)
            site: int | None = self.heap.allocation_node(
                object_id=object_id,
            )
            if site is not None:
                self.scopes.graph.add(
                    consumer=identity,
                    producer=site,
                    kind=kind,
                )

    def _havoc_unknown_call(
        self,
        *,
        callee: AbstractValue,
        arguments: tuple[AbstractValue, ...],
        state: State,
        node: AST,
    ) -> None:
        """Invalidate heap objects an unanalyzable call may mutate.

        Args:
            arguments: Collection of arguments supplied for this operation.
            callee: Callee supplied as AbstractValue for this operation.
            node: Call expression causing the invalidation.
            state: State supplied as State for this operation.

        """
        for argument in arguments:
            if isinstance(argument, ObjectReference):
                self._touch_heap(node=node, reference=argument, write=True)
                self.heap.havoc(reference=argument, objects=state.heap)
        if isinstance(callee, UnknownValue):
            for value in state.values.values():
                if isinstance(value, ObjectReference):
                    self._touch_heap(node=node, reference=value, write=True)
                    self.heap.havoc(reference=value, objects=state.heap)

    def _call(
        self,
        *,
        node: Call,
        state: State,
        context_id: int,
    ) -> AbstractValue:
        """Interpret a known call or conservatively invalidate effects.

        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while interpret a known call or
                conservatively invalidate effects.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        callee: AbstractValue = self._eval(
            node=node.func,
            state=state,
            context_id=context_id,
        )
        arguments: tuple[AbstractValue, ...] = tuple(
            self._eval(node=item, state=state, context_id=context_id)
            for item in node.args
        )
        keywords: dict[str, AbstractValue] = {
            item.arg: self._eval(
                node=item.value,
                state=state,
                context_id=context_id,
            )
            for item in node.keywords
            if item.arg is not None
        }
        if isinstance(callee, BuiltinValue):
            return self._builtin(name=callee.name, args=arguments)
        if isinstance(callee, BoundMethodValue):
            return self._method(
                method=callee,
                args=arguments,
                state=state,
                node=node,
            )
        if isinstance(callee, FunctionValue):
            return self._call_function(
                node=node,
                callee=callee,
                arguments=arguments,
                keywords=keywords,
                state=state,
            )
        self._havoc_unknown_call(
            callee=callee,
            arguments=arguments,
            state=state,
            node=node,
        )
        return UnknownValue(
            reason="external or dynamic call may have side effects",
        )

    def _method(
        self,
        *,
        method: BoundMethodValue,
        args: tuple[AbstractValue, ...],
        state: State,
        node: AST,
    ) -> AbstractValue:
        """Model approved list mutations; unknown methods clear the heap.

        Args:
            args: Collection of args supplied for this operation.
            method: Method supplied as BoundMethodValue for this operation.
            node: Call expression performing the method access.
            state: State supplied as State for this operation.

        Returns:
            AbstractValue produced by this operation.

        """
        self._touch_heap(node=node, reference=method.receiver, write=True)
        for identity in method.receiver.object_ids:
            found: HeapObject | None = state.heap.get(identity)
            if found is None or found.kind != "list" or found.unknown_content:
                self.heap.havoc(reference=method.receiver, objects=state.heap)
                return UnknownValue(reason="unknown receiver method effects")
            contents: list[AbstractValue] = list(found.elements)
            if method.name == "append" and len(args) == 1:
                contents.append(args[0])
            elif (
                method.name == "extend"
                and len(args) == 1
                and isinstance(args[0], SequenceValue)
            ):
                contents.extend(args[0].elements)
            elif method.name == "pop" and len(args) <= 1 and contents:
                if args and (
                    not isinstance(args[0], LiteralValue)
                    or type(args[0].value) is not int
                ):
                    self.heap.havoc(
                        reference=method.receiver,
                        objects=state.heap,
                    )
                    return UnknownValue(reason="unknown pop index")
                index: int = (
                    args[0].value
                    if args
                    and isinstance(args[0], LiteralValue)
                    and (type(args[0].value) is int)
                    else -1
                )
                if not -len(contents) <= index < len(contents):
                    return UnknownValue(reason="pop index out of range")
                popped: AbstractValue = contents.pop(index)
                state.heap[identity] = HeapObject(
                    id=identity,
                    kind="list",
                    elements=tuple(contents),
                    summary=found.summary,
                    allocation_node_id=found.allocation_node_id,
                )
                return popped
            elif method.name == "clear" and (not args):
                contents.clear()
            else:
                self.heap.havoc(reference=method.receiver, objects=state.heap)
                return UnknownValue(
                    reason="unmodelled mutable collection method",
                )
            state.heap[identity] = HeapObject(
                id=identity,
                kind="list",
                elements=tuple(contents),
                summary=found.summary,
                allocation_node_id=found.allocation_node_id,
            )
        return LiteralValue(value=None)

    def _call_context(
        self,
        *,
        key: tuple[int, int, tuple[AbstractValue, ...]],
    ) -> int | UnknownValue:
        """Allocate or find the analysis context of a call, within budgets.

        Args:
            key: Key supplied as tuple[int, int, tuple[AbstractValue, ...]] for
                this operation.

        Returns:
            int | UnknownValue produced by this operation.

        """
        if (
            key in self._active_calls
            or self._current_call_depth >= self.budgets.max_recursion
        ):
            return UnknownValue(
                reason="recursive call reached conservative budget",
            )
        if key not in self.contexts:
            if len(self.contexts) >= self.budgets.max_contexts:
                return UnknownValue(reason="function context budget exceeded")
            self.contexts[key] = self._next_context
            self._next_context += 1
        context: int = self.contexts[key]
        call_node: AST | None = self.scopes.node_index.get(key[1])
        if call_node is not None:
            write_attribute(node=call_node, name="context_id", value=context)
        return context

    def _bind_parameters(
        self,
        *,
        function: FunctionDef | AsyncFunctionDef | Lambda,
        function_id: int,
        arguments: ActualArguments,
        caller_id: int,
        environment: State,
    ) -> None:
        """Bind actual arguments and defaults to the callee's parameters.

        Args:
            arguments: Collection of arguments supplied for this operation.
            caller_id: Caller id supplied as int for this operation.
            environment: Environment supplied as State for this operation.
            function: The function examined while bind actual arguments and
                defaults to the callee's parameters.
            function_id: Function id supplied as int for this operation.

        """
        args, keywords = (arguments.positional, arguments.named)
        parameters: tuple[arg, ...] = (
            *function.args.posonlyargs,
            *function.args.args,
        )
        defaults: tuple[AbstractValue, ...] = self.function_defaults.get(
            function_id,
            (),
        )
        default_offset: int = len(parameters) - len(defaults)
        caller_node: AST | None = self.scopes.node_index.get(caller_id)
        call_arguments: list[expr] = (
            caller_node.args if isinstance(caller_node, Call) else []
        )
        for index, parameter in enumerate(iterable=parameters):
            parameter_id: int | None = read_attribute(
                node=parameter,
                name="symbol_id",
                kind=int,
            )
            if parameter_id is None:
                continue
            value: AbstractValue = (
                args[index]
                if index < len(args)
                else keywords[parameter.arg]
                if parameter.arg in keywords
                else defaults[index - default_offset]
                if index >= default_offset
                else UnboundValue()
            )
            environment.values[parameter_id] = value
            if index < len(args):
                self.scopes.graph.add(
                    consumer=self.identities.node_id(node=parameter),
                    producer=self.identities.node_id(
                        node=call_arguments[index],
                    ),
                    kind="DEPENDS_ON_VALUE",
                )
        if function.args.vararg is not None:
            variable_id: int | None = read_attribute(
                node=function.args.vararg,
                name="symbol_id",
                kind=int,
            )
            if variable_id is not None:
                environment.values[variable_id] = SequenceValue(
                    elements=args[len(parameters) :],
                )
        for parameter in function.args.kwonlyargs:
            keyword_id: int | None = read_attribute(
                node=parameter,
                name="symbol_id",
                kind=int,
            )
            if keyword_id is not None:
                environment.values[keyword_id] = keywords.get(
                    parameter.arg,
                    UnboundValue(),
                )

    def _execute_call(
        self,
        *,
        function: FunctionDef | AsyncFunctionDef | Lambda,
        environment: State,
        call_context: int,
        key: tuple[int, int, tuple[AbstractValue, ...]],
    ) -> list[Flow]:
        """Run a callee body while tracking the active call stack.

        Args:
            call_context: Call context supplied as int for this operation.
            environment: Environment supplied as State for this operation.
            function: The function examined while run a callee body while
                tracking the active call stack.
            key: Key supplied as tuple[int, int, tuple[AbstractValue, ...]] for
                this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        self._active_calls.add(key)
        self._current_call_depth += 1
        try:
            if isinstance(function, Lambda):
                result: AbstractValue = self._eval(
                    node=function.body,
                    state=environment,
                    context_id=call_context,
                )
                return [
                    Flow(state=environment, control="return", value=result),
                ]
            return self._execute_suite(
                body=function.body,
                paths=[Flow(state=environment)],
                context_id=call_context,
            )
        finally:
            self._active_calls.remove(key)
            self._current_call_depth -= 1

    def _join_paths(
        self,
        *,
        paths: list[Flow],
    ) -> tuple[AbstractValue, State | None]:
        """Join normal returns, falling back to raised values.

        Args:
            paths: Paths supplied as list[Flow] for this operation.

        Returns:
            tuple[AbstractValue, State | None] produced by this operation.

        """
        result: AbstractValue = NeverValue()
        merged_state: State | None = None
        for path in paths:
            if path.control in ("normal", "return"):
                result = join_values(
                    left=result,
                    right=path.value
                    if path.control == "return"
                    else LiteralValue(value=None),
                    limit=self.budgets.max_union,
                )
                merged_state = (
                    path.state
                    if merged_state is None
                    else merged_state.merge(
                        other=path.state,
                        limit=self.budgets.max_union,
                    )
                )
        if merged_state is not None:
            return (result, merged_state)
        failures: list[AbstractValue] = [
            path.value for path in paths if path.control == "raise"
        ]
        if not failures:
            return (
                UnknownValue(reason="function has no normal return path"),
                None,
            )
        result = failures[0]
        for failure in failures[1:]:
            result = join_values(
                left=result,
                right=failure,
                limit=self.budgets.max_union,
            )
        return (result, None)

    def _publish_effects(
        self,
        *,
        state: State,
        merged_state: State,
        input_state: State,
        function_scope_id: int,
    ) -> None:
        """Publish changes to globals and closure cells, never to locals.

        Args:
            function_scope_id: Function scope id supplied as int for this
                operation.
            input_state: Input state supplied as State for this operation.
            merged_state: Merged state supplied as State for this operation.
            state: State supplied as State for this operation.

        """
        state.heap = merged_state.heap
        for symbol_id, value in merged_state.values.items():
            symbol: Symbol | None = self.scopes.symbols.get(symbol_id)
            if (
                symbol is not None
                and symbol.scope_id != function_scope_id
                and (
                    symbol.scope_id == self.scopes.root_id
                    or symbol_id in input_state.values
                )
            ) and value != state.values.get(symbol_id, UnboundValue()):
                state.values[symbol_id] = value

    def _invalidate_definition_results(self, *, body: list[stmt]) -> None:
        """Forget cached results inside function and class bodies.

        Function bodies may be revisited under new call contexts, so their
        previously aggregated expression values are not valid evidence in
        this revision, even when the syntax itself did not change.


        Args:
            body: Body supplied as list[stmt] for this operation.

        """
        for statement in body:
            if not isinstance(
                statement,
                (FunctionDef, AsyncFunctionDef, ClassDef),
            ):
                continue
            descendants: list[AST] = list(iter_child_nodes(node=statement))
            while descendants:
                descendant: AST = descendants.pop()
                descendant_id: int = self.identities.node_id(node=descendant)
                self.node_results.pop(descendant_id, None)
                self.at.pop(descendant_id, None)
                self.call_results.pop(descendant_id, None)
                self.exceptions.pop(descendant_id, None)
                for touched in (self.heap_readers, self.heap_writers):
                    for accessing in touched.values():
                        accessing.discard(descendant_id)
                clear_attribute(node=descendant, name="inferred_value")
                descendants.extend(iter_child_nodes(node=descendant))

    def _reads_stable(
        self,
        *,
        statement: stmt,
        changed_symbols: set[int],
    ) -> bool:
        """Whether a statement's reads avoid calls and changed symbols.

        Args:
            changed_symbols: Changed symbols supplied as set[int] for this
                operation.
            statement: The statement examined while whether a statement's reads
                avoid calls and changed symbols.

        Returns:
            Whether the requested condition holds.

        """
        for node in iter_child_nodes(node=statement):
            stack: list[AST] = [node]
            while stack:
                child: AST = stack.pop()
                if isinstance(
                    child,
                    (Call, NamedExpr, Await, Yield, YieldFrom),
                ):
                    return False
                if isinstance(child, Name) and isinstance(child.ctx, Load):
                    occurrence: Occurrence | None = (
                        self.scopes.occurrences.get(
                            self.identities.node_id(node=child),
                        )
                    )
                    if (
                        occurrence is None
                        or occurrence.symbol_id in changed_symbols
                    ):
                        return False
                stack.extend(iter_child_nodes(node=child))
        return True

    def _reusable_changes(
        self,
        *,
        statement: stmt,
        index: int,
        dirty: frozenset[int],
        inputs: list[Flow],
    ) -> set[int] | None:
        """Symbols that changed on entry, or ``None`` if reuse is unsafe.

        An unchanged transfer is reused when none of its read dependencies or
        abstract heap locations changed.


        Args:
            dirty: Dirty supplied as frozenset[int] for this operation.
            index: Index identifying a position in the relevant sequence or
                source.
            inputs: Inputs supplied as list[Flow] for this operation.
            statement: The statement examined while symbols that changed on
                entry, or ``None`` if reuse is unsafe.

        Returns:
            set[int] | None produced by this operation.

        """
        previous_inputs: tuple[Flow, ...] = self._module_inputs[index]
        previous_outputs: tuple[Flow, ...] = self._module_outputs[index]
        if not (
            index not in dirty
            and isinstance(statement, (Assign, AnnAssign))
            and all(
                isinstance(target, Name)
                for target in (
                    statement.targets
                    if isinstance(statement, Assign)
                    else [statement.target]
                )
            )
            and (
                len(inputs)
                == len(previous_inputs)
                == len(previous_outputs)
                == 1
            )
            and (inputs[0].control == previous_inputs[0].control == "normal")
            and (previous_outputs[0].control == "normal")
            and (inputs[0].state.heap == previous_inputs[0].state.heap)
        ):
            return None
        changed_symbols: set[int] = {
            identity
            for identity in inputs[0].state.values.keys()
            | previous_inputs[0].state.values.keys()
            if inputs[0].state.values.get(identity)
            != previous_inputs[0].state.values.get(identity)
        }
        if not self._reads_stable(
            statement=statement,
            changed_symbols=changed_symbols,
        ):
            return None
        return changed_symbols

    def _reuse_output(
        self,
        *,
        index: int,
        inputs: list[Flow],
        changed_symbols: set[int],
    ) -> tuple[Flow, ...]:
        """Carry incoming differences through a statement's cached output.

        Args:
            changed_symbols: Changed symbols supplied as set[int] for this
                operation.
            index: Index identifying a position in the relevant sequence or
                source.
            inputs: Inputs supplied as list[Flow] for this operation.

        Returns:
            tuple[Flow, ...] produced by this operation.

        """
        cached: Flow = self._module_outputs[index][0]
        copied: State = cached.state.clone()
        for identity in changed_symbols:
            if identity in inputs[0].state.values:
                copied.values[identity] = inputs[0].state.values[identity]
            else:
                copied.values.pop(identity, None)
        return (
            Flow(state=copied, control=cached.control, value=cached.value),
        )

    def _reexecute_statement(
        self,
        *,
        statement: stmt,
        inputs: list[Flow],
    ) -> tuple[Flow, ...]:
        """Clear a statement's cached facts and interpret it again.

        Args:
            inputs: Inputs supplied as list[Flow] for this operation.
            statement: The statement examined while clear a statement's cached
                facts and interpret it again.

        Returns:
            tuple[Flow, ...] produced by this operation.

        """
        nodes: list[AST] = [statement]
        while nodes:
            node: AST = nodes.pop()
            node_id: int = self.identities.node_id(node=node)
            self.node_results.pop(node_id, None)
            self.at.pop(node_id, None)
            self.call_results.pop(node_id, None)
            for touched in (self.heap_readers, self.heap_writers):
                for accessing in touched.values():
                    accessing.discard(node_id)
            nodes.extend(iter_child_nodes(node=node))
        outputs: list[Flow] = []
        for path in inputs:
            if path.control != "normal":
                outputs.append(path)
            else:
                outputs.extend(
                    self._step(node=statement, state=path.state, context_id=0),
                )
        return self._clone_paths(paths=self._limit_paths(paths=outputs))

    def _final_module_state(self) -> State:
        """Merge the states leaving the last module statement.

        Returns:
            State produced by this operation.

        """
        final: State | None = None
        if self._module_outputs:
            for path in self._module_outputs[-1]:
                final = (
                    path.state
                    if final is None
                    else final.merge(
                        other=path.state,
                        limit=self.budgets.max_union,
                    )
                )
        return final or State()

    def _execute_suite(
        self,
        *,
        body: list[stmt],
        paths: list[Flow],
        context_id: int,
    ) -> list[Flow]:
        """Interpret structured statements and snapshot the module dataflow.

        Args:
            body: Body supplied as list[stmt] for this operation.
            context_id: Context id supplied as int for this operation.
            paths: Paths supplied as list[Flow] for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        module: bool = context_id == 0 and body is getattr(
            self.root,
            "body",
            None,
        )
        for statement in body:
            if module:
                self._module_inputs.append(self._clone_paths(paths=paths))
            new_paths: list[Flow] = []
            for path in paths:
                if path.control == "normal":
                    new_paths.extend(
                        self._step(
                            node=statement,
                            state=path.state,
                            context_id=context_id,
                        ),
                    )
                else:
                    new_paths.append(path)
            paths = self._limit_paths(paths=new_paths)
            if module:
                self._module_outputs.append(self._clone_paths(paths=paths))
            if not any(path.control == "normal" for path in paths):
                if module:
                    self._module_outputs.extend(
                        self._clone_paths(paths=paths)
                        for _ in body[len(self._module_outputs) :]
                    )
                    self._module_inputs.extend(
                        self._clone_paths(paths=paths)
                        for _ in body[len(self._module_inputs) :]
                    )
                break
        return paths

    def _limit_paths(self, *, paths: list[Flow]) -> list[Flow]:
        """Bound active paths without discarding possible control transfers.

        Args:
            paths: Paths supplied as list[Flow] for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        if len(paths) <= self.budgets.max_paths:
            return paths
        grouped: dict[Control, Flow] = {}
        for path in paths:
            existing: Flow | None = grouped.get(path.control)
            if existing is None:
                grouped[path.control] = path
            else:
                existing.state = existing.state.merge(
                    other=path.state,
                    limit=self.budgets.max_union,
                )
                existing.value = join_values(
                    left=existing.value,
                    right=path.value,
                    limit=self.budgets.max_union,
                )
        return list(grouped.values())

    def _step(
        self,
        *,
        node: stmt,
        state: State,
        context_id: int,
    ) -> list[Flow]:
        """Execute one statement and return all relevant abstract exits.

        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while execute one statement and return all
                relevant abstract exits.
            state: State supplied as State for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        self.at[identity] = state.clone()
        if not self._budget():
            return [Flow(state=state)]
        frame: StepFrame = StepFrame(
            context_id=context_id,
            identity=identity,
            state=state,
        )
        for handler_name in handler_names(node=node, prefix="step_"):
            handler: Callable[..., list[Flow]] | None = getattr(
                self,
                handler_name,
                None,
            )
            if handler is not None:
                return handler(node, frame)
        return [Flow(state=state)]

    def _match_pattern(
        self,
        *,
        pattern: AST,
        subject: AbstractValue,
        state: State,
        context_id: int,
    ) -> bool | None:
        """Safely model Python match patterns and their capture bindings.

        Args:
            pattern: Python structural pattern node.
            subject: Abstract subject value.
            state: State receiving tentative pattern bindings.
            context_id: Active function call context.

        Returns:
            True, False, or None if matching cannot be established.

        """
        frame: MatchPatternFrame = MatchPatternFrame(
            context_id=context_id,
            state=state,
            subject=subject,
        )
        for handler_name in handler_names(
            node=pattern,
            prefix="match_pattern_",
        ):
            handler: Callable[..., bool | None] | None = getattr(
                self,
                handler_name,
                None,
            )
            if handler is not None:
                return handler(pattern, frame)
        return None

    def _write_pattern_binding(
        self,
        *,
        pattern: AST,
        value: AbstractValue,
        state: State,
    ) -> None:
        """Bind one statically identified pattern capture to the current state.

        Args:
            pattern: Pattern node owning its capture name.
            value: Captured subject abstraction.
            state: Matching branch environment.

        """
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            self.identities.node_id(node=pattern),
        )
        if occurrence is not None and occurrence.symbol_id is not None:
            state.values[occurrence.symbol_id] = value

    def _for_values(
        self,
        *,
        node: For | AsyncFor,
        state: State,
        context_id: int,
    ) -> tuple[AbstractValue, ...] | None:
        """Known elements a ``for`` loop iterates over, if any.

        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while known elements a ``for`` loop
                iterates over, if any.
            state: State supplied as State for this operation.

        Returns:
            tuple[AbstractValue, ...] | None produced by this operation.

        """
        iterable: AbstractValue = self._eval(
            node=node.iter,
            state=state,
            context_id=context_id,
        )
        if isinstance(iterable, SequenceValue):
            return iterable.elements
        if (
            isinstance(iterable, ObjectReference)
            and len(iterable.object_ids) == 1
        ):
            item: HeapObject | None = state.heap.get(
                next(iter(iterable.object_ids)),
            )
            if item is not None and (not item.unknown_content):
                return item.elements
        return None

    def _advance_path(
        self,
        *,
        node: While | For | AsyncFor,
        path: Flow,
        values: tuple[AbstractValue, ...] | None,
        ordinal: int,
        context_id: int,
    ) -> tuple[list[Flow], list[Flow], list[Flow]]:
        """Run one loop iteration on a path.

        Returns:
            Paths that left the loop normally, paths that exited abruptly,
            and paths that continue to the next iteration.



        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while run one loop iteration on a path.
            ordinal: Ordinal supplied as int for this operation.
            path: Filesystem path identifying the path.
            values: Values supplied as tuple[AbstractValue, ...] | None for
                this operation.

        """
        completed: list[Flow] = []
        interrupted: list[Flow] = []
        running: list[Flow] = []
        if path.control != "normal":
            return (completed, [path], running)
        if isinstance(node, While):
            condition: AbstractValue = self._eval(
                node=node.test,
                state=path.state,
                context_id=context_id,
            )
            truth: bool | None = truth_value(value=condition)
            if truth is not True:
                completed.append(Flow(state=path.state.clone()))
                if truth is False:
                    return (completed, interrupted, running)
        else:
            self._assign(
                target=node.target,
                value=values[ordinal]
                if values is not None
                else UnknownValue(reason="unknown iterable element"),
                state=path.state,
                context_id=context_id,
            )
        for outcome in self._execute_suite(
            body=node.body,
            paths=[path],
            context_id=context_id,
        ):
            if outcome.control == "break":
                interrupted.append(Flow(state=outcome.state))
            elif outcome.control in ("normal", "continue"):
                running.append(Flow(state=outcome.state))
            else:
                interrupted.append(outcome)
        return (completed, interrupted, running)

    def _widen_loop_state(self, *, start: State, prior: State) -> State:
        """Widen loop-carried values and heap objects after the unroll.

        Args:
            prior: Prior supplied as State for this operation.
            start: Start identifying a position in the relevant sequence or
                source.

        Returns:
            State produced by this operation.

        """
        widened: State = start.merge(other=prior, limit=self.budgets.max_union)
        widened.values = {
            symbol_id: UnknownValue(reason="unbounded loop-carried value")
            if value != start.values.get(symbol_id, UnboundValue())
            else value
            for symbol_id, value in widened.values.items()
        }
        widened.heap = {
            identity: HeapObject(
                id=identity,
                kind=entry.kind,
                unknown_content=True,
                summary=True,
            )
            for identity, entry in widened.heap.items()
        }
        return widened

    def _loop(
        self,
        *,
        node: While | For | AsyncFor,
        state: State,
        context_id: int,
    ) -> list[Flow]:
        """Unroll bounded loops, preserving break versus natural-else exits.

        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while unroll bounded loops, preserving
                break versus natural-else exits.
            state: State supplied as State for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        start: State = state.clone()
        running: list[Flow] = [Flow(state=state)]
        completed: list[Flow] = []
        interrupted: list[Flow] = []
        values: tuple[AbstractValue, ...] | None = None
        steps: int = self.budgets.max_iterations
        if isinstance(node, (For, AsyncFor)):
            values = self._for_values(
                node=node,
                state=state,
                context_id=context_id,
            )
            if values is None:
                steps = 1
                completed.append(Flow(state=start.clone()))
            else:
                steps = min(len(values), self.budgets.max_iterations)
        for ordinal in range(steps):
            next_running: list[Flow] = []
            for path in running:
                done, stopped, advanced = self._advance_path(
                    node=node,
                    path=path,
                    values=values,
                    ordinal=ordinal,
                    context_id=context_id,
                )
                completed.extend(done)
                interrupted.extend(stopped)
                next_running.extend(advanced)
            running = self._limit_paths(paths=next_running)
            if not running:
                break
        if values is not None and len(values) <= steps:
            completed.extend(running)
        elif running:
            completed.append(
                Flow(
                    state=self._widen_loop_state(
                        start=start,
                        prior=running[0].state,
                    ),
                ),
            )
        return self._limit_paths(
            paths=[
                *interrupted,
                *self._execute_suite(
                    body=node.orelse,
                    paths=completed,
                    context_id=context_id,
                ),
            ],
        )

    def _exception_symbol(self, *, handler: ExceptHandler) -> int | None:
        """Symbol bound by ``except ... as name``, if any.

        Args:
            handler: Handler supplied as ExceptHandler for this operation.

        Returns:
            int | None produced by this operation.

        """
        if handler.name is None:
            return None
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            self.identities.node_id(node=handler),
        )
        return occurrence.symbol_id if occurrence is not None else None

    def _handle_path(
        self,
        *,
        handler: ExceptHandler,
        path: Flow,
        context_id: int,
    ) -> list[Flow]:
        """Run a handler body for one exceptional path.

        Args:
            context_id: Context id supplied as int for this operation.
            handler: Handler supplied as ExceptHandler for this operation.
            path: Filesystem path identifying the path.

        Returns:
            list[Flow] produced by this operation.

        """
        symbol_id: int | None = self._exception_symbol(handler=handler)
        environment: State = path.state.clone()
        if symbol_id is not None:
            environment.values[symbol_id] = path.value
        outcomes: list[Flow] = self._execute_suite(
            body=handler.body,
            paths=[Flow(state=environment)],
            context_id=context_id,
        )
        if symbol_id is not None:
            for outcome in outcomes:
                outcome.state.values[symbol_id] = UnboundValue()
        return outcomes

    def _route_exception(
        self,
        *,
        node: Try | TryStar,
        exceptional: Flow,
        context_id: int,
    ) -> list[Flow]:
        """Send one raised path through each handler in order.

        Args:
            context_id: Context id supplied as int for this operation.
            exceptional: Exceptional supplied as Flow for this operation.
            node: The node examined while send one raised path through each
                handler in order.

        Returns:
            list[Flow] produced by this operation.

        """
        handled: list[Flow] = []
        pending: list[Flow] = [exceptional]
        for handler in node.handlers:
            remaining: list[Flow] = []
            for path in pending:
                match: bool | None = self._handler_matches(
                    handler=handler,
                    exception=path.value,
                )
                if match is not False:
                    handled.extend(
                        self._handle_path(
                            handler=handler,
                            path=path,
                            context_id=context_id,
                        ),
                    )
                if match is not True or isinstance(node, TryStar):
                    remaining.append(path)
            pending = remaining
        handled.extend(pending)
        return handled

    def _try(
        self,
        *,
        node: Try | TryStar,
        state: State,
        context_id: int,
    ) -> list[Flow]:
        """Route exceptional paths to matching handlers and honor final exits.

        Unknown exceptions and exception-group splitting are kept as possible
        paths rather than being treated as proven successful handling.


        Args:
            context_id: Context id supplied as int for this operation.
            node: The node examined while route exceptional paths to matching
                handlers and honor final exits.
            state: State supplied as State for this operation.

        Returns:
            list[Flow] produced by this operation.

        """
        paths: list[Flow] = self._execute_suite(
            body=node.body,
            paths=[Flow(state=state.clone())],
            context_id=context_id,
        )
        handled: list[Flow] = self._execute_suite(
            body=node.orelse,
            paths=[path for path in paths if path.control == "normal"],
            context_id=context_id,
        )
        handled.extend(
            path for path in paths if path.control not in ("normal", "raise")
        )
        for exceptional in (path for path in paths if path.control == "raise"):
            handled.extend(
                self._route_exception(
                    node=node,
                    exceptional=exceptional,
                    context_id=context_id,
                ),
            )
        if not node.finalbody:
            return self._limit_paths(paths=handled)
        finals: list[Flow] = []
        for path in handled:
            outcomes: list[Flow] = self._execute_suite(
                body=node.finalbody,
                paths=[Flow(state=path.state)],
                context_id=context_id,
            )
            finals.extend(
                Flow(
                    state=outcome.state,
                    control=path.control,
                    value=path.value,
                )
                if outcome.control == "normal"
                else outcome
                for outcome in outcomes
            )
        return self._limit_paths(paths=finals)
