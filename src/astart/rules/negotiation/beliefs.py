"""What is currently believed about one node."""

from __future__ import annotations

from math import log2
from typing import Final, final

from astart.rules.negotiation.algebra import Intersection, TypeAlgebra
from astart.rules.negotiation.model import (
    Candidate,
    Conflict,
    Origin,
    Polarity,
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        default_limit: Most union members a settled type may have.
        not_none: Constraint text that removes ``None`` from a type.

    """

    default_limit: Final[int] = 3
    not_none: Final[str] = "!None"


@final
class Belief:
    """The candidates, conflicts and declaration of one node.

    Attributes:
        path: Path text of the node.
        candidates: Current candidates by type text.
        constraints: Narrowing types by text; they apply when the belief
            settles, so the result does not depend on arrival order.
        declared: The hard declaration, when the node has one.

    """

    def __init__(
        self,
        *,
        path: str,
        limit: int = Constants.default_limit,
    ) -> None:
        """Start with an empty belief.

        Args:
            path: Path text of the node.
            limit: Most union members a settled type may have.

        """
        self.path: str = path
        self.candidates: dict[str, Candidate] = {}
        self.constraints: dict[str, Candidate] = {}
        self._recorded: list[Conflict] = []
        self.declared: Candidate | None = None
        self._limit: int = limit
        self._algebra: TypeAlgebra = TypeAlgebra()

    def add(self, *, candidate: Candidate, polarity: Polarity) -> bool:
        """Fold one candidate into the belief.

        Args:
            candidate: The proposed type.
            polarity: How it contributes.

        Returns:
            ``True`` when the belief changed.

        """
        if polarity is Polarity.capability:
            return False
        if polarity is Polarity.declaration:
            return self._declare(candidate=candidate)
        if polarity is Polarity.conflict:
            return self._clash(candidate=candidate)
        if polarity is Polarity.intersection:
            return self._narrow(candidate=candidate)
        return self._join(candidate=candidate)

    def entropy(self) -> float:
        """Measure how undecided the belief is.

        Returns:
            Shannon entropy of the normalized candidate confidences.

        """
        total: float = sum(
            item.confidence for item in self.candidates.values()
        )
        if total <= 0.0:
            return 0.0
        return -sum(
            (item.confidence / total) * log2(item.confidence / total)
            for item in self.candidates.values()
            if item.confidence > 0.0
        )

    @property
    def conflicts(self) -> list[Conflict]:
        """List every conflict, recorded or implied by the constraints.

        Returns:
            Recorded clashes plus one per constraint that no value of the
            current candidates can satisfy.

        """
        found: list[Conflict] = list(self._recorded)
        base: str | None = self._base()
        if base is None:
            return found
        for text in sorted(self.constraints):
            if text == Constants.not_none:
                continue
            result: Intersection = self._algebra.intersect(
                left=base,
                right=text,
            )
            if result.decided and result.type_text is None:
                found.append(
                    Conflict(
                        path=self.path,
                        left=base,
                        right=text,
                        explanation=self.constraints[text].explanation,
                    ),
                )
        return found

    def support(self) -> list[Candidate]:
        """List what the settled type rests on.

        Returns:
            The candidates, or the constraints when there are no candidates
            (a declared upper bound travelling backward).

        """
        return list(
            self.candidates.values()
            if self.candidates
            else self.constraints.values(),
        )

    def origins(self) -> frozenset[Origin]:
        """Collect everything that supports the current candidates.

        Returns:
            The union of the candidates' origins.

        """
        return frozenset(
            origin
            for item in self.candidates.values()
            for origin in item.origins
        )

    def settle(self) -> str | None:
        """Decide the one type the evidence supports.

        Returns:
            The declaration or the union of all candidates, narrowed by every
            constraint; ``None`` while a conflict is open, when nothing is
            known, or when the union has more members than allowed.

        """
        if self.conflicts:
            return None
        current: str | None = self._base()
        if current is None:
            return None
        for text in sorted(self.constraints):
            current = self._apply(current=current, constraint=text)
            if current is None:
                return None
        return current

    def narrowed(self, *, candidate: Candidate) -> Candidate | None:
        """Apply this node's constraints to a candidate that leaves it.

        Args:
            candidate: A candidate the node holds or has just received.

        Returns:
            The candidate with its type narrowed, or ``None`` when nothing of
            it survives.

        """
        current: str = candidate.type_text
        for text in sorted(self.constraints):
            applied: str | None = self._apply(
                current=current,
                constraint=text,
            )
            if applied is None:
                return None
            current = applied
        return candidate.retyped(type_text=current)

    def _base(self) -> str | None:
        """Combine the candidates before any narrowing.

        Returns:
            The declaration, the union of the candidates, or the meet of the
            constraints when there are no candidates; ``None`` when unknown.

        """
        if self.declared is not None:
            return self.declared.type_text
        if self.candidates:
            return self._algebra.union(
                types=[item.type_text for item in self.candidates.values()],
                limit=self._limit,
            )
        bound: str | None = None
        for text in sorted(self.constraints):
            if text == Constants.not_none:
                return None
            if bound is None:
                bound = text
                continue
            result: Intersection = self._algebra.intersect(
                left=bound,
                right=text,
            )
            if not result.decided or result.type_text is None:
                return None
            bound = result.type_text
        return bound

    def _apply(self, *, current: str, constraint: str) -> str | None:
        """Narrow a type by one constraint.

        Args:
            current: The type so far.
            constraint: Constraint text.

        Returns:
            The narrowed type; unchanged when the relation is unknown.

        """
        if constraint == Constants.not_none:
            kept: list[str] = [
                member
                for member in self._algebra.members(source=current)
                if member != "None"
            ]
            return " | ".join(kept) if kept else None
        result: Intersection = self._algebra.intersect(
            left=current,
            right=constraint,
        )
        return result.type_text if result.decided else current

    def _declare(self, *, candidate: Candidate) -> bool:
        """Record a hard declaration.

        Args:
            candidate: The declared type.

        Returns:
            ``True`` when the declaration is new.

        """
        if self.declared is None:
            self.declared = candidate
            for current in self.candidates.values():
                self._check_against_declaration(candidate=current)
            self.candidates = {candidate.type_text: candidate}
            return True
        if self.declared.type_text != candidate.type_text:
            self._record(left=self.declared.type_text, candidate=candidate)
        return False

    def _check_against_declaration(self, *, candidate: Candidate) -> None:
        """Record a conflict when a candidate cannot satisfy the declaration.

        Args:
            candidate: A candidate that was believed before or after.

        """
        if self.declared is None:
            return
        result: Intersection = self._algebra.intersect(
            left=self.declared.type_text,
            right=candidate.type_text,
        )
        if result.decided and result.type_text != candidate.type_text:
            self._record(left=self.declared.type_text, candidate=candidate)

    def _join(self, *, candidate: Candidate) -> bool:
        """Union a candidate into the belief.

        Args:
            candidate: The proposed type.

        Returns:
            ``True`` when the belief changed.

        """
        if self.declared is not None:
            before: int = len(self._recorded)
            self._check_against_declaration(candidate=candidate)
            return len(self._recorded) != before
        replaced: bool = False
        if candidate.slot:
            for key in [
                key
                for key, held in self.candidates.items()
                if held.slot == candidate.slot and key != candidate.type_text
            ]:
                del self.candidates[key]
                replaced = True
        current: Candidate | None = self.candidates.get(candidate.type_text)
        if current is None:
            self.candidates[candidate.type_text] = candidate
            return True
        if replaced:
            return True
        merged: Candidate = Candidate(
            type_text=candidate.type_text,
            confidence=max(current.confidence, candidate.confidence),
            distance=min(current.distance, candidate.distance),
            origins=current.origins | candidate.origins,
            explanation=current.explanation,
            slot=current.slot,
        )
        if merged == current:
            return False
        self.candidates[candidate.type_text] = merged
        return True

    def _narrow(self, *, candidate: Candidate) -> bool:
        """Remember a narrowing constraint.

        Args:
            candidate: The narrowing type.

        Returns:
            ``True`` when the constraint, or an origin of it, is new.

        """
        current: Candidate | None = self.constraints.get(candidate.type_text)
        if current is None:
            self.constraints[candidate.type_text] = candidate
            return True
        merged: Candidate = Candidate(
            type_text=candidate.type_text,
            confidence=max(current.confidence, candidate.confidence),
            distance=min(current.distance, candidate.distance),
            origins=current.origins | candidate.origins,
            explanation=current.explanation,
        )
        if merged == current:
            return False
        self.constraints[candidate.type_text] = merged
        return True

    def _clash(self, *, candidate: Candidate) -> bool:
        """Record a conflict against every differing candidate.

        Args:
            candidate: The clashing type.

        Returns:
            ``True`` when a conflict was recorded.

        """
        before: int = len(self._recorded)
        for current in list(self.candidates.values()):
            if current.type_text != candidate.type_text:
                self._record(left=current.type_text, candidate=candidate)
        return len(self._recorded) != before

    def _record(self, *, left: str, candidate: Candidate) -> None:
        """Remember one conflict once.

        Args:
            left: The type already believed.
            candidate: The type that clashes with it.

        """
        found: Conflict = Conflict(
            path=self.path,
            left=left,
            right=candidate.type_text,
            explanation=candidate.explanation,
        )
        if found not in self._recorded:
            self._recorded.append(found)
