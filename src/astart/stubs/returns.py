"""Return types that typeshed states plainly enough to rely on."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
    Call,
    Constant,
    FunctionDef,
    Load,
    Name,
    Subscript,
    Tuple,
    arguments,
    dump,
    expr,
    parse,
    unparse,
    walk,
)
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING, Final, final

from astart.graph.dispatch import LowercaseTransformer

type DictExpr = dict[str, expr]

if TYPE_CHECKING:
    from astart.stubs.parser import StubModule, StubName
    from astart.stubs.resolver import Resolved, Resolver


@final
class Constants:
    """Group module-level constants.

    Attributes:
        plain (Final[frozenset[str]]): Builtin types a return annotation may be
            made of.
        decorators (Final[frozenset[str]]): Decorators a library function may
            carry.
        structure (Final[tuple[type[AST], ...]]): Syntax a return annotation
            may use besides names.
        alias_depth (Final[int]): Alias-expansion rounds before a type is
            refused.
        tower (Final[dict[str, frozenset[str]]]): Numeric-tower promotions
            between builtin scalar names.

    """

    plain: Final[frozenset[str]] = frozenset(
        {
            "int",
            "str",
            "bool",
            "bytes",
            "float",
            "complex",
            "list",
            "dict",
            "set",
            "frozenset",
            "tuple",
        },
    )
    decorators: Final[frozenset[str]] = frozenset({"staticmethod"})
    structure: Final[tuple[type[AST], ...]] = (BitOr, Subscript, Tuple, Load)
    tower: Final[dict[str, frozenset[str]]] = {
        "float": frozenset({"int"}),
        "complex": frozenset({"int", "float"}),
        "int": frozenset({"bool"}),
    }
    alias_depth: Final[int] = 8


def _plain(
    *,
    node: expr,
    typevars: set[str],
    allowed: frozenset[str],
) -> bool:
    """Tell whether an annotation uses only types the caller may name.

    Args:
        node (expr): The return annotation.
        typevars (set[str]): Type variables of the defining stub.
        allowed (frozenset[str]): Extra bare names the caller can import
            (``Path``, ``Decimal``,…); ``X | Y`` and subscripts of those
            count too.

    Returns:
        bool: ``True`` for builtin names, ``None``, allowed importable names,
            ``X | Y`` and subscripts of those; ``False`` for other names,
            type variables, strings and anything else.

    """
    names: frozenset[str] = Constants.plain | allowed
    for part in walk(node=node):
        if isinstance(part, Name):
            if part.id not in names or part.id in typevars:
                return False
        elif isinstance(part, Constant):
            if part.value is not None and part.value is not Ellipsis:
                return False
        elif isinstance(part, BinOp):
            if not isinstance(part.op, BitOr):
                return False
        elif not isinstance(part, Constants.structure):
            return False
    return True


def function_return(
    *,
    resolved: Resolved,
    allowed: frozenset[str] = frozenset(),
) -> str | None:
    """State the return type of a library function, if it is certain.

    The function must have exactly one definition (no ``@overload``), be
    defined in a branch the evaluator decided, and return a type spelled
    with builtin names plus the caller's ``allowed`` importable names, so
    the result does not depend on the arguments. Methods of stub classes
    count the same way: ``self`` never reaches the return annotation.

    Args:
        resolved (Resolved): The function as found by the resolver.
        allowed (frozenset[str]): Bare names the caller may import for the
            return type.

    Returns:
        str | None: The return annotation as source text, or ``None``.

    """
    entry: StubName = resolved.name
    if (
        entry.kind != "function"
        or entry.overloaded
        or entry.ambiguous
        or len(entry.nodes) != 1
        or set(entry.decorators) - Constants.decorators
    ):
        return None
    node: AST = entry.nodes[0]
    returns: expr | None = getattr(node, "returns", None)
    if returns is None or not _plain(
        node=returns,
        typevars=resolved.module.typevars,
        allowed=allowed,
    ):
        return None
    return unparse(ast_obj=returns)


def _members(*, node: expr) -> list[expr]:
    """Flatten a ``X | Y`` annotation into its member expressions.

    Args:
        node (expr): The annotation.

    Returns:
        list[expr]: The union members as syntax trees.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return [*_members(node=node.left), *_members(node=node.right)]
    return [node]


