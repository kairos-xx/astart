"""Advanced semantic regression tests for statements, scopes and fallbacks."""

from __future__ import annotations

from ast import Assign, Constant, Name, parse
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.ast import CommentedModule
from astart.semantic import (
    AbstractHeap,
    AnalysisBudgets,
    ErrorValue,
    HeapObject,
    LiteralValue,
    SemanticAnalyzer,
    UnboundValue,
    UnionValue,
    UnknownValue,
)
from astart.semantic.evaluator import State
from astart.semantic.values import (
    AbstractValue,
    MappingValue,
    NeverValue,
    SymbolicValue,
    join_values,
    proof_status,
    truth_value,
)

from tests.expectations import (
    expect_constant_expr,
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_not_in,
    expect_not_none,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.semantic.control_flow import ControlFlowGraph
    from astart.semantic.evaluator import AbstractInterpreter
    from astart.semantic.identities import Symbol
    from astart.semantic.values import ObjectReference


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        (
            """\
x=0
while False:
 x=1
else:
 x=3
""",
            "x",
            3,
        ),
        (
            """\
x=0
while x<3:
 x+=1
else:
 x+=10
""",
            "x",
            13,
        ),
        (
            """\
x=0
while True:
 x=2
 break
else:
 x=3
""",
            "x",
            2,
        ),
        (
            """\
x=0
for i in range(0):
 x=1
else:
 x=3
""",
            "x",
            3,
        ),
        (
            """\
x=0
for i in range(2):
 x=i
else:
 x=3
""",
            "x",
            3,
        ),
        (
            """\
x=0
for i in range(2):
 break
else:
 x=3
""",
            "x",
            0,
        ),
        (
            """\
x=0
for i in range(2):
 if i==0:
  continue
 x=i
""",
            "x",
            1,
        ),
        (
            """\
x=0
for i in [1,2,3]:
 x+=i
""",
            "x",
            6,
        ),
        (
            """\
x=0
for i in (1,2,3):
 x+=i
""",
            "x",
            6,
        ),
        (
            """\
x=0
for i in range(3):
 x+=i
""",
            "x",
            3,
        ),
        (
            """\
x=4
assert True
y=x
""",
            "y",
            4,
        ),
        (
            """\
x=1
pass
y=x
""",
            "y",
            1,
        ),
        (
            """\
x=1
del x
x=5
y=x
""",
            "y",
            5,
        ),
        (
            """\
x=0
x=(y:=4)
z=y
""",
            "z",
            4,
        ),
        (
            """\
x=0
match 2:
 case 1:
  x=11
 case 2:
  x=22
 case _:
  x=33
""",
            "x",
            22,
        ),
        (
            """\
x=0
match 4:
 case 1|2:
  x=11
 case 4:
  x=44
""",
            "x",
            44,
        ),
        (
            """\
x=0
match (1,2):
 case (a,b):
  x=a+b
 case _:
  x=-1
""",
            "x",
            3,
        ),
        (
            (
                """\
x=0
match (1,2,3):
 case (a,*middle,z):
  x=a+z
 case _:
  x=-1
"""
            ),
            "x",
            4,
        ),
        (
            """\
x=0
match 4:
 case n if n>3:
  x=n
 case _:
  x=-1
""",
            "x",
            4,
        ),
        (
            """\
x=0
match None:
 case None:
  x=5
 case _:
  x=0
""",
            "x",
            5,
        ),
        (
            """\
x=0
match (1,2,3):
 case (a,b):
  x=10
 case _:
  x=7
""",
            "x",
            7,
        ),
        (
            """\
x=0
match 10:
 case 1 | 2:
  x=1
 case _:
  x=8
""",
            "x",
            8,
        ),
        (
            """\
x=0
match 2:
 case a as b:
  x=b
""",
            "x",
            2,
        ),
        (
            (
                """\
x=1
def change():
 global x
 x=9
 return x
y=change()
z=x
"""
            ),
            "z",
            9,
        ),
        (
            (
                """\
def outer():
 x=1
 def inner():
  nonlocal x
  x=7
 inner()
 return x
y=outer()
"""
            ),
            "y",
            7,
        ),
        (
            """\
x=1
def f():
 return x
y=f()
""",
            "y",
            1,
        ),
        (
            """\
def f(*args):
 return args[0]
y=f(3,4)
""",
            "y",
            3,
        ),
        (
            """\
def f(a,b):
 return a+b
y=f(b=3,a=4)
""",
            "y",
            7,
        ),
        (
            """\
def f(a):
 return a
y=f(a=4)
""",
            "y",
            4,
        ),
        (
            """\
x=[1,2]
y=x.pop()
z=x[0]
""",
            "z",
            1,
        ),
        (
            """\
x=[1,2]
x.clear()
y=len((1,))
""",
            "y",
            1,
        ),
        (
            """\
x=[1]
y=x[0]
x[0]=2
z=x[0]
""",
            "z",
            2,
        ),
        (
            """\
x={'a':1}
x['a']=3
y=x['a']
""",
            "y",
            3,
        ),
        (
            """\
x='abc'
y=len(x)
""",
            "y",
            3,
        ),
        (
            """\
x='a'*3
""",
            "x",
            "aaa",
        ),
        (
            """\
x=b'a'*3
""",
            "x",
            b"aaa",
        ),
        (
            """\
x=f'{1+2:04d}'
""",
            "x",
            "0003",
        ),
        (
            """\
x=f'{3!s}'
""",
            "x",
            "3",
        ),
        (
            """\
x=f'{3!a}'
""",
            "x",
            "3",
        ),
        (
            """\
x=f'{7:>{3}}'
""",
            "x",
            "  7",
        ),
        (
            """\
x=(not False)
""",
            "x",
            True,
        ),
        (
            """\
x=(1==1 and 2==2)
""",
            "x",
            True,
        ),
        (
            """\
x=(1==2 or 2==2)
""",
            "x",
            True,
        ),
        (
            """\
x=(1<2<3)
""",
            "x",
            True,
        ),
        (
            """\
x=(1<2>3)
""",
            "x",
            False,
        ),
    ],
)
def test_advanced_known_values(
    *,
    source: str,
    name: str,
    expected: int | bool | bytes | str,
) -> None:
    """Safely infer known values in advanced supported syntax.

    Args:
        expected: Expected supplied as int | bool | bytes | str for this
            operation.
        name: Identifier of the name being resolved.
        source: The source examined while safely infer known values in
            advanced supported syntax.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node=name),
        expected=LiteralValue(value=expected),
    )


@pytest.mark.parametrize(
    ("source", "name"),
    [
        (
            """\
