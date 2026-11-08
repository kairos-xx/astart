"""Corroborated type hints: candidates are accepted only with evidence."""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFor,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BitOr,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Expr,
    Expression,
    For,
    FunctionDef,
    Lambda,
    List,
    Load,
    Module,
    Name,
    NamedExpr,
    Not,
    Pass,
    Raise,
    Return,
    Store,
    Subscript,
    Tuple,
    UnaryOp,
    Yield,
    YieldFrom,
    alias,
    arg,
    arguments,
    expr,
    iter_child_nodes,
    parse,
    stmt,
    unparse,
    walk,
    withitem,
)
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, Self, final

from astart.rules.attributes import (
    Attributes,
    Scope,
    attribute_annotations,
    receiver_of,
)
from astart.rules.imports import Constants as ImportConstants
from astart.rules.imports import bound_names
from astart.rules.methods import MethodIndex
from astart.rules.project_bridge import qualified_names
from astart.rules.provable import (
    expression_type,
    module_constants,
    never_returns,
    own_calls,
    provable_return_detail,
    scope_types,
)
from astart.rules.reasons import Rejection
from astart.rules.resolve import CallBindings, binding_counts
from astart.semantic import ArgumentOrigin

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from astart import BoundArgument, BoundCall, CommentedModule
    from astart.rules.project_bridge import CrossSite, ProjectView
    from astart.semantic.graph_conversion import GraphAnnotation
type Function = FunctionDef | AsyncFunctionDef


class HintBasis(StrEnum):
    """Why a hint was accepted.

    Attributes:
        proven_none: The function provably returns nothing.
        default_literal: The default value's literal type agrees.
        call_sites: Every in-module call site agrees.
        derived_return: The return type depends only on typed names.
        syntax_proven: The return type is guaranteed by the language itself,
            whatever the types of the parameters.
        optional_default: The parameter defaults to ``None`` and every call
            site that passes a value proves the same type.
        attribute_assignments: Every write to an instance attribute proves
            the same type.
        protocol_result: A protocol dunder (``__exit__``, ``__len__``, …)
            whose body is consistent with the type the protocol declares.
        union_sites: Call sites pass several syntax-proven types and the
            inference candidate is exactly their union.
        negotiated: A type settled by the contract negotiator from evidence
            that proves it (local variables and instance attributes).
        engine: An annotation of the inference engine alone, taken in
            conversion mode (``--engine``) and left to the checker gate.
        calibrated_candidate: An inference-engine candidate in a category
            measured against annotated real-world code and found reliable
            (see ``Constants.calibrated_returns``).

    """

    proven_none = "proven_none"
    default_literal = "default_literal"
    call_sites = "call_sites"
    derived_return = "derived_return"
    syntax_proven = "syntax_proven"
    optional_default = "optional_default"
    protocol_result = "protocol_result"
    attribute_assignments = "attribute_assignments"
    calibrated_candidate = "calibrated_candidate"
    union_sites = "union_sites"
    negotiated = "negotiated"
    engine = "engine"


@final
@dataclass(frozen=True, slots=True)
class Hint:
    """An accepted annotation and the evidence behind it.

    Attributes:
        source: Annotation source text.
        basis: Why it was accepted.

    """

    source: str
    basis: HintBasis


@final
class Constants:
    """Group module-level constants.

    Attributes:
        protocol_results: Result type each protocol dunder must declare.
        variadic_origins: Origins of arguments bound to ``*args``/``**kwargs``.
        calibrated_returns: Return candidates accepted on the engine's word
            alone: ``bool`` matched the original in 97 % of 232 cases and
            contradicted it in none (stdlib + 25 typed libraries).
        predicate_calls: Builtins whose result is always a ``bool``.
        propagation_passes: Most times accepted parameter hints are fed back
            into call-site evidence before the index is final.
        max_union_members: Most distinct types a call-site union may have to
            be written.
        shape_specific: Prefix of types that describe one literal's exact
            shape (a tuple's length), which says nothing about other callers.
        inference_errors: Failures of the inference layer that are contained:
            the module simply gets no inferred candidates.
        builtin_names: Grouped module constant.
        banned_names: Grouped module constant.
        scalar_types: Grouped module constant.
        expression_nodes: Grouped module constant.
        proposal_roles: Grouped module constant.
        skipped_names: Grouped module constant.
        declaration_decorators: Grouped module constant.
        scope_nodes: Grouped module constant.

    """

    protocol_results: Final[dict[str, str]] = {
        "__aexit__": "bool | None",
        "__bool__": "bool",
        "__contains__": "bool",
        "__exit__": "bool | None",
        "__float__": "float",
        "__format__": "str",
        "__hash__": "int",
        "__index__": "int",
        "__int__": "int",
        "__len__": "int",
        "__repr__": "str",
        "__str__": "str",
    }
    variadic_origins: Final[frozenset[ArgumentOrigin]] = frozenset(
        {ArgumentOrigin.VAR_POSITIONAL, ArgumentOrigin.VAR_KEYWORD},
    )
    propagation_passes: Final[int] = 12
    max_union_members: Final[int] = 3
    calibrated_returns: Final[frozenset[str]] = frozenset({"bool"})
    predicate_calls: Final[frozenset[str]] = frozenset(
        {"isinstance", "issubclass", "callable", "hasattr", "bool"},
    )
    shape_specific: Final[str] = "tuple["
    inference_errors: Final[tuple[type[Exception], ...]] = (
        AttributeError,
        IndexError,
        KeyError,
        RecursionError,
        SyntaxError,
        TypeError,
        ValueError,
    )
    builtin_names: Final[frozenset[str]] = frozenset(
        {
            "bool",
            "bytearray",
            "bytes",
            "complex",
            "dict",
            "float",
            "frozenset",
            "int",
            "list",
            "set",
            "str",
            "tuple",
            "type",
        },
    )
    banned_names: Final[frozenset[str]] = frozenset({"object", "Any"})
    scalar_types: Final[frozenset[str]] = frozenset(
        {"bool", "bytes", "float", "int", "str"},
    )
    expression_nodes: Final[tuple[type[AST], ...]] = (
        Expression,
        Name,
        Attribute,
        Subscript,
        Tuple,
        List,
        BinOp,
        BitOr,
        Load,
        Constant,
    )
    proposal_roles: Final[frozenset[str]] = frozenset({"parameter", "return"})
    skipped_names: Final[frozenset[str]] = frozenset({"self", "cls"})
    declaration_decorators: Final[frozenset[str]] = frozenset(
        {"overload", "abstractmethod"},
    )
    scope_nodes: Final[tuple[type[AST], ...]] = (
        FunctionDef,
        AsyncFunctionDef,
        ClassDef,
        Lambda,
    )


type Key = tuple[str, int, int]


def _key(*, node: AST) -> Key:
    """Identify a parameter or function by kind and source position.

    Positions are identical in every parse of the same text, so hints
    computed on one parse can be looked up on another.

    Args:
        node: Parameter or function node.

    Returns:
        (kind, line, column).

    """
    return (
        "arg" if isinstance(node, arg) else "def",
        getattr(node, "lineno", 0),
        getattr(node, "col_offset", 0),
    )


