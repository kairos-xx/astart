"""How sure the engine is about each offered fix."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart.rules.hints import Hint, HintBasis
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart.rules.facts import ModuleFacts, Subject
    from astart.rules.model import Fix


@final
class Constants:
    """Group module-level constants.

    Attributes:
        proven: Confidence of a fix that preserves meaning by construction.
        by_basis: Confidence of an inferred annotation, by its evidence.
        by_fix: Confidence of other guarded fixes, by fix key.
        fallback: Confidence of a guarded fix not listed above.
        hinted_fixes: Fixes whose confidence comes from the hint's basis.

    """

    proven: Final[float] = 1.0
    by_basis: Final[Mapping[HintBasis, float]] = {
        HintBasis.proven_none: 1.0,
        HintBasis.default_literal: 0.99,
        HintBasis.call_sites: 0.95,
        HintBasis.derived_return: 0.9,
        HintBasis.syntax_proven: 0.99,
        HintBasis.optional_default: 0.95,
        HintBasis.protocol_result: 0.97,
        HintBasis.attribute_assignments: 0.9,
    }
    by_fix: Final[Mapping[str, float]] = {
        "calls.add-keywords": 0.95,
        "typing.synthesize-protocol": 0.9,
        "typing.synthesize-typevar": 0.9,
    }
    fallback: Final[float] = 0.9
    hinted_fixes: Final[frozenset[str]] = frozenset(
        {"typing.add-inferred-annotation", "typing.add-attribute-annotation"},
    )


def offer_confidence(
    *,
    fix: Fix,
    subject: Subject,
    facts: ModuleFacts,
) -> float:
    """Rate how sure the engine is that a fix is right for a subject.

    Args:
        fix: Offered fix.
        subject: Subject the fix would edit.
        facts: Resolved module facts, including lazily computed hints.

    Returns:
        A confidence between 0 and 1; proven fixes are 1.0 and an inferred
        annotation takes the confidence of the evidence that justified it.

    """
    if fix.safety is FixSafety.proven:
        return Constants.proven
    if fix.key in Constants.hinted_fixes and facts.hints is not None:
        hint: Hint | None = facts.hints.index().hint_for(node=subject.node)
        if hint is not None:
            return Constants.by_basis[hint.basis]
    return Constants.by_fix.get(fix.key, Constants.fallback)
