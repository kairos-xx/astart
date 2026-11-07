"""Stable semantic identifiers, symbols, references, and dependency indexes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, final

from astart.node_attributes import clear_attribute, write_attribute

if TYPE_CHECKING:
    from ast import AST


@final
class Constants:
    """Group module-level constants.

    Attributes:
        inherited_attributes: Grouped module constant.

    """

    inherited_attributes: Final[tuple[str, ...]] = (
        "node_id",
        "symbol_id",
        "binding_id",
        "scope_id",
        "object_id",
        "context_id",
        "inferred_value",
        "value_evidence",
        "inferred_type",
        "inferred_type_hint",
        "call_binding",
        "type_conflicts",
        "class_contract",
    )


type Role = Literal[
    "DEFINE",
    "READ",
    "WRITE",
    "DELETE",
    "PARAMETER",
    "IMPORT",
    "CAPTURE",
    "ANNOTATION",
]
type EdgeKind = Literal[
    "READS_SYMBOL",
    "DEFINES_SYMBOL",
    "REACHES_DEFINITION",
    "DEPENDS_ON_VALUE",
    "REFERENCES_OBJECT",
    "READS_HEAP_LOCATION",
    "WRITES_HEAP_LOCATION",
    "CALLS_FUNCTION",
    "DEPENDS_ON_CONTROL",
    "CAPTURES_SYMBOL",
    "DEPENDS_ON_SCOPE",
]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Symbol:
    """Persistent lexical symbol, independent from its current name.

    Attributes:
        id: Semantic identity.
        name: Current lexical spelling.
        kind: Parameter, function, class, import, or variable.
        scope_id: Scope owning the lexical binding.
        declaration_node_id: First syntax node defining the symbol.
        origin_id: Previous-revision symbol this record descends from
            after a cross-scope relocation, or None.

    """

    id: int
    name: str
    kind: str
    scope_id: int
    declaration_node_id: int | None
    origin_id: int | None = None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Binding:
    """One definition occurrence of a symbol.

    Attributes:
        id: Assignment identity.
        symbol_id: Lexical symbol receiving the definition.
        node_id: Syntax occurrence performing the assignment.
        kind: Definition, deletion, argument, or import.

    """

    id: int
    symbol_id: int
    node_id: int
    kind: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Occurrence:
    """One syntax occurrence with one or more symbol reference roles.

    Attributes:
        node_id: Syntax occurrence identifier.
        symbol_id: Referenced lexical symbol, when statically resolvable.
        scope_id: Lexical context of the occurrence.
        roles: All operations performed by this occurrence.

    """

    node_id: int
    symbol_id: int | None
    scope_id: int
    roles: frozenset[Role]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DependencyEdge:
    """Directed, labeled semantic dependency from consumer to producer.

    Attributes:
        consumer: Node ID affected when producer changes.
        producer: Node ID supplying the semantic fact.
        kind: Kind of semantic dependence.

    """

    consumer: int
    producer: int
    kind: EdgeKind


@final
class IdentityIndex:
    """Module-owned stable node identities that survive copied metadata."""

    def __init__(self) -> None:
        """Start a fresh per-module identity allocator."""
        self._next_id: int = 1
        self._by_python_id: dict[int, tuple[AST, int]] = {}

    def node_id(self, *, node: AST) -> int:
        """Return stable syntax identity for an owned mutable AST object.

        Args:
            node: AST object; never identified by source position.

        Returns:
            Per-module persistent node identity.

        """
        existing: tuple[AST, int] | None = self._by_python_id.get(id(node))
        if existing is not None and existing[0] is node:
            return existing[1]
        for name in Constants.inherited_attributes:
            clear_attribute(node=node, name=name)
        identity: int = self._next_id
        self._next_id += 1
        self._by_python_id[id(node)] = (node, identity)
        write_attribute(node=node, name="node_id", value=identity)
        return identity

    def all_nodes(self) -> tuple[AST, ...]:
        """Return all identities owned since the first indexing.

        Returns:
            tuple[AST, ...] produced by this operation.

        """
        return tuple(item[0] for item in self._by_python_id.values())


@final
class DependencyGraph:
    """Bi-directional, labeled semantic edges with cycle-safe worklists."""

    def __init__(self) -> None:
        """Allocate empty forward and reverse edge indexes."""
        self._forward: dict[int, set[DependencyEdge]] = {}
        self._reverse: dict[int, set[DependencyEdge]] = {}

    def add(self, *, consumer: int, producer: int, kind: EdgeKind) -> None:
        """Add a dependency edge, deduplicated by all three fields.

        Args:
            consumer: Dependent node ID.
            producer: Producer node ID.
            kind: Dependency classification.

        """
        edge: DependencyEdge = DependencyEdge(
            consumer=consumer,
            producer=producer,
            kind=kind,
        )
        self._forward.setdefault(consumer, set()).add(edge)
        self._reverse.setdefault(producer, set()).add(edge)

    def remove(self, *, consumer: int, producer: int, kind: EdgeKind) -> None:
        """Remove one matching dependency edge from both indexes.

        Args:
            consumer: Dependent node ID.
            producer: Producer node ID.
            kind: Dependency classification.

        """
        edge: DependencyEdge = DependencyEdge(
            consumer=consumer,
            producer=producer,
            kind=kind,
        )
        forward: set[DependencyEdge] | None = self._forward.get(consumer)
        if forward is not None:
            forward.discard(edge)
        reverse: set[DependencyEdge] | None = self._reverse.get(producer)
        if reverse is not None:
            reverse.discard(edge)

    def dependencies(self, *, node_id: int) -> tuple[DependencyEdge, ...]:
        """List direct producer dependencies ordered deterministically.

        Args:
            node_id: Consumer identity.

        Returns:
            Producer edges.

        """
        return tuple(
            sorted(
                self._forward.get(node_id, ()),
                key=lambda edge: (edge.producer, edge.kind),
            ),
        )

    def dependents(self, *, node_id: int) -> tuple[DependencyEdge, ...]:
        """List direct consumers that rely on this node.

        Args:
            node_id: Producer identity.

        Returns:
            Consumer edges.

        """
        return tuple(
            sorted(
                self._reverse.get(node_id, ()),
                key=lambda edge: (edge.consumer, edge.kind),
            ),
        )

    def affected_by(
        self,
        *,
        node_id: int,
        exclude: frozenset[EdgeKind] = frozenset(),
    ) -> frozenset[int]:
        """Compute transitive invalidation closure without recursive revisits.

        Args:
            exclude: Edge kinds to skip while walking consumers, for
                dependencies that must not drive reanalysis.
            node_id: Mutated identity.

        Returns:
            Set of affected node identities, including the source.

        """
        seen: set[int] = set()
        pending: list[int] = [node_id]
        while pending:
            current: int = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(
                edge.consumer
                for edge in self._reverse.get(current, ())
                if edge.consumer not in seen and edge.kind not in exclude
            )
        return frozenset(seen)
