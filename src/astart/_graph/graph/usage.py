"""Usage graph primitives and indexed semantic graph builder."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    ExceptHandler,
    Expr,
    For,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Lambda,
    List,
    Match,
    Name,
    NamedExpr,
    Return,
    Subscript,
    Try,
    Tuple,
    UnaryOp,
    With,
    alias,
    arg,
    arguments,
    iter_child_nodes,
    keyword,
    match_case,
    withitem,
)
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Self

from astart._graph.graph.document import read_node_span

if TYPE_CHECKING:
    from astart._graph.graph.document import AstDocument
    from astart._graph.graph.positions import SourceSpan


class ScopeKind(StrEnum):
    """Kinds of lexical scopes represented by the usage graph.

    Attributes:
        CLASS: Class associated with this instance.
        COMPREHENSION: Comprehension associated with this instance.
        FUNCTION: Function associated with this instance.
        LAMBDA: Lambda associated with this instance.
        MODULE: Module associated with this instance.

    """

    CLASS = "class"
    COMPREHENSION = "comprehension"
    FUNCTION = "function"
    LAMBDA = "lambda"
    MODULE = "module"


class SymbolKind(StrEnum):
    """Supported symbol kinds.

    Attributes:
        ATTRIBUTE: Attribute associated with this instance.
        CLASS: Class associated with this instance.
        EXCEPTION: Exception associated with this instance.
        FUNCTION: Function associated with this instance.
        IMPORT: Import associated with this instance.
        PARAMETER: Parameter associated with this instance.
        RETURN: Return associated with this instance.
        VARIABLE: Variable associated with this instance.

    """

    ATTRIBUTE = "attribute"
    CLASS = "class"
    EXCEPTION = "exception"
    FUNCTION = "function"
    IMPORT = "import"
    PARAMETER = "parameter"
    RETURN = "return"
    VARIABLE = "variable"


class UsageKind(StrEnum):
    """Supported observable usage kinds.

    Attributes:
        ARGUMENT: Argument associated with this instance.
        ASSIGNMENT: Assignment associated with this instance.
        AUGMENTED_ASSIGNMENT: Augmented assignment associated with this
            instance.
        BOOL_OPERATOR: Bool operator associated with this instance.
        CALL: Call associated with this instance.
        CLASS_DECORATOR: Class decorator associated with this instance.
        COMPARISON: Comparison associated with this instance.
        CONDITION: Condition associated with this instance.
        CONTEXT_MANAGER: Context manager associated with this instance.
        DECORATOR: Decorator associated with this instance.
        IMPORT: Import associated with this instance.
        LITERAL: Literal associated with this instance.
        MATCH_CASE: Match case associated with this instance.
        OPERATOR: Operator associated with this instance.
        RETURN: Return associated with this instance.
        SUBSCRIPT: Subscript associated with this instance.
        TRY_EXCEPT: Try except associated with this instance.
        UNARY_OPERATOR: Unary operator associated with this instance.
        WALRUS: Walrus associated with this instance.

    """

    ARGUMENT = "argument"
    ASSIGNMENT = "assignment"
    AUGMENTED_ASSIGNMENT = "augmented_assignment"
    BOOL_OPERATOR = "bool_operator"
    CALL = "call"
    CLASS_DECORATOR = "class_decorator"
    COMPARISON = "comparison"
    CONDITION = "condition"
    CONTEXT_MANAGER = "context_manager"
    DECORATOR = "decorator"
    IMPORT = "import"
    LITERAL = "literal"
    MATCH_CASE = "match_case"
    OPERATOR = "operator"
    RETURN = "return"
    SUBSCRIPT = "subscript"
    TRY_EXCEPT = "try_except"
    UNARY_OPERATOR = "unary_operator"
    WALRUS = "walrus"


class EdgeKind(StrEnum):
    """Semantic edge relations in the usage graph.

    Attributes:
        ARGUMENT_OF: Argument of associated with this instance.
        ASSIGNED_FROM: Assigned from associated with this instance.
        BINDS: Binds associated with this instance.
        CALLS: Calls associated with this instance.
        CONTAINS: Contains associated with this instance.
        DECORATES: Decorates associated with this instance.
        FLOWS_TO: Flows to associated with this instance.
        RAISES: Raises associated with this instance.
        READS: Reads associated with this instance.
        RETURNS: Returns associated with this instance.
        WRITES: Writes associated with this instance.

    """

    ARGUMENT_OF = "argument_of"
    ASSIGNED_FROM = "assigned_from"
    BINDS = "binds"
    CALLS = "calls"
    CONTAINS = "contains"
    DECORATES = "decorates"
    FLOWS_TO = "flows_to"
    RAISES = "raises"
    READS = "reads"
    RETURNS = "returns"
    WRITES = "writes"


@dataclass(frozen=True, slots=True)
class Scope:
    """A lexical scope in the source file.

    Attributes:
        kind: Kind retained as ScopeKind by this instance.
        name: Identifier used to refer to the name.
        node_id: Node id retained as int by this instance.
        parent_id: Parent id retained as int | None by this instance.
        scope_id: Scope id retained as int by this instance.
        span: Span retained as SourceSpan | None by this instance.

    """

    scope_id: int
    kind: ScopeKind
    name: str
    parent_id: int | None
    node_id: int
    span: SourceSpan | None = None


@dataclass(frozen=True, slots=True)
class Symbol:
    """A named entity in a scope.

    Attributes:
        kind: Kind retained as SymbolKind by this instance.
        name: Identifier used to refer to the name.
        node_id: Node id retained as int by this instance.
        scope_id: Scope id retained as int by this instance.
        span: Span retained as SourceSpan | None by this instance.

    """

    name: str
    kind: SymbolKind
    scope_id: int
    node_id: int
    span: SourceSpan | None = None


@dataclass(frozen=True, slots=True)
class UsageEvent:
    """An observable operation involving a symbol or expression.

    Attributes:
        kind: Kind retained as UsageKind by this instance.
        name: Identifier used to refer to the name.
        node_id: Node id retained as int by this instance.
        operation: Operation retained as str | None by this instance.
        scope_id: Scope id retained as int by this instance.
        span: Span retained as SourceSpan | None by this instance.

    """

    kind: UsageKind
    node_id: int
    scope_id: int
    name: str | None = None
    operation: str | None = None
    span: SourceSpan | None = None


@dataclass(frozen=True, slots=True)
class UsageEdge:
    """Directed graph edge between usage entities.

    Attributes:
        relation: Relation retained as EdgeKind by this instance.
        source_node_id: Source node id retained as int by this instance.
        target_node_id: Target node id retained as int by this instance.

    """

    source_node_id: int
    target_node_id: int
    relation: EdgeKind


@dataclass(frozen=True, slots=True)
class CallSite:
    """Indexed call site information.

    Attributes:
        keyword_names: Keyword names retained as tuple[str, ...] by this
            instance.
        keyword_value_ids: Keyword value ids retained as tuple[int, ...] by
            this instance.
        node_id: Node id retained as int by this instance.
        positional_argument_ids: Positional argument ids retained as tuple[int,
            ...] by this instance.
        scope_id: Scope id retained as int by this instance.
        target: AST target associated with this record.

    """

    node_id: int
    scope_id: int
    target: str | None
    positional_argument_ids: tuple[int, ...]
    keyword_names: tuple[str, ...]
    keyword_value_ids: tuple[int, ...]


@dataclass(slots=True)
class UsageGraph:
    """Indexed usage graph for fast semantic lookup.

    Attributes:
        call_sites: Call sites retained as list[CallSite] by this instance.
        edges: Edges retained as list[UsageEdge] by this instance.
        events: Events retained as list[UsageEvent] by this instance.
        scopes: Scopes retained as list[Scope] by this instance.
        symbols: Symbols retained as list[Symbol] by this instance.

    """

    scopes: list[Scope] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    events: list[UsageEvent] = field(default_factory=list)
    edges: list[UsageEdge] = field(default_factory=list)
    call_sites: list[CallSite] = field(default_factory=list)
    _scopes_by_id: dict[int, Scope] = field(default_factory=dict)
    _symbols_by_name: dict[str, list[Symbol]] = field(default_factory=dict)
    _symbols_by_scope: dict[int, list[Symbol]] = field(default_factory=dict)
    _events_by_kind: dict[UsageKind, list[UsageEvent]] = field(
        default_factory=dict,
    )
    _events_by_node_id: dict[int, list[UsageEvent]] = field(
        default_factory=dict,
    )
    _edges_by_source: dict[int, list[UsageEdge]] = field(
        default_factory=dict,
    )
    _edges_by_target: dict[int, list[UsageEdge]] = field(
        default_factory=dict,
    )
    _calls_by_target: dict[str, list[CallSite]] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> Self:
        """Create an empty usage graph.

        Returns:
            Self produced by this operation.

        """
        return cls()

    def add_scope(self, *, scope: Scope) -> None:
        """Add a scope and update indexes.

        Args:
            scope: The scope examined while add a scope and update indexes.

        """
        self.scopes.append(scope)
        self._scopes_by_id[scope.scope_id] = scope

    def add_symbol(self, *, symbol: Symbol) -> None:
        """Add a symbol and update name/scope indexes.

        Args:
            symbol: Symbol supplied as Symbol for this operation.

        """
        self.symbols.append(symbol)
        self._symbols_by_name.setdefault(symbol.name, []).append(symbol)
        self._symbols_by_scope.setdefault(symbol.scope_id, []).append(symbol)

    def add_event(self, *, event: UsageEvent) -> None:
        """Add an event and update kind/node indexes.

        Args:
            event: Event supplied as UsageEvent for this operation.

        """
        self.events.append(event)
        self._events_by_kind.setdefault(event.kind, []).append(event)
        self._events_by_node_id.setdefault(event.node_id, []).append(event)

    def add_edge(self, *, edge: UsageEdge) -> None:
        """Add a graph edge and update adjacency indexes.

        Args:
            edge: Edge supplied as UsageEdge for this operation.

        """
        self.edges.append(edge)
        self._edges_by_source.setdefault(edge.source_node_id, []).append(edge)
        self._edges_by_target.setdefault(edge.target_node_id, []).append(edge)

    def add_call_site(self, *, call_site: CallSite) -> None:
        """Add an indexed call site.

        Args:
            call_site: Call site supplied as CallSite for this operation.

        """
        self.call_sites.append(call_site)
        if call_site.target is not None:
            self._calls_by_target.setdefault(call_site.target, []).append(
                call_site,
            )

    def scope_by_id(self, *, scope_id: int) -> Scope | None:
        """Return a scope by identifier.

        Args:
            scope_id: Scope id supplied as int for this operation.

        Returns:
            Scope | None produced by this operation.

        """
        return self._scopes_by_id.get(scope_id)

    def symbols_named(self, *, name: str) -> tuple[Symbol, ...]:
        """Return symbols matching a name.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            tuple[Symbol, ...] produced by this operation.

        """
        return tuple(self._symbols_by_name.get(name, ()))

    def symbols_in_scope(self, *, scope_id: int) -> tuple[Symbol, ...]:
        """Return symbols declared in ``scope_id``.

        Args:
            scope_id: Scope id supplied as int for this operation.

        Returns:
            tuple[Symbol, ...] produced by this operation.

        """
        return tuple(self._symbols_by_scope.get(scope_id, ()))

    def events_of_kind(self, *, kind: UsageKind) -> tuple[UsageEvent, ...]:
        """Return events matching a usage kind.

        Args:
            kind: Kind supplied as UsageKind for this operation.

        Returns:
            tuple[UsageEvent, ...] produced by this operation.

        """
        return tuple(self._events_by_kind.get(kind, ()))

    def events_for_node(self, *, node_id: int) -> tuple[UsageEvent, ...]:
        """Return events attached to one AST node identity.

        Args:
            node_id: Node id supplied as int for this operation.

        Returns:
            tuple[UsageEvent, ...] produced by this operation.

        """
        return tuple(self._events_by_node_id.get(node_id, ()))

    def outgoing_edges(self, *, node_id: int) -> tuple[UsageEdge, ...]:
        """Return outgoing edges for ``node_id``.

        Args:
            node_id: Node id supplied as int for this operation.

        Returns:
            tuple[UsageEdge, ...] produced by this operation.

        """
        return tuple(self._edges_by_source.get(node_id, ()))

    def incoming_edges(self, *, node_id: int) -> tuple[UsageEdge, ...]:
        """Return incoming edges for ``node_id``.

        Args:
            node_id: Node id supplied as int for this operation.

        Returns:
            tuple[UsageEdge, ...] produced by this operation.

        """
        return tuple(self._edges_by_target.get(node_id, ()))

    def calls_named(self, *, name: str) -> tuple[CallSite, ...]:
        """Return call sites whose target has ``name``.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            tuple[CallSite, ...] produced by this operation.

        """
        return tuple(self._calls_by_target.get(name, ()))

    def reachable(
        self,
        *,
        start_node_id: int,
        direction: EdgeKind | None = None,
        max_depth: int = 64,
    ) -> tuple[int, ...]:
        """Return nodes reachable by outgoing graph edges.

        Args:
            direction: Direction supplied as EdgeKind | None for this
                operation.
            max_depth: Max depth supplied as int for this operation.
            start_node_id: Start node id supplied as int for this operation.

        Returns:
            tuple[int, ...] produced by this operation.

        """
        visited: set[int] = {start_node_id}
        frontier: list[tuple[int, int]] = [(start_node_id, 0)]
        ordered: list[int] = []
        while frontier:
            node_id: int
            depth: int
            node_id, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            edge: UsageEdge
            for edge in self.outgoing_edges(node_id=node_id):
                if direction is not None and edge.relation is not direction:
                    continue
                if edge.target_node_id in visited:
                    continue
                visited.add(edge.target_node_id)
                ordered.append(edge.target_node_id)
                frontier.append((edge.target_node_id, depth + 1))
        return tuple(ordered)


def build_usage_graph(*, document: AstDocument) -> UsageGraph:
    """Build a usage graph by walking the document AST once.

    Args:
        document: Document supplied as AstDocument for this operation.

    Returns:
        UsageGraph produced by this operation.

    """
    builder: _UsageGraphBuilder = _UsageGraphBuilder(document=document)
    return builder.build()


@dataclass(slots=True)
class _UsageGraphBuilder:
    """Stateful graph builder with lexical scope tracking.

    Attributes:
        document: Document retained as AstDocument by this instance.
        graph: Graph retained as UsageGraph by this instance.

    """

    document: AstDocument
    graph: UsageGraph = field(default_factory=UsageGraph.empty)

    def build(self) -> UsageGraph:
        """Build and return the usage graph.

        Returns:
            UsageGraph produced by this operation.

        """
        module_scope: Scope = Scope(
            scope_id=id(self.document.tree),
            kind=ScopeKind.MODULE,
            name="<module>",
            parent_id=None,
            node_id=id(self.document.tree),
            span=None,
        )
        self.graph.add_scope(scope=module_scope)
        self._visit_body(
            body=tuple(self.document.tree.body),
            scope=module_scope,
        )
        return self.graph

    def _visit_body(self, *, body: tuple[AST, ...], scope: Scope) -> None:
        """Visit a sequence of statements in ``scope``.

        Args:
            body: Body supplied as tuple[AST, ...] for this operation.
            scope: The scope examined while visit a sequence of statements in
                ``scope``.

        """
        statement: AST
        for statement in body:
            self._visit_statement(node=statement, scope=scope)

    def _visit_statement(self, *, node: AST, scope: Scope) -> None:
        """Visit one statement-like AST node.

        Args:
            node: The node examined while visit one statement-like AST node.
            scope: The scope examined while visit one statement-like AST node.

        """
        if self._visit_definition_statement(node=node, scope=scope):
            return
        if self._visit_binding_statement(node=node, scope=scope):
            return
        if self._visit_control_statement(node=node, scope=scope):
            return
        if isinstance(node, Return):
            self._visit_return(node=node, scope=scope)
        elif isinstance(node, Expr):
            self._visit_expression(node=node.value, scope=scope)
        else:
            self._visit_unknown(node=node, scope=scope)

    def _visit_definition_statement(self, *, node: AST, scope: Scope) -> bool:
        """Visit class/function definitions when matched.

        Args:
            node: The node examined while visit class/function definitions when
                matched.
            scope: The scope examined while visit class/function definitions
                when matched.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(node, ClassDef):
            self._visit_class(node=node, scope=scope)
            return True
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            self._visit_function(node=node, scope=scope)
            return True
        return False

    def _visit_binding_statement(self, *, node: AST, scope: Scope) -> bool:
        """Visit assignments and imports when matched.

        Args:
            node: The node examined while visit assignments and imports when
                matched.
            scope: The scope examined while visit assignments and imports when
                matched.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(node, (Assign, AnnAssign, AugAssign)):
            self._visit_assignment(node=node, scope=scope)
            return True
        if isinstance(node, Import):
            self._visit_import(node=node, scope=scope)
            return True
        if isinstance(node, ImportFrom):
            self._visit_import_from(node=node, scope=scope)
            return True
        return False

    def _visit_control_statement(self, *, node: AST, scope: Scope) -> bool:
        """Visit control-flow statements when matched.

        Args:
            node: The node examined while visit control-flow statements when
                matched.
            scope: The scope examined while visit control-flow statements when
                matched.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(node, If):
            self._visit_if(node=node, scope=scope)
            return True
        if isinstance(node, Match):
            self._visit_match(node=node, scope=scope)
            return True
        if isinstance(node, Try):
            self._visit_try(node=node, scope=scope)
            return True
        if isinstance(node, With):
            self._visit_with(node=node, scope=scope)
            return True
        if isinstance(node, For):
            self._visit_for(node=node, scope=scope)
            return True
        return False

    def _visit_class(self, *, node: ClassDef, scope: Scope) -> None:
        """Visit a class definition.

        Args:
            node: The node examined while visit a class definition.
            scope: The scope examined while visit a class definition.

        """
        self.graph.add_symbol(
            symbol=Symbol(
                name=node.name,
                kind=SymbolKind.CLASS,
                scope_id=scope.scope_id,
                node_id=id(node),
                span=_span_of(node=node),
            ),
        )
        self._add_decorator_events(
            decorators=tuple(node.decorator_list),
            target=node,
            scope=scope,
            kind=UsageKind.CLASS_DECORATOR,
        )
        class_scope: Scope = Scope(
            scope_id=id(node),
            kind=ScopeKind.CLASS,
            name=node.name,
            parent_id=scope.scope_id,
            node_id=id(node),
            span=_span_of(node=node),
        )
        self.graph.add_scope(scope=class_scope)
        self._visit_body(body=tuple(node.body), scope=class_scope)

    def _visit_function(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        scope: Scope,
    ) -> None:
        """Visit a function or async function definition.

        Args:
            node: The node examined while visit a function or async function
                definition.
            scope: The scope examined while visit a function or async function
                definition.

        """
        self.graph.add_symbol(
            symbol=Symbol(
                name=node.name,
                kind=SymbolKind.FUNCTION,
                scope_id=scope.scope_id,
                node_id=id(node),
                span=_span_of(node=node),
            ),
        )
        self._add_decorator_events(
            decorators=tuple(node.decorator_list),
            target=node,
            scope=scope,
            kind=UsageKind.DECORATOR,
        )
        function_scope: Scope = Scope(
            scope_id=id(node),
            kind=ScopeKind.FUNCTION,
            name=node.name,
            parent_id=scope.scope_id,
            node_id=id(node),
            span=_span_of(node=node),
        )
        self.graph.add_scope(scope=function_scope)
        self._visit_arguments(arguments_node=node.args, scope=function_scope)
        if node.returns is not None:
            self.graph.add_event(
                event=UsageEvent(
                    kind=UsageKind.RETURN,
                    node_id=id(node),
                    scope_id=scope.scope_id,
                    name=node.name,
                    operation="annotation",
                    span=_span_of(node=node),
                ),
            )
        self._visit_body(body=tuple(node.body), scope=function_scope)

    def _visit_arguments(
        self,
        *,
        arguments_node: arguments,
        scope: Scope,
    ) -> None:
        """Visit function argument declarations.

        Args:
            arguments_node: Arguments node supplied as arguments for this
                operation.
            scope: The scope examined while visit function argument
                declarations.

        """
        parameters: tuple[arg, ...] = (
            *arguments_node.posonlyargs,
            *arguments_node.args,
            *arguments_node.kwonlyargs,
        )
        parameter: arg
        for parameter in parameters:
            self.graph.add_symbol(
                symbol=Symbol(
                    name=parameter.arg,
                    kind=SymbolKind.PARAMETER,
                    scope_id=scope.scope_id,
                    node_id=id(parameter),
                    span=_span_of(node=parameter),
                ),
            )
            if parameter.annotation is not None:
                self.graph.add_event(
                    event=UsageEvent(
                        kind=UsageKind.ARGUMENT,
                        node_id=id(parameter),
                        scope_id=scope.scope_id,
                        name=parameter.arg,
                        operation="annotation",
                        span=_span_of(node=parameter),
                    ),
                )
        if arguments_node.vararg is not None:
            self._visit_vararg(parameter=arguments_node.vararg, scope=scope)
        if arguments_node.kwarg is not None:
            self._visit_vararg(parameter=arguments_node.kwarg, scope=scope)

    def _visit_vararg(self, *, parameter: arg, scope: Scope) -> None:
        """Add a vararg or kwarg parameter symbol.

        Args:
            parameter: Parameter supplied as arg for this operation.
            scope: The scope examined while add a vararg or kwarg parameter
                symbol.

        """
        self.graph.add_symbol(
            symbol=Symbol(
                name=parameter.arg,
                kind=SymbolKind.PARAMETER,
                scope_id=scope.scope_id,
                node_id=id(parameter),
                span=_span_of(node=parameter),
            ),
        )

    def _visit_assignment(
        self,
        *,
        node: Assign | AnnAssign | AugAssign,
        scope: Scope,
    ) -> None:
        """Visit assignment targets and values.

        Args:
            node: The node examined while visit assignment targets and values.
            scope: The scope examined while visit assignment targets and
                values.

        """
        targets: tuple[AST, ...]
        value: AST | None
        if isinstance(node, Assign):
            targets = tuple(node.targets)
            value = node.value
            kind: UsageKind = UsageKind.ASSIGNMENT
        elif isinstance(node, AnnAssign):
            targets = (node.target,)
            value = node.value
            kind = UsageKind.ASSIGNMENT
        else:
            targets = (node.target,)
            value = node.value
            kind = UsageKind.AUGMENTED_ASSIGNMENT
        self.graph.add_event(
            event=UsageEvent(
                kind=kind,
                node_id=id(node),
                scope_id=scope.scope_id,
                operation=type(node).__name__,
                span=_span_of(node=node),
            ),
        )
        target: AST
        for target in targets:
            self._add_target_symbol(target=target, scope=scope)
            self.graph.add_edge(
                edge=UsageEdge(
                    source_node_id=id(node),
                    target_node_id=id(target),
                    relation=EdgeKind.WRITES,
                ),
            )
        if value is not None:
            self._visit_expression(node=value, scope=scope)
            for target in targets:
                self.graph.add_edge(
                    edge=UsageEdge(
                        source_node_id=id(value),
                        target_node_id=id(target),
                        relation=EdgeKind.ASSIGNED_FROM,
                    ),
                )

    def _visit_import(self, *, node: Import, scope: Scope) -> None:
        """Visit an ``import`` statement.

        Args:
            node: The node examined while visit an ``import`` statement.
            scope: The scope examined while visit an ``import`` statement.

        """
        import_alias: alias
        for import_alias in node.names:
            name: str = (
                import_alias.asname or import_alias.name.split(sep=".")[0]
            )
            self._add_import_symbol(
                name=name,
                source_name=import_alias.name,
                node=node,
                scope=scope,
            )

    def _visit_import_from(self, *, node: ImportFrom, scope: Scope) -> None:
        """Visit a ``from ... import ...`` statement.

        Args:
            node: The node examined while visit a ``from ... import ...``
                statement.
            scope: The scope examined while visit a ``from ... import ...``
                statement.

        """
        module_name: str = node.module or ""
        import_alias: alias
        for import_alias in node.names:
            name: str = import_alias.asname or import_alias.name
            source_name: str = f"{module_name}.{import_alias.name}".strip(
                ".",
            )
            self._add_import_symbol(
                name=name,
                source_name=source_name,
                node=node,
                scope=scope,
            )

    def _visit_if(self, *, node: If, scope: Scope) -> None:
        """Visit an if statement with condition evidence.

        Args:
            node: The node examined while visit an if statement with condition
                evidence.
            scope: The scope examined while visit an if statement with
                condition evidence.

        """
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.CONDITION,
                node_id=id(node.test),
                scope_id=scope.scope_id,
                operation=_expr_name(node=node.test),
                span=_span_of(node=node.test),
            ),
        )
        self._visit_expression(node=node.test, scope=scope)
        self._visit_body(body=tuple(node.body), scope=scope)
        self._visit_body(body=tuple(node.orelse), scope=scope)

    def _visit_match(self, *, node: Match, scope: Scope) -> None:
        """Visit a structural pattern matching statement.

        Args:
            node: The node examined while visit a structural pattern matching
                statement.
            scope: The scope examined while visit a structural pattern matching
                statement.

        """
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.MATCH_CASE,
                node_id=id(node),
                scope_id=scope.scope_id,
                span=_span_of(node=node),
            ),
        )
        self._visit_expression(node=node.subject, scope=scope)
        case_node: match_case | None = None
        for case_node in node.cases:
            if case_node.guard is not None:
                self._visit_expression(node=case_node.guard, scope=scope)
            self._visit_body(body=tuple(case_node.body), scope=scope)

    def _visit_try(self, *, node: Try, scope: Scope) -> None:
        """Visit a try/except/finally statement.

        Args:
            node: The node examined while visit a try/except/finally statement.
            scope: The scope examined while visit a try/except/finally
                statement.

        """
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.TRY_EXCEPT,
                node_id=id(node),
                scope_id=scope.scope_id,
                span=_span_of(node=node),
            ),
        )
        self._visit_body(body=tuple(node.body), scope=scope)
        handler: ExceptHandler
        for handler in node.handlers:
            if handler.name is not None:
                self.graph.add_symbol(
                    symbol=Symbol(
                        name=handler.name,
                        kind=SymbolKind.EXCEPTION,
                        scope_id=scope.scope_id,
                        node_id=id(handler),
                        span=_span_of(node=handler),
                    ),
                )
            self._visit_body(body=tuple(handler.body), scope=scope)
        self._visit_body(body=tuple(node.orelse), scope=scope)
        self._visit_body(body=tuple(node.finalbody), scope=scope)

    def _visit_with(self, *, node: With, scope: Scope) -> None:
        """Visit a context-manager statement.

        Args:
            node: The node examined while visit a context-manager statement.
            scope: The scope examined while visit a context-manager statement.

        """
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.CONTEXT_MANAGER,
                node_id=id(node),
                scope_id=scope.scope_id,
                span=_span_of(node=node),
            ),
        )
        item: withitem | None = None
        for item in node.items:
            self._visit_expression(node=item.context_expr, scope=scope)
            if item.optional_vars is not None:
                self._add_target_symbol(target=item.optional_vars, scope=scope)
        self._visit_body(body=tuple(node.body), scope=scope)

    def _visit_for(self, *, node: For, scope: Scope) -> None:
        """Visit a for loop.

        Args:
            node: The node examined while visit a for loop.
            scope: The scope examined while visit a for loop.

        """
        self._add_target_symbol(target=node.target, scope=scope)
        self._visit_expression(node=node.iter, scope=scope)
        self._visit_body(body=tuple(node.body), scope=scope)
        self._visit_body(body=tuple(node.orelse), scope=scope)

    def _visit_return(self, *, node: Return, scope: Scope) -> None:
        """Visit a return statement.

        Args:
            node: The node examined while visit a return statement.
            scope: The scope examined while visit a return statement.

        """
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.RETURN,
                node_id=id(node),
                scope_id=scope.scope_id,
                span=_span_of(node=node),
            ),
        )
        if node.value is not None:
            self._visit_expression(node=node.value, scope=scope)
            self.graph.add_edge(
                edge=UsageEdge(
                    source_node_id=id(node.value),
                    target_node_id=id(node),
                    relation=EdgeKind.RETURNS,
                ),
            )

    def _visit_expression(self, *, node: AST, scope: Scope) -> None:
        """Visit an expression and record observable evidence.

        Args:
            node: The node examined while visit an expression and record
                observable evidence.
            scope: The scope examined while visit an expression and record
                observable evidence.

        """
        if isinstance(node, Call):
            self._visit_call(node=node, scope=scope)
        elif isinstance(node, Name):
            self.graph.add_edge(
                edge=UsageEdge(
                    source_node_id=id(node),
                    target_node_id=id(node),
                    relation=EdgeKind.READS,
                ),
            )
        elif isinstance(node, Attribute):
            self.graph.add_event(
                event=UsageEvent(
                    kind=UsageKind.ARGUMENT,
                    node_id=id(node),
                    scope_id=scope.scope_id,
                    name=node.attr,
                    operation="attribute",
                    span=_span_of(node=node),
                ),
            )
            self._visit_expression(node=node.value, scope=scope)
        elif isinstance(node, Subscript):
            self.graph.add_event(
                event=UsageEvent(
                    kind=UsageKind.SUBSCRIPT,
                    node_id=id(node),
                    scope_id=scope.scope_id,
                    operation=type(node.slice).__name__,
                    span=_span_of(node=node),
                ),
            )
            self._visit_unknown(node=node, scope=scope)
        elif isinstance(node, (BinOp, BoolOp, UnaryOp, Compare)):
            self._visit_operator_expression(node=node, scope=scope)
        elif isinstance(node, NamedExpr):
            self.graph.add_event(
                event=UsageEvent(
                    kind=UsageKind.WALRUS,
                    node_id=id(node),
                    scope_id=scope.scope_id,
                    span=_span_of(node=node),
                ),
            )
            self._add_target_symbol(target=node.target, scope=scope)
            self._visit_expression(node=node.value, scope=scope)
        elif isinstance(node, Constant):
            self.graph.add_event(
                event=UsageEvent(
                    kind=UsageKind.LITERAL,
                    node_id=id(node),
                    scope_id=scope.scope_id,
                    operation=type(node.value).__name__,
                    span=_span_of(node=node),
                ),
            )
        elif isinstance(node, Lambda):
            lambda_scope: Scope = Scope(
                scope_id=id(node),
                kind=ScopeKind.LAMBDA,
                name="<lambda>",
                parent_id=scope.scope_id,
                node_id=id(node),
                span=_span_of(node=node),
            )
            self.graph.add_scope(scope=lambda_scope)
            self._visit_arguments(arguments_node=node.args, scope=lambda_scope)
            self._visit_expression(node=node.body, scope=lambda_scope)
        else:
            self._visit_unknown(node=node, scope=scope)

    def _visit_call(self, *, node: Call, scope: Scope) -> None:
        """Visit a call expression.

        Args:
            node: The node examined while visit a call expression.
            scope: The scope examined while visit a call expression.

        """
        target_name: str | None = _expr_name(node=node.func)
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.CALL,
                node_id=id(node),
                scope_id=scope.scope_id,
                name=target_name,
                operation=target_name,
                span=_span_of(node=node),
            ),
        )
        keyword_names: list[str] = []
        keyword_value_ids: list[int] = []
        call_keyword: keyword | None = None
        for call_keyword in node.keywords:
            keyword_names.append(call_keyword.arg or "**")
            keyword_value_ids.append(id(call_keyword.value))
            self._visit_expression(node=call_keyword.value, scope=scope)
        argument: AST
        for argument in node.args:
            self._visit_expression(node=argument, scope=scope)
            self.graph.add_edge(
                edge=UsageEdge(
                    source_node_id=id(argument),
                    target_node_id=id(node),
                    relation=EdgeKind.ARGUMENT_OF,
                ),
            )
        self.graph.add_call_site(
            call_site=CallSite(
                node_id=id(node),
                scope_id=scope.scope_id,
                target=target_name,
                positional_argument_ids=tuple(
                    id(arg_node) for arg_node in node.args
                ),
                keyword_names=tuple(keyword_names),
                keyword_value_ids=tuple(keyword_value_ids),
            ),
        )
        self._visit_expression(node=node.func, scope=scope)

    def _visit_operator_expression(
        self,
        *,
        node: BinOp | BoolOp | UnaryOp | Compare,
        scope: Scope,
    ) -> None:
        """Visit an operator or comparison expression.

        Args:
            node: The node examined while visit an operator or comparison
                expression.
            scope: The scope examined while visit an operator or comparison
                expression.

        """
        if isinstance(node, BinOp):
            kind: UsageKind = UsageKind.OPERATOR
            operation: str = type(node.op).__name__
        elif isinstance(node, BoolOp):
            kind = UsageKind.BOOL_OPERATOR
            operation = type(node.op).__name__
        elif isinstance(node, UnaryOp):
            kind = UsageKind.UNARY_OPERATOR
            operation = type(node.op).__name__
        else:
            kind = UsageKind.COMPARISON
            operation = ",".join(
                type(operator).__name__ for operator in node.ops
            )
        self.graph.add_event(
            event=UsageEvent(
                kind=kind,
                node_id=id(node),
                scope_id=scope.scope_id,
                operation=operation,
                span=_span_of(node=node),
            ),
        )
        self._visit_unknown(node=node, scope=scope)

    def _visit_unknown(self, *, node: AST, scope: Scope) -> None:
        """Fallback recursive visitor for unhandled expression nodes.

        Args:
            node: The node examined while fallback recursive visitor for
                unhandled expression nodes.
            scope: The scope examined while fallback recursive visitor for
                unhandled expression nodes.

        """
        child: AST
        for child in iter_child_nodes(node=node):
            self._visit_expression(node=child, scope=scope)

    def _add_decorator_events(
        self,
        *,
        decorators: tuple[AST, ...],
        target: AST,
        scope: Scope,
        kind: UsageKind,
    ) -> None:
        """Add decorator events and edges.

        Args:
            decorators: Decorators supplied as tuple[AST, ...] for this
                operation.
            kind: Kind supplied as UsageKind for this operation.
            scope: The scope examined while add decorator events and edges.
            target: The target examined while add decorator events and edges.

        """
        decorator: AST
        for decorator in decorators:
            name: str | None = _expr_name(node=decorator)
            self.graph.add_event(
                event=UsageEvent(
                    kind=kind,
                    node_id=id(decorator),
                    scope_id=scope.scope_id,
                    name=name,
                    operation=name,
                    span=_span_of(node=decorator),
                ),
            )
            self.graph.add_edge(
                edge=UsageEdge(
                    source_node_id=id(decorator),
                    target_node_id=id(target),
                    relation=EdgeKind.DECORATES,
                ),
            )

    def _add_target_symbol(self, *, target: AST, scope: Scope) -> None:
        """Add symbols for a target expression.

        Args:
            scope: The scope examined while add symbols for a target
                expression.
            target: The target examined while add symbols for a target
                expression.

        """
        if isinstance(target, Name):
            self.graph.add_symbol(
                symbol=Symbol(
                    name=target.id,
                    kind=SymbolKind.VARIABLE,
                    scope_id=scope.scope_id,
                    node_id=id(target),
                    span=_span_of(node=target),
                ),
            )
        elif isinstance(target, Attribute):
            self.graph.add_symbol(
                symbol=Symbol(
                    name=target.attr,
                    kind=SymbolKind.ATTRIBUTE,
                    scope_id=scope.scope_id,
                    node_id=id(target),
                    span=_span_of(node=target),
                ),
            )
            self._visit_expression(node=target.value, scope=scope)
        elif isinstance(target, (Tuple, List)):
            element: AST
            for element in target.elts:
                self._add_target_symbol(target=element, scope=scope)

    def _add_import_symbol(
        self,
        *,
        name: str,
        source_name: str,
        node: Import | ImportFrom,
        scope: Scope,
    ) -> None:
        """Add one import symbol and import event.

        Args:
            name: Identifier of the name being resolved.
            node: The node examined while add one import symbol and import
                event.
            scope: The scope examined while add one import symbol and import
                event.
            source_name: Identifier of the source being resolved.

        """
        self.graph.add_symbol(
            symbol=Symbol(
                name=name,
                kind=SymbolKind.IMPORT,
                scope_id=scope.scope_id,
                node_id=id(node),
                span=_span_of(node=node),
            ),
        )
        self.graph.add_event(
            event=UsageEvent(
                kind=UsageKind.IMPORT,
                node_id=id(node),
                scope_id=scope.scope_id,
                name=name,
                operation=source_name,
                span=_span_of(node=node),
            ),
        )


def _span_of(*, node: AST) -> SourceSpan | None:
    """Return a node span when available.

    Args:
        node: The node examined while return a node span when available.

    Returns:
        SourceSpan | None produced by this operation.

    """
    return read_node_span(node=node)


def _expr_name(*, node: AST) -> str | None:
    """Return a dotted expression name when statically available.

    Args:
        node: The node examined while return a dotted expression name when
            statically available.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        base: str | None = _expr_name(node=node.value)
        if base is None:
            return node.attr
        return f"{base}.{node.attr}"
    if isinstance(node, Call):
        return _expr_name(node=node.func)
    return None
