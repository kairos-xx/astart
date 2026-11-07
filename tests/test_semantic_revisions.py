"""Revision-aware semantic features: roles, edges, provenance and reuse."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    If,
    List,
    Name,
    Return,
    While,
    expr,
)
from copy import copy
from symtable import SymbolTable, symtable
from typing import TYPE_CHECKING

from astart.ast import CommentedModule
from astart.semantic import (
    AbstractValue,
    AnalysisBudgets,
    LiteralValue,
    SemanticAnalyzer,
    UnknownValue,
)
from astart.semantic.scopes import ScopeGraph

from tests.expectations import (
    expect_binary_expr,
    expect_call_expr,
    expect_constant_expr,
    expect_equal,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_name_expr,
    expect_not_equal,
    expect_not_in,
    expect_not_none,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.semantic.control_flow import ControlFlowGraph
    from astart.semantic.identities import (
        Binding,
        DependencyEdge,
        Occurrence,
        Symbol,
    )


def _occurrence(*, tree: CommentedModule, node: AST) -> Occurrence:
    """Look up the indexed occurrence for a syntax node.

    Args:
        node: Syntax object carrying a stable identity.
        tree: Parsed module whose semantic graph is queried.

    Returns:
        The occurrence record registered for ``node``.

    """
    semantic: SemanticAnalyzer = tree.semantic
    identity: int = semantic.identities.node_id(node=node)
    return expect_not_none(value=semantic.scopes.occurrences.get(identity))


def _edge_kinds(*, tree: CommentedModule, node: AST) -> set[str]:
    """Collect dependency-edge kinds leaving a syntax node.

    Args:
        node: Syntax object carrying a stable identity.
        tree: Parsed module whose semantic graph is queried.

    Returns:
        Set of edge kinds whose consumer is ``node``.

    """
    semantic: SemanticAnalyzer = tree.semantic
    identity: int = semantic.identities.node_id(node=node)
    return {
        edge.kind
        for edge in semantic.scopes.graph.dependencies(node_id=identity)
    }


def test_capture_role_and_edge_for_cross_function_read() -> None:
    """A read captured through a function boundary earns CAPTURE."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def outer():
    x = 1
    def inner():
        return x
    return inner
""",
    )
    outer: FunctionDef = expect_instance(value=tree.body[0], kind=FunctionDef)
    inner: FunctionDef = expect_instance(value=outer.body[1], kind=FunctionDef)
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=inner.body[0]),
    )
    occurrence: Occurrence = _occurrence(tree=tree, node=read)
    expect_in(item="READ", container=occurrence.roles)
    expect_in(item="CAPTURE", container=occurrence.roles)
    expect_in(
        item="CAPTURES_SYMBOL",
        container=_edge_kinds(tree=tree, node=read),
    )


def test_module_scope_read_is_not_a_capture() -> None:
    """Reads resolving to module scope stay ordinary READs."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
def f():
    return x
""",
    )
    function: FunctionDef = expect_instance(
        value=tree.body[1],
        kind=FunctionDef,
    )
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=function.body[0]),
    )
    occurrence: Occurrence = _occurrence(tree=tree, node=read)
    expect_in(item="READ", container=occurrence.roles)
    expect_not_in(item="CAPTURE", container=occurrence.roles)
    expect_not_in(
        item="CAPTURES_SYMBOL",
        container=_edge_kinds(tree=tree, node=read),
    )


def test_capture_classification_matches_symtable_free_symbols() -> None:
    """CAPTURE occurrences correspond to stdlib-symtable free symbols."""
    source: str = """\
g = 0
def outer():
    x = 1
    def inner():
        return x + g
    return inner
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    outer: FunctionDef = expect_instance(value=tree.body[1], kind=FunctionDef)
    inner: FunctionDef = expect_instance(value=outer.body[1], kind=FunctionDef)
    binary: BinOp = expect_binary_expr(
        value=expression_of_stmt(value=inner.body[0]),
    )
    read_x: Name = expect_name_expr(value=binary.left)
    read_g: Name = expect_name_expr(value=binary.right)
    inner_table: SymbolTable = (
        (
            symtable(code=source, filename="<t>", compile_type="exec")
        ).get_children()[0]
    ).get_children()[0]
    expect_true(condition=inner_table.lookup(name="x").is_free())
    expect_true(condition=inner_table.lookup(name="g").is_global())
    expect_in(
        item="CAPTURE",
        container=_occurrence(tree=tree, node=read_x).roles,
    )
    expect_not_in(
        item="CAPTURE",
        container=_occurrence(tree=tree, node=read_g).roles,
    )


