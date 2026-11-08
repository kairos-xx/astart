"""Propagate candidates through the contract graph until beliefs settle."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from astart.rules.negotiation import transfer
from astart.rules.negotiation.algebra import TypeAlgebra
from astart.rules.negotiation.beliefs import Belief
from astart.rules.negotiation.model import (
    Candidate,
    Conflict,
    Contract,
    Origin,
    Polarity,
)
from astart.rules.provable import expression_type

if TYPE_CHECKING:
    from astart.rules.negotiation.graph import ContractGraph

type _Memo = tuple[str, str, Polarity, tuple[str, ...]]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        carried_back: Contract polarities a constraint may travel back over.
        joining: Contract polarities whose missing transfer loses a type.

    """

    carried_back: Final[frozenset[Polarity]] = frozenset(
        {Polarity.declaration, Polarity.intersection},
    )
    joining: Final[frozenset[Polarity]] = frozenset(
        {Polarity.union, Polarity.declaration},
    )


@final
@dataclass(frozen=True, slots=True)
class NegotiatorConfig:
    """Bounds and decay of one negotiation.

    Attributes:
        max_iterations: Most propagation rounds.
        max_events: Most beliefs that may change in total.
        minimum_confidence: Candidates weaker than this are dropped.
        forward_decay: Factor for each contract crossed forward.
        backward_decay: Factor for each contract crossed backward.
        memo_delta: A repeated message must beat the best one by this much.
        entropy_epsilon: Entropy change below which a round counts as still.
        union_limit: Most union members a settled type may have.

    """

    max_iterations: int = 24
    max_events: int = 10000
    minimum_confidence: float = 0.02
    forward_decay: float = 0.86
    backward_decay: float = 0.63
    memo_delta: float = 0.000001
    entropy_epsilon: float = 0.0001
    union_limit: int = 3


@final
@dataclass(frozen=True, slots=True)
class Snapshot:
    """The state after one round.

    Attributes:
        iteration: Round number from zero.
        entropy: Total entropy of all beliefs.
        changed: Beliefs that changed in the round.

    """

    iteration: int
    entropy: float
    changed: int


@final
@dataclass(frozen=True, slots=True)
class Negotiation:
    """The outcome of a negotiation.

    Attributes:
        beliefs: Final belief of every node, by path text.
        snapshots: One entry per round.
        conflicts: Every conflict, sorted by path.
        exhausted: ``True`` when a bound ended the run before stability.
        lost: Paths that ended without a type: wrapper targets no candidate
            survived for and derived expressions the typer rejected.

    """

    beliefs: dict[str, Belief]
    snapshots: tuple[Snapshot, ...]
    conflicts: tuple[Conflict, ...]
    exhausted: bool
    lost: frozenset[str]

    def settled(self, *, path: str) -> str | None:
        """Give the type a node ended up with.

        Args:
            path: Path text of the node.

        Returns:
            The settled type, or ``None`` when unknown, ambiguous or in
            conflict.

        """
        belief: Belief | None = self.beliefs.get(path)
        return None if belief is None else belief.settle()


@final
@dataclass(frozen=True, slots=True)
class _Ant:
    """One message travelling through the graph.

    Attributes:
        path: Node it is arriving at.
        candidate: The proposed type.
        polarity: How it contributes there.

    """

    path: str
    candidate: Candidate
    polarity: Polarity


