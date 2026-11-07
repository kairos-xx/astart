"""Predicate algebra: rule triggers expressed as data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart.rules.jsonvalue import JsonValue
type FactValue = str | int | float | bool | None


class CompareOp(StrEnum):
    """Comparison operator of a :class:`Compare` node.

    Attributes:
        eq: Equal.
        ne: Not equal.
        lt: Less than.
        le: Less than or equal.
        gt: Greater than.
        ge: Greater than or equal.

    """

    eq = "eq"
    ne = "ne"
    lt = "lt"
    le = "le"
    gt = "gt"
    ge = "ge"


@final
@dataclass(frozen=True, slots=True)
class AllOf:
    """Hold when every item holds.

    Attributes:
        items: Child predicates.

    """

    items: tuple[Predicate, ...]


@final
@dataclass(frozen=True, slots=True)
class AnyOf:
    """Hold when at least one item holds.

    Attributes:
        items: Child predicates.

    """

    items: tuple[Predicate, ...]


@final
@dataclass(frozen=True, slots=True)
class Not:
    """Hold when the item does not.

    Attributes:
        item: Negated predicate.

    """

    item: Predicate


@final
@dataclass(frozen=True, slots=True)
class Compare:
    """Compare one fact with a constant.

    Attributes:
        fact: Fact name.
        op: Comparison operator.
        value: Constant to compare with.

    """

    fact: str
    op: CompareOp
    value: FactValue


@final
@dataclass(frozen=True, slots=True)
class Exists:
    """Hold when some node of a kind satisfies a predicate.

    Attributes:
        selector: Node kind to quantify over.
        where: Predicate each candidate must satisfy.

    """

    selector: str
    where: Predicate


type Predicate = AllOf | AnyOf | Not | Compare | Exists


def predicate_to_json(*, predicate: Predicate) -> JsonValue:
    """Convert a predicate to its JSON form.

    Args:
        predicate: Predicate to convert.

    Returns:
        JSON-compatible value.

    """
    match predicate:
        case AllOf(items=items):
            return {
                "op": "all",
                "of": [predicate_to_json(predicate=item) for item in items],
            }
        case AnyOf(items=items):
            return {
                "op": "any",
                "of": [predicate_to_json(predicate=item) for item in items],
            }
        case Not(item=item):
            return {"op": "not", "of": predicate_to_json(predicate=item)}
        case Compare(fact=fact, op=op, value=value):
            return {
                "op": "compare",
                "fact": fact,
                "cmp": op.value,
                "value": value,
            }
        case Exists(selector=selector, where=where):
            return {
                "op": "exists",
                "selector": selector,
                "where": predicate_to_json(predicate=where),
            }


def predicate_from_json(*, value: JsonValue) -> Predicate:
    """Restore a predicate from its JSON form.

    Args:
        value: JSON-compatible value.

    Returns:
        The predicate.

    Raises:
        ValueError: If the value is not a predicate object, or its operator
            or a required key is unknown.

    """
    match value:
        case dict():
            return _node_from_json(value=value)
        case _:
            msg: str = f"predicate must be a JSON object, got {value!r}"
            raise ValueError(msg)


def _node_from_json(*, value: dict[str, JsonValue]) -> Predicate:
    """Restore a predicate from a JSON object.

    Args:
        value: Predicate object.

    Returns:
        The predicate.

    Raises:
        ValueError: If the operator or a required key is invalid.

    """
    op: JsonValue = value.get("op")
    match op:
        case "all" | "any":
            items: tuple[Predicate, ...] = tuple(
                predicate_from_json(value=child)
                for child in _children(value=value)
            )
            return AllOf(items=items) if op == "all" else AnyOf(items=items)
        case "not":
            return Not(
                item=predicate_from_json(
                    value=_required(value=value, key="of"),
                ),
            )
        case "compare":
            return _compare_from_json(value=value)
        case "exists":
            match _required(value=value, key="selector"):
                case str() as selector:
                    return Exists(
                        selector=selector,
                        where=predicate_from_json(
                            value=_required(value=value, key="where"),
                        ),
                    )
                case _:
                    msg: str = "'exists' needs a string 'selector'"
                    raise ValueError(msg)
        case _:
            msg = f"unknown predicate op {op!r}"
            raise ValueError(msg)


def _children(*, value: dict[str, JsonValue]) -> list[JsonValue]:
    """Return the child list of an ``all`` or ``any`` object.

    Args:
        value: Predicate object.

    Returns:
        The children.

    Raises:
        ValueError: If ``of`` is not a list.

    """
    match value.get("of"):
        case list() as children:
            return children
        case _:
            msg: str = f"'{value.get('op')}' needs a list under 'of'"
            raise ValueError(msg)


def _required(value: dict[str, JsonValue], key: str) -> JsonValue:
    """Return a mandatory key of a predicate object.

    Args:
        value: Predicate object.
        key: Required key.

    Returns:
        The stored value.

    Raises:
        ValueError: If the key is absent.

    """
    if key not in value:
        msg: str = f"predicate {value.get('op')!r} is missing key {key!r}"
        raise ValueError(msg)
    return value[key]


def _compare_from_json(*, value: dict[str, JsonValue]) -> Compare:
    """Restore a comparison node.

    Args:
        value: Predicate object whose op is ``compare``.

    Returns:
        The comparison.

    Raises:
        ValueError: If the fact, operator or constant is malformed.

    """
    match (
        _required(value=value, key="fact"),
        _required(value=value, key="cmp"),
        _required(value=value, key="value"),
    ):
        case (str() as fact, str() as cmp, list() | dict()):
            msg: str = f"'compare' value for {fact!r} must be a scalar"
            raise ValueError(msg)
        case (
            str() as fact,
            str() as cmp,
            (str() | int() | float() | bool() | None) as constant,
        ):
            return Compare(fact=fact, op=CompareOp(cmp), value=constant)
        case _:
            msg = "'compare' needs string 'fact' and 'cmp'"
            raise ValueError(msg)


def predicate_facts(*, predicate: Predicate) -> frozenset[str]:
    """Collect every fact name a predicate reads.

    Args:
        predicate: Predicate to inspect.

    Returns:
        The fact names.

    """
    match predicate:
        case AllOf(items=items) | AnyOf(items=items):
            names: frozenset[str] = frozenset()
            for item in items:
                names |= predicate_facts(predicate=item)
            return names
        case Not(item=item):
            return predicate_facts(predicate=item)
        case Compare(fact=fact):
            return frozenset({fact})
        case Exists(where=where):
            return predicate_facts(predicate=where)


def evaluate(*, predicate: Predicate, facts: Mapping[str, FactValue]) -> bool:
    """Evaluate a predicate against computed facts.

    Args:
        predicate: Predicate to evaluate.
        facts: Fact values by name.

    Returns:
        Whether the predicate holds.

    Raises:
        KeyError: If a fact the predicate reads is missing.
        NotImplementedError: For ``Exists``, which the engine evaluates.

    """
    match predicate:
        case AllOf(items=items):
            return all(evaluate(predicate=item, facts=facts) for item in items)
        case AnyOf(items=items):
            return any(evaluate(predicate=item, facts=facts) for item in items)
        case Not(item=item):
            return not evaluate(predicate=item, facts=facts)
        case Compare(fact=fact, op=op, value=value):
            if fact not in facts:
                msg: str = f"fact {fact!r} is missing"
                raise KeyError(msg)
            return _compare(left=facts[fact], op=op, right=value)
        case Exists(selector=selector):
            msg = f"'exists' over {selector!r} is evaluated by the engine"
            raise NotImplementedError(msg)


def _compare(*, left: FactValue, op: CompareOp, right: FactValue) -> bool:
    """Apply a comparison operator.

    Args:
        left: Computed fact value.
        op: Operator.
        right: Constant from the predicate.

    Returns:
        The comparison result.

    """
    if op is CompareOp.eq:
        return left == right
    if op is CompareOp.ne:
        return left != right
    order: int = _order(left=left, right=right)
    if op is CompareOp.lt:
        return order < 0
    if op is CompareOp.le:
        return order <= 0
    if op is CompareOp.gt:
        return order > 0
    return order >= 0


def _order(*, left: FactValue, right: FactValue) -> int:
    """Three-way compare two numbers or two strings.

    Args:
        left: Computed fact value.
        right: Constant from the predicate.

    Returns:
        Negative, zero or positive.

    Raises:
        TypeError: If the operands are not both numbers or both strings.

    """
    match (left, right):
        case (int() | float() as first, int() | float() as second):
            return (first > second) - (first < second)
        case (str() as first, str() as second):
            return (first > second) - (first < second)
        case _:
            msg: str = f"cannot order {left!r} and {right!r}"
            raise TypeError(msg)
