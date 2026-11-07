"""Semantic integration, identity, CFG, aliasing, and safe inference tests."""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    Call,
    Constant,
    FunctionDef,
    Module,
    Name,
    Subscript,
    expr,
    parse,
    stmt,
)
from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from astart.ast import CommentedModule
from astart.semantic import (
    AbstractHeap,
    AnalysisBudgets,
    ControlFlowGraph,
    ErrorValue,
    LiteralValue,
    SemanticAnalyzer,
    UnboundValue,
    UnionValue,
    UnknownValue,
)
from astart.semantic.identities import DependencyGraph, IdentityIndex
from astart.semantic.values import (
    AbstractValue,
    NeverValue,
    SequenceValue,
    join_values,
    proof_status,
    truth_value,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_is,
    expect_not_equal,
    expect_not_in,
    expect_not_none,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.semantic.analyzer import MutationEvent
    from astart.semantic.identities import Symbol
    from astart.semantic.values import ObjectReference


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        (
            """\
a = 4
b = a + 7
""",
            "b",
            11,
        ),
        (
            """\
a = 4
a = 5
b = a + 7
""",
            "b",
            12,
        ),
        (
            """\
a = 2 * 3
b = a - 1
""",
            "b",
            5,
        ),
        (
            """\
a = 8 / 2
""",
            "a",
            4.0,
        ),
        (
            """\
a = 7 // 2
""",
            "a",
            3,
        ),
        (
            """\
a = 2 ** 5
""",
            "a",
            32,
        ),
        (
            """\
a = 9 % 5
""",
            "a",
            4,
        ),
        (
            """\
a = 1 << 3
""",
            "a",
            8,
        ),
        (
            """\
a = 16 >> 2
""",
            "a",
            4,
        ),
        (
            """\
a = 5 & 3
""",
            "a",
            1,
        ),
        (
            """\
a = 5 | 2
""",
            "a",
            7,
        ),
        (
            """\
a = 5 ^ 3
""",
            "a",
            6,
        ),
        (
            """\
a = +3
""",
            "a",
            3,
        ),
        (
            """\
a = -3
""",
            "a",
            -3,
        ),
        (
            """\
a = ~3
""",
            "a",
            -4,
        ),
        (
            """\
a = not 0
""",
            "a",
            True,
        ),
        (
            """\
a = 2 < 3
""",
            "a",
            True,
        ),
        (
            """\
a = 2 <= 2
""",
            "a",
            True,
        ),
        (
            """\
a = 4 > 3
""",
            "a",
            True,
        ),
        (
            """\
a = 3 >= 3
""",
            "a",
            True,
        ),
        (
            """\
a = 3 == 3
""",
            "a",
            True,
        ),
        (
            """\
a = 3 != 3
""",
            "a",
            False,
        ),
        (
            """\
a = 1 is None
""",
            "a",
            False,
        ),
        (
            """\
a = 1 is not None
""",
            "a",
            True,
        ),
        (
            """\
a = 'ab' in 'abc'
""",
            "a",
            True,
        ),
        (
            """\
a = 'd' not in 'abc'
""",
            "a",
            True,
        ),
        (
            """\
a = True and 2
""",
            "a",
            2,
        ),
        (
            """\
a = False or 7
""",
            "a",
            7,
        ),
        (
            """\
a = False and bad_unknown()
""",
            "a",
            False,
        ),
        (
            """\
a = True or bad_unknown()
""",
            "a",
            True,
        ),
        (
            """\
a = 4 if 1 else 8
""",
            "a",
            4,
        ),
        (
            """\
a = 4 if 0 else 8
""",
            "a",
            8,
        ),
        (
            """\
a = (1, 3)[1]
""",
            "a",
            3,
        ),
        (
            """\
a = 'abc'[1]
""",
            "a",
            "b",
        ),
        (
            """\
a = -1
b = abs(a)
""",
            "b",
            1,
        ),
        (
            """\
a = int('12')
""",
            "a",
            12,
        ),
        (
            """\
a = str(12)
""",
            "a",
            "12",
        ),
        (
            """\
a = bool(0)
""",
            "a",
            False,
        ),
        (
            """\
a = len((1, 2, 3))
""",
            "a",
            3,
        ),
        (
            """\
a = sum((1, 2, 3))
""",
            "a",
            6,
        ),
        (
            """\
a = f'answer={2+3}'
""",
            "a",
            "answer=5",
        ),
        (
            """\
a = f'{3!r}'
""",
            "a",
            "3",
        ),
        (
            """\
a = f'{3:03d}'
""",
            "a",
            "003",
        ),
        (
            """\
a = 1
a += 2
""",
            "a",
            3,
        ),
        (
            """\
a, b = (1, 2)
""",
            "b",
            2,
        ),
        (
            """\
a = [1, 2]
b = a[0]
""",
            "b",
            1,
        ),
        (
            """\
a = {'x': 5}
b = a['x']
""",
            "b",
            5,
        ),
        (
            """\
a = [1]
a.append(8)
b = a[1]
""",
            "b",
            8,
        ),
        (
            """\
a = [1]
a.extend((2, 3))
b = a[2]
""",
            "b",
            3,
        ),
        (
            """\
a = [1, 2]
b = a.pop()
""",
            "b",
            2,
        ),
        (
            """\
a = [1, 2]
a[0] = 7
b = a[0]
""",
            "b",
            7,
        ),
        (
            """\
a = [1, 2]
b = a
b[0] = 7
c = a[0]
""",
            "c",
            7,
        ),
        (
            """\
def f(x):
 return x*2
a=f(3)
""",
            "a",
            6,
        ),
        (
            """\
def f(x, y=4):
 return x+y
a=f(3)
""",
            "a",
            7,
        ),
        (
            """\
def f(x, y=4):
 return x+y
a=f(3, y=5)
""",
            "a",
            8,
        ),
        (
            """\
f = lambda x: x * 3
a=f(4)
""",
            "a",
            12,
        ),
        (
            (
                """\
def outer(x):
 def inner(y):
  return x+y
 return inner(4)
a=outer(5)
"""
            ),
            "a",
            9,
        ),
        (
            """\
a = 0
for i in range(4):
 a += i
""",
            "a",
            6,
        ),
        (
            (
                """\
def fib(n):
 if n <= 1:
  return n
 return fib(n-1)+fib(n-2)
a=fib(5)
"""
            ),
            "a",
            5,
        ),
        (
            """\
a = 1
if True:
 a = 2
else:
 a = 3
""",
            "a",
            2,
        ),
        (
            """\
a = 1
if False:
 a = 2
else:
 a = 3
""",
            "a",
            3,
        ),
        (
            """\
x = 1
def f():
 x=2
 return x
a=f()
""",
            "a",
            2,
        ),
        (
            """\
x = 1
def f():
 x=2
 return x
a=x
""",
            "a",
            1,
        ),
    ],
)
def test_exact_inference(
    *,
    source: str,
    name: str,
    expected: float | str | bool,
) -> None:
    """Interpret known built-in operations without evaluating source code.

    Args:
        expected: Expected supplied as float | str | bool for this
            operation.
        name: Identifier of the name being resolved.
        source: The source examined while interpret known built-in
            operations without evaluating source code.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node=name),
        expected=LiteralValue(value=expected),
    )
    expect_equal(
        actual=tree.semantic.infer(node=name).status,
        expected="exact",
    )


@pytest.mark.parametrize(
    ("source", "name"),
    [
        (
            """\
