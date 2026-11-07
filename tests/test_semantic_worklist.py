"""Differential and deletion-sensitive worklist/regression tests."""

from __future__ import annotations

from ast import Assign, BinOp, Name, expr, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.ast import CommentedModule
from astart.semantic.values import (
    CoroutineValue,
    GeneratorValue,
    LiteralValue,
    UnknownValue,
)
from astart.semantic.worklist import IncrementalWorklist

from tests.expectations import (
    expect_binary_expr,
    expect_constant_expr,
    expect_equal,
    expect_in,
    expect_instance,
    expect_is_not,
    expect_not_none,
    expect_suite_node,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.semantic.identities import Symbol
    from astart.semantic.worklist import SolveStatistics


@final
class Constants:
    """Group module-level constants.

    Attributes:
        branch_identity: Grouped module constant.

    """

    branch_identity: Final[int] = 2


def test_reaching_worklist_deletion_and_fixed_point() -> None:
    """A removed producer must retract its facts from every descendant."""
    assignments: dict[int, int] = {1: 10, 2: 20}

    def transfer(
        identity: int,
        incoming: dict[int, frozenset[int]],
    ) -> dict[int, frozenset[int]]:
        """Replace the definition at a designated assignment block.

        Args:
            identity: Identity supplied as int for this operation.
            incoming: Incoming supplied as dict[int, frozenset[int]] for
                this operation.

        Returns:
            dict[int, frozenset[int]] produced by this operation.

        """
        result: dict[int, frozenset[int]] = dict(incoming)
        if identity in assignments:
            result[1] = frozenset({assignments[identity]})
        return result

    solver: IncrementalWorklist = IncrementalWorklist(
        successors={1: (2,), 2: (3,), 3: ()},
        entry=1,
        transfer=transfer,
    )
    expect_true(condition=solver.solve().converged)
    expect_equal(actual=solver.incoming[3][1], expected=frozenset({20}))
    del assignments[2]
    result: SolveStatistics = solver.solve(dirty=frozenset({2}))
    expect_true(condition=result.converged)
    expect_equal(actual=result.visited, expected=frozenset({2, 3}))
    expect_equal(actual=solver.incoming[3][1], expected=frozenset({10}))
    expect_equal(
        actual=solver.solve(dirty=frozenset({2})).changed,
        expected=frozenset(),
    )


def test_worklist_graph_edge_retraction() -> None:
    """Updating an edge must remove a path's old reachable facts."""
    solver: IncrementalWorklist = IncrementalWorklist(
        successors={1: (2, 3), 2: (3,), 3: ()},
        entry=1,
        transfer=lambda identity, incoming: (
            incoming | {1: frozenset({identity})}
            if identity == Constants.branch_identity
            else incoming
        ),
    )
    expect_true(condition=solver.solve().converged)
    expect_equal(actual=solver.incoming[3].get(1), expected=frozenset({2}))
    expect_true(
        condition=solver.update_graph(
            successors={1: (3,), 2: (), 3: ()},
        ).converged,
    )
    expect_equal(
        actual=solver.incoming[3].get(1, frozenset()),
        expected=frozenset(),
    )


def test_incremental_value_solver_differential() -> None:
    """An edited source and a fresh parse infer identical abstract results."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+2
c=b*2
d=100
""",
    )
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=6))
    statement: Assign = expect_instance(value=tree.body[0], kind=Assign)
    expect_constant_expr(value=statement.value).value = 4
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=12))
    expect_true(condition=bool(tree.semantic.incremental_statements))
    baseline: CommentedModule = CommentedModule.parse(
        source="""\
a=4
b=a+2
c=b*2
d=100
""",
    )
    expect_equal(
        actual=tree.infer(node="c"),
        expected=baseline.infer(node="c"),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
x=0
try:
 x=2
except ValueError:
 x=8
""",
            2,
        ),
        (
            """\
x=0
try:
 x=1/0
except ZeroDivisionError:
 x=8
""",
            8,
        ),
        (
            """\
x=0
try:
 x=2
finally:
 x=4
""",
            4,
        ),
        (
            """\
def f():
 try:
  return 3
 finally:
  return 4
x=f()
""",
            4,
        ),
        (
            """\
def f():
 try:
  return 3
 finally:
  y=4
x=f()
""",
            3,
        ),
        (
            """\
x=0
try:
 raise ValueError()
except ValueError:
 x=5
""",
            5,
        ),
    ],
)
def test_precise_try_paths(*, source: str, expected: int) -> None:
    """Handlers run only on exceptional paths; finally overrides exits.

    Args:
        expected: Expected supplied as int for this operation.
        source: The source examined while handlers run only on exceptional
            paths; finally overrides exits.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node="x"),
        expected=LiteralValue(value=expected),
    )