def _head_name(*, node: expr) -> str | None:
    """Name the origin a type expression refers to.

    Args:
        node (expr): The type expression.

    Returns:
        str | None: The bare class name, or ``None`` for non-name origins.

    """
    while isinstance(node, Subscript):
        node = node.value
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def _covers(*, outer: expr, inner: expr) -> bool:
    """Tell whether ``inner`` is provably assignable to ``outer``.

    Args:
        outer (expr): A single parameter member.
        inner (expr): A single argument member.

    Returns:
        bool: ``True`` for identical trees, ``Any``/``object`` parameters, a
            bare origin covering any parameterization, ``bool`` inside
            ``int`` and numeric-tower promotions; ``False`` otherwise.

    """
    if dump(node=outer) == dump(node=inner):
        return True
    outer_name: str | None = _head_name(node=outer)
    if outer_name in {"Any", "object"}:
        return True
    inner_name: str | None = _head_name(node=inner)
    if inner_name == "bool" and outer_name == "int":
        return True
    if (
        outer_name is not None
        and outer_name == inner_name
        and not isinstance(outer, Subscript)
    ):
        return True
    return outer_name is not None and inner_name in Constants.tower.get(
        outer_name,
        frozenset(),
    )


def _accepts(*, param: expr, arg: expr) -> bool:
    """Tell whether an argument type fits a parameter annotation.

    Both sides are flattened into union members as syntax trees; every
    argument member must fit some parameter member. Aliases the stubs
    cannot expand and generics stay refused.

    Args:
        param (expr): Parameter annotation, aliases expanded.
        arg (expr): Argument type.

    Returns:
        bool: ``True`` when the fit is certain for every member.

    """
    params: list[expr] = _members(node=param)
    return all(
        any(_covers(outer=member, inner=part) for member in params)
        for part in _members(node=arg)
    )


def _alias_value(*, name: StubName) -> expr | None:
    """Find the value expression of a stub alias or variable.

    Args:
        name (StubName): The stub name.

    Returns:
        expr | None: The assigned expression, or ``None``.

    """
    for node in name.nodes:
        value: expr | None = getattr(node, "value", None)
        if value is not None:
            return value
    return None


def _qualified(*, name: StubName) -> str | None:
    """Name the dotted target a stub name refers somewhere else.

    Args:
        name (StubName): The stub name.

    Returns:
        str | None: The qualified name for ``import`` and ``X = Y`` aliases, or
            ``None`` for definitions.

    """
    if name.kind == "import" and name.imported is not None:
        return f"{name.imported.module}.{name.imported.name}"
    return name.alias_of


def _param_expr(
    *,
    node: expr,
    module: StubModule,
    resolver: Resolver | None,
) -> expr:
    """Expand a parameter annotation's stub aliases.

    A bare name that the stub imports or aliases is followed to its
    definition — ``StrPath`` becomes the ``str | PathLike[str]`` tree —
    so argument types compare against the real union. Anything
    unresolved keeps its own syntax tree.

    Args:
        node (expr): The parameter annotation.
        module (StubModule): Stub module the signature lives in.
        resolver (Resolver | None): Resolver for following imports, when
            available.

    Returns:
        expr: The annotation expression, aliases expanded.

    """
    if resolver is None or not isinstance(node, Name):
        return node
    local: str = node.id
    current: StubModule = module
    seen: set[str] = set()
    for _ in range(Constants.alias_depth):
        stub: StubName | None = current.names.get(local)
        if stub is None:
            return node
        if stub.kind == "variable":
            value: expr | None = _alias_value(name=stub)
            return node if value is None else value
        qualified: str | None = _qualified(name=stub)
        if qualified is None or qualified in seen:
            return node
        seen.add(qualified)
        resolved: Resolved | None = resolver.resolve(qualified=qualified)
        if resolved is None:
            return node
        local = resolved.name.name
        current = resolved.module
    return node


@dataclass(frozen=True, slots=True)
class _Selection:
    """What one overload candidate is checked against.

    Attributes:
        positional (tuple[expr, ...]): Type of each positional argument.
        keywords (DictExpr): Type by keyword name.
        skip_first (bool): Drop the leading ``self``/``cls`` parameter.
        module (StubModule): Stub module the signature lives in.
        resolver (Resolver | None): Resolver for expanding parameter aliases.
        binding (DictExpr): Class type-variable name to receiver argument.

    """

    positional: tuple[expr, ...]
    keywords: DictExpr
    skip_first: bool
    module: StubModule
    resolver: Resolver | None
    binding: DictExpr = dataclass_field(default_factory=dict)