a = unknown_name
""",
            "a",
        ),
        (
            """\
a = unknown_call(1)
""",
            "a",
        ),
        (
            """\
a = object.x
""",
            "a",
        ),
        (
            """\
a = 2 ** 1000
""",
            "a",
        ),
        (
            """\
a = len(unknown)
""",
            "a",
        ),
        (
            """\
a = [1, 2][unknown]
""",
            "a",
        ),
        (
            """\
a = 3 @ 4
""",
            "a",
        ),
        (
            """\
a = {1 for i in range(10)}
""",
            "a",
        ),
        (
            """\
a = (x for x in range(10))
""",
            "a",
        ),
        (
            """\
def f(x):
 return f(x)
a=f(1)
""",
            "a",
        ),
    ],
)
def test_conservative_unknown(*, source: str, name: str) -> None:
    """Unsupported or unsafe constructs must not invent exact values.

    Args:
        name: Identifier of the name being resolved.
        source: The source examined while unsupported or unsafe constructs
            must not invent exact values.

    """
    expect_instance(
        value=CommentedModule.parse(source=source).infer(node=name),
        kind=UnknownValue,
    )


def test_shadowing_and_unbound() -> None:
    """Lexical scoping differentiates declarations and early local reads."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
x = 1
def f():
 y=x
 x=2
 return y