def test_cycle_retraction_reaches_least_fixed_point() -> None:
    """Removing a cyclic fact producer must not retain self-supported facts."""
    enabled: dict[str, bool] = {"producer": True}

    def transfer(
        identity: int,
        incoming: dict[int, frozenset[int]],
    ) -> dict[int, frozenset[int]]:
        """Add one optional fact on entry into a cycle.

        Args:
            identity: Identity supplied as int for this operation.
            incoming: Incoming supplied as dict[int, frozenset[int]] for
                this operation.

        Returns:
            dict[int, frozenset[int]] produced by this operation.

        """
        return (
            incoming | {1: frozenset({3})}
            if identity == 1 and enabled["producer"]
            else incoming
        )

    solver: IncrementalWorklist = IncrementalWorklist(
        successors={1: (2,), 2: (3,), 3: (2,)},
        entry=1,
        transfer=transfer,
    )
    expect_true(condition=solver.solve().converged)
    expect_equal(actual=solver.incoming[3][1], expected=frozenset({3}))
    enabled["producer"] = False
    expect_true(condition=solver.solve(dirty=frozenset({1})).converged)
    expect_equal(
        actual=solver.incoming[3].get(1, frozenset()),
        expected=frozenset(),
    )


def test_async_function_deferred_until_awaited() -> None:
    """Coroutine creation does not run its body; await may infer a result."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
async def f(value):
 return value+2
result=f(3)
""",
    )
    expect_instance(value=tree.infer(node="result"), kind=CoroutineValue)
    expect_equal(
        actual=tree.semantic.infer_await(node="result").value,
        expected=LiteralValue(value=5),
    )


def test_generator_deferred_before_iteration() -> None:
    """Generator creation must not eagerly execute a yielding function body."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
 yield 1
value=f()
""",
    )
    expect_instance(value=tree.infer(node="value"), kind=GeneratorValue)


def test_incremental_skips_pure_unrelated_statement() -> None:
    """Unchanged independent assignments reuse transfer results."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a+3
c=b+5
d=100
""",
    )
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=9))
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 2
    expect_equal(actual=tree.infer(node="c"), expected=LiteralValue(value=10))
    expect_is_not(actual=tree.semantic.interpreter, unexpected=None)
    expect_equal(
        actual=expect_not_none(
            value=tree.semantic.interpreter,
        ).incremental_reused,
        expected=(tree.semantic.identities.node_id(node=tree.body[3]),),
    )


@pytest.mark.parametrize(
    ("source", "symbol_name", "kind"),
    [
        (
            """\
def transform[T](value: T) -> T:
 return value
""",
            "T",
            "type_parameter",
        ),
        (
            """\
type Collection[T] = list[T]
""",
            "T",
            "type_parameter",
        ),
        (
            """\
class Holder[T]:
 value: T
""",
            "T",
            "type_parameter",
        ),
    ],
)
def test_generic_annotation_scope(
    *,
    source: str,
    symbol_name: str,
    kind: str,
) -> None:
    """PEP 695 symbols resolve in annotation scopes, not as function locals.

    Args:
        kind: Kind supplied as str for this operation.
        source: The source examined while pEP 695 symbols resolve in
            annotation scopes, not as function locals.
        symbol_name: Identifier of the symbol being resolved.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    references: list[Name] = [
        node
        for node in walk(node=tree)
        if isinstance(node, Name) and node.id == symbol_name
    ]
    expect_true(condition=bool(references))
    symbols: list[Symbol | None] = [
        tree.semantic.symbol(node=reference) for reference in references
    ]
    expect_true(
        condition=all(
            symbol is not None and symbol.kind == kind for symbol in symbols
        ),
    )
    expect_equal(
        actual=len({symbol.id for symbol in symbols if symbol is not None}),
        expected=1,
    )


def test_nested_function_error_reaches_handler() -> None:
    """A proven exception from a local call selects the matching handler."""
    source: str = dedent(
        text=(
            """\
    def failure():
     raise ValueError()
    try:
     failure()
    except ValueError:
     result=42
    """
        ),
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node="result"),
        expected=LiteralValue(value=42),
    )


def test_async_unknown_awaitable_is_conservative() -> None:
    """Unknown external awaitables are never treated as safe exact values."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
async def task():
 return await external()
result=task()
""",
    )
    expect_instance(
        value=tree.semantic.infer_await(node="result").value,
        kind=UnknownValue,
    )


def test_async_generator_is_not_awaitable_coroutine() -> None:
    """An async generator creation yields a deferred asynchronous iterator."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
async def stream():
 yield 1
result=stream()
""",
    )
    expect_instance(value=tree.infer(node="result"), kind=GeneratorValue)
    expect_instance(
        value=tree.semantic.infer_await(node="result").value,
        kind=UnknownValue,
    )


@pytest.mark.parametrize("value", range(-20, 101))
def test_incremental_equivalent_to_fresh_for_nested_dependencies(
    *,
    value: int,
) -> None:
    """Repeated edits must agree with independent whole-tree analysis.

    Args:
        value: The value examined while repeated edits must agree with
            independent whole-tree analysis.

    """
    source: str = """\
