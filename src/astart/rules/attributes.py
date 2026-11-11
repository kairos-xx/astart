"""Prove the type of ``self.attr`` from every write to it in a class.

An instance attribute is annotated only when each assignment to it, in every
method of the class, has a type the syntax proves, they all agree (``None``
plus one other type gives ``T | None``), and nothing else in the module can
write it: no other receiver, no class-level binding, no base class that
declares it, no dynamic ``setattr``.

"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    ClassDef,
    Del,
    FloorDiv,
    FunctionDef,
    Mod,
    Module,
    Mult,
    Name,
    Store,
    Sub,
    arg,
    walk,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from astart.rules.provable import expression_type, own_nodes, scope_types
from astart.rules.resolve import constructor_key
from astart.rules.scopes import names_bound_by

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart.rules.methods import MethodIndex

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        scalars (Final[frozenset[str]]): Types an attribute annotation may name
            directly.
        init (Final[str]): Name of the constructor, where an attribute is
            declared.
        numeric_ops (Final[tuple[type[AST], ...]]): Operators that keep a
            numeric attribute numeric.

    """

    scalars: Final[frozenset[str]] = frozenset(
        {"bool", "bytes", "float", "int", "str"},
    )
    init: Final[str] = "__init__"
    numeric_ops: Final[tuple[type[AST], ...]] = (Add, Sub, Mult, FloorDiv, Mod)


@final
@dataclass(slots=True)
class _Attribute:
    """What the class's methods do to one attribute.

    Attributes:
        writes (list[tuple[Assign,str,bool]]): ``(assignment, type, in_init)``
            per plain assignment.
        augments (list[tuple[AST, str | None]]): ``(operator, value type)`` per
            augmented assignment.
        bad (bool): Whether some write cannot be understood.

    """

    writes: list[tuple[Assign, str, bool]]
    augments: list[tuple[AST, str | None]]
    bad: bool = False


def receiver_of(*, function: Function) -> str | None:
    """Name the parameter that holds the instance.

    Args:
        function (Function): Method definition.

    Returns:
        str | None: The first positional parameter, or ``None``
            for static methods and methods without one.

    """
    first: list[arg] = [*function.args.posonlyargs, *function.args.args]
    plain: bool = not any(
        isinstance(item, Name) and item.id in {"staticmethod", "classmethod"}
        for item in function.decorator_list
    )
    return first[0].arg if first and plain else None


def _self_attribute(*, node: AST, receiver: str) -> str | None:
    """Read the attribute of ``receiver.attr``.

    Args:
        node (AST): Candidate expression.
        receiver (str): Name that holds the instance.

    Returns:
        str | None: The attribute name, or ``None`` for any other expression.

    """
    if (
        isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and node.value.id == receiver
    ):
        return node.attr
    return None


@final
@dataclass(frozen=True, slots=True)
class _Typing:
    """What typing a method's writes needs.

    Attributes:
        env (Mapping[str, str]): Types of the names visible in the method.
        counts (Mapping[str, int]): Module binding counts.
        receiver (str): Name that holds the instance.
        in_init (bool): Whether the method is the constructor.

    """

    env: Mapping[str, str]
    counts: Mapping[str, int]
    receiver: str
    in_init: bool


