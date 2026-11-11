"""Turn a parsed module into a graph of contracts.

Every parameter, return value and singly-bound local of a function is a
node. Facts the syntax proves become seeds; flows between nodes become
contracts. Anything the builder cannot account for marks the node *opaque*,
so no type is ever settled from partial knowledge.

"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Del,
    Dict,
    DictComp,
    ExceptHandler,
    For,
    FormattedValue,
    FunctionDef,
    GeneratorExp,
    Global,
    If,
    IfExp,
    Import,
    ImportFrom,
    JoinedStr,
    Lambda,
    List,
    ListComp,
    Load,
    Match,
    MatchAs,
    MatchMapping,
    MatchStar,
    Name,
    NamedExpr,
    Nonlocal,
    Return,
    Set,
    SetComp,
    Slice,
    Store,
    Subscript,
    Tuple,
    UnaryOp,
    Yield,
    YieldFrom,
    arg,
    arguments,
    boolop,
    cmpop,
    comprehension,
    expr,
    expr_context,
    iter_child_nodes,
    iter_fields,
    keyword,
    operator,
    stmt,
    unaryop,
    unparse,
    walk,
)
from builtins import __dict__
from collections import Counter
from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, cast, final

from astart.rules.attributes import receiver_of
from astart.rules.hints import Constants as HintConstants
from astart.rules.hints import (
    boolean_returns,
    is_declaration,
    protocol_result_for,
)
from astart.rules.imports import Constants as ImportConstants
from astart.rules.library_calls import callee_name, import_aliases
from astart.rules.methods import MethodIndex
from astart.rules.negotiation.algebra import TypeAlgebra
from astart.rules.negotiation.containers import (
    attribute_risky,
    empty_kind,
    fillings,
    literal_kind,
)
from astart.rules.negotiation.graph import ContractGraph, Derived
from astart.rules.negotiation.model import (
    Candidate,
    Contract,
    Origin,
    Polarity,
    Relation,
)
from astart.rules.negotiation.narrowing import (
    CaseArms,
    exception_types,
    read_case,
    read_test,
)
from astart.rules.negotiation.narrowing import Constants as Narrowing
from astart.rules.negotiation.transfer import forward
from astart.rules.provable import (
    can_fall_off,
    expression_type,
    module_constants,
    never_returns,
    own_calls,
    own_nodes,
    scope_types,
)
from astart.rules.resolve import CallBindings, binding_counts
from astart.rules.scopes import names_bound_by
from astart.semantic import ArgumentOrigin
from astart.stubs import (
    CallArguments,
    function_return,
    method_return,
    receiver_parts,
    select_overload,
    variable_type,
)

type StrOrNone = str | None
type SetStr = set[str]
type DictStr = dict[str, str]

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from astart import BoundCall, CommentedModule
    from astart.stubs import Resolver
    from astart.stubs.resolver import Resolved

type Function = FunctionDef | AsyncFunctionDef

# A field of an expression node, as ``ast.iter_fields`` yields it.
type FieldValue = (
    AST | list[AST | None] | str | int | float | complex | bytes | bool | None
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        receivers (Final[frozenset[str]]): Names of the implicit first
            parameter of a method.
        passed (Final[frozenset[ArgumentOrigin]]): Argument origins that carry
            an explicit value.
        variadic (Final[frozenset[ArgumentOrigin]]): Argument origins of
            ``*args`` and ``**kwargs``.
        constructors (Final[frozenset[str]]): Methods whose call evaluates to
            the class instead.
        scopes (Final[tuple[type[AST], ...]]): Nodes that open a scope the
            narrowing must not enter.
        derivable (Final[tuple[type[expr], ...]]): Expression kinds a derived
            node may be built from.
        comprehensions (Final[tuple[type[expr], ...]]): Comprehensions, which
            build fresh containers.
        leaves (Final[tuple[type[expr], ...]]): Expressions that need no
            operand.
        markers (Final[tuple[type[AST], ...]]): Syntax nodes that are copied as
            they are.
        type_variables (Final[frozenset[str]]): Callees that declare a type
            variable.
        qualifiers (Final[frozenset[str]]): Grouped module constant.

    """

    receivers: Final[frozenset[str]] = frozenset({"self", "cls"})
    passed: Final[frozenset[ArgumentOrigin]] = frozenset(
        {ArgumentOrigin.POSITIONAL, ArgumentOrigin.KEYWORD},
    )
    constructors: Final[frozenset[str]] = frozenset({"__init__", "__new__"})
    derivable: Final[tuple[type[expr], ...]] = (
        BinOp,
        UnaryOp,
        BoolOp,
        Compare,
        IfExp,
        Tuple,
        List,
        Set,
        Dict,
        JoinedStr,
        FormattedValue,
        Call,
        Subscript,
        Attribute,
        ListComp,
        SetComp,
        DictComp,
        GeneratorExp,
    )
    comprehensions: Final[tuple[type[expr], ...]] = (
        ListComp,
        SetComp,
        DictComp,
        GeneratorExp,
    )
    leaves: Final[tuple[type[expr], ...]] = (Constant,)
    markers: Final[tuple[type[AST], ...]] = (
        operator,
        unaryop,
        boolop,
        cmpop,
        expr_context,
    )
    type_variables: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple"},
    )
    scopes: Final[tuple[type[AST], ...]] = (
        FunctionDef,
        AsyncFunctionDef,
        Lambda,
        ClassDef,
        ListComp,
        SetComp,
        DictComp,
        GeneratorExp,
    )
    variadic: Final[frozenset[ArgumentOrigin]] = frozenset(
        {ArgumentOrigin.VAR_POSITIONAL, ArgumentOrigin.VAR_KEYWORD},
    )

    qualifiers: Final[frozenset[str]] = frozenset(
        {"Final", "ClassVar", "InitVar"},
    )


@final
@dataclass(frozen=True, slots=True)
class Built:
    """A module's contract graph.

    Attributes:
        graph (ContractGraph): Nodes, contracts and seeds.
        opaque (frozenset[str]): Nodes whose evidence is incomplete; nothing
            may
            be settled for them or anything they flow into.
        kinds (DictStr): ``"parameter"`` or ``"return"`` for the nodes worth
            reporting.
        variables (dict[str, Assign]): The assignment that binds each
            function-local variable, by node path.
        attributes (dict[str, Assign]): The first write of each instance
            attribute (the one
            in ``__init__`` when there is one), by node path.
        why (DictStr): The first reason each opaque node is opaque.
        risky (frozenset[str]): Attributes some method uses in a way that could
            change the element
            type of a container they hold; opaque if they settle to one.

    """

    graph: ContractGraph
    opaque: frozenset[str]
    kinds: DictStr
    variables: dict[str, Assign]
    attributes: dict[str, Assign]
    risky: frozenset[str]
    why: DictStr


@final
@dataclass(slots=True)
class _Scope:
    """The names a function body can reason about.

    Attributes:
        names (DictStr): Node path by local or parameter name.
        env (DictStr): Proven type by name, for the syntax typer.
        receiver (StrOrNone): Name of the instance parameter inside a method.
        members (DictStr): Node path by instance attribute the class owns.
        qual (str): Qualified name of the function.

    """

    names: DictStr = field(default_factory=dict)
    env: DictStr = field(default_factory=dict)
    receiver: StrOrNone = None
    members: DictStr = field(default_factory=dict)
    qual: str = ""


def walk_functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    in_class: bool,
) -> Iterator[tuple[str, Function, bool]]:
    """List every function with its qualified name.

    Args:
        node (AST): Module or class or function whose body is scanned.
        trail (tuple[str, ...]): Qualified-name prefix.
        in_class (bool): Whether ``node`` is a class body.

    Yields:
        tuple[str, Function, bool]:
            ``(qualified name, definition, defined directly in a class)``.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            yield ".".join((*trail, child.name)), child, in_class
            yield from walk_functions(
                node=child,
                trail=(*trail, child.name),
                in_class=False,
            )
        elif isinstance(child, ClassDef):
            yield from walk_functions(
                node=child,
                trail=(*trail, child.name),
                in_class=True,
            )


def _parameters(
    *,
    function: Function,
    skip_receiver: bool,
) -> list[tuple[arg, expr | None]]:
    """Pair each plain parameter with its default.

    Args:
        function (Function): Function definition.
        skip_receiver (bool): Whether the first parameter is an implicit
            receiver.

    Returns:
        list[tuple[arg, expr | None]]: Positional-only, positional and
            keyword-only parameters.

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
    if skip_receiver and pairs and pairs[0][0].arg in Constants.receivers:
        return pairs[1:]
    return pairs