def is_allowed_source(*, source: str, known_names: frozenset[str]) -> bool:
    """Decide whether an annotation may be written into a module.

    Args:
        source: Annotation source text.
        known_names: Names the module already imports or defines.

    Returns:
        Whether every name is a builtin type or known, and neither
        ``object`` nor ``Any`` appears.

    """
    try:
        tree: Expression = parse(source=source, mode="eval")
    except SyntaxError:
        return False
    allowed: frozenset[str] = Constants.builtin_names | known_names
    for node in walk(node=tree):
        if not isinstance(node, Constants.expression_nodes):
            return False
        match node:
            case Name(id=name):
                if name in Constants.banned_names or name not in allowed:
                    return False
            case Constant(value=value):
                if value is not None and value is not Ellipsis:
                    return False
            case _:
                continue
    return True


def _importable(*, module: Module) -> frozenset[str]:
    """List known names a new annotation may use because they can be imported.

    Args:
        module: Parsed module.

    Returns:
        Importable names the module does not already bind to something else.

    """
    return frozenset(ImportConstants.known_imports) - bound_names(
        module=module,
    )


def _imported_names(*, module: Module) -> frozenset[str]:
    """Collect names bound by imports and by top-level definitions.

    Args:
        module: Parsed module.

    Returns:
        Names available to a new annotation.

    """
    names: set[str] = set()
    for node in walk(node=module):
        match node:
            case alias(name=name, asname=asname):
                names.add(asname or name.split(sep=".")[0])
            case ClassDef(name=name):
                names.add(name)
            case _:
                continue
    return frozenset(names)


def _parameters(
    *,
    function: FunctionDef | AsyncFunctionDef,
) -> list[tuple[arg, expr | None]]:
    """Pair each plain parameter with its default.

    Args:
        function: Function definition.

    Returns:
        Positional-only, positional and keyword-only parameters.

    """
    arguments: arguments = function.args
    positional: list[arg] = [*arguments.posonlyargs, *arguments.args]
    offset: int = len(positional) - len(arguments.defaults)
    pairs: list[tuple[arg, expr | None]] = [
        (
            parameter,
            arguments.defaults[index - offset] if index >= offset else None,
        )
        for index, parameter in enumerate(iterable=positional)
    ]
    pairs.extend(zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True))
    return pairs


def own_nodes(*, function: Function) -> Iterator[AST]:
    """Walk a function body without entering nested scopes.

    Args:
        function: Function definition.

    Yields:
        Every node that belongs to the function itself.

    """
    stack: list[AST] = [
        statement
        for statement in reversed(function.body)
        if not isinstance(statement, Constants.scope_nodes)
    ]
    while stack:
        node: AST = stack.pop()
        yield node
        stack.extend(
            child
            for child in reversed(list(iter_child_nodes(node=node)))
            if not isinstance(child, Constants.scope_nodes)
        )


def _is_stub_statement(*, statement: stmt) -> bool:
    """Report whether a statement carries no behaviour.

    Args:
        statement: Statement from a function body.

    Returns:
        Whether it is ``pass``, a docstring, ``...`` or a
        ``NotImplementedError`` raise.

    """
    match statement:
        case Pass() | Expr(value=Constant()):
            return True
        case Raise(exc=exc):
            target: expr | None = exc.func if isinstance(exc, Call) else exc
            return (
                isinstance(target, Name) and target.id == "NotImplementedError"
            )
        case _:
            return False


def is_declaration(*, function: Function) -> bool:
    """Report whether a function only declares a signature.

    Args:
        function: Function definition.

    Returns:
        Whether it is an overload or abstract method, or has a stub body.

    """
    for decorator in function.decorator_list:
        name: str | None = (
            decorator.id
            if isinstance(decorator, Name)
            else decorator.attr
            if isinstance(decorator, Attribute)
            else None
        )
        if name in Constants.declaration_decorators:
            return True
    return all(_is_stub_statement(statement=s) for s in function.body)


def _value_returns(*, function: Function) -> list[expr]:
    """Collect the expressions of ``return <value>`` statements.

    Args:
        function: Function definition.

    Returns:
        Return expressions, ignoring bare and ``return None`` statements.

    """
    return [
        node.value
        for node in own_nodes(function=function)
        if isinstance(node, Return)
        and node.value is not None
        and (
            not (isinstance(node.value, Constant) and node.value.value is None)
        )
    ]


def _is_generator(*, function: Function) -> bool:
    """Report whether a function yields.

    Args:
        function: Function definition.

    Returns:
        Whether the body contains ``yield`` or ``yield from``.

    """
    return any(
        isinstance(node, (Yield, YieldFrom))
        for node in own_nodes(function=function)
    )


def returns_nothing(*, function: Function) -> bool:
    """Prove that a function always returns ``None``, as its own contract.

    Protocol dunders such as ``__exit__`` are excluded: their declared result
    is wider than what their body returns (``bool | None``).

    Args:
        function: Function definition.

    Returns:
        Whether it has no returned value, does not yield, and is not a
        declaration (overload, abstract method or stub body).

    """
    return function.name not in Constants.protocol_results and (
        _body_returns_nothing(function=function)
    )


def _body_returns_nothing(*, function: Function) -> bool:
    """Prove that a function body returns nothing.

    Args:
        function: Function definition.

    Returns:
        Whether it has no returned value, does not yield, never only raises,
        and is not a declaration.

    """
    return not (
        is_declaration(function=function)
        or _is_generator(function=function)
        or _value_returns(function=function)
        or never_returns(function=function)
    )


def _mentions(*, node: AST, names: dict[str, str]) -> str | None:
    """Find the first tainted name an expression mentions.

    Args:
        node: Expression or statement part.
        names: Tainted names mapped to their originating parameter.

    Returns:
        The originating parameter, or ``None``.

    """
    for inner in walk(node=node):
        if isinstance(inner, Name) and inner.id in names:
            return names[inner.id]
    return None


def _targets(*, node: AST) -> list[str]:
    """List the names bound by an assignment target.

    Args:
        node: Target expression.

    Returns:
        The stored names.

    """
    return [
        inner.id
        for inner in walk(node=node)
        if isinstance(inner, Name) and isinstance(inner.ctx, Store)
    ]


def _spread(*, node: AST, names: dict[str, str]) -> bool:
    """Spread taint through one statement or expression.

    Args:
        node: Node from the function body.
        names: Tainted names, extended in place.

    Returns:
        Whether a new name became tainted.

    """
    pairs: list[tuple[AST, AST]] = []
    match node:
        case Assign(targets=targets, value=value):
            pairs = [(target, value) for target in targets]
        case AugAssign(target=target, value=value):
            pairs = [(target, value)]
        case (
            For(target=target, iter=source)
            | AsyncFor(target=target, iter=source)
        ):
            pairs = [(target, source)]
        case NamedExpr(target=target, value=value):
            pairs = [(target, value)]
        case withitem(context_expr=source, optional_vars=target) if (
            target is not None
        ):
            pairs = [(target, source)]
        case _:
            return False
    changed: bool = False
    for target, source in pairs:
        origin: str | None = _mentions(node=source, names=names)
        if origin is None:
            continue
        for name in _targets(node=target):
            if name not in names:
                names[name] = origin
                changed = True
    return changed


