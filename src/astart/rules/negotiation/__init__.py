"""Two-way type negotiation over a graph of contracts.

Entities are nodes, facts about the program are directed contracts between
them, and typed candidates travel forward and backward along the contracts
until every belief stops changing. See ``docs/planning/TODO.md`` chapter 10
(contract negotiation).

"""

from __future__ import annotations

from astart.rules.negotiation.algebra import Intersection, TypeAlgebra
from astart.rules.negotiation.beliefs import Belief
from astart.rules.negotiation.graph import ContractGraph
from astart.rules.negotiation.model import (
    Candidate,
    Conflict,
    Contract,
    Origin,
    Polarity,
    Relation,
)
from astart.rules.negotiation.negotiator import (
    Negotiation,
    Negotiator,
    NegotiatorConfig,
    Snapshot,
)

__all__: list[str] = [
    "Belief",
    "Candidate",
    "Conflict",
    "Contract",
    "ContractGraph",
    "Intersection",
    "Negotiation",
    "Negotiator",
    "NegotiatorConfig",
    "Origin",
    "Polarity",
    "Relation",
    "Snapshot",
    "TypeAlgebra",
]
