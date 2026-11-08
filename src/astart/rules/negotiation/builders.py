"""Turn a parsed module into a graph of contracts.

Every parameter, return value and singly-bound local of a function is a
node. Facts the syntax proves become seeds; flows between nodes become
contracts. Anything the builder cannot account for marks the node *opaque*,
so no type is ever settled from partial knowledge.
"""

from __future__ import annotations

import builtins
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
    Name,
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
    operator,
    stmt,
    unaryop,
    unparse,
    walk,
)
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
from astart.rules.library_calls import callee_name
from astart.rules.methods import MethodIndex
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
from astart.rules.negotiation.narrowing import Arms, read_test
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
from astart.stubs import function_return

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
        receivers: Names of the implicit first parameter of a method.
        passed: Argument origins that carry an explicit value.
        variadic: Argument origins of ``*args`` and ``**kwargs``.
        constructors: Methods whose call evaluates to the class instead.
        scopes: Nodes that open a scope the narrowing must not enter.
        derivable: Expression kinds a derived node may be built from.
        comprehensions: Comprehensions, which build fresh containers.
        leaves: Expressions that need no operand.
        markers: Syntax nodes that are copied as they are.
        type_variables: Callees that declare a type variable.

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
    )
    comprehensions: Final[tuple[type[expr], ...]] = (
        ListComp,
        SetComp,
        DictComp,
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


@final
@dataclass(frozen=True, slots=True)
class Built:
    """A module's contract graph.

    Attributes:
        graph: Nodes, contracts and seeds.
        opaque: Nodes whose evidence is incomplete; nothing may be settled
            for them or anything they flow into.
        kinds: ``"parameter"`` or ``"return"`` for the nodes worth reporting.
        variables: The assignment that binds each function-local variable,
            by node path.
        attributes: The first write of each instance attribute (the one in
            ``__init__`` when there is one), by node path.
        why: The first reason each opaque node is opaque.
        risky: Attributes some method uses in a way that could change the
            element type of a container they hold; opaque if they settle to
            one.

    """

    graph: ContractGraph
    opaque: frozenset[str]
    kinds: dict[str, str]
    variables: dict[str, Assign]
    attributes: dict[str, Assign]
    risky: frozenset[str]
    why: dict[str, str]


@final
@dataclass(slots=True)
class _Scope:
    """The names a function body can reason about.

    Attributes:
        names: Node path by local or parameter name.
        env: Proven type by name, for the syntax typer.
        receiver: Name of the instance parameter inside a method.
        members: Node path by instance attribute the class owns.
        qual: Qualified name of the function.

    """

    names: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    receiver: str | None = None
    members: dict[str, str] = field(default_factory=dict)
    qual: str = ""


def walk_functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    in_class: bool,
) -> Iterator[tuple[str, Function, bool]]:
    """List every function with its qualified name.

    Args:
        node: Module or class or function whose body is scanned.
        trail: Qualified-name prefix.
        in_class: Whether ``node`` is a class body.

    Yields:
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
        function: Function definition.
        skip_receiver: Whether the first parameter is an implicit receiver.

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
    if skip_receiver and pairs and pairs[0][0].arg in Constants.receivers:
        return pairs[1:]
    return pairs


def _blocked_names(*, node: AST) -> set[str]:
    """List the names a statement binds in a way contracts cannot follow.

    Args:
        node: Any node of a function body.

    Returns:
        Names bound by ``global``/``nonlocal``, imports, nested definitions,
        exception handlers and annotated assignments.

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
    if (
        isinstance(node, AnnAssign)
        and isinstance(node.target, Name)
        and node.value is None
    ):
        return {node.target.id}
    return set()