def _taint_origins(
    *,
    function: Function,
    accepted: frozenset[str],
) -> dict[str, str]:
    """Compute which names depend on an untyped parameter.

    Args:
        function: Function definition.
        accepted: Parameters that have an accepted hint.

    Returns:
        Tainted names mapped to the parameter that taints them.

    """
    arguments: arguments = function.args
    parameters: list[arg] = [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        *[a for a in (arguments.vararg, arguments.kwarg) if a is not None],
    ]
    names: dict[str, str] = {
        parameter.arg: parameter.arg
        for parameter in parameters
        if parameter.annotation is None and parameter.arg not in accepted
    }
    changed: bool = True
    while changed:
        changed = False
        for node in own_nodes(function=function):
            changed = _spread(node=node, names=names) or changed
    return names


def tainted_names(
    *,
    function: Function,
    accepted: frozenset[str],
) -> frozenset[str]:
    """List names whose type depends on an untyped parameter.

    Parameters without an annotation or an accepted hint are tainted, and
    taint flows through assignments, loops and walrus targets.

    Args:
        function: Function definition.
        accepted: Parameters that have an accepted hint.

    Returns:
        The tainted names.

    """
    return frozenset(_taint_origins(function=function, accepted=accepted))


@final
@dataclass(frozen=True, slots=True)
class _Judging:
    """What a parameter-judging pass needs besides the call sites.

    Attributes:
        candidates: Proposed annotation sources by node identity.
        known: Names a new annotation may use.
        escaped: Names of functions used as values.
        counts: Module binding counts.
        constants: Types of the module's constants, for typing defaults.
        project: Cross-module view of the project, or ``None``.
        qualifieds: ``id`` of each definition to its project-qualified
            name, for reading cross-module evidence and open-world status.

    """

    candidates: dict[Key, str]
    known: frozenset[str]
    escaped: frozenset[str]
    counts: dict[str, int]
    constants: dict[str, str]
    project: ProjectView | None = None
    qualifieds: Mapping[int, str] = field(default_factory=dict[int, str])

    def function_escaped(self, *, function: Function) -> bool:
        """Whether a function's callers cannot all be known.

        Local escapes apply as always; with a project view an escaped or
        externally callable qualified name counts too.

        Args:
            function: The definition being judged.

        Returns:
            Whether its caller set is incomplete.

        """
        if function.name in self.escaped:
            return True
        if self.project is None:
            return False
        qualified: str | None = self.qualifieds.get(id(function))
        return qualified is not None and self.project.open_world(
            qualified=qualified,
        )


@final
@dataclass(frozen=True, slots=True)
class _Site:
    """What one direct call shows about one parameter.

    Attributes:
        definite: Whether the argument type is trustworthy.
        types: Rendered type spellings.
        proven: Whether the argument expression's syntax alone proves the
            type, independent of the analyzer.

    """

    definite: bool
    types: tuple[str, ...]
    proven: bool = False


@final
@dataclass(frozen=True, slots=True)
class _Evidence:
    """What the module shows about a function's parameter types.

    Attributes:
        sites: One entry per direct call: whether the argument type is
            definite, and its rendered spellings.
        escaped: Whether the function is also used as a value (aliased,
            passed as a callback, stored), so its callers cannot be known.
        default_type: Scalar type the syntax of a non-literal default proves
            (``-1``, a constant's name), else ``None``.

    """

    sites: list[_Site]
    escaped: bool
    default_type: str | None = None


def _escaped_names(*, module: Module) -> frozenset[str]:
    """Collect names that are read anywhere other than as a direct callee.

    Args:
        module: Parsed module.

    Returns:
        Names used as values, which may reach callers the module cannot see.

    """
    callees: set[int] = {
        id(call.func)
        for call in walk(node=module)
        if isinstance(call, Call) and isinstance(call.func, Name)
    }
    return frozenset(
        node.id
        for node in walk(node=module)
        if isinstance(node, Name)
        and isinstance(node.ctx, Load)
        and (id(node) not in callees)
    )