def _bound(*, node: expr, selection: _Selection) -> expr:
    """Apply the receiver's type-variable binding to a parameter type.

    Args:
        node (expr): Parameter annotation expression.
        selection (_Selection): Selection context carrying the binding.

    Returns:
        expr: The annotation with bound type variables replaced.

    """
    if not selection.binding:
        return node
    visited: AST | list[AST] | None = _TypeVarSubstitution(
        mapping=selection.binding,
    ).visit(node=deepcopy(x=node))
    return visited if isinstance(visited, expr) else node


def _signature_fits(*, node: AST, selection: _Selection) -> bool:
    """Tell whether call argument types fit one overload's parameters.

    Args:
        node (AST): The overload's function definition.
        selection (_Selection): Argument types and resolution context.

    Returns:
        bool: ``True`` when every supplied argument fits a parameter and every
            required parameter received one.

    """
    arguments: arguments | None = getattr(node, "args", None)
    if arguments is None:
        return False
    params: list[tuple[str, expr | None, bool]] = [
        (item.arg, item.annotation, False)
        for item in (*arguments.posonlyargs, *arguments.args)
    ]
    params.extend(
        (item.arg, item.annotation, True) for item in arguments.kwonlyargs
    )
    if selection.skip_first and params:
        params = params[1:]
    positional_count: int = len(params) - len(arguments.kwonlyargs)
    if (
        len(selection.positional) > positional_count
        and arguments.vararg is None
    ):
        return False
    seen: set[str] = set()
    for index, arg_type in enumerate(iterable=selection.positional):
        if index >= positional_count:
            break
        name, annotation, _ = params[index]
        if annotation is None or not _accepts(
            param=_param_expr(
                node=_bound(node=annotation, selection=selection),
                module=selection.module,
                resolver=selection.resolver,
            ),
            arg=arg_type,
        ):
            return False
        seen.add(name)
    for name, arg_type in selection.keywords.items():
        match: tuple[str, expr | None, bool] | None = next(
            (p for p in params if p[0] == name),
            None,
        )
        if (
            match is None
            or match[1] is None
            or not _accepts(
                param=_param_expr(
                    node=_bound(node=match[1], selection=selection),
                    module=selection.module,
                    resolver=selection.resolver,
                ),
                arg=arg_type,
            )
        ):
            return False
        seen.add(name)
    return _required_covered(
        params=params,
        seen=seen,
        arguments=arguments,
        positional_count=positional_count,
    )


def _required_covered(
    *,
    params: list[tuple[str, expr | None, bool]],
    seen: set[str],
    arguments: arguments,
    positional_count: int,
) -> bool:
    """Answer whether every parameter without a default was supplied.

    Args:
        params: ``(name, annotation, is_kwonly)`` in signature order.
        seen (set[str]): Parameter names that received an argument.
        arguments (arguments): The signature's parameter list node.
        positional_count (int): Positional parameter count.

    Returns:
        bool: ``True`` when no required parameter is missing.

    """
    defaults: int = len(arguments.defaults)
    kwonly: int = len(arguments.kwonlyargs)
    kw_defaults: int = kwonly - sum(
        1 for item in arguments.kw_defaults if item is None
    )
    first_default: int = positional_count - defaults
    for index, (name, _, is_kwonly) in enumerate(iterable=params):
        if name in seen:
            continue
        if is_kwonly:
            if index - positional_count >= kwonly - kw_defaults:
                continue
            return False
        if index < first_default:
            return False
    return True


def _type_expr(*, source: str | None) -> expr | None:
    """Parse an argument type source into a syntax tree.

    Args:
        source (str | None): Annotation text, ``None`` when the type is
            unknown.

    Returns:
        expr | None: The expression, or ``None`` when unknown or unparseable.

    """
    if source is None:
        return None
    try:
        return parse(source=source, mode="eval").body
    except SyntaxError:
        return None


@dataclass(frozen=True)
class CallArguments:
    """Types of a call's positional and keyword arguments.

    Attributes:
        positional (tuple[str | None, ...]): Type of each positional argument,
            ``None`` if unknown.
        keywords (dict[str, str | None]): Type by keyword name, ``None`` if
            unknown.

    """

    positional: tuple[str | None, ...] = ()
    keywords: dict[str, str | None] = dataclass_field(default_factory=dict)


