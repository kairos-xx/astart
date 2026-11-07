"""Corroborated type hints: candidates are accepted only with evidence."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, Self, final

from astart.rules.imports import Constants as ImportConstants
from astart.rules.imports import bound_names
from astart.rules.provable import expression_type, provable_return
from astart.rules.resolve import CallBindings, binding_counts
from astart.semantic import ArgumentOrigin

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from astart import BoundArgument, CommentedModule
type Function = ast.FunctionDef | ast.AsyncFunctionDef


class HintBasis(StrEnum):
    """Why a hint was accepted.

    Attributes:
        proven_none: The function provably returns nothing.
        default_literal: The default value's literal type agrees.
        call_sites: Every in-module call site agrees.
        derived_return: The return type depends only on typed names.

    """

    proven_none = "proven_none"
    default_literal = "default_literal"
    call_sites = "call_sites"
    derived_return = "derived_return"


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
        builtin_names: Grouped module constant.
        banned_names: Grouped module constant.
        scalar_types: Grouped module constant.
        expression_nodes: Grouped module constant.
        proposal_roles: Grouped module constant.
        skipped_names: Grouped module constant.
        declaration_decorators: Grouped module constant.
        scope_nodes: Grouped module constant.

    """

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
    expression_nodes: Final[tuple[type[ast.AST], ...]] = (
        ast.Expression,
        ast.Name,
        ast.Attribute,
        ast.Subscript,
        ast.Tuple,
        ast.List,
        ast.BinOp,
        ast.BitOr,
        ast.Load,
        ast.Constant,
    )
    proposal_roles: Final[frozenset[str]] = frozenset({"parameter", "return"})
    skipped_names: Final[frozenset[str]] = frozenset({"self", "cls"})
    declaration_decorators: Final[frozenset[str]] = frozenset(
        {"overload", "abstractmethod"},
    )
    scope_nodes: Final[tuple[type[ast.AST], ...]] = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Lambda,
    )


type Key = tuple[str, int, int]


def _key(*, node: ast.AST) -> Key:
    """Identify a parameter or function by kind and source position.

    Positions are identical in every parse of the same text, so hints
    computed on one parse can be looked up on another.

    Args:
        node: Parameter or function node.

    Returns:
        (kind, line, column).

    """
    return (
        "arg" if isinstance(node, ast.arg) else "def",
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
        tree: ast.Expression = ast.parse(source=source, mode="eval")
    except SyntaxError:
        return False
    allowed: frozenset[str] = Constants.builtin_names | known_names
    for node in ast.walk(node=tree):
        if not isinstance(node, Constants.expression_nodes):
            return False
        match node:
            case ast.Name(id=name):
                if name in Constants.banned_names or name not in allowed:
                    return False
            case ast.Constant(value=value):
                if value is not None and value is not Ellipsis:
                    return False
            case _:
                continue
    return True


def _importable(*, module: ast.Module) -> frozenset[str]:
    """List known names a new annotation may use because they can be imported.

    Args:
        module: Parsed module.

    Returns:
        Importable names the module does not already bind to something else.

    """
    return frozenset(ImportConstants.known_imports) - bound_names(
        module=module,
    )


def _imported_names(*, module: ast.Module) -> frozenset[str]:
    """Collect names bound by imports and by top-level definitions.

    Args:
        module: Parsed module.

    Returns:
        Names available to a new annotation.

    """
    names: set[str] = set()
    for node in ast.walk(node=module):
        match node:
            case ast.alias(name=name, asname=asname):
                names.add(asname or name.split(sep=".")[0])
            case ast.ClassDef(name=name):
                names.add(name)
            case _:
                continue
    return frozenset(names)


def _parameters(
    *,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[ast.arg, ast.expr | None]]:
    """Pair each plain parameter with its default.

    Args:
        function: Function definition.

    Returns:
        Positional-only, positional and keyword-only parameters.

    """
    arguments: ast.arguments = function.args
    positional: list[ast.arg] = [*arguments.posonlyargs, *arguments.args]
    offset: int = len(positional) - len(arguments.defaults)
    pairs: list[tuple[ast.arg, ast.expr | None]] = [
        (
            parameter,
            arguments.defaults[index - offset] if index >= offset else None,
        )
        for index, parameter in enumerate(iterable=positional)
    ]
    pairs.extend(zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True))
    return pairs


def own_nodes(*, function: Function) -> Iterator[ast.AST]:
    """Walk a function body without entering nested scopes.

    Args:
        function: Function definition.

    Yields:
        Every node that belongs to the function itself.

    """
    stack: list[ast.AST] = [
        statement
        for statement in reversed(function.body)
        if not isinstance(statement, Constants.scope_nodes)
    ]
    while stack:
        node: ast.AST = stack.pop()
        yield node
        stack.extend(
            child
            for child in reversed(list(ast.iter_child_nodes(node=node)))
            if not isinstance(child, Constants.scope_nodes)
        )


