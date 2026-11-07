"""Typed, keyword-only expectation helpers used by the test-suite.

Each helper raises :class:`AssertionError` with a message that shows both
operands, so a failing expectation is as informative as a rewritten ``assert``.
"""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    AugAssign,
    BinOp,
    BoolOp,
    Call,
    ClassDef,
    Constant,
    Expr,
    For,
    FunctionDef,
    If,
    JoinedStr,
    List,
    Name,
    Return,
    Set,
    Try,
    TryStar,
    Tuple,
    While,
    With,
    expr,
    stmt,
)
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Container, Hashable


def _fail(*, message: str, detail: str) -> NoReturn:
    """Raise an :class:`AssertionError` combining ``message`` and ``detail``.

    Args:
        message: Caller-supplied context, possibly empty.
        detail: Description of the mismatch.

    Raises:
        AssertionError: Always.

    """
    msg: str = f"{message}: {detail}" if message else detail
    raise AssertionError(msg)


def expect_true(*, condition: bool, message: str = "") -> None:
    """Require ``condition`` to be true.

    Args:
        condition: Boolean result being checked.
        message: Optional context shown on failure.

    """
    if not condition:
        _fail(message=message, detail="condition was false")


def expect_false(*, condition: bool, message: str = "") -> None:
    """Require ``condition`` to be false.

    Args:
        condition: Boolean result being checked.
        message: Optional context shown on failure.

    """
    if condition:
        _fail(message=message, detail="condition was true")


def expect_equal[T](*, actual: T, expected: T, message: str = "") -> None:
    """Require ``actual == expected``.

    Args:
        actual: Observed value.
        expected: Required value.
        message: Optional context shown on failure.

    """
    if actual != expected:
        _fail(message=message, detail=f"{actual!r} != {expected!r}")


def expect_not_equal[T](
    *,
    actual: T,
    unexpected: T,
    message: str = "",
) -> None:
    """Require ``actual != unexpected``.

    Args:
        actual: Observed value.
        unexpected: Value that must differ.
        message: Optional context shown on failure.

    """
    if actual == unexpected:
        _fail(message=message, detail=f"{actual!r} == {unexpected!r}")


def expect_is[T](*, actual: T, expected: T, message: str = "") -> None:
    """Require ``actual is expected``.

    Args:
        actual: Observed object.
        expected: Required identical object.
        message: Optional context shown on failure.

    """
    if actual is not expected:
        _fail(message=message, detail=f"{actual!r} is not {expected!r}")


def expect_is_not[T](
    *,
    actual: T,
    unexpected: T,
    message: str = "",
) -> None:
    """Require ``actual is not unexpected``.

    Args:
        actual: Observed object.
        unexpected: Object that must be a different one.
        message: Optional context shown on failure.

    """
    if actual is unexpected:
        _fail(message=message, detail=f"{actual!r} is {unexpected!r}")


def expect_in[T](
    *,
    item: T,
    container: Container[T],
    message: str = "",
) -> None:
    """Require ``item in container``.

    Args:
        item: Value that must be present.
        container: Collection searched.
        message: Optional context shown on failure.

    """
    if item not in container:
        _fail(message=message, detail=f"{item!r} not in {container!r}")


def expect_not_in[T](
    *,
    item: T,
    container: Container[T],
    message: str = "",
) -> None:
    """Require ``item not in container``.

    Args:
        item: Value that must be absent.
        container: Collection searched.
        message: Optional context shown on failure.

    """
    if item in container:
        _fail(message=message, detail=f"{item!r} in {container!r}")


def expect_instance[T](
    *,
    value: Hashable,
    kind: type[T],
    message: str = "",
) -> T:
    """Require ``value`` to be an instance of ``kind`` and return it narrowed.

    Args:
        value: Object being checked.
        kind: Required class.
        message: Optional context shown on failure.

    Returns:
        ``value``, typed as ``kind``.

    """
    if not isinstance(value, kind):
        _fail(message=message, detail=f"{value!r} is not a {kind.__name__}")
    return value


def expect_not_none[T](*, value: T | None, message: str = "") -> T:
    """Require ``value`` to be present and return it narrowed.

    Args:
        value: Possibly-missing value.
        message: Optional context shown on failure.

    Returns:
        ``value`` with ``None`` removed from its type.

    """
    if value is None:
        _fail(message=message, detail="value was None")
    return value


type SuiteStatement = (
    ClassDef
    | FunctionDef
    | AsyncFunctionDef
    | If
    | For
    | AsyncFor
    | While
    | With
    | AsyncWith
    | Try
    | TryStar
)
type ValueStatement = Assign | AnnAssign | AugAssign | Expr | Return
type NamedStatement = ClassDef | FunctionDef | AsyncFunctionDef
type FunctionStatement = FunctionDef | AsyncFunctionDef
type ValuesExpression = JoinedStr | BoolOp
type ElementsExpression = List | Tuple | Set