def _blocked_names(*, node: AST) -> SetStr:
    """List the names a statement binds in a way contracts cannot follow.

    Args:
        node (AST): Any node of a function body.

    Returns:
        SetStr: Names bound by ``global`` /``nonlocal``, imports, nested
            definitions, exception handlers and annotated assignments.

    """
    if isinstance(node, (Global, Nonlocal)):
        return set(node.names)
    if isinstance(node, (Import, ImportFrom)):
        return {
            (item.asname or item.name).split(sep=".")[0] for item in node.names
        }
    if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
        return {node.name}
    if isinstance(node, ExceptHandler) and node.name is not None:
        return {node.name}
    bound: StrOrNone = None
    if isinstance(node, (MatchAs, MatchStar)):
        bound = node.name
    elif isinstance(node, MatchMapping):
        bound = node.rest
    elif (
        isinstance(node, AnnAssign)
        and isinstance(node.target, Name)
        and node.value is None
    ):
        bound = node.target.id
    return {bound} if bound is not None else set()


def _head_name(*, node: expr) -> str:
    """Name the head of an attribute or name expression.

    Args:
        node (expr): The expression.

    Returns:
        str: ``x`` for ``x`` and ``mod.x``, else ``""``.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return ""


def _declared_source(*, annotation: expr) -> StrOrNone:
    """Read the type an annotation declares, skipping bare qualifiers.

    ``x: Final = v`` declares no type — ``Final`` is a qualifier — so the
    value must speak instead; ``x: Final[int] = v`` still declares ``int``.

    Args:
        annotation (expr): The annotation expression.

    Returns:
        StrOrNone: The type text, or ``None`` for a bare qualifier.

    """
    if (
        isinstance(annotation, Subscript)
        and _head_name(node=annotation.value) in Constants.qualifiers
    ):
        return unparse(ast_obj=annotation.slice)
    if _head_name(node=annotation) in Constants.qualifiers:
        return None
    return unparse(ast_obj=annotation)


def _plain_target(*, node: AST) -> StrOrNone:
    """Name the variable a simple assignment or loop binds.

    Args:
        node (AST): Any node of a function body.

    Returns:
        StrOrNone: The name for ``x = ...`` , ``for x in ...``
            and ``(x := ...)``, else ``None``.

    """
    if (
        isinstance(node, Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], Name)
    ):
        return node.targets[0].id
    if isinstance(node, For) and isinstance(node.target, Name):
        return node.target.id
    if (
        isinstance(node, AnnAssign)
        and isinstance(node.target, Name)
        and node.value is not None
    ):
        return node.target.id
    if isinstance(node, NamedExpr):
        return node.target.id
    return None


def walk_classes(
    *,
    node: AST,
    trail: tuple[str, ...],
) -> Iterator[tuple[str, ClassDef]]:
    """List every class with its qualified name.

    Args:
        node (AST): Module, class or function whose body is scanned.
        trail (tuple[str, ...]): Qualified-name prefix.

    Yields:
        tuple[str, ClassDef]: ``(qualified name, definition)``.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, ClassDef):
            qual: str = ".".join((*trail, child.name))
            yield qual, child
            yield from walk_classes(node=child, trail=(*trail, child.name))
        elif isinstance(child, (FunctionDef, AsyncFunctionDef)):
            yield from walk_classes(node=child, trail=(*trail, child.name))


def _external_stores(*, module: AST) -> Counter[str]:
    """Count the attribute writes of the whole module by attribute name.

    Args:
        module (AST): Parsed module.

    Returns:
        Counter[str]: Stores and deletes by attribute name.

    """
    return Counter(
        node.attr
        for node in walk(node=module)
        if isinstance(node, Attribute) and isinstance(node.ctx, (Store, Del))
    )


def _own_writes(
    *,
    method: Function,
    receiver: str,
) -> tuple[dict[str, list[Assign]], SetStr]:
    """Find the plain writes a method makes to its instance's attributes.

    Args:
        method (Function): Method definition.
        receiver (str): Name of the instance parameter.

    Returns:
        tuple[dict[str, list[Assign]], SetStr]: The ``self.name = value``
            assignments by attribute, and the
            attributes touched in any other way (augmented, unpacked,
            deleted) — all of them when the receiver is rebound.

    """
    own: list[AST] = list(own_nodes(function=method))
    plain: dict[int, str] = {}
    writes: dict[str, list[Assign]] = {}
    for node in own:
        if (
            isinstance(node, Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], Attribute)
            and isinstance(node.targets[0].value, Name)
            and node.targets[0].value.id == receiver
        ):
            plain[id(node.targets[0])] = node.targets[0].attr
            writes.setdefault(node.targets[0].attr, []).append(node)
    bad: SetStr = set()
    for node in walk(node=method):
        if (
            isinstance(node, Attribute)
            and isinstance(node.ctx, (Store, Del))
            and isinstance(node.value, Name)
            and node.value.id == receiver
            and id(node) not in plain
        ):
            bad.add(node.attr)
    if any(receiver in names_bound_by(node=node) for node in own):
        bad.update(writes)
    return writes, bad


def _plain_classes(*, module: AST) -> frozenset[str]:
    """List the top-level classes whose instances need no type arguments.

    A generic class (``Generic[T]``, ``Protocol[T]``, a base parameterised by
    a type variable of the module, or PEP 695 parameters) is left out: its
    bare name would be a bare generic.

    Args:
        module (AST): Parsed module.

    Returns:
        frozenset[str]: Names of the top-level classes that are not generic.

    """
    body: list[stmt] = list(getattr(module, "body", []))
    typevars: SetStr = {
        statement.targets[0].id
        for statement in body
        if isinstance(statement, Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], Name)
        and isinstance(statement.value, Call)
        and isinstance(statement.value.func, Name)
        and statement.value.func.id in Constants.type_variables
    }
    return frozenset(
        statement.name
        for statement in body
        if isinstance(statement, ClassDef)
        and not getattr(statement, "type_params", None)
        and not any(
            isinstance(base, Subscript)
            and (
                unparse(ast_obj=base.value).endswith(("Generic", "Protocol"))
                or any(
                    isinstance(part, Name) and part.id in typevars
                    for part in walk(node=base.slice)
                )
            )
            for base in statement.bases
        )
    )


@final
class _Templater:
    """Rewrite an expression with its operand nodes as placeholders."""

    def __init__(self, *, builder: ContractBuilder, scope: _Scope) -> None:
        """Start with no operands.

        Args:
            builder (ContractBuilder): The builder, to recognise operand nodes.
            scope (_Scope): Scope the expression is evaluated in.

        """
        self._builder: ContractBuilder = builder
        self._scope: _Scope = scope
        self.parts: list[tuple[str, str]] = []
        self.fixed: DictStr = {}
        self._bound: SetStr = set()

    def convert(self, *, value: expr) -> expr | None:
        """Copy an expression, replacing operands by placeholder names.

        Args:
            value (expr): The expression.

        Returns:
            expr | None: The template, or ``None`` when the expression contains
                something the syntax typer cannot read (lambdas,
                async comprehensions, unknown calls or names).

        """
        handled, atom = self._atom(value=value)
        if handled:
            return atom
        if not isinstance(value, Constants.derivable):
            return None
        if isinstance(value, Call) and not (
            isinstance(value.func, Attribute)
            or (
                isinstance(value.func, Name)
                and self._builder.is_builtin(name=value.func.id)
            )
        ):
            return None
        return self._copy(value=value)

    def _atom(self, *, value: expr) -> tuple[bool, expr | None]:
        """Handle operands, names and constants, which have no children.

        Args:
            value (expr): The expression.

        Returns:
            tuple[bool, expr | None]: ``(True, result)`` when the expression
                was
                handled here (the result is ``None`` for
                an unknown name), else ``(False, None)``.

        """
        if isinstance(value, Name) and value.id in self._bound:
            return True, value
        path: StrOrNone = self._builder.operand(
            value=value,
            scope=self._scope,
        )
        if path is not None:
            placeholder: str = f"__{len(self.parts)}"
            self.parts.append((placeholder, path))
            return True, Name(id=placeholder, ctx=Load())
        if isinstance(value, Name):
            known: StrOrNone = self._scope.env.get(value.id)
            if known is None:
                return True, None
            self.fixed[value.id] = known
            return True, value
        return isinstance(value, Constants.leaves), value

    def _comprehension(self, *, value: comprehension) -> comprehension | None:
        """Copy one ``for … in … if …`` clause of a comprehension.

        Names in tuple/list targets are bound inside the expression, so
        they stay as written and are not outer-scope operands.

        Args:
            value (comprehension): The clause.

        Returns:
            comprehension | None: The copy, or ``None`` for an async
                clause or an unreadable part.

        """
        targets: list[AST] = list(walk(node=value.target))
        if value.is_async or any(
            not isinstance(target, (Name, Tuple, List, Store))
            for target in targets
        ):
            return None
        source: expr | None = self.convert(value=value.iter)
        self._bound.update(
            target.id for target in targets if isinstance(target, Name)
        )
        tests: list[expr] = []
        for test in value.ifs:
            converted: expr | None = self.convert(value=test)
            if converted is None:
                return None
            tests.append(converted)
        if source is None:
            return None
        return comprehension(
            target=value.target,
            iter=source,
            ifs=tests,
            is_async=0,
        )

    def _copy(self, *, value: expr) -> expr | None:
        """Copy a compound expression, converting every child.

        The clauses of a comprehension are converted first, so its loop
        variable is known when the element expression is read, and the
        variable is bound only inside that comprehension.

        Args:
            value (expr): The expression.

        Returns:
            expr | None:
                The copy, or ``None`` when some child cannot be converted.

        """
        outer: SetStr = set(self._bound)
        copied: expr = copy(x=value)
        for field_name, field_value in sorted(
            iter_fields(node=value),
            key=lambda pair: pair[0] != "generators",
        ):
            if (
                field_name == "func"
                and isinstance(value, Call)
                and isinstance(value.func, Name)
            ):
                continue
            converted: FieldValue | None = self._field(value=field_value)
            if converted is None:
                return None
            setattr(copied, field_name, converted)
        self._bound = outer
        return copied

    @staticmethod
    def _plain(*, value: FieldValue) -> bool:
        """Tell whether a field value can be copied as it is.

        Args:
            value (FieldValue): A field of an expression node.

        Returns:
            bool: ``True`` for names, numbers and the operator and
                context markers; ``False`` for any other syntax node.

        """
        return not isinstance(value, AST) or isinstance(
            value,
            Constants.markers,
        )

    def _field(self, *, value: FieldValue) -> FieldValue | None:
        """Convert one field of an expression node.

        Args:
            value (FieldValue): An expression, a list of nodes, or a plain
                value.

        Returns:
            FieldValue | None:
                The converted field; plain values are returned as they
                are and ``None`` means the field cannot be converted.

        """
        if isinstance(value, expr):
            return self.convert(value=value)
        if not isinstance(value, list):
            return value if self._plain(value=value) else None
        items: list[AST | None] = []
        for item in value:
            converted: AST | None
            if isinstance(item, keyword):
                inner: expr | None = self.convert(value=item.value)
                converted = (
                    None
                    if inner is None
                    else keyword(arg=item.arg, value=inner)
                )
            elif isinstance(item, expr):
                converted = self.convert(value=item)
            elif isinstance(item, comprehension):
                converted = self._comprehension(value=item)
            else:
                converted = item if self._plain(value=item) else None
            if converted is None:
                return None
            items.append(converted)
        return items