def _record(
    *,
    node: AST,
    typing: _Typing,
    seen: dict[str, _Attribute],
    plain: set[int],
) -> None:
    """Record one plain or augmented assignment to an instance attribute.

    Args:
        node (AST): A statement of the method.
        typing (_Typing): How to type the assigned values.
        seen (dict[str, _Attribute]): Attributes found so far, extended in
            place.
        plain (set[int]): Targets already understood, extended in place.

    """
    if isinstance(node, Assign):
        names: list[str] = [
            found
            for target in node.targets
            if (
                found := _self_attribute(node=target, receiver=typing.receiver)
            )
        ]
        if len(node.targets) != 1 or len(names) != 1:
            return
        plain.add(id(node.targets[0]))
        kind: str | None = expression_type(
            node=node.value,
            counts=typing.counts,
            env=typing.env,
        )
        slot: _Attribute = seen.setdefault(
            names[0],
            _Attribute(writes=[], augments=[]),
        )
        if kind is None:
            slot.bad = True
        else:
            slot.writes.append((node, kind, typing.in_init))
    elif isinstance(node, AugAssign):
        name: str | None = _self_attribute(
            node=node.target,
            receiver=typing.receiver,
        )
        if name is not None:
            plain.add(id(node.target))
            seen.setdefault(
                name,
                _Attribute(writes=[], augments=[]),
            ).augments.append(
                (
                    node.op,
                    expression_type(
                        node=node.value,
                        counts=typing.counts,
                        env=typing.env,
                    ),
                ),
            )


def _scan_method(
    *,
    method: Function,
    typing: _Typing,
    seen: dict[str, _Attribute],
) -> None:
    """Record the writes one method makes to its instance's attributes.

    Any write that is not a plain or augmented assignment in the method's own
    scope, or any rebinding of the receiver, makes every attribute it touches
    unprovable.

    Args:
        method (Function): Method definition.
        typing (_Typing): How to type the assigned values.
        seen (dict[str, _Attribute]): Attributes found so far, extended in
            place.

    """
    own: list[AST] = list(own_nodes(function=method))
    plain: set[int] = set()
    for node in own:
        _record(node=node, typing=typing, seen=seen, plain=plain)
    rebound: bool = any(
        typing.receiver in names_bound_by(node=node) for node in own
    )
    for node in walk(node=method):
        name: str | None = _self_attribute(node=node, receiver=typing.receiver)
        if name is None or not isinstance(node, Attribute):
            continue
        stored: bool = isinstance(node.ctx, (Store, Del))
        if (stored and id(node) not in plain) or rebound:
            seen.setdefault(
                name,
                _Attribute(writes=[], augments=[]),
            ).bad = True
    if rebound:
        for slot in seen.values():
            slot.bad = True


def _compatible(*, kind: str, augments: list[tuple[AST, str | None]]) -> bool:
    """Tell whether augmented assignments keep an attribute's type.

    Args:
        kind (str): The attribute's non-``None`` type.
        augments (list[tuple[AST, str | None]]): ``(operator, value type)`` per
            augmented assignment.

    Returns:
        bool: ``True`` when each keeps the type.

    """
    for operator, value in augments:
        if value is None:
            return False
        numeric_ok: bool = (
            kind in {"int", "float"}
            and isinstance(operator, Constants.numeric_ops)
            and (
                value in {"int", "bool"}
                or (kind == "float" and value == "float")
            )
        )
        text_ok: bool = (
            kind == "str" and isinstance(operator, Add) and value == "str"
        )
        if not (numeric_ok or text_ok):
            return False
    return True


def _agreed(*, slot: _Attribute, counts: Mapping[str, int]) -> str | None:
    """Combine the writes of one attribute into an annotation.

    Args:
        slot (_Attribute): The attribute's writes.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        str | None: ``T`` or ``T | None``, or ``None`` when the
            writes do not agree on a single simple type.

    """
    if slot.bad or not slot.writes:
        return None
    kinds: set[str] = {kind for _node, kind, _init in slot.writes}
    plain: set[str] = kinds - {"None"}
    if len(plain) != 1:
        return None
    kind: str = next(iter(plain))
    if kind not in Constants.scalars and not counts.get(
        constructor_key(name=kind),
    ):
        return None
    if not _compatible(kind=kind, augments=slot.augments):
        return None
    return f"{kind} | None" if "None" in kinds else kind


def _external_stores(*, module: Module) -> dict[str, int]:
    """Count the attribute writes in the whole module, by attribute name.

    Args:
        module (Module): Parsed module.

    Returns:
        dict[str, int]: Store and delete counts by attribute name.

    """
    found: dict[str, int] = {}
    for node in walk(node=module):
        if isinstance(node, Attribute) and isinstance(
            node.ctx,
            (Store, Del),
        ):
            found[node.attr] = found.get(node.attr, 0) + 1
    return found