def test_annotation_role_on_type_expressions() -> None:
    """Names inside annotation fields receive the ANNOTATION role."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
T = int
x: T = 1
def f(a: T) -> T:
    return a
""",
    )
    annotated: AnnAssign = expect_instance(value=tree.body[1], kind=AnnAssign)
    function: FunctionDef = expect_instance(
        value=tree.body[2],
        kind=FunctionDef,
    )
    annotation_nodes: tuple[AST | None, ...] = (
        annotated.annotation,
        function.args.args[0].annotation,
        function.returns,
    )
    for node in annotation_nodes:
        occurrence: Occurrence = _occurrence(
            tree=tree,
            node=expect_not_none(value=node),
        )
        expect_in(item="ANNOTATION", container=occurrence.roles)
        expect_in(item="READ", container=occurrence.roles)


def test_depends_on_scope_edges_record_lookup_path() -> None:
    """Reads depend on every lexical scope consulted during resolution."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
def f():
    return x
""",
    )
    function: FunctionDef = expect_instance(
        value=tree.body[1],
        kind=FunctionDef,
    )
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=function.body[0]),
    )
    expect_in(
        item="DEPENDS_ON_SCOPE",
        container=_edge_kinds(tree=tree, node=read),
    )


def test_suspend_edges_mark_yield_and_await() -> None:
    """Statements suspending execution carry suspend CFG edges."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def gen():
    yield 1
    x = 2
async def coro():
    await task()
    return 3
""",
    )
    generator: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    coroutine: AsyncFunctionDef = expect_instance(
        value=tree.body[1],
        kind=AsyncFunctionDef,
    )
    for owner in (generator, coroutine):
        cfg: ControlFlowGraph = tree.semantic.cfg(scope=owner)
        kinds: set[str] = {
            edge.kind
            for block in cfg.blocks.values()
            for edge in block.successors
        }
        expect_in(item="suspend", container=kinds)


def test_call_nodes_carry_context_identities() -> None:
    """Evaluated call sites expose stable context identifiers."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(a):
    return a + 1
y = f(2)
z = f(4)
""",
    )
    tree.semantic.evaluate()
    call_y: Call = expect_call_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    call_z: Call = expect_call_expr(
        value=expression_of_stmt(value=tree.body[2]),
    )
    context_y: int | None = tree.semantic.call_context(node=call_y)
    context_z: int | None = tree.semantic.call_context(node=call_z)
    expect_not_none(value=context_y)
    expect_not_none(value=context_z)
    expect_not_equal(actual=context_y, unexpected=context_z)
    expect_in(
        item=context_y,
        container=tree.semantic.call_contexts(node=call_y),
    )


def test_copied_nodes_do_not_inherit_semantic_identities() -> None:
    """Shallow copies drop stale semantic attributes on re-identification."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
""",
    )
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    target: Name = expect_name_expr(value=assign.targets[0])
    tree.semantic.refresh()
    old_identity: int = tree.semantic.identities.node_id(node=target)
    expect_not_none(value=getattr(target, "symbol_id", None))
    clone: Name = copy(x=target)
    clone_identity: int = tree.semantic.identities.node_id(node=clone)
    expect_not_equal(actual=clone_identity, unexpected=old_identity)
    expect_is(actual=getattr(clone, "symbol_id", None), expected=None)
    expect_is(actual=getattr(clone, "binding_id", None), expected=None)


def test_allocation_site_reports_allocating_syntax() -> None:
    """points_to object identities map back to their allocation node."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1, 2]
y = x
""",
    )
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    literal: List = expect_instance(value=assign.value, kind=List)
    target: Name = expect_name_expr(value=assign.targets[0])
    objects: frozenset[int] = tree.semantic.points_to(node=target)
    expect_equal(actual=len(objects), expected=1)
    site: AST = expect_not_none(
        value=tree.semantic.allocation_site(object_id=next(iter(objects))),
    )
    expect_is(actual=site, expected=literal)