@final
class HintIndex:
    """Accepted hints and rejection reasons for one module."""

    def __init__(
        self,
        *,
        hints: dict[Key, Hint],
        rejections: dict[Key, str],
    ) -> None:
        """Store computed results.

        Args:
            hints: Accepted hints by node identity.
            rejections: Rejection reasons by node identity.

        """
        self._hints: dict[Key, Hint] = hints
        self._rejections: dict[Key, str] = rejections
        self._extra: dict[Key, Hint] = {}
        self.proposals: dict[Key, str] = {}
        self._accepted: dict[int, dict[str, str]] = {}
        self._attribute_types: dict[int, dict[str, str]] = {}

    @classmethod
    def create(
        cls,
        *,
        module: CommentedModule,
        stubs_path: Path | None,
        project: ProjectView | None = None,
    ) -> Self:
        """Compute hints for every unannotated parameter of a module.

        Args:
            module: Parsed module.
            stubs_path: Stub directory, or ``None`` for an empty one.
            project: Cross-module view of the project, or ``None`` for
                single-module analysis.

        Returns:
            The index.

        """
        if stubs_path is None:
            with TemporaryDirectory() as scratch:
                candidates: dict[Key, str] = _candidates(
                    module=module,
                    stubs_path=Path(scratch),
                )
        else:
            candidates = _candidates(module=module, stubs_path=stubs_path)
        index: Self = cls(hints={}, rejections={})
        index.proposals = candidates
        index.judge_parameters(
            module=module,
            candidates=candidates,
            project=project,
        )
        index.judge_attributes(module=module)
        index.judge_returns(
            module=module,
            candidates=candidates,
            counts=binding_counts(module=module),
        )
        return index

    def hint_for(self, *, node: AST) -> Hint | None:
        """Return the accepted hint for a node, if any.

        Args:
            node: Parameter or function node.

        Returns:
            The hint or ``None``.

        """
        key: Key = _key(node=node)
        return self._hints.get(key) or self._extra.get(key)

    def own_hint_for(self, *, node: AST) -> Hint | None:
        """Return the hint this index itself accepted, ignoring supplements.

        Args:
            node: Parameter or function node.

        Returns:
            The hint or ``None``.

        """
        return self._hints.get(_key(node=node))

    def supplement(self, *, hints: Mapping[Key, Hint]) -> None:
        """Add hints from another source where this index has none.

        Args:
            hints: Hints by node identity; existing ones always win.

        """
        self._extra = {
            key: hint for key, hint in hints.items() if key not in self._hints
        }

    def rejection_for(self, *, node: AST) -> str | None:
        """Explain why a candidate was refused.

        Args:
            node: Parameter or function node.

        Returns:
            The reason, or ``None`` when accepted or never proposed.

        """
        return self._rejections.get(_key(node=node))

    def judge_returns(
        self,
        *,
        module: CommentedModule,
        candidates: dict[Key, str],
        counts: dict[str, int],
    ) -> None:
        """Accept or refuse a return hint for every unannotated function.

        Args:
            module: Parsed module.
            candidates: Proposed annotation sources by node identity.
            counts: Module binding counts.

        """
        known: frozenset[str] = _imported_names(module=module) | _importable(
            module=module,
        )
        owners: dict[int, ClassDef] = {
            id(item): cls
            for cls in walk(node=module)
            if isinstance(cls, ClassDef)
            for item in cls.body
            if isinstance(item, (FunctionDef, AsyncFunctionDef))
        }
        for function in walk(node=module):
            if (
                not isinstance(
                    function,
                    (FunctionDef, AsyncFunctionDef),
                )
                or function.returns is not None
            ):
                continue
            key: Key = _key(node=function)
            if function.name in Constants.protocol_results:
                self._judge_protocol_result(
                    function=function,
                    counts=counts,
                    key=key,
                )
                continue
            if returns_nothing(function=function):
                self._hints[key] = Hint(
                    source="None",
                    basis=HintBasis.proven_none,
                )
                continue
            if is_declaration(function=function):
                self._rejections[key] = Rejection.declaration_body
            elif _is_generator(function=function):
                self._rejections[key] = Rejection.generator
            else:
                self._judge_derived(
                    function=function,
                    candidate=candidates.get(key),
                    known=known,
                    counts=counts,
                    owner=owners.get(id(function)),
                )

    def _judge_protocol_result(
        self,
        *,
        function: Function,
        counts: dict[str, int],
        key: Key,
    ) -> None:
        """Give a protocol dunder its declared result when the body fits.

        Args:
            function: A dunder listed in ``Constants.protocol_results``.
            counts: Module binding counts.
            key: Function node key.

        """
        declared: str | None = protocol_result_for(
            function=function,
            counts=counts,
        )
        if declared is not None:
            self._hints[key] = Hint(
                source=declared,
                basis=HintBasis.protocol_result,
            )
        elif is_declaration(function=function) or _is_generator(
            function=function,
        ):
            self._rejections[key] = Rejection.declaration_body
        else:
            self._rejections[key] = Rejection.protocol_mismatch

    def judge_attributes(self, *, module: CommentedModule) -> None:
        """Accept an annotation for each instance attribute whose writes agree.

        Args:
            module: Parsed module.

        """
        counts: dict[str, int] = binding_counts(module=module)
        found: Attributes = attribute_annotations(
            scope=Scope(
                module=module,
                counts=counts,
                constants=module_constants(module=module, counts=counts),
                accepted=self._accepted,
                index=MethodIndex(module=module, counts=counts),
            ),
        )
        known: frozenset[str] = _imported_names(module=module) | _importable(
            module=module,
        )
        self._attribute_types = found.types
        for node in walk(node=module):
            source: str | None = found.annotations.get(id(node))
            if source is not None and is_allowed_source(
                source=source,
                known_names=known,
            ):
                self._hints[_key(node=node)] = Hint(
                    source=source,
                    basis=HintBasis.attribute_assignments,
                )

    def judge_parameters(
        self,
        *,
        module: CommentedModule,
        candidates: dict[Key, str],
        project: ProjectView | None = None,
    ) -> None:
        """Accept or refuse a hint for every unannotated parameter.

        Args:
            module: Parsed module.
            candidates: Proposed annotation sources by node identity.
            project: Cross-module view of the project, or ``None``.

        """
        known: frozenset[str] = _imported_names(module=module) | _importable(
            module=module,
        )
        counts: dict[str, int] = binding_counts(module=module)
        bindings: CallBindings = CallBindings(module=module, counts=counts)
        escaped: frozenset[str] = _escaped_names(module=module)
        constants: dict[str, str] = module_constants(
            module=module,
            counts=counts,
        )
        qualifieds: dict[int, str] = (
            qualified_names(module=module, name=project.module)
            if project is not None
            else {}
        )
        accepted: dict[int, dict[str, str]] = self._accepted
        for _pass in range(Constants.propagation_passes):
            sites: dict[tuple[int, str], list[_Site]] = _call_sites(
                module=module,
                counts=counts,
                bindings=bindings,
                accepted=accepted,
                project=project,
            )
            if not self._judge_pass(
                module=module,
                context=_Judging(
                    candidates=candidates,
                    known=known,
                    escaped=escaped,
                    counts=counts,
                    constants=constants,
                    project=project,
                    qualifieds=qualifieds,
                ),
                sites=sites,
                accepted=accepted,
            ):
                break

    def _judge_pass(
        self,
        *,
        module: CommentedModule,
        context: _Judging,
        sites: dict[tuple[int, str], list[_Site]],
        accepted: dict[int, dict[str, str]],
    ) -> bool:
        """Judge every parameter not yet hinted, once.

        Args:
            module: Parsed module.
            context: Candidates, importable names and escaped functions.
            sites: Call-site evidence by function identity and parameter.
            accepted: Accepted hint sources by function identity and
                parameter name, extended in place.

        Returns:
            Whether any parameter gained a hint in this pass.

        """
        gained: bool = False
        for function in walk(node=module):
            if not isinstance(
                function,
                (FunctionDef, AsyncFunctionDef),
            ):
                continue
            for position, (parameter, default) in enumerate(
                iterable=_parameters(function=function),
            ):
                key: Key = _key(node=parameter)
                if parameter.annotation is not None or key in self._hints:
                    continue
                if position == 0 and parameter.arg in Constants.skipped_names:
                    continue
                self._judge(
                    parameter=parameter,
                    default=default,
                    candidate=context.candidates.get(key),
                    evidence=_Evidence(
                        sites=sites.get((id(function), parameter.arg), []),
                        escaped=context.function_escaped(
                            function=function,
                        ),
                        default_type=_default_type(
                            default=default,
                            context=context,
                        ),
                    ),
                    known=context.known,
                )
                hint: Hint | None = self._hints.get(key)
                if hint is not None:
                    accepted.setdefault(id(function), {})[parameter.arg] = (
                        hint.source
                    )
                    gained = True
            self._judge_variadics(
                function=function,
                context=context,
                sites=sites,
            )
        return gained

    def _judge_variadics(
        self,
        *,
        function: Function,
        context: _Judging,
        sites: dict[tuple[int, str], list[_Site]],
    ) -> None:
        """Judge ``*args`` and ``**kwargs`` from what callers pass.

        Only call-site evidence is used: an inferred candidate describes the
        tuple or dict the name is bound to, not the element type annotated.
        The hint is not fed back as the name's type for the same reason.

        Args:
            function: Function definition.
            context: Importable names and escaped functions.
            sites: Call-site evidence by function identity and parameter.

        """
        for parameter in _variadics(function=function):
            key: Key = _key(node=parameter)
            if parameter.annotation is not None or key in self._hints:
                continue
            self._judge(
                parameter=parameter,
                default=None,
                candidate=None,
                evidence=_Evidence(
                    sites=sites.get((id(function), parameter.arg), []),
                    escaped=context.function_escaped(function=function),
                ),
                known=context.known,
            )

    def _accepted_parameters(self, *, function: Function) -> frozenset[str]:
        """List the parameters of a function that have an accepted hint.

        Args:
            function: Function definition.

        Returns:
            Parameter names with a hint.

        """
        return frozenset(
            (
                parameter.arg
                for parameter, _default in _parameters(function=function)
                if self.hint_for(node=parameter) is not None
            ),
        )

    def _trusted_receiver(
        self,
        *,
        function: Function,
        owner: ClassDef | None,
    ) -> str | None:
        """Name the receiver whose attribute reads the class table types.

        The receiver is trusted only while nothing in the method rebinds it.

        Args:
            function: Method definition.
            owner: Class the method belongs to, if any.

        Returns:
            The receiver name, or ``None`` when the table does not apply.

        """
        if owner is None or id(owner) not in self._attribute_types:
            return None
        receiver: str | None = receiver_of(function=function)
        if receiver is None or any(
            isinstance(node, Name)
            and node.id == receiver
            and not isinstance(node.ctx, Load)
            for node in own_nodes(function=function)
        ):
            return None
        return receiver

    def _known_types(self, *, function: Function) -> dict[str, str]:
        """Collect the types of a function's parameters.

        Args:
            function: Function definition.

        Returns:
            Parameter names mapped to an accepted hint or a usable
            declared annotation.

        """
        types: dict[str, str] = {}
        for parameter, _default in _parameters(function=function):
            hint: Hint | None = self.hint_for(node=parameter)
            if hint is not None:
                types[parameter.arg] = hint.source
            elif parameter.annotation is not None:
                types[parameter.arg] = unparse(
                    ast_obj=parameter.annotation,
                )
        return types

    def _judge_unproven(
        self,
        *,
        function: Function,
        candidate: str | None,
        tainted: str | None,
    ) -> None:
        """Decide a return the prover could not type.

        Only a candidate from a category measured as reliable is accepted;
        everything else is refused with the reason.

        Args:
            function: Function definition.
            candidate: Proposed annotation source, if any.
            tainted: The untyped parameter the return depends on, if any.

        """
        key: Key = _key(node=function)
        if (
            tainted is not None
            and candidate is not None
            and candidate in Constants.calibrated_returns
            and not _is_generator(function=function)
            and all(
                _boolean_by_syntax(node=value)
                for value in _value_returns(function=function)
            )
        ):
            self._hints[key] = Hint(
                source=candidate,
                basis=HintBasis.calibrated_candidate,
            )
        else:
            self._rejections[key] = (
                Rejection.not_provable
                if tainted is None
                else f"{Rejection.tainted} {tainted}"
            )

    def _judge_derived(
        self,
        *,
        function: Function,
        candidate: str | None,
        known: frozenset[str],
        counts: dict[str, int],
        owner: ClassDef | None,
    ) -> None:
        """Decide a derived return hint.

        Args:
            function: Function definition.
            candidate: Proposed annotation source, if any.
            known: Names a new annotation may use.
            counts: Module binding counts.
            owner: Class the function is a method of, if any.

        """
        key: Key = _key(node=function)
        types: dict[str, str] = self._known_types(function=function)
        accepted: frozenset[str] = self._accepted_parameters(function=function)
        receiver: str | None = self._trusted_receiver(
            function=function,
            owner=owner,
        )
        if receiver is not None and owner is not None:
            types.update(
                {
                    f"{receiver}.{name}": kind
                    for name, kind in self._attribute_types[id(owner)].items()
                },
            )
            accepted = accepted | {receiver}
        proved, guaranteed = provable_return_detail(
            function=function,
            known_types=types,
            counts=counts,
        )
        origins: dict[str, str] = _taint_origins(
            function=function,
            accepted=accepted,
        )
        tainted: str | None = next(
            (
                found
                for value in _value_returns(function=function)
                if (found := _mentions(node=value, names=origins)) is not None
            ),
            None,
        )
        if proved is None:
            self._judge_unproven(
                function=function,
                candidate=candidate,
                tainted=tainted,
            )
            return
        if not is_allowed_source(source=proved, known_names=known):
            self._rejections[key] = Rejection.needs_import
            return
        if guaranteed:
            self._hints[key] = Hint(
                source=proved,
                basis=HintBasis.syntax_proven,
            )
            return
        if tainted is not None:
            self._rejections[key] = f"{Rejection.tainted} {tainted}"
            return
        if candidate is None:
            self._rejections[key] = Rejection.no_candidate
            return
        if (
            candidate != proved
            and not (
                receiver is not None
                and _drops_none(candidate=candidate, proved=proved)
            )
            and not (
                any(" | " in kind for kind in types.values())
                and _refines(candidate=candidate, proved=proved)
            )
        ):
            self._rejections[key] = Rejection.engine_disagrees
            return
        self._hints[key] = Hint(source=proved, basis=HintBasis.derived_return)

    def _judge(
        self,
        *,
        parameter: arg,
        default: expr | None,
        candidate: str | None,
        evidence: _Evidence,
        known: frozenset[str],
    ) -> None:
        """Decide one parameter and record the outcome.

        Args:
            parameter: Parameter node.
            default: Default value expression, if any.
            candidate: Proposed annotation source, if any.

            evidence: What the module shows about the parameter's callers.
            known: Names a new annotation may use.

        """
        key: Key = _key(node=parameter)
        if isinstance(default, Constant) and default.value is None:
            self._judge_optional(key=key, evidence=evidence, known=known)
            return
        if candidate is None:
            candidate = _proven_site_type(evidence=evidence)
        if candidate is None:
            self._rejections[key] = Rejection.no_candidate
            return
        if not is_allowed_source(source=candidate, known_names=known):
            reason: str = (
                Rejection.contains_object
                if any(name in candidate for name in Constants.banned_names)
                else Rejection.needs_import
            )
            self._rejections[key] = reason
            return
        literal: str | None = (
            type(default.value).__name__
            if isinstance(default, Constant)
            and type(default.value).__name__ in Constants.scalar_types
            else evidence.default_type
        )
        if literal is not None:
            if literal == candidate:
                self._hints[key] = Hint(
                    source=candidate,
                    basis=(
                        HintBasis.call_sites
                        if _call_sites_agree(evidence=evidence, kind=literal)
                        else HintBasis.default_literal
                    ),
                )
            else:
                self._rejections[key] = Rejection.default_disagrees
            return
        self._judge_call_sites(key=key, candidate=candidate, evidence=evidence)

    def _judge_optional(
        self,
        *,
        key: Key,
        evidence: _Evidence,
        known: frozenset[str],
    ) -> None:
        """Decide a parameter whose default is ``None``.

        The type is ``T | None`` when every call site that passes a value
        proves the same ``T`` from the syntax of its argument, and at least
        one site passes a value. Sites that pass ``None`` add nothing.

        Args:
            key: Parameter node key.
            evidence: What the module shows about the parameter's callers.
            known: Names a new annotation may use.

        """
        if evidence.escaped:
            self._rejections[key] = Rejection.escapes
            return
        passed: set[str] = set()
        for site in evidence.sites:
            if not (site.proven and len(site.types) == 1):
                self._rejections[key] = Rejection.call_sites_unknown
                return
            if site.types[0] != "None":
                passed.add(site.types[0])
        if not passed:
            self._rejections[key] = Rejection.none_default
            return
        if len(passed) != 1:
            self._rejections[key] = Rejection.call_sites_disagree
            return
        source: str = f"{next(iter(passed))} | None"
        if not is_allowed_source(source=source, known_names=known):
            self._rejections[key] = Rejection.needs_import
            return
        self._hints[key] = Hint(
            source=source,
            basis=HintBasis.optional_default,
        )

    def _judge_call_sites(
        self,
        *,
        key: Key,
        candidate: str,
        evidence: _Evidence,
    ) -> None:
        """Compare a candidate with the types passed at call sites.

        Args:
            key: Parameter node key.
            candidate: Proposed annotation source.
            evidence: What the module shows about the parameter's callers.

        """
        if evidence.escaped:
            self._rejections[key] = Rejection.escapes
            return
        if not evidence.sites:
            self._rejections[key] = Rejection.uncorroborated
            return
        if any(
            (not site.definite or len(site.types) != 1)
            for site in evidence.sites
        ):
            self._rejections[key] = Rejection.call_sites_unknown
            return
        seen: set[str] = {site.types[0] for site in evidence.sites}
        if seen == {candidate}:
            self._hints[key] = Hint(
                source=candidate,
                basis=HintBasis.call_sites,
            )
        else:
            union: str | None = _site_union(
                evidence=evidence,
                candidate=candidate,
            )
            if union is None:
                self._rejections[key] = Rejection.call_sites_disagree
            else:
                self._hints[key] = Hint(
                    source=union,
                    basis=HintBasis.union_sites,
                )