def select_overload(
    *,
    resolved: Resolved,
    positional: list[str | None],
    keywords: dict[str, str | None],
    allowed: frozenset[str] = frozenset(),
    resolver: Resolver | None = None,
) -> str | None:
    """Pick the overload whose parameters accept the argument types.

    The first overload whose signature fits wins, and its return type is
    stated only when it passes the same plainness test as
    :func:`function_return`. Any unknown argument type refuses the whole
    selection.

    Args:
        resolved: The overloaded function as found by the resolver.
        positional: Type of each positional argument, ``None`` if unknown.
        keywords: Type by keyword name, ``None`` if unknown.
        allowed: Bare names the caller may import for the return type.
        resolver: Resolver for expanding parameter aliases.

    Returns:
        The selected return annotation as source text, or ``None``.

    """
    entry: StubName = resolved.name
    if not entry.overloaded or entry.ambiguous:
        return None
    chosen: expr | None = _selected(
        resolved=resolved,
        call=CallArguments(
            positional=tuple(positional),
            keywords=keywords,
        ),
        allowed=allowed,
        resolver=resolver,
        receiver=None,
    )
    return None if chosen is None else unparse(ast_obj=chosen)


def method_return(
    *,
    resolved: Resolved,
    receiver: list[expr],
    call: CallArguments,
    allowed: frozenset[str] = frozenset(),
    resolver: Resolver | None = None,
) -> str | None:
    """State a method's return for a receiver of known class type.

    The receiver's type arguments bind the class's type variables, so
    ``Match[str].group()`` states ``str``. Overloads and plain methods
    are both handled; anything the substitution cannot name plainly is
    refused.

    Args:
        resolved (Resolved): The method as found by the resolver, owner set.
        receiver (list[expr]): Type arguments of the receiver's class, as
            syntax.
        call (CallArguments): Types of the call's positional and keyword
            arguments.
        allowed (frozenset[str]): Bare names the caller may import for the
            return type.
        resolver (Resolver | None): Resolver for expanding parameter aliases.

    Returns:
        str | None: The return annotation as source text, or ``None``.

    """
    if resolved.owner is None or resolved.name.ambiguous:
        return None
    chosen: expr | None = _selected(
        resolved=resolved,
        call=call,
        allowed=allowed,
        resolver=resolver,
        receiver=receiver,
    )
    return None if chosen is None else unparse(ast_obj=chosen)


def receiver_parts(*, source: str) -> tuple[str, list[expr]] | None:
    """Split a proven receiver type into class head and arguments.

    Args:
        source (str): Type annotation text such as ``Match[str]``.

    Returns:
        tuple[str, list[expr]] | None:
            ``(dotted head, argument expressions)``, or ``None``
            for unions, callables and other shapes with no single
            class head. ``...`` members of a subscript are
            dropped, so ``tuple[int, ...]`` binds one argument.

    """
    parsed: expr | None = _type_expr(source=source)
    if parsed is None:
        return None
    node: expr = parsed
    args: list[expr] = []
    if isinstance(node, Subscript):
        sl: expr = node.slice
        args = [
            arg
            for arg in (sl.elts if isinstance(sl, Tuple) else [sl])
            if not (isinstance(arg, Constant) and arg.value is Ellipsis)
        ]
        node = node.value
        if isinstance(node, Subscript):
            return None
    if not isinstance(node, (Name, Attribute)):
        return None
    return unparse(ast_obj=node), args


def class_typevars(*, owner: StubName) -> list[str]:
    """List a stub class's type variables in binding order.

    PEP 695 ``class C[T]`` parameters come first; otherwise the
    ``Generic[...]` subscript of a base class names them.

    Args:
        owner (StubName): The class as the resolver found it.

    Returns:
        list[str]: Type variable names, empty for a non-generic class.

    """
    if owner.kind != "class" or not owner.nodes:
        return []
    node: AST = owner.nodes[0]
    params: list[AST] = list(getattr(node, "type_params", None) or [])
    names: list[str] = [
        name
        for param in params
        if isinstance(name := getattr(param, "name", None), str)
    ]
    if names:
        return names
    for base in owner.bases:
        parsed: expr | None = _type_expr(source=base)
        if not isinstance(parsed, Subscript):
            continue
        head: expr = parsed.value
        if unparse(ast_obj=head) not in {"Generic", "typing.Generic"}:
            continue
        sl: expr = parsed.slice
        elts: list[expr] = sl.elts if isinstance(sl, Tuple) else [sl]
        return [elt.id for elt in elts if isinstance(elt, Name) and elt.id]
    return []