def test_references_object_edges_on_aliasing_read() -> None:
    """Reads resolving to allocated objects gain REFERENCES_OBJECT edges."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1]
y = x
""",
    )
    tree.semantic.evaluate()
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    expect_in(
        item="REFERENCES_OBJECT",
        container=_edge_kinds(tree=tree, node=read),
    )


def test_heap_location_edges_and_indexes() -> None:
    """Subscript reads and mutations produce heap edges plus indexes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1]
y = x[0]
x.append(2)
""",
    )
    tree.semantic.evaluate()
    semantic: SemanticAnalyzer = tree.semantic
    subscript: expr = expression_of_stmt(value=tree.body[1])
    mutation: Call = expect_call_expr(
        value=expression_of_stmt(value=tree.body[2]),
    )
    expect_in(
        item="READS_HEAP_LOCATION",
        container=_edge_kinds(tree=tree, node=subscript),
    )
    expect_in(
        item="WRITES_HEAP_LOCATION",
        container=_edge_kinds(tree=tree, node=mutation),
    )
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    target: Name = expect_name_expr(value=assign.targets[0])
    object_id: int = next(iter(semantic.points_to(node=target)))
    expect_in(
        item=semantic.identities.node_id(node=subscript),
        container=semantic.heap_readers(object_id=object_id),
    )
    expect_in(
        item=semantic.identities.node_id(node=mutation),
        container=semantic.heap_writers(object_id=object_id),
    )


def test_heap_mutation_invalidates_later_read() -> None:
    """A stronger mutation re-analyzes reads through the heap index."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1]
x.append(2)
z = x[0]
""",
    )
    tree.semantic.refresh()
    call: Call = expect_call_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    mutation_method: Attribute = expect_instance(
        value=call.func,
        kind=Attribute,
    )
    mutation_method.attr = "clear"
    call.args.clear()
    tree.semantic.refresh()
    assign: Assign = expect_instance(value=tree.body[2], kind=Assign)
    value: AbstractValue = tree.semantic.infer(node=assign.targets[0]).value
    expect_instance(value=value, kind=UnknownValue)


def test_cross_scope_move_preserves_symbol_origin() -> None:
    """Relocated declarations chain to their predecessor symbol."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    return 1
class C:
    q = 2
""",
    )
    tree.semantic.refresh()
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    original: Symbol = expect_not_none(
        value=tree.semantic.symbol(node=function),
    )
    tree.body.remove(function)
    wrapper: ClassDef = expect_instance(
        value=tree.body[0],
        kind=ClassDef,
    )
    wrapper.body.append(function)
    tree.semantic.refresh()
    relocated: Symbol = expect_not_none(
        value=tree.semantic.symbol(node=function),
    )
    expect_not_equal(actual=relocated.id, unexpected=original.id)
    expect_equal(actual=relocated.origin_id, expected=original.id)
    expect_equal(
        actual=tree.semantic.symbol_origin(symbol_id=relocated.id),
        expected=original.id,
    )


def test_symbols_facade_delegates_to_scope_graph() -> None:
    """The registry facade mirrors the scope graph query surface."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = x + 1
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    symbol: Symbol = expect_not_none(
        value=semantic.symbols.resolve(name="x"),
    )
    expect_is(
        actual=semantic.symbols.get(symbol_id=symbol.id),
        expected=symbol,
    )
    references: tuple[AST, ...] = semantic.symbols.references(
        symbol_id=symbol.id,
    )
    expect_equal(actual=len(references), expected=1)
    reader: Assign = expect_instance(value=tree.body[1], kind=Assign)
    read: Name = expect_name_expr(
        value=expect_binary_expr(value=reader.value).left,
    )
    expect_is(actual=references[0], expected=read)
    definitions: tuple[AST, ...] = semantic.symbols.definitions(
        symbol_id=symbol.id,
    )
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    expect_in(item=assign.targets[0], container=definitions)
    bindings: tuple[Binding, ...] = semantic.symbols.bindings(
        symbol_id=symbol.id,
    )
    expect_true(condition=len(bindings) >= 1)


def test_invalidate_symbol_clears_dependent_values() -> None:
    """Symbol invalidation drops cached values of dependents only."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = x + 2