z=f()
"""
        ),
    )
    outer: int = expect_not_none(value=tree.semantic.resolve(name="x")).id
    function: FunctionDef = expect_instance(
        value=tree.body[1],
        kind=FunctionDef,
    )
    inner: int = expect_not_none(
        value=tree.semantic.resolve(name="x", scope=function),
    ).id
    expect_not_equal(actual=outer, unexpected=inner)
    expect_instance(value=tree.infer(node="z"), kind=UnboundValue)


def test_branch_join_and_reaching() -> None:
    """Both unknown branch definitions must reach following uses."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
if unknown:
 x=10
else:
 x=20
y=x
"""
        ),
    )
    result: AbstractValue = tree.infer(node="y")
    if not isinstance(result, UnionValue):
        pytest.fail(reason="Branch join must yield UnionValue")
    expect_equal(
        actual={
            item.value
            for item in result.options
            if isinstance(item, LiteralValue)
        },
        expected={10, 20},
    )
    symbol: Symbol | None = tree.semantic.resolve(name="x")
    symbol = expect_not_none(value=symbol)
    expect_equal(
        actual=len(
            tree.semantic.reaching(
                symbol_id=symbol.id,
                at=tree.body[-1],
            ).binding_ids,
        ),
        expected=2,
    )


def test_incremental_preserves_symbol_identity() -> None:
    """A lexical rename keeps symbol identity and invalidates users."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+2
c=b*3
d=100
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    original: Symbol | None = semantic.resolve(name="a")
    original = expect_not_none(value=original)
    semantic.rename(symbol_id=original.id, new_name="amount")
    expect_equal(
        actual=expect_not_none(value=semantic.resolve(name="amount")).id,
        expected=original.id,
    )
    expect_equal(
        actual=len(semantic.references(symbol_id=original.id)),
        expected=1,
    )
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=9))
    expect_equal(actual=tree.infer(node="d"), expected=LiteralValue(value=100))
    value: Constant = expect_instance(
        value=expression_of_stmt(value=tree.body[0]),
        kind=Constant,
    )
    final_assignment: Assign = expect_instance(
        value=tree.body[-1],
        kind=Assign,
    )
    expect_not_in(
        item=semantic.identities.node_id(node=final_assignment.targets[0]),
        container=semantic.affected_by(
            node=value,
        ),
    )
    value.value = 10
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=36))
    expect_equal(actual=tree.infer(node="d"), expected=LiteralValue(value=100))
    expect_true(condition=bool(semantic.mutations))


def test_sibling_move_preserves_node_id_but_changes_reaching_definitions() -> (
    None
):
    """Moving a definition can make a read unbound, keeping its node ID."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+1
c=10
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    identity: int = semantic.identities.node_id(node=assignment)
    expect_equal(actual=tree.infer(node="b"), expected=LiteralValue(value=2))
    tree.body.append(tree.body.pop(0))
    events: tuple[MutationEvent, ...] = semantic.refresh()
    expect_true(
        condition=any(event.kind == "NODE_MOVED" for event in events),
    )
    expect_equal(
        actual=semantic.identities.node_id(node=assignment),
        expected=identity,
    )
    expect_instance(value=tree.infer(node="b"), kind=UnknownValue)


def test_scope_move_changes_lexical_binding() -> None:
    """A syntax node keeps its ID while changing lexical ownership."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
def a():
 x=1
 return x
def b():
 return 0
"""
        ),
    )
    semantic: SemanticAnalyzer = tree.semantic
    first: FunctionDef = expect_instance(value=tree.body[0], kind=FunctionDef)
    second: FunctionDef = expect_instance(value=tree.body[1], kind=FunctionDef)
    moved: Assign = expect_instance(value=first.body.pop(0), kind=Assign)
    old_id: int = semantic.identities.node_id(node=moved)
    second.body.insert(0, moved)
    events: tuple[MutationEvent, ...] = semantic.refresh()
    expect_equal(
        actual=semantic.identities.node_id(node=moved),
        expected=old_id,
    )
    expect_true(
        condition=any(event.kind == "NODE_REPARENTED" for event in events),
    )
    expect_equal(
        actual=semantic.scopes.node_scopes[
            semantic.identities.node_id(node=moved.targets[0])
        ],
        expected=semantic.identities.node_id(node=second),
    )


def test_alias_reference_identity() -> None:
    """Must-alias and may-alias reflect the abstract heap, not Python id()."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