def _union_members(*, source: str) -> tuple[str, ...]:
    """Split a ``A | B | C`` annotation into its members.

    Args:
        source: Annotation source.

    Returns:
        The unparsed top-level members in source order; one element when it
        is no union.

    """
    try:
        tree: Expression = parse(source=source, mode="eval")
    except SyntaxError:
        return (source,)
    pending: list[expr] = [tree.body]
    members: list[str] = []
    while pending:
        node: expr = pending.pop()
        if isinstance(node, BinOp) and isinstance(node.op, BitOr):
            pending.extend((node.right, node.left))
        else:
            members.append(unparse(ast_obj=node))
    return tuple(dict.fromkeys(members))


def _site_union(*, evidence: _Evidence, candidate: str) -> str | None:
    """Spell the union of the call sites when the candidate corroborates it.

    Every site must be syntax-proven, the types must differ, there must be at
    most ``Constants.max_union_members`` of them, and the inference
    candidate must name precisely that set (the second, independent signal).
    ``bool`` is dropped beside ``int`` because it is a subtype.

    Args:
        evidence: What the module shows about the parameter's callers.
        candidate: Proposed annotation source.

    Returns:
        The annotation source, or ``None`` when the union is not corroborated.

    """
    if not all(site.proven for site in evidence.sites):
        return None
    seen: frozenset[str] = frozenset(site.types[0] for site in evidence.sites)
    members: tuple[str, ...] = _union_members(source=candidate)
    if not (
        1 < len(seen) <= Constants.max_union_members
        and "None" not in seen
        and frozenset(members) == seen
    ):
        return None
    kept: tuple[str, ...] = tuple(
        item for item in members if not (item == "bool" and "int" in seen)
    )
    return " | ".join(kept)