seed=0
b=seed+3
c=b*4
d=100
e=c+d
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=tree.infer(node="e"), expected=LiteralValue(value=112))
    for number in (value, value + 1, value - 1):
        expect_constant_expr(
            value=expression_of_stmt(value=tree.body[0]),
        ).value = number
        fresh: CommentedModule = CommentedModule.parse(
            source=(
                f"""\
seed={number}
b=seed+3
c=b*4
d=100
e=c+d
"""
            ),
        )
        expect_equal(
            actual=tree.infer(node="e"),
            expected=fresh.infer(node="e"),
        )
        expect_equal(
            actual=tree.infer(node="d"),
            expected=LiteralValue(value=100),
        )


@pytest.mark.parametrize("replacement", range(-12, 25))
def test_function_edit_reuses_unaffected_module_transfer(
    *,
    replacement: int,
) -> None:
    """An internal edit invalidates its callers but not unrelated literals.

    Args:
        replacement: Replacement supplied as int for this operation.

    """
    source: str = """\
def calculate(x):
 return x+1
value=calculate(4)
independent=100
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node="value"),
        expected=LiteralValue(value=5),
    )
    expect_constant_expr(
        value=expect_binary_expr(
            value=expression_of_stmt(
                value=expect_suite_node(value=tree.body[0]).body[0],
            ),
        ).right,
    ).value = replacement
    expect_equal(
        actual=tree.infer(node="value"),
        expected=LiteralValue(value=4 + replacement),
    )
    fresh: CommentedModule = CommentedModule.parse(
        source=(
            f"""\
def calculate(x):
 return x+{replacement}
value=calculate(4)
independent=100
"""
        ),
    )
    expect_equal(
        actual=tree.infer(node="value"),
        expected=fresh.infer(node="value"),
    )
    if replacement == 1:
        expect_equal(actual=tree.semantic.incremental_statements, expected=())
        return
    expect_true(condition=bool(tree.semantic.incremental_statements))
    expect_is_not(actual=tree.semantic.interpreter, unexpected=None)
    expect_in(
        item=tree.semantic.identities.node_id(node=tree.body[2]),
        container=expect_not_none(
            value=tree.semantic.interpreter,
        ).incremental_reused,
    )


def test_nested_wrapper_function_invalidation() -> None:
    """Calls through a wrapper must reflect an edited callee's body."""
    source: str = dedent(
        text=(
            """\
    def base(n):
     return n+1
    def wrapper(n):
     return base(n)
    result=wrapper(3)
    unrelated=99
    """
        ),
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.infer(node="result"),
        expected=LiteralValue(value=4),
    )
    expect_constant_expr(
        value=expect_binary_expr(
            value=expression_of_stmt(
                value=expect_suite_node(value=tree.body[0]).body[0],
            ),
        ).right,
    ).value = 9
    expect_equal(
        actual=tree.infer(node="result"),
        expected=LiteralValue(value=12),
    )
    expect_equal(
        actual=tree.infer(node="unrelated"),
        expected=LiteralValue(value=99),
    )


def test_incremental_function_proof_does_not_contain_prior_revision() -> None:
    """Expression proof caches must not join stale values across revisions."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
 return x+1
value=f(2)
""",
    )
    expression: BinOp = expect_binary_expr(
        value=expression_of_stmt(
            value=expect_suite_node(value=tree.body[0]).body[0],
        ),
    )
    expect_equal(
        actual=tree.infer(node="value"),
        expected=LiteralValue(value=3),
    )
    expect_equal(
        actual=tree.semantic.infer_node(node=expression).value,
        expected=LiteralValue(value=3),
    )
    expect_constant_expr(value=expression.right).value = 5
    expect_equal(
        actual=tree.infer(node="value"),
        expected=LiteralValue(value=7),
    )
    expect_equal(
        actual=tree.semantic.infer_node(node=expression).value,
        expected=LiteralValue(value=7),
    )


def test_incremental_function_global_read_is_refreshed() -> None:
    """Changed globals must update cached function-body read proofs."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
global_value=2
def f():
 return global_value
result=f()
""",
    )
    reference: expr = expression_of_stmt(
        value=expect_suite_node(value=tree.body[1]).body[0],
    )
    expect_equal(
        actual=tree.infer(node="result"),
        expected=LiteralValue(value=2),
    )
    expect_equal(
        actual=tree.semantic.infer_node(node=reference).value,
        expected=LiteralValue(value=2),
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 8
    expect_equal(
        actual=tree.infer(node="result"),
        expected=LiteralValue(value=8),
    )
    expect_equal(
        actual=tree.semantic.infer_node(node=reference).value,
        expected=LiteralValue(value=8),
    )