def _is_stub_statement(*, statement: ast.stmt) -> bool:
    """Report whether a statement carries no behaviour.

    Args:
        statement: Statement from a function body.

    Returns:
        Whether it is ``pass``, a docstring, ``...`` or a
        ``NotImplementedError`` raise.

    """
    match statement:
        case ast.Pass() | ast.Expr(value=ast.Constant()):
            return True
        case ast.Raise(exc=exc):
            target: ast.expr | None = (
                exc.func if isinstance(exc, ast.Call) else exc
            )
            return (
                isinstance(target, ast.Name)
                and target.id == "NotImplementedError"
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
            if isinstance(decorator, ast.Name)
            else decorator.attr
            if isinstance(decorator, ast.Attribute)
            else None
        )
        if name in Constants.declaration_decorators:
            return True
    return all(_is_stub_statement(statement=s) for s in function.body)


def _value_returns(*, function: Function) -> list[ast.expr]:
    """Collect the expressions of ``return <value>`` statements.

    Args:
        function: Function definition.

    Returns:
        Return expressions, ignoring bare and ``return None`` statements.

    """
    return [
        node.value
        for node in own_nodes(function=function)
        if isinstance(node, ast.Return)
        and node.value is not None
        and (
            not (
                isinstance(node.value, ast.Constant)
                and node.value.value is None
            )
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
        isinstance(node, (ast.Yield, ast.YieldFrom))
        for node in own_nodes(function=function)
    )


def returns_nothing(*, function: Function) -> bool:
    """Prove that a function always returns ``None``.

    Args:
        function: Function definition.

    Returns:
        Whether it has no returned value, does not yield, and is not a
        declaration (overload, abstract method or stub body).

    """
    return not (
        is_declaration(function=function)
        or _is_generator(function=function)
        or _value_returns(function=function)
    )


def _mentions(*, node: ast.AST, names: dict[str, str]) -> str | None:
    """Find the first tainted name an expression mentions.

    Args:
        node: Expression or statement part.
        names: Tainted names mapped to their originating parameter.

    Returns:
        The originating parameter, or ``None``.

    """
    for inner in ast.walk(node=node):
        if isinstance(inner, ast.Name) and inner.id in names:
            return names[inner.id]
    return None


def _targets(*, node: ast.AST) -> list[str]:
    """List the names bound by an assignment target.

    Args:
        node: Target expression.

    Returns:
        The stored names.

    """
    return [
        inner.id
        for inner in ast.walk(node=node)
        if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Store)
    ]