x=unknown if mystery else 4
""",
            "x",
        ),
        (
            """\
x=(unknown and 4)
""",
            "x",
        ),
        (
            """\
x=1<unknown
""",
            "x",
        ),
        (
            """\
x='a'+1
""",
            "x",
        ),
        (
            """\
x=[1]
x.unknown_method()
y=x[0]
""",
            "y",
        ),
        (
            """\
x=[1]
y=other(x)
z=x[0]
""",
            "z",
        ),
        (
            """\
x=[1]
y=x[unknown]
""",
            "y",
        ),
        (
            """\
x=[1]
x[unknown]=2
y=x[0]
""",
            "y",
        ),
        (
            """\
x=[1]
y=x.pop(unknown)
""",
            "y",
        ),
        (
            """\
x=[1]
y=x.pop(99)
""",
            "y",
        ),
        (
            """\
x=[1]
y=x.append()
""",
            "y",
        ),
        (
            """\
x=[1]
y=x.extend(unknown)
""",
            "y",
        ),
        (
            """\
x=unknown and 3
""",
            "x",
        ),
        (
            """\
x=1 if unknown else 2
""",
            "x",
        ),
        (
            """\
x={1:2}
y=x[unknown]
""",
            "y",
        ),
        (
            """\
x=(1,2)[99]
y=2
""",
            "x",
        ),
        (
            """\
x=3
match x:
 case SomeClass():
  y=1
""",
            "y",
        ),
        (
            """\
x=1
from os import path as p
y=p
""",
            "y",
        ),
        (
            """\
