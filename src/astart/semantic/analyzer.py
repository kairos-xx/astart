"""Public orchestrator for persistent symbols and bounded static semantics."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Call,
    ClassDef,
    FunctionDef,
    Global,
    Import,
    ImportFrom,
    Module,
    Name,
    Nonlocal,
    alias,
    arg,
    stmt,
    walk,
)
from dataclasses import dataclass
from keyword import iskeyword
from typing import TYPE_CHECKING, Literal, cast, final

from astart.delta import moved_identities, node_paths
from astart.node_attributes import (
    clear_attribute,
    write_attribute,
)
from astart.semantic.control_flow import ControlFlowGraph, ReachingDefinition
from astart.semantic.evaluator import (
    AbstractInterpreter,
    ActualArguments,
    AnalysisBudgets,
    State,
)
from astart.semantic.graph_bridge import GraphTypeBridge
from astart.semantic.graph_conversion import (
    GraphConversion,
    apply_graph_annotations,
    collect_graph_annotations,
)
from astart.semantic.identities import (
    Binding,
    DependencyEdge,
    IdentityIndex,
    Occurrence,
    Symbol,
)
from astart.semantic.scopes import RevisionDiff, Scope, ScopeGraph
from astart.semantic.stubs import StubIndex
from astart.semantic.type_inference import TypeConstraintSolver, TypeInference
from astart.semantic.type_shapes import TypeShape
from astart.semantic.values import (
    AbstractValue,
    CoroutineValue,
    InferenceResult,
    ObjectReference,
    UnboundValue,
    UnknownValue,
    proof_status,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from pathlib import Path

    from astart._graph.graph.document import (
        AstDocument,
        AstListItem,
        AstScalar,
    )
    from astart.delta import NodePath
    from astart.docstrings import DocstringNode
    from astart.semantic.typing_contracts import (
        BoundCall,
        CallableContract,
        ContractDiagnostic,
    )
type MutationKind = Literal[
    "NODE_INSERTED",
    "NODE_REMOVED",
    "NODE_REPLACED",
    "NODE_MOVED",
    "NODE_PROPERTY_CHANGED",
    "NODE_RENAMED",
    "NODE_REPARENTED",
    "NODE_CONTENT_CHANGED",
]


type FingerprintField = (
    tuple[str, int, tuple[AstScalar, ...]] | tuple[str, AstScalar]
)
type FingerprintEntry = tuple[
    int,
    int | None,
    str,
    tuple[FingerprintField, ...],
]
type FingerprintRecord = tuple[
    int | None,
    str,
    tuple[FingerprintField, ...],
]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MutationEvent:
    """Immutable semantic invalidation event for one AST identity.

    Attributes:
        node_id: Persistent syntax identity.
        kind: Semantic mutation classification.
        old_scope_id: Previous lexical scope, if indexed.
        new_scope_id: Current lexical scope, if indexed.

    """

    node_id: int
    kind: MutationKind
    old_scope_id: int | None
    new_scope_id: int | None


@final
class SemanticAnalyzer:
    """Module-owned semantic layer attached to an existing mutable AST.

    No target Python code is executed. All analysis operations inspect mutable
    Python AST objects and return immutable abstract-value results.
    """

    def __init__(
        self,
        *,
        root: Module,
        budgets: AnalysisBudgets | None = None,
    ) -> None:
        """Create a semantic graph and defer expensive value inference.

        Args:
            root: Original extended or ordinary module AST.
            budgets: Explicit, bounded safe-analysis policy.

        """
        self.root: Module = root
        self.budgets: AnalysisBudgets = budgets or AnalysisBudgets()
        self.identities: IdentityIndex = IdentityIndex()
        self.scopes: ScopeGraph = ScopeGraph(
            root=root,
            identities=self.identities,
        )
        self._fingerprint: tuple[FingerprintEntry, ...] = (
            self._fingerprint_tree()
        )
        self._link_documentation()
        self._paths = node_paths(root=root)
        self._last_events: tuple[MutationEvent, ...] = ()
        self._invalidated: frozenset[int] = frozenset()
        self.interpreter: AbstractInterpreter | None = None
        self._cfgs: dict[int, ControlFlowGraph] = {}
        self._incremental_statement_ids: tuple[int, ...] = ()
        self._type_solver: TypeConstraintSolver | None = None
        self._stub_index: StubIndex | None = None
        self._graph_conversion: GraphConversion | None = None
        self._graph_auto_path: Path | None = None
        self._symbols: SymbolRegistry = SymbolRegistry(analyzer=self)
        self._cfgs.update(self._refine_reaching_edges(graph=self.scopes))

    @property
    def symbols(self) -> SymbolRegistry:
        """Facade over the persistent lexical symbol registry.

        Returns:
            Symbol registry view bound to this analyzer.

        """
        return self._symbols

    @property
    def incremental_statements(self) -> tuple[int, ...]:
        """Statement identities re-executed by the last incremental pass.

        Returns:
            tuple[int, ...] produced by this operation.

        """
        self.refresh()
        return self._incremental_statement_ids

    @property
    def incremental_reused(self) -> tuple[int, ...]:
        """Statement identities whose prior abstract transfer was reused.

        Returns:
            tuple[int, ...] produced by this operation.

        """
        self.refresh()
        return (
            self.interpreter.incremental_reused
            if self.interpreter is not None
            else ()
        )

    @property
    def mutations(self) -> tuple[MutationEvent, ...]:
        """Return events produced by the most recent effective revision.

        Returns:
            tuple[MutationEvent, ...] produced by this operation.

        """
        self.refresh()
        return self._last_events

    @property
    def invalidated(self) -> frozenset[int]:
        """Return identities affected by the latest revision.

        Returns:
            frozenset[int] produced by this operation.

        """
        self.refresh()
        return self._invalidated

    @property
    def typing_diagnostics(self) -> tuple[ContractDiagnostic, ...]:
        """Return known override and class-contract violations.

        Returns:
            tuple[ContractDiagnostic, ...] produced by this operation.

        """
        return self._solver().contracts.diagnostics

    @property
    def types(self) -> TypeConstraintSolver:
        """Return the lazily solved bidirectional type-constraint graph.

        Returns:
            TypeConstraintSolver produced by this operation.

        """
        self.refresh()
        return self._solver()

    def _solver(self) -> TypeConstraintSolver:
        """Return the solver, building it lazily without reconciling.

        Callers that reach the analyzer through ``module.semantic`` have
        already reconciled, so per-query refresh calls would make every
        lookup pay a whole-tree fingerprint. This mirrors
        :meth:`bind_calls`: reconcile once, then query many.

        Returns:
            TypeConstraintSolver produced by this operation.

        """
        if self._type_solver is None:
            if (
                self._graph_auto_path is not None
                and self._graph_conversion is None
            ):
                self._graph_conversion = collect_graph_annotations(
                    root=self.root,
                    stubs_path=self._graph_auto_path,
                )
            self._type_solver = TypeConstraintSolver(
                root=self.root,
                scopes=self.scopes,
                stubs=self._stub_index,
                graph_conversion=(
                    self._graph_conversion.proposals
                    if self._graph_conversion is not None
                    else ()
                ),
            )
        return self._type_solver

    def refresh(self) -> tuple[MutationEvent, ...]:
        """Reconcile changed syntax, identities, scopes, and dependent caches.

        Returns:
            Immutable events for structural and semantic changes.

        Notes:
            Lexical scope reindexing is currently conservative and global;
            value inference is lazy and rebuilt after a semantic mutation.
            Pure source-coordinate shifts do not affect this fingerprint.

        """
        current: tuple[FingerprintEntry, ...] = self._fingerprint_tree()
        if current == self._fingerprint:
            return ()
        old: dict[int, FingerprintRecord] = {
            identity: (parent, kind, fields)
            for identity, parent, kind, fields in self._fingerprint
        }
        new: dict[int, FingerprintRecord] = {
            identity: (parent, kind, fields)
            for identity, parent, kind, fields in current
        }
        previous: ScopeGraph = self.scopes
        paths: dict[int, NodePath] = node_paths(root=self.root)
        relocated: set[int] = moved_identities(old=self._paths, new=paths)
        diff: RevisionDiff = self._revision_diff(
            old=old,
            new=new,
            relocated=relocated,
        )
        updated: ScopeGraph = ScopeGraph(
            root=self.root,
            identities=self.identities,
            previous=previous,
            diff=diff,
        )
        moved: set[int] = {
            identity
            for identity, node in updated.node_index.items()
            if id(node) in relocated
        }
        events: tuple[MutationEvent, ...] = self._mutation_events(
            old=old,
            new=new,
            moved=moved,
            previous=previous,
            updated=updated,
        )
        refined_cfgs: dict[int, ControlFlowGraph] = (
            self._refine_reaching_edges(
                graph=updated,
                events=events,
                previous=previous,
                diff=diff,
            )
        )
        invalidated: set[int] = self._invalidated_nodes(
            events=events,
            previous=previous,
            updated=updated,
        )
        changed_ids: frozenset[int] = frozenset(
            event.node_id for event in events
        )
        eligible: bool = self._incremental_eligible(
            events=events,
            moved=moved,
            same_identities=old.keys() == new.keys(),
            previous=previous,
            updated=updated,
        )
        dirty: frozenset[int] = self._dirty_statements(
            changed_ids=changed_ids,
        )
        invalidated.update(self._heap_invalidated(dirty=dirty))
        if eligible and dirty:
            eligible, dirty = self._refine_dirty(
                dirty=dirty,
                invalidated=invalidated,
                previous=previous,
            )
        interpreter: AbstractInterpreter | None = self.interpreter
        self.scopes = updated
        self._type_solver = None
        self._graph_conversion = None
        self._link_documentation()
        self._paths = paths
        self._fingerprint = current
        self._last_events = tuple(events)
        self._invalidated = frozenset(invalidated)
        self._cfgs.clear()
        self._cfgs.update(refined_cfgs)
        executed: tuple[int, ...] | None = None
        if eligible and interpreter is not None:
            executed = interpreter.recompute_module(
                dirty=dirty,
                scopes=updated,
            )
        self._incremental_statement_ids = executed or ()
        if executed is None:
            self.interpreter = None
        return self._last_events

    def evaluate(self) -> AbstractInterpreter:
        """Compute lazy abstract values for the latest semantic revision.

        Returns:
            AbstractInterpreter produced by this operation.

        """
        self.refresh()
        if self.interpreter is None:
            self.interpreter = AbstractInterpreter(
                root=self.root,
                scopes=self.scopes,
                budgets=self.budgets,
            )
        return self.interpreter

    def configure_stubs(self, *, root: Path | None) -> None:
        """Set an optional lazy ``.pyi`` source and invalidate type facts.

        Args:
            root: Filesystem path identifying the root.

        """
        self._stub_index = StubIndex(root=root) if root is not None else None
        self._type_solver = None

    def configure_graph(self, *, stubs_path: Path | None) -> None:
        """Enable/disable automatic original-graph inference per AST revision.

        When enabled, the integrated graph conversion pipeline is
        run lazily when type facts are requested, including after AST edits.
        Unchanged revisions reuse the prior graph-proposal set and solver.


        Args:
            stubs_path: Filesystem path identifying the stubs.

        """
        self.refresh()
        self._graph_auto_path = stubs_path
        self._graph_conversion = None
        self._type_solver = None

    def convert(
        self,
        *,
        stubs_path: Path,
        filename: str = "<memory>",
        apply: bool = False,
    ) -> GraphConversion:
        """Run the full internal graph converter and integrate its evidence.

        With ``apply=False``, annotations remain virtual; normal AST nodes
        acquire causal type evidence and constraints without altering source.
        With ``apply=True``, only verified annotations are added to the mutable
        AST, preserving existing comments and unrelated code.

        Raises:
            SyntaxError: Either source version is not valid Python.
            OSError: A required input source cannot be read.
            RuntimeError: The integrated graph pipeline reports a failure.



        Args:
            apply: Apply supplied as bool for this operation.
            filename: Filename supplied as str for this operation.
            stubs_path: Filesystem path identifying the stubs.

        Returns:
            GraphConversion produced by this operation.

        """
        self.refresh()
        result: GraphConversion = collect_graph_annotations(
            root=self.root,
            stubs_path=stubs_path,
            filename=filename,
        )
        if apply:
            apply_graph_annotations(root=self.root, integration=result)
            self.refresh()
        else:
            self._graph_conversion = result
            self._type_solver = None
        return result

    def graph_document(self, *, filename: str = "<memory>") -> AstDocument:
        """Get internal graph view of current edited source.

        Args:
            filename: Filename supplied as str for this operation.

        Returns:
            AstDocument produced by this operation.

        """
        return GraphTypeBridge.document(tree=self.root, filename=filename)

    def signature(self, *, name: str) -> tuple[CallableContract, ...]:
        """Find module or class method signatures with all parameter kinds.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            tuple[CallableContract, ...] produced by this operation.

        """
        return self._solver().contracts.variants(qualified_name=name)

    def bind_call(self, *, node: Call) -> BoundCall | None:
        """Return a complete effective argument binding for a source call.

        Args:
            node: The node examined while return a complete effective argument
                binding for a source call.

        Returns:
            BoundCall | None produced by this operation.

        """
        solver: TypeConstraintSolver = self._solver()
        return solver.call_bindings.get(self.identities.node_id(node=node))

    def bind_calls(self, *, nodes: Iterable[Call]) -> list[BoundCall | None]:
        """Bind many source calls after a single revision check.

        :meth:`bind_call` reconciles the whole tree before every lookup, which
        makes binding every call of a module quadratic. This method reconciles
        once and then only looks bindings up.

        Args:
            nodes: Calls to bind, in the order results are wanted.

        Returns:
            One binding, or ``None``, per call.

        """
        bindings: Mapping[int, BoundCall] = self._solver().call_bindings
        return [
            bindings.get(self.identities.node_id(node=node)) for node in nodes
        ]

    def infer_type(self, *, node: AST | str) -> TypeInference:
        """Infer type hints from annotations, expressions and contracts.

        Args:
            node: The node examined while infer type hints from annotations,
                expressions and contracts.

        Returns:
            TypeInference produced by this operation.

        """
        if isinstance(node, str):
            symbol: Symbol | None = self.resolve(name=node)
            if symbol is not None:
                return self._solver().infer_symbol(symbol_id=symbol.id)
            return TypeInference(inferred=TypeShape(name="Unknown"))
        return self._solver().infer_node(node=node)

    def symbol(self, *, node: AST) -> Symbol | None:
        """Resolve the symbol associated with a specific name occurrence.

        Args:
            node: Definition or reference AST node.

        Returns:
            Symbol record or None for unresolvable expressions.

        """
        self.refresh()
        occurrence: Occurrence | None = self.scopes.occurrences.get(
            self.identities.node_id(node=node),
        )
        return (
            self.scopes.symbols.get(occurrence.symbol_id)
            if occurrence is not None and occurrence.symbol_id is not None
            else None
        )

    def resolve(
        self,
        *,
        name: str,
        scope: AST | int | None = None,
    ) -> Symbol | None:
        """Resolve a lexical name from an AST node or scope identity.

        Args:
            name: Name to resolve.
            scope: AST or scope identity, defaulting to the module.

        Returns:
            Lexical symbol record when known.

        """
        self.refresh()
        scope_id: int = (
            self.scopes.root_id
            if scope is None
            else scope
            if isinstance(scope, int)
            else getattr(scope, "scope_id", self.scopes.root_id)
        )
        identity: int | None = self.scopes.resolve(
            name=name,
            scope_id=scope_id,
        )
        return (
            self.scopes.symbols.get(identity) if identity is not None else None
        )

    def references(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return read occurrences of the named lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Ordered individual referencing AST nodes.

        """
        self.refresh()
        return self.scopes.references(symbol_id=symbol_id)

    def definitions(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return definition occurrences of the lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Ordered definition AST nodes.

        """
        self.refresh()
        return self.scopes.definitions(symbol_id=symbol_id)

    def bindings(self, *, symbol_id: int) -> tuple[Binding, ...]:
        """Return all stored bindings for a lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Binding records in ascending identity order.

        """
        self.refresh()
        return tuple(
            self.scopes.bindings[identity]
            for identity in sorted(
                self.scopes.symbol_bindings.get(symbol_id, ()),
            )
        )

    def cfg(self, *, scope: AST | None = None) -> ControlFlowGraph:
        """Return the CFG and reaching definitions of one lexical scope.

        Args:
            scope: Module, function, or class scope owner.

        Returns:
            Graph with exceptional/control exit edges.

        Raises:
            TypeError: If the requested AST object has no statement suite.

        """
        self.refresh()
        owner: AST = scope or self.root
        identity: int = self.identities.node_id(node=owner)
        existing: ControlFlowGraph | None = self._cfgs.get(identity)
        if existing is not None:
            return existing
        body: list[stmt] | None = getattr(owner, "body", None)
        if not isinstance(body, list):
            msg: str = "CFG owner must expose a statement suite."
            raise TypeError(msg)
        graph: ControlFlowGraph = ControlFlowGraph(
            body=body,
            scopes=self.scopes,
        )
        self._cfgs[identity] = graph
        return graph

    def reaching(self, *, symbol_id: int, at: stmt) -> ReachingDefinition:
        """Find bindings that may reach a source-level statement.

        Args:
            symbol_id: Lexical symbol identity.
            at: Statement occurring in its owning suite.

        Returns:
            Reaching bindings.

        """
        self.refresh()
        scope_id: int = getattr(at, "scope_id", self.scopes.root_id)
        scope: Scope = self.scopes.scopes[scope_id]
        owner: AST = self.scopes.node_index[scope.owner_node_id]
        return self.cfg(scope=owner).reaching(at=at, symbol_id=symbol_id)

    def infer_node(self, *, node: AST) -> InferenceResult:
        """Infer one AST node's value and proof status.

        Args:
            node: AST expression, call, or assignment target.

        Returns:
            Safe abstract value and derivation trace.

        """
        evaluator: AbstractInterpreter = self.evaluate()
        identity: int = self.identities.node_id(node=node)
        found: InferenceResult | None = evaluator.node_results.get(identity)
        if found is not None:
            return found
        if isinstance(node, Name):
            occurrence: Occurrence | None = self.scopes.occurrences.get(
                identity,
            )
            if occurrence is not None and occurrence.symbol_id is not None:
                state: State = evaluator.at.get(
                    identity,
                    evaluator.final_state,
                )
                value: AbstractValue = state.values.get(
                    occurrence.symbol_id,
                    UnboundValue(),
                )
                return InferenceResult(
                    value=value,
                    status=proof_status(value=value),
                    dependencies=(occurrence.symbol_id,),
                    trace=(f"Read {node.id} at node {identity}",),
                )
        return InferenceResult(
            value=UnknownValue(
                reason="node has no executed inference context",
            ),
            status="unknown",
        )

    def infer_symbol(
        self,
        *,
        symbol_id: int,
        at: AST | None = None,
    ) -> InferenceResult:
        """Infer lexical binding at a program point or after module execution.

        Args:
            symbol_id: Lexical symbol identity.
            at: AST node at which to examine the incoming environment.

        Returns:
            Exact, approximate, unknown, or unbound result.

        """
        evaluator: AbstractInterpreter = self.evaluate()
        state: State = (
            evaluator.final_state
            if at is None
            else evaluator.at.get(
                self.identities.node_id(node=at),
                evaluator.final_state,
            )
        )
        value: AbstractValue = state.values.get(symbol_id, UnboundValue())
        symbol: Symbol | None = self.scopes.symbols.get(symbol_id)
        return InferenceResult(
            value=value,
            status=proof_status(value=value),
            dependencies=(symbol_id,),
            trace=(
                (
                    f"Symbol "
                    f"{(symbol.name if symbol else symbol_id)}"
                    f" at requested program point: "
                    f"{value!r}"
                ),
            ),
        )

    def infer(self, *, node: AST | str) -> InferenceResult:
        """Infer an expression node or a module-level symbol by name.

        Args:
            node: AST expression or module-level identifier.

        Returns:
            Abstract value and its proof classification.

        """
        if isinstance(node, str):
            symbol: Symbol | None = self.resolve(name=node)
            if symbol is None:
                return InferenceResult(
                    value=UnknownValue(reason=f"unresolved symbol {node}"),
                    status="unknown",
                )
            return self.infer_symbol(symbol_id=symbol.id)
        return self.infer_node(node=node)

    def infer_await(self, *, node: AST | str) -> InferenceResult:
        """Model the first awaited execution of a known deferred coroutine.

        This is a hypothetical static execution; it never runs analyzed code.
        Unknown external awaitables remain unknown rather than assumed pure.


        Args:
            node: The node examined while model the first awaited execution of
                a known deferred coroutine.

        Returns:
            InferenceResult produced by this operation.

        """
        result: InferenceResult = self.infer(node=node)
        if not isinstance(result.value, CoroutineValue):
            return InferenceResult(
                value=UnknownValue(
                    reason="expression is not a known coroutine",
                ),
                status="unknown",
            )
        coroutine: CoroutineValue = result.value
        interpreter: AbstractInterpreter = self.evaluate()
        value: AbstractValue = interpreter.function_call(
            function_id=coroutine.function_id,
            arguments=ActualArguments(
                positional=coroutine.arguments,
                named=dict(coroutine.keywords),
            ),
            state=interpreter.final_state.clone(),
            caller_id=coroutine.caller_id,
            awaited=True,
        )
        return InferenceResult(
            value=value,
            status=proof_status(value=value),
            trace=("Hypothetical execution of a known coroutine",),
        )

    def infer_call(self, *, node: AST) -> InferenceResult:
        """Return context-specific inference for a call expression.

        Args:
            node: Python call syntax node.

        Returns:
            Call result with effects already analyzed.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        return interpreter.call_results.get(
            self.identities.node_id(node=node),
            InferenceResult(
                value=UnknownValue(reason="call not evaluated"),
                status="unknown",
            ),
        )

    def call_contexts(self, *, node: AST) -> frozenset[int]:
        """Return every analysis context allocated for a call site.

        Args:
            node: Call expression whose contexts are requested.

        Returns:
            Context identities; multiple when argument values differ.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        identity: int = self.identities.node_id(node=node)
        return frozenset(
            context
            for (_function, caller, _args), context in (
                interpreter.contexts.items()
            )
            if caller == identity
        )

    def call_context(self, *, node: AST) -> int | None:
        """Return the most recent analysis context of a call site.

        Args:
            node: Call expression carrying ``context_id`` metadata.

        Returns:
            Context identity, or None when never analyzed.

        """
        self.evaluate()
        found: object = getattr(node, "context_id", None)
        return found if isinstance(found, int) else None

    def points_to(self, *, node: AST) -> frozenset[int]:
        """Return abstract object identities for an expression.

        Args:
            node: Expression whose points-to set is requested.

        Returns:
            Possible allocation IDs, empty for nonreferences.

        """
        value: AbstractValue = self.infer_node(node=node).value
        return (
            value.object_ids
            if isinstance(value, ObjectReference)
            else frozenset()
        )

    def may_alias(self, *, a: AST, b: AST) -> bool:
        """Check possible overlap of two inferred reference sets.

        Args:
            a: First expression.
            b: Second expression.

        Returns:
            True if both may reference the same allocation site.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        return interpreter.heap.may_alias(
            left=self.infer_node(node=a).value,
            right=self.infer_node(node=b).value,
        )

    def must_alias(self, *, a: AST, b: AST) -> bool:
        """Prove two expressions refer to the same unique allocation site.

        Args:
            a: First expression.
            b: Second expression.

        Returns:
            True only when must-alias can be established.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        return interpreter.heap.must_alias(
            left=self.infer_node(node=a).value,
            right=self.infer_node(node=b).value,
        )

    def allocation_site(self, *, object_id: int) -> AST | None:
        """Return the syntax node that allocated an abstract object.

        Args:
            object_id: Abstract allocation identity from ``points_to``.

        Returns:
            Allocation-site node, or None for unmodeled origins.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        site: int | None = interpreter.heap.allocation_node(
            object_id=object_id,
        )
        if site is None:
            return None
        for node in self.identities.all_nodes():
            if self.identities.node_id(node=node) == site:
                return node
        return None

    def heap_readers(self, *, object_id: int) -> frozenset[int]:
        """Return node identities that may read an abstract object.

        Args:
            object_id: Abstract allocation identity from ``points_to``.

        Returns:
            Syntax identities of recorded heap-location reads.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        return frozenset(interpreter.heap_readers.get(object_id, ()))

    def heap_writers(self, *, object_id: int) -> frozenset[int]:
        """Return node identities that may mutate an abstract object.

        Args:
            object_id: Abstract allocation identity from ``points_to``.

        Returns:
            Syntax identities of recorded heap-location writes.

        """
        interpreter: AbstractInterpreter = self.evaluate()
        return frozenset(interpreter.heap_writers.get(object_id, ()))

    def dependencies(self, *, node: AST) -> tuple[DependencyEdge, ...]:
        """Find the semantic producer edges of an AST expression.

        Args:
            node: Consumer expression.

        Returns:
            Direct incoming semantic dependency edges.

        """
        self.evaluate()
        return self.scopes.graph.dependencies(
            node_id=self.identities.node_id(node=node),
        )

    def dependents(self, *, node: AST) -> tuple[DependencyEdge, ...]:
        """Find AST consumers affected by a node.

        Args:
            node: Producer expression.

        Returns:
            Direct dependent edges.

        """
        self.evaluate()
        return self.scopes.graph.dependents(
            node_id=self.identities.node_id(node=node),
        )

    def affected_by(self, *, node: AST) -> frozenset[int]:
        """Compute the transitive semantic invalidation closure.

        Scope-resolution edges are visible through ``dependencies`` and
        ``dependents`` but excluded here: lexical scope changes trigger a
        non-incremental rebuild, so they must not fan out value
        invalidation.

        Args:
            node: Mutated producer AST node.

        Returns:
            All affected syntax identities.

        """
        self.evaluate()
        return self.scopes.graph.affected_by(
            node_id=self.identities.node_id(node=node),
            exclude=frozenset({"DEPENDS_ON_SCOPE"}),
        )

    def explain(
        self,
        *,
        node: AST,
        max_nodes: int = 128,
    ) -> tuple[str, ...]:
        """Explain inference by walking its recorded semantic dependency graph.

        Args:
            node: Value-producing node to explain.
            max_nodes: Maximum visited proof nodes before truncation.

        Returns:
            Deterministic proof with exact value and each producer edge.

        """
        result: InferenceResult = self.infer_node(node=node)
        evaluator: AbstractInterpreter = self.evaluate()
        start: int = self.identities.node_id(node=node)
        lines: list[str] = [
            f"Result [{result.status}]: {result.value!r}",
            *result.trace,
        ]
        visited: set[int] = set()
        pending: list[tuple[int, int]] = [(start, 0)]
        while pending and len(visited) < max_nodes:
            identity, depth = pending.pop()
            if identity in visited:
                continue
            visited.add(identity)
            consumer: AST | None = self.scopes.node_index.get(identity)
            if consumer is not None:
                proof: InferenceResult | None = evaluator.node_results.get(
                    identity,
                )
                detail: str = (
                    f" = {proof.value!r}" if proof is not None else ""
                )
                lines.append(
                    f"{'  ' * min(depth, 16)}{identity} "
                    f"{type(consumer).__name__}{detail}",
                )
            edges: tuple[DependencyEdge, ...] = self.scopes.graph.dependencies(
                node_id=identity,
            )
            for edge in reversed(edges):
                lines.append(
                    f"{'  ' * min(depth + 1, 16)}{edge.kind}: "
                    f"{edge.consumer} -> {edge.producer}",
                )
                if edge.producer not in visited:
                    pending.append((edge.producer, depth + 1))
        if pending:
            lines.append("Explanation truncated at analysis node budget.")
        return tuple(lines)

    def rename(self, *, symbol_id: int, new_name: str) -> None:
        """Rename a lexical symbol across its references and definitions.

        Args:
            symbol_id: Symbol to rename, preserving lexical identity.
            new_name: Valid Python identifier not shadowing another local.

        Raises:
            ValueError: If renamed spelling is invalid or collides in scope.

        """
        self.refresh()
        old: Symbol = self.scopes.symbols[symbol_id]
        self._validate_new_name(new_name=new_name, old=old)
        if old.name == new_name:
            return
        self._check_nested_capture(
            symbol_id=symbol_id,
            old=old,
            new_name=new_name,
        )
        self._update_references_and_definitions(
            symbol_id=symbol_id,
            new_name=new_name,
        )
        self._update_global_nonlocal(
            symbol_id=symbol_id,
            old=old,
            new_name=new_name,
        )
        self.refresh()

    def symbol_origin(self, *, symbol_id: int) -> int | None:
        """Return the predecessor symbol after a cross-scope relocation.

        A declaration moved between scopes receives a new symbol identity;
        its ``origin_id`` chains back to the previous-revision symbol, so
        callers can follow the lineage across repeated moves.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Previous-revision symbol identity, or None.

        """
        self.refresh()
        symbol: Symbol | None = self.scopes.symbols.get(symbol_id)
        return symbol.origin_id if symbol is not None else None

    def invalidate(self, *, symbol_id: int) -> None:
        """Discard cached inference for a symbol and its dependents.

        Abstract interpreter states map values by symbol identity, so
        surgical removal inside a live interpretation is unsound; the
        interpreter is rebuilt lazily on the next query instead.

        Args:
            symbol_id: Stable symbol identity to invalidate.

        """
        self.refresh()
        if symbol_id not in self.scopes.symbols:
            return
        seeds: set[int] = set(
            self.scopes.symbol_references.get(symbol_id, ()),
        )
        seeds.update(self.scopes.symbol_definitions.get(symbol_id, ()))
        seeds.update(
            self.scopes.bindings[binding].node_id
            for binding in self.scopes.symbol_bindings.get(symbol_id, ())
            if binding in self.scopes.bindings
        )
        affected: set[int] = set()
        for seed in seeds:
            affected.update(
                self.scopes.graph.affected_by(
                    node_id=seed,
                    exclude=frozenset({"DEPENDS_ON_SCOPE"}),
                ),
            )
        for node in self.identities.all_nodes():
            if self.identities.node_id(node=node) in affected:
                for name in (
                    "inferred_value",
                    "value_evidence",
                    "inferred_type",
                    "inferred_type_hint",
                    "object_id",
                ):
                    clear_attribute(node=node, name=name)
        self.interpreter = None
        self._type_solver = None

    @staticmethod
    def _walk_scope_chain(
        *,
        parents: dict[int, int | None],
        scopes: dict[int, Scope],
        node_scopes: dict[int, int],
        node_id: int,
    ) -> int | None:
        """Climb the syntax parent chain to the enclosing lexical scope.

        Args:
            node_id: Node identity supplied as int for this operation.
            node_scopes: Occurrence-node to scope map of one revision.
            parents: Node to parent map of one revision.
            scopes: Scope identity set of one revision.

        Returns:
            Owning scope identity, or None when the chain is exhausted.

        """
        parent: int | None = parents.get(node_id)
        while parent is not None:
            if parent in scopes:
                return parent
            found: int | None = node_scopes.get(parent)
            if found is not None:
                return found
            parent = parents.get(parent)
        return None

    @staticmethod
    def _mutation_events(
        *,
        old: dict[int, FingerprintRecord],
        new: dict[int, FingerprintRecord],
        moved: set[int],
        previous: ScopeGraph,
        updated: ScopeGraph,
    ) -> tuple[MutationEvent, ...]:
        """Classify each differing node identity into a mutation event.

        Args:
            moved: Node identities whose containment path changed.
            new: Fingerprint records for the current revision.
            old: Fingerprint records for the previous revision.
            previous: Scope graph of the earlier revision.
            updated: Scope graph of the current revision.

        Returns:
            Ordered mutation events for this revision.

        """
        events: list[MutationEvent] = []
        for identity in sorted(old.keys() | new.keys()):
            before: FingerprintRecord | None = old.get(identity)
            after: FingerprintRecord | None = new.get(identity)
            if before == after and identity not in moved:
                continue
            kind: MutationKind = (
                "NODE_INSERTED"
                if before is None
                else "NODE_REMOVED"
                if after is None
                else "NODE_REPARENTED"
                if before[0] != after[0]
                else "NODE_MOVED"
                if identity in moved
                else "NODE_REPLACED"
                if before[1] != after[1]
                else "NODE_RENAMED"
                if (
                    ("Name" in before[1] and "Name" in after[1])
                    or (
                        before[1] in ("arg", "FunctionDef", "ClassDef")
                        and before[2] != after[2]
                    )
                )
                else "NODE_CONTENT_CHANGED"
                if before[1] in ("Constant", "TypeIgnore")
                else "NODE_PROPERTY_CHANGED"
            )
            events.append(
                MutationEvent(
                    node_id=identity,
                    kind=kind,
                    old_scope_id=previous.node_scopes.get(identity),
                    new_scope_id=updated.node_scopes.get(identity),
                ),
            )
        return tuple(events)

    @staticmethod
    def _invalidated_nodes(
        *,
        events: tuple[MutationEvent, ...],
        previous: ScopeGraph,
        updated: ScopeGraph,
    ) -> set[int]:
        """Expand mutation events through both revisions' dependency graphs.

        Scope-resolution edges describe lexical structure, not value flow:
        when scopes change the revision is not incrementally eligible anyway,
        so they are excluded from the closure here.

        Args:
            events: Mutation events from this revision's diff.
            previous: Scope graph of the earlier revision.
            updated: Scope graph of the current revision.

        Returns:
            Node identities whose cached results cannot be trusted.

        """
        invalidated: set[int] = set()
        for event in events:
            invalidated.update(
                previous.graph.affected_by(
                    node_id=event.node_id,
                    exclude=frozenset({"DEPENDS_ON_SCOPE"}),
                ),
            )
            invalidated.update(
                updated.graph.affected_by(
                    node_id=event.node_id,
                    exclude=frozenset({"DEPENDS_ON_SCOPE"}),
                ),
            )
        return invalidated

    @staticmethod
    def _read_occurrences_by_scope(
        *,
        graph: ScopeGraph,
    ) -> dict[int, list[Occurrence]]:
        """Group same-scope read occurrences by their owning scope.

        Args:
            graph: Scope graph whose occurrences are grouped.

        Returns:
            Read occurrences keyed by owning scope identity.

        """
        by_scope: dict[int, list[Occurrence]] = {}
        for occurrence in graph.occurrences.values():
            if occurrence.symbol_id is None or "READ" not in occurrence.roles:
                continue
            symbol: Symbol | None = graph.symbols.get(occurrence.symbol_id)
            if symbol is None or symbol.scope_id != occurrence.scope_id:
                continue
            by_scope.setdefault(occurrence.scope_id, []).append(occurrence)
        return by_scope

    def _incremental_eligible(
        self,
        *,
        events: tuple[MutationEvent, ...],
        moved: set[int],
        same_identities: bool,
        previous: ScopeGraph,
        updated: ScopeGraph,
    ) -> bool:
        """Decide whether statement-level incremental evaluation applies.

        Args:
            events: Mutation events from this revision's diff.
            moved: Node identities whose containment path changed.
            previous: Scope graph of the earlier revision.
            same_identities: Whether the revision kept every node identity.
            updated: Scope graph of the current revision.

        Returns:
            True when the revision only changed node content in place.

        """
        return (
            self.interpreter is not None
            and same_identities
            and not moved
            and all(
                event.kind
                in (
                    "NODE_PROPERTY_CHANGED",
                    "NODE_RENAMED",
                    "NODE_CONTENT_CHANGED",
                )
                for event in events
            )
            and previous.symbols == updated.symbols
            and previous.occurrences == updated.occurrences
            and previous.bindings == updated.bindings
        )

    def _dirty_statements(
        self,
        *,
        changed_ids: frozenset[int],
    ) -> frozenset[int]:
        """Map changed node identities onto top-level statement indexes.

        Args:
            changed_ids: Node identities mutated by this revision.

        Returns:
            Indexes into ``self.root.body`` containing a changed node.

        """
        return frozenset(
            index
            for index, statement in enumerate(iterable=self.root.body)
            if any(
                self.identities.node_id(node=item) in changed_ids
                for item in walk(node=statement)
            )
        )

    def _heap_invalidated(self, *, dirty: frozenset[int]) -> set[int]:
        """Invalidate heap accessors sharing objects with changed writes.

        Heap mutations flow through abstract locations rather than lexical
        producers: a changed write invalidates every node that may read or
        write the same possible object.

        Args:
            dirty: Top-level statement indexes containing a changed node.

        Returns:
            Additional node identities to invalidate.

        """
        if self.interpreter is None or not dirty:
            return set()
        node_objects: dict[int, set[int]] = {}
        for object_id, writers in self.interpreter.heap_writers.items():
            for writer in writers:
                node_objects.setdefault(writer, set()).add(object_id)
        touched: set[int] = set()
        for index in dirty:
            for item in walk(node=self.root.body[index]):
                touched.update(
                    node_objects.get(
                        self.identities.node_id(node=item),
                        (),
                    ),
                )
        invalidated: set[int] = set()
        for object_id in touched:
            invalidated.update(
                self.interpreter.heap_writers.get(object_id, ()),
            )
            invalidated.update(
                self.interpreter.heap_readers.get(object_id, ()),
            )
        return invalidated

    def _refine_dirty(
        self,
        *,
        dirty: frozenset[int],
        invalidated: set[int],
        previous: ScopeGraph,
    ) -> tuple[bool, frozenset[int]]:
        """Widen the dirty set to callers of edited function bodies.

        A function-body edit can leave its definition's abstract value
        unchanged while changing callers.  The previous semantic graph
        carries CALLS_FUNCTION edges from each call to that definition;
        schedule those consumers even when the function binding stays the
        same.  Class-body edits are not incrementally modeled, so a dirty
        class statement disables eligibility entirely.

        Args:
            dirty: Top-level statement indexes containing a changed node.
            invalidated: Node identities already invalidated.
            previous: Scope graph of the earlier revision.

        Returns:
            Updated eligibility flag and widened dirty statement indexes.

        """
        eligible: bool = all(
            not isinstance(self.root.body[index], ClassDef) for index in dirty
        )
        dependent_ids: set[int] = set(invalidated)
        for index in dirty:
            owner: stmt = self.root.body[index]
            if isinstance(owner, (FunctionDef, AsyncFunctionDef)):
                dependent_ids.update(
                    previous.graph.affected_by(
                        node_id=self.identities.node_id(node=owner),
                        exclude=frozenset({"DEPENDS_ON_SCOPE"}),
                    ),
                )
        widened: frozenset[int] = frozenset(
            index
            for index, statement in enumerate(iterable=self.root.body)
            if index in dirty
            or any(
                self.identities.node_id(node=item) in dependent_ids
                and isinstance(item, (FunctionDef, AsyncFunctionDef)) is False
                for item in walk(node=statement)
            )
        )
        return eligible, widened

    def _revision_diff(
        self,
        *,
        old: dict[int, FingerprintRecord],
        new: dict[int, FingerprintRecord],
        relocated: set[int],
    ) -> RevisionDiff:
        """Summarize fingerprint changes for incremental reindexing.

        Args:
            new: Identity to ``(parent, kind, fields)`` entries now.
            old: Identity to ``(parent, kind, fields)`` entries before.
            relocated: Python object identities whose tree path moved.

        Returns:
            Changed and structural identity sets plus both parent maps.

        """
        moved_nodes: set[int] = {
            self.identities.node_id(node=node)
            for node in self.identities.all_nodes()
            if id(node) in relocated
        }
        changed: set[int] = set()
        structural: set[int] = set()
        for identity in old.keys() | new.keys():
            before_entry: FingerprintRecord | None = old.get(
                identity,
            )
            after_entry: FingerprintRecord | None = new.get(
                identity,
            )
            if before_entry == after_entry and identity not in moved_nodes:
                continue
            changed.add(identity)
            if (
                before_entry is None
                or after_entry is None
                or before_entry[0] != after_entry[0]
                or before_entry[1] != after_entry[1]
                or identity in moved_nodes
            ):
                structural.add(identity)
        return RevisionDiff(
            changed=frozenset(changed),
            structural=frozenset(structural),
            parents_new={
                identity: parent for identity, (parent, _, _) in new.items()
            },
            parents_old={
                identity: parent for identity, (parent, _, _) in old.items()
            },
        )

    def _refine_reaching_edges(
        self,
        *,
        graph: ScopeGraph,
        events: tuple[MutationEvent, ...] = (),
        previous: ScopeGraph | None = None,
        diff: RevisionDiff | None = None,
    ) -> dict[int, ControlFlowGraph]:
        """Replace conservative all-definition edges with CFG-precise ones.

        Only same-scope reads are refined; reads of symbols owned by other
        scopes keep the conservative fan-out because cross-scope reaching is
        not modeled by a single suite's control-flow graph.

        Control-flow graphs are reused across revisions: a scope whose suite
        kept its statement topology only re-solves blocks containing changed
        nodes, while a structurally altered suite is rebuilt completely.

        Args:
            events: Mutation events from this revision's diff.
            graph: Freshly indexed scope graph to refine in place.
            previous: Scope graph of the earlier revision, for scope lookup
                of removed nodes.
            diff: Node-level change summary supplying parent maps so that
                non-occurrence nodes can be attributed to a lexical scope.

        Returns:
            Control-flow graphs built during refinement, keyed by owner.

        """
        content_kinds: frozenset[str] = frozenset(
            {
                "NODE_PROPERTY_CHANGED",
                "NODE_RENAMED",
                "NODE_CONTENT_CHANGED",
            },
        )
        changed_ids: frozenset[int] = frozenset(
            event.node_id for event in events
        )
        structural_ids: frozenset[int] = frozenset(
            event.node_id
            for event in events
            if event.kind not in content_kinds
        )
        by_scope: dict[int, list[Occurrence]] = (
            self._read_occurrences_by_scope(graph=graph)
        )
        cached: dict[int, ControlFlowGraph] = self._cfgs
        cfgs: dict[int, ControlFlowGraph] = {}
        for scope_id, occurrences in by_scope.items():
            scope: Scope = graph.scopes[scope_id]
            owner: AST | None = graph.node_index.get(scope.owner_node_id)
            body: list[stmt] | None = getattr(owner, "body", None)
            if not isinstance(body, list):
                continue
            structural: bool = any(
                self._node_scope(
                    graph=graph,
                    previous=previous,
                    diff=diff,
                    node_id=identity,
                )
                == scope_id
                for identity in structural_ids
            )
            cached_cfg: ControlFlowGraph | None = (
                None if structural else cached.get(scope.owner_node_id)
            )
            reused: bool = cached_cfg is not None
            if reused:
                cfg: ControlFlowGraph = cached_cfg
                cfg.retarget(scopes=graph)
            else:
                cfg = ControlFlowGraph(
                    body=body,
                    scopes=graph,
                )
            cfgs[scope.owner_node_id] = cfg
            node_statements: dict[int, stmt] = {}
            statement_bindings: dict[int, dict[int, set[int]]] = (
                self._statement_maps(
                    cfg=cfg,
                    graph=graph,
                    node_statements=node_statements,
                )
            )
            if reused:
                dirty_blocks: frozenset[int] = frozenset(
                    cfg.statement_blocks[
                        self.identities.node_id(node=statement)
                    ]
                    for identity in changed_ids
                    if (
                        self._node_scope(
                            graph=graph,
                            previous=previous,
                            diff=diff,
                            node_id=identity,
                        )
                        == scope_id
                    )
                    and (statement := node_statements.get(identity))
                    is not None
                )
                if dirty_blocks:
                    cfg.solve_incremental(dirty=dirty_blocks)
            self._refine_scope_edges(
                graph=graph,
                cfg=cfg,
                occurrences=occurrences,
                node_statements=node_statements,
                statement_bindings=statement_bindings,
            )
        return cfgs

    def _statement_maps(
        self,
        *,
        cfg: ControlFlowGraph,
        graph: ScopeGraph,
        node_statements: dict[int, stmt],
    ) -> dict[int, dict[int, set[int]]]:
        """Index CFG blocks by member node and by binding they contain.

        Args:
            cfg: Control-flow graph to index.
            graph: Scope graph supplying binding records.
            node_statements: Output map from member node identity to the
                statement that contains it; filled in place.

        Returns:
            Map from statement identity to the binding nodes it contains,
            grouped per symbol.

        """
        statement_bindings: dict[int, dict[int, set[int]]] = {}
        for block_id in sorted(cfg.blocks):
            statement: stmt | None = cfg.blocks[block_id].statement
            if statement is None:
                continue
            statement_id: int = self.identities.node_id(node=statement)
            members: set[int] = {
                self.identities.node_id(node=item)
                for item in walk(node=statement)
            }
            for member in members:
                node_statements[member] = statement
            for binding in graph.bindings.values():
                if binding.node_id in members:
                    statement_bindings.setdefault(
                        statement_id,
                        {},
                    ).setdefault(binding.symbol_id, set()).add(
                        binding.node_id,
                    )
        return statement_bindings

    def _refine_scope_edges(
        self,
        *,
        graph: ScopeGraph,
        cfg: ControlFlowGraph,
        occurrences: list[Occurrence],
        node_statements: dict[int, stmt],
        statement_bindings: dict[int, dict[int, set[int]]],
    ) -> None:
        """Replace one scope's REACHES_DEFINITION edges with precise ones.

        Args:
            cfg: Solved control-flow graph for the scope.
            graph: Scope graph refined in place.
            node_statements: Member node to containing statement map.
            occurrences: Read occurrences owned by this scope.
            statement_bindings: Binding nodes per statement per symbol.

        """
        for occurrence in occurrences:
            statement: stmt | None = node_statements.get(occurrence.node_id)
            if statement is None or occurrence.symbol_id is None:
                continue
            symbol_id: int = occurrence.symbol_id
            reaching: ReachingDefinition = cfg.reaching(
                at=statement,
                symbol_id=symbol_id,
            )
            producers: set[int] = {
                graph.bindings[binding].node_id
                for binding in reaching.binding_ids
                if binding in graph.bindings
            }
            producers.update(
                statement_bindings.get(
                    self.identities.node_id(node=statement),
                    {},
                ).get(symbol_id, ()),
            )
            for edge in graph.graph.dependencies(
                node_id=occurrence.node_id,
            ):
                if edge.kind == "REACHES_DEFINITION":
                    graph.graph.remove(
                        consumer=edge.consumer,
                        producer=edge.producer,
                        kind=edge.kind,
                    )
            for producer in producers:
                graph.graph.add(
                    consumer=occurrence.node_id,
                    producer=producer,
                    kind="REACHES_DEFINITION",
                )

    def _node_scope(
        self,
        *,
        graph: ScopeGraph,
        previous: ScopeGraph | None,
        diff: RevisionDiff | None,
        node_id: int,
    ) -> int | None:
        """Attribute a changed node to its enclosing lexical scope.

        Occurrence nodes resolve through ``node_scopes``; other nodes,
        including statements, resolve through the revision's parent map,
        then through the previous revision when the node is gone.

        Args:
            diff: Revision parent maps, when incremental data exists.
            graph: Current scope graph.
            node_id: Syntax identity to attribute.
            previous: Earlier scope graph for removed nodes.

        Returns:
            Owning scope identity, or None when unattributable.

        """
        found: int | None = graph.node_scopes.get(node_id)
        if found is not None:
            return found
        if diff is not None:
            found = self._walk_scope_chain(
                parents=diff.parents_new,
                scopes=graph.scopes,
                node_scopes=graph.node_scopes,
                node_id=node_id,
            )
            if found is not None:
                return found
        if previous is None:
            return None
        found = previous.node_scopes.get(node_id)
        if found is not None:
            return found
        if diff is not None:
            return self._walk_scope_chain(
                parents=diff.parents_old,
                scopes=previous.scopes,
                node_scopes=previous.node_scopes,
                node_id=node_id,
            )
        return None

    def _link_documentation(self) -> None:
        """Connect structured documentation fields to referenced AST syntax."""
        documents: list[DocstringNode] = getattr(self.root, "docstrings", [])
        for document in documents:
            for entry in document.entries():
                if entry.target is not None:
                    self.scopes.graph.add(
                        consumer=self.identities.node_id(node=entry),
                        producer=self.identities.node_id(node=entry.target),
                        kind="DEPENDS_ON_VALUE",
                    )

    def _fingerprint_tree(
        self,
    ) -> tuple[FingerprintEntry, ...]:
        """Build an identity-preserving structural signature.

        Returns:
            tuple[FingerprintEntry, ...] produced by this operation.

        """
        result: list[FingerprintEntry] = []
        pending: list[tuple[AST, int | None]] = [(self.root, None)]
        visited: set[int] = set()
        node_id: Callable[..., int] = self.identities.node_id
        while pending:
            node, parent = pending.pop()
            identity: int = node_id(node=node)
            if identity in visited:
                continue
            visited.add(identity)
            values: list[FingerprintField] = []
            children: list[AST] = []
            for field in node._fields:
                value: object = getattr(node, field, None)
                if isinstance(value, AST):
                    children.append(value)
                elif isinstance(value, list):
                    items: list[AstListItem] = cast(
                        typ="list[AstListItem]",
                        val=value,
                    )
                    scalars: list[AstScalar] = []
                    for item in items:
                        if isinstance(item, AST):
                            children.append(item)
                        else:
                            scalars.append(item)
                    values.append((field, len(items), tuple(scalars)))
                elif isinstance(
                    value,
                    (str, bytes, int, float, complex, bool, type(None)),
                ):
                    values.append((field, value))
                else:
                    values.append((field, repr(value)))
            result.append(
                (identity, parent, type(node).__name__, tuple(values)),
            )
            pending.extend((child, identity) for child in reversed(children))
        return tuple(result)

    def _validate_new_name(self, *, new_name: str, old: Symbol) -> None:
        """Validate the new name is an identifier without collisions.

        Args:
            new_name: Identifier of the new being resolved.
            old: Old supplied as Symbol for this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        if not new_name.isidentifier() or iskeyword(new_name):
            msg: str = (
                "Renamed symbol must be a valid non-keyword Python identifier."
            )
            raise ValueError(msg)
        if self.scopes.scope_symbols[old.scope_id].get(new_name) not in (
            None,
            old.id,
        ):
            msg = "Renaming would collide with an existing lexical symbol."
            raise ValueError(msg)

    def _check_nested_capture(
        self,
        *,
        symbol_id: int,
        old: Symbol,
        new_name: str,
    ) -> None:
        """Check that renaming won't capture an existing nested reference.

        Args:
            new_name: Identifier of the new being resolved.
            old: Old supplied as Symbol for this operation.
            symbol_id: Symbol id supplied as int for this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        for occurrence in self.scopes.occurrences.values():
            node: AST = self.scopes.node_index[occurrence.node_id]
            if not isinstance(node, Name) or node.id != new_name:
                continue
            if occurrence.symbol_id == symbol_id:
                continue
            current: int = occurrence.scope_id
            while current != old.scope_id:
                scope_info: Scope = self.scopes.scopes[current]
                if scope_info.parent_id is None:
                    break
                current = scope_info.parent_id
            if current == old.scope_id:
                msg: str = (
                    "Renaming would capture an existing nested reference."
                )
                raise ValueError(msg)

    def _update_references_and_definitions(
        self,
        *,
        symbol_id: int,
        new_name: str,
    ) -> None:
        """Update all references and definitions of the symbol.

        Args:
            new_name: Identifier of the new being resolved.
            symbol_id: Symbol id supplied as int for this operation.

        """
        targets: tuple[AST, ...] = (
            *self.references(symbol_id=symbol_id),
            *self.definitions(symbol_id=symbol_id),
        )
        for target in targets:
            if isinstance(target, Name):
                target.id = new_name
            elif isinstance(target, arg):
                target.arg = new_name
            elif isinstance(target, (FunctionDef, AsyncFunctionDef, ClassDef)):
                target.name = new_name
            elif isinstance(target, (Import, ImportFrom, alias)):
                if isinstance(target, alias):
                    target.asname = new_name
            elif hasattr(target, "name"):
                write_attribute(node=target, name="name", value=new_name)

    def _update_global_nonlocal(
        self,
        *,
        symbol_id: int,
        old: Symbol,
        new_name: str,
    ) -> None:
        """Update global and nonlocal statements referencing the symbol.

        Args:
            new_name: Identifier of the new being resolved.
            old: Old supplied as Symbol for this operation.
            symbol_id: Symbol id supplied as int for this operation.

        """
        for statement in self.scopes.node_index.values():
            if (
                isinstance(statement, (Global, Nonlocal))
                and old.name in statement.names
            ):
                owning_scope: int = self.scopes.node_scopes[
                    self.identities.node_id(node=statement)
                ]
                if (
                    self.scopes.resolve(name=old.name, scope_id=owning_scope)
                    == symbol_id
                ):
                    statement.names = [
                        new_name if name == old.name else name
                        for name in statement.names
                    ]


@final
class SymbolRegistry:
    """Query facade over a module's persistent lexical symbols.

    Delegates to one ``SemanticAnalyzer`` so callers use the registry
    abstraction without touching scope internals.
    """

    def __init__(self, *, analyzer: SemanticAnalyzer) -> None:
        """Bind the facade to a single analyzer.

        Args:
            analyzer: Analyzer supplied as SemanticAnalyzer for this
                operation.

        """
        self._analyzer: SemanticAnalyzer = analyzer

    def get(self, *, symbol_id: int) -> Symbol | None:
        """Return the symbol record for one identity.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Symbol record, or None for unknown identities.

        """
        self._analyzer.refresh()
        return self._analyzer.scopes.symbols.get(symbol_id)

    def resolve(
        self,
        *,
        name: str,
        scope: AST | int | None = None,
    ) -> Symbol | None:
        """Resolve a lexical name within a scope.

        Args:
            name: Name to resolve.
            scope: AST or scope identity, defaulting to the module.

        Returns:
            Symbol record, or None for unknown names.

        """
        return self._analyzer.resolve(name=name, scope=scope)

    def references(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return read occurrences of a lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Ordered individual referencing AST nodes.

        """
        return self._analyzer.references(symbol_id=symbol_id)

    def definitions(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return definition occurrences of a lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Ordered definition AST nodes.

        """
        return self._analyzer.definitions(symbol_id=symbol_id)

    def bindings(self, *, symbol_id: int) -> tuple[Binding, ...]:
        """Return all stored bindings for a lexical symbol.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Binding records, possibly empty.

        """
        return self._analyzer.bindings(symbol_id=symbol_id)

    def origin(self, *, symbol_id: int) -> int | None:
        """Return the predecessor symbol after a cross-scope relocation.

        Args:
            symbol_id: Stable symbol identity.

        Returns:
            Previous-revision symbol identity, or None.

        """
        return self._analyzer.symbol_origin(symbol_id=symbol_id)

    def rename(self, *, symbol_id: int, new_name: str) -> None:
        """Rename a lexical symbol across references and definitions.

        Args:
            symbol_id: Symbol to rename, preserving lexical identity.
            new_name: Valid Python identifier not shadowing another local.

        """
        self._analyzer.rename(symbol_id=symbol_id, new_name=new_name)

    def invalidate(self, *, symbol_id: int) -> None:
        """Discard cached inference for a symbol and its dependents.

        Args:
            symbol_id: Stable symbol identity to invalidate.

        """
        self._analyzer.invalidate(symbol_id=symbol_id)
