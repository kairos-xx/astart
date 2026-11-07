"""Inspectible Python control-flow graphs and reaching-definition dataflow."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    Await,
    Break,
    ClassDef,
    Continue,
    For,
    FunctionDef,
    If,
    Lambda,
    Match,
    Raise,
    Return,
    Try,
    TryStar,
    While,
    With,
    Yield,
    YieldFrom,
    iter_child_nodes,
    stmt,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, final

from astart.semantic.worklist import IncrementalWorklist, SolveStatistics

if TYPE_CHECKING:
    from astart.semantic.identities import Binding, Occurrence
    from astart.semantic.scopes import ScopeGraph
type EdgeLabel = Literal[
    "next",
    "true",
    "false",
    "loop",
    "break",
    "continue",
    "return",
    "exception",
    "handler",
    "finally",
    "match",
    "suspend",
]


@dataclass(frozen=True, slots=True)
class SuiteContext:
    """Context for building a suite of statements.

    Attributes:
        break_target: Break target retained as int | None by this instance.
        continue_target: Continue target retained as int | None by this
            instance.
        exception_target: Exception target retained as int by this instance.
        successor: Successor retained as int by this instance.

    """

    successor: int
    break_target: int | None
    continue_target: int | None
    exception_target: int


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FlowEdge:
    """One control-flow transition, including exceptional edges.

    Attributes:
        target: Destination block identity.
        kind: Control transfer classification.

    """

    target: int
    kind: EdgeLabel


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BasicBlock:
    """One statement-level CFG block.

    Attributes:
        id: CFG-local block identity.
        statement: Executed syntactic statement, or None for sentinel blocks.
        successors: Outgoing edges.

    """

    id: int
    statement: stmt | None
    successors: tuple[FlowEdge, ...]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ReachingDefinition:
    """A symbol and all binding IDs potentially reaching a program point.

    Attributes:
        symbol_id: Lexical symbol identity.
        binding_ids: Conservative set of possible reaching bindings.

    """

    symbol_id: int
    binding_ids: frozenset[int]


@final
class ControlFlowGraph:
    """Statement-level CFG with fixed-point reaching-definition analysis."""

    def __init__(
        self,
        *,
        body: list[stmt],
        scopes: ScopeGraph,
    ) -> None:
        """Build a CFG with explicit branch, loop, return, and cleanup edges.

        Args:
            body: Executable suite of one lexical scope.
            scopes: Indexed symbol and binding graph.

        """
        self._scopes: ScopeGraph = scopes
        self._mutable: dict[int, tuple[stmt | None, list[FlowEdge]]] = {}
        self._next_id: int = 1
        self.exit_id: int = self._new(statement=None)
        self.exception_id: int = self._new(statement=None)
        self.entry_id: int = self._new(statement=None)
        first: int = self._suite(
            statements=body,
            ctx=SuiteContext(
                successor=self.exit_id,
                break_target=None,
                continue_target=None,
                exception_target=self.exception_id,
            ),
        )
        self._edge(origin=self.entry_id, target=first, kind="next")
        self.blocks: dict[int, BasicBlock] = {
            identity: BasicBlock(
                id=identity,
                statement=statement,
                successors=tuple(edges),
            )
            for identity, (statement, edges) in self._mutable.items()
        }
        self.statement_blocks: dict[int, int] = {
            scopes.identities.node_id(node=statement): identity
            for identity, block in self.blocks.items()
            if (statement := block.statement) is not None
        }
        self._reaching: dict[int, dict[int, frozenset[int]]] = {}
        self._build_reaching()

    @property
    def solve_statistics(self) -> SolveStatistics:
        """Return visited blocks, changed blocks and convergence status.

        Returns:
            SolveStatistics produced by this operation.

        """
        return self._solver.statistics

    def retarget(self, *, scopes: ScopeGraph) -> None:
        """Point transfer functions at a rebuilt lexical index.

        Block topology and the worklist solver survive; subsequent
        ``solve_incremental`` calls read symbols and bindings from the new
        graph while reusing unchanged results.

        Args:
            scopes: Freshly indexed symbol and binding graph.

        """
        self._scopes = scopes

    def solve_incremental(
        self,
        *,
        dirty: frozenset[int],
    ) -> SolveStatistics:
        """Recompute changed blocks and all their data-dependent successors.

        Args:
            dirty: CFG block IDs whose transfer behavior changed in place.

        Returns:
            Exact worklist statistics, including visited and changed blocks.

        """
        statistics: SolveStatistics = self._solver.solve(dirty=dirty)
        self._publish_solution(statistics=statistics)
        return statistics

    def reaching(
        self,
        *,
        at: stmt,
        symbol_id: int,
    ) -> ReachingDefinition:
        """Query all definitions reaching a statement's entry.

        Args:
            at: Statement in this CFG.
            symbol_id: Lexical symbol being queried.

        Returns:
            Conservative reaching-definition set.

        Raises:
            KeyError: If the statement belongs to another scope's CFG.

        """
        block_id: int = self.statement_blocks[
            self._scopes.identities.node_id(node=at)
        ]
        return ReachingDefinition(
            symbol_id=symbol_id,
            binding_ids=self._reaching.get(block_id, {}).get(
                symbol_id,
                frozenset(),
            ),
        )

    @staticmethod
    def _suspends(*, statement: stmt) -> bool:
        """Whether a statement can pause its own suite's flow.

        Descends into the statement's expressions while skipping nested
        scope owners: a ``yield`` inside a nested function suspends that
        function's flow, not the enclosing suite's.

        Args:
            statement: Statement inspected for ``yield`` or ``await``.

        Returns:
            True when the statement contains a suspension point.

        """
        pending: list[AST] = [statement]
        while pending:
            node: AST = pending.pop()
            if isinstance(node, (Yield, YieldFrom, Await)):
                return True
            pending.extend(
                child
                for child in iter_child_nodes(node=node)
                if not isinstance(
                    child,
                    (FunctionDef, AsyncFunctionDef, ClassDef, Lambda),
                )
            )
        return False

    def _new(self, *, statement: stmt | None) -> int:
        """Allocate a new block identity.

        Args:
            statement: The statement examined while allocate a new block
                identity.

        Returns:
            int produced by this operation.

        """
        identity: int = self._next_id
        self._next_id += 1
        self._mutable[identity] = (statement, [])
        return identity

    def _edge(self, *, origin: int, target: int, kind: EdgeLabel) -> None:
        """Add a deterministic directed CFG edge.

        Args:
            kind: Kind supplied as EdgeLabel for this operation.
            origin: Origin supplied as int for this operation.
            target: The target examined while add a deterministic directed CFG
                edge.

        """
        edge: FlowEdge = FlowEdge(target=target, kind=kind)
        if edge not in self._mutable[origin][1]:
            self._mutable[origin][1].append(edge)

    def _suite(self, *, statements: list[stmt], ctx: SuiteContext) -> int:
        """Build a structured suite backwards, preserving entry order.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            statements: Collection of statements supplied for this operation.

        Returns:
            int produced by this operation.

        """
        next_id: int = ctx.successor
        for statement in reversed(statements):
            identity: int = self._new(statement=statement)
            self._dispatch_statement(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
            next_id = identity
        return next_id

    def _dispatch_statement(
        self,
        *,
        identity: int,
        statement: stmt,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Dispatch a statement to its appropriate control-flow handler.

        Args:
            identity: Identifier of the statement's control-flow node.
            statement: Statement whose control flow is dispatched.
            next_id: Identifier of the subsequent control-flow node.
            ctx: Suite context containing active control-flow targets.

        """
        if isinstance(statement, If):
            self._handle_if(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        elif isinstance(statement, (While, For, AsyncFor)):
            self._handle_loop(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        elif isinstance(statement, (Try, TryStar)):
            self._handle_try(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        elif isinstance(statement, Match):
            self._handle_match(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        elif isinstance(statement, (With, AsyncWith)):
            self._handle_with(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        elif isinstance(statement, (Return, Raise, Break, Continue)):
            self._dispatch_terminal(
                identity=identity,
                statement=statement,
                next_id=next_id,
                ctx=ctx,
            )
        else:
            self._edge(origin=identity, target=next_id, kind="next")
        if not isinstance(
            statement,
            (Return, Raise, Break, Continue),
        ) and self._suspends(statement=statement):
            self._edge(origin=identity, target=next_id, kind="suspend")

    def _dispatch_terminal(
        self,
        *,
        identity: int,
        statement: Return | Raise | Break | Continue,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Dispatch a terminal statement to its control-flow handler.

        Args:
            identity: Identifier of the terminal statement's control-flow node.
            statement: Return, raise, break, or continue statement to dispatch.
            next_id: Identifier of the subsequent control-flow node.
            ctx: Suite context containing exception and loop targets.

        """
        if isinstance(statement, Return):
            self._handle_return(identity=identity)
        elif isinstance(statement, Raise):
            self._handle_raise(
                identity=identity,
                exception_target=ctx.exception_target,
            )
        elif isinstance(statement, Break):
            self._handle_break(
                identity=identity,
                break_target=ctx.break_target,
                next_id=next_id,
            )
        else:
            self._handle_continue(
                identity=identity,
                continue_target=ctx.continue_target,
                next_id=next_id,
            )

    def _handle_if(
        self,
        *,
        identity: int,
        statement: If,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Handle If statement control flow.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.
            statement: The statement examined while handle If statement control
                flow.

        """
        branches: tuple[tuple[EdgeLabel, list[stmt]], ...] = (
            ("true", statement.body),
            ("false", statement.orelse),
        )
        for branch, suite in branches:
            target: int = self._suite(
                statements=suite,
                ctx=SuiteContext(
                    successor=next_id,
                    break_target=ctx.break_target,
                    continue_target=ctx.continue_target,
                    exception_target=ctx.exception_target,
                ),
            )
            self._edge(origin=identity, target=target, kind=branch)

    def _handle_loop(
        self,
        *,
        identity: int,
        statement: While | For | AsyncFor,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Handle While, For, and AsyncFor loop control flow.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.
            statement: The statement examined while handle While, For, and
                AsyncFor loop control flow.

        """
        loop_entry: int = self._suite(
            statements=statement.body,
            ctx=SuiteContext(
                successor=identity,
                break_target=next_id,
                continue_target=identity,
                exception_target=ctx.exception_target,
            ),
        )
        loop_exit: int = self._suite(
            statements=statement.orelse,
            ctx=SuiteContext(
                successor=next_id,
                break_target=ctx.break_target,
                continue_target=ctx.continue_target,
                exception_target=ctx.exception_target,
            ),
        )
        self._edge(origin=identity, target=loop_entry, kind="loop")
        self._edge(origin=identity, target=loop_exit, kind="false")

    def _handle_try(
        self,
        *,
        identity: int,
        statement: Try | TryStar,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Handle Try and TryStar control flow.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.
            statement: The statement examined while handle Try and TryStar
                control flow.

        """
        final_entry: int = self._suite(
            statements=statement.finalbody,
            ctx=SuiteContext(
                successor=next_id,
                break_target=ctx.break_target,
                continue_target=ctx.continue_target,
                exception_target=ctx.exception_target,
            ),
        )
        success_entry: int = self._suite(
            statements=statement.orelse,
            ctx=SuiteContext(
                successor=final_entry,
                break_target=ctx.break_target,
                continue_target=ctx.continue_target,
                exception_target=ctx.exception_target,
            ),
        )
        handlers: list[int] = [
            self._suite(
                statements=handler.body,
                ctx=SuiteContext(
                    successor=final_entry,
                    break_target=ctx.break_target,
                    continue_target=ctx.continue_target,
                    exception_target=final_entry
                    if statement.finalbody
                    else ctx.exception_target,
                ),
            )
            for handler in statement.handlers
        ]
        body_entry: int = self._suite(
            statements=statement.body,
            ctx=SuiteContext(
                successor=success_entry,
                break_target=ctx.break_target,
                continue_target=ctx.continue_target,
                exception_target=handlers[0]
                if handlers
                else (
                    final_entry
                    if statement.finalbody
                    else ctx.exception_target
                ),
            ),
        )
        self._edge(origin=identity, target=body_entry, kind="next")
        for target in handlers:
            self._edge(origin=identity, target=target, kind="handler")
        if statement.finalbody:
            self._edge(
                origin=identity,
                target=final_entry,
                kind="finally",
            )

    def _handle_match(
        self,
        *,
        identity: int,
        statement: Match,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Handle Match statement control flow.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.
            statement: The statement examined while handle Match statement
                control flow.

        """
        for case in statement.cases:
            case_entry: int = self._suite(
                statements=case.body,
                ctx=SuiteContext(
                    successor=next_id,
                    break_target=ctx.break_target,
                    continue_target=ctx.continue_target,
                    exception_target=ctx.exception_target,
                ),
            )
            self._edge(
                origin=identity,
                target=case_entry,
                kind="match",
            )
        self._edge(origin=identity, target=next_id, kind="false")

    def _handle_with(
        self,
        *,
        identity: int,
        statement: With | AsyncWith,
        next_id: int,
        ctx: SuiteContext,
    ) -> None:
        """Handle With and AsyncWith control flow.

        Args:
            ctx: Ctx supplied as SuiteContext for this operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.
            statement: The statement examined while handle With and AsyncWith
                control flow.

        """
        body_entry: int = self._suite(
            statements=statement.body,
            ctx=SuiteContext(
                successor=next_id,
                break_target=ctx.break_target,
                continue_target=ctx.continue_target,
                exception_target=ctx.exception_target,
            ),
        )
        self._edge(origin=identity, target=body_entry, kind="next")
        self._edge(
            origin=identity,
            target=ctx.exception_target,
            kind="exception",
        )

    def _handle_return(self, *, identity: int) -> None:
        """Handle Return statement control flow.

        Args:
            identity: Identity supplied as int for this operation.

        """
        self._edge(origin=identity, target=self.exit_id, kind="return")

    def _handle_raise(self, *, identity: int, exception_target: int) -> None:
        """Handle Raise statement control flow.

        Args:
            exception_target: Exception target supplied as int for this
                operation.
            identity: Identity supplied as int for this operation.

        """
        self._edge(
            origin=identity,
            target=exception_target,
            kind="exception",
        )

    def _handle_break(
        self,
        *,
        identity: int,
        break_target: int | None,
        next_id: int,
    ) -> None:
        """Handle Break statement control flow.

        Args:
            break_target: Break target supplied as int | None for this
                operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.

        """
        self._edge(
            origin=identity,
            target=break_target or next_id,
            kind="break",
        )

    def _handle_continue(
        self,
        *,
        identity: int,
        continue_target: int | None,
        next_id: int,
    ) -> None:
        """Handle Continue statement control flow.

        Args:
            continue_target: Continue target supplied as int | None for this
                operation.
            identity: Identity supplied as int for this operation.
            next_id: Next id supplied as int for this operation.

        """
        self._edge(
            origin=identity,
            target=continue_target or next_id,
            kind="continue",
        )

    def _transfer(
        self,
        *,
        block: BasicBlock,
        incoming: dict[int, frozenset[int]],
    ) -> dict[int, frozenset[int]]:
        """Kill previous definitions on writes and generate new bindings.

        Args:
            block: Block supplied as BasicBlock for this operation.
            incoming: Incoming supplied as dict[int, frozenset[int]] for this
                operation.

        Returns:
            dict[int, frozenset[int]] produced by this operation.

        """
        outgoing: dict[int, frozenset[int]] = dict(incoming)
        statement: stmt | None = block.statement
        if statement is None:
            return outgoing
        nodes: list[AST] = [statement]
        while nodes:
            node: AST = nodes.pop()
            nodes.extend(
                child
                for child in iter_child_nodes(node=node)
                if not isinstance(child, stmt)
            )
            node_id: int = self._scopes.identities.node_id(node=node)
            occurrence: Occurrence | None = self._scopes.occurrences.get(
                node_id,
            )
            if occurrence is None or occurrence.symbol_id is None:
                continue
            if not occurrence.roles.intersection(
                {"WRITE", "DEFINE", "DELETE", "IMPORT"},
            ):
                continue
            for binding_id in self._scopes.symbol_bindings.get(
                occurrence.symbol_id,
                (),
            ):
                binding: Binding = self._scopes.bindings[binding_id]
                if binding.node_id == node_id:
                    outgoing[occurrence.symbol_id] = frozenset({binding_id})
        return outgoing

    def _build_reaching(self) -> None:
        """Solve reaching definitions via a deletion-safe worklist."""
        self._solver: IncrementalWorklist = IncrementalWorklist(
            successors={
                identity: tuple(edge.target for edge in block.successors)
                for identity, block in self.blocks.items()
            },
            entry=self.entry_id,
            transfer=lambda identity, incoming: self._transfer(
                block=self.blocks[identity],
                incoming=incoming,
            ),
        )
        self._publish_solution(statistics=self._solver.solve())

    def _publish_solution(self, *, statistics: SolveStatistics) -> None:
        """Publish a converged solution or a sound conservative top state.

        Args:
            statistics: Statistics supplied as SolveStatistics for this
                operation.

        """
        if statistics.converged:
            self._reaching = dict(self._solver.incoming)
        else:
            top: dict[int, frozenset[int]] = {
                symbol_id: frozenset(
                    self._scopes.symbol_bindings.get(symbol_id, ()),
                )
                for symbol_id in self._scopes.symbols
            }
            self._reaching = {identity: dict(top) for identity in self.blocks}