z = 5
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    tree.infer(node="y")
    tree.infer(node="z")
    dependent: expr = expression_of_stmt(value=tree.body[1])
    unrelated: expr = expression_of_stmt(value=tree.body[2])
    expect_not_none(value=getattr(dependent, "inferred_value", None))
    expect_not_none(value=getattr(unrelated, "inferred_value", None))
    symbol: Symbol = expect_not_none(value=semantic.resolve(name="x"))
    semantic.invalidate(symbol_id=symbol.id)
    expect_is(
        actual=getattr(dependent, "inferred_value", None),
        expected=None,
    )
    expect_is_not(
        actual=getattr(unrelated, "inferred_value", None),
        unexpected=None,
    )
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=3))


def test_precise_reaches_definition_after_conditional() -> None:
    """Reads link only to definitions that may reach them on the CFG."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
import sys
x = 0
if sys.argv:
    x = 1
else:
    x = 2
y = x
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=tree.body[3]),
    )
    read_id: int = semantic.identities.node_id(node=read)
    producers: set[int] = {
        edge.producer
        for edge in semantic.scopes.graph.dependencies(node_id=read_id)
        if edge.kind == "REACHES_DEFINITION"
    }
    conditional: If = expect_instance(value=tree.body[2], kind=If)
    branch_defs: set[int] = {
        semantic.identities.node_id(
            node=expect_instance(value=suite[0], kind=Assign).targets[0],
        )
        for suite in (conditional.body, conditional.orelse)
    }
    expect_equal(actual=producers, expected=branch_defs)


def test_context_sensitivity_modes_partition_contexts() -> None:
    """Full sensitivity keys contexts by call sites; none shares one."""
    source: str = """\
def f(a):
    return a + 1
y = f(1)
z = f(2)
"""
    full: SemanticAnalyzer = SemanticAnalyzer(
        root=CommentedModule.parse(source=source),
        budgets=AnalysisBudgets(context_sensitivity="full"),
    )
    none: SemanticAnalyzer = SemanticAnalyzer(
        root=CommentedModule.parse(source=source),
        budgets=AnalysisBudgets(context_sensitivity="none"),
    )
    expect_true(condition=len(full.evaluate().contexts) > 1)
    expect_equal(actual=len(none.evaluate().contexts), expected=1)
    expect_equal(
        actual=none.infer(node="y").value,
        expected=LiteralValue(value=2),
    )


def test_symbolic_operation_budget_returns_bounded_unknown() -> None:
    """Exhausted symbolic budgets degrade to explicit unknown values."""
    semantic: SemanticAnalyzer = SemanticAnalyzer(
        root=CommentedModule.parse(
            source="""\
def f(a):
    return a + 1
y = f(1)
""",
        ),
        budgets=AnalysisBudgets(max_symbolic_operations=0),
    )
    result: AbstractValue = semantic.infer(node="y").value
    expect_instance(value=result, kind=UnknownValue)


def test_heap_object_budget_returns_bounded_unknown() -> None:
    """Exhausted heap budgets degrade allocations to unknown values."""
    semantic: SemanticAnalyzer = SemanticAnalyzer(
        root=CommentedModule.parse(
            source="""\
x = [1]
z = [2]
y = z[0]
""",
        ),
        budgets=AnalysisBudgets(max_heap_objects=1),
    )
    result: AbstractValue = semantic.infer(node="y").value
    expect_instance(value=result, kind=UnknownValue)


def test_cfg_reuse_and_rebuild_across_revisions() -> None:
    """Content edits reuse CFGs; structural edits rebuild the owner."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(a):
    x = 1
    return x + a
