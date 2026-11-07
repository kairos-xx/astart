"""Exercise the from-scratch engine's type helpers and inferer classes."""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, parse
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart._graph.engine import types
from astart._graph.engine.inference import (
    ExpressionInferer,
    ModuleFacts,
    ParameterInferer,
    ReturnInferer,
    constant_type,
)

from tests.expectations import (
    expect_equal,
    expect_function_node,
    expect_instance,
)

if TYPE_CHECKING:
    from ast import expr
    from types import EllipsisType


def _inferer(
    *,
    function_returns: dict[str, str] | None = None,
    class_names: set[str] | None = None,
) -> ExpressionInferer:
    """Build an expression inferer with optional module facts.

    Args:
        function_returns: Known function return types for call resolution.
        class_names: Class names whose calls resolve to the class itself.

    Returns:
        Expression inferer bound to the assembled module facts.

    """
    facts: ModuleFacts = ModuleFacts(
        function_returns=function_returns or {},
        class_names=class_names or set(),
    )
    return ExpressionInferer(facts=facts)


def _infer_expression(
    *,
    source: str,
    scope: dict[str, str],
    function_returns: dict[str, str] | None = None,
    class_names: set[str] | None = None,
) -> str:
    """Infer the type source of one expression in a lexical scope.

    Args:
        class_names: Class names whose calls resolve to the class itself.
        function_returns: Known function return types for call resolution.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    Returns:
        Type source inferred for the parsed expression.

    """
    inferer: ExpressionInferer = _inferer(
        function_returns=function_returns,
        class_names=class_names,
    )
    return inferer.infer(
        node=parse(source=dedent(text=source), mode="eval").body,
        scope=scope,
    )


def _parameter_type(*, source: str) -> str:
    """Infer the type of the first parameter of a leading function.

    Args:
        source: Function source text with a single positional parameter.

    Returns:
        Type source inferred for the parameter.

    """
    function: FunctionDef = expect_instance(
        value=parse(source=dedent(text=source)).body[0],
        kind=FunctionDef,
    )
    default: expr | None = (
        function.args.defaults[0] if function.args.defaults else None
    )
    return ParameterInferer().infer(
        parameter=function.args.args[0],
        default=default,
        body=function.body,
    )


def _return_type(*, source: str, scope: dict[str, str]) -> str:
    """Infer the return type of a leading function definition.

    Args:
        scope: Name-to-type mapping visible inside the function body.
        source: Function source text parsed in module mode.

    Returns:
        Type source inferred for the function's return statements.

    """
    function: FunctionDef | AsyncFunctionDef = expect_function_node(
        value=parse(source=dedent(text=source)).body[0],
    )
    inferer: ExpressionInferer = _inferer()
    return ReturnInferer(inferer=inferer).infer(function=function, scope=scope)


@pytest.mark.parametrize(
    argnames=("source", "expected"),
    argvalues=[
        ("int", ["int"]),
        ("int | str", ["int", "str"]),
        ("dict[str, int | None] | str", ["dict[str, int | None]", "str"]),
        (
            "Callable[[int | None], str] | bytes",
            ["Callable[[int | None], str]", "bytes"],
        ),
        ("(int | str) | bytes", ["(int | str)", "bytes"]),
        ("None", ["None"]),
        ("", []),
        ("int |", ["int"]),
    ],
)
def test_split_union(source: str, expected: list[str]) -> None:
    """Split top-level union members without breaking nested brackets.

    Args:
        expected: Ordered union members preserved from the source.
        source: Union annotation text under test.

    """
    expect_equal(actual=types.split_union(source=source), expected=expected)