@final
class ContractBuilder:
    """Collect the contracts of one module."""

    def __init__(
        self,
        *,
        module: CommentedModule,
        escaped: frozenset[str],
        library: Resolver | None = None,
    ) -> None:
        """Prepare the shared analyses.

        Args:
            module (CommentedModule): Parsed module.
            escaped (frozenset[str]): Names read as values, whose callers are
                unknown.
            library (Resolver | None): Resolver over typeshed, to type calls
                into
                the standard library; ``None`` types none.

        """
        self._library: Resolver | None = library
        self._module: CommentedModule = module
        self._escaped: frozenset[str] = escaped
        self._counts: dict[str, int] = binding_counts(module=module)
        self._bindings: CallBindings = CallBindings(
            module=module,
            counts=self._counts,
        )
        self._constants: DictStr = module_constants(
            module=module,
            counts=self._counts,
        )
        self._graph: ContractGraph = ContractGraph()
        self._opaque: SetStr = set()
        self._why: DictStr = {}
        self._kinds: DictStr = {}
        self._ids: dict[int, str] = {}
        self._scopes: dict[int, _Scope] = {}
        self._params: dict[str, list[str]] = {}
        self._by_name: DictStr = {}
        self._coroutines: SetStr = set()
        self._name_path: dict[int, str] = {}
        self._methods: MethodIndex = MethodIndex(
            module=module,
            counts=self._counts,
        )
        self._top_classes: frozenset[str] = _plain_classes(module=module)
        self._variables: dict[str, Assign] = {}
        self._attribute_writes: dict[str, Assign] = {}
        self._risky: SetStr = set()

    def build(self) -> Built:
        """Build the graph.

        Returns:
            Built: The graph, the opaque nodes and the reportable node kinds.

        """
        entries: list[tuple[str, Function, bool]] = list(
            walk_functions(node=self._module, trail=(), in_class=False),
        )
        seen: Counter[str] = Counter(qual for qual, _fn, _cls in entries)
        unique: list[tuple[str, Function, bool]] = [
            item for item in entries if seen[item[0]] == 1
        ]
        for qual, function, in_class in unique:
            self._ids[id(function)] = qual
            if isinstance(function, AsyncFunctionDef):
                self._coroutines.add(qual)
            if self._counts.get(function.name, 0) == 1:
                self._by_name[function.name] = qual
            self._declare(qual=qual, function=function, in_class=in_class)
        for qual, function, _in_class in unique:
            self._narrowing(qual=qual, function=function)
        self._attributes(unique=unique)
        for qual, function, _in_class in unique:
            self._body(qual=qual, function=function)
        self._calls(unique=unique)
        self._starved()
        return Built(
            graph=self._graph,
            opaque=frozenset(self._opaque),
            kinds=dict(self._kinds),
            variables=dict(self._variables),
            attributes=dict(self._attribute_writes),
            risky=frozenset(self._risky),
            why=dict(self._why),
        )

    def _block(self, *, path: str, why: str) -> None:
        """Mark a node as having incomplete evidence, keeping the first reason.

        Args:
            path (str): Node path.
            why (str): What made the evidence incomplete.

        """
        self._opaque.add(path)
        _ = self._why.setdefault(path, why)

    def _block_all(self, *, paths: Iterable[str], why: str) -> None:
        """Mark several nodes as having incomplete evidence.

        Args:
            paths (Iterable[str]): Node paths.
            why (str): What made the evidence incomplete.

        """
        for path in paths:
            self._block(path=path, why=why)

    def _starved(self) -> None:
        """Mark nodes that feed others but have no evidence of their own.

        A parameter nobody calls and that has no default says nothing about
        its type; anything that depends on it must not settle from the other
        things that reach it.

        """
        for path in self._graph.nodes:
            if self._graph.feeds(path=path) and not self._graph.has_input(
                path=path,
            ):
                self._block(path=path, why="no evidence reaches it")

    def _declare(
        self,
        *,
        qual: str,
        function: Function,
        in_class: bool,
    ) -> None:
        """Create the parameter and return nodes of a function.

        Args:
            qual (str): Qualified name.
            function (Function): Function definition.
            in_class (bool): Whether it is defined directly in a class.

        """
        scope: _Scope = _Scope(qual=qual)
        scope.env = scope_types(
            function=function,
            counts=self._counts,
            constants=self._constants,
        )
        self._scopes[id(function)] = scope
        names: list[str] = []
        pairs: list[tuple[arg, expr | None]] = _parameters(
            function=function,
            skip_receiver=in_class,
        )
        for parameter, default in pairs:
            path: str = f"{qual}.{parameter.arg}"
            names.append(path)
            scope.names[parameter.arg] = path
            self._kinds[path] = "parameter"
            self._graph.add_node(path=path)
            if parameter.annotation is not None:
                self._declared(
                    path=path,
                    source=unparse(ast_obj=parameter.annotation),
                )
            if default is not None:
                self._seed_value(
                    value=default,
                    target=path,
                    scope=_Scope(env=self._constants),
                    origin=Origin.default,
                )
        self._params[qual] = names
        ret: str = f"{qual}->"
        self._kinds[ret] = "return"
        self._graph.add_node(path=ret)
        if function.returns is not None:
            self._declared(path=ret, source=unparse(ast_obj=function.returns))
        self._locals(function=function, qual=qual, scope=scope)

    def _declared(self, *, path: str, source: str) -> None:
        """Seed a written annotation as a hard declaration.

        Args:
            path (str): Node path.
            source (str): Annotation text.

        """
        self._graph.seed(
            path=path,
            candidate=Candidate(
                type_text=source,
                confidence=1.0,
                distance=0,
                origins=frozenset({Origin.declared}),
                explanation=f"{path} is declared {source}",
            ),
            polarity=Polarity.declaration,
        )

    def _locals(self, *, function: Function, qual: str, scope: _Scope) -> None:
        """Create nodes for locals bound exactly once by a plain statement.

        Args:
            function (Function): Function definition.
            qual (str): Qualified name.
            scope (_Scope): Scope extended in place.

        """
        stores: Counter[str] = Counter()
        blocked: SetStr = {
            name
            for node in walk(node=function)
            if isinstance(node, (Global, Nonlocal))
            for name in node.names
        }
        parameters: frozenset[str] = frozenset(scope.names)
        plain: list[str] = []
        for node in own_nodes(function=function):
            if isinstance(node, Name) and isinstance(node.ctx, Store):
                stores[node.id] += 1
            elif isinstance(node, Name) and isinstance(node.ctx, Del):
                blocked.add(node.id)
            blocked.update(_blocked_names(node=node))
            target: StrOrNone = _plain_target(node=node)
            if target is not None:
                plain.append(target)
        for parameter in [
            name for name in scope.names if stores[name] or name in blocked
        ]:
            del scope.names[parameter]
        blocked.update(scope.names)
        for name in plain:
            if (
                name not in blocked
                and name not in parameters
                and stores[name] == 1
            ):
                path: str = f"{qual}.{name}"
                scope.names[name] = path
                self._graph.add_node(path=path)

    def _narrowing(self, *, qual: str, function: Function) -> None:
        """Give every name read after a type test the path of its narrowing.

        Args:
            qual (str): Qualified name.
            function (Function): Function definition.

        """
        scope: _Scope = self._scopes[id(function)]
        self._statements(
            stmts=function.body,
            env=dict(scope.names),
            scope=scope,
            qual=qual,
        )

    def _statements(
        self,
        *,
        stmts: list[stmt],
        env: DictStr,
        scope: _Scope,
        qual: str,
    ) -> DictStr:
        """Walk statements in order, threading the narrowed environment.

        Args:
            stmts (list[stmt]): Statements of one block.
            env (DictStr): Current path of each name.
            scope (_Scope): Function scope.
            qual (str): Qualified name of the function.

        Returns:
            DictStr: The environment after the block.

        """
        for item in stmts:
            env = self._statement(item=item, env=env, scope=scope, qual=qual)
        return env

    def _statement(
        self,
        *,
        item: stmt,
        env: DictStr,
        scope: _Scope,
        qual: str,
    ) -> DictStr:
        """Register the names of one statement and walk its blocks.

        Args:
            item (stmt): The statement.
            env (DictStr): Current path of each name.
            scope (_Scope): Function scope.
            qual (str): Qualified name of the function.

        Returns:
            DictStr: The environment after the statement.

        """
        if isinstance(item, If):
            return self._branch(item=item, env=env, scope=scope, qual=qual)
        if isinstance(item, Match):
            return self._match(item=item, env=env, scope=scope, qual=qual)
        if isinstance(item, Constants.scopes):
            return env
        for _field, raw in iter_fields(node=item):
            value: object = raw
            if (
                isinstance(value, list)
                and value
                and isinstance(value[0], stmt)
            ):
                self._statements(
                    stmts=cast(typ="list[stmt]", val=value),
                    env=env,
                    scope=scope,
                    qual=qual,
                )
            elif isinstance(value, list):
                for part in cast(typ="list[AST]", val=value):
                    if isinstance(part, ExceptHandler):
                        self._register(node=part.type, env=env, scope=scope)
                        self._statements(
                            stmts=part.body,
                            env=self._handler_env(
                                part=part,
                                env=env,
                                qual=qual,
                            ),
                            scope=scope,
                            qual=qual,
                        )
                        if part.name is not None:
                            env.pop(part.name, None)
                    else:
                        self._register(node=part, env=env, scope=scope)
            else:
                self._register(
                    node=value if isinstance(value, AST) else None,
                    env=env,
                    scope=scope,
                )
        return env

    def _branch(
        self,
        *,
        item: If,
        env: DictStr,
        scope: _Scope,
        qual: str,
    ) -> DictStr:
        """Narrow a name on each arm of an ``if`` and after it.

        Args:
            item (If): The ``if`` statement.
            env (DictStr): Current path of each name.
            scope (_Scope): Function scope.
            qual (str): Qualified name of the function.

        Returns:
            DictStr: The environment after the ``if`` : an arm's narrowing
                survives it when the other arm cannot fall through.

        """
        self._register(node=item.test, env=env, scope=scope)
        true_env: DictStr = dict(env)
        false_env: DictStr = dict(env)
        for arms in read_test(test=item.test, counts=self._counts):
            if arms.name not in env:
                continue
            if arms.when_true is not None:
                true_env[arms.name] = self._narrowed(
                    base=env[arms.name],
                    line=item.lineno,
                    tag="t",
                    constraint=arms.when_true,
                )
            if arms.when_false is not None:
                false_env[arms.name] = self._narrowed(
                    base=env[arms.name],
                    line=item.lineno,
                    tag="f",
                    constraint=arms.when_false,
                )
        after_true: DictStr = self._statements(
            stmts=item.body,
            env=true_env,
            scope=scope,
            qual=qual,
        )
        after_false: DictStr = self._statements(
            stmts=item.orelse,
            env=false_env,
            scope=scope,
            qual=qual,
        )
        body_falls: bool = can_fall_off(body=item.body)
        else_falls: bool = can_fall_off(body=item.orelse)
        if not body_falls and else_falls:
            return after_false
        if not else_falls and body_falls:
            return after_true
        return env

    def _narrowed(
        self,
        *,
        base: str,
        line: int,
        tag: str,
        constraint: str,
    ) -> str:
        """Create the node for a name inside a narrowing arm.

        Args:
            base (str): Path the name had before the test.
            line (int): Line of the test, to keep paths unique.
            tag (str): ``"t"`` or ``"f"`` for the arm.
            constraint (str): What the arm establishes (``!None``, a class,
                ...).

        Returns:
            str: The new node's path.

        """
        path: str = f"{base}#{line}{tag}"
        why: str = f"{base} is {constraint} on line {line}"
        self._graph.add_node(path=path)
        self._link(
            source=base,
            target=path,
            relation=Relation.narrows,
            why=why,
        )
        self._graph.seed(
            path=path,
            candidate=Candidate(
                type_text=constraint,
                confidence=1.0,
                distance=0,
                origins=frozenset({Origin.syntax}),
                explanation=why,
            ),
            polarity=Polarity.intersection,
        )
        return path

    def _match(
        self,
        *,
        item: Match,
        env: DictStr,
        scope: _Scope,
        qual: str,
    ) -> DictStr:
        """Narrow the subject inside each ``case`` body of a ``match``.

        Every case sees the subject narrowed by its own pattern plus the
        complement of the earlier unguarded cases; guarded cases narrow
        positively but never subtract for the cases that follow.

        Args:
            item (Match): The ``match`` statement.
            env (DictStr): Current path of each name.
            scope (_Scope): Function scope.
            qual (str): Qualified name of the function.

        Returns:
            DictStr: The environment after the ``match`` :
                case narrowing does not outlive its body.

        """
        self._register(node=item.subject, env=env, scope=scope)
        subject_name: StrOrNone = (
            item.subject.id if isinstance(item.subject, Name) else None
        )
        subject: StrOrNone = (
            None if subject_name is None else env.get(subject_name)
        )
        excluded: list[str] = []
        for index, case in enumerate(iterable=item.cases):
            case_env: DictStr = dict(env)
            arms: CaseArms = read_case(
                node=case.pattern,
                counts=self._counts,
                classes=self._top_classes,
            )
            atoms: list[str] = []
            if arms.positive is not None:
                atoms.append(arms.positive)
            atoms.extend(f"{Narrowing.negation}{text}" for text in excluded)
            if subject_name is not None and subject is not None and atoms:
                case_env[subject_name] = self._narrowed(
                    base=subject,
                    line=case.pattern.lineno,
                    tag=f"m{index}",
                    constraint=" & ".join(atoms),
                )
            self._register(node=case.guard, env=case_env, scope=scope)
            self._statements(
                stmts=case.body,
                env=case_env,
                scope=scope,
                qual=qual,
            )
            if case.guard is None:
                excluded.extend(arms.excluded)
        return env

    def _handler_env(
        self,
        *,
        part: ExceptHandler,
        env: DictStr,
        qual: str,
    ) -> DictStr:
        """Bind ``except E as e`` to the handler's exception type.

        The binding lives only inside the handler body: the caller deletes
        the name when the handler ends, as Python does, so the returned
        environment is a copy and later reads stay opaque.

        Args:
            part (ExceptHandler): The exception handler.
            env (DictStr): Current path of each name.
            qual (str): Qualified name of the function.

        Returns:
            DictStr: The environment for the handler body.

        """
        if part.name is None:
            return env
        found: StrOrNone = exception_types(
            node=part.type,
            counts=self._counts,
            classes=self._top_classes,
        )
        if found is None:
            return env
        path: str = f"{qual}.{part.name}#{part.lineno}e"
        self._graph.add_node(path=path)
        self._seed_type(
            target=path,
            type_text=found,
            origin=Origin.syntax,
            why=f"{path} is {found} from the except clause",
        )
        bound: DictStr = dict(env)
        bound[part.name] = path
        return bound

    def _register(
        self,
        *,
        node: AST | None,
        env: DictStr,
        scope: _Scope,
    ) -> None:
        """Record the narrowed path of every name an expression reads.

        Args:
            node (AST | None): AST node to walk, or ``None``.
            env (DictStr): Current path of each name.
            scope (_Scope): Function scope.

        """
        pending: list[AST] = [node] if isinstance(node, AST) else []
        while pending:
            current: AST = pending.pop()
            if isinstance(current, Constants.scopes):
                continue
            if (
                isinstance(current, Name)
                and isinstance(current.ctx, Load)
                and current.id in env
                and env[current.id] != scope.names.get(current.id)
            ):
                self._name_path[id(current)] = env[current.id]
            pending.extend(iter_child_nodes(node=current))

    def _attributes(self, *, unique: list[tuple[str, Function, bool]]) -> None:
        """Create nodes for instance attributes that only the class writes.

        An attribute qualifies when every write to that name in the whole
        module is a plain ``self.name = value`` in a method of one safe
        class, the class has no dynamic attribute access, no base class or
        class-level binding clashes, and the receiver is never rebound.

        Args:
            unique (list[tuple[str, Function, bool]]): Functions with
                unambiguous qualified names.

        """
        index: MethodIndex = self._methods
        if index.dynamic_attributes or index.intercepts:
            return
        stores: Counter[str] = _external_stores(module=self._module)
        classes: dict[str, ClassDef] = dict(
            walk_classes(node=self._module, trail=()),
        )
        owned: dict[str, list[tuple[Function, str]]] = {}
        for qual, function, in_class in unique:
            receiver: StrOrNone = receiver_of(function=function)
            owner: str = qual.rpartition(".")[0]
            if in_class and receiver is not None and owner in classes:
                owned.setdefault(owner, []).append((function, receiver))
        for owner, methods in owned.items():
            cls: ClassDef = classes[owner]
            if index.class_ok(cls=cls):
                self._class_attributes(
                    owner=owner,
                    _cls=cls,
                    methods=methods,
                    index=index,
                    stores=stores,
                )

    def _bind_receivers(
        self,
        *,
        methods: list[tuple[Function, str]],
        members: DictStr,
    ) -> None:
        """Let each method read the class's attributes through its receiver.

        A method that rebinds its receiver (``self = other``) reads another
        object's attributes afterwards, so it gets none.

        Args:
            methods (list[tuple[Function, str]]): The class's methods with
                their receiver names.
            members (DictStr): Node path by attribute name.

        """
        for function, receiver in methods:
            if any(
                receiver in names_bound_by(node=node)
                for node in own_nodes(function=function)
            ):
                continue
            scope: _Scope = self._scopes[id(function)]
            scope.receiver = receiver
            scope.members = members

    def _class_attributes(
        self,
        *,
        owner: str,
        _cls: ClassDef,
        methods: list[tuple[Function, str]],
        index: MethodIndex,
        stores: Counter[str],
    ) -> None:
        """Create the attribute nodes of one class and link their writes.

        Args:
            owner (str): Qualified name of the class.
            _cls (ClassDef): The class definition.
            methods (list[tuple[Function, str]]): Its methods with their
                receiver parameter names.
            index (MethodIndex): Method facts of the module.
            stores (Counter[str]): Attribute writes in the module by name.

        """
        writes: dict[str, list[tuple[Function, Assign]]] = {}
        bad: SetStr = set()
        for function, receiver in methods:
            found, touched = _own_writes(method=function, receiver=receiver)
            bad |= touched
            for name, assigns in found.items():
                writes.setdefault(name, []).extend(
                    (function, item) for item in assigns
                )
        inherited: SetStr = index.inherited_names(_cls=_cls)
        members: DictStr = {}
        for name, items in writes.items():
            if (
                name in bad
                or name in inherited
                or index.binds(owner=_cls, name=name) > 0
                or stores.get(name, 0) != len(items)
            ):
                continue
            path: str = f"{owner}.{name}"
            members[name] = path
            self._graph.add_node(path=path)
        for name, path in members.items():
            for function, receiver in methods:
                if attribute_risky(
                    function=function,
                    receiver=receiver,
                    attribute=name,
                    counts=self._counts,
                ):
                    self._risky.add(path)
            first: tuple[Function, Assign] = sorted(
                writes[name],
                key=lambda pair: (pair[0].name != "__init__", pair[1].lineno),
            )[0]
            self._attribute_writes[path] = first[1]
            for function, item in writes[name]:
                self._flow(
                    value=item.value,
                    target=path,
                    scope=self._scopes[id(function)],
                    origin=Origin.syntax,
                    relation=Relation.instance_field,
                )
        self._bind_receivers(methods=methods, members=members)

    def _body(self, *, qual: str, function: Function) -> None:
        """Add the contracts of a function body.

        Args:
            qual (str): Qualified name.
            function (Function): Function definition.

        """
        scope: _Scope = self._scopes[id(function)]
        ret: str = f"{qual}->"
        if function.name in HintConstants.protocol_results:
            self._protocol(function=function, ret=ret)
            return
        if is_declaration(function=function) or never_returns(
            function=function,
        ):
            self._block(path=ret, why="stub, abstract or never returns")
        calibrated: bool = boolean_returns(function=function)
        for node in own_nodes(function=function):
            if isinstance(node, (Yield, YieldFrom)):
                self._block(path=ret, why="generator")
            elif isinstance(node, Return):
                self._return(
                    value=node.value,
                    ret=ret,
                    scope=scope,
                    calibrated=calibrated,
                )
            elif isinstance(node, Assign):
                self._assignment(
                    node=node,
                    function=function,
                    qual=qual,
                    scope=scope,
                )
            elif isinstance(node, AnnAssign):
                self._annotated(node=node, qual=qual, scope=scope)
            elif isinstance(node, (For, NamedExpr)):
                self._rebind(node=node, qual=qual, scope=scope)
        if can_fall_off(body=function.body):
            self._seed_type(
                target=ret,
                type_text="None",
                origin=Origin.syntax,
                why="falls off the end",
            )

    def _library_return(self, *, call: Call, scope: _Scope) -> StrOrNone:
        """Type a call into the standard library from its stub.

        A single plain signature counts directly; an ``@overload`` group
        is picked by the proven types of the arguments. Methods of stub
        classes resolve through the receiver's class name.

        Args:
            call (Call): The call expression.
            scope (_Scope): Scope the call is evaluated in.

        Returns:
            StrOrNone: The return type, or ``None`` when it is not certain.

        """
        if self._library is None:
            return None
        allowed: frozenset[str] = frozenset(ImportConstants.known_imports)
        key: StrOrNone = callee_name(
            module=self._module,
            counts=self._counts,
            call=call,
        )
        found: Resolved | None = (
            None if key is None else self._library.resolve(qualified=key)
        )
        if found is None and isinstance(call.func, Attribute):
            found = self._library_method(call=call)
        if found is None and isinstance(call.func, Attribute):
            return self._library_typed_method(call=call, scope=scope)
        if found is None:
            return None
        if found.name.overloaded:
            return select_overload(
                resolved=found,
                positional=[
                    expression_type(
                        node=arg,
                        counts=self._counts,
                        env=scope.env,
                    )
                    for arg in call.args
                ],
                keywords={
                    keyword.arg: expression_type(
                        node=keyword.value,
                        counts=self._counts,
                        env=scope.env,
                    )
                    for keyword in call.keywords
                    if keyword.arg is not None
                },
                allowed=allowed,
                resolver=self._library,
            )
        return function_return(resolved=found, allowed=allowed)

    def _library_method(self, *, call: Call) -> Resolved | None:
        """Resolve ``receiver.method(...)`` on a known library class.

        The receiver must name a class syntactically: a constructor call
        (``Path(p).read_text()``) or an imported class object
        (``datetime.now()``). Anything else stays opaque.

        Args:
            call (Call): The call expression; ``call.func`` is an ``Attribute``
                .

        Returns:
            Resolved | None: The resolved method, or ``None``.

        """
        if self._library is None or not isinstance(call.func, Attribute):
            return None
        owner: StrOrNone = self._receiver_class(node=call.func.value)
        if owner is None:
            return None
        return self._library.resolve_method(
            class_name=owner,
            method=call.func.attr,
        )

    def _receiver_kind(
        self,
        *,
        value: expr,
        scope: _Scope,
    ) -> tuple[StrOrNone, StrOrNone]:
        """Resolve a method receiver's proven type and import origin.

        Args:
            value (expr): The receiver expression.
            scope (_Scope): Scope the call is evaluated in.

        Returns:
            tuple[StrOrNone, StrOrNone]: ``(type, origin)``, ``None`` when the
                type is unproven.

        """
        if isinstance(value, Name):
            kind: StrOrNone = self._seeded_type(node=value, scope=scope)
            if kind is None:
                kind = expression_type(
                    node=value,
                    counts=self._counts,
                    env=scope.env,
                )
                constraint: StrOrNone = self._narrowing_of(node=value)
                if constraint is not None and kind is not None:
                    kind = TypeAlgebra().narrow(
                        current=kind,
                        constraint=constraint,
                    )
            return kind, None
        if isinstance(value, Attribute):
            library: Resolver | None = self._library
            if library is None:
                return None, None
            variable: Resolved | None = library.resolve(
                qualified=unparse(ast_obj=value),
            )
            if variable is not None and variable.name.kind == "variable":
                return variable_type(resolved=variable), variable.module.name
        return None, None

    def _library_typed_method(
        self,
        *,
        call: Call,
        scope: _Scope,
    ) -> StrOrNone:
        """Type a method call on a name with a proven library type.

        The receiver's proven annotation names the stub class and binds
        its type variables, so ``m: Match[str]`` makes ``m.group()``
        state ``str``. Unions and unknown receivers are refused.

        Args:
            call (Call): The call expression.
            scope (_Scope): Scope the call is evaluated in.

        Returns:
            StrOrNone: The return type, or ``None`` when it is not certain.

        """
        if self._library is None:
            return None
        func: expr = call.func
        if not isinstance(func, Attribute):
            return None
        kind: StrOrNone
        origin: StrOrNone
        kind, origin = self._receiver_kind(value=func.value, scope=scope)
        if kind is None:
            return None
        parts: tuple[str, list[expr]] | None = receiver_parts(source=kind)
        if parts is None:
            return None
        head: str = parts[0]
        if "." not in head:
            if origin is not None:
                head = f"{origin}.{head}"
            else:
                prefix: StrOrNone = ImportConstants.known_imports.get(head)
                head = (
                    f"{prefix}.{head}"
                    if prefix is not None
                    else f"builtins.{head}"
                )
        resolved: Resolved | None = self._library.resolve_method(
            class_name=head,
            method=func.attr,
        )
        if resolved is None:
            return None
        return method_return(
            resolved=resolved,
            receiver=parts[1],
            call=CallArguments(
                positional=tuple(
                    expression_type(
                        node=arg,
                        counts=self._counts,
                        env=scope.env,
                    )
                    for arg in call.args
                ),
                keywords={
                    keyword.arg: expression_type(
                        node=keyword.value,
                        counts=self._counts,
                        env=scope.env,
                    )
                    for keyword in call.keywords
                    if keyword.arg is not None
                },
            ),
            allowed=frozenset(ImportConstants.known_imports),
            resolver=self._library,
        )

    def _narrowing_of(self, *, node: expr) -> StrOrNone:
        """Constraint text narrowing the node a name read resolved to.

        Args:
            node (expr): The name expression read.

        Returns:
            StrOrNone: The ``" & "`` -joined constraint of its narrowed
                node, or ``None`` when the read saw no narrowing.

        """
        path: StrOrNone = self._name_path.get(id(node))
        if path is None or "#" not in path:
            return None
        return self._seed_text(path=path)

    def _seeded_type(self, *, node: expr, scope: _Scope) -> StrOrNone:
        """Type a name read from the seeds of the node it resolves to.

        A narrowed read applies its constraint to the base node's seed,
        so ``m`` inside ``if m:`` reads ``Match[str]`` rather than
        ``Match[str] | None``. Several distinct seeds union, which the
        receiver parser then refuses.

        Args:
            node (expr): The name expression read.
            scope (_Scope): Function scope, for the binding's node path.

        Returns:
            StrOrNone: The seeded type text, or ``None``.

        """
        if not isinstance(node, Name):
            return None
        path: StrOrNone = self._name_path.get(id(node))
        if path is not None and "#" in path:
            base: str = path.split(sep="#", maxsplit=1)[0]
            constraint: StrOrNone = self._seed_text(path=path)
            seeded: StrOrNone = self._seed_text(path=base)
            if constraint is None or seeded is None:
                return None
            return TypeAlgebra().narrow(current=seeded, constraint=constraint)
        path = path or scope.names.get(node.id)
        return None if path is None else self._seed_text(path=path)

    def _seed_text(self, *, path: str) -> StrOrNone:
        """Type text a node path is seeded with.

        Args:
            path (str): Contract node path.

        Returns:
            StrOrNone:
                The single seed's text, the union of several, or ``None``.

        """
        texts: SetStr = {
            candidate.type_text
            for seed_path, candidate, _polarity in self._graph.seeds()
            if seed_path == path
        }
        if not texts:
            return None
        if len(texts) == 1:
            return next(iter(texts))
        return " | ".join(sorted(texts))

    def _receiver_class(self, *, node: expr) -> StrOrNone:
        """Name the library class an expression constructs or refers to.

        Args:
            node (expr): Receiver expression of a method call.

        Returns:
            StrOrNone:
                A dotted class name the resolver understands, or ``None``.

        """
        target: expr = node
        if isinstance(target, Call):
            target = target.func
        aliases: DictStr = import_aliases(module=self._module)
        parts: list[str] = []
        while isinstance(target, Attribute):
            parts.append(target.attr)
            target = target.value
        if not isinstance(target, Name):
            return None
        root: str = target.id
        prefix: StrOrNone = aliases.get(root)
        if prefix is not None:
            limit: int = 1 if root in aliases else 0
            if self._counts.get(root, 0) > limit:
                return None
            return ".".join((prefix, *reversed(parts)))
        return None

    def _proved(self, *, value: expr, scope: _Scope) -> bool:
        """Tell whether an expression's type is known without any derivation.

        Args:
            value (expr): The expression.
            scope (_Scope): Scope the expression is evaluated in.

        Returns:
            bool: ``True`` for a node or an expression the syntax typer proves.

        """
        return (
            self._node_source(value=value, scope=scope) is not None
            or expression_type(
                node=value,
                counts=self._counts,
                env=scope.env,
            )
            is not None
        )

    def _return(
        self,
        *,
        value: expr | None,
        ret: str,
        scope: _Scope,
        calibrated: bool,
    ) -> None:
        """Account for one ``return`` statement.

        Args:
            value (expr | None): The returned expression, or ``None`` for a
                bare return.
            ret (str): The function's return node path.
            scope (_Scope): Function scope.
            calibrated (bool): Whether every returned value is boolean by
                syntax.

        """
        if value is None:
            self._seed_type(
                target=ret,
                type_text="None",
                origin=Origin.syntax,
                why="bare return",
            )
        elif calibrated and not self._proved(value=value, scope=scope):
            self._seed_type(
                target=ret,
                type_text="bool",
                origin=Origin.calibrated,
                why=f"{ret} returns {unparse(ast_obj=value)}",
            )
        else:
            self._flow(
                value=value,
                target=ret,
                scope=scope,
                origin=Origin.syntax,
                relation=Relation.returns,
            )

    def _protocol(self, *, function: Function, ret: str) -> None:
        """Give a protocol dunder its declared result, or leave it opaque.

        Args:
            function (Function): A function named like a protocol method.
            ret (str): Its return node path.

        """
        declared: StrOrNone = protocol_result_for(
            function=function,
            counts=self._counts,
        )
        if declared is None:
            self._block(path=ret, why="protocol result does not fit")
        else:
            self._seed_type(
                target=ret,
                type_text=declared,
                origin=Origin.protocol,
                why=f"{function.name} is declared to return {declared}",
            )

    def _annotated(self, *, node: AnnAssign, qual: str, scope: _Scope) -> None:
        """Take an annotated local at its word.

        Args:
            node (AnnAssign): The annotated assignment.
            qual (str): Qualified name of the function.
            scope (_Scope): Function scope.

        """
        if not isinstance(node.target, Name):
            return
        path: StrOrNone = scope.names.get(node.target.id)
        if path is None or not path.startswith(f"{qual}."):
            return
        source: StrOrNone = _declared_source(annotation=node.annotation)
        if source is None:
            if node.value is not None:
                self._flow(
                    value=node.value,
                    target=path,
                    scope=scope,
                    origin=Origin.syntax,
                    relation=Relation.assigns,
                )
            return
        self._declared(path=path, source=source)

    def _assignment(
        self,
        *,
        node: Assign,
        function: Function,
        qual: str,
        scope: _Scope,
    ) -> None:
        """Link ``name = value`` for a node-backed local.

        Args:
            node (Assign): The assignment.
            function (Function): The enclosing function.
            qual (str): Qualified name of the function.
            scope (_Scope): Function scope.

        """
        if len(node.targets) != 1 or not isinstance(node.targets[0], Name):
            return
        name: str = node.targets[0].id
        path: StrOrNone = scope.names.get(name)
        if path is None or not path.startswith(f"{qual}."):
            return
        self._variables[path] = node
        literal: StrOrNone = literal_kind(value=node.value)
        if literal is not None:
            self._literal_container(
                node=node,
                function=function,
                path=path,
                kind=literal,
                scope=scope,
            )
            return
        kind: StrOrNone = empty_kind(value=node.value, counts=self._counts)
        if kind is not None:
            self._container(
                function=function,
                name=name,
                path=path,
                kind=kind,
                scope=scope,
            )
            return
        self._flow(
            value=node.value,
            target=path,
            scope=scope,
            origin=Origin.syntax,
            relation=Relation.assigns,
        )

    def _literal_container(
        self,
        *,
        node: Assign,
        function: Function,
        path: str,
        kind: str,
        scope: _Scope,
    ) -> None:
        """Type a container built from a literal, if nothing widens it.

        The literal fixes the element type only while every later use is
        understood; elements added by ``append``/``insert``/``add`` join it,
        and a dict (or anything else that is mutated in a way not modelled)
        must stay read-only.

        Args:
            node (Assign): The assignment.
            function (Function): The enclosing function.
            path (str): The variable's node path.
            kind (str): ``"list"``, ``"set"`` or ``"dict"``.
            scope (_Scope): Function scope.

        """
        name: str = (
            node.targets[0].id if isinstance(node.targets[0], Name) else ""
        )
        elements: tuple[expr, ...] | None = fillings(
            function=function,
            name=name,
            kind=kind,
            counts=self._counts,
        )
        proven: StrOrNone = expression_type(
            node=node.value,
            counts=self._counts,
            env=scope.env,
        )
        if (
            proven is None
            and elements == ()
            and isinstance(node.value, Constants.comprehensions)
        ):
            found: tuple[str, str, Relation] | None = self._derived(
                value=node.value,
                scope=scope,
                shapes=True,
            )
            if found is not None:
                self._link(
                    source=found[1],
                    target=path,
                    relation=Relation.assigns,
                    why=f"{path} = {unparse(ast_obj=node.value)}",
                )
                return
        if elements is None or proven is None:
            self._block(
                path=path,
                why="container literal mutated or not provable",
            )
            return
        if not elements:
            self._seed_type(
                target=path,
                type_text=proven,
                origin=Origin.syntax,
                why=f"{path} = {unparse(ast_obj=node.value)}",
            )
            return
        held: str = f"{path}[]"
        self._graph.add_node(path=held)
        first: Candidate | None = forward(
            candidate=Candidate(
                type_text=proven,
                confidence=1.0,
                distance=0,
                origins=frozenset({Origin.syntax}),
                explanation=f"{path} starts as {unparse(ast_obj=node.value)}",
            ),
            relation=Relation.element,
        )
        if first is None or kind == "dict":
            self._block(path=path, why="container element type unknown")
            return
        self._graph.seed(path=held, candidate=first)
        for element in elements:
            self._flow(
                value=element,
                target=held,
                scope=scope,
                origin=Origin.syntax,
                relation=Relation.assigns,
            )
        self._link(
            source=held,
            target=path,
            relation=Relation.list_of if kind == "list" else Relation.set_of,
            why=f"{path} holds what is added to it",
        )

    def _container(
        self,
        *,
        function: Function,
        name: str,
        path: str,
        kind: str,
        scope: _Scope,
    ) -> None:
        """Type a local container from the elements put into it.

        Args:
            function (Function): The enclosing function.
            name (str): The local's name.
            path (str): Its node path.
            kind (str): ``"list"`` or ``"set"``.
            scope (_Scope): Function scope.

        """
        elements: tuple[expr, ...] | None = fillings(
            function=function,
            name=name,
            kind=kind,
            counts=self._counts,
        )
        if elements is None:
            self._block(path=path, why="container used in an unknown way")
            return
        held: str = f"{path}[]"
        self._graph.add_node(path=held)
        for element in elements:
            self._flow(
                value=element,
                target=held,
                scope=scope,
                origin=Origin.syntax,
                relation=Relation.assigns,
            )
        self._link(
            source=held,
            target=path,
            relation=Relation.list_of if kind == "list" else Relation.set_of,
            why=f"{path} holds what is added to it",
        )

    def _loop(self, *, node: For, qual: str, scope: _Scope) -> None:
        """Link ``for name in iterable`` to the element type.

        Args:
            node (For): The loop.
            qual (str): Qualified name of the function.
            scope (_Scope): Function scope.

        """
        if not isinstance(node.target, Name):
            return
        path: StrOrNone = scope.names.get(node.target.id)
        if path is None or not path.startswith(f"{qual}."):
            return
        source: expr = node.iter
        if isinstance(source, Name) and source.id in scope.names:
            self._link(
                source=scope.names[source.id],
                target=path,
                relation=Relation.element,
                why=f"{path} iterates {source.id}",
            )
            return
        proven: StrOrNone = expression_type(
            node=source,
            counts=self._counts,
            env=scope.env,
        )
        if proven is None:
            self._block(path=path, why="loop iterable not provable")
            return
        moved: Candidate | None = forward(
            candidate=Candidate(
                type_text=proven,
                confidence=1.0,
                distance=0,
                origins=frozenset({Origin.syntax}),
                explanation=f"{path} iterates {unparse(ast_obj=source)}",
            ),
            relation=Relation.element,
        )
        if moved is None:
            self._block(path=path, why="loop iterable has no element type")
        else:
            self._graph.seed(path=path, candidate=moved)

    def _rebind(
        self,
        *,
        node: For | NamedExpr,
        qual: str,
        scope: _Scope,
    ) -> None:
        """Build the contract of a name-binding flow node.

        Args:
            node (For | NamedExpr): A ``for`` target or a walrus assignment.
            qual (str): Qualified name of the enclosing function.
            scope (_Scope): Name resolution of the enclosing function.

        """
        if isinstance(node, For):
            self._loop(node=node, qual=qual, scope=scope)
        else:
            self._walrus(node=node, qual=qual, scope=scope)

    def _walrus(self, *, node: NamedExpr, qual: str, scope: _Scope) -> None:
        """Link ``(name := value)`` to the local it binds.

        Args:
            node (NamedExpr): The walrus expression.
            qual (str): Qualified name of the function.
            scope (_Scope): Function scope.

        """
        path: StrOrNone = scope.names.get(node.target.id)
        if path is None or not path.startswith(f"{qual}."):
            return
        self._flow(
            value=node.value,
            target=path,
            scope=scope,
            origin=Origin.syntax,
            relation=Relation.assigns,
        )

    def _calls(self, *, unique: list[tuple[str, Function, bool]]) -> None:
        """Add argument contracts and evidence for every call.

        Args:
            unique (list[tuple[str, Function, bool]]): Functions with
                unambiguous qualified names.

        """
        scopes: dict[int, _Scope] = {
            id(call): self._scopes[id(function)]
            for _qual, function, _cls in unique
            for call in own_calls(function=function)
        }
        outer: _Scope = _Scope(env=self._constants)
        for name in self._escaped & self._by_name.keys():
            self._block_all(
                paths=self._params.get(self._by_name[name], ()),
                why="function escapes as a value",
            )
        for call in walk(node=self._module):
            if not isinstance(call, Call):
                continue
            scope: _Scope = scopes.get(id(call), outer)
            bound: BoundCall | None = self._bindings.get(call=call)
            callee: StrOrNone = (
                None
                if bound is None or bound.signature.declaration is None
                else self._ids.get(id(bound.signature.declaration))
            )
            if bound is not None and callee is not None:
                self._arguments(bound=bound, callee=callee, scope=scope)
            elif isinstance(call.func, Name) and call.func.id in self._by_name:
                self._block_all(
                    paths=self._params.get(self._by_name[call.func.id], ()),
                    why="a call to it cannot be bound",
                )

    def _arguments(
        self,
        *,
        bound: BoundCall,
        callee: str,
        scope: _Scope,
    ) -> None:
        """Turn the arguments of a bound call into evidence.

        Args:
            bound (BoundCall): The trusted binding.
            callee (str): Qualified name of the called function.
            scope (_Scope): Scope of the call.

        """
        for argument in bound.arguments:
            path: str = f"{callee}.{argument.parameter.name}"
            if path not in self._kinds:
                continue
            origin: ArgumentOrigin = argument.origin
            if origin in Constants.variadic or origin not in (
                *Constants.passed,
                ArgumentOrigin.EXPANSION_UNKNOWN,
            ):
                continue
            if (
                origin is ArgumentOrigin.EXPANSION_UNKNOWN
                or len(argument.values) != 1
            ):
                self._block(path=path, why="argument unknown (star or many)")
                continue
            value: AST = argument.values[0]
            if isinstance(value, expr):
                self._flow(
                    value=value,
                    target=path,
                    scope=scope,
                    origin=Origin.call_sites,
                    relation=Relation.argument,
                )
            else:
                self._block(path=path, why="argument is not an expression")

    def _node_source(
        self,
        *,
        value: expr,
        scope: _Scope,
    ) -> tuple[str, str, Relation] | None:
        """Recognise an expression that is another node's value.

        Args:
            value (expr): Expression.
            scope (_Scope): Scope the expression is evaluated in.

        Returns:
            tuple[str, str, Relation] | None:
                ``("node", path, relation)`` for a variable, a parameter,
                an attribute of the instance, a call to a function of the
                module (``("seed", class, assigns)`` for a constructor)
                or an item of one of those; ``None`` for anything else.

        """
        if isinstance(value, Name):
            narrowed: StrOrNone = self._name_path.get(id(value))
            if narrowed is not None:
                return "node", narrowed, Relation.assigns
            if value.id in scope.names:
                return (
                    "node",
                    scope.names[value.id],
                    Relation.assigns,
                )
        if (
            isinstance(value, Attribute)
            and isinstance(value.ctx, Load)
            and isinstance(value.value, Name)
            and value.value.id == scope.receiver
            and value.attr in scope.members
        ):
            return "node", scope.members[value.attr], Relation.instance_field
        if isinstance(value, Call):
            return self._call_source(call=value)
        if (
            isinstance(value, Subscript)
            and isinstance(value.value, Name)
            and value.value.id in scope.names
            and not isinstance(value.slice, Slice)
        ):
            return (
                "node",
                self._name_path.get(
                    id(value.value),
                    scope.names[value.value.id],
                ),
                Relation.item,
            )
        return None

    def _source(
        self,
        *,
        value: expr,
        scope: _Scope,
        shapes: bool = True,
    ) -> tuple[str, str, Relation] | None:
        """Decide where a value's type comes from.

        Args:
            value (expr): Expression.
            scope (_Scope): Scope the expression is evaluated in.
            shapes (bool): Whether a tuple-literal shape may be the type;
                call-site arguments say too little about it.

        Returns:
            tuple[str, str, Relation] | None:
                ``("node", path, relation)`` or ``("seed", type, relation)``
                , or ``None`` when nothing sound can be said.

        """
        found: tuple[str, str, Relation] | None = self._node_source(
            value=value,
            scope=scope,
        )
        if found is not None:
            return found
        proven: StrOrNone = expression_type(
            node=value,
            counts=self._counts,
            env=scope.env,
        )
        if proven is None and isinstance(value, Call):
            proven = self._library_return(call=value, scope=scope)
        if proven is None:
            return self._derived(value=value, scope=scope, shapes=shapes)
        if proven.startswith(HintConstants.shape_specific) and not shapes:
            return None
        return "seed", proven, Relation.assigns

    def _call_source(
        self,
        *,
        call: Call,
    ) -> tuple[str, str, Relation] | None:
        """Decide what a call to a function of this module evaluates to.

        Args:
            call (Call): The call expression.

        Returns:
            tuple[str, str, Relation] | None:
                The callee's return node, the class name
                for a constructor call, or ``None`` for
                anything else (coroutines, unbound callees).

        """
        if (
            isinstance(call.func, Name)
            and call.func.id in self._top_classes
            and self._methods.is_class_name(name=call.func.id)
            and self._methods.constructor_safe(name=call.func.id)
        ):
            return "seed", call.func.id, Relation.assigns
        bound: BoundCall | None = self._bindings.get(call=call)
        if bound is None or bound.signature.declaration is None:
            return None
        callee: StrOrNone = self._ids.get(id(bound.signature.declaration))
        if callee is None or callee in self._coroutines:
            return None
        owner, _, method = callee.rpartition(".")
        if method in Constants.constructors:
            if owner in self._top_classes and self._counts.get(owner) == 1:
                return "seed", owner, Relation.assigns
            return None
        return "node", f"{callee}->", Relation.call_result

    def _operand(self, *, value: expr, scope: _Scope) -> StrOrNone:
        """Name the node that holds the value of an operand expression.

        Args:
            value (expr): A sub-expression.
            scope (_Scope): Scope the expression is evaluated in.

        Returns:
            StrOrNone:
                The node path for a variable, a parameter, an attribute of
                the instance, a call to a function of the module or an item
                of one of those; ``None`` when the expression is not a node.

        """
        found: tuple[str, str, Relation] | None = self._node_source(
            value=value,
            scope=scope,
        )
        if found is None or found[0] != "node":
            return None
        if found[2] in {
            Relation.assigns,
            Relation.call_result,
            Relation.instance_field,
        }:
            return found[1]
        hidden: str = self._hidden(value=value, scope=scope)
        self._link(
            source=found[1],
            target=hidden,
            relation=found[2],
            why=f"{hidden} is {unparse(ast_obj=value)}",
        )
        return hidden

    def operand(self, *, value: expr, scope: _Scope) -> StrOrNone:
        """Name the node that holds the value of an operand expression.

        Args:
            value (expr): A sub-expression.
            scope (_Scope): Scope the expression is evaluated in.

        Returns:
            StrOrNone:
                The node path, or ``None`` when the expression is not a node.

        """
        return self._operand(value=value, scope=scope)

    def is_builtin(self, *, name: str) -> bool:
        """Tell whether a name is a builtin the module does not rebind.

        Args:
            name (str): A name used as a callee.

        Returns:
            bool: ``True`` for an unshadowed builtin.

        """
        return (name in __dict__) and self._counts.get(name, 0) == 0

    def _hidden(self, *, value: expr, scope: _Scope) -> str:
        """Make the node that stands for an expression's value.

        Args:
            value (expr): The expression.
            scope (_Scope): Scope the expression is evaluated in.

        Returns:
            str: Its path, unique by position.

        """
        path: str = (
            f"{scope.qual}.<{type(value).__name__}"
            f"@{value.lineno}:{value.col_offset}>"
        )
        self._graph.add_node(path=path)
        return path

    def _derived(
        self,
        *,
        value: expr,
        scope: _Scope,
        shapes: bool,
    ) -> tuple[str, str, Relation] | None:
        """Make a derived node for an expression over other nodes.

        Args:
            value (expr): The expression.
            scope (_Scope): Scope the expression is evaluated in.
            shapes (bool): Whether a container literal may be derived.

        Returns:
            tuple[str, str, Relation] | None:
                ``("node", path, assigns)`` for the new node, or ``None`` when
                the expression has no operand node or reads something unknown.

        """
        if not isinstance(value, Constants.derivable):
            return None
        if not shapes and isinstance(value, (Tuple, List, Dict, Set)):
            return None
        templater: _Templater = _Templater(builder=self, scope=scope)
        template: expr | None = templater.convert(value=value)
        if template is None or not templater.parts:
            return None
        target: str = self._hidden(value=value, scope=scope)
        self._graph.add_derived(
            derived=Derived(
                target=target,
                template=template,
                parts=tuple(templater.parts),
                fixed=tuple(sorted(templater.fixed.items())),
                explanation=unparse(ast_obj=value),
            ),
        )
        return "node", target, Relation.assigns

    def _flow(
        self,
        *,
        value: expr,
        target: str,
        scope: _Scope,
        origin: Origin,
        relation: Relation,
    ) -> None:
        """Connect a value to a node, or mark the node opaque.

        Args:
            value (expr): The expression flowing in.
            target (str): Node path receiving it.
            scope (_Scope): Scope of the expression.
            origin (Origin): Origin recorded for a syntax-proven seed.
            relation (Relation): Relation to use when the value is another
                node.

        """
        if isinstance(value, IfExp):
            self._flow(
                value=value.body,
                target=target,
                scope=scope,
                origin=origin,
                relation=relation,
            )
            self._flow(
                value=value.orelse,
                target=target,
                scope=scope,
                origin=origin,
                relation=relation,
            )
            return
        found: tuple[str, str, Relation] | None = self._source(
            value=value,
            scope=scope,
            shapes=origin is not Origin.call_sites,
        )
        if found is None:
            self._block(
                path=target,
                why=(
                    f"unprovable {type(value).__name__}: "
                    f"{unparse(ast_obj=value)[:60]}"
                ),
            )
        elif found[0] == "node":
            link: Relation = (
                relation if found[2] is Relation.assigns else found[2]
            )
            self._link(
                source=found[1],
                target=target,
                relation=link,
                why=f"{target} <- {unparse(ast_obj=value)}",
            )
        else:
            self._seed_type(
                target=target,
                type_text=found[1],
                origin=origin,
                why=f"{target} <- {unparse(ast_obj=value)}",
            )

    def _seed_value(
        self,
        *,
        value: expr,
        target: str,
        scope: _Scope,
        origin: Origin,
    ) -> None:
        """Seed a node with a syntax-proven expression, or mark it opaque.

        Args:
            value (expr): The expression.
            target (str): Node path.
            scope (_Scope): Scope of the expression.
            origin (Origin): Origin to record.

        """
        proven: StrOrNone = expression_type(
            node=value,
            counts=self._counts,
            env=scope.env,
        )
        if proven is None or proven.startswith(HintConstants.shape_specific):
            self._block(path=target, why="default or value not provable")
        else:
            self._seed_type(
                target=target,
                type_text=proven,
                origin=origin,
                why=f"{target} = {unparse(ast_obj=value)}",
            )

    def _seed_type(
        self,
        *,
        target: str,
        type_text: str,
        origin: Origin,
        why: str,
    ) -> None:
        """Seed a node with a type.

        Args:
            target (str): Node path.
            type_text (str): The type.
            origin (Origin): What supports it.
            why (str): Explanation recorded with the candidate.

        """
        self._graph.seed(
            path=target,
            candidate=Candidate(
                type_text=type_text,
                confidence=1.0,
                distance=0,
                origins=frozenset({origin}),
                explanation=why,
            ),
        )

    def _link(
        self,
        *,
        source: str,
        target: str,
        relation: Relation,
        why: str,
    ) -> None:
        """Add a union contract between two nodes.

        Args:
            source (str): Source node path.
            target (str): Target node path.
            relation (Relation): What the contract states.
            why (str): Explanation recorded with the contract.

        """
        self._graph.add_contract(
            contract=Contract(
                source=source,
                target=target,
                relation=relation,
                polarity=Polarity.union,
                confidence=1.0,
                decay=1.0,
                explanation=why,
            ),
        )


def build_contracts(
    *,
    module: CommentedModule,
    escaped: frozenset[str],
    library: Resolver | None = None,
) -> Built:
    """Build the contract graph of a module.

    Args:
        module (CommentedModule): Parsed module.
        escaped (frozenset[str]): Names read as values, whose callers are
            unknown.
        library (Resolver | None): Resolver over typeshed, or ``None``.

    Returns:
        Built: The graph with its opaque nodes and node kinds.

    """
    return ContractBuilder(
        module=module,
        escaped=escaped,
        library=library,
    ).build()
