"""Shared shape for standalone rule detectors.

Detectors in this package inspect a parsed module and yield
:class:`Candidate` records — a span plus evidence — without being wired
into a catalog or registry yet. Registry and catalog entries adapt each
``find_*`` function to the engine's procedure calling convention.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.rules.model import Span

if TYPE_CHECKING:
    from ast import AST

    from astart.rules.jsonvalue import JsonValue


@final
@dataclass(frozen=True, slots=True)
class Candidate:
    """One detector hit, before it becomes a catalog finding.

    Attributes:
        span (Span): Source range the rule flags.
        evidence (dict[str, JsonValue]): Values for the rule's evidence slots.

    """

    span: Span
    evidence: dict[str, JsonValue]


def span_of(*, node: AST, filename: str) -> Span:
    """Locate an AST node for a candidate.

    Args:
        node (AST): Node carrying line and column attributes.
        filename (str): Name used in the span.

    Returns:
        Span: The node's source range.

    """
    return Span(
        file=filename,
        start_line=getattr(node, "lineno", 1),
        start_column=getattr(node, "col_offset", 0),
        end_line=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        end_column=getattr(node, "end_col_offset", 0),
    )