@pytest.mark.parametrize(
    argnames=("sources", "expected"),
    argvalues=[
        ((), types.Constants.object),
        (("int",), types.Constants.int),
        (("int", "str"), "int | str"),
        (("str", "int"), "int | str"),
        (("int", "int"), types.Constants.int),
        (("int", "None"), "int | None"),
        (("None", "int"), "int | None"),
        (("object", "int"), types.Constants.object),
        (("int | str", "float"), "float | int | str"),
        (("", "int"), types.Constants.int),
    ],
)
def test_union(sources: tuple[str, ...], expected: str) -> None:
    """Combine type sources with dedup, sorting, and object absorption.

    Args:
        expected: Normalized union source produced by the combination.
        sources: Individual type sources fed into the union.

    """
    expect_equal(actual=types.union(*sources), expected=expected)


@pytest.mark.parametrize(
    argnames=("source", "expected"),
    argvalues=[
        ("int", "int | None"),
        ("int | str", "int | str | None"),
        ("int | None", "int | None"),
        ("float | None", "float | None"),
        ("None", types.Constants.none),
    ],
)
def test_optional(source: str, expected: str) -> None:
    """Attach ``None`` to a union without duplicating an existing member.

    Args:
        expected: Optionalized union source produced by the operation.
        source: Union annotation text under test.

    """
    expect_equal(actual=types.optional(source=source), expected=expected)


@pytest.mark.parametrize(
    argnames=("value", "expected"),
    argvalues=[
        (None, types.Constants.none),
        (True, types.Constants.bool),
        (0, types.Constants.int),
        (1.5, types.Constants.float),
        ("x", types.Constants.str),
        (b"x", types.Constants.bytes),
        (1j, types.Constants.object),
        (Ellipsis, types.Constants.object),
    ],
)
def test_constant_type(
    *,
    value: str | bytes | complex | bool | None | EllipsisType,
    expected: str,
) -> None:
    """Map literal constants onto their scalar type sources.

    Args:
        expected: Type source inferred for the literal value.
        value: Literal constant value under test.

    """
    expect_equal(actual=constant_type(value=value), expected=expected)