""",
    )
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    semantic: SemanticAnalyzer = tree.semantic
    original: ControlFlowGraph = semantic.cfg(scope=function)
    assign: Assign = expect_instance(value=function.body[0], kind=Assign)
    constant: Constant = expect_constant_expr(value=assign.value)
    constant.value = 9
    semantic.refresh()
    reused: ControlFlowGraph = semantic.cfg(scope=function)
    expect_is(actual=reused, expected=original)
    function.body.insert(0, Expr(value=Constant(value=0)))
    semantic.refresh()
    expect_is_not(actual=semantic.cfg(scope=function), unexpected=original)


def test_scope_graft_reuses_untouched_subtrees() -> None:
    """Sibling scopes untouched by an edit retain their index."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def g(b):
    return b
def f(a):
    return a
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    semantic.refresh()
    sibling: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    sibling_scope: int = semantic.identities.node_id(node=sibling)
    target: FunctionDef = expect_instance(value=tree.body[1], kind=FunctionDef)
    returned: Return = expect_instance(value=target.body[0], kind=Return)
    returned.value = Constant(value=1)
    semantic.refresh()
    expect_in(item=sibling_scope, container=semantic.scopes.grafted_scopes)


def test_scope_graft_matches_fresh_index() -> None:
    """A grafted graph is identical to a full reindex of the same tree."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
def g(b):
    z = b * 2
    return z
def f(a):
    y = a + x
    return y
""",
    )
    tree.semantic.refresh()
    function: FunctionDef = expect_instance(
        value=tree.body[2],
        kind=FunctionDef,
    )
    assign: Assign = expect_instance(value=function.body[0], kind=Assign)
    expect_binary_expr(value=assign.value).right = Constant(value=42)
    tree.semantic.refresh()
    current: ScopeGraph = tree.semantic.scopes
    fresh: ScopeGraph = ScopeGraph(
        root=tree,
        identities=tree.semantic.identities,
    )
    for name in (
        "symbols",
        "occurrences",
        "scopes",
        "scope_symbols",
        "scope_children",
        "node_scopes",
        "symbol_references",
        "symbol_definitions",
    ):
        expect_equal(
            actual=getattr(current, name),
            expected=getattr(fresh, name),
            message=name,
        )
    expect_equal(
        actual={
            (b.node_id, b.symbol_id, b.kind) for b in current.bindings.values()
        },
        expected={
            (b.node_id, b.symbol_id, b.kind) for b in fresh.bindings.values()
        },
    )


def test_alias_queries_and_public_dependency_views() -> None:
    """Alias and dependency views expose the recorded object graph."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1]
y = x
z = 3
""",
    )
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    target: Name = expect_name_expr(value=assign.targets[0])
    read: Name = expect_name_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    expect_true(condition=tree.semantic.may_alias(a=target, b=read))
    expect_true(condition=tree.semantic.must_alias(a=target, b=read))
    edges: tuple[DependencyEdge, ...] = tree.semantic.dependencies(node=read)
    kinds: set[str] = {edge.kind for edge in edges}
    expect_in(item="READS_SYMBOL", container=kinds)
    expect_true(condition=len(tree.semantic.dependents(node=target)) >= 1)
    expect_in(
        item=tree.semantic.identities.node_id(node=read),
        container=tree.semantic.affected_by(node=target),
    )


def test_explain_reports_dependency_walk() -> None:
    """Explanations trace values through recorded dependency edges."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = x + 1
""",
    )
    expression: BinOp = expect_binary_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    lines: tuple[str, ...] = tree.semantic.explain(node=expression)
    expect_true(condition=lines[0].startswith("Result"))
    expect_true(condition=any("READS_SYMBOL" in line for line in lines))
    truncated: tuple[str, ...] = tree.semantic.explain(
        node=expression,
        max_nodes=1,
    )
    expect_in(
        item="Explanation truncated at analysis node budget.",
        container=truncated,
    )


def test_rename_updates_references_and_rejects_captures() -> None:
    """Renames rewrite every occurrence and reject nested capture."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = x + 1
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    symbol: Symbol = expect_not_none(value=semantic.resolve(name="x"))
    semantic.rename(symbol_id=symbol.id, new_name="value")
    renamed: Symbol = expect_not_none(value=semantic.resolve(name="value"))
    expect_equal(actual=renamed.id, expected=symbol.id)
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=2))
    nested: CommentedModule = CommentedModule.parse(
        source="""\
a = 1
def outer():
    b = a
    def inner():
        return a
    return inner