a=[1]
b=a
c=[2]
x=a[0]
y=b[0]
"""
        ),
    )
    semantic: SemanticAnalyzer = tree.semantic
    left_index: Subscript = expect_instance(
        value=expression_of_stmt(value=tree.body[3]),
        kind=Subscript,
    )
    right_index: Subscript = expect_instance(
        value=expression_of_stmt(value=tree.body[4]),
        kind=Subscript,
    )
    left: Name = expect_instance(value=left_index.value, kind=Name)
    right: Name = expect_instance(value=right_index.value, kind=Name)
    expect_true(condition=semantic.may_alias(a=left, b=right))
    expect_true(condition=semantic.must_alias(a=left, b=right))
    expect_equal(
        actual=semantic.points_to(node=left),
        expected=semantic.points_to(node=right),
    )


def test_basic_references_and_definitions() -> None:
    """Individual read and write nodes are reverse-indexed by symbol."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1
y=x+2
z=x*3
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    symbol: Symbol | None = semantic.resolve(name="x")
    symbol = expect_not_none(value=symbol)
    expect_equal(
        actual=len(semantic.references(symbol_id=symbol.id)),
        expected=2,
    )
    expect_equal(
        actual=len(semantic.definitions(symbol_id=symbol.id)),
        expected=1,
    )
    expect_equal(
        actual=len(semantic.bindings(symbol_id=symbol.id)),
        expected=1,
    )
    node: AST = semantic.references(symbol_id=symbol.id)[0]
    expect_equal(actual=semantic.symbol(node=node), expected=symbol)
    expect_true(condition=bool(semantic.dependencies(node=node)))
    expect_true(
        condition=bool(
            semantic.dependents(
                node=semantic.definitions(symbol_id=symbol.id)[0],
            ),
        ),
    )


def test_function_context_separation() -> None:
    """One function called with different arguments stays context sensitive."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
def double(x):
 return x*2
a=double(3)
b=double(7)
"""
        ),
    )
    semantic: SemanticAnalyzer = tree.semantic
    expect_equal(actual=tree.infer(node="a"), expected=LiteralValue(value=6))
    expect_equal(actual=tree.infer(node="b"), expected=LiteralValue(value=14))
    first: Call = expect_instance(
        value=expression_of_stmt(value=tree.body[1]),
        kind=Call,
    )
    expect_equal(
        actual=semantic.infer_call(node=first).value,
        expected=LiteralValue(value=6),
    )
    expect_true(condition=bool(semantic.explain(node=first)))


def test_identity_not_copied_from_deepcopy() -> None:
    """Cloned syntax nodes must receive new IDs despite copied attributes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    original: stmt = tree.body[0]
    duplicate: stmt = deepcopy(x=original)
    tree.body.append(duplicate)
    semantic.refresh()
    expect_not_equal(
        actual=semantic.identities.node_id(node=original),
        unexpected=semantic.identities.node_id(node=duplicate),
    )


def test_custom_analysis_budgets() -> None:
    """Restricted recursion budgets produce a safe approximation."""
    root: Module = expect_instance(
        value=parse(
            source=(
                """\
def f(x):
 if x==0:
  return 1
 return x*f(x-1)
y=f(4)
"""
            ),
        ),
        kind=Module,
    )
    semantic: SemanticAnalyzer = SemanticAnalyzer(
        root=root,
        budgets=AnalysisBudgets(max_recursion=2),
    )
    expect_instance(value=semantic.infer(node="y").value, kind=UnknownValue)


def test_cfg_integrity() -> None:
    """Every control-flow edge must point to a real block."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
x=0
while unknown:
 if x:
  break
 else:
  continue
