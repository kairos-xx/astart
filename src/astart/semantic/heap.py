"""Abstract allocation sites, mutable storage and alias relations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, final

from astart.semantic.values import (
    AbstractValue,
    LiteralValue,
    ObjectReference,
    UnknownValue,
    join_values,
)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HeapObject:
    """Immutable snapshot of one mutable abstract heap allocation.

    Attributes:
        allocation_node_id: Syntax identity of the allocation site, or 0
            when the object has no modeled origin.
        id: Unique abstract allocation identity.
        kind: List, dictionary, set, or user-created object.
        elements: Ordered abstract list elements, if known.
        attributes: Known key and value pairs for modeled members.
        unknown_content: True if other mutations may have changed the object.
        summary: True if one abstract allocation represents multiple objects.

    """

    id: int
    kind: Literal["list", "dict", "set", "object"]
    elements: tuple[AbstractValue, ...] = ()
    attributes: tuple[tuple[AbstractValue, AbstractValue], ...] = ()
    unknown_content: bool = False
    summary: bool = False
    allocation_node_id: int = 0


@final
class AbstractHeap:
    """Per-analysis abstract allocation registry; real objects untouched."""

    def __init__(self, *, max_objects: int = 10000) -> None:
        """Initialize empty object snapshots with monotonic identities.

        Args:
            max_objects: Maximum distinct abstract allocations before new
                sites collapse into one shared summary object.

        """
        self._next_id: int = 1
        self._max_objects: int = max_objects
        self._overflow: int | None = None
        self.objects: dict[int, HeapObject] = {}
        self._allocation_sites: dict[tuple[int, int], int] = {}

    @staticmethod
    def may_alias(*, left: AbstractValue, right: AbstractValue) -> bool:
        """Test possible overlap of abstract object identities.

        Args:
            left: First object reference.
            right: Second object reference.

        Returns:
            True when the references share a possible allocation.

        """
        return (
            isinstance(left, ObjectReference)
            and isinstance(right, ObjectReference)
            and bool(left.object_ids & right.object_ids)
        )

    @staticmethod
    def read_index(
        *,
        reference: ObjectReference,
        index: AbstractValue,
        objects: dict[int, HeapObject],
    ) -> AbstractValue:
        """Read from a known built-in abstract collection, without user calls.

        Args:
            reference: Potentially aliased object references.
            index: Index or dictionary key.
            objects: Current path-local heap snapshots.

        Returns:
            Exact, union, or unknown value.

        """
        result: AbstractValue | None = None
        for identity in sorted(reference.object_ids):
            found: HeapObject | None = objects.get(identity)
            item: AbstractValue = UnknownValue(reason="unknown heap location")
            if found is not None and not found.unknown_content:
                if (
                    found.kind == "list"
                    and isinstance(index, LiteralValue)
                    and type(index.value) is int
                ):
                    idx: int = index.value
                    if -len(found.elements) <= idx < len(found.elements):
                        item = found.elements[idx]
                elif found.kind == "dict":
                    for key, value in found.attributes:
                        if key == index:
                            item = value
                            break
            result = (
                item
                if result is None
                else join_values(left=result, right=item)
            )
        return (
            result
            if result is not None
            else UnknownValue(reason="empty points-to set")
        )

    @staticmethod
    def write_index(
        *,
        reference: ObjectReference,
        index: AbstractValue,
        value: AbstractValue,
        objects: dict[int, HeapObject],
    ) -> None:
        """Apply strong or conservative weak updates to an abstract location.

        Args:
            reference: Mutated reference.
            index: Abstract element index.
            value: Written abstract value.
            objects: Path-local heap snapshots.

        """
        unique: bool = len(reference.object_ids) == 1
        for identity in reference.object_ids:
            found: HeapObject | None = objects.get(identity)
            if found is None:
                continue
            strong: bool = unique and not found.summary
            elements: list[AbstractValue] = list(found.elements)
            attributes: list[tuple[AbstractValue, AbstractValue]] = list(
                found.attributes,
            )
            known: bool = False
            if (
                found.kind == "list"
                and isinstance(index, LiteralValue)
                and type(index.value) is int
            ):
                idx: int = index.value
                if -len(elements) <= idx < len(elements):
                    old: AbstractValue = elements[idx]
                    elements[idx] = (
                        value
                        if strong
                        else join_values(
                            left=old,
                            right=value,
                        )
                    )
                    known = True
            elif found.kind in ("dict", "object") and isinstance(
                index,
                LiteralValue,
            ):
                for pos, (key, old) in enumerate(iterable=attributes):
                    if key == index:
                        attributes[pos] = (
                            key,
                            value
                            if strong
                            else join_values(left=old, right=value),
                        )
                        known = True
                        break
                if not known and strong:
                    attributes.append((index, value))
                    known = True
            objects[identity] = HeapObject(
                id=identity,
                kind=found.kind,
                elements=tuple(elements),
                attributes=tuple(attributes),
                unknown_content=found.unknown_content or not known,
                summary=found.summary,
                allocation_node_id=found.allocation_node_id,
            )

    @staticmethod
    def havoc(
        *,
        reference: ObjectReference,
        objects: dict[int, HeapObject],
    ) -> None:
        """Invalidate known contents after an unanalyzable mutation.

        Args:
            reference: Objects potentially affected by an external call.
            objects: Path-local abstract heap snapshots.

        """
        for identity in reference.object_ids:
            found: HeapObject | None = objects.get(identity)
            if found is not None:
                objects[identity] = HeapObject(
                    id=identity,
                    kind=found.kind,
                    unknown_content=True,
                    summary=found.summary,
                    allocation_node_id=found.allocation_node_id,
                )

    def allocate(
        self,
        *,
        node_id: int,
        context_id: int,
        kind: Literal["list", "dict", "set", "object"],
        elements: tuple[AbstractValue, ...] = (),
        attributes: tuple[tuple[AbstractValue, AbstractValue], ...] = (),
    ) -> ObjectReference:
        """Allocate or reuse one abstract site for a call context.

        Args:
            node_id: Originating Python AST node identity.
            context_id: Function or call-site context identity.
            kind: Abstract object kind.
            elements: Initial sequence elements.
            attributes: Initial mapping/attribute pairs.

        Returns:
            Abstract reference; a reused site is marked summarized.

        """
        key: tuple[int, int] = (node_id, context_id)
        existing: int | None = self._allocation_sites.get(key)
        if existing is not None:
            old: HeapObject = self.objects[existing]
            self.objects[existing] = HeapObject(
                id=existing,
                kind=kind,
                elements=tuple(
                    join_values(left=a, right=b)
                    for a, b in zip(old.elements, elements, strict=False)
                )
                if len(old.elements) == len(elements)
                else (),
                attributes=old.attributes
                if old.attributes == attributes
                else (),
                unknown_content=old.unknown_content
                or (
                    len(old.elements) != len(elements)
                    or old.attributes != attributes
                ),
                summary=True,
                allocation_node_id=old.allocation_node_id,
            )
            return ObjectReference(object_ids=frozenset({existing}))
        if len(self.objects) >= self._max_objects:
            if self._overflow is None:
                self._overflow = self._next_id
                self._next_id += 1
                self.objects[self._overflow] = HeapObject(
                    id=self._overflow,
                    kind="object",
                    unknown_content=True,
                    summary=True,
                )
            return ObjectReference(
                object_ids=frozenset({self._overflow}),
            )
        identity: int = self._next_id
        self._next_id += 1
        self._allocation_sites[key] = identity
        self.objects[identity] = HeapObject(
            id=identity,
            kind=kind,
            elements=elements,
            attributes=attributes,
            allocation_node_id=node_id,
        )
        return ObjectReference(object_ids=frozenset({identity}))

    def allocation_node(self, *, object_id: int) -> int | None:
        """Return the allocation site of an abstract object, when modeled.

        Args:
            object_id: Abstract allocation identity.

        Returns:
            Syntax identity of the allocation site, or None.

        """
        found: HeapObject | None = self.objects.get(object_id)
        return (
            found.allocation_node_id
            if found is not None and found.allocation_node_id
            else None
        )

    def must_alias(self, *, left: AbstractValue, right: AbstractValue) -> bool:
        """Prove both references denote one unique unsummarized allocation.

        Args:
            left: First object reference.
            right: Second object reference.

        Returns:
            True only for provable must-alias relationships.

        """
        if not isinstance(left, ObjectReference) or not isinstance(
            right,
            ObjectReference,
        ):
            return False
        if left.object_ids != right.object_ids or len(left.object_ids) != 1:
            return False
        identity: int = next(iter(left.object_ids))
        found: HeapObject | None = self.objects.get(identity)
        return found is not None and not found.summary
