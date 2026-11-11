"""Regression tests for bidirectional, provenance-carrying type inference."""

from __future__ import annotations

from ast import Attribute, Call, Load, Name, arg, walk
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.semantic import TypeShape, join_types
from astart.semantic.type_inference import (
    TypeBudgets,
    TypeConstraintSolver,
)
from astart.semantic.values import LiteralValue
from astart.source.ast import CommentedModule

from tests.support.expectations import (
    expect_constant_expr,
    expect_elements_expr,
    expect_equal,
    expect_false,
    expect_function_node,
    expect_instance,
    expect_is,
    expect_not_none,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.semantic.type_inference import TypeInference


@final
class Constants:
    """Group module-level constants.

    Attributes:
        min_evidence_items (Final[int]): Grouped module constant.

    """

    min_evidence_items: Final[int] = 4


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        ("a = [1]", "a", "list[int]"),
        (
            """\
a = [1]
a += ['c']""",
            "a",
            "list[int | str]",
        ),
        (
            """\
a = [1]
a += ['c']
a += [0.1]""",
            "a",
            "list[float | str]",
        ),
        ("b: dict[str, int] = {}", "b", "dict[str, int]"),
        (
            """\
a = [1]
a.append('x')""",
            "a",
            "list[int | str]",
        ),
        (
            """\
a = [1]
a.extend([2.0])""",
            "a",
            "list[float]",
        ),
        (
            """\
def identity(x):
    return x
a = identity(5)""",
            "a",
            "int",
        ),
        (
            """\
def identity(x):
    return x
a = identity('abc')""",
            "a",
            "str",
        ),
        (
            """\
def identity(x):
    return x
a: float = identity(3)""",
            "a",
            "float",
        ),
        (
            """\
a = 0
a = 1.0""",
            "a",
            "float",
        ),
        ("a = {'a': 2}", "a", "dict[str, int]"),
        ("a = True if flag else 2", "a", "int"),
        ("a = (1, 'a')", "a", "tuple[int | str]"),
        ("a = set([1])", "a", "set[int]"),
        (
            """\
d = {'a': 1}
a = list(d)""",
            "a",
            "list[str]",
        ),
        (
            """\
d = {'a': 1}
a = set(d)""",
            "a",
            "set[str]",
        ),
        (
            """\
d = {'a': 1}
a = dict(d)""",
            "a",
            "dict[str, int]",
        ),
        ("a = list('ab')", "a", "list[str]"),
        ("a = list(b'ab')", "a", "list[int]"),
        (
            """\
a = 'abc'
b = a[0]""",
            "b",
            "str",
        ),
        (
            """\
a = b'ab'
b = a[0]""",
            "b",
            "int",
        ),
    ],
)
def test_inferred_type_examples(
    *,
    source: str,
    name: str,
    expected: str,
) -> None:
    """Infer stable generic types and numeric promotions.

    Args:
        expected (str): Expected supplied as str for this operation.
        name (str): Identifier of the name being resolved.
        source (str): The source examined while infer stable generic types and
            numeric promotions.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=str(object=tree.infer_type(node=name).inferred),
        expected=expected,
    )


def test_multi_step_sequence_and_narrowing() -> None:
    """Recognize each stage of a heterogeneous list mutation."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
a = [1]
a += ["c"]
a += [0.1]
b: dict[str, int] = {}
a += [b]
d = c if isinstance(c:=a[-1], dict) else {"e":0}
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[dict[str, int] | float | str]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="d").inferred),
        expected="dict[str, int]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="c").inferred),
        expected="dict[str, int] | float | str",
    )
    expect_true(
        condition=len(tree.infer_type(node="a").evidence)
        >= Constants.min_evidence_items,
    )
    expect_equal(
        actual=tree.infer_type(node="b").declared,
        expected=TypeShape(
            name="dict",
            arguments=(TypeShape(name="str"), TypeShape(name="int")),
        ),
    )
    expect_true(condition=tree.semantic.types.statistics.converged)


def test_backward_return_contract() -> None:
    """Backpropagate a declared return type to a direct parameter return."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def source(x) -> int:
    return x
""",
    )
    parameter: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    expect_equal(
        actual=str(object=tree.infer_type(node=parameter).inferred),
        expected="int",
    )
    expect_true(
        condition=any(
            item.kind == "backward_contract"
            for item in tree.infer_type(node=parameter).evidence
        ),
    )


