"""Bounded bidirectional type inference with immutable provenance records.

The analyzer never evaluates analyzed Python code. A type estimate is distinct
from a declared annotation, and conflicting contracts remain inspectable.
"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    AnnAssign,
    Assert,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    Await,
    BinOp,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    Expr,
    FunctionDef,
    If,
    IfExp,
    Import,
    ImportFrom,
    Is,
    IsNot,
    List,
    Module,
    Name,
    NamedExpr,
    Not,
    Return,
    Set,
    Starred,
    Subscript,
    Tuple,
    TypeVar,
    UnaryOp,
    While,
    arg,
    expr,
    iter_child_nodes,
    walk,
)
from collections import deque
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart.semantic.parameter_kinds import ParameterKind
from astart.semantic.type_expressions import (
    TypeExpression,
    TypeExpressionCodec,
)
from astart.semantic.typing_contracts import (
    ArgumentOrigin,
    BoundArgument,
    BoundCall,
    CallableContract,
    ContractIndex,
    ParameterContract,
    bind_signature,
)
from astart.semantic.typing_relations import specialize, subtype, unify

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from astart.semantic.graph_conversion import GraphAnnotation
    from astart.semantic.identities import IdentityIndex, Occurrence
    from astart.semantic.scopes import ScopeGraph
    from astart.semantic.stubs import StubIndex, StubSignature
    from astart.semantic.typing_contracts import ClassContract
    from astart.semantic.typing_relations import Compatibility
from astart._graph.dispatch import handler_names
from astart.node_attributes import read_attribute, write_attribute
from astart.semantic.type_shapes import (
    TypeShape,
    atomic,
    join_types,
    type_shape,
    union_shapes,
)
from astart.semantic.values import (
    AbstractValue,
    LiteralValue,
    MappingValue,
    SequenceValue,
    UnionValue,
)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeEvidence:
    """Proof origin for a type or value statement, without executing source.

    Attributes:
        dependencies: Dependencies retained as tuple[int, ...] by this
            instance.
        description: Description retained as str by this instance.
        kind: Kind retained as str by this instance.
        node_id: Node id retained as int by this instance.

    """

    node_id: int
    kind: str
    description: str
    dependencies: tuple[int, ...] = ()


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeInference:
    """A type estimate with immutable evidence and contract diagnostics.

    Attributes:
        conflicts: Conflicts retained as tuple[str, ...] by this instance.
        declared: Declared retained as TypeShape | None by this instance.
        evidence: Evidence retained as tuple[TypeEvidence, ...] by this
            instance.
        inferred: Inferred retained as TypeShape by this instance.
        stable: Stable retained as bool by this instance.

    """

    inferred: TypeShape
    evidence: tuple[TypeEvidence, ...] = ()
    declared: TypeShape | None = None
    conflicts: tuple[str, ...] = ()
    stable: bool = True


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CallArguments:
    """Inferred types of a call's positional and named arguments.

    Attributes:
        named: Named retained as dict[str, TypeShape] by this instance.
        positional: Positional retained as tuple[TypeShape, ...] by this
            instance.

    """

    positional: tuple[TypeShape, ...]
    named: dict[str, TypeShape]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeBudgets:
    """Resource limits for the bounded type constraint solver.

    Attributes:
        max_visits: Maximum analysis-context visits before stopping.
        max_evidence: Maximum retained evidence records per type fact.

    """

    max_visits: int = 20000
    max_evidence: int = 40


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CallSite:
    """A call expression with its inferred arguments and local context.

    Attributes:
        arguments: Arguments retained as CallArguments by this instance.
        env: Env retained as dict[int, TypeShape] by this instance.
        name: Identifier used to refer to the name.
        narrowing: Narrowing retained as dict[str, TypeShape] | None by this
            instance.
        node: AST node associated with this record.

    """

    node: Call
    name: str | None
    arguments: CallArguments
    env: dict[int, TypeShape]
    narrowing: dict[str, TypeShape] | None


# Qualified names of imported constructors whose call arguments are typed
# from a curated signature.  Each entry maps the qualified name to
# ``(parameter name, kind, annotation source, optional)`` tuples; ``self``
# and ``cls`` receivers are excluded.  The table covers the constructors
# ``rules.imports.Constants.constructors`` recognizes plus their qualified
# origins, and stays deliberately small: anything absent resolves to
# ``Unknown`` rather than guessing.
_IMPORTED_CONSTRUCTOR_PARAMS: Final[
    dict[str, tuple[tuple[str, ParameterKind, str, bool], ...]]
] = {
    "datetime.date": (
        ("year", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
        ("month", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
        ("day", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
    ),
    "datetime.datetime": (
        ("year", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
        ("month", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
        ("day", ParameterKind.POSITIONAL_OR_KEYWORD, "int", False),
        ("hour", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("minute", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("second", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("microsecond", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("tzinfo", ParameterKind.POSITIONAL_OR_KEYWORD, "tzinfo | None", True),
        ("fold", ParameterKind.KEYWORD_ONLY, "int", True),
    ),
    "datetime.time": (
        ("hour", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("minute", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("second", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("microsecond", ParameterKind.POSITIONAL_OR_KEYWORD, "int", True),
        ("tzinfo", ParameterKind.POSITIONAL_OR_KEYWORD, "tzinfo | None", True),
        ("fold", ParameterKind.KEYWORD_ONLY, "int", True),
    ),
    "datetime.timedelta": tuple(
        (name, ParameterKind.POSITIONAL_OR_KEYWORD, "float | Decimal", True)
        for name in (
            "days",
            "seconds",
            "microseconds",
            "milliseconds",
            "minutes",
            "hours",
            "weeks",
        )
    ),
    "decimal.Decimal": (
        (
            "value",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "Decimal | float | str | tuple[int, ...]",
            True,
        ),
        (
            "context",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "Context | None",
            True,
        ),
    ),
    "fractions.Fraction": (
        (
            "numerator",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "int | float | Decimal | Fraction",
            True,
        ),
        (
            "denominator",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "int | float | Decimal | Fraction | None",
            True,
        ),
    ),
    "pathlib.Path": (
        (
            "args",
            ParameterKind.VAR_POSITIONAL,
            "str | PathLike[str]",
            False,
        ),
    ),
    "pathlib.PurePath": (
        (
            "args",
            ParameterKind.VAR_POSITIONAL,
            "str | PathLike[str]",
            False,
        ),
    ),
    "uuid.UUID": (
        ("hex", ParameterKind.POSITIONAL_OR_KEYWORD, "str | None", True),
        ("bytes", ParameterKind.POSITIONAL_OR_KEYWORD, "bytes | None", True),
        (
            "bytes_le",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "bytes | None",
            True,
        ),
        (
            "fields",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "tuple[int, int, int, int, int, int] | None",
            True,
        ),
        ("int", ParameterKind.POSITIONAL_OR_KEYWORD, "int | None", True),
        ("version", ParameterKind.POSITIONAL_OR_KEYWORD, "int | None", True),
        (
            "is_safe",
            ParameterKind.POSITIONAL_OR_KEYWORD,
            "UUIDSafe | None",
            True,
        ),
    ),
}


@final
class Constants:
    """Group module-level constants.

    Attributes:
        builtin_call_results: Grouped module constant.
        str_to_str: Grouped module constant.
        str_to_bool: Grouped module constant.
        str_to_int: Grouped module constant.
        mutating_methods: Grouped module constant.
        container_methods: Grouped module constant.
        implicit_origins: Grouped module constant.
        pair_size: Grouped module constant.

    """

    builtin_call_results: Final[dict[str, TypeShape]] = {
        "isinstance": atomic(name="bool"),
        **{
            name: atomic(name=name)
            for name in ("int", "float", "str", "bool", "complex")
        },
        **{
            name: TypeShape(name=name, arguments=(atomic(name="Unknown"),))
            for name in ("list", "dict", "set", "tuple")
        },
        **dict.fromkeys(("len", "hash", "ord", "id"), atomic(name="int")),
        **dict.fromkeys(
            ("repr", "ascii", "chr", "format"),
            atomic(name="str"),
        ),
        **dict.fromkeys(
            ("all", "any", "issubclass", "callable"),
            atomic(name="bool"),
        ),
    }
    str_to_str: Final[frozenset[str]] = frozenset(
        (
            "upper",
            "lower",
            "strip",
            "lstrip",
            "rstrip",
            "title",
            "capitalize",
            "casefold",
            "replace",
            "join",
            "removeprefix",
            "removesuffix",
            "center",
            "ljust",
            "rjust",
            "zfill",
            "format",
        ),
    )
    str_to_bool: Final[frozenset[str]] = frozenset(
        (
            "startswith",
            "endswith",
            "isalpha",
            "isalnum",
            "isdigit",
            "isnumeric",
            "isspace",
            "islower",
            "isupper",
            "istitle",
        ),
    )
    str_to_int: Final[frozenset[str]] = frozenset(
        ("find", "rfind", "index", "rindex", "count"),
    )
    mutating_methods: Final[frozenset[str]] = frozenset(
        ("append", "extend", "add", "update", "clear", "sort", "reverse"),
    )
    container_methods: Final[frozenset[str]] = frozenset(
        (
            "append",
            "extend",
            "add",
            "update",
            "pop",
            "get",
            "setdefault",
            "keys",
            "values",
            "items",
        ),
    )
    implicit_origins: Final[tuple[ArgumentOrigin, ...]] = (
        ArgumentOrigin.DEFAULT,
        ArgumentOrigin.DEFAULT_FACTORY,
        ArgumentOrigin.IMPLICIT_RECEIVER,
    )
    pair_size: Final[int] = 2


def _builtin_str_method(
    *,
    receiver_name: str,
    method: str,
) -> TypeShape | None:
    """Return the result type of a modeled ``str`` method, if it is one.

    Args:
        method: Method supplied as str for this operation.
        receiver_name: Identifier of the receiver being resolved.

    Returns:
        TypeShape | None produced by this operation.

    """
    if receiver_name != "str":
        return None
    if method in Constants.str_to_str:
        return atomic(name="str")
    if method in Constants.str_to_bool:
        return atomic(name="bool")
    if method in Constants.str_to_int:
        return atomic(name="int")
    return None


def _container_method_result(
    *,
    receiver: TypeShape,
    method: str,
    args: tuple[TypeShape, ...],
) -> TypeShape:
    """Return the result type of a modeled list, dict or set method.

    Args:
        args: Collection of args supplied for this operation.
        method: Method supplied as str for this operation.
        receiver: Receiver supplied as TypeShape for this operation.

    Returns:
        TypeShape produced by this operation.

    """
    if (
        method in ("pop", "get", "setdefault")
        and receiver.name == "dict"
        and (len(receiver.arguments) == Constants.pair_size)
    ):
        if method in ("get", "setdefault") and len(args) > 1:
            return join_types(left=receiver.arguments[1], right=args[1])
        if method == "get":
            return join_types(
                left=receiver.arguments[1],
                right=atomic(name="None"),
            )
        return receiver.arguments[1]
    if method == "pop" and receiver.name == "list" and receiver.arguments:
        return receiver.arguments[0]
    if method == "copy" and receiver.name in ("list", "dict", "set"):
        return receiver
    return atomic(
        name="None" if method in Constants.mutating_methods else "Unknown",
    )


def _receiver_update(
    *,
    receiver: TypeShape,
    method: str,
    args: tuple[TypeShape, ...],
) -> tuple[TypeShape, str] | None:
    """Return a container's updated type and why, if the call mutates it.

    Args:
        args: Collection of args supplied for this operation.
        method: Method supplied as str for this operation.
        receiver: Receiver supplied as TypeShape for this operation.

    Returns:
        tuple[TypeShape, str] | None produced by this operation.

    """
    if receiver.name in ("list", "set") and args:
        incoming: TypeShape = (
            args[0].arguments[0]
            if method == "extend"
            and args[0].name in ("tuple", "list", "set")
            and args[0].arguments
            else args[0]
        )
        return (
            TypeShape(
                name=receiver.name,
                arguments=(
                    join_types(left=receiver.arguments[0], right=incoming)
                    if receiver.arguments
                    else incoming,
                ),
            ),
            (f"{method} mutates receiver"),
        )
    if receiver.name == "dict" and method == "setdefault" and (len(args) > 1):
        updated: TypeShape = (
            TypeShape(
                name="dict",
                arguments=(
                    join_types(left=receiver.arguments[0], right=args[0]),
                    join_types(left=receiver.arguments[1], right=args[1]),
                ),
            )
            if len(receiver.arguments) == Constants.pair_size
            else TypeShape(name="dict", arguments=(args[0], args[1]))
        )
        return (updated, "setdefault may mutate mapping")
    if (
        receiver.name == "dict"
        and method == "update"
        and args
        and (args[0].name == "dict")
    ):
        return (
            join_types(left=receiver, right=args[0]),
            "update mutates mapping",
        )
    return None


def _iterated_element(*, site: CallSite) -> TypeShape:
    """Type one element produced by iterating a constructor argument.

    Iterating a ``dict`` yields its keys, a heterogeneous ``tuple`` the
    join of its elements, ``str`` yields ``str`` and ``bytes`` yields
    ``int``.

    Args:
        site: Call whose first positional argument is the iterable.

    Returns:
        The element type, or ``Unknown`` when indeterminate.

    """
    if len(site.arguments.positional) != 1:
        return atomic(name="Unknown")
    shape: TypeShape = site.arguments.positional[0]
    if shape.name == "dict" and len(shape.arguments) == Constants.pair_size:
        return shape.arguments[0]
    if shape.name == "tuple" and shape.arguments:
        element: TypeShape = shape.arguments[0]
        for extra in shape.arguments[1:]:
            element = join_types(left=element, right=extra)
        return element
    if shape.name in ("list", "set", "frozenset") and shape.arguments:
        return shape.arguments[0]
    if shape.name == "str":
        return atomic(name="str")
    return (
        atomic(name="int") if shape.name == "bytes" else atomic(name="Unknown")
    )


def _builtin_call(*, name: str, site: CallSite) -> TypeShape:
    """Type a call to an unresolved builtin name.

    Container constructors derive their element type from the iterated
    argument instead of reporting ``Unknown``; ``dict`` of a mapping
    keeps the mapping's key and value types.

    Args:
        name: Callee identifier.
        site: Call site with inferred argument shapes.

    Returns:
        The result shape.

    """
    base: TypeShape | None = Constants.builtin_call_results.get(name)
    if base is None:
        if name != "frozenset":
            return atomic(name="Unknown")
        base = TypeShape(
            name="frozenset",
            arguments=(atomic(name="Unknown"),),
        )
    if name in ("list", "set", "tuple", "frozenset"):
        return TypeShape(
            name=name,
            arguments=(_iterated_element(site=site),),
        )
    if (
        name == "dict"
        and len(site.arguments.positional) == 1
        and (source := site.arguments.positional[0]).name == "dict"
        and len(source.arguments) == Constants.pair_size
    ):
        return source
    return base


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeSolveStatistics:
    """Bounded constraint propagation counts and convergence status.

    Attributes:
        changes: Changes retained as int by this instance.
        converged: Converged retained as bool by this instance.
        reused: Reused retained as int by this instance.
        visits: Visits retained as int by this instance.

    """

    visits: int
    changes: int
    converged: bool
    reused: int


def _hint(*, node: AST | None) -> TypeShape:
    """Parse an annotation structurally without running annotation code.

    Args:
        node: The node examined while parse an annotation structurally without
            running annotation code.

    Returns:
        TypeShape produced by this operation.

    """
    return (
        atomic(name="Unknown")
        if node is None
        else type_shape(expression=TypeExpressionCodec.from_ast(node=node))
    )


def _literal(*, value: AbstractValue) -> TypeShape:
    """Project an abstract exact value to a conservative nominal type.

    Args:
        value: The value examined while project an abstract exact value to a
            conservative nominal type.

    Returns:
        TypeShape produced by this operation.

    """
    if isinstance(value, LiteralValue):
        return atomic(
            name="None" if value.value is None else type(value.value).__name__,
        )
    if isinstance(value, SequenceValue):
        element: TypeShape = atomic(name="Never")
        for item in value.elements:
            element = join_types(left=element, right=_literal(value=item))
        return TypeShape(name=value.kind, arguments=(element,))
    if isinstance(value, MappingValue):
        key: TypeShape = atomic(name="Never")
        content: TypeShape = atomic(name="Never")
        for item_key, item_value in value.entries:
            key = join_types(left=key, right=_literal(value=item_key))
            content = join_types(
                left=content,
                right=_literal(value=item_value),
            )
        return TypeShape(name="dict", arguments=(key, content))
    if isinstance(value, UnionValue):
        result: TypeShape = atomic(name="Never")
        for item in value.options:
            result = join_types(left=result, right=_literal(value=item))
        return result
    return atomic(name="Unknown")


@final
class TypeConstraintSolver:
    """Solve forward and backward local contracts with a bounded worklist.

    Contracts are soft evidence for inferred runtime values. The API never
    treats an annotation as proof that an incompatible runtime value cannot
    occur. Changed revisions create fresh solver state; unchanged revisions
    reuse their immutable results.
    """

    def __init__(
        self,
        *,
        root: Module,
        scopes: ScopeGraph,
        budgets: TypeBudgets | None = None,
        stubs: StubIndex | None = None,
        graph_conversion: tuple[GraphAnnotation, ...] = (),
    ) -> None:
        """Prepare the symbol/AST graph and solve to a bounded fixed point.

        Args:
            budgets: Budgets supplied as TypeBudgets | None for this operation.
            graph_conversion: Graph conversion supplied as
                tuple[GraphAnnotation, ...] for this operation.
            root: Filesystem path identifying the root.
            scopes: Collection of scopes supplied for this operation.
            stubs: Stubs supplied as StubIndex | None for this operation.

        """
        limits: TypeBudgets = budgets if budgets is not None else TypeBudgets()
        self.root: Module = root
        self.scopes: ScopeGraph = scopes
        self.identities: IdentityIndex = scopes.identities
        self.max_visits: int = limits.max_visits
        self.max_evidence: int = limits.max_evidence
        self.stubs: StubIndex | None = stubs
        self.graph_conversion: tuple[GraphAnnotation, ...] = graph_conversion
        self.contracts: ContractIndex = ContractIndex(root=root)
        self._imported_constructors: dict[
            str,
            CallableContract | None,
        ] = {}
        self.call_bindings: dict[int, BoundCall] = {}
        self._type_variables: set[str] = set()
        self._type_variable_bounds: dict[str, tuple[TypeShape, ...]] = {}
        self._scan_type_variables()
        self._imports: dict[str, str] = {}
        self.types: dict[int, TypeShape] = {}
        self.declarations: dict[int, TypeShape] = {}
        self.proofs: dict[int, list[TypeEvidence]] = {}
        self.node_types: dict[int, TypeShape] = {}
        self.node_proofs: dict[int, list[TypeEvidence]] = {}
        self.conflicts: dict[int, set[str]] = {}
        self._definitions: dict[str, FunctionDef | AsyncFunctionDef] = {}
        self._return_types: dict[str, TypeShape] = {}
        self._parameters: dict[str, tuple[int, ...]] = {}
        self._call_edges: dict[str, set[str]] = {}
        self._calls: dict[str, list[Call]] = {}
        self._scopes: dict[int, int] = {}
        self._nodes: dict[int, AST] = {}
        self._owner: dict[int, str] = {}
        self._symbol_by_name: dict[tuple[int, str], int] = {}
        self._function_parameters: dict[tuple[str, str], int] = {}
        self._method_receivers: dict[int, tuple[str, str, bool]] = {}
        self._instance_attributes: dict[
            tuple[str, str],
            list[AST],
        ] = {}
        self._instance_annotations: dict[
            tuple[str, str],
            TypeExpression,
        ] = {}
        self._class_assignments: dict[
            tuple[str, str],
            list[AST],
        ] = {}
        self._self_attr_active: set[int] = set()
        self._method_nodes: list[FunctionDef | AsyncFunctionDef] = []
        self._work: deque[str] = deque()
        self._queued: set[str] = set()
        self._build_index()
        self.statistics: TypeSolveStatistics = self._solve()
        self._solve_methods()
        self._publish()

    @staticmethod
    def infer_constant(
        node: Constant,
        _env: dict[int, TypeShape],
        _narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Constant for ``_infer``.

        Args:
            _env: Env supplied as dict[int, TypeShape] for this operation.
            _narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Constant for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        return atomic(
            name="None" if node.value is None else type(node.value).__name__,
        )

    def infer_name(
        self,
        node: Name,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Name for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Name for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        sid: int | None = self._symbol_id(node=node)
        return (narrowing or {}).get(
            node.id,
            env.get(sid, self.types.get(sid, atomic(name="Unknown")))
            if sid is not None
            else atomic(name="Unknown"),
        )

    def infer_list(
        self,
        node: List | Set | Tuple,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer List or Set or Tuple for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer List or Set or Tuple for
                ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        element: TypeShape = atomic(name="Never")
        for item in node.elts:
            element = join_types(
                left=element,
                right=self._infer(node=item, env=env, narrowing=narrowing),
            )
        return TypeShape(
            name="tuple"
            if isinstance(node, Tuple)
            else "set"
            if isinstance(node, Set)
            else "list",
            arguments=(element,),
        )

    def infer_set(
        self,
        node: List | Set | Tuple,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Alias of ``infer_list`` for Set.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while alias of ``infer_list`` for Set.

        Returns:
            TypeShape produced by this operation.

        """
        return self.infer_list(node, env, narrowing)

    def infer_tuple(
        self,
        node: List | Set | Tuple,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Alias of ``infer_list`` for Tuple.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while alias of ``infer_list`` for Tuple.

        Returns:
            TypeShape produced by this operation.

        """
        return self.infer_list(node, env, narrowing)

    def infer_dict(
        self,
        node: Dict,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Dict for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Dict for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        key: TypeShape = atomic(name="Never")
        value: TypeShape = atomic(name="Never")
        for k, v in zip(node.keys, node.values, strict=True):
            key = (
                join_types(
                    left=key,
                    right=self._infer(node=k, env=env, narrowing=narrowing),
                )
                if k is not None
                else atomic(name="Unknown")
            )
            value = join_types(
                left=value,
                right=self._infer(node=v, env=env, narrowing=narrowing),
            )
        return TypeShape(name="dict", arguments=(key, value))

    def infer_subscript(
        self,
        node: Subscript,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Subscript for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Subscript for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        container: TypeShape = self._infer(
            node=node.value,
            env=env,
            narrowing=narrowing,
        )
        self._infer(node=node.slice, env=env, narrowing=narrowing)
        typed_dict: ClassContract | None = self.contracts.classes.get(
            container.name,
        )
        if (
            typed_dict is not None
            and typed_dict.is_typed_dict
            and isinstance(node.slice, Constant)
            and isinstance(node.slice.value, str)
        ):
            field: TypeExpression | None = self.contracts.class_member(
                owner=typed_dict.name,
                name=node.slice.value,
            )
            if field is not None:
                result = type_shape(expression=field)
        if (
            result.name == "Unknown"
            and container.name in ("list", "set", "tuple")
            and container.arguments
        ):
            result = container.arguments[0]
        elif (
            container.name == "dict"
            and len(container.arguments) == Constants.pair_size
        ):
            result = container.arguments[1]
        elif result.name == "Unknown" and container.name == "str":
            result = atomic(name="str")
        elif result.name == "Unknown" and container.name == "bytes":
            result = atomic(name="int")
        return result

    def infer_await(
        self,
        node: Await,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Await for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Await for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        awaited: TypeShape = self._infer(
            node=node.value,
            env=env,
            narrowing=narrowing,
        )
        if awaited.name in ("Awaitable", "Coroutine") and awaited.arguments:
            result = awaited.arguments[-1]
        return result

    def infer_namedexpr(
        self,
        node: NamedExpr,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer NamedExpr for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer NamedExpr for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        result = self._infer(node=node.value, env=env, narrowing=narrowing)
        self._write(target=node.target, shape=result, env=env, origin=node)
        return result

    def infer_ifexp(
        self,
        node: IfExp,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer IfExp for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer IfExp for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        self._infer(node=node.test, env=env, narrowing=narrowing)
        true_narrow: dict[str, TypeShape] = self._narrow(
            test=node.test,
            yes=True,
        )
        false_narrow: dict[str, TypeShape] = self._narrow(
            test=node.test,
            yes=False,
        )
        return join_types(
            left=self._infer(
                node=node.body,
                env=env.copy(),
                narrowing={**(narrowing or {}), **true_narrow},
            ),
            right=self._infer(
                node=node.orelse,
                env=env.copy(),
                narrowing={**(narrowing or {}), **false_narrow},
            ),
        )

    def infer_compare(
        self,
        node: Compare | BoolOp | UnaryOp,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Compare or BoolOp or UnaryOp for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Compare or BoolOp or UnaryOp
                for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        for child in iter_child_nodes(node=node):
            self._infer(node=child, env=env, narrowing=narrowing)
        return (
            atomic(name="bool")
            if isinstance(node, Compare)
            or (isinstance(node, UnaryOp) and isinstance(node.op, Not))
            else atomic(name="Unknown")
        )

    def infer_boolop(
        self,
        node: Compare | BoolOp | UnaryOp,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Alias of ``infer_compare`` for BoolOp.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while alias of ``infer_compare`` for
                BoolOp.

        Returns:
            TypeShape produced by this operation.

        """
        return self.infer_compare(node, env, narrowing)

    def infer_unaryop(
        self,
        node: Compare | BoolOp | UnaryOp,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Alias of ``infer_compare`` for UnaryOp.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while alias of ``infer_compare`` for
                UnaryOp.

        Returns:
            TypeShape produced by this operation.

        """
        return self.infer_compare(node, env, narrowing)

    def infer_binop(
        self,
        node: BinOp,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer BinOp for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer BinOp for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        left: TypeShape = self._infer(
            node=node.left,
            env=env,
            narrowing=narrowing,
        )
        right: TypeShape = self._infer(
            node=node.right,
            env=env,
            narrowing=narrowing,
        )
        if left.name in ("int", "float", "complex", "bool") and right.name in (
            "int",
            "float",
            "complex",
            "bool",
        ):
            result = join_types(left=left, right=right)
        elif (
            isinstance(node.op, Add)
            and left == right
            and (left.name in ("str", "bytes", "list", "tuple"))
        ):
            result = left
        return result

    def infer_attribute(
        self,
        node: Attribute,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Attribute for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Attribute for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        receiver: TypeShape = self._infer(
            node=node.value,
            env=env,
            narrowing=narrowing,
        )
        cls: ClassContract | None = self.contracts.classes.get(
            receiver.name,
        ) or (
            self.contracts.classes.get(node.value.id)
            if isinstance(node.value, Name)
            else None
        )
        if cls is not None:
            result = self._class_attribute_type(contract=cls, node=node)
        if result.name == "Unknown":
            method: tuple[str, str, bool] | None = self._method_receivers.get(
                self.identities.node_id(node=node),
            )
            identity: int = self.identities.node_id(node=node)
            if (
                method is not None
                and isinstance(node.value, Name)
                and node.value.id == method[1]
                and identity not in self._self_attr_active
            ):
                self._self_attr_active.add(identity)
                try:
                    result = self._self_attribute_type(
                        class_name=method[0],
                        attr=node.attr,
                        node=node,
                        instance=not method[2],
                    )
                finally:
                    self._self_attr_active.discard(identity)
        if (
            result.name == "Unknown"
            and receiver.name in ("list", "dict", "set")
            and (node.attr in Constants.container_methods)
        ):
            result = TypeShape(name="method", arguments=(receiver,))
        return result

    def infer_call(
        self,
        node: Call,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
        /,
    ) -> TypeShape:
        """Infer Call for ``_infer``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer Call for ``_infer``.

        Returns:
            TypeShape produced by this operation.

        """
        atomic(name="Unknown")
        return self._call(node=node, env=env, narrowing=narrowing)

    def suite_assign(
        self,
        statement: Assign | AnnAssign,
        env: dict[int, TypeShape],
        _owner: str,
        /,
    ) -> bool:
        """Propagate an assignment's value into its targets.

        Args:
            _owner: Owner supplied as str for this operation.
            env: Env supplied as dict[int, TypeShape] for this operation.
            statement: The statement examined while propagate an assignment's
                value into its targets.

        Returns:
            Whether the requested condition holds.

        """
        self._declare_annotation(statement=statement)
        value: AST | None = statement.value
        if value is None:
            return False
        changed: bool = False
        shape: TypeShape = self._infer(node=value, env=env)
        targets: tuple[AST, ...] = (
            tuple(statement.targets)
            if isinstance(statement, Assign)
            else (statement.target,)
        )
        for target in targets:
            if isinstance(target, Name):
                sid: int | None = self._symbol_id(node=target)
                if sid is not None and sid in self.declarations:
                    changed = (
                        self._backward(
                            node=value,
                            required=self.declarations[sid],
                            env=env,
                            origin=statement,
                        )
                        or changed
                    )
            changed = (
                self._write(
                    target=target,
                    shape=shape,
                    env=env,
                    origin=statement,
                )
                or changed
            )
        return changed

    def suite_annassign(
        self,
        statement: AnnAssign,
        env: dict[int, TypeShape],
        owner: str,
        /,
    ) -> bool:
        """Propagate an annotated assignment (see ``suite_assign``).

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statement: The statement examined while propagate an annotated
                assignment (see ``suite_assign``).

        Returns:
            Whether the requested condition holds.

        """
        return self.suite_assign(statement, env, owner)

    def suite_augassign(
        self,
        statement: AugAssign,
        env: dict[int, TypeShape],
        _owner: str,
        /,
    ) -> bool:
        """Join an augmented assignment's value into its target.

        Args:
            _owner: Owner supplied as str for this operation.
            env: Env supplied as dict[int, TypeShape] for this operation.
            statement: The statement examined while join an augmented
                assignment's value into its target.

        Returns:
            Whether the requested condition holds.

        """
        old: TypeShape = self._infer(node=statement.target, env=env)
        new: TypeShape = self._infer(node=statement.value, env=env)
        return self._write(
            target=statement.target,
            shape=join_types(left=old, right=new),
            env=env,
            origin=statement,
        )

    def suite_expr(
        self,
        statement: Expr,
        env: dict[int, TypeShape],
        _owner: str,
        /,
    ) -> bool:
        """Infer an expression statement for its effects.

        Args:
            _owner: Owner supplied as str for this operation.
            env: Env supplied as dict[int, TypeShape] for this operation.
            statement: The statement examined while infer an expression
                statement for its effects.

        Returns:
            Whether the requested condition holds.

        """
        self._infer(node=statement.value, env=env)
        return False

    def suite_assert(
        self,
        statement: Assert,
        env: dict[int, TypeShape],
        _owner: str,
        /,
    ) -> bool:
        """Narrow names by an assertion's test.

        Args:
            _owner: Owner supplied as str for this operation.
            env: Env supplied as dict[int, TypeShape] for this operation.
            statement: The statement examined while narrow names by an
                assertion's test.

        Returns:
            Whether the requested condition holds.

        """
        self._infer(node=statement.test, env=env)
        self._apply_narrowing(
            test=statement.test,
            narrowing=self._narrow(test=statement.test, yes=True),
            env=env,
        )
        return False

    def suite_return(
        self,
        statement: Return,
        env: dict[int, TypeShape],
        owner: str,
        /,
    ) -> bool:
        """Join a returned value into the function's return type.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statement: The statement examined while join a returned value into
                the function's return type.

        Returns:
            Whether the requested condition holds.

        """
        changed: bool = False
        shape: TypeShape = (
            self._infer(node=statement.value, env=env)
            if statement.value is not None
            else atomic(name="None")
        )
        if statement.value is not None and owner in self._return_types:
            changed = self._backward(
                node=statement.value,
                required=self._return_types[owner],
                env=env,
                origin=statement,
            )
        old: TypeShape = self._return_types.get(owner, atomic(name="Never"))
        updated: TypeShape = join_types(left=old, right=shape)
        if updated != old:
            self._return_types[owner] = updated
            for consumer in self._call_edges.get(owner, set()):
                self._schedule(name=consumer)
            changed = True
        return changed

    def suite_if(
        self,
        statement: If,
        env: dict[int, TypeShape],
        owner: str,
        /,
    ) -> bool:
        """Analyze both branches and join their environments.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statement: The statement examined while analyze both branches and
                join their environments.

        Returns:
            Whether the requested condition holds.

        """
        self._infer(node=statement.test, env=env)
        true_env: dict[int, TypeShape] = dict(env)
        false_env: dict[int, TypeShape] = dict(env)
        self._apply_narrowing(
            test=statement.test,
            narrowing=self._narrow(test=statement.test, yes=True),
            env=true_env,
        )
        changed: bool = self._suite(
            statements=statement.body,
            env=true_env,
            owner=owner,
        )
        changed = (
            self._suite(
                statements=statement.orelse,
                env=false_env,
                owner=owner,
            )
            or changed
        )
        for sid in true_env.keys() | false_env.keys():
            env[sid] = join_types(
                left=true_env.get(sid, atomic(name="Never")),
                right=false_env.get(sid, atomic(name="Never")),
            )
        return changed

    def suite_while(
        self,
        statement: While,
        env: dict[int, TypeShape],
        owner: str,
        /,
    ) -> bool:
        """Analyze a loop body once and join it with the entry state.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statement: The statement examined while analyze a loop body once
                and join it with the entry state.

        Returns:
            Whether the requested condition holds.

        """
        self._infer(node=statement.test, env=env)
        after: dict[int, TypeShape] = dict(env)
        changed: bool = self._suite(
            statements=statement.body,
            env=after,
            owner=owner,
        )
        for sid, shape in after.items():
            env[sid] = join_types(
                left=env.get(sid, atomic(name="Never")),
                right=shape,
            )
        return changed

    def suite_functiondef(
        self,
        statement: FunctionDef | AsyncFunctionDef,
        _env: dict[int, TypeShape],
        _owner: str,
        /,
    ) -> bool:
        """Queue a nested function for its own analysis.

        Args:
            _env: Env supplied as dict[int, TypeShape] for this operation.
            _owner: Owner supplied as str for this operation.
            statement: The statement examined while queue a nested function for
                its own analysis.

        Returns:
            Whether the requested condition holds.

        """
        self._schedule(name=statement.name)
        return False

    def suite_asyncfunctiondef(
        self,
        statement: AsyncFunctionDef,
        env: dict[int, TypeShape],
        owner: str,
        /,
    ) -> bool:
        """Queue a nested async function (see ``suite_functiondef``).

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statement: The statement examined while queue a nested async
                function (see ``suite_functiondef``).

        Returns:
            Whether the requested condition holds.

        """
        return self.suite_functiondef(statement, env, owner)

    def infer_node(self, *, node: AST) -> TypeInference:
        """Return a current syntax node's type and supporting evidence.

        Args:
            node: The node examined while return a current syntax node's type
                and supporting evidence.

        Returns:
            TypeInference produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        occurrence: Occurrence | None = self.scopes.occurrences.get(identity)
        sid: int | None = (
            occurrence.symbol_id if occurrence is not None else None
        )
        return TypeInference(
            inferred=self.node_types.get(
                identity,
                self.types.get(sid, atomic(name="Unknown")),
            )
            if sid is not None
            else self.node_types.get(identity, atomic(name="Unknown")),
            evidence=tuple(self.proofs.get(sid, ()))
            if sid is not None
            else tuple(self.node_proofs.get(identity, ())),
            declared=self.declarations.get(sid) if sid is not None else None,
            conflicts=tuple(sorted(self.conflicts.get(sid, ())))
            if sid is not None
            else (),
            stable=self.statistics.converged,
        )

    def infer_symbol(self, *, symbol_id: int) -> TypeInference:
        """Return the aggregated inferred type and declaration of a symbol.

        Args:
            symbol_id: Symbol id supplied as int for this operation.

        Returns:
            TypeInference produced by this operation.

        """
        return TypeInference(
            inferred=self.types.get(symbol_id, atomic(name="Unknown")),
            evidence=tuple(self.proofs.get(symbol_id, ())),
            declared=self.declarations.get(symbol_id),
            conflicts=tuple(sorted(self.conflicts.get(symbol_id, ()))),
            stable=self.statistics.converged,
        )

    @staticmethod
    def _enum_value_type(
        *,
        contract: ClassContract,
        node: Attribute,
    ) -> TypeShape:
        """Type of ``Enum.MEMBER.value`` or of a generic enum ``.value``.

        Args:
            contract: Class contract supplying enum member declarations.
            node: The node examined while type of ``Enum.MEMBER.value`` or of a
                generic enum ``.value``.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        if (
            isinstance(node.value, Attribute)
            and isinstance(node.value.value, Name)
            and (node.value.value.id == contract.name)
        ):
            for declaration in contract.node.body:
                if isinstance(declaration, Assign) and any(
                    isinstance(target, Name) and target.id == node.value.attr
                    for target in declaration.targets
                ):
                    if isinstance(declaration.value, Constant):
                        result = atomic(
                            name=type(declaration.value.value).__name__,
                        )
                    break
        if result.name != "Unknown":
            return result
        parent_bases: frozenset[str] = frozenset(
            base.split(sep=".")[-1] for base in contract.bases
        )
        if "IntEnum" in parent_bases or "IntFlag" in parent_bases:
            return atomic(name="int")
        if "StrEnum" in parent_bases:
            return atomic(name="str")
        return result

    def _scan_type_variables(self) -> None:
        """Record declared type variables, their bounds and PEP 695 params."""
        for statement in self.root.body:
            if (
                isinstance(statement, Assign)
                and isinstance(statement.value, Call)
                and isinstance(statement.value.func, Name)
                and (
                    statement.value.func.id
                    in ("TypeVar", "ParamSpec", "TypeVarTuple")
                )
            ):
                for target in statement.targets:
                    if isinstance(target, Name):
                        self._type_variables.add(target.id)
                        bounds: list[TypeShape] = [
                            _hint(node=argument)
                            for argument in statement.value.args[1:]
                        ]
                        bounds.extend(
                            _hint(node=argument.value)
                            for argument in statement.value.keywords
                            if argument.arg == "bound"
                        )
                        if bounds:
                            self._type_variable_bounds[target.id] = tuple(
                                bounds,
                            )
            elif isinstance(
                statement,
                (FunctionDef, AsyncFunctionDef, ClassDef),
            ):
                self._type_variables.update(
                    type_param_name
                    for param in statement.type_params
                    if (
                        type_param_name := read_attribute(
                            node=param,
                            name="name",
                            kind=str,
                        )
                    )
                    is not None
                )
                self._type_variable_bounds.update(
                    (param.name, (_hint(node=param.bound),))
                    for param in statement.type_params
                    if isinstance(param, TypeVar) and param.bound is not None
                )

    def _index_nodes(self) -> None:
        """Index every scoped node and the symbols its names resolve to."""
        for identity, node in self.scopes.node_index.items():
            self._nodes[identity] = node
            self._scopes[identity] = self.scopes.node_scopes.get(
                identity,
                self.scopes.root_id,
            )
            occurrence: Occurrence | None = self.scopes.occurrences.get(
                identity,
            )
            if (
                isinstance(node, Name)
                and occurrence is not None
                and (occurrence.symbol_id is not None)
            ):
                self._symbol_by_name[self._scopes[identity], node.id] = (
                    occurrence.symbol_id
                )
        for symbol in self.scopes.symbols.values():
            self._symbol_by_name[symbol.scope_id, symbol.name] = symbol.id

    def _index_imports(self) -> None:
        """Map imported local names to their qualified origins."""
        for statement in self.root.body:
            if isinstance(statement, Import):
                for item in statement.names:
                    self._imports[
                        item.asname or item.name.split(sep=".")[0]
                    ] = (
                        item.name
                        if item.asname
                        else item.name.split(sep=".")[0]
                    )
            elif (
                isinstance(statement, ImportFrom)
                and statement.module is not None
            ):
                for item in statement.names:
                    if item.name != "*":
                        self._imports[item.asname or item.name] = (
                            f"{statement.module}.{item.name}"
                        )

    def _index_function(
        self,
        *,
        function: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Register one function's parameters, declared types and returns.

        Args:
            function: The function examined while register one function's
                parameters, declared types and returns.

        """
        parameter_nodes: tuple[arg, ...] = (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
        parameter_ids: list[int] = []
        for parameter in parameter_nodes:
            symbol_id: int | None = self._symbol_id(node=parameter)
            if symbol_id is None:
                continue
            parameter_ids.append(symbol_id)
            self._function_parameters[function.name, parameter.arg] = symbol_id
            if parameter.annotation is not None:
                self._declare(
                    symbol_id=symbol_id,
                    shape=_hint(node=parameter.annotation),
                    node=parameter,
                )
        self._parameters[function.name] = tuple(parameter_ids)
        self._return_types[function.name] = (
            _hint(node=function.returns)
            if function.returns is not None
            else atomic(name="Never")
        )
        self._calls[function.name] = []

    def _index_calls(self) -> None:
        """Attribute nodes to owning functions and record local call edges."""
        self._calls["<module>"] = []
        for name, function in self._definitions.items():
            self._owner[self.identities.node_id(node=function)] = name
            for node in walk(node=function):
                self._owner[self.identities.node_id(node=node)] = name
        for node in walk(node=self.root):
            if (
                isinstance(node, Call)
                and isinstance(node.func, Name)
                and (node.func.id in self._definitions)
            ):
                owner: str = self._owner.get(
                    self.identities.node_id(node=node),
                    "<module>",
                )
                self._calls.setdefault(owner, []).append(node)
                self._call_edges.setdefault(node.func.id, set()).add(owner)

    def _index_annotated_assignments(self) -> None:
        """Declare the annotated type of every annotated assignment."""
        for node in walk(node=self.root):
            if isinstance(node, AnnAssign) and isinstance(node.target, Name):
                sid: int | None = self._symbol_id(node=node.target)
                if sid is not None:
                    self._declare(
                        symbol_id=sid,
                        shape=_hint(node=node.annotation),
                        node=node,
                    )

    @staticmethod
    def _self_target(
        *,
        target: AST,
        receiver: str,
    ) -> Attribute | None:
        """Return ``target`` when it is ``<receiver>.<attr>``.

        Args:
            receiver: Receiver supplied as str for this operation.
            target: The target examined while return ``target`` when it is
                ``<receiver>.<attr>``.

        Returns:
            Attribute | None produced by this operation.

        """
        if (
            isinstance(target, Attribute)
            and isinstance(target.value, Name)
            and target.value.id == receiver
        ):
            return target
        return None

    def _index_class_assignments(self, *, _cls: ClassDef) -> None:
        """Record class-level ``name = value`` assignments.

        Args:
            _cls: The class definition to index.

        """
        for item in _cls.body:
            if not isinstance(item, Assign):
                continue
            for target in item.targets:
                if isinstance(target, Name):
                    self._class_assignments.setdefault(
                        (_cls.name, target.id),
                        [],
                    ).append(item.value)

    def _index_method(
        self,
        *,
        _cls: ClassDef,
        item: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Index one method's parameters and register its receiver.

        Args:
            _cls: Class definition.
            item: Method definition.

        """
        parameters: tuple[arg, ...] = (
            *item.args.posonlyargs,
            *item.args.args,
            *item.args.kwonlyargs,
        )
        self._method_nodes.append(item)
        if not parameters:
            return
        for parameter in parameters:
            if parameter.annotation is not None:
                sid: int | None = self._symbol_id(node=parameter)
                if sid is not None:
                    self._declare(
                        symbol_id=sid,
                        shape=_hint(node=parameter.annotation),
                        node=parameter,
                    )
        decorators: frozenset[str] = frozenset(
            (
                decorator.id
                if isinstance(decorator, Name)
                else decorator.attr
                if isinstance(decorator, Attribute)
                else ""
            )
            for decorator in item.decorator_list
        )
        if "staticmethod" in decorators:
            return
        receiver: str = parameters[0].arg
        is_classmethod: bool = "classmethod" in decorators
        for node in walk(node=item):
            self._method_receivers[self.identities.node_id(node=node)] = (
                _cls.name,
                receiver,
                is_classmethod,
            )

    def _index_methods(self) -> None:
        """Index method receivers, parameter declarations and self writes."""
        for cls in walk(node=self.root):
            if not isinstance(cls, ClassDef):
                continue
            self._index_class_assignments(_cls=cls)
            for item in cls.body:
                if isinstance(item, (FunctionDef, AsyncFunctionDef)):
                    self._index_method(_cls=cls, item=item)
        self._index_self_writes()

    def _index_self_writes(self) -> None:
        """Record ``self.attr`` writes inside every indexed method."""
        for node in walk(node=self.root):
            context: tuple[str, str, bool] | None = self._method_receivers.get(
                self.identities.node_id(node=node),
            )
            if context is not None and not context[2]:
                self._record_self_write(node=node, context=context)

    def _record_self_write(
        self,
        *,
        node: AST,
        context: tuple[str, str, bool],
    ) -> None:
        """Record one ``self.attr = value`` or annotated write.

        Args:
            node: Assignment statement inside a method.
            context: ``(class name, receiver, is classmethod)`` of the
                enclosing method.

        """
        class_name, receiver, _ = context
        if isinstance(node, Assign):
            for target in node.targets:
                attribute: Attribute | None = self._self_target(
                    target=target,
                    receiver=receiver,
                )
                if attribute is not None:
                    self._instance_attributes.setdefault(
                        (class_name, attribute.attr),
                        [],
                    ).append(node.value)
        elif isinstance(node, AnnAssign):
            attribute = self._self_target(
                target=node.target,
                receiver=receiver,
            )
            if attribute is None:
                return
            self._instance_annotations[(class_name, attribute.attr)] = (
                TypeExpressionCodec.from_ast(node=node.annotation)
            )
            if node.value is not None:
                self._instance_attributes.setdefault(
                    (class_name, attribute.attr),
                    [],
                ).append(node.value)

    def _self_attribute_type(
        self,
        *,
        class_name: str,
        attr: str,
        node: Attribute,
        instance: bool,
    ) -> TypeShape:
        """Type of ``self.attr`` inside a method of a known class.

        Args:
            attr: Attribute supplied as str for this operation.
            class_name: Class name supplied as str for this operation.
            instance: Instance supplied as bool for this operation.
            node: The node examined while type of ``self.attr`` inside a
                method of a known class.

        Returns:
            TypeShape produced by this operation.

        """
        cls: ClassContract | None = self.contracts.classes.get(class_name)
        if cls is not None:
            result: TypeShape = self._class_attribute_type(
                contract=cls,
                node=node,
            )
            if result.name != "Unknown":
                return result
        if not instance:
            return atomic(name="Unknown")
        annotation: TypeExpression | None = self._instance_annotations.get(
            (class_name, attr),
        )
        if annotation is not None:
            return type_shape(expression=annotation)
        values: list[AST] | None = self._instance_attributes.get(
            (class_name, attr),
        )
        if not values:
            values = self._class_assignments.get((class_name, attr))
        if not values:
            return atomic(name="Unknown")
        result = atomic(name="Never")
        for value in values:
            result = join_types(
                left=result,
                right=self._infer(node=value, env={}, narrowing=None),
                promote=False,
            )
        return result

    def _build_index(self) -> None:
        """Register node and symbol indexes, including callable contracts."""
        self._index_nodes()
        self._index_imports()
        self._definitions = {
            statement.name: statement
            for statement in self.root.body
            if isinstance(statement, (FunctionDef, AsyncFunctionDef))
        }
        for function in self._definitions.values():
            self._index_function(function=function)
        self._index_calls()
        self._index_annotated_assignments()
        self._index_methods()
        self._seed_graph_annotations()
        self._work = deque(iterable=["<module>", *self._definitions])
        self._queued = set(self._work)

    def _seed_graph_annotations(self) -> None:
        """Import validated graph evidence into native type constraints.

        Proposals retain their original node identity. They do not masquerade
        as explicit annotations, and they do not replace existing contracts.
        """
        for proposal in self.graph_conversion:
            target: AST = proposal.target
            identity: int = self.identities.node_id(node=target)
            evidence: TypeEvidence = self._evidence(
                node=target,
                kind="graph-inference",
                description=(
                    f"graph conversion suggests "
                    f"{proposal.annotation}"
                    f" at "
                    f"{'.'.join(proposal.site)}"
                ),
            )
            if proposal.role == "parameter" and isinstance(target, arg):
                sid: int | None = self._symbol_id(node=target)
                if sid is not None and sid not in self.declarations:
                    self._add(
                        symbol_id=sid,
                        shape=proposal.annotation,
                        evidence=evidence,
                    )
            elif proposal.role == "return" and isinstance(
                target,
                (FunctionDef, AsyncFunctionDef),
            ):
                if (
                    target.returns is None
                    and target.name in self._return_types
                ):
                    self._return_types[target.name] = join_types(
                        left=self._return_types[target.name],
                        right=proposal.annotation,
                    )
                    self.node_types[identity] = proposal.annotation
                    self.node_proofs.setdefault(identity, []).append(evidence)
            elif proposal.role == "variable" and isinstance(target, Assign):
                if len(target.targets) == 1 and isinstance(
                    target.targets[0],
                    Name,
                ):
                    sid = self._symbol_id(node=target.targets[0])
                    if sid is not None and sid not in self.declarations:
                        self._add(
                            symbol_id=sid,
                            shape=proposal.annotation,
                            evidence=evidence,
                        )

    def _symbol_id(self, *, node: AST) -> int | None:
        """Resolve a declaration or reference via the scope index.

        Args:
            node: The node examined while resolve a declaration or reference
                via the scope index.

        Returns:
            int | None produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        occurrence: Occurrence | None = self.scopes.occurrences.get(identity)
        if occurrence is not None and occurrence.symbol_id is not None:
            return occurrence.symbol_id
        if isinstance(node, arg):
            scope_id: int = self.scopes.node_scopes.get(
                identity,
                self.scopes.root_id,
            )
            return self.scopes.resolve(name=node.arg, scope_id=scope_id)
        return None

    def _evidence(
        self,
        *,
        node: AST,
        kind: str,
        description: str,
        dependencies: tuple[int, ...] = (),
    ) -> TypeEvidence:
        """Create evidence with a stable source node identity.

        Args:
            dependencies: Dependencies supplied as tuple[int, ...] for this
                operation.
            description: Description supplied as str for this operation.
            kind: Kind supplied as str for this operation.
            node: The node examined while create evidence with a stable source
                node identity.

        Returns:
            TypeEvidence produced by this operation.

        """
        return TypeEvidence(
            node_id=self.identities.node_id(node=node),
            kind=kind,
            description=description,
            dependencies=dependencies,
        )

    def _declare(self, *, symbol_id: int, shape: TypeShape, node: AST) -> None:
        """Record an explicit annotation without overwriting observed types.

        Args:
            node: The node examined while record an explicit annotation without
                overwriting observed types.
            shape: Shape supplied as TypeShape for this operation.
            symbol_id: Symbol id supplied as int for this operation.

        """
        self.declarations[symbol_id] = shape
        self._add(
            symbol_id=symbol_id,
            shape=shape,
            evidence=self._evidence(
                node=node,
                kind="annotation",
                description=(f"declared {shape}"),
            ),
            contract=True,
        )

    def _add(
        self,
        *,
        symbol_id: int,
        shape: TypeShape,
        evidence: TypeEvidence,
        contract: bool = False,
    ) -> bool:
        """Join new information, keeping provenance and conflicts.

        Args:
            contract: Contract supplied as bool for this operation.
            evidence: Evidence supplied as TypeEvidence for this operation.
            shape: Shape supplied as TypeShape for this operation.
            symbol_id: Symbol id supplied as int for this operation.

        Returns:
            Whether the requested condition holds.

        """
        old: TypeShape = self.types.get(symbol_id, atomic(name="Never"))
        if contract and symbol_id not in self.types:
            new: TypeShape = shape
        else:
            new = join_types(left=old, right=shape)
        changed: bool = old != new
        if changed:
            self.types[symbol_id] = new
        proofs: list[TypeEvidence] = self.proofs.setdefault(symbol_id, [])
        if evidence not in proofs and len(proofs) < self.max_evidence:
            proofs.append(evidence)
        declared: TypeShape | None = self.declarations.get(symbol_id)
        if (
            declared is not None
            and (not contract)
            and (shape.name not in ("Unknown", "Never"))
            and (shape != declared)
            and (
                not (
                    shape.name == declared.name
                    and all(item.name == "Never" for item in shape.arguments)
                )
            )
        ) and (
            not (declared.name == "float" and shape.name in ("int", "bool"))
        ):
            self.conflicts.setdefault(symbol_id, set()).add(
                f"observed {shape} versus declared {declared}",
            )
        return changed

    def _record(
        self,
        *,
        node: AST,
        shape: TypeShape,
        kind: str,
        dependencies: tuple[int, ...] = (),
    ) -> TypeShape:
        """Store local inferred syntax shape and causal evidence.

        Args:
            dependencies: Dependencies supplied as tuple[int, ...] for this
                operation.
            kind: Kind supplied as str for this operation.
            node: The node examined while store local inferred syntax shape and
                causal evidence.
            shape: Shape supplied as TypeShape for this operation.

        Returns:
            TypeShape produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        self.node_types[identity] = shape
        evidence: TypeEvidence = self._evidence(
            node=node,
            kind=kind,
            description=(f"{type(node).__name__} yields {shape}"),
            dependencies=dependencies,
        )
        found: list[TypeEvidence] = self.node_proofs.setdefault(identity, [])
        if evidence not in found and len(found) < self.max_evidence:
            found.append(evidence)
        if shape.name == "WidenedUnknown":
            widening: TypeEvidence = self._evidence(
                node=node,
                kind="widening",
                description=(
                    "bounded type precision lost to guarantee convergence"
                ),
            )
            if widening not in found and len(found) < self.max_evidence:
                found.append(widening)
        return shape

    def _infer(
        self,
        *,
        node: AST,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None = None,
    ) -> TypeShape:
        """Infer an expression without executing user-defined operations.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while infer an expression without executing
                user-defined operations.

        Returns:
            TypeShape produced by this operation.

        """
        result: TypeShape = atomic(name="Unknown")
        for handler_name in handler_names(node=node, prefix="infer_"):
            handler: Callable[..., TypeShape] | None = getattr(
                self,
                handler_name,
                None,
            )
            if handler is not None:
                result = handler(node, env, narrowing)
                break
        return self._record(node=node, shape=result, kind="expression")

    def _class_attribute_type(
        self,
        *,
        contract: ClassContract,
        node: Attribute,
    ) -> TypeShape:
        """Type of an attribute read through a known class contract.

        Args:
            contract: Class contract supplying attribute type information.
            node: The node examined while type of an attribute read through a
                known class contract.

        Returns:
            TypeShape produced by this operation.

        """
        if contract.is_enum:
            if any((field == node.attr for field, _ in contract.members)):
                return atomic(name=contract.name)
            if node.attr == "name":
                return atomic(name="str")
            if node.attr == "value":
                return self._enum_value_type(contract=contract, node=node)
        declared_field: TypeExpression | None = self.contracts.class_member(
            owner=contract.name,
            name=node.attr,
        )
        if declared_field is not None:
            return type_shape(expression=declared_field)
        properties: tuple[CallableContract, ...] = tuple(
            method
            for method in contract.methods
            if method.method_kind == "property"
            and method.qualified_name.endswith(f".{node.attr}")
        )
        if properties and properties[0].returns is not None:
            return type_shape(expression=properties[0].returns)
        return atomic(name="Unknown")

    def _narrow_none_test(
        self,
        *,
        test: AST,
        yes: bool,
    ) -> dict[str, TypeShape] | None:
        """Narrow ``x is None`` and ``x is not None``; ``None`` if not one.

        Args:
            test: Test supplied as AST for this operation.
            yes: Yes supplied as bool for this operation.

        Returns:
            dict[str, TypeShape] | None produced by this operation.

        """
        if not (
            isinstance(test, Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], (Is, IsNot))
            and isinstance(test.left, Name)
            and (len(test.comparators) == 1)
            and isinstance(test.comparators[0], Constant)
            and (test.comparators[0].value is None)
        ):
            return None
        found: TypeShape = self.types.get(
            self._symbol_id(node=test.left) or -1,
            atomic(name="Unknown"),
        )
        if yes == isinstance(test.ops[0], Is):
            return {test.left.id: atomic(name="None")}
        alternatives: tuple[TypeShape, ...] = (
            found.arguments if found.name == "union" else (found,)
        )
        remaining: tuple[TypeShape, ...] = tuple(
            item for item in alternatives if item.name != "None"
        )
        return (
            {test.left.id: union_shapes(shapes=remaining, promote=False)}
            if remaining
            else {}
        )

    def _guard_expectation(
        self,
        *,
        name: str,
        test: Call,
    ) -> tuple[TypeShape, bool] | None:
        """Return the expected type of an isinstance or guard call.

        Returns:
            The expected type and whether the negative branch may narrow.



        Args:
            name: Identifier of the name being resolved.
            test: Test supplied as Call for this operation.

        """
        if name == "isinstance" and len(test.args) == Constants.pair_size:
            arg: AST = test.args[1]
            expected: TypeShape = (
                union_shapes(
                    shapes=tuple(_hint(node=item) for item in arg.elts),
                    promote=False,
                )
                if isinstance(arg, Tuple)
                else _hint(node=arg)
            )
            return (expected, True)
        guards: tuple[TypeExpression, ...] = tuple(
            item.returns
            for item in self.contracts.variants(qualified_name=name)
            if item.returns is not None
            and item.returns.name.split(sep=".")[-1] in ("TypeGuard", "TypeIs")
            and item.returns.arguments
        )
        if not guards:
            return None
        return (
            union_shapes(
                shapes=tuple(
                    type_shape(expression=item.arguments[0]) for item in guards
                ),
                promote=False,
            ),
            all(item.name.split(sep=".")[-1] == "TypeIs" for item in guards),
        )

    def _select_alternatives(
        self,
        *,
        alternatives: tuple[TypeShape, ...],
        known: tuple[TypeShape, ...],
        matching: bool,
    ) -> tuple[TypeShape, ...]:
        """Keep alternatives that do (or do not) match any known type.

        Args:
            alternatives: Alternatives supplied as tuple[TypeShape, ...] for
                this operation.
            known: Known supplied as tuple[TypeShape, ...] for this operation.
            matching: Matching supplied as bool for this operation.

        Returns:
            tuple[TypeShape, ...] produced by this operation.

        """
        return tuple(
            item
            for item in alternatives
            if any(
                subtype(
                    actual=item,
                    expected=kind,
                    index=self.contracts,
                ).compatible
                is True
                for kind in known
            )
            == matching
        )

    def _narrow_call(self, *, test: Call, yes: bool) -> dict[str, TypeShape]:
        """Narrow ``isinstance`` and user-defined guard calls.

        Args:
            test: Test supplied as Call for this operation.
            yes: Yes supplied as bool for this operation.

        Returns:
            dict[str, TypeShape] produced by this operation.

        """
        if not isinstance(test.func, Name) or not test.args:
            return {}
        candidate: AST = test.args[0]
        if isinstance(candidate, NamedExpr):
            candidate = candidate.target
        guard: tuple[TypeShape, bool] | None = self._guard_expectation(
            name=test.func.id,
            test=test,
        )
        if not isinstance(candidate, Name) or guard is None:
            return {}
        expected, negative_supported = guard
        observed: TypeShape = self.types.get(
            self._symbol_id(node=candidate) or -1,
            atomic(name="Unknown"),
        )
        alternatives: tuple[TypeShape, ...] = (
            observed.arguments if observed.name == "union" else (observed,)
        )
        known: tuple[TypeShape, ...] = (
            expected.arguments if expected.name == "union" else (expected,)
        )
        if yes:
            selected: tuple[TypeShape, ...] = self._select_alternatives(
                alternatives=alternatives,
                known=known,
                matching=True,
            )
            return {
                candidate.id: union_shapes(shapes=selected, promote=False)
                if selected
                else expected,
            }
        if not negative_supported:
            return {}
        remaining: tuple[TypeShape, ...] = self._select_alternatives(
            alternatives=alternatives,
            known=known,
            matching=False,
        )
        return (
            {candidate.id: union_shapes(shapes=remaining, promote=False)}
            if remaining
            else {}
        )

    def _narrow(self, *, test: AST, yes: bool) -> dict[str, TypeShape]:
        """Narrow isinstance, TypeGuard, TypeIs and None tests safely.

        Args:
            test: Test supplied as AST for this operation.
            yes: Yes supplied as bool for this operation.

        Returns:
            dict[str, TypeShape] produced by this operation.

        """
        if isinstance(test, UnaryOp) and isinstance(test.op, Not):
            return self._narrow(test=test.operand, yes=not yes)
        none_result: dict[str, TypeShape] | None = self._narrow_none_test(
            test=test,
            yes=yes,
        )
        if none_result is not None:
            return none_result
        if isinstance(test, Call):
            return self._narrow_call(test=test, yes=yes)
        return {}

    def _write(
        self,
        *,
        target: AST,
        shape: TypeShape,
        env: dict[int, TypeShape],
        origin: AST,
    ) -> bool:
        """Apply a binding and register a producer-to-consumer causal proof.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            origin: Origin supplied as AST for this operation.
            shape: Shape supplied as TypeShape for this operation.
            target: The target examined while apply a binding and register a
                producer-to-consumer causal proof.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(target, Name):
            sid: int | None = self._symbol_id(node=target)
            if sid is None:
                return False
            declared: TypeShape | None = self.declarations.get(sid)
            env[sid] = (
                join_types(left=shape, right=declared)
                if declared is not None
                and shape.arguments
                and all(item.name == "Never" for item in shape.arguments)
                else shape
            )
            self._record(node=target, shape=env[sid], kind="assignment_target")
            return self._add(
                symbol_id=sid,
                shape=shape,
                evidence=self._evidence(
                    node=origin,
                    kind="assignment",
                    description=(f"assigned {shape}"),
                    dependencies=(self.identities.node_id(node=target),),
                ),
            )
        if (
            isinstance(target, (Tuple, List))
            and shape.name in ("tuple", "list")
            and shape.arguments
        ):
            changed: bool = False
            for item in target.elts:
                changed = (
                    self._write(
                        target=item,
                        shape=shape.arguments[0],
                        env=env,
                        origin=origin,
                    )
                    or changed
                )
            return changed
        return False

    def _import_is_unmodified(self, *, alias: str, node: AST) -> bool:
        """Reject imported contracts shadowed or rebound in lexical scope.

        Args:
            alias: Alias supplied as str for this operation.
            node: The node examined while reject imported contracts shadowed or
                rebound in lexical scope.

        Returns:
            Whether the requested condition holds.

        """
        origin: int | None = self.scopes.scope_symbols[
            self.scopes.root_id
        ].get(alias)
        current: int | None = self.scopes.resolve(
            name=alias,
            scope_id=self.scopes.node_scopes.get(
                self.identities.node_id(node=node),
                self.scopes.root_id,
            ),
        )
        if origin is None or current != origin:
            return False
        bindings: set[int] = self.scopes.symbol_bindings.get(origin, set())
        return bool(bindings) and all(
            self.scopes.bindings[identity].kind == "import"
            for identity in bindings
        )

    def _bind_keywords(
        self,
        *,
        node: Call,
        named: dict[str, TypeShape],
        infer_unpacked: bool,
    ) -> tuple[tuple[str | None, TypeShape], ...]:
        """Pair each keyword with its inferred type for signature binding.

        Args:
            infer_unpacked: Infer unpacked supplied as bool for this operation.
            named: Named supplied as dict[str, TypeShape] for this operation.
            node: The node examined while pair each keyword with its inferred
                type for signature binding.

        Returns:
            tuple[tuple[str | None, TypeShape], ...] produced by this
            operation.

        """
        unknown: TypeShape = atomic(name="Unknown")
        return tuple(
            (part.arg, named.get(part.arg, unknown))
            if part.arg is not None
            else (
                None,
                self._infer(node=part.value, env={}, narrowing=None)
                if infer_unpacked
                else unknown,
            )
            for part in node.keywords
        )

    def _argument_with_default_type(
        self,
        *,
        argument: BoundArgument,
    ) -> BoundArgument:
        """Give an omitted argument the type of its default or annotation.

        Args:
            argument: Argument supplied as BoundArgument for this operation.

        Returns:
            BoundArgument produced by this operation.

        """
        if argument.origin not in (
            ArgumentOrigin.DEFAULT,
            ArgumentOrigin.DEFAULT_FACTORY,
        ):
            return argument
        if argument.parameter.annotation is not None:
            types: tuple[TypeShape, ...] = (
                type_shape(expression=argument.parameter.annotation),
            )
        elif argument.parameter.default is not None:
            types = (
                self._infer(
                    node=argument.parameter.default,
                    env={},
                    narrowing=None,
                ),
            )
        else:
            types = ()
        return replace(argument, types=types)

    def _score_argument(
        self,
        *,
        argument: BoundArgument,
        generics: frozenset[str],
        assignments: dict[str, TypeShape],
    ) -> tuple[int, bool]:
        """Score one bound argument against its declared parameter type.

        Returns:
            The quality gained and whether the argument rejects the overload.



        Args:
            argument: Argument supplied as BoundArgument for this operation.
            assignments: Assignments supplied as dict[str, TypeShape] for this
                operation.
            generics: Generics supplied as frozenset[str] for this operation.

        """
        if (
            argument.origin
            in (ArgumentOrigin.DEFAULT, ArgumentOrigin.DEFAULT_FACTORY)
            or argument.parameter.annotation is None
            or (not argument.types)
        ):
            return (0, False)
        expected: TypeShape = type_shape(
            expression=argument.parameter.annotation,
        )
        if (
            expected.name.split(sep=".")[-1] == "Annotated"
            and expected.arguments
        ):
            expected = expected.arguments[0]
        quality: int = 0
        rejected: bool = False
        for source_node, actual in zip(
            argument.values,
            argument.types,
            strict=False,
        ):
            if (
                expected.name.split(sep=".")[-1] == "Literal"
                and expected.arguments
            ):
                if isinstance(source_node, Constant):
                    if repr(source_node.value) not in {
                        member.name for member in expected.arguments
                    }:
                        rejected = True
                    else:
                        quality += 4
                continue
            gained, refused = self._score_value(
                expected=expected,
                actual=actual,
                generics=generics,
                assignments=assignments,
            )
            quality += gained
            rejected = rejected or refused
        return (quality, rejected)

    def _score_value(
        self,
        *,
        expected: TypeShape,
        actual: TypeShape,
        generics: frozenset[str],
        assignments: dict[str, TypeShape],
    ) -> tuple[int, bool]:
        """Score one inferred value against an expected parameter type.

        Args:
            actual: Actual supplied as TypeShape for this operation.
            assignments: Assignments supplied as dict[str, TypeShape] for this
                operation.
            expected: Expected supplied as TypeShape for this operation.
            generics: Generics supplied as frozenset[str] for this operation.

        Returns:
            tuple[int, bool] produced by this operation.

        """
        if expected.name in generics or any(
            child.name in generics for child in expected.arguments
        ):
            unify(
                declared=expected,
                actual=actual,
                parameters=generics,
                bindings=assignments,
            )
            if expected.name in self._type_variable_bounds and all(
                subtype(
                    actual=actual,
                    expected=bound,
                    index=self.contracts,
                ).compatible
                is False
                for bound in self._type_variable_bounds[expected.name]
            ):
                return (0, True)
            return (1, False)
        compatible: Compatibility = subtype(
            actual=actual,
            expected=expected,
            index=self.contracts,
        )
        if compatible.compatible is False:
            return (0, True)
        if compatible.compatible is True:
            return (2 if actual == expected else 1, False)
        return (0, False)

    def _score_variant(
        self,
        *,
        signature: CallableContract,
        bound: BoundCall,
    ) -> tuple[int, dict[str, TypeShape]] | None:
        """Score a bound overload; ``None`` when any argument rejects it.

        Args:
            bound: Bound supplied as BoundCall for this operation.
            signature: Signature supplied as CallableContract for this
                operation.

        Returns:
            tuple[int, dict[str, TypeShape]] | None produced by this operation.

        """
        generics: frozenset[str] = frozenset(
            (*signature.type_parameters, *self._type_variables),
        )
        assignments: dict[str, TypeShape] = {}
        quality: int = 0
        for argument in bound.arguments:
            gained, rejected = self._score_argument(
                argument=argument,
                generics=generics,
                assignments=assignments,
            )
            if rejected:
                return None
            quality += gained
        return (quality, assignments)

    def _variant_return(
        self,
        *,
        signature: CallableContract,
        assignments: dict[str, TypeShape],
        receiver: TypeShape | None,
        constructor: str | None,
    ) -> TypeShape:
        """Specialize an overload's declared return for this call.

        Args:
            assignments: Assignments supplied as dict[str, TypeShape] for this
                operation.
            constructor: Constructor supplied as str | None for this operation.
            receiver: Receiver supplied as TypeShape | None for this operation.
            signature: Signature supplied as CallableContract for this
                operation.

        Returns:
            TypeShape produced by this operation.

        """
        raw_return: TypeShape = (
            type_shape(expression=signature.returns)
            if signature.returns is not None
            else self._return_types.get(
                signature.qualified_name,
                atomic(name="Unknown"),
            )
        )
        specialized: TypeShape = specialize(
            declared=raw_return,
            bindings={
                **assignments,
                "Self": receiver or atomic(name=constructor or "Unknown"),
            },
        )
        if (
            isinstance(signature.declaration, AsyncFunctionDef)
            and constructor is None
        ):
            return TypeShape(
                name="Coroutine",
                arguments=(
                    atomic(name="Unknown"),
                    atomic(name="Unknown"),
                    specialized,
                ),
            )
        return specialized

    def _publish_call_binding(self, *, node: Call, binding: BoundCall) -> None:
        """Store a call's binding and resolved signature on its node.

        Args:
            binding: Binding supplied as BoundCall for this operation.
            node: The node examined while store a call's binding and resolved
                signature on its node.

        """
        self.call_bindings[self.identities.node_id(node=node)] = binding
        write_attribute(node=node, name="call_binding", value=binding)
        write_attribute(
            node=node,
            name="resolved_signature",
            value=binding.signature,
        )
        write_attribute(
            node=node,
            name="call_arguments",
            value=binding.arguments,
        )

    def _record_unresolved_call(
        self,
        *,
        node: Call,
        variants: tuple[CallableContract, ...],
        arguments: CallArguments,
        receiver: TypeShape | None,
    ) -> None:
        """Describe a call no overload accepts, using the first variant.

        Args:
            arguments: Collection of arguments supplied for this operation.
            node: The node examined while describe a call no overload accepts,
                using the first variant.
            receiver: Receiver supplied as TypeShape | None for this operation.
            variants: Variants supplied as tuple[CallableContract, ...] for
                this operation.

        """
        if variants:
            unresolved: BoundCall = bind_signature(
                call=node,
                signature=variants[0],
                positional_types=arguments.positional,
                keyword_types=self._bind_keywords(
                    node=node,
                    named=arguments.named,
                    infer_unpacked=False,
                ),
                receiver_type=receiver,
            )
            self._publish_call_binding(node=node, binding=unresolved)
            write_attribute(
                node=node,
                name="type_conflicts",
                value=unresolved.errors
                or ("argument types violate available overload contracts",),
            )
        self._record(
            node=node,
            shape=atomic(name="Unknown"),
            kind="unresolved_call_contract",
        )

    def _annotate_argument_source(
        self,
        *,
        node: Call,
        source: AST,
        argument: BoundArgument,
    ) -> None:
        """Attach parameter metadata to an argument expression.

        Args:
            argument: Argument supplied as BoundArgument for this operation.
            node: The node examined while attach parameter metadata to an
                argument expression.
            source: The source examined while attach parameter metadata to an
                argument expression.

        """
        write_attribute(
            node=source,
            name="call_parameter_name",
            value=argument.name,
        )
        write_attribute(
            node=source,
            name="call_parameter_kind",
            value=argument.parameter.kind,
        )
        write_attribute(
            node=source,
            name="call_parameter_type",
            value=argument.parameter.annotation,
        )
        write_attribute(
            node=source,
            name="call_argument_origin",
            value=argument.origin,
        )
        if (
            argument.parameter.annotation is not None
            and argument.origin not in Constants.implicit_origins
        ):
            self._backward(
                node=source,
                required=type_shape(expression=argument.parameter.annotation),
                env={},
                origin=node,
            )

    def _propagate_parameter_types(
        self,
        *,
        node: Call,
        chosen: BoundCall,
        argument: BoundArgument,
    ) -> None:
        """Feed argument types into the callee's parameter symbols.

        Args:
            argument: Argument supplied as BoundArgument for this operation.
            chosen: Chosen supplied as BoundCall for this operation.
            node: The node examined while feed argument types into the callee's
                parameter symbols.

        """
        if not isinstance(
            chosen.signature.declaration,
            (FunctionDef, AsyncFunctionDef),
        ):
            return
        for actual in argument.types:
            parameter_node: AST | None = argument.parameter.declaration
            if (
                parameter_node is None
                or argument.origin in Constants.implicit_origins
            ):
                continue
            sid: int | None = self._symbol_id(node=parameter_node)
            if sid is not None and self._add(
                symbol_id=sid,
                shape=actual,
                evidence=self._evidence(
                    node=node,
                    kind="signature_argument",
                    description=(f"bound parameter {argument.name}"),
                ),
            ):
                owner: str = chosen.signature.qualified_name.split(sep=".")[0]
                if owner in self._definitions:
                    self._schedule(name=owner)

    def _commit_choice(self, *, node: Call, chosen: BoundCall) -> None:
        """Publish the winning overload and propagate its argument types.

        Args:
            chosen: Chosen supplied as BoundCall for this operation.
            node: The node examined while publish the winning overload and
                propagate its argument types.

        """
        self._publish_call_binding(node=node, binding=chosen)
        write_attribute(node=node, name="type_conflicts", value=())
        for argument in chosen.arguments:
            for source in argument.values:
                if argument.origin in (
                    ArgumentOrigin.DEFAULT,
                    ArgumentOrigin.DEFAULT_FACTORY,
                ):
                    continue
                self._annotate_argument_source(
                    node=node,
                    source=source,
                    argument=argument,
                )
            self._propagate_parameter_types(
                node=node,
                chosen=chosen,
                argument=argument,
            )

    def _contract_call(
        self,
        *,
        node: Call,
        variants: tuple[CallableContract, ...],
        arguments: CallArguments,
        receiver: TypeShape | None = None,
        constructor: str | None = None,
    ) -> TypeShape:
        """Select applicable overloads from named bindings and constraints.

        Args:
            arguments: Collection of arguments supplied for this operation.
            constructor: Constructor supplied as str | None for this operation.
            node: The node examined while select applicable overloads from
                named bindings and constraints.
            receiver: Receiver supplied as TypeShape | None for this operation.
            variants: Variants supplied as tuple[CallableContract, ...] for
                this operation.

        Returns:
            TypeShape produced by this operation.

        """
        candidates: list[
            tuple[int, CallableContract, BoundCall, TypeShape]
        ] = []
        for signature in variants:
            bound: BoundCall = bind_signature(
                call=node,
                signature=signature,
                positional_types=arguments.positional,
                keyword_types=self._bind_keywords(
                    node=node,
                    named=arguments.named,
                    infer_unpacked=True,
                ),
                receiver_type=receiver,
            )
            if not bound.valid:
                continue
            bound = replace(
                bound,
                arguments=tuple(
                    self._argument_with_default_type(argument=argument)
                    for argument in bound.arguments
                ),
            )
            scored: tuple[int, dict[str, TypeShape]] | None = (
                self._score_variant(
                    signature=signature,
                    bound=bound,
                )
            )
            if scored is None:
                continue
            quality, assignments = scored
            candidates.append(
                (
                    quality,
                    signature,
                    bound,
                    atomic(name=constructor)
                    if constructor is not None
                    else self._variant_return(
                        signature=signature,
                        assignments=assignments,
                        receiver=receiver,
                        constructor=constructor,
                    ),
                ),
            )
        if not candidates:
            self._record_unresolved_call(
                node=node,
                variants=variants,
                arguments=arguments,
                receiver=receiver,
            )
            return atomic(name="Unknown")
        best_score: int = max((score for score, _, _, _ in candidates))
        best: list[tuple[int, CallableContract, BoundCall, TypeShape]] = [
            item for item in candidates if item[0] == best_score
        ]
        if any((signature.is_overload for _, signature, _, _ in best)):
            best = [item for item in best if item[1].is_overload]
        self._commit_choice(node=node, chosen=best[0][2])
        answer: TypeShape = atomic(name="Never")
        for _, signature, _, shape in best:
            answer = join_types(left=answer, right=shape, promote=False)
            self._record(
                node=node,
                shape=shape,
                kind=(
                    f"signature:\
                        {signature.source_path or signature.qualified_name}"
                ),
            )
        return answer

    def _resolve_newtype(self, *, site: CallSite) -> TypeShape | None:
        """Type-check a ``NewType`` constructor call.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        name, args = (site.name, site.arguments.positional)
        if (
            name is None
            or name not in self.contracts.newtypes
            or len(args) != 1
        ):
            return None
        expected: TypeShape = type_shape(
            expression=self.contracts.newtypes[name],
        )
        if (
            subtype(
                actual=args[0],
                expected=expected,
                index=self.contracts,
            ).compatible
            is not False
        ):
            return self._record(
                node=site.node,
                shape=TypeShape(name=name),
                kind="NewType_constructor",
            )
        write_attribute(
            node=site.node,
            name="type_conflicts",
            value=((f"NewType {name} expects {expected}"),),
        )
        return atomic(name="Unknown")

    def _resolve_callable_variable(
        self,
        *,
        site: CallSite,
    ) -> TypeShape | None:
        """Use the ``Callable[[...], R]`` contract of a called variable.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        name, node = (site.name, site.node)
        if (
            name is None
            or name in self.contracts.functions
            or name in self.contracts.classes
        ):
            return None
        resolved: int | None = self._symbol_id(node=node.func)
        variable_shape: TypeShape = (
            site.env.get(
                resolved,
                self.types.get(resolved, atomic(name="Unknown")),
            )
            if resolved is not None
            else atomic(name="Unknown")
        )
        if not (
            variable_shape.name.split(sep=".")[-1] == "Callable"
            and len(variable_shape.arguments) == Constants.pair_size
        ):
            return None
        callable_parameters: TypeShape = variable_shape.arguments[0]
        args: tuple[TypeShape, ...] = site.arguments.positional
        if callable_parameters.name != "parameters" or len(args) != len(
            callable_parameters.arguments,
        ):
            return None
        for given, expected in zip(
            args,
            callable_parameters.arguments,
            strict=True,
        ):
            if (
                subtype(
                    actual=given,
                    expected=expected,
                    index=self.contracts,
                ).compatible
                is False
            ):
                return atomic(name="Unknown")
        return self._record(
            node=node,
            shape=variable_shape.arguments[1],
            kind="Callable_contract",
        )

    def _resolve_function_contract(
        self,
        *,
        site: CallSite,
    ) -> TypeShape | None:
        """Resolve a call of a function with a source-defined contract.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        if site.name is None or site.name not in self.contracts.functions:
            return None
        return self._contract_call(
            node=site.node,
            variants=self.contracts.variants(qualified_name=site.name),
            arguments=site.arguments,
        )

    def _resolve_class_constructor(
        self,
        *,
        site: CallSite,
    ) -> TypeShape | None:
        """Resolve a call of a class through its constructor contract.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        if site.name is None or site.name not in self.contracts.classes:
            return None
        constructor_contract: CallableContract | None = (
            self.contracts.constructor(
                name=site.name,
            )
        )
        return self._contract_call(
            node=site.node,
            variants=(constructor_contract,)
            if constructor_contract is not None
            else (),
            arguments=site.arguments,
            receiver=TypeShape(name=site.name),
            constructor=site.name,
        )

    def _imported_constructor_contract(
        self,
        *,
        qualified_name: str,
    ) -> CallableContract | None:
        """Build the curated contract for a known imported constructor.

        Args:
            qualified_name: Qualified import origin such as
                ``pathlib.Path``.

        Returns:
            CallableContract | None produced by this operation.

        """
        if qualified_name in self._imported_constructors:
            return self._imported_constructors[qualified_name]
        parameters: tuple[tuple[str, ParameterKind, str, bool], ...] = (
            _IMPORTED_CONSTRUCTOR_PARAMS.get(qualified_name, ())
        )
        contract: CallableContract | None = (
            CallableContract(
                qualified_name=qualified_name,
                parameters=tuple(
                    ParameterContract(
                        name=name,
                        kind=kind,
                        annotation=TypeExpressionCodec.from_source(
                            source=annotation,
                        ),
                        optional=optional,
                    )
                    for name, kind, annotation, optional in parameters
                ),
                returns=TypeExpression(
                    name=qualified_name.rsplit(sep=".", maxsplit=1)[-1],
                ),
            )
            if parameters or qualified_name in _IMPORTED_CONSTRUCTOR_PARAMS
            else None
        )
        self._imported_constructors[qualified_name] = contract
        return contract

    def _resolve_imported_constructor(
        self,
        *,
        site: CallSite,
    ) -> TypeShape | None:
        """Resolve a call of an imported constructor from its signature.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        node: Call = site.node
        if (
            site.name is None
            or not isinstance(node.func, Name)
            or not self._import_is_unmodified(
                alias=site.name,
                node=node.func,
            )
        ):
            return None
        qualified: str | None = self._imports.get(site.name)
        if qualified is None:
            return None
        contract: CallableContract | None = (
            self._imported_constructor_contract(
                qualified_name=qualified,
            )
        )
        if contract is None:
            return None
        return self._contract_call(
            node=node,
            variants=(contract,),
            arguments=site.arguments,
            constructor=qualified.rsplit(sep=".", maxsplit=1)[-1],
        )

    def _resolve_method_contract(self, *, site: CallSite) -> TypeShape | None:
        """Resolve a method call on a receiver with a known class contract.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape | None produced by this operation.

        """
        node: Call = site.node
        if not isinstance(node.func, Attribute):
            return None
        receiver_shape: TypeShape = self._infer(
            node=node.func.value,
            env=site.env,
            narrowing=site.narrowing,
        )
        receiver_name: str = (
            receiver_shape.name
            if receiver_shape.name in self.contracts.classes
            else node.func.value.id
            if isinstance(node.func.value, Name)
            and node.func.value.id in self.contracts.classes
            else ""
        )
        if not receiver_name:
            return None
        methods: tuple[CallableContract, ...] = self.contracts.variants(
            qualified_name=(f"{receiver_name}.{node.func.attr}"),
        )
        if not methods:
            inherited: CallableContract | None = (
                self.contracts.inherited_method(
                    owner=receiver_name,
                    method=node.func.attr,
                )
            )
            methods = (inherited,) if inherited is not None else ()
        if not methods:
            return None
        is_class_object: bool = (
            isinstance(node.func.value, Name)
            and node.func.value.id == receiver_name
            and (receiver_shape.name == "Unknown")
        )
        implicit_receiver: TypeShape | None = (
            receiver_shape
            if not is_class_object or methods[0].method_kind == "class"
            else None
        )
        return self._contract_call(
            node=node,
            variants=methods,
            arguments=site.arguments,
            receiver=implicit_receiver,
        )

    def _record_local_call(
        self,
        *,
        site: CallSite,
        function: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Flow call arguments into the parameters of a local function.

        Args:
            function: The function examined while flow call arguments into the
                parameters of a local function.
            site: Site supplied as CallSite for this operation.

        """
        node, args = (site.node, site.arguments.positional)
        parameters: tuple[arg, ...] = (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
        for index, parameter in enumerate(iterable=parameters):
            supplied: TypeShape | None = (
                args[index]
                if index < len(args)
                else site.arguments.named.get(parameter.arg)
            )
            source_node: AST | None = (
                node.args[index]
                if index < len(node.args)
                else next(
                    (
                        kw.value
                        for kw in node.keywords
                        if kw.arg == parameter.arg
                    ),
                    None,
                )
            )
            if supplied is None:
                continue
            sid: int | None = self._function_parameters.get(
                (function.name, parameter.arg),
            )
            if (
                sid is not None
                and sid in self.declarations
                and (source_node is not None)
            ):
                self._backward(
                    node=source_node,
                    required=self.declarations[sid],
                    env=site.env,
                    origin=node,
                )
            if sid is not None and self._add(
                symbol_id=sid,
                shape=supplied,
                evidence=self._evidence(
                    node=node,
                    kind="argument",
                    description=(f"call passes {supplied} to {parameter.arg}"),
                ),
            ):
                self._schedule(name=function.name)

    def _name_call_type(self, *, site: CallSite, name: str) -> TypeShape:
        """Type a call of a plain name: a local function or a builtin.

        Args:
            name: Identifier of the name being resolved.
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape produced by this operation.

        """
        if name in self._definitions:
            self._record_local_call(
                site=site,
                function=self._definitions[name],
            )
            return self._return_types.get(name, atomic(name="Unknown"))
        scope_id: int = self.scopes.node_scopes.get(
            self.identities.node_id(node=site.node.func),
            self.scopes.root_id,
        )
        if self.scopes.resolve(name=name, scope_id=scope_id) is None:
            return _builtin_call(name=name, site=site)
        return atomic(name="Unknown")

    def _apply_receiver_effect(
        self,
        *,
        site: CallSite,
        receiver: TypeShape,
        method: str,
    ) -> None:
        """Model mutation of a container variable by a method call.

        Args:
            method: Method supplied as str for this operation.
            receiver: Receiver supplied as TypeShape for this operation.
            site: Site supplied as CallSite for this operation.

        """
        func: expr = site.node.func
        if not isinstance(func, Attribute) or not isinstance(func.value, Name):
            return
        sid: int | None = self._symbol_id(node=func.value)
        update: tuple[TypeShape, str] | None = _receiver_update(
            receiver=receiver,
            method=method,
            args=site.arguments.positional,
        )
        if sid is None or update is None:
            return
        updated, description = update
        site.env[sid] = updated
        self._add(
            symbol_id=sid,
            shape=updated,
            evidence=self._evidence(
                node=site.node,
                kind="method_effect",
                description=description,
            ),
        )

    def _method_call_type(
        self,
        *,
        site: CallSite,
        func: Attribute,
    ) -> TypeShape:
        """Type a method call using modeled builtin container effects.

        Args:
            func: Func supplied as Attribute for this operation.
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape produced by this operation.

        """
        receiver: TypeShape = self._infer(
            node=func.value,
            env=site.env,
            narrowing=site.narrowing,
        )
        method: str = func.attr
        builtin: TypeShape | None = _builtin_str_method(
            receiver_name=receiver.name,
            method=method,
        )
        if builtin is not None:
            return self._record(
                node=site.node,
                shape=builtin,
                kind="builtin_method",
            )
        result: TypeShape = _container_method_result(
            receiver=receiver,
            method=method,
            args=site.arguments.positional,
        )
        self._apply_receiver_effect(
            site=site,
            receiver=receiver,
            method=method,
        )
        return result

    def _call_effects(self, *, site: CallSite) -> TypeShape:
        """Type a call by local flow, builtin tables and modeled effects.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            TypeShape produced by this operation.

        """
        func: expr = site.node.func
        if isinstance(func, Name):
            return self._name_call_type(site=site, name=func.id)
        if isinstance(func, Attribute):
            return self._method_call_type(site=site, func=func)
        return atomic(name="Unknown")

    def _qualified_call_name(self, *, site: CallSite) -> str | None:
        """Qualified import-based name of the called object, if any.

        Args:
            site: Site supplied as CallSite for this operation.

        Returns:
            str | None produced by this operation.

        """
        func: expr = site.node.func
        if isinstance(func, Name) and self._import_is_unmodified(
            alias=func.id,
            node=func,
        ):
            return self._imports.get(func.id)
        if not (isinstance(func, Attribute) and isinstance(func.value, Name)):
            return None
        base: str | None = (
            self._imports.get(func.value.id)
            if self._import_is_unmodified(alias=func.value.id, node=func.value)
            else None
        )
        if base is not None:
            return f"{base}.{func.attr}"
        receiver_shape: TypeShape = self._infer(
            node=func.value,
            env=site.env,
            narrowing=site.narrowing,
        )
        if "." in receiver_shape.name:
            return f"{receiver_shape.name}.{func.attr}"
        return None

    def _stub_call_type(
        self,
        *,
        site: CallSite,
        stubs: StubIndex,
        result: TypeShape,
    ) -> TypeShape:
        """Resolve an unknown call through bundled typeshed stubs.

        Args:
            result: The result examined while resolve an unknown call through
                bundled typeshed stubs.
            site: Site supplied as CallSite for this operation.
            stubs: Stubs supplied as StubIndex for this operation.

        Returns:
            TypeShape produced by this operation.

        """
        qualified: str | None = self._qualified_call_name(site=site)
        if qualified is None:
            return result
        candidates: tuple[StubSignature, ...] = stubs.lookup(
            qualified_name=qualified,
        )
        contracts: tuple[CallableContract, ...] = tuple(
            item.contract for item in candidates if item.contract is not None
        )
        func: expr = site.node.func
        if contracts:
            result = self._contract_call(
                node=site.node,
                variants=contracts,
                arguments=site.arguments,
                receiver=self._infer(
                    node=func.value,
                    env=site.env,
                    narrowing=site.narrowing,
                )
                if isinstance(func, Attribute)
                and any(
                    item.method_kind in ("instance", "class")
                    for item in contracts
                )
                else None,
            )
        else:
            for signature in candidates:
                result = join_types(
                    left=result,
                    right=type_shape(expression=signature.returns),
                    promote=False,
                )
        for signature in candidates:
            self._record(
                node=site.node,
                shape=result,
                kind=(f"stub:{signature.source_path}"),
            )
        return result

    def _call(
        self,
        *,
        node: Call,
        env: dict[int, TypeShape],
        narrowing: dict[str, TypeShape] | None,
    ) -> TypeShape:
        """Propagate local function contracts and modeled built-in effects.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] | None for
                this operation.
            node: The node examined while propagate local function contracts
                and modeled built-in effects.

        Returns:
            TypeShape produced by this operation.

        """
        args: tuple[TypeShape, ...] = tuple(
            self._infer(
                node=item.value if isinstance(item, Starred) else item,
                env=env,
                narrowing=narrowing,
            )
            for item in node.args
        )
        keywords: dict[str, TypeShape] = {
            item.arg: self._infer(
                node=item.value,
                env=env,
                narrowing=narrowing,
            )
            for item in node.keywords
            if item.arg is not None
        }
        site: CallSite = CallSite(
            node=node,
            name=node.func.id if isinstance(node.func, Name) else None,
            arguments=CallArguments(positional=args, named=keywords),
            env=env,
            narrowing=narrowing,
        )
        for resolver in (
            self._resolve_newtype,
            self._resolve_callable_variable,
            self._resolve_function_contract,
            self._resolve_class_constructor,
            self._resolve_imported_constructor,
            self._resolve_method_contract,
        ):
            resolved: TypeShape | None = resolver(site=site)
            if resolved is not None:
                return resolved
        result: TypeShape = self._call_effects(site=site)
        if self.stubs is not None and result.name == "Unknown":
            result = self._stub_call_type(
                site=site,
                stubs=self.stubs,
                result=result,
            )
        return result

    def _backward(
        self,
        *,
        node: AST,
        required: TypeShape,
        env: dict[int, TypeShape],
        origin: AST,
    ) -> bool:
        """Propagate syntactic contracts backward through pure shapes.

        This is an evidence-producing constraint, not proof that untrusted
        runtime values satisfy the annotation. Unsupported operators stop the
        propagation rather than inventing constraints.


        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            node: The node examined while propagate syntactic contracts
                backward through pure shapes.
            origin: Origin supplied as AST for this operation.
            required: Required supplied as TypeShape for this operation.

        Returns:
            Whether the requested condition holds.

        """
        if required.name in ("Never", "Unknown"):
            return False
        if isinstance(node, Name):
            sid: int | None = self._symbol_id(node=node)
            return sid is not None and self._add(
                symbol_id=sid,
                shape=required,
                evidence=self._evidence(
                    node=origin,
                    kind="backward_contract",
                    description=(f"context expects {required} from {node.id}"),
                ),
            )
        if (
            isinstance(node, (List, Set, Tuple))
            and required.name in ("list", "set", "tuple")
            and required.arguments
        ):
            changed: bool = False
            for item in node.elts:
                changed = (
                    self._backward(
                        node=item,
                        required=required.arguments[0],
                        env=env,
                        origin=origin,
                    )
                    or changed
                )
            return changed
        if isinstance(node, IfExp):
            first: bool = self._backward(
                node=node.body,
                required=required,
                env=env,
                origin=origin,
            )
            second: bool = self._backward(
                node=node.orelse,
                required=required,
                env=env,
                origin=origin,
            )
            return first or second
        if (
            isinstance(node, Call)
            and isinstance(node.func, Name)
            and (node.func.id in self._definitions)
        ):
            name: str = node.func.id
            before: TypeShape = self._return_types.get(
                name,
                atomic(name="Never"),
            )
            after: TypeShape = join_types(left=before, right=required)
            if after != before:
                self._return_types[name] = after
                self._schedule(name=name)
                return True
        return False

    def _schedule(self, *, name: str) -> None:
        """Queue an analysis context once, with bounded reprocessing.

        Args:
            name: Identifier of the name being resolved.

        """
        if name != "<module>" and name not in self._definitions:
            return
        if name not in self._queued:
            self._queued.add(name)
            self._work.append(name)

    def _apply_narrowing(
        self,
        *,
        test: AST,
        narrowing: dict[str, TypeShape],
        env: dict[int, TypeShape],
    ) -> None:
        """Bind narrowed shapes to the first matching name in ``test``.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            narrowing: Narrowing supplied as dict[str, TypeShape] for this
                operation.
            test: Test supplied as AST for this operation.

        """
        for name, shape in narrowing.items():
            for item in walk(node=test):
                if isinstance(item, Name) and item.id == name:
                    sid: int | None = self._symbol_id(node=item)
                    if sid is not None:
                        env[sid] = shape
                        break

    def _declare_annotation(self, *, statement: Assign | AnnAssign) -> None:
        """Record the declared type of an annotated assignment target.

        Args:
            statement: The statement examined while record the declared type of
                an annotated assignment target.

        """
        if isinstance(statement, AnnAssign) and isinstance(
            statement.target,
            Name,
        ):
            sid: int | None = self._symbol_id(node=statement.target)
            if sid is not None:
                self._declare(
                    symbol_id=sid,
                    shape=_hint(node=statement.annotation),
                    node=statement,
                )

    def _suite(
        self,
        *,
        statements: Sequence[AST],
        env: dict[int, TypeShape],
        owner: str,
    ) -> bool:
        """Propagate suite contracts, with bounded joins across branches.

        Args:
            env: Env supplied as dict[int, TypeShape] for this operation.
            owner: Owner supplied as str for this operation.
            statements: Collection of statements supplied for this operation.

        Returns:
            Whether the requested condition holds.

        """
        changed: bool = False
        for statement in statements:
            for handler_name in handler_names(node=statement, prefix="suite_"):
                handler: Callable[..., bool] | None = getattr(
                    self,
                    handler_name,
                    None,
                )
                if handler is not None:
                    changed = handler(statement, env, owner) or changed
                    break
        return changed

    def _solve_methods(self) -> None:
        """Propagate contracts through method bodies to a bounded fixpoint.

        Method receivers and ``self.attr`` writes are indexed by
        :meth:`_index_methods`; their bodies join the same constraint
        system so attribute reads resolve against declared members and
        recorded writes.
        """
        for _ in range(8):
            changed: bool = False
            for function in self._method_nodes:
                parameters: tuple[arg, ...] = (
                    *function.args.posonlyargs,
                    *function.args.args,
                    *function.args.kwonlyargs,
                )
                env: dict[int, TypeShape] = {
                    sid: self.types[sid]
                    for parameter in parameters
                    if (sid := self._symbol_id(node=parameter)) is not None
                    and sid in self.types
                }
                changed = (
                    self._suite(
                        statements=function.body,
                        env=env,
                        owner=function.name,
                    )
                    or changed
                )
            if not changed:
                return

    def _solve(self) -> TypeSolveStatistics:
        """Iterate call and return constraints until stable or exhausted.

        Returns:
            TypeSolveStatistics produced by this operation.

        """
        visits: int = 0
        changes: int = 0
        while self._work and visits < self.max_visits:
            name: str = self._work.popleft()
            self._queued.discard(name)
            visits += 1
            env: dict[int, TypeShape] = (
                {}
                if name == "<module>"
                else {
                    identity: self.types[identity]
                    for identity in self._parameters.get(name, ())
                    if identity in self.types
                }
            )
            body: Sequence[AST] = (
                self.root.body
                if name == "<module>"
                else self._definitions[name].body
            )
            if self._suite(statements=body, env=env, owner=name):
                changes += 1
        return TypeSolveStatistics(
            visits=visits,
            changes=changes,
            converged=not self._work,
            reused=0,
        )

    def _publish(self) -> None:
        """Attach immutable type and evidence snapshots to owned AST nodes."""
        for diagnostic in self.contracts.diagnostics:
            write_attribute(
                node=diagnostic.node,
                name="typing_diagnostics",
                value=(
                    *getattr(diagnostic.node, "typing_diagnostics", ()),
                    diagnostic,
                ),
            )
        for cls in self.contracts.classes.values():
            write_attribute(node=cls.node, name="class_contract", value=cls)
        for node_id, node in self._nodes.items():
            occurrence: Occurrence | None = self.scopes.occurrences.get(
                node_id,
            )
            sid: int | None = (
                occurrence.symbol_id if occurrence is not None else None
            )
            shape: TypeShape = (
                self.node_types.get(
                    node_id,
                    self.types.get(sid, atomic(name="Unknown")),
                )
                if sid is not None
                else self.node_types.get(node_id, atomic(name="Unknown"))
            )
            write_attribute(node=node, name="inferred_type_hint", value=shape)
            write_attribute(
                node=node,
                name="type_evidence",
                value=tuple(self.proofs.get(sid, ()))
                if sid is not None
                else tuple(self.node_proofs.get(node_id, ())),
            )
            write_attribute(
                node=node,
                name="declared_type_hint",
                value=self.declarations.get(sid) if sid is not None else None,
            )
            write_attribute(
                node=node,
                name="type_conflicts",
                value=tuple(sorted(self.conflicts.get(sid, ())))
                if sid is not None
                else tuple(getattr(node, "type_conflicts", ())),
            )
            write_attribute(
                node=node,
                name="value_evidence",
                value=tuple(getattr(node, "value_evidence", ())),
            )