"""
        ),
    )
    cfg: ControlFlowGraph = tree.semantic.cfg()
    expect_in(item=cfg.entry_id, container=cfg.blocks)
    expect_in(item=cfg.exit_id, container=cfg.blocks)
    expect_in(item=cfg.exception_id, container=cfg.blocks)
    expect_true(
        condition=all(
            edge.target in cfg.blocks
            for block in cfg.blocks.values()
            for edge in block.successors
        ),
    )


def test_direct_graph_and_lattice() -> None:
    """Dependency cycles terminate and abstract joins remain bounded."""
    graph: DependencyGraph = DependencyGraph()
    graph.add(consumer=2, producer=1, kind="DEPENDS_ON_VALUE")
    graph.add(consumer=3, producer=2, kind="DEPENDS_ON_VALUE")
    graph.add(consumer=1, producer=3, kind="DEPENDS_ON_CONTROL")
    expect_equal(
        actual=graph.affected_by(node_id=1),
        expected=frozenset({1, 2, 3}),
    )
    expect_equal(actual=len(graph.dependencies(node_id=2)), expected=1)
    expect_equal(actual=len(graph.dependents(node_id=2)), expected=1)
    expect_equal(
        actual=join_values(
            left=NeverValue(),
            right=LiteralValue(value=1),
        ),
        expected=LiteralValue(value=1),
    )
    expect_instance(
        value=join_values(
            left=LiteralValue(value=1),
            right=LiteralValue(value=2),
        ),
        kind=UnionValue,
    )
    expect_instance(
        value=join_values(left=LiteralValue(value=1), right=UnknownValue()),
        kind=UnknownValue,
    )
    expect_is(
        actual=truth_value(value=SequenceValue(elements=())),
        expected=False,
    )
    expect_equal(
        actual=proof_status(value=UnboundValue()),
        expected="approximate",
    )


def test_identity_index_node_reuse() -> None:
    """Per-module syntax identities remain stable over repeated lookups."""
    index: IdentityIndex = IdentityIndex()
    source: Module = expect_instance(
        value=parse(
            source="""\
x=1
""",
        ),
        kind=Module,
    )
    node: AST = source.body[0]
    expect_equal(
        actual=index.node_id(node=node),
        expected=index.node_id(node=node),
    )
    expect_in(item=node, container=index.all_nodes())


def test_abstract_heap_mutation_and_aliasing() -> None:
    """Abstract mutation never touches runtime values or calls methods."""
    heap: AbstractHeap = AbstractHeap()
    first: ObjectReference = heap.allocate(
        node_id=1,
        context_id=0,
        kind="list",
        elements=(LiteralValue(value=1),),
    )
    expect_true(condition=heap.must_alias(left=first, right=first))
    expect_true(condition=heap.may_alias(left=first, right=first))
    expect_equal(
        actual=heap.read_index(
            reference=first,
            index=LiteralValue(value=0),
            objects=heap.objects,
        ),
        expected=LiteralValue(value=1),
    )
    heap.write_index(
        reference=first,
        index=LiteralValue(value=0),
        value=LiteralValue(value=4),
        objects=heap.objects,
    )
    expect_equal(
        actual=heap.read_index(
            reference=first,
            index=LiteralValue(value=0),
            objects=heap.objects,
        ),
        expected=LiteralValue(value=4),
    )
    heap.havoc(reference=first, objects=heap.objects)
    expect_instance(
        value=heap.read_index(
            reference=first,
            index=LiteralValue(value=0),
            objects=heap.objects,
        ),
        kind=UnknownValue,
    )
    heap.allocate(
        node_id=1,
        context_id=0,
        kind="list",
        elements=(LiteralValue(value=2),),
    )
    expect_false(condition=heap.must_alias(left=first, right=first))


def test_mutable_ast_compiles_unchanged() -> None:
    """Semantic metadata does not break standard Python AST compilation."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1
y=x+2
""",
    )
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=3))
    compile(source=tree, filename="<semantic-test>", mode="exec")


def test_definite_exception_is_not_unknown_normal_value() -> None:
    """Proven arithmetic failure becomes an exceptional control-flow exit."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1/0
y=3
""",
    )
    expression: expr = expression_of_stmt(value=tree.body[0])
    expect_instance(
        value=tree.semantic.infer_node(node=expression).value,
        kind=ErrorValue,
    )
    expect_equal(
        actual=tree.semantic.infer_node(node=expression).status,
        expected="error",
    )
    expect_instance(value=tree.infer(node="y"), kind=UnboundValue)
