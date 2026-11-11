"""SUP001 ``suppression.marker-comment``: checker suppression comments.

Suppression comments are forbidden: a finding is fixed, not silenced.
The detector flags every comment the tokenizer recognized as a
suppression directive — ``noqa``, ``type: ignore``, ``pylint:
disable`` and friends — keeping ``enable``/``on`` reversals quiet.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart.rules.procedural import Candidate, span_of
from astart.source.ast import SuppressionComment

if TYPE_CHECKING:
    from astart import CommentedModule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        suppressive_actions (Final[frozenset[str]]): Directive actions that
            hide diagnostics.
        evidence_tool (str): Evidence key for the directive's tool.
        evidence_action (str): Evidence key for the directive's action.
        evidence_rules (str): Evidence key for the suppressed codes.

    """

    suppressive_actions: Final[frozenset[str]] = frozenset(
        {"ignore", "disable", "off", "skip"},
    )
    evidence_tool: str = "tool"
    evidence_action: str = "action"
    evidence_rules: str = "rules"


def find_suppressions(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag suppression comments in a parsed module.

    Args:
        module (CommentedModule): Module carrying tokenized comments.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: Candidates in source order.

    """
    return tuple(
        Candidate(
            span=span_of(node=comment, filename=filename),
            evidence={
                Constants.evidence_tool: comment.tool,
                Constants.evidence_action: comment.action,
                Constants.evidence_rules: [
                    rule.code for rule in comment.rules
                ],
            },
        )
        for comment in module.comments
        if isinstance(comment, SuppressionComment)
        and comment.action in Constants.suppressive_actions
    )