def _plain_target(*, node: AST) -> str | None:
    """Name the variable a simple assignment or loop binds.

    Args:
        node: Any node of a function body.

    Returns:
        The name for ``x = ...`` and ``for x in ...``, else ``None``.

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
    return None


def walk_classes(
    *,
    node: AST,
    trail: tuple[str, ...],
) -> Iterator[tuple[str, ClassDef]]:
    """List every class with its qualified name.

    Args:
        node: Module, class or function whose body is scanned.
        trail: Qualified-name prefix.

    Yields:
        ``(qualified name, definition)``.

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
        module: Parsed module.

    Returns:
        Stores and deletes by attribute name.

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
) -> tuple[dict[str, list[Assign]], set[str]]:
    """Find the plain writes a method makes to its instance's attributes.

    Args:
        method: Method definition.
        receiver: Name of the instance parameter.

    Returns:
        The ``self.name = value`` assignments by attribute, and the
        attributes touched in any other way (augmented, unpacked, deleted) —
        all of them when the receiver is rebound.

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
    bad: set[str] = set()
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
        module: Parsed module.

    Returns:
        Names of the top-level classes that are not generic.

    """
    body: list[stmt] = list(getattr(module, "body", []))
    typevars: set[str] = {
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
            builder: The builder, to recognise operand nodes.
            scope: Scope the expression is evaluated in.

        """
        self._builder: ContractBuilder = builder
        self._scope: _Scope = scope
        self.parts: list[tuple[str, str]] = []
        self.fixed: dict[str, str] = {}
        self._bound: set[str] = set()

    def convert(self, *, value: expr) -> expr | None:
        """Copy an expression, replacing operands by placeholder names.

        Args:
            value: The expression.

        Returns:
            The template, or ``None`` when the expression contains something
            the syntax typer cannot read (lambdas, comprehensions, unknown
            calls or names).

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
            value: The expression.

        Returns:
            ``(True, result)`` when the expression was handled here (the
            result is ``None`` for an unknown name), else ``(False, None)``.

        """
        if isinstance(value, Name) and value.id in self._bound:
            return True, value
        path: str | None = self._builder.operand(
            value=value,
            scope=self._scope,
        )
        if path is not None:
            placeholder: str = f"__{len(self.parts)}"
            self.parts.append((placeholder, path))
            return True, Name(id=placeholder, ctx=Load())
        if isinstance(value, Name):
            known: str | None = self._scope.env.get(value.id)
            if known is None:
                return True, None
            self.fixed[value.id] = known
            return True, value
        return isinstance(value, Constants.leaves), value

    def _comprehension(self, *, value: comprehension) -> comprehension | None:
        """Copy one ``for … in … if …`` clause of a comprehension.

        The loop target is a name bound inside the expression, so it stays as
        written and is not an operand.

        Args:
            value: The clause.

        Returns:
            The copy, or ``None`` for an async clause or an unreadable part.

        """
        if value.is_async or not isinstance(value.target, Name):
            return None
        source: expr | None = self.convert(value=value.iter)
        self._bound.add(value.target.id)
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
            value: The expression.

        Returns:
            The copy, or ``None`` when some child cannot be converted.

        """
        outer: set[str] = set(self._bound)
        copied: expr = copy(x=value)
        for field_name, field_value in sorted(
            iter_fields(node=value),
            key=lambda pair: pair[0] != "generators",
        ):
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
            value: A field of an expression node.

        Returns:
            ``True`` for names, numbers and the operator and context markers;
            ``False`` for any other syntax node.

        """
        return not isinstance(value, AST) or isinstance(
            value,
            Constants.markers,
        )

    def _field(self, *, value: FieldValue) -> FieldValue | None:
        """Convert one field of an expression node.

        Args:
            value: An expression, a list of nodes, or a plain value.

        Returns:
            The converted field; plain values are returned as they are and
            ``None`` means the field cannot be converted.

        """
        if isinstance(value, expr):
            return self.convert(value=value)
        if not isinstance(value, list):
            return value if self._plain(value=value) else None
        items: list[AST | None] = []
        for item in value:
            converted: AST | None
            if isinstance(item, expr):
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
            module: Parsed module.
            escaped: Names read as values, whose callers are unknown.
            library: Resolver over typeshed, to type calls into the standard
                library; ``None`` types none.

        """
        self._library: Resolver | None = library
        self._module: CommentedModule = module
        self._escaped: frozenset[str] = escaped
        self._counts: dict[str, int] = binding_counts(module=module)
        self._bindings: CallBindings = CallBindings(
            module=module,
            counts=self._counts,
        )
        self._constants: dict[str, str] = module_constants(
            module=module,
            counts=self._counts,
        )
        self._graph: ContractGraph = ContractGraph()
        self._opaque: set[str] = set()
        self._why: dict[str, str] = {}
        self._kinds: dict[str, str] = {}
        self._ids: dict[int, str] = {}
        self._scopes: dict[int, _Scope] = {}
        self._params: dict[str, list[str]] = {}
        self._by_name: dict[str, str] = {}
        self._coroutines: set[str] = set()
        self._name_path: dict[int, str] = {}
        self._methods: MethodIndex = MethodIndex(
            module=module,
            counts=self._counts,
        )
        self._top_classes: frozenset[str] = _plain_classes(module=module)
        self._variables: dict[str, Assign] = {}
        self._attribute_writes: dict[str, Assign] = {}
        self._risky: set[str] = set()

    def build(self) -> Built:
        """Build the graph.

        Returns:
            The graph, the opaque nodes and the reportable node kinds.

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
            path: Node path.
            why: What made the evidence incomplete.

        """
        self._opaque.add(path)
        _ = self._why.setdefault(path, why)

    def _block_all(self, *, paths: Iterable[str], why: str) -> None:
        """Mark several nodes as having incomplete evidence.

        Args:
            paths: Node paths.
            why: What made the evidence incomplete.

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
            qual: Qualified name.
            function: Function definition.
            in_class: Whether it is defined directly in a class.

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
            path: Node path.
            source: Annotation text.

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
            function: Function definition.
            qual: Qualified name.
            scope: Scope extended in place.

        """
        stores: Counter[str] = Counter()
        blocked: set[str] = {
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
            target: str | None = _plain_target(node=node)
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
            qual: Qualified name.
            function: Function definition.

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
        env: dict[str, str],
        scope: _Scope,
        qual: str,
    ) -> dict[str, str]:
        """Walk statements in order, threading the narrowed environment.

        Args:
            stmts: Statements of one block.
            env: Current path of each name.
            scope: Function scope.
            qual: Qualified name of the function.

        Returns:
            The environment after the block.

        """
        for item in stmts:
            env = self._statement(item=item, env=env, scope=scope, qual=qual)
        return env

    def _statement(
        self,
        *,
        item: stmt,
        env: dict[str, str],
        scope: _Scope,
        qual: str,
    ) -> dict[str, str]:
        """Register the names of one statement and walk its blocks.

        Args:
            item: The statement.
            env: Current path of each name.
            scope: Function scope.
            qual: Qualified name of the function.

        Returns:
            The environment after the statement.

        """
        if isinstance(item, If):
            return self._branch(item=item, env=env, scope=scope, qual=qual)
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
                            env=env,
                            scope=scope,
                            qual=qual,
                        )
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
        env: dict[str, str],
        scope: _Scope,
        qual: str,
    ) -> dict[str, str]:
        """Narrow a name on each arm of an ``if`` and after it.

        Args:
            item: The ``if`` statement.
            env: Current path of each name.
            scope: Function scope.
            qual: Qualified name of the function.

        Returns:
            The environment after the ``if``: an arm's narrowing survives it
            when the other arm cannot fall through.

        """
        self._register(node=item.test, env=env, scope=scope)
        arms: Arms | None = read_test(test=item.test, counts=self._counts)
        true_env: dict[str, str] = dict(env)
        false_env: dict[str, str] = dict(env)
        if arms is not None and arms.name in env:
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
        after_true: dict[str, str] = self._statements(
            stmts=item.body,
            env=true_env,
            scope=scope,
            qual=qual,
        )
        after_false: dict[str, str] = self._statements(
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
            base: Path the name had before the test.
            line: Line of the test, to keep paths unique.
            tag: ``"t"`` or ``"f"`` for the arm.
            constraint: What the arm establishes (``!None``, a class, ...).

        Returns:
            The new node's path.

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

    def _register(
        self,
        *,
        node: AST | None,
        env: dict[str, str],
        scope: _Scope,
    ) -> None:
        """Record the narrowed path of every name an expression reads.

        Args:
            node: AST node to walk, or ``None``.
            env: Current path of each name.
            scope: Function scope.

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
            unique: Functions with unambiguous qualified names.

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
            receiver: str | None = receiver_of(function=function)
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
        members: dict[str, str],
    ) -> None:
        """Let each method read the class's attributes through its receiver.

        A method that rebinds its receiver (``self = other``) reads another
        object's attributes afterwards, so it gets none.

        Args:
            methods: The class's methods with their receiver names.
            members: Node path by attribute name.

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
            owner: Qualified name of the class.
            _cls: The class definition.
            methods: Its methods with their receiver parameter names.
            index: Method facts of the module.
            stores: Attribute writes in the module by name.

        """
        writes: dict[str, list[tuple[Function, Assign]]] = {}
        bad: set[str] = set()
        for function, receiver in methods:
            found, touched = _own_writes(method=function, receiver=receiver)
            bad |= touched
            for name, assigns in found.items():
                writes.setdefault(name, []).extend(
                    (function, item) for item in assigns
                )
        inherited: set[str] = index.inherited_names(_cls=_cls)
        members: dict[str, str] = {}
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
            qual: Qualified name.
            function: Function definition.

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
            elif isinstance(node, For):
                self._loop(node=node, qual=qual, scope=scope)
        if can_fall_off(body=function.body):
            self._seed_type(
                target=ret,
                type_text="None",
                origin=Origin.syntax,
                why="falls off the end",
            )

    def _library_return(self, *, call: Call) -> str | None:
        """Type a call into the standard library from its stub.

        Only a function with one definition and a plain return type counts,
        so the result does not depend on the arguments.

        Args:
            call: The call expression.

        Returns:
            The return type, or ``None`` when it is not certain.

        """
        if self._library is None:
            return None
        key: str | None = callee_name(
            module=self._module,
            counts=self._counts,
            call=call,
        )
        found: Resolved | None = (
            None if key is None else self._library.resolve(qualified=key)
        )
        return None if found is None else function_return(resolved=found)

    def _proved(self, *, value: expr, scope: _Scope) -> bool:
        """Tell whether an expression's type is known without any derivation.

        Args:
            value: The expression.
            scope: Scope the expression is evaluated in.

        Returns:
            ``True`` for a node or an expression the syntax typer proves.

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
            value: The returned expression, or ``None`` for a bare return.
            ret: The function's return node path.
            scope: Function scope.
            calibrated: Whether every returned value is boolean by syntax.

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
            function: A function named like a protocol method.
            ret: Its return node path.

        """
        declared: str | None = protocol_result_for(
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
            node: The annotated assignment.
            qual: Qualified name of the function.
            scope: Function scope.

        """
        if not isinstance(node.target, Name):
            return
        path: str | None = scope.names.get(node.target.id)
        if path is not None and path.startswith(f"{qual}."):
            self._declared(path=path, source=unparse(ast_obj=node.annotation))

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
            node: The assignment.
            function: The enclosing function.
            qual: Qualified name of the function.
            scope: Function scope.

        """
        if len(node.targets) != 1 or not isinstance(node.targets[0], Name):
            return
        name: str = node.targets[0].id
        path: str | None = scope.names.get(name)
        if path is None or not path.startswith(f"{qual}."):
            return
        self._variables[path] = node
        literal: str | None = literal_kind(value=node.value)
        if literal is not None:
            self._literal_container(
                node=node,
                function=function,
                path=path,
                kind=literal,
                scope=scope,
            )
            return
        kind: str | None = empty_kind(value=node.value, counts=self._counts)
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
            node: The assignment.
            function: The enclosing function.
            path: The variable's node path.
            kind: ``"list"``, ``"set"`` or ``"dict"``.
            scope: Function scope.

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
        proven: str | None = expression_type(
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
            function: The enclosing function.
            name: The local's name.
            path: Its node path.
            kind: ``"list"`` or ``"set"``.
            scope: Function scope.

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
            node: The loop.
            qual: Qualified name of the function.
            scope: Function scope.

        """
        if not isinstance(node.target, Name):
            return
        path: str | None = scope.names.get(node.target.id)
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
        proven: str | None = expression_type(
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

    def _calls(self, *, unique: list[tuple[str, Function, bool]]) -> None:
        """Add argument contracts and evidence for every call.

        Args:
            unique: Functions with unambiguous qualified names.

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
            callee: str | None = (
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
            bound: The trusted binding.
            callee: Qualified name of the called function.
            scope: Scope of the call.

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
            value: Expression.
            scope: Scope the expression is evaluated in.

        Returns:
            ``("node", path, relation)`` for a variable, a parameter, an
            attribute of the instance, a call to a function of the module
            (``("seed", class, assigns)`` for a constructor) or an item of
            one of those; ``None`` for anything else.

        """
        if isinstance(value, Name) and value.id in scope.names:
            return (
                "node",
                self._name_path.get(id(value), scope.names[value.id]),
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
            value: Expression.
            scope: Scope the expression is evaluated in.
            shapes: Whether a tuple-literal shape may be the type; call-site
                arguments say too little about it.

        Returns:
            ``("node", path, relation)`` or ``("seed", type, relation)``, or
            ``None`` when nothing sound can be said.

        """
        found: tuple[str, str, Relation] | None = self._node_source(
            value=value,
            scope=scope,
        )
        if found is not None:
            return found
        proven: str | None = expression_type(
            node=value,
            counts=self._counts,
            env=scope.env,
        )
        if proven is None and isinstance(value, Call):
            proven = self._library_return(call=value)
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
            call: The call expression.

        Returns:
            The callee's return node, the class name for a constructor call,
            or ``None`` for anything else (coroutines, unbound callees).

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
        callee: str | None = self._ids.get(id(bound.signature.declaration))
        if callee is None or callee in self._coroutines:
            return None
        owner, _, method = callee.rpartition(".")
        if method in Constants.constructors:
            if owner in self._top_classes and self._counts.get(owner) == 1:
                return "seed", owner, Relation.assigns
            return None
        return "node", f"{callee}->", Relation.call_result

    def _operand(self, *, value: expr, scope: _Scope) -> str | None:
        """Name the node that holds the value of an operand expression.

        Args:
            value: A sub-expression.
            scope: Scope the expression is evaluated in.

        Returns:
            The node path for a variable, a parameter, an attribute of the
            instance, a call to a function of the module or an item of one
            of those; ``None`` when the expression is not a node.

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

    def operand(self, *, value: expr, scope: _Scope) -> str | None:
        """Name the node that holds the value of an operand expression.

        Args:
            value: A sub-expression.
            scope: Scope the expression is evaluated in.

        Returns:
            The node path, or ``None`` when the expression is not a node.

        """
        return self._operand(value=value, scope=scope)

    def is_builtin(self, *, name: str) -> bool:
        """Tell whether a name is a builtin the module does not rebind.

        Args:
            name: A name used as a callee.

        Returns:
            ``True`` for an unshadowed builtin.

        """
        return hasattr(builtins, name) and self._counts.get(name, 0) == 0

    def _hidden(self, *, value: expr, scope: _Scope) -> str:
        """Make the node that stands for an expression's value.

        Args:
            value: The expression.
            scope: Scope the expression is evaluated in.

        Returns:
            Its path, unique by position.

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
            value: The expression.
            scope: Scope the expression is evaluated in.
            shapes: Whether a container literal may be derived.

        Returns:
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
            value: The expression flowing in.
            target: Node path receiving it.
            scope: Scope of the expression.
            origin: Origin recorded for a syntax-proven seed.
            relation: Relation to use when the value is another node.

        """
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
            value: The expression.
            target: Node path.
            scope: Scope of the expression.
            origin: Origin to record.

        """
        proven: str | None = expression_type(
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
            target: Node path.
            type_text: The type.
            origin: What supports it.
            why: Explanation recorded with the candidate.

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
            source: Source node path.
            target: Target node path.
            relation: What the contract states.
            why: Explanation recorded with the contract.

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
        module: Parsed module.
        escaped: Names read as values, whose callers are unknown.
        library: Resolver over typeshed, or ``None``.

    Returns:
        The graph with its opaque nodes and node kinds.

    """
    return ContractBuilder(
        module=module,
        escaped=escaped,
        library=library,
    ).build()
