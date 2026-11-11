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
        name (str): Dotted fact name.
        value_type (str): One of ``bool``, ``int``, ``float`` or ``str``.
        cost (Cost): What computing the fact needs.

    """

    name: str
    value_type: str
    cost: Cost


@final
@dataclass(frozen=True, slots=True)
class Registries:
    """Vocabulary the engine supplies when a catalog is loaded.

    Attributes:
        node_kinds (frozenset[str]): Subject kinds rules may target.
        facts (Mapping[str, FactSpec]): Fact declarations by name.
        procedures (frozenset[str]): Keys of registered procedural triggers.
        appliers (frozenset[str]): Keys of registered edit appliers.

    """

    node_kinds: frozenset[str]
    facts: Mapping[str, FactSpec]
    procedures: frozenset[str]
    appliers: frozenset[str]

    def fact(self, *, name: str) -> FactSpec:
        """Look up a fact declaration.

        Args:
            name (str): Fact name.

        Returns:
            FactSpec: The declaration.

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
        registries (Registries): Declared facts.
        requires (Iterable[str]): Fact names the rule needs.

    Returns:
        Cost: The highest cost among the facts, syntactic when none.

    """
    highest: Cost = Cost.syntactic
    for name in requires:
        cost: Cost = registries.fact(name=name).cost
        if cost.rank() > highest.rank():
            highest = cost
    return highest