def test_module_facts_defaults() -> None:
    """Start module facts empty for incremental evidence collection."""
    facts: ModuleFacts = ModuleFacts()
    expect_equal(actual=facts.function_returns, expected={})
    expect_equal(actual=facts.function_params, expected={})
    expect_equal(actual=facts.class_names, expected=set())


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        ("42", {}, types.Constants.int),
        ("True", {}, types.Constants.bool),
        ("'x'", {}, types.Constants.str),
        ("b'y'", {}, types.Constants.bytes),
        ("None", {}, types.Constants.none),
        ("1.5", {}, types.Constants.float),
        ("1j", {}, types.Constants.object),
        ("x", {"x": "int"}, types.Constants.int),
        ("x", {}, types.Constants.object),
        ("obj.attr", {"obj.attr": "str"}, types.Constants.str),
        ("obj.attr", {}, types.Constants.object),
        ("obj.inner.attr", {}, types.Constants.object),
        ("x[0]", {}, types.Constants.object),
        ("(x := 1)", {}, types.Constants.object),
        ("lambda v: v", {}, types.Constants.object),
    ],
)
def test_infer_expression_leaves(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Resolve constants, names, and attributes; fall back conservatively.

    Args:
        expected: Type source inferred for the expression.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope=scope),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        ("x and y", {}, types.Constants.bool),
        ("x or y", {}, types.Constants.bool),
        ("x < y", {}, types.Constants.bool),
        ("x == y", {}, types.Constants.bool),
        ("not x", {}, types.Constants.bool),
        ("-x", {"x": "int"}, types.Constants.int),
        ("-x", {}, types.Constants.object),
        ("~x", {"x": "int"}, types.Constants.int),
        ("+x", {"x": "int"}, types.Constants.int),
        ("a if flag else b", {"a": "int", "b": "float"}, "float | int"),
        ("a if flag else b", {"a": "int", "b": "str"}, "int | str"),
        ("a if flag else b", {}, types.Constants.object),
    ],
)
def test_infer_expression_branching(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Infer boolean, unary, and conditional expressions from scope.

    Args:
        expected: Type source inferred for the expression.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope=scope),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        ("x + 1", {"x": "int"}, types.Constants.int),
        ("x - y", {"x": "int", "y": "bool"}, types.Constants.int),
        ("x << y", {"x": "int", "y": "int"}, types.Constants.int),
        ("x @ y", {"x": "int", "y": "int"}, types.Constants.int),
        ("x - y", {"x": "bool", "y": "bool"}, types.Constants.int),
        ("x + y", {"x": "float"}, types.Constants.float),
        ("x + y", {"x": "str", "y": "int"}, types.Constants.str),
        ("x % y", {"x": "str"}, types.Constants.str),
        ("x * 2", {"x": "str"}, types.Constants.object),
        ("x + y", {"x": "bytes", "y": "bytes"}, types.Constants.bytes),
        (
            "x + y",
            {"x": "list[int]", "y": "list[int]"},
            types.Constants.object,
        ),
        ("x | y", {"x": "int", "y": "str"}, types.Constants.object),
    ],
)
def test_infer_expression_binops(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Promote binary operands through the arithmetic evidence rules.

    Args:
        expected: Type source inferred for the binary operation.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope=scope),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        ("[1, 2, 3]", {}, "list[int]"),
        ("[1, 'x']", {}, "list[int | str]"),
        ("[]", {}, "list[object]"),
        ("[x, y]", {"x": "int", "y": "int"}, "list[int]"),
        ("[*xs]", {}, "list[object]"),
        ("{1, 2}", {}, "set[int]"),
        ("{1, 'x'}", {}, "set[int | str]"),
        ("{*xs}", {}, "set[object]"),
        ("(1, 'x')", {}, "tuple[int, str]"),
        ("()", {}, "tuple[()]"),
        ("(x, *ys)", {"x": "int"}, "tuple[int, ...]"),
        ("(*ys,)", {}, "tuple[object, ...]"),
        ("{'a': 1}", {}, "dict[str, int]"),
        ("{}", {}, "dict[object, object]"),
        ("{1: 'a', 'k': 'b'}", {}, "dict[int | str, str]"),
        ("{**base, 'k': 1}", {}, "dict[str, object]"),
    ],
)
def test_infer_expression_containers(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Infer container displays including starred and unpacking members.

    Args:
        expected: Type source inferred for the container expression.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope=scope),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        ("[x * 2 for x in items]", {"x": "int"}, "list[int]"),
        ("[x for x in items]", {}, "list[object]"),
        ("{x for x in items}", {"x": "str"}, "set[str]"),
        ("{x for x in items}", {}, "set[object]"),
        ("(x for x in items)", {"x": "float"}, "Generator[float, None, None]"),
        ("{k: v for k, v in pairs}", {}, "dict[object, object]"),
    ],
)
def test_infer_expression_comprehensions(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Infer comprehension results from their element expressions.

    Args:
        expected: Type source inferred for the comprehension.
        scope: Name-to-type mapping visible inside the expression.
        source: Expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope=scope),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "expected"),
    argvalues=[
        ("len(x)", types.Constants.int),
        ("sorted(x)", "list[object]"),
        ("int(x)", types.Constants.int),
        ("isinstance(x, int)", types.Constants.bool),
        ("type(x)", "type[object]"),
        ("foo()", types.Constants.object),
        ("text.upper()", types.Constants.object),
        ("items[0]()", types.Constants.object),
        ("pkg.inner.func()", types.Constants.object),
    ],
)
def test_infer_expression_calls(source: str, expected: str) -> None:
    """Resolve builtin call returns and fall back for unknown callables.

    Args:
        expected: Type source inferred for the call expression.
        source: Call expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(source=source, scope={}),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "function_returns", "class_names", "expected"),
    argvalues=[
        ("add(1, 2)", {"add": "int"}, set[int](), types.Constants.int),
        ("Widget()", {}, {"Widget"}, "Widget"),
        ("add(1)", {}, set[int](), types.Constants.object),
        ("Widget()", {}, set[int](), types.Constants.object),
    ],
)
def test_infer_expression_fact_calls(
    source: str,
    function_returns: dict[str, str],
    class_names: set[str],
    expected: str,
) -> None:
    """Resolve calls through recorded function and class facts.

    Args:
        class_names: Class names whose calls resolve to the class itself.
        expected: Type source inferred for the call expression.
        function_returns: Known function return types for call resolution.
        source: Call expression source text parsed in eval mode.

    """
    expect_equal(
        actual=_infer_expression(
            source=source,
            scope={},
            function_returns=function_returns,
            class_names=class_names,
        ),
        expected=expected,
    )


@pytest.mark.parametrize(
    argnames=("source", "expected"),
    argvalues=[
        (
            """\