x=[1]
y=unsafe(x)
z=x[0]
""",
            "z",
        ),
    ],
)
def test_advanced_unknowns(*, source: str, name: str) -> None:
    """Unsupported operations return conservative abstractions.

    Args:
        name: Identifier of the name being resolved.
        source: The source examined while unsupported operations return
            conservative abstractions.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: AbstractValue = tree.infer(node=name)
    expect_true(
        condition=isinstance(
            result,
            (UnknownValue, UnionValue, UnboundValue, ErrorValue),
        ),
    )


def test_heap_state_join_paths() -> None:
    """Join abstract heap alternatives without unsound strong updates."""
    first: State = State(
        values={1: LiteralValue(value=2)},
        heap={
            1: HeapObject(
                id=1,
                kind="list",
                elements=(LiteralValue(value=1),),
            ),
        },
    )
    second: State = State(
        values={1: LiteralValue(value=4)},
        heap={
            1: HeapObject(
                id=1,
                kind="list",
                elements=(LiteralValue(value=3),),
            ),
        },
    )
    merged: State = first.merge(other=second, limit=4)
    expect_instance(value=merged.values[1], kind=UnionValue)
    expect_instance(value=merged.heap[1].elements[0], kind=UnionValue)
    one_sided: State = State().merge(other=second, limit=4)
    expect_true(condition=one_sided.heap[1].unknown_content)
    expect_is_not(actual=first.clone(), unexpected=first)


def test_heap_dict_and_weak_update() -> None:
    """Known map elements allow updates; summarized sites need weak writes."""
    heap: AbstractHeap = AbstractHeap()
    reference: ObjectReference = heap.allocate(
        node_id=1,
        context_id=1,
        kind="dict",
        attributes=((LiteralValue(value="k"), LiteralValue(value=1)),),
    )
    heap.write_index(
        reference=reference,
        index=LiteralValue(value="k"),
        value=LiteralValue(value=2),
        objects=heap.objects,
    )
    expect_equal(
        actual=heap.read_index(
            reference=reference,
            index=LiteralValue(value="k"),
            objects=heap.objects,
        ),
        expected=LiteralValue(value=2),
    )
    heap.allocate(node_id=1, context_id=1, kind="dict")
    heap.write_index(
        reference=reference,
        index=LiteralValue(value="k"),
        value=LiteralValue(value=3),
        objects=heap.objects,
    )
    expect_false(
        condition=heap.must_alias(left=reference, right=reference),
    )
    expect_false(
        condition=heap.may_alias(left=LiteralValue(value=1), right=reference),
    )


def test_scope_resolution_and_rename_rejections() -> None:
    """Renames reject keywords, collisions, and nested capture hazards."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
value=1
other=2
def f():
 return other + value
"""
        ),
    )
    semantic: SemanticAnalyzer = tree.semantic
    value: Symbol | None = semantic.resolve(name="value")
    value = expect_not_none(value=value)
    with pytest.raises(
        expected_exception=ValueError,
        match="valid non-keyword",
    ):
        semantic.rename(symbol_id=value.id, new_name="for")
    with pytest.raises(
        expected_exception=ValueError,
        match="collide with an existing",
    ):
        semantic.rename(symbol_id=value.id, new_name="other")
    expect_equal(
        actual=expect_not_none(value=tree.semantic.resolve(name="value")).id,
        expected=value.id,
    )


def test_rename_updates_global_declaration() -> None:
    """Moving a global symbol name rewrites its explicit global declaration."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
x=1
def f():
 global x
 x=2
 return x
y=f()
"""
        ),
    )
    semantic: SemanticAnalyzer = tree.semantic
    symbol: Symbol | None = semantic.resolve(name="x")
    symbol = expect_not_none(value=symbol)
    semantic.rename(symbol_id=symbol.id, new_name="price")
    expect_in(item="global price", container=tree.unparse())
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=2))


def test_cfg_advanced_edges() -> None:
    """Try, return, continue, match, and cleanup edges are inspectable."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            dedent(
                text="""\
    x=0
    try:
     with something as item:
      x=1
    except ValueError:
     x=2
    finally:
     x+=1
    match x:
     case 1:
      x=3
     case _:
      x=4
    """,
            )
        ),
    )
    graph: ControlFlowGraph = tree.semantic.cfg()
    labels: set[str] = {
        edge.kind
        for block in graph.blocks.values()
        for edge in block.successors
    }
    expect_true(
        condition={"next", "handler", "finally", "match", "exception"}
        <= labels,
    )


def test_cfg_function_scope() -> None:
    """Function-specific CFG excludes unrelated module-level statements."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
