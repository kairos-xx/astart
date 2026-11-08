"""Evaluate the ``if`` tests that stub files use to branch by environment."""

from __future__ import annotations

from ast import (
    And,
    Attribute,
    BoolOp,
    Call,
    Compare,
    Constant,
    Name,
    Not,
    Subscript,
    Tuple,
    UnaryOp,
    cmpop,
    expr,
    unparse,
)
from dataclasses import dataclass
from operator import ge, gt, le, lt
from sys import platform as host_platform
from sys import version_info
from typing import Final, final


@final
class Constants:
    """Constants used in the conditions module.

    Attributes:
        equality: Comparison operator names decided by equality.

    """

    equality: Final[frozenset[str]] = frozenset({"Eq", "NotEq"})


@final
@dataclass(frozen=True, slots=True)
class Target:
    """The environment a stub is read for.

    Attributes:
        version: Python ``(major, minor)``.
        platform: Value of ``sys.platform``.
        implementation: Value of ``sys.implementation.name``.

    """

    version: tuple[int, int] = (version_info.major, version_info.minor)
    platform: str = host_platform
    implementation: str = "cpython"


def _compare(
    *,
    left: tuple[int, ...] | str | int,
    operator: cmpop,
    right: tuple[int, ...] | str | int,
) -> bool | None:
    """Apply a comparison operator to two comparable values.

    The operator is read by name, so the result does not depend on which copy
    of the ``ast`` classes created the node.

    Args:
        left: Left operand.
        operator: An ``ast`` comparison operator instance.
        right: Right operand.

    Returns:
        The result, or ``None`` for an operator or operands not understood.

    """
    if type(left) is not type(right):
        return None
    name: str = type(operator).__name__
    if name in Constants.equality:
        return (left == right) == (name == "Eq")
    result: bool | None = None
    if isinstance(left, (tuple, int)) and isinstance(right, (tuple, int)):
        if name == "Lt":
            result = lt(left, right)
        elif name == "LtE":
            result = le(left, right)
        elif name == "Gt":
            result = gt(left, right)
        elif name == "GtE":
            result = ge(left, right)
    return result


def _literal(*, node: expr) -> tuple[int, ...] | str | int | None:
    """Read a constant a stub compares against.

    Args:
        node: The comparator.

    Returns:
        An int, a string, a tuple of ints, or ``None``.

    """
    if isinstance(node, Constant) and isinstance(node.value, (int, str)):
        return node.value
    if isinstance(node, Tuple) and all(
        isinstance(item, Constant) and isinstance(item.value, int)
        for item in node.elts
    ):
        return tuple(
            item.value
            for item in node.elts
            if isinstance(item, Constant) and isinstance(item.value, int)
        )
    return None


def _subject(
    *,
    node: expr,
    target: Target,
) -> tuple[int, ...] | str | int | None:
    """Read the environment value a comparison's left side stands for.

    Args:
        node: The left operand.
        target: The environment.

    Returns:
        ``sys.version_info`` (or an index or prefix of it), ``sys.platform``
        or ``sys.implementation.name``; ``None`` for anything else.

    """
    text: str = unparse(ast_obj=node)
    if text == "sys.version_info":
        return target.version
    if text == "sys.platform":
        return target.platform
    if text == "sys.implementation.name":
        return target.implementation
    if (
        isinstance(node, Subscript)
        and unparse(ast_obj=node.value) == "sys.version_info"
        and isinstance(node.slice, Constant)
        and isinstance(node.slice.value, int)
    ):
        return target.version[node.slice.value]
    return None


def _sized(
    *,
    subject: tuple[int, ...] | str | int,
    other: tuple[int, ...] | str | int,
) -> tuple[int, ...] | str | int:
    """Cut a version tuple to the length of the tuple it is compared with.

    ``sys.version_info >= (3, 9)`` compares the first two fields only.

    Args:
        subject: The environment value.
        other: The literal on the other side.

    Returns:
        The subject, trimmed when both are tuples.

    """
    if isinstance(subject, tuple) and isinstance(other, tuple):
        return subject[: len(other)]
    return subject


def _comparison(*, node: Compare, target: Target) -> bool | None:
    """Evaluate ``subject OP literal``.

    Args:
        node: The comparison.
        target: The environment.

    Returns:
        The truth value, or ``None`` when it cannot be decided.

    """
    if len(node.ops) != 1:
        return None
    subject: tuple[int, ...] | str | int | None = _subject(
        node=node.left,
        target=target,
    )
    literal: tuple[int, ...] | str | int | None = _literal(
        node=node.comparators[0],
    )
    if subject is None or literal is None:
        return None
    return _compare(
        left=_sized(subject=subject, other=literal),
        operator=node.ops[0],
        right=literal,
    )


def _platform_call(*, node: Call, target: Target) -> bool | None:
    """Evaluate ``sys.platform.startswith("linux")``.

    Args:
        node: A call expression.
        target: The environment.

    Returns:
        The truth value, or ``None`` for any other call.

    """
    if (
        isinstance(node.func, Attribute)
        and node.func.attr == "startswith"
        and unparse(ast_obj=node.func.value) == "sys.platform"
        and len(node.args) == 1
        and isinstance(node.args[0], Constant)
        and isinstance(node.args[0].value, str)
    ):
        return target.platform.startswith(node.args[0].value)
    return None


def _boolean(*, node: BoolOp, target: Target) -> bool | None:
    """Evaluate ``a and b`` / ``a or b`` with three-valued logic.

    Args:
        node: The boolean operation.
        target: The environment.

    Returns:
        ``True``/``False`` when decided (a decided operand can settle an
        ``and``/``or`` even if another is unknown), else ``None``.

    """
    results: list[bool | None] = [
        evaluate(test=value, target=target) for value in node.values
    ]
    decisive: bool = not isinstance(node.op, And)
    if decisive in results:
        return decisive
    return None if None in results else not decisive


def evaluate(*, test: expr, target: Target) -> bool | None:
    """Decide a stub ``if`` test for an environment.

    Args:
        test: The test expression.
        target: The environment.

    Returns:
        ``True`` or ``False`` when decided; ``None`` when the test depends
        on something this evaluator does not know.

    """
    if isinstance(test, Constant) and isinstance(test.value, bool):
        return test.value
    if isinstance(test, (Name, Attribute)):
        return (
            True
            if unparse(ast_obj=test)
            in {"TYPE_CHECKING", "typing.TYPE_CHECKING"}
            else None
        )
    if isinstance(test, UnaryOp) and isinstance(test.op, Not):
        inner: bool | None = evaluate(test=test.operand, target=target)
        return None if inner is None else not inner
    if isinstance(test, BoolOp):
        return _boolean(node=test, target=target)
    if isinstance(test, Compare):
        return _comparison(node=test, target=target)
    return (
        _platform_call(node=test, target=target)
        if isinstance(test, Call)
        else None
    )