@final
@dataclass(frozen=True, slots=True)
class Scope:
    """What the attribute prover knows about the module.

    Attributes:
        module (Module): Parsed module.
        counts (Mapping[str, int]): Module binding counts.
        constants (Mapping[str, str]): Types of module-level constants.
        accepted (Mapping[int, Mapping[str, str]]): Parameter hints already
            accepted, by function identity.
        index (MethodIndex): Method facts of the module.

    """

    module: Module
    counts: Mapping[str, int]
    constants: Mapping[str, str]
    accepted: Mapping[int, Mapping[str, str]]
    index: MethodIndex


@final
@dataclass(frozen=True, slots=True)
class Attributes:
    """What the attribute prover concluded about a module.

    Attributes:
        annotations (dict[int, str]): For each assignment that should carry the
            annotation (the first write in ``__init__``,
            else the first write), its annotation source.
        types (dict[int, dict[str, str]]): For each class (by identity), the
            agreed type
            of each of its instance attributes; every read
            of ``self.name`` in the class has that type.

    """

    annotations: dict[int, str]
    types: dict[int, dict[str, str]]


def attribute_annotations(*, scope: Scope) -> Attributes:
    """Find the instance attributes whose type every write proves.

    Args:
        scope (Scope): What is known about the module.

    Returns:
        Attributes: The assignments to annotate and the agreed types by class.

    """
    found: Attributes = Attributes(annotations={}, types={})
    if scope.index.dynamic_attributes or scope.index.intercepts:
        return found
    stores: dict[str, int] = _external_stores(module=scope.module)
    for cls in walk(node=scope.module):
        if isinstance(cls, ClassDef) and scope.index.class_ok(cls=cls):
            agreed: dict[str, str] = {}
            found.annotations.update(
                _class_annotations(
                    _cls=cls,
                    scope=scope,
                    stores=stores,
                    agreed=agreed,
                ),
            )
            if agreed:
                found.types[id(cls)] = agreed
    return found


def _class_annotations(
    *,
    _cls: ClassDef,
    scope: Scope,
    stores: Mapping[str, int],
    agreed: dict[str, str],
) -> dict[int, str]:
    """Annotate the attributes of one class.

    Args:
        _cls (ClassDef): A class that is safe to reason about.
        scope (Scope): What is known about the module.
        stores (Mapping[str, int]): Attribute writes in the module, by name.
        agreed (dict[str, str]): Receives each attribute's agreed type.

    Returns:
        dict[int, str]: Annotation sources by assignment identity.

    """
    seen: dict[str, _Attribute] = {}
    for method in _cls.body:
        if not isinstance(method, (FunctionDef, AsyncFunctionDef)):
            continue
        receiver: str | None = receiver_of(function=method)
        if receiver is None:
            continue
        _scan_method(
            method=method,
            typing=_Typing(
                env=scope_types(
                    function=method,
                    counts=scope.counts,
                    constants=scope.constants,
                    declared=scope.accepted.get(id(method)),
                ),
                counts=scope.counts,
                receiver=receiver,
                in_init=method.name == Constants.init,
            ),
            seen=seen,
        )
    inherited: set[str] = scope.index.inherited_names(_cls=_cls)
    found: dict[int, str] = {}
    for name, slot in seen.items():
        writes: int = len(slot.writes) + len(slot.augments)
        annotation: str | None = _agreed(slot=slot, counts=scope.counts)
        if (
            annotation is None
            or name in inherited
            or scope.index.binds(owner=_cls, name=name) > 0
            or stores.get(name, 0) != writes
        ):
            continue
        initial: list[tuple[Assign, str, bool]] = [
            item for item in slot.writes if item[2]
        ]
        found[id((initial or slot.writes)[0][0])] = annotation
        agreed[name] = annotation
    return found