@final
class _TypeVarSubstitution(LowercaseTransformer):
    """Replace type-variable names by the receiver's argument syntax."""

    def __init__(self, *, mapping: DictExpr) -> None:
        """Bind names to argument trees.

        Args:
            mapping (DictExpr): Type variable name to argument expression.

        """
        self._mapping: DictExpr = mapping

    def visit_name(self, node: Name) -> AST:
        """Substitute a bound type variable.

        Args:
            node (Name): Name node visited.

        Returns:
            AST: The argument tree, or the node itself.

        """
        found: expr | None = self._mapping.get(node.id)
        return node if found is None else deepcopy(x=found)


def _call_exprs(
    *,
    call: CallArguments,
) -> tuple[list[expr], DictExpr] | None:
    """Parse call argument types into syntax trees.

    Args:
        call (CallArguments): Positional and keyword argument types.

    Returns:
        tuple[list[expr], DictExpr] | None:
            ``(positional, keyword)`` expression lists,
            or ``None`` when any type fails to parse.

    """
    args: list[expr] = []
    for kind in call.positional:
        parsed: expr | None = _type_expr(source=kind)
        if parsed is None:
            return None
        args.append(parsed)
    named: DictExpr = {}
    for name, kind in call.keywords.items():
        parsed = _type_expr(source=kind)
        if parsed is None:
            return None
        named[name] = parsed
    return args, named


def _decorator_tail(*, node: expr) -> str | None:
    """Return the final name of a decorator expression.

    Args:
        node (expr): Decorator expression, possibly a call.

    Returns:
        str | None: The attribute or name it ends in, or ``None``.

    """
    while isinstance(node, Call):
        node = node.func
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def _selected(
    *,
    resolved: Resolved,
    call: CallArguments,
    allowed: frozenset[str],
    resolver: Resolver | None,
    receiver: list[expr] | None,
) -> expr | None:
    """First definition whose signature fits, as a return expression.

    Args:
        resolved (Resolved): The function or method as found by the resolver.
        call (CallArguments): Types of the call's positional and keyword
            arguments.
        allowed (frozenset[str]): Bare names the caller may import for the
            return type.
        resolver (Resolver | None): Resolver for expanding parameter aliases.
        receiver (list[expr] | None): Class type arguments for method TypeVar
            binding, or ``None`` for plain functions.

    Returns:
        expr | None: The plain return expression, or ``None``.

    """
    entry: StubName = resolved.name
    parsed_args: tuple[list[expr], DictExpr] | None = _call_exprs(
        call=call,
    )
    if parsed_args is None:
        return None
    args: list[expr]
    named: DictExpr
    args, named = parsed_args
    binding: DictExpr = {}
    if receiver is not None:
        typevars: list[str] = (
            []
            if resolved.owner is None
            else class_typevars(owner=resolved.owner)
        )
        if len(typevars) != len(receiver):
            return None
        binding = dict(zip(typevars, receiver, strict=True))
    for node in entry.nodes:
        if not isinstance(node, (AsyncFunctionDef, FunctionDef)):
            continue
        static: bool = any(
            _decorator_tail(node=decorator) == "staticmethod"
            for decorator in node.decorator_list
        )
        selection: _Selection = _Selection(
            positional=tuple(args),
            keywords=named,
            skip_first=resolved.owner is not None and not static,
            module=resolved.module,
            resolver=resolver,
            binding=binding,
        )
        if not _signature_fits(node=node, selection=selection):
            continue
        returns: expr | None = getattr(node, "returns", None)
        if returns is None:
            continue
        stated: expr = deepcopy(x=returns)
        if binding:
            visited: AST | list[AST] | None = _TypeVarSubstitution(
                mapping=binding,
            ).visit(node=stated)
            stated = visited if isinstance(visited, expr) else stated
        if _plain(
            node=stated,
            typevars=resolved.module.typevars,
            allowed=allowed,
        ):
            return stated
    return None


def variable_type(*, resolved: Resolved) -> str | None:
    """State the annotation of a stub variable.

    Args:
        resolved (Resolved): The variable as found by the resolver.

    Returns:
        str | None: The annotation as source text, or ``None`` when the
            variable is unannotated or its annotation is not plain.

    """
    entry: StubName = resolved.name
    if entry.kind != "variable" or not entry.nodes:
        return None
    node: AST = entry.nodes[0]
    annotation: expr | None = getattr(node, "annotation", None)
    return None if annotation is None else unparse(ast_obj=annotation)