def _spread(*, node: ast.AST, names: dict[str, str]) -> bool:
    """Spread taint through one statement or expression.

    Args:
        node: Node from the function body.
        names: Tainted names, extended in place.

    Returns:
        Whether a new name became tainted.

    """
    pairs: list[tuple[ast.AST, ast.AST]] = []
    match node:
        case ast.Assign(targets=targets, value=value):
            pairs = [(target, value) for target in targets]
        case ast.AugAssign(target=target, value=value):
            pairs = [(target, value)]
        case (
            ast.For(target=target, iter=source)
            | ast.AsyncFor(target=target, iter=source)
        ):
            pairs = [(target, source)]
        case ast.NamedExpr(target=target, value=value):
            pairs = [(target, value)]
        case ast.withitem(context_expr=source, optional_vars=target) if (
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
    arguments: ast.arguments = function.args
    parameters: list[ast.arg] = [
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
class _Evidence:
    """What the module shows about a function's parameter types.

    Attributes:
        sites: One entry per direct call: whether the argument type is
            definite, and its rendered spellings.
        escaped: Whether the function is also used as a value (aliased,
            passed as a callback, stored), so its callers cannot be known.

    """

    sites: list[tuple[bool, tuple[str, ...]]]
    escaped: bool


def _escaped_names(*, module: ast.Module) -> frozenset[str]:
    """Collect names that are read anywhere other than as a direct callee.

    Args:
        module: Parsed module.

    Returns:
        Names used as values, which may reach callers the module cannot see.

    """
    callees: set[int] = {
        id(call.func)
        for call in ast.walk(node=module)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    return frozenset(
        node.id
        for node in ast.walk(node=module)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
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

    @classmethod
    def create(
        cls,
        *,
        module: CommentedModule,
        stubs_path: Path | None,
    ) -> Self:
        """Compute hints for every unannotated parameter of a module.

        Args:
            module: Parsed module.
            stubs_path: Stub directory, or ``None`` for an empty one.

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
        index.judge_parameters(module=module, candidates=candidates)
        index.judge_returns(
            module=module,
            candidates=candidates,
            counts=binding_counts(module=module),
        )
        return index

    def hint_for(self, *, node: ast.AST) -> Hint | None:
        """Return the accepted hint for a node, if any.

        Args:
            node: Parameter or function node.

        Returns:
            The hint or ``None``.

        """
        return self._hints.get(_key(node=node))

    def rejection_for(self, *, node: ast.AST) -> str | None:
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
        for function in ast.walk(node=module):
            if (
                not isinstance(
                    function,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
                or function.returns is not None
            ):
                continue
            key: Key = _key(node=function)
            if returns_nothing(function=function):
                self._hints[key] = Hint(
                    source="None",
                    basis=HintBasis.proven_none,
                )
                continue
            if is_declaration(function=function):
                self._rejections[key] = "declaration body"
            elif _is_generator(function=function):
                self._rejections[key] = "generator"
            else:
                self._judge_derived(
                    function=function,
                    candidate=candidates.get(key),
                    known=known,
                    counts=counts,
                )

    def judge_parameters(
        self,
        *,
        module: CommentedModule,
        candidates: dict[Key, str],
    ) -> None:
        """Accept or refuse a hint for every unannotated parameter.

        Args:
            module: Parsed module.
            candidates: Proposed annotation sources by node identity.

        """
        known: frozenset[str] = _imported_names(module=module) | _importable(
            module=module,
        )
        sites: dict[tuple[int, str], list[tuple[bool, tuple[str, ...]]]] = (
            _call_sites(module=module)
        )
        escaped: frozenset[str] = _escaped_names(module=module)
        for function in ast.walk(node=module):
            if not isinstance(
                function,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue
            for position, (parameter, default) in enumerate(
                iterable=_parameters(function=function),
            ):
                if parameter.annotation is not None:
                    continue
                if position == 0 and parameter.arg in Constants.skipped_names:
                    continue
                self._judge(
                    parameter=parameter,
                    default=default,
                    candidate=candidates.get(_key(node=parameter)),
                    evidence=_Evidence(
                        sites=sites.get((id(function), parameter.arg), []),
                        escaped=function.name in escaped,
                    ),
                    known=known,
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
                types[parameter.arg] = ast.unparse(
                    ast_obj=parameter.annotation,
                )
        return types

    def _judge_derived(
        self,
        *,
        function: Function,
        candidate: str | None,
        known: frozenset[str],
        counts: dict[str, int],
    ) -> None:
        """Decide a derived return hint.

        Args:
            function: Function definition.
            candidate: Proposed annotation source, if any.
            known: Names a new annotation may use.
            counts: Module binding counts.

        """
        key: Key = _key(node=function)
        origins: dict[str, str] = _taint_origins(
            function=function,
            accepted=self._accepted_parameters(function=function),
        )
        for value in _value_returns(function=function):
            origin: str | None = _mentions(node=value, names=origins)
            if origin is not None:
                self._rejections[key] = f"tainted by parameter {origin}"
                return
        proved: str | None = provable_return(
            function=function,
            known_types=self._known_types(function=function),
            counts=counts,
        )
        if proved is None:
            self._rejections[key] = "return type not provable"
            return
        if not is_allowed_source(source=proved, known_names=known):
            self._rejections[key] = "needs import or unknown name"
            return
        if candidate is None:
            self._rejections[key] = "no candidate"
            return
        if candidate != proved:
            self._rejections[key] = "engine disagrees"
            return
        self._hints[key] = Hint(source=proved, basis=HintBasis.derived_return)

    def _judge(
        self,
        *,
        parameter: ast.arg,
        default: ast.expr | None,
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
        if isinstance(default, ast.Constant) and default.value is None:
            self._rejections[key] = "None default"
            return
        if candidate is None:
            self._rejections[key] = "no candidate"
            return
        if not is_allowed_source(source=candidate, known_names=known):
            reason: str = (
                "contains object"
                if any(name in candidate for name in Constants.banned_names)
                else "needs import or unknown name"
            )
            self._rejections[key] = reason
            return
        literal: str | None = (
            type(default.value).__name__
            if isinstance(default, ast.Constant)
            and type(default.value).__name__ in Constants.scalar_types
            else None
        )
        if literal is not None:
            if literal == candidate:
                self._hints[key] = Hint(
                    source=candidate,
                    basis=HintBasis.default_literal,
                )
            else:
                self._rejections[key] = "default disagrees"
            return
        self._judge_call_sites(key=key, candidate=candidate, evidence=evidence)

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
            self._rejections[key] = "escapes as a value"
            return
        if not evidence.sites:
            self._rejections[key] = "uncorroborated"
            return
        if any(
            (
                not definite or len(types) != 1
                for definite, types in evidence.sites
            ),
        ):
            self._rejections[key] = "call sites unknown"
            return
        seen: set[str] = {types[0] for _definite, types in evidence.sites}
        if seen == {candidate}:
            self._hints[key] = Hint(
                source=candidate,
                basis=HintBasis.call_sites,
            )
        else:
            self._rejections[key] = "call sites disagree"


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
    return {
        _key(node=proposal.target): proposal.source
        for proposal in module.convert(
            stubs_path=stubs_path,
            apply=False,
        ).proposals
        if proposal.role in Constants.proposal_roles
    }


def _argument_evidence(
    *,
    argument: BoundArgument,
    counts: dict[str, int],
) -> tuple[bool, tuple[str, ...]]:
    """Turn one bound argument into call-site evidence.

    The analyzer's type is cross-checked against what the argument
    expression's syntax proves; a disagreement makes the evidence unknown.

    Args:
        argument: Bound argument of a direct call.
        counts: Module binding counts.

    Returns:
        Whether the type is trustworthy, and its rendered spellings.

    """
    types: tuple[str, ...] = tuple(str(object=t) for t in argument.types)
    if not argument.definite:
        return (False, ())
    if len(types) == 1:
        for value in argument.values:
            proved: str | None = expression_type(node=value, counts=counts)
            if proved is not None and proved != types[0]:
                return (False, ())
    return (True, types)


def _call_sites(
    *,
    module: CommentedModule,
) -> dict[tuple[int, str], list[tuple[bool, tuple[str, ...]]]]:
    """Index argument types by callee definition and parameter name.

    Direct calls to a function that cannot be bound (for example because an
    argument comes from a loop or ``with`` target) count as unknown evidence
    for every parameter, never as absent.

    Args:
        module: Parsed module.

    Returns:
        For each (definition identity, parameter name), one entry per call
        site: whether the type is trustworthy and its rendered spellings.

    """
    counts: dict[str, int] = binding_counts(module=module)
    bindings: CallBindings = CallBindings(module=module, counts=counts)
    functions: dict[str, Function] = {
        node.name: node
        for node in ast.walk(node=module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and counts.get(node.name, 0) == 1
    }
    index: dict[tuple[int, str], list[tuple[bool, tuple[str, ...]]]] = {}
    for call in ast.walk(node=module):
        if not isinstance(call, ast.Call):
            continue
        bound = bindings.get(call=call)
        if bound is not None and bound.signature.declaration is not None:
            owner: int = id(bound.signature.declaration)
            for argument in bound.arguments:
                if argument.origin in (
                    ArgumentOrigin.POSITIONAL,
                    ArgumentOrigin.KEYWORD,
                ):
                    index.setdefault(
                        (owner, argument.parameter.name),
                        [],
                    ).append(
                        _argument_evidence(argument=argument, counts=counts),
                    )
            continue
        target: Function | None = (
            functions.get(call.func.id)
            if isinstance(call.func, ast.Name)
            else None
        )
        if target is not None:
            for parameter, _default in _parameters(function=target):
                index.setdefault((id(target), parameter.arg), []).append(
                    (False, ()),
                )
    return index


@final
class HintCache:
    """Share hint indexes between parses of the same source text."""

    def __init__(self) -> None:
        """Start with no indexes."""
        self._entries: dict[tuple[str, str | None], HintIndex] = {}

    def fetch(
        self,
        *,
        source: str,
        stubs_path: Path | None,
        build: Callable[[], HintIndex],
    ) -> HintIndex:
        """Return the index for a text, building it on the first request.

        Args:
            source: Source text the index describes.
            stubs_path: Stub directory used for inference.
            build: Builds the index when it is not cached.

        Returns:
            The cached or newly built index.

        """
        key: tuple[str, str | None] = (
            source,
            None if stubs_path is None else str(object=stubs_path),
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
    ) -> None:
        """Remember what is needed to build the index.

        Args:
            module: Parsed module.
            stubs_path: Stub directory, or ``None`` for an empty one.
            source: Source text of the module, needed for caching.
            cache: Shared cache, or ``None`` to compute privately.

        """
        self._module: CommentedModule = module
        self._stubs_path: Path | None = stubs_path
        self._source: str | None = source
        self._cache: HintCache | None = cache
        self._index: HintIndex | None = None

    def index(self) -> HintIndex:
        """Return the index, building it on the first call.

        Returns:
            The module's hint index.

        """
        if self._index is None:

            def build() -> HintIndex:
                return HintIndex.create(
                    module=self._module,
                    stubs_path=self._stubs_path,
                )

            if self._cache is not None and self._source is not None:
                self._index = self._cache.fetch(
                    source=self._source,
                    stubs_path=self._stubs_path,
                    build=build,
                )
            else:
                self._index = build()
        return self._index