def expect_suite_node(*, value: stmt) -> SuiteStatement:
    """Require a statement with a concrete, mutable body suite.

    Args:
        value: The value examined while require a statement with a
            concrete, mutable body suite.

    Returns:
        SuiteStatement produced by this operation.

    """
    if not isinstance(
        value,
        (
            ClassDef,
            FunctionDef,
            AsyncFunctionDef,
            If,
            For,
            AsyncFor,
            While,
            With,
            AsyncWith,
            Try,
            TryStar,
        ),
    ):
        _fail(message="", detail=f"{type(value).__name__} has no body suite")
    return value


def expect_value_stmt(*, value: stmt) -> ValueStatement:
    """Require a statement with a Python AST expression-value field.

    Args:
        value: The value examined while require a statement with a Python
            AST expression-value field.

    Returns:
        ValueStatement produced by this operation.

    """
    if not isinstance(value, (Assign, AnnAssign, AugAssign, Expr, Return)):
        _fail(message="", detail=f"{type(value).__name__} has no value field")
    return value


def expression_of_stmt(*, value: stmt) -> expr:
    """Require an expression-valued statement with a nonempty expression.

    Args:
        value: The value examined while require an expression-valued
            statement with a nonempty expression.

    Returns:
        expr produced by this operation.

    """
    candidate: expr | None = expect_value_stmt(value=value).value
    if candidate is None:
        _fail(message="", detail="statement's value was None")
    return candidate


def expect_named_node(*, value: stmt) -> NamedStatement:
    """Narrow a statement to one declaring a named class or function.

    Args:
        value: The value examined while narrow a statement to one declaring
            a named class or function.

    Returns:
        NamedStatement produced by this operation.

    """
    if not isinstance(value, (ClassDef, FunctionDef, AsyncFunctionDef)):
        _fail(message="", detail=f"{type(value).__name__} has no name")
    return value


def expect_function_node(*, value: stmt) -> FunctionStatement:
    """Narrow a function statement to one with signature AST fields.

    Args:
        value: The value examined while narrow a function statement to one
            with signature AST fields.

    Returns:
        FunctionStatement produced by this operation.

    """
    if not isinstance(value, (FunctionDef, AsyncFunctionDef)):
        _fail(message="", detail=f"{type(value).__name__} is not a function")
    return value


def expect_values_expr(*, value: expr) -> ValuesExpression:
    """Require an expression with a mutable .values list.

    Args:
        value: The value examined while require an expression with a
            mutable .values list.

    Returns:
        ValuesExpression produced by this operation.

    """
    if not isinstance(value, (JoinedStr, BoolOp)):
        _fail(message="", detail=f"{type(value).__name__} has no values")
    return value


def expect_elements_expr(*, value: expr) -> ElementsExpression:
    """Require a list, tuple or set expression with mutable elements.

    Args:
        value: The value examined while require a list, tuple or set
            expression with mutable elements.

    Returns:
        ElementsExpression produced by this operation.

    """
    if not isinstance(value, (List, Tuple, Set)):
        _fail(message="", detail=f"{type(value).__name__} has no elements")
    return value


def expect_binary_expr(*, value: expr) -> BinOp:
    """Require a binary operation, including its left and right terms.

    Args:
        value: The value examined while require a binary operation,
            including its left and right terms.

    Returns:
        BinOp produced by this operation.

    """
    if not isinstance(value, BinOp):
        _fail(message="", detail=f"{type(value).__name__} is not a BinOp")
    return value


def expect_name_expr(*, value: expr) -> Name:
    """Require an AST Name expression.

    Args:
        value: The value examined while require an AST Name expression.

    Returns:
        Name produced by this operation.

    """
    if not isinstance(value, Name):
        _fail(message="", detail=f"{type(value).__name__} is not a Name")
    return value


def expect_call_expr(*, value: expr) -> Call:
    """Require a function call expression with a real args list.

    Args:
        value: The value examined while require a function call expression
            with a real args list.

    Returns:
        Call produced by this operation.

    """
    if not isinstance(value, Call):
        _fail(message="", detail=f"{type(value).__name__} is not a Call")
    return value


def expect_constant_expr(*, value: expr) -> Constant:
    """Narrow an AST expression to a mutable constant literal.

    Args:
        value: The value examined while narrow an AST expression to a
            mutable constant literal.

    Returns:
        Constant produced by this operation.

    """
    if not isinstance(value, Constant):
        _fail(message="", detail=f"{type(value).__name__} is not Constant")
    return value