def _candidates(
    *,
    module: CommentedModule,
    stubs_path: Path,
) -> dict[Key, str]:
    """Collect the inference pipeline's parameter and return proposals.

    Args:
        module: Parsed module.
        stubs_path: Stub directory handed to the pipeline.

    Returns:
        Proposed annotation sources by target node position.

    """
    try:
        proposals: tuple[GraphAnnotation, ...] = module.convert(
            stubs_path=stubs_path,
            apply=False,
        ).proposals
    except Constants.inference_errors:
        return {}
    return {
        _key(node=proposal.target): proposal.source
        for proposal in proposals
        if proposal.role in Constants.proposal_roles
    }


def _proven_site_type(*, evidence: _Evidence) -> str | None:
    """Find the type every call site's syntax proves, when they all agree.

    Args:
        evidence: What the module shows about the parameter's callers.

    Returns:
        The single proven type, or ``None``.

    """
    if evidence.escaped or not evidence.sites:
        return None
    if not all(
        site.proven and len(site.types) == 1 for site in evidence.sites
    ):
        return None
    seen: set[str] = {site.types[0] for site in evidence.sites}
    return next(iter(seen)) if len(seen) == 1 else None


def _argument_evidence(
    *,
    argument: BoundArgument,
    counts: dict[str, int],
    env: Mapping[str, str],
) -> _Site:
    """Turn one bound argument into call-site evidence.

    Only what the argument expression's syntax proves counts. The analyzer's
    own type for the argument is not independent evidence (it comes from the
    same inference that proposes the candidates, and is wrong in cases like
    ``True + True``), so it is not consulted.

    Args:
        argument: Bound argument of a direct call.
        counts: Module binding counts.
        env: Types of the names visible at the call, from its scope.

    Returns:
        The site's trust, rendered spellings, and whether syntax proves them.

    """
    proofs: set[str | None] = {
        expression_type(node=value, counts=counts, env=env)
        for value in argument.values
    }
    syntax: str | None = (
        next(iter(proofs))
        if argument.values and len(proofs) == 1 and None not in proofs
        else None
    )
    if syntax is None or syntax.startswith(Constants.shape_specific):
        return _Site(definite=False, types=())
    return _Site(definite=True, types=(syntax,), proven=True)


def _call_sites_agree(*, evidence: _Evidence, kind: str) -> bool:
    """Tell whether every in-module call independently proves one type.

    A literal default alone matches the original annotation only about 70 %
    of the time for ``int`` and ``str``; callers that all pass that type are
    the second signal that lifts it to the strong tier.

    Args:
        evidence: What the module shows about the parameter's callers.
        kind: The default literal's type.

    Returns:
        ``True`` when there are call sites and all prove ``kind``.

    """
    return (
        not evidence.escaped
        and bool(evidence.sites)
        and all(
            site.definite and site.proven and site.types == (kind,)
            for site in evidence.sites
        )
    )


def _boolean_by_syntax(*, node: AST) -> bool:
    """Tell whether an expression is boolean because of how it is written.

    The calibration behind ``Constants.calibrated_returns`` was measured on
    results like these; a bare name that merely *happens* to carry a ``bool``
    elsewhere is not covered by it.

    Args:
        node: A returned expression.

    Returns:
        ``True`` for comparisons, ``not``, ``and``/``or`` of such
        expressions, ``bool`` constants and calls of builtin predicates.

    """
    match node:
        case Compare() | UnaryOp(op=Not()):
            return True
        case Constant(value=bool()):
            return True
        case BoolOp(values=values):
            return all(_boolean_by_syntax(node=item) for item in values)
        case Call(func=Name(id=name)):
            return name in Constants.predicate_calls
        case _:
            return False


