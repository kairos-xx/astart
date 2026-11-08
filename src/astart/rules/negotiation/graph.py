"""The graph of contracts between nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.rules.negotiation.model import Candidate, Contract, Polarity

if TYPE_CHECKING:
    from ast import expr

type _Key = tuple[str, str, str, str]


def _candidate_key(
    *,
    candidate: Candidate,
) -> tuple[str, float, tuple[str, ...], str]:
    """Order candidates without depending on insertion order.

    Args:
        candidate: Any candidate.

    Returns:
        A sortable key.

    """
    return (
        candidate.type_text,
        -candidate.confidence,
        tuple(sorted(origin.value for origin in candidate.origins)),
        candidate.explanation,
    )


@final
@dataclass(frozen=True, slots=True)
class Derived:
    """A node whose type is an expression over other nodes.

    Attributes:
        target: Path of the node holding the expression's value.
        template: The expression with each operand replaced by a placeholder
            name; the syntax typer evaluates it once the operands settle.
        parts: ``(placeholder, node path)`` for every operand.
        fixed: ``(name, type text)`` pairs for names the template reads
            whose type is already known.
        explanation: The source text of the expression.

    """

    target: str
    template: expr
    parts: tuple[tuple[str, str], ...]
    fixed: tuple[tuple[str, str], ...]
    explanation: str


@final
class ContractGraph:
    """Nodes, contracts and seed candidates, queried in a stable order."""

    def __init__(self) -> None:
        """Start with an empty graph."""
        self._nodes: set[str] = set()
        self._contracts: dict[_Key, Contract] = {}
        self._seeds: dict[str, list[tuple[Candidate, Polarity]]] = {}
        self._derived: dict[str, Derived] = {}
        self._out: dict[str, list[Contract]] | None = None
        self._in: dict[str, list[Contract]] | None = None

    def add_node(self, *, path: str) -> None:
        """Make sure a node exists.

        Args:
            path: Path text of the node.

        """
        self._nodes.add(path)

    def add_contract(self, *, contract: Contract) -> None:
        """Add a contract, keeping the stronger of two equal ones.

        Args:
            contract: The contract; both ends become nodes.

        """
        self._nodes.update((contract.source, contract.target))
        key: _Key = (
            contract.source,
            contract.target,
            contract.relation.value,
            contract.polarity.value,
        )
        current: Contract | None = self._contracts.get(key)
        if current is None or contract.confidence > current.confidence:
            self._contracts[key] = contract
        self._out = None
        self._in = None

    def add_derived(self, *, derived: Derived) -> None:
        """Add a node that is an expression over other nodes.

        Args:
            derived: The expression and its operands; every path becomes a
                node.

        """
        self._nodes.add(derived.target)
        self._nodes.update(path for _name, path in derived.parts)
        self._derived[derived.target] = derived

    def derived(self) -> tuple[Derived, ...]:
        """List every derived node in a stable order.

        Returns:
            The derived nodes sorted by target.

        """
        return tuple(self._derived[key] for key in sorted(self._derived))

    def derived_from(self, *, path: str) -> tuple[Derived, ...]:
        """List the derived nodes that read a node.

        Args:
            path: Path text of the operand.

        Returns:
            The derived nodes sorted by target.

        """
        return tuple(
            item
            for item in self.derived()
            if any(part == path for _name, part in item.parts)
        )

    def feeds(self, *, path: str) -> bool:
        """Tell whether a node's type goes anywhere.

        Args:
            path: Path text of the node.

        Returns:
            ``True`` when a contract or a derived node reads it.

        """
        return bool(self.outgoing(path=path)) or bool(
            self.derived_from(path=path),
        )

    def seed(
        self,
        *,
        path: str,
        candidate: Candidate,
        polarity: Polarity = Polarity.union,
    ) -> None:
        """Start a candidate at a node.

        Args:
            path: Path text of the node.
            candidate: The seed type.
            polarity: How it contributes at the node.

        """
        self._nodes.add(path)
        self._seeds.setdefault(path, []).append((candidate, polarity))

    @property
    def nodes(self) -> tuple[str, ...]:
        """List every node.

        Returns:
            The path texts, sorted.

        """
        return tuple(sorted(self._nodes))

    def seeds(self) -> tuple[tuple[str, Candidate, Polarity], ...]:
        """List every seed in a stable order.

        Returns:
            ``(path, candidate, polarity)`` sorted by path and candidate.

        """
        return tuple(
            (path, candidate, polarity)
            for path in sorted(self._seeds)
            for candidate, polarity in sorted(
                self._seeds[path],
                key=lambda item: (
                    _candidate_key(candidate=item[0]),
                    item[1].value,
                ),
            )
        )

    def has_input(self, *, path: str) -> bool:
        """Tell whether anything can give a node a type.

        Args:
            path: Path text of the node.

        Returns:
            ``True`` when the node has a seed or an incoming contract.

        """
        return (
            path in self._seeds
            or path in self._derived
            or bool(self.incoming(path=path))
        )

    def outgoing(self, *, path: str) -> tuple[Contract, ...]:
        """List the contracts leaving a node.

        Args:
            path: Path text of the node.

        Returns:
            The contracts sorted by target, relation and polarity.

        """
        if self._out is None:
            self._index()
        return tuple((self._out or {}).get(path, ()))

    def incoming(self, *, path: str) -> tuple[Contract, ...]:
        """List the contracts reaching a node.

        Args:
            path: Path text of the node.

        Returns:
            The contracts sorted by source, relation and polarity.

        """
        if self._in is None:
            self._index()
        return tuple((self._in or {}).get(path, ()))

    def _index(self) -> None:
        """Build the sorted adjacency lists."""
        outgoing: dict[str, list[Contract]] = {}
        incoming: dict[str, list[Contract]] = {}
        for key in sorted(self._contracts):
            contract: Contract = self._contracts[key]
            outgoing.setdefault(contract.source, []).append(contract)
            incoming.setdefault(contract.target, []).append(contract)
        self._out = outgoing
        self._in = incoming
