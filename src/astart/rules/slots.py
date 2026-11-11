"""Evidence slots: named buckets where sources deposit type claims."""

from __future__ import annotations

from typing import final


@final
class SlotTable:
    """Collect type claims per slot until they settle to one type.

    A slot gathers ``(kind, source)`` deposits. ``settle`` answers with the
    kind only when exactly one kind has claims, so disagreeing evidence
    stays unresolved instead of being guessed.

    """

    def __init__(self) -> None:
        """Create an empty table."""
        self._claims: dict[str, dict[str, set[str]]] = {}

    def deposit(self, *, slot: str, kind: str, source: str) -> None:
        """Record that ``source`` claims ``kind`` for ``slot``.

        Args:
            slot (str): Slot name the claim belongs to.
            kind (str): Claimed type.
            source (str): Evidence source identifier.

        """
        self._claims.setdefault(slot, {}).setdefault(kind, set()).add(source)

    def claims(self, *, slot: str) -> dict[str, set[str]]:
        """Return the slot's kind-to-sources mapping.

        Args:
            slot (str): Slot name to inspect.

        Returns:
            dict[str, set[str]]: A copy of kind → set of evidence sources;
                empty when the slot was never deposited into.

        """
        return {
            kind: set(sources)
            for kind, sources in self._claims.get(slot, {}).items()
        }

    def settle(self, *, slot: str) -> str | None:
        """Return the slot's kind when exactly one kind has claims.

        Args:
            slot (str): Slot name to settle.

        Returns:
            str | None: The single claimed kind, or ``None`` when
                the slot is empty or kinds disagree.

        """
        kinds: dict[str, set[str]] | None = self._claims.get(slot)
        if kinds is None or len(kinds) != 1:
            return None
        return next(iter(kinds))