@final
class Negotiator:
    """Run the ant-farm propagation over a contract graph."""

    def __init__(self, *, config: NegotiatorConfig | None = None) -> None:
        """Remember the bounds.

        Args:
            config: Bounds and decay; the defaults when omitted.

        """
        self._config: NegotiatorConfig = config or NegotiatorConfig()
        self._lost: set[str] = set()
        self._derived_ok: dict[str, bool] = {}

    def solve(self, *, graph: ContractGraph) -> Negotiation:
        """Propagate until nothing changes or a bound is reached.

        Args:
            graph: Nodes, contracts and seeds.

        Returns:
            The beliefs, a snapshot per round and every conflict.

        """
        config: NegotiatorConfig = self._config
        self._lost = set()
        self._derived_ok = {}
        beliefs: dict[str, Belief] = {
            path: Belief(path=path, limit=config.union_limit)
            for path in graph.nodes
        }
        queue: deque[_Ant] = deque(
            iterable=(
                _Ant(path=path, candidate=candidate, polarity=polarity)
                for path, candidate, polarity in graph.seeds()
            ),
        )
        memo: dict[_Memo, float] = {}
        snapshots: list[Snapshot] = []
        events: int = 0
        previous: float = -1.0
        exhausted: bool = True
        for iteration in range(config.max_iterations):
            changed: int = self._round(
                graph=graph,
                beliefs=beliefs,
                queue=queue,
                memo=memo,
                budget=config.max_events - events,
            )
            events += changed
            entropy: float = sum(b.entropy() for b in beliefs.values())
            snapshots.append(
                Snapshot(
                    iteration=iteration,
                    entropy=entropy,
                    changed=changed,
                ),
            )
            if not queue:
                exhausted = False
                break
            if events >= config.max_events:
                break
            if (
                changed == 0
                and abs(entropy - previous) < config.entropy_epsilon
            ):
                exhausted = False
                break
            previous = entropy
        failed: set[str] = {
            item.target
            for item in graph.derived()
            if not self._derived_ok.get(item.target, False)
        }
        return Negotiation(
            beliefs=beliefs,
            snapshots=tuple(snapshots),
            conflicts=tuple(
                conflict
                for path in sorted(beliefs)
                for conflict in beliefs[path].conflicts
            ),
            exhausted=exhausted,
            lost=frozenset(self._lost | failed),
        )

    def _round(
        self,
        *,
        graph: ContractGraph,
        beliefs: dict[str, Belief],
        queue: deque[_Ant],
        memo: dict[_Memo, float],
        budget: int,
    ) -> int:
        """Process the messages queued at the start of the round.

        Args:
            graph: The contract graph.
            beliefs: Beliefs by path, updated in place.
            queue: Pending messages; new ones are appended.
            memo: Best confidence seen per message identity.
            budget: Most beliefs this round may change.

        Returns:
            How many beliefs changed.

        """
        changed: int = 0
        for _ in range(len(queue)):
            if changed >= budget:
                queue.clear()
                break
            ant: _Ant = queue.popleft()
            if not self._fresh(ant=ant, memo=memo):
                continue
            belief: Belief | None = beliefs.get(ant.path)
            if belief is None:
                continue
            if belief.add(candidate=ant.candidate, polarity=ant.polarity):
                changed += 1
                self._spread(
                    graph=graph,
                    ant=ant,
                    belief=belief,
                    queue=queue,
                )
                self._derive(
                    graph=graph,
                    path=ant.path,
                    beliefs=beliefs,
                    queue=queue,
                )
        return changed

    def _fresh(self, *, ant: _Ant, memo: dict[_Memo, float]) -> bool:
        """Tell whether a message adds anything over the ones seen.

        Args:
            ant: The message.
            memo: Best confidence seen per message identity; updated.

        Returns:
            ``True`` when it is new or clearly stronger.

        """
        key: _Memo = (
            ant.path,
            ant.candidate.type_text,
            ant.polarity,
            tuple(sorted(origin.value for origin in ant.candidate.origins)),
        )
        best: float = memo.get(key, -1.0)
        if ant.candidate.confidence <= best + self._config.memo_delta:
            return False
        memo[key] = ant.candidate.confidence
        return True

    def _derive(
        self,
        *,
        graph: ContractGraph,
        path: str,
        beliefs: dict[str, Belief],
        queue: deque[_Ant],
    ) -> None:
        """Evaluate the derived nodes that read a node that just changed.

        A derived node is typed only when every operand has settled; the
        syntax typer then types its expression, and the result replaces what
        the node was given before.

        Args:
            graph: The contract graph.
            path: The node that changed.
            beliefs: Beliefs by path.
            queue: Pending messages; the result is appended.

        """
        for derived in graph.derived_from(path=path):
            env: dict[str, str] = dict(derived.fixed)
            origins: set[Origin] = set()
            confidence: float = 1.0
            ready: bool = True
            for placeholder, part in derived.parts:
                belief: Belief | None = beliefs.get(part)
                settled: str | None = (
                    None if belief is None else belief.settle()
                )
                if belief is None or settled is None:
                    ready = False
                    break
                env[placeholder] = settled
                support: list[Candidate] = belief.support()
                origins |= {o for item in support for o in item.origins}
                confidence = min(
                    confidence,
                    max(item.confidence for item in support),
                )
            if not ready:
                continue
            typed: str | None = expression_type(
                node=derived.template,
                counts={},
                env=env,
            )
            self._derived_ok[derived.target] = typed is not None
            if typed is None:
                continue
            queue.append(
                _Ant(
                    path=derived.target,
                    candidate=Candidate(
                        type_text=typed,
                        confidence=confidence * self._config.forward_decay,
                        distance=1,
                        origins=frozenset(origins)
                        or frozenset({Origin.syntax}),
                        explanation=derived.explanation,
                        slot=f"derived:{derived.target}",
                    ),
                    polarity=Polarity.union,
                ),
            )

    @staticmethod
    def _leaving(*, belief: Belief, ant: _Ant) -> list[Candidate]:
        """Pick the candidates that leave a node after it changed.

        A value leaving a narrowed node is narrowed too. A constraint that
        has just arrived is not forwarded itself; it re-sends what the node
        holds, now narrowed.

        Args:
            belief: The node's belief after the change.
            ant: The message that changed it.

        Returns:
            The candidates to send forward.

        """
        pool: list[Candidate] = (
            [belief.candidates[key] for key in sorted(belief.candidates)]
            if ant.polarity is Polarity.intersection
            else [ant.candidate]
        )
        narrowed: list[Candidate | None] = [
            belief.narrowed(candidate=item) for item in pool
        ]
        return [item for item in narrowed if item is not None]

    def _joined(
        self,
        *,
        belief: Belief,
        contract: Contract,
    ) -> list[Candidate]:
        """Join everything a node holds into one candidate for a wrapper.

        A container's element type is the union of all its elements, so the
        wrapper must see that union, and it replaces what the same contract
        sent before.

        Args:
            belief: The element node's belief.
            contract: The wrapping contract.

        Returns:
            One candidate, or none when nothing can be said.

        """
        held: list[Candidate] = [
            narrowed
            for key in sorted(belief.candidates)
            if (narrowed := belief.narrowed(candidate=belief.candidates[key]))
            is not None
        ]
        joined: str | None = TypeAlgebra().union(
            types=[item.type_text for item in held],
            limit=self._config.union_limit,
        )
        if joined is None:
            return []
        return [
            Candidate(
                type_text=joined,
                confidence=max(item.confidence for item in held),
                distance=min(item.distance for item in held),
                origins=frozenset(
                    origin for item in held for origin in item.origins
                ),
                explanation=held[0].explanation,
                slot=f"{contract.source}>{contract.target}",
            ),
        ]

    def _spread(
        self,
        *,
        graph: ContractGraph,
        ant: _Ant,
        belief: Belief,
        queue: deque[_Ant],
    ) -> None:
        """Queue the messages a changed belief sends to its neighbours.

        Args:
            graph: The contract graph.
            ant: The message that changed the belief.
            belief: The node's belief after the change.
            queue: Pending messages; new ones are appended.

        """
        sent: list[Candidate] = self._leaving(belief=belief, ant=ant)
        for contract in graph.outgoing(path=ant.path):
            if contract.polarity is Polarity.capability:
                continue
            wraps: bool = contract.relation in transfer.Constants.wrappers
            outgoing: list[Candidate] = (
                self._joined(belief=belief, contract=contract)
                if wraps
                else sent
            )
            if wraps and not outgoing:
                self._lost.add(contract.target)
            for candidate in outgoing:
                moved: Candidate | None = transfer.forward(
                    candidate=candidate,
                    relation=contract.relation,
                )
                if moved is None and contract.polarity in Constants.joining:
                    self._lost.add(contract.target)
                self._enqueue(
                    queue=queue,
                    moved=moved,
                    contract=contract,
                    forward=True,
                )
        for contract in graph.incoming(path=ant.path):
            if contract.polarity not in Constants.carried_back:
                continue
            self._enqueue(
                queue=queue,
                moved=transfer.backward(
                    candidate=ant.candidate,
                    relation=contract.relation,
                ),
                contract=contract,
                forward=False,
            )

    def _enqueue(
        self,
        *,
        queue: deque[_Ant],
        moved: Candidate | None,
        contract: Contract,
        forward: bool,
    ) -> None:
        """Queue one message when it is still strong enough.

        Args:
            queue: Pending messages.
            moved: The transferred candidate, or ``None``.
            contract: The contract crossed.
            forward: Whether the message follows the contract's direction.

        """
        if moved is None:
            return
        config: NegotiatorConfig = self._config
        weakened: Candidate = moved.decayed(
            decay=contract.confidence
            * contract.decay
            * (config.forward_decay if forward else config.backward_decay),
        )
        if weakened.confidence < config.minimum_confidence:
            return
        narrowing: bool = (
            not forward or contract.polarity is Polarity.intersection
        )
        queue.append(
            _Ant(
                path=contract.target if forward else contract.source,
                candidate=weakened,
                polarity=(
                    Polarity.intersection if narrowing else Polarity.union
                ),
            ),
        )