def _refines(*, candidate: str, proved: str) -> bool:
    """Tell whether the proof is a strict part of the candidate's union.

    Flow narrowing (``isinstance``, ``is None``) can prove less than the
    inference layer's union; such a proof refines the candidate instead of
    contradicting it.

    Args:
        candidate: Inference candidate source.
        proved: Syntax-proven source.

    Returns:
        ``True`` when every arm of ``proved`` is an arm of ``candidate`` and
        some arm of ``candidate`` is missing from ``proved``.

    """
    mine: set[str] = set(proved.split(sep=" | "))
    theirs: set[str] = set(candidate.split(sep=" | "))
    return mine < theirs


def _drops_none(*, candidate: str, proved: str) -> bool:
    """Tell whether the inference candidate is the proof minus ``None``.

    The inference layer reports the non-``None`` part of an attribute that
    starts out ``None``; the class's own writes show the ``None`` too.

    Args:
        candidate: Inference candidate source.
        proved: Syntax-proven source.

    Returns:
        ``True`` when both name the same types apart from ``None``.

    """
    kept: set[str] = set(proved.split(sep=" | ")) - {"None"}
    return kept == set(candidate.split(sep=" | ")) and kept != set()


def _default_type(*, default: expr | None, context: _Judging) -> str | None:
    """Prove the scalar type of a non-literal default expression.

    Args:
        default: Default value expression, if any.
        context: Binding counts and module constants.

    Returns:
        ``int``, ``str``, ``float``, ``bool`` or ``bytes`` when the syntax
        guarantees it, else ``None``.

    """
    if default is None or isinstance(default, Constant):
        return None
    proven: str | None = expression_type(
        node=default,
        counts=context.counts,
        env=context.constants,
    )
    return proven if proven in Constants.scalar_types else None


def _variadics(*, function: Function) -> list[arg]:
    """List a function's ``*args`` and ``**kwargs`` parameters.

    Args:
        function: Function definition.

    Returns:
        The variadic parameters that exist, positional one first.

    """
    arguments: arguments = function.args
    return [
        item
        for item in (arguments.vararg, arguments.kwarg)
        if item is not None
    ]


def _bound_evidence(
    *,
    argument: BoundArgument,
    counts: dict[str, int],
    env: Mapping[str, str],
) -> _Site | None:
    """Turn one bound argument into evidence for its parameter, if any.

    An argument that the binder could not resolve (``f(*xs)``) is unknown
    evidence, never absence. A variadic parameter that received nothing
    carries no evidence either way.

    Args:
        argument: Bound argument of a direct call.
        counts: Module binding counts.
        env: Types of the names visible at the call, from its scope.

    Returns:
        The site, or ``None`` when the argument says nothing.

    """
    origin: ArgumentOrigin = argument.origin
    if origin in Constants.variadic_origins:
        if not argument.definite:
            return _Site(definite=False, types=())
        if not argument.values:
            return None
    elif origin is ArgumentOrigin.EXPANSION_UNKNOWN:
        return _Site(definite=False, types=())
    elif origin not in (ArgumentOrigin.POSITIONAL, ArgumentOrigin.KEYWORD):
        return None
    return _argument_evidence(argument=argument, counts=counts, env=env)


def _scope_env(
    *,
    scope: Function,
    envs: dict[int, dict[str, str]],
    counts: dict[str, int],
    constants: dict[str, str],
    declared: Mapping[str, str] | None,
) -> dict[str, str]:
    """Return the types visible in a scope, computing them once per pass.

    Args:
        scope: Enclosing function.
        envs: Environments computed so far, by function identity.
        counts: Module binding counts.
        constants: Types of the module's constants.
        declared: Parameter hints already accepted for the scope.

    Returns:
        The scope's environment.

    """
    found: dict[str, str] | None = envs.get(id(scope))
    if found is None:
        found = envs[id(scope)] = scope_types(
            function=scope,
            counts=counts,
            constants=constants,
            declared=declared,
        )
    return found


def _call_sites(
    *,
    module: CommentedModule,
    counts: dict[str, int],
    bindings: CallBindings,
    accepted: Mapping[int, Mapping[str, str]],
    project: ProjectView | None = None,
) -> dict[tuple[int, str], list[_Site]]:
    """Index argument types by callee definition and parameter name.

    Direct calls to a function that cannot be bound (for example because an
    argument comes from a loop or ``with`` target) count as unknown evidence
    for every parameter, never as absent.

    Args:
        module: Parsed module.
        counts: Module binding counts.
        bindings: Trusted call bindings of the module.
        accepted: Hints already accepted for parameters, by function identity
            and parameter name; they type the names callers pass on.
        project: Cross-module view of the project, or ``None``.

    Returns:
        For each (definition identity, parameter name), one entry per call
        site: whether the type is trustworthy and its rendered spellings.

    """
    functions: dict[str, Function] = {
        node.name: node
        for node in walk(node=module)
        if isinstance(node, (FunctionDef, AsyncFunctionDef))
        and counts.get(node.name, 0) == 1
    }
    index: dict[tuple[int, str], list[_Site]] = {}
    constants: dict[str, str] = module_constants(module=module, counts=counts)
    scopes: dict[int, Function] = {
        id(inner): function
        for function in walk(node=module)
        if isinstance(function, (FunctionDef, AsyncFunctionDef))
        for inner in own_calls(function=function)
    }
    envs: dict[int, dict[str, str]] = {}
    for call in walk(node=module):
        if not isinstance(call, Call):
            continue
        scope: Function | None = scopes.get(id(call))
        if scope is None:
            env: dict[str, str] = constants
        else:
            env = _scope_env(
                scope=scope,
                envs=envs,
                counts=counts,
                constants=constants,
                declared=accepted.get(id(scope)),
            )
        bound: BoundCall | None = bindings.get(call=call)
        if bound is not None and bound.signature.declaration is not None:
            owner: int = id(bound.signature.declaration)
            for argument in bound.arguments:
                site: _Site | None = _bound_evidence(
                    argument=argument,
                    counts=counts,
                    env=env,
                )
                if site is not None:
                    index.setdefault(
                        (owner, argument.parameter.name),
                        [],
                    ).append(site)
            continue
        target: Function | None = (
            functions.get(call.func.id)
            if isinstance(call.func, Name)
            else None
        )
        if target is not None:
            for parameter in (
                *(item for item, _default in _parameters(function=target)),
                *_variadics(function=target),
            ):
                index.setdefault((id(target), parameter.arg), []).append(
                    _Site(definite=False, types=()),
                )
    if project is not None:
        _merge_project_sites(
            index=index,
            module=module,
            project=project,
            qualifieds=qualified_names(
                module=module,
                name=project.module,
            ),
        )
    return index