def f(x):
    return x + 1""",
            types.Constants.int,
        ),
        (
            """\
def f(x):
    return x * 2""",
            types.Constants.int,
        ),
        (
            """\
def f(x):
    if x:
        return x - 2
    return x""",
            types.Constants.int,
        ),
        (
            """\
def f(x):
    return x.upper()""",
            types.Constants.str,
        ),
        (
            """\
def f(x):
    y = x.strip()
    return y""",
            types.Constants.str,
        ),
        (
            """\
def f(x='a'):
    return x.strip()""",
            types.Constants.str,
        ),
        (
            """\
def f(x=None):
    return x + 1""",
            "int | None",
        ),
        (
            """\
def f(x=None):
    return x.lower()""",
            "str | None",
        ),
        (
            """\
def f(x=None):
    return x""",
            types.Constants.object,
        ),
        (
            """\
def f(x=5):
    return x""",
            types.Constants.int,
        ),
        (
            """\
def f(x='a'):
    return x""",
            types.Constants.str,
        ),
        (
            """\
def f(x):
    return x""",
            types.Constants.object,
        ),
        (
            """\
def f(x=g()):
    return x""",
            types.Constants.object,
        ),
        (
            """\
def f(x):
    def g():
        return x + 1
    return x""",
            types.Constants.object,
        ),
    ],
)
def test_parameter_inferer(source: str, expected: str) -> None:
    """Infer parameter types from defaults, usage, and local scope only.

    Args:
        expected: Type source inferred for the parameter.
        source: Function source text with a single positional parameter.

    """
    expect_equal(actual=_parameter_type(source=source), expected=expected)


@pytest.mark.parametrize(
    argnames=("source", "scope", "expected"),
    argvalues=[
        (
            """\
def f():
    return 1""",
            {},
            types.Constants.int,
        ),
        (
            """\
def f():
    return x""",
            {"x": "bool"},
            types.Constants.bool,
        ),
        (
            """\
def f():
    return""",
            {},
            types.Constants.none,
        ),
        (
            """\
def f():
    pass""",
            {},
            types.Constants.none,
        ),
        (
            """\
def f():
    if c:
        return 1
    return 'x'""",
            {},
            "int | str",
        ),
        (
            """\
def f():
    if c:
        return
    return 2""",
            {},
            "int | None",
        ),
        (
            """\
def f():
    def g():
        return 1
    return 's'""",
            {},
            types.Constants.str,
        ),
    ],
)
def test_return_inferer(
    source: str,
    scope: dict[str, str],
    expected: str,
) -> None:
    """Union returned values while ignoring nested function scopes.

    Args:
        expected: Type source inferred for the return annotation.
        scope: Name-to-type mapping visible inside the function body.
        source: Function source text parsed in module mode.

    """
    expect_equal(
        actual=_return_type(source=source, scope=scope),
        expected=expected,
    )


def test_return_inferer_async() -> None:
    """Flow async functions through the same return analysis."""
    function: AsyncFunctionDef = expect_instance(
        value=parse(
            source="""\
async def f():
    return 1""",
        ).body[0],
        kind=AsyncFunctionDef,
    )
    inferer: ExpressionInferer = _inferer()
    expect_equal(
        actual=ReturnInferer(inferer=inferer).infer(
            function=function,
            scope={},
        ),
        expected=types.Constants.int,
    )