""",
    )
    outer: FunctionDef = expect_instance(
        value=nested.body[1],
        kind=FunctionDef,
    )
    assign_b: Assign = expect_instance(value=outer.body[0], kind=Assign)
    write_b: Name = expect_name_expr(value=assign_b.targets[0])
    outer_symbol: Symbol = expect_not_none(
        value=nested.semantic.symbol(node=write_b),
    )
    try:
        nested.semantic.rename(symbol_id=outer_symbol.id, new_name="a")
    except ValueError as error:
        expect_in(item="capture", container=str(object=error))
    else:
        expect_true(condition=False, message="rename should reject capture")


def test_registry_facade_rename_invalidate_and_origin() -> None:
    """The facade forwards rename, invalidate and provenance queries."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
y = x + 1
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    symbol: Symbol = expect_not_none(value=semantic.symbols.resolve(name="x"))
    expect_is(
        actual=semantic.symbols.origin(symbol_id=symbol.id),
        expected=None,
    )
    semantic.symbols.rename(symbol_id=symbol.id, new_name="value")
    expect_not_none(value=semantic.symbols.resolve(name="value"))
    semantic.symbols.invalidate(symbol_id=symbol.id)
    semantic.invalidate(symbol_id=999999)
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=2))


def test_allocation_site_unknown_for_unmodeled_objects() -> None:
    """Unknown allocation identities report no allocating node."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
""",
    )
    tree.semantic.evaluate()
    expect_is(
        actual=tree.semantic.allocation_site(object_id=424242),
        expected=None,
    )
    call: Constant = Constant(value=0)
    expect_equal(
        actual=tree.semantic.call_contexts(node=call),
        expected=frozenset(),
    )


def test_heap_write_reanalysis_with_live_interpreter() -> None:
    """Mutation edits flow through the heap index during refresh."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = [1]
x.append(2)
z = x[0]
""",
    )
    expect_equal(actual=tree.infer(node="z"), expected=LiteralValue(value=1))
    call: Call = expect_call_expr(
        value=expression_of_stmt(value=tree.body[1]),
    )
    mutation_method: Attribute = expect_instance(
        value=call.func,
        kind=Attribute,
    )
    mutation_method.attr = "clear"
    call.args.clear()
    tree.semantic.refresh()
    expect_true(condition=len(tree.semantic.invalidated) >= 1)
    assign: Assign = expect_instance(value=tree.body[2], kind=Assign)
    value: AbstractValue = tree.semantic.infer(node=assign.targets[0]).value
    expect_instance(value=value, kind=UnknownValue)


def test_incremental_properties_reflect_last_revision() -> None:
    """Revision counters describe the most recent incremental pass."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = 1
b = a + 2
""",
    )
    tree.infer(node="b")
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    constant: Constant = expect_constant_expr(value=assign.value)
    constant.value = 7
    tree.semantic.refresh()
    expect_true(condition=len(tree.semantic.incremental_statements) >= 1)
    reused: tuple[int, ...] = tree.semantic.incremental_reused
    expect_instance(value=reused, kind=tuple)
    expect_true(condition=len(tree.semantic.invalidated) >= 1)
    expect_equal(
        actual=tree.infer(node="b"),
        expected=LiteralValue(value=9),
    )


def test_docstring_entries_link_to_argument_nodes() -> None:
    """Structured docstrings record edges to their documented targets."""
    tree: CommentedModule = CommentedModule.parse(
        source='''\
def f(x):
    """Do a thing.

    Args:
        x: the input
    """
    return x
''',
    )
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    expect_true(
        condition=len(tree.semantic.dependents(node=(function.args.args[0])))
        >= 1,
    )


def test_scope_attribution_via_parent_chain() -> None:
    """Statement edits inside nested suites rebuild the owning CFG."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(items):
    while items:
        x = 1
        items.pop()
    return 0
""",
    )
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    semantic: SemanticAnalyzer = tree.semantic
    loop: While = expect_instance(value=function.body[0], kind=While)
    original: ControlFlowGraph = semantic.cfg(scope=function)
    loop.body.append(Expr(value=Constant(value=0)))
    semantic.refresh()
    expect_is_not(
        actual=semantic.cfg(scope=function),
        unexpected=original,
    )
