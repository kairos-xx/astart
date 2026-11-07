"""Incremental, deletion-safe, deterministic forward dataflow solver.

The engine owns immutable fact mappings and accepts pure transfer
functions.  It recomputes joins from predecessor outputs, rather than
monotonically unioning previous inputs, so changed or deleted facts can be
removed at a fixed point.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, final

type Facts = dict[int, frozenset[int]]
type Transfer = Callable[[int, Facts], Facts]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SolveStatistics:
    """Counters for one incremental worklist pass.

    Attributes:
        changed: Changed retained as frozenset[int] by this instance.
        converged: Converged retained as bool by this instance.
        transfers: Transfers retained as int by this instance.
        visited: Visited retained as frozenset[int] by this instance.

    """

    transfers: int
    changed: frozenset[int]
    visited: frozenset[int]
    converged: bool


@final
class IncrementalWorklist:
    """Compute and incrementally maintain a forward may-analysis fixed point.

    Transfer functions must be deterministic, monotone, and have finite-height
    fact lattices.  When the caller changes the graph, it must pass changed
    nodes as dirty nodes; changed predecessors are discovered automatically.
    """

    def __init__(
        self,
        *,
        successors: Mapping[int, tuple[int, ...]],
        entry: int,
        transfer: Transfer,
        max_transfers: int = 100_000,
    ) -> None:
        """Initialize graph and an initially empty dataflow solution.

        Args:
            entry: Entry supplied as int for this operation.
            max_transfers: Max transfers supplied as int for this operation.
            successors: Successors supplied as Mapping[int, tuple[int, ...]]
                for this operation.
            transfer: Transfer supplied as Transfer for this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        if entry not in successors:
            msg: str = "Entry block is not present in the dataflow graph."
            raise ValueError(msg)
        if max_transfers < 1:
            msg = "max_transfers must be positive."
            raise ValueError(msg)
        self._successors: dict[int, tuple[int, ...]] = dict(successors)
        self._predecessors: dict[int, set[int]] = self._reverse(
            successors=self._successors,
        )
        self._entry: Final[int] = entry
        self._transfer: Transfer = transfer
        self._maximum: Final[int] = max_transfers
        self.incoming: dict[int, Facts] = {}
        self.outgoing: dict[int, Facts] = {}
        self.statistics: SolveStatistics = SolveStatistics(
            transfers=0,
            changed=frozenset(),
            visited=frozenset(),
            converged=True,
        )

    def update_graph(
        self,
        *,
        successors: Mapping[int, tuple[int, ...]],
        dirty: frozenset[int] = frozenset(),
    ) -> SolveStatistics:
        """Replace edges, drop vanished blocks and solve the affected part.

        Args:
            dirty: Dirty supplied as frozenset[int] for this operation.
            successors: Successors supplied as Mapping[int, tuple[int, ...]]
                for this operation.

        Returns:
            SolveStatistics produced by this operation.

        """
        updated: dict[int, tuple[int, ...]] = dict(successors)
        reverse: dict[int, set[int]] = self._reverse(successors=updated)
        affected: set[int] = set(dirty)
        for identity in self._successors.keys() | updated.keys():
            if self._successors.get(identity) != updated.get(identity):
                affected.add(identity)
                affected.update(self._successors.get(identity, ()))
                affected.update(updated.get(identity, ()))
        self._successors = updated
        self._predecessors = reverse
        self.incoming = {
            identity: value
            for identity, value in self.incoming.items()
            if identity in updated
        }
        self.outgoing = {
            identity: value
            for identity, value in self.outgoing.items()
            if identity in updated
        }
        return self.solve(dirty=frozenset(affected & updated.keys()))

    def solve(self, *, dirty: frozenset[int] | None = None) -> SolveStatistics:
        """Recompute only the transitive dependents of changed transfer facts.

        A first solve starts from the entry and traverses reachable blocks. On
        subsequent solves, a supplied dirty set seeds only changed blocks.
        A result that exceeds the budget is marked non-converged and MUST NOT
        be used as a sound fixed point by callers.


        Args:
            dirty: Dirty supplied as frozenset[int] | None for this operation.

        Returns:
            SolveStatistics produced by this operation.

        """
        initial: tuple[int, ...] = (
            (self._entry,)
            if dirty is None and not self.outgoing
            else tuple(sorted(self._successors))
            if dirty is None
            else tuple(sorted(dirty & self._successors.keys()))
        )
        # Clear the entire downstream region before a differential pass.
        # Otherwise an obsolete fact can sustain itself around a cycle after
        # its original producer is deleted (a non-least fixed point).
        original: dict[int, Facts] = {
            identity: dict(value) for identity, value in self.outgoing.items()
        }
        if dirty is not None:
            initial = self._invalidate_downstream(seeds=initial)
        pending: deque[int] = deque(iterable=initial)
        queued: set[int] = set(initial)
        changed: set[int] = set()
        visited: set[int] = set()
        transfers: int = 0
        while pending and transfers < self._maximum:
            identity: int = pending.popleft()
            queued.remove(identity)
            visited.add(identity)
            incoming: Facts = self._join(
                values=tuple(
                    self.outgoing.get(source, {})
                    for source in sorted(self._predecessors[identity])
                ),
            )
            # A reachable entry is always reachable, even without predecessors.
            if identity == self._entry:
                incoming = self._join(values=(incoming, {}))
            previous: Facts | None = self.outgoing.get(identity)
            result: Facts = self._transfer(identity, dict(incoming))
            transfers += 1
            self.incoming[identity] = incoming
            if result != previous:
                self.outgoing[identity] = dict(result)
                changed.add(identity)
                for target in self._successors[identity]:
                    if target not in queued:
                        pending.append(target)
                        queued.add(target)
        self.statistics = SolveStatistics(
            transfers=transfers,
            changed=frozenset(
                identity
                for identity in changed
                if self.outgoing.get(identity, {})
                != original.get(identity, {})
            ),
            visited=frozenset(visited),
            converged=not pending,
        )
        return self.statistics

    @staticmethod
    def _reverse(
        *,
        successors: Mapping[int, tuple[int, ...]],
    ) -> dict[int, set[int]]:
        """Build a complete reverse index and reject dangling edge targets.

        Args:
            successors: Successors supplied as Mapping[int, tuple[int, ...]]
                for this operation.

        Returns:
            dict[int, set[int]] produced by this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        reverse: dict[int, set[int]] = {
            identity: set() for identity in successors
        }
        for origin, targets in successors.items():
            for target in targets:
                if target not in reverse:
                    msg: str = f"Unknown successor block {target}."
                    raise ValueError(msg)
                reverse[target].add(origin)
        return reverse

    @staticmethod
    def _join(*, values: tuple[Facts, ...]) -> Facts:
        """Join incoming finite sets of facts deterministically.

        Args:
            values: Values supplied as tuple[Facts, ...] for this operation.

        Returns:
            Facts produced by this operation.

        """
        merged: Facts = {}
        for item in values:
            for identity, definitions in item.items():
                merged[identity] = (
                    merged.get(identity, frozenset()) | definitions
                )
        return merged

    def _invalidate_downstream(
        self,
        *,
        seeds: tuple[int, ...],
    ) -> tuple[int, ...]:
        """Drop the facts of every block reachable from ``seeds``.

        Args:
            seeds: Blocks whose transfer facts changed.

        Returns:
            Sorted identities of the seeds and all their transitive successors.

        """
        affected: set[int] = set(seeds)
        stack: list[int] = list(seeds)
        while stack:
            for target in self._successors[stack.pop()]:
                if target not in affected:
                    affected.add(target)
                    stack.append(target)
        for identity in affected:
            self.incoming.pop(identity, None)
            self.outgoing.pop(identity, None)
        return tuple(sorted(affected))
