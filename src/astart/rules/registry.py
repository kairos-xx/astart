"""Registries of node kinds, facts, procedures and appliers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.rules.vocabulary import Cost

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


@final
@dataclass(frozen=True, slots=True)
class FactSpec:
    """Declare one fact a predicate may read.

    Attributes:
        name: Dotted fact name.
        value_type: One of ``bool``, ``int``, ``float`` or ``str``.
        cost: What computing the fact needs.

    """

    name: str
    value_type: str
    cost: Cost


@final
@dataclass(frozen=True, slots=True)
class Registries:
    """Vocabulary the engine supplies when a catalog is loaded.

    Attributes:
        node_kinds: Subject kinds rules may target.
        facts: Fact declarations by name.
        procedures: Keys of registered procedural triggers.
        appliers: Keys of registered edit appliers.

    """

    node_kinds: frozenset[str]
    facts: Mapping[str, FactSpec]
    procedures: frozenset[str]
    appliers: frozenset[str]

    def fact(self, *, name: str) -> FactSpec:
        """Look up a fact declaration.

        Args:
            name: Fact name.

        Returns:
            The declaration.

        Raises:
            KeyError: If the fact is not declared.

        """
        if name not in self.facts:
            known: str = ", ".join(sorted(self.facts))
            msg: str = f"fact {name!r} is not declared; known facts: {known}"
            raise KeyError(msg)
        return self.facts[name]


def rule_cost(*, registries: Registries, requires: Iterable[str]) -> Cost:
    """Compute the cost of evaluating a rule.

    Args:
        registries: Declared facts.
        requires: Fact names the rule needs.

    Returns:
        The highest cost among the facts, syntactic when none.

    """
    highest: Cost = Cost.syntactic
    for name in requires:
        cost: Cost = registries.fact(name=name).cost
        if cost.rank() > highest.rank():
            highest = cost
    return highest