def test_backward_caller_contract() -> None:
    """Infer a callee's output and input from a caller annotation."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def identity(x):
    return x
r: str = identity(q)
""",
    )
    expect_equal(
        actual=str(
            object=tree.infer_type(
                node=expect_function_node(value=tree.body[0]).args.args[0],
            ).inferred,
        ),
        expected="str",
    )


def test_recompute_after_mutation() -> None:
    """Replace obsolete facts after mutation instead of keeping stale ones."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = [1]
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[int]",
    )
    expect_constant_expr(
        value=expect_elements_expr(
            value=expression_of_stmt(value=tree.body[0]),
        ).elts[0],
    ).value = "new"
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[str]",
    )


def test_node_metadata_and_values() -> None:
    """Provide type evidence and causal value evidence on executable nodes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = 10
b = a + 1
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="int",
    )
    expect_equal(actual=tree.infer(node="b"), expected=LiteralValue(value=11))
    names: list[Name] = [
        node for node in walk(node=tree) if isinstance(node, Name)
    ]
    expect_true(
        condition=any(getattr(node, "type_evidence", ()) for node in names),
    )
    expect_true(
        condition=any(
            getattr(node, "value_evidence", ()) for node in walk(node=tree)
        ),
    )


def test_union_numeric_promotion_and_conflict() -> None:
    """Keep immutable scalar annotation contracts and disclose disagreement."""
    expect_equal(
        actual=str(
            object=join_types(
                left=TypeShape(name="int"),
                right=TypeShape(name="complex"),
            ),
        ),
        expected="complex",
    )
    tree: CommentedModule = CommentedModule.parse(source="a: int = 'wrong'")
    result: TypeInference = tree.infer_type(node="a")
    expect_true(condition=bool(result.conflicts))
    expect_equal(actual=result.declared, expected=TypeShape(name="int"))


def test_function_parameter_backwards_to_caller() -> None:
    """Propagate parameter annotations to unknown caller arguments."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
input_value = external()
def f(x: int):
    return x
y = f(input_value)
"""
        ),
    )
    result: TypeInference = tree.infer_type(node="input_value")
    expect_equal(actual=str(object=result.inferred), expected="int")
    expect_true(
        condition=any(
            item.kind == "backward_contract" for item in result.evidence
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
a = [1]
a = ['z']""",
            "list[int | str]",
        ),
        (
            """\
a: list[int] = []
a.append(2)""",
            "list[int]",
        ),
        (
            """\
a = {'a': 3}
a.update({'b': 2.2})""",
            "dict[str, float]",
        ),
        (
            """\
def fn(x: int):
    return x
y = fn(x=3)""",
            "int",
        ),
        ("x: int | str = 'ok'", "int | str"),
        ("a = {1, 2.0}", "set[float]"),
        (
            """\
x = {'k': [1]}
a = x['k']""",
            "list[int]",
        ),
        (
            """\
x = 1
if flag:
    x = 2.0""",
            "float",
        ),
        (
            """\
x = 1
while flag:
    x = 2.0""",
            "float",
        ),
    ],
)
def test_additional_type_shapes(*, source: str, expected: str) -> None:
    """Check generic widening, control joins, annotations and contracts.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while check generic widening, control
            joins, annotations and contracts.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    target: str = (
        "y"
        if "y =" in source
        else "a"
        if "a =" in source or "a:" in source
        else "x"
    )
    expect_equal(
        actual=str(object=tree.infer_type(node=target).inferred),
        expected=expected,
    )


def test_node_facts_stabilize_with_repeat_access() -> None:
    """Reuse a completed type-constraint graph for the same AST revision."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = [1]
b = a[0]
""",
    )
    first: TypeConstraintSolver = tree.semantic.types
    expect_is(actual=first, expected=tree.semantic.types)
    expect_true(condition=tree.infer_type(node="b").stable)
    expect_equal(
        actual=str(
            object=tree.infer_type(
                node=expression_of_stmt(value=tree.body[1]),
            ).inferred,
        ),
        expected="int",
    )


def test_partial_budget_rejects_false_convergence() -> None:
    """Never label an unfinished worklist as converged."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x
y = f(3)
""",
    )
    solver: TypeConstraintSolver = TypeConstraintSolver(
        root=tree,
        scopes=tree.semantic.scopes,
        budgets=TypeBudgets(max_visits=1),
    )
    expect_false(condition=solver.statistics.converged)
    expect_false(
        condition=solver.infer_symbol(
            symbol_id=expect_not_none(
                value=tree.semantic.resolve(name="y"),
            ).id,
        ).stable,
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
a = {'x': 2}
y = a.get('x')""",
            "None | int",
        ),
        (
            """\
a = {'x': 2}
y = a.get('x', 1.2)""",
            "float",
        ),
        (
            """\
a = {'x': 2}
y = a.pop('x')""",
            "int",
        ),
        (
            """\
a = [1.2]
y = a.pop()""",
            "float",
        ),
        (
            """\
a = [1]
y = a.copy()""",
            "list[int]",
        ),
        (
            """\
a: dict[str, int] = {}
y = a.setdefault('x', 2)""",
            "int",
        ),
    ],
)
def test_modeled_container_method_return(
    *,
    source: str,
    expected: str,
) -> None:
    """Transfer known built-in method return contracts without running them.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while transfer known built-in method
            return contracts without running them.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=str(object=tree.infer_type(node="y").inferred),
        expected=expected,
    )


