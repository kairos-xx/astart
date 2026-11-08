"""Read what an ``if`` test says about a name on each of its arms."""

from __future__ import annotations

from ast import (
    Call,
    Compare,
    Constant,
    Is,
    IsNot,
    Name,
    Not,
    Tuple,
    UnaryOp,
    expr,
    unparse,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Mapping


@final
class Constants:
    """Group module-level constants.

    Attributes:
        not_none: Constraint text that removes ``None``.
        none: Constraint text of the ``None`` arm.
        pair: Arguments of ``isinstance``.

    """

    not_none: Final[str] = "!None"
    none: Final[str] = "None"
    pair: Final[int] = 2


@final
@dataclass(frozen=True, slots=True)
class Arms:
    """What a test establishes about one name.

    Attributes:
        name: The narrowed name.
        when_true: Constraint on the arm where the test holds, or ``None``.
        when_false: Constraint on the arm where it does not, or ``None``.

    """

    name: str
    when_true: str | None
    when_false: str | None

    def negated(self) -> Arms:
        """Swap the arms, as ``not`` does.

        Returns:
            The arms with the two constraints exchanged.

        """
        return Arms(
            name=self.name,
            when_true=self.when_false,
            when_false=self.when_true,
        )


def _is_none(*, test: Compare) -> Arms | None:
    """Read ``x is None`` and ``x is not None``.

    Args:
        test: A comparison.

    Returns:
        The arms, or ``None`` for any other comparison.

    """
    if not (
        isinstance(test.left, Name)
        and len(test.ops) == 1
        and isinstance(test.comparators[0], Constant)
        and test.comparators[0].value is None
    ):
        return None
    if isinstance(test.ops[0], Is):
        return Arms(
            name=test.left.id,
            when_true=Constants.none,
            when_false=Constants.not_none,
        )
    if isinstance(test.ops[0], IsNot):
        return Arms(
            name=test.left.id,
            when_true=Constants.not_none,
            when_false=Constants.none,
        )
    return None


def _isinstance(*, test: Call, counts: Mapping[str, int]) -> Arms | None:
    """Read ``isinstance(x, C)`` and ``isinstance(x, (C, D))``.

    Args:
        test: A call.
        counts: Module binding counts, to see that ``isinstance`` is the
            builtin.

    Returns:
        The arms, or ``None`` for any other call.

    """
    if not (
        isinstance(test.func, Name)
        and test.func.id == "isinstance"
        and counts.get("isinstance", 0) == 0
        and len(test.args) == Constants.pair
        and isinstance(test.args[0], Name)
        and not test.keywords
    ):
        return None
    classes: expr = test.args[1]
    members: list[expr] = (
        list(classes.elts) if isinstance(classes, Tuple) else [classes]
    )
    if not members or not all(isinstance(item, Name) for item in members):
        return None
    return Arms(
        name=test.args[0].id,
        when_true=" | ".join(unparse(ast_obj=item) for item in members),
        when_false=None,
    )


def read_test(*, test: expr, counts: Mapping[str, int]) -> Arms | None:
    """Read the narrowing an ``if`` test establishes.

    Args:
        test: The test expression.
        counts: Module binding counts.

    Returns:
        The arms for ``x is None``, ``x is not None``, ``isinstance(x, C)``,
        ``not`` of those, and bare ``x`` (truthiness removes ``None``);
        ``None`` for anything else.

    """
    if isinstance(test, UnaryOp) and isinstance(test.op, Not):
        inner: Arms | None = read_test(test=test.operand, counts=counts)
        return None if inner is None else inner.negated()
    if isinstance(test, Compare):
        return _is_none(test=test)
    if isinstance(test, Call):
        return _isinstance(test=test, counts=counts)
    if isinstance(test, Name):
        return Arms(
            name=test.id,
            when_true=Constants.not_none,
            when_false=None,
        )
    return None
