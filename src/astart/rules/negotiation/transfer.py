"""How a type changes when it crosses a contract."""

from __future__ import annotations

from ast import Subscript, Tuple, expr, parse, unparse
from typing import Final, final

from astart.rules.negotiation.algebra import TypeAlgebra
from astart.rules.negotiation.model import Candidate, Relation


@final
class Constants:
    """Group module-level constants.

    Attributes:
        identity (Final[frozenset[Relation]]): Relations whose type passes
            through unchanged.
        element_origins (Final[frozenset[str]]): Containers with one element
            type argument.
        mapping_origins (Final[frozenset[str]]): Containers with a key and a
            value argument.
        union_limit (Final[int]): Most members of a transferred union.
        pair (Final[int]): Number of arguments of a mapping type.
        scalar_items (Final[dict[str, str]]): Type of one item of a string or
            bytes value.
        wrappers (Final[dict[Relation, str]]): Container built around an
            element type, by relation.

    """

    identity: Final[frozenset[Relation]] = frozenset(
        {
            Relation.assigns,
            Relation.returns,
            Relation.argument,
            Relation.call_result,
            Relation.attribute,
            Relation.instance_field,
            Relation.class_field,
            Relation.narrows,
        },
    )
    element_origins: Final[frozenset[str]] = frozenset(
        {
            "list",
            "set",
            "frozenset",
            "Sequence",
            "MutableSequence",
            "Iterable",
            "Iterator",
            "Collection",
            "Set",
            "MutableSet",
        },
    )
    mapping_origins: Final[frozenset[str]] = frozenset(
        {"dict", "Mapping", "MutableMapping"},
    )
    union_limit: Final[int] = 8
    pair: Final[int] = 2
    wrappers: Final[dict[Relation, str]] = {
        Relation.list_of: "list",
        Relation.set_of: "set",
    }
    scalar_items: Final[dict[str, str]] = {"str": "str", "bytes": "int"}


def _arguments(*, member: str) -> tuple[str, tuple[str, ...]] | None:
    """Split one non-union type into origin and argument texts.

    Args:
        member (str): A single type.

    Returns:
        tuple[str, tuple[str, ...]] | None:
            The origin and arguments, or ``None`` when
            it does not parse or is not subscripted.

    """
    try:
        node: expr = parse(source=member, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, Subscript):
        return None
    inner: expr = node.slice
    parts: list[expr] = (
        list(inner.elts) if isinstance(inner, Tuple) else [inner]
    )
    return unparse(ast_obj=node.value), tuple(
        unparse(ast_obj=part) for part in parts
    )


def _member_component(*, member: str, relation: Relation) -> str | None:
    """Take a component out of one non-union container type.

    Iterating a mapping yields its keys; subscripting it yields its values.

    Args:
        member (str): A single container type.
        relation (Relation): ``element``, ``key``, ``value`` or ``item``.

    Returns:
        str | None: The component type, or ``None`` when the container is not
            recognised for the relation.

    """
    if member in Constants.scalar_items:
        return (
            Constants.scalar_items[member]
            if relation in (Relation.element, Relation.item)
            else None
        )
    split: tuple[str, tuple[str, ...]] | None = _arguments(member=member)
    if split is None:
        return None
    origin, arguments = split
    if origin in Constants.mapping_origins:
        if len(arguments) != Constants.pair:
            return None
        position: dict[Relation, int] = {
            Relation.element: 0,
            Relation.key: 0,
            Relation.mapping_value: 1,
            Relation.item: 1,
        }
        return arguments[position[relation]]
    if (
        origin in Constants.element_origins
        and len(arguments) == 1
        and relation in (Relation.element, Relation.item)
    ):
        return arguments[0]
    return None


def _component(*, type_text: str, relation: Relation) -> str | None:
    """Take the element, key, value or item type out of a container type.

    Args:
        type_text (str): The container type, possibly a union of containers.
        relation (Relation): ``element``, ``key``, ``value`` or ``item``.

    Returns:
        str | None: The joined component type, or ``None`` when
            any member is not a recognised container.

    """
    algebra: TypeAlgebra = TypeAlgebra()
    found: list[str] = []
    for member in algebra.members(source=type_text):
        part: str | None = _member_component(member=member, relation=relation)
        if part is None:
            return None
        found.append(part)
    return algebra.union(types=found, limit=Constants.union_limit)


def forward(*, candidate: Candidate, relation: Relation) -> Candidate | None:
    """Carry a candidate from a contract's source to its target.

    Args:
        candidate (Candidate): The type at the source.
        relation (Relation): The contract's relation.

    Returns:
        Candidate | None: The candidate at the target, or
            ``None`` when nothing sound follows.

    """
    if relation in Constants.identity:
        return candidate
    if relation in Constants.wrappers:
        return candidate.retyped(
            type_text=f"{Constants.wrappers[relation]}[{candidate.type_text}]",
        )
    if relation in (
        Relation.element,
        Relation.key,
        Relation.mapping_value,
        Relation.item,
    ):
        component: str | None = _component(
            type_text=candidate.type_text,
            relation=relation,
        )
        return (
            None
            if component is None
            else candidate.retyped(type_text=component)
        )
    return None


def backward(*, candidate: Candidate, relation: Relation) -> Candidate | None:
    """Carry a constraint from a contract's target to its source.

    Only relations that pass a value through unchanged can be reversed; a
    container cannot be guessed from its element.

    Args:
        candidate (Candidate): The type at the target.
        relation (Relation): The contract's relation.

    Returns:
        Candidate | None: The constraint at the source, or ``None``.

    """
    return candidate if relation in Constants.identity else None