def test_type_evidence_retracted_on_mutation() -> None:
    """Refresh evidence and types after a mutable source AST edit."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = 'old'
""",
    )
    initial: TypeInference = tree.infer_type(node="a")
    expect_equal(actual=str(object=initial.inferred), expected="str")
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 4
    current: TypeInference = tree.infer_type(node="a")
    expect_equal(actual=str(object=current.inferred), expected="int")
    expect_true(
        condition=all(
            "str" not in item.description for item in current.evidence
        ),
    )


def test_imported_constructor_types_call_and_arguments() -> None:
    """Imported constructors type their result and their arguments.

    ``Path(p)`` and ``UUID(hex=u)`` resolve through curated signatures, so
    the call yields the constructor type and each argument picks up the
    declared parameter type as backward evidence.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
from pathlib import Path
from uuid import UUID

def f(p, u):
    q = Path(p)
    r = UUID(hex=u)
    return q, r
""",
    )
    parameters: dict[str, arg] = {
        node.arg: node for node in walk(node=tree) if isinstance(node, arg)
    }
    calls: dict[str, Call] = {}
    for node in walk(node=tree):
        if isinstance(node, Call) and isinstance(node.func, Name):
            calls[node.func.id] = node
    expect_equal(
        actual=str(object=tree.infer_type(node=calls["Path"]).inferred),
        expected="Path",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node=calls["UUID"]).inferred),
        expected="UUID",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node=parameters["p"]).inferred),
        expected="PathLike[str] | str",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node=parameters["u"]).inferred),
        expected="str | None",
    )


def test_imported_constructor_rebound_name_stays_unknown() -> None:
    """A rebound import loses its constructor contract."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
from pathlib import Path
Path = str

x = Path("a")
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="x").inferred),
        expected="Unknown",
    )


def test_imported_constructor_local_shadow_wins() -> None:
    """A local callable with the same name keeps its own contract."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def Path(x):
    return x

y = Path(1)
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="y").inferred),
        expected="int",
    )


def test_self_attribute_reads_resolve_members_and_writes() -> None:
    """``self.attr`` reads see class members and recorded ``self`` writes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
class C:
    count: int = 0
    name = "x"

    def __init__(self, v: int):
        self.total = v
        self.label: str = "t"

    def get(self):
        return self.count, self.name, self.total, self.label, self.missing
""",
    )
    reads: dict[str, Attribute] = {
        node.attr: node
        for node in walk(node=tree)
        if isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and node.value.id == "self"
        and isinstance(node.ctx, Load)
    }
    for attr, expected in (
        ("count", "int"),
        ("name", "str"),
        ("total", "int"),
        ("label", "str"),
        ("missing", "Unknown"),
    ):
        expect_equal(
            actual=str(object=tree.infer_type(node=reads[attr]).inferred),
            expected=expected,
        )