def f(x):
 if x:
  return 1
 return 2
y=f(True)
"""
        ),
    )
    graph: ControlFlowGraph = tree.semantic.cfg(scope=tree.body[0])
    expect_true(
        condition=any(
            edge.kind == "return"
            for block in graph.blocks.values()
            for edge in block.successors
        ),
    )
    with pytest.raises(expected_exception=TypeError):
        tree.semantic.cfg(scope=expression_of_stmt(value=tree.body[1]))


def test_infer_missing_symbol_or_node() -> None:
    """Unknown nodes and missing lexical names must not fabricate values."""
    semantic: SemanticAnalyzer = SemanticAnalyzer(
        root=parse(
            source="""\
x=1
""",
        ),
    )
    expect_instance(
        value=semantic.infer(node="missing").value,
        kind=UnknownValue,
    )
    expect_instance(
        value=semantic.infer_node(node=Name(id="foreign")).value,
        kind=UnknownValue,
    )
    expect_is(actual=semantic.resolve(name="nope"), expected=None)


def test_invalidations_are_limited_and_reset() -> None:
    """Unrelated module statements remain valid after a local literal edit."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+2
c=100
""",
    )
    semantic: SemanticAnalyzer = tree.semantic
    tree.infer(node="b")
    changed: Constant = expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    )
    third: Assign = expect_instance(value=tree.body[2], kind=Assign)
    expect_not_in(
        item=semantic.identities.node_id(node=third.targets[0]),
        container=semantic.affected_by(
            node=changed,
        ),
    )
    changed.value = 7
    expect_true(condition=bool(semantic.refresh()))
    expect_true(condition=bool(semantic.invalidated))
    expect_equal(actual=semantic.refresh(), expected=())
    expect_equal(actual=tree.infer(node="b"), expected=LiteralValue(value=9))
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=100))


def test_call_summary_effects() -> None:
    """Complete call summaries retain observable mutations to module state."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            dedent(
                text="""\
    total=1
    def increase():
     global total
     total+=1
     return total
    x=increase()
    y=total
    """,
            )
        ),
    )
    expect_equal(actual=tree.infer(node="x"), expected=LiteralValue(value=2))
    expect_equal(actual=tree.infer(node="y"), expected=LiteralValue(value=2))
    interpreter: AbstractInterpreter = tree.semantic.evaluate()
    expect_equal(actual=interpreter.summaries.size, expected=1)


def test_analysis_budgets_limit_unknown_calls() -> None:
    """A zero-context budget safely prevents entering any function body."""
    semantic: SemanticAnalyzer = SemanticAnalyzer(
        root=parse(
            source="""\
def f(x):
 return x+1
y=f(2)
""",
        ),
        budgets=AnalysisBudgets(max_contexts=0),
    )
    expect_instance(value=semantic.infer(node="y").value, kind=UnknownValue)


def test_value_lattice_edge_cases() -> None:
    """Widening and truth proofs are deterministic per value category."""
    expect_equal(
        actual=proof_status(value=NeverValue()),
        expected="unreachable",
    )
    expect_equal(
        actual=proof_status(value=SymbolicValue(expression="x + 2")),
        expected="approximate",
    )
    expect_is(
        actual=truth_value(value=MappingValue(entries=())),
        expected=False,
    )
    expect_is(
        actual=truth_value(
            value=UnionValue(
                options=(LiteralValue(value=0), LiteralValue(value=1)),
            ),
        ),
        expected=None,
    )
    expect_instance(
        value=join_values(
            left=UnionValue(
                options=(LiteralValue(value=1), LiteralValue(value=2)),
            ),
            right=LiteralValue(value=3),
            limit=2,
        ),
        kind=UnknownValue,
    )


def test_unknown_external_call_havocs_heap() -> None:
    """Unknown methods and callees invalidate mutable abstract contents."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
values=[3]
call_external(values)
result=values[0]
"""
        ),
    )
    expect_instance(value=tree.infer(node="result"), kind=UnknownValue)