def _merge_project_sites(
    *,
    index: dict[tuple[int, str], list[_Site]],
    module: CommentedModule,
    project: ProjectView,
    qualifieds: Mapping[int, str],
) -> None:
    """Add cross-module call evidence to the site index.

    A qualified name claimed by more than one definition (a function
    defined in both branches of an ``if``, a method defined twice) is
    ambiguous and contributes nothing — the index's record may describe
    the other one.

    Args:
        index: The site index, extended in place.
        module: Parsed module.
        project: Cross-module view of the project.
        qualifieds: ``id`` of each definition to its qualified name.

    """
    counts: dict[str, int] = {}
    for qualified in qualifieds.values():
        counts[qualified] = counts.get(qualified, 0) + 1
    for function in walk(node=module):
        if not isinstance(function, (FunctionDef, AsyncFunctionDef)):
            continue
        qualified: str | None = qualifieds.get(id(function))
        if qualified is None or counts.get(qualified, 0) != 1:
            continue
        extras: list[dict[str, tuple[CrossSite, ...]] | None] = [
            project.sites(qualified=qualified),
        ]
        if function.name in ("__init__", "__new__"):
            owner, _, _leaf = qualified.rpartition(".")
            extras.append(project.sites(qualified=owner))
        for extra in extras:
            if not extra:
                continue
            for name, sites in extra.items():
                index.setdefault((id(function), name), []).extend(
                    _Site(
                        definite=site.definite,
                        types=site.types,
                        proven=site.proven,
                    )
                    for site in sites
                )


@final
class HintCache:
    """Share hint indexes between parses of the same source text."""

    def __init__(self) -> None:
        """Start with no indexes."""
        self._entries: dict[
            tuple[str, str | None, tuple[int, int, str] | None],
            HintIndex,
        ] = {}

    def fetch(
        self,
        *,
        source: str,
        stubs_path: Path | None,
        build: Callable[[], HintIndex],
        project: ProjectView | None = None,
    ) -> HintIndex:
        """Return the index for a text, building it on the first request.

        Args:
            source: Source text the index describes.
            stubs_path: Stub directory used for inference.
            build: Builds the index when it is not cached.
            project: Cross-module view the hints were computed with; the
                index's identity and version discriminate the cache key.

        Returns:
            The cached or newly built index.

        """
        key: tuple[str, str | None, tuple[int, int, str] | None] = (
            source,
            None if stubs_path is None else str(object=stubs_path),
            None
            if project is None
            else (id(project.index), project.index.version, project.module),
        )
        if key not in self._entries:
            self._entries[key] = build()
        return self._entries[key]


@final
class LazyHints:
    """Compute a module's :class:`HintIndex` on first use.

    Inference is the expensive part of a run, so rules that never read a
    hint never pay for it, and a shared :class:`HintCache` lets repeated
    parses of one text pay only once.
    """

    def __init__(
        self,
        *,
        module: CommentedModule,
        stubs_path: Path | None,
        source: str | None = None,
        cache: HintCache | None = None,
        project: ProjectView | None = None,
    ) -> None:
        """Remember what is needed to build the index.

        Args:
            module: Parsed module.
            stubs_path: Stub directory, or ``None`` for an empty one.
            source: Source text of the module, needed for caching.
            cache: Shared cache, or ``None`` to compute privately.
            project: Cross-module view of the project, or ``None``.

        """
        self._module: CommentedModule = module
        self._stubs_path: Path | None = stubs_path
        self._source: str | None = source
        self._cache: HintCache | None = cache
        self._project: ProjectView | None = project
        self._supplement: Callable[[HintIndex], Mapping[Key, Hint]] | None = (
            None
        )
        self._index: HintIndex | None = None

    def supplemented(
        self,
        *,
        by: Callable[[HintIndex], Mapping[Key, Hint]],
    ) -> Self:
        """Add hints from another source for nodes the index has none for.

        Args:
            by: Produces the extra hints from the built index.

        Returns:
            This object, for chaining.

        """
        self._supplement = by
        return self

    def index(self) -> HintIndex:
        """Return the index, building it on the first call.

        Returns:
            The module's hint index.

        """
        if self._index is None:

            def build() -> HintIndex:
                """Compute the index from scratch.

                Returns:
                    A freshly built hint index.

                """
                return HintIndex.create(
                    module=self._module,
                    stubs_path=self._stubs_path,
                    project=self._project,
                )

            if self._cache is not None and self._source is not None:
                self._index = self._cache.fetch(
                    source=self._source,
                    stubs_path=self._stubs_path,
                    build=build,
                    project=self._project,
                )
            else:
                self._index = build()
            if self._supplement is not None:
                self._index.supplement(hints=self._supplement(self._index))
        return self._index


def engine_proposals(*, module: CommentedModule) -> dict[Key, str]:
    """Run the inference engine and list its parameter and return proposals.

    Args:
        module: Parsed module.

    Returns:
        Proposed annotation sources by node position (see :func:`_key`).

    """
    with TemporaryDirectory() as scratch:
        return _candidates(module=module, stubs_path=Path(scratch))


def escaped_function_names(*, module: Module) -> frozenset[str]:
    """Collect names read anywhere other than as a direct callee.

    Args:
        module: Parsed module.

    Returns:
        Names used as values, which may reach callers the module cannot see.

    """
    return _escaped_names(module=module)


def node_key(*, node: AST) -> Key:
    """Identify a parameter or function by kind and source position.

    Args:
        node: Parameter or function node.

    Returns:
        (kind, line, column), the identity used by :class:`HintIndex`.

    """
    return _key(node=node)


def protocol_result_for(
    *,
    function: Function,
    counts: Mapping[str, int],
) -> str | None:
    """Give a protocol dunder its declared result when its body fits.

    Args:
        function: A function; only those listed in
            ``Constants.protocol_results`` can qualify.
        counts: Module binding counts.

    Returns:
        The declared result (``__len__`` gives ``int``), or ``None`` when the
        function is no protocol dunder, is a declaration or generator, or
        its body does not fit the declared type.

    """
    declared: str | None = Constants.protocol_results.get(function.name)
    if (
        declared is None
        or is_declaration(function=function)
        or _is_generator(function=function)
    ):
        return None
    allowed: set[str] = set(declared.split(sep=" | "))
    if "None" in allowed and _body_returns_nothing(function=function):
        return declared
    proved: str | None = provable_return_detail(
        function=function,
        known_types={},
        counts=counts,
    )[0]
    fits: bool = proved is not None and set(proved.split(sep=" | ")) <= allowed
    return declared if fits else None


def boolean_returns(*, function: Function) -> bool:
    """Tell whether every returned value is boolean by how it is written.

    This is the category the calibrated-candidate rule was measured on.

    Args:
        function: Function definition.

    Returns:
        ``True`` for a non-generator that returns at least one value, all of
        them comparisons, ``not``, ``bool`` constants, predicate calls or
        ``and``/``or`` of those.

    """
    values: list[expr] = _value_returns(function=function)
    return (
        bool(values)
        and not _is_generator(function=function)
        and all(_boolean_by_syntax(node=value) for value in values)
    )


def allowed_names(*, module: Module) -> frozenset[str]:
    """List the names a new annotation of this module may use.

    Args:
        module: Parsed module.

    Returns:
        Imported names plus those a fix can import on its own.

    """
    return _imported_names(module=module) | _importable(module=module)
