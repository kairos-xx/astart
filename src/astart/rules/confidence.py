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
        proven (Final[float]): Confidence of a fix that preserves meaning by
            construction.
        by_basis (Final[Mapping[HintBasis, float]]): Confidence of an inferred
            annotation, by its evidence.
        by_fix (Final[Mapping[str, float]]): Confidence of other guarded fixes,
            by fix key.
        by_literal (Final[Mapping[str, float]]): Confidence of an annotation
            taken from a literal default alone, by
            type: the share of such parameters in 165 typed libraries whose
            original annotation was exactly that type (``int`` 73 %, ``str``
            69 %; the rest are wider, such as ``float`` or ``str | None``).
        default_minimum (Final[float]): Confidence below which ``astart fix``
            writes
            nothing unless asked (``--min-confidence``).
        fallback (Final[float]): Confidence of a guarded fix not listed above.
        hinted_fixes (Final[frozenset[str]]): Fixes whose confidence comes from
            the hint's basis.

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
        HintBasis.calibrated_candidate: 0.9,
        HintBasis.union_sites: 0.9,
        HintBasis.negotiated: 0.95,
        HintBasis.engine: 0.55,
    }
    by_fix: Final[Mapping[str, float]] = {
        "calls.add-keywords": 0.95,
        "typing.synthesize-protocol": 0.9,
        "typing.synthesize-typevar": 0.9,
        "typing.add-variable-annotation": 0.95,
    }
    by_literal: Final[Mapping[str, float]] = {
        "bool": 0.99,
        "float": 0.99,
        "int": 0.72,
        "str": 0.69,
    }
    default_minimum: Final[float] = 0.8
    fallback: Final[float] = 0.9
    hinted_fixes: Final[frozenset[str]] = frozenset(
        {
            "typing.add-inferred-annotation",
            "typing.add-attribute-annotation",
        },
    )


def offer_confidence(
    *,
    fix: Fix,
    subject: Subject,
    facts: ModuleFacts,
) -> float:
    """Rate how sure the engine is that a fix is right for a subject.

    Args:
        fix (Fix): Offered fix.
        subject (Subject): Subject the fix would edit.
        facts (ModuleFacts): Resolved module facts, including lazily computed
            hints.

    Returns:
        float: A confidence between 0 and 1; proven fixes are 1.0 and an
            inferred
            annotation takes the confidence of the evidence that justified it.

    """
    if fix.safety is FixSafety.proven:
        return Constants.proven
    if fix.key in Constants.hinted_fixes and facts.hints is not None:
        hint: Hint | None = facts.hints.index().hint_for(node=subject.node)
        if hint is not None:
            if hint.basis is HintBasis.default_literal:
                return Constants.by_literal.get(
                    hint.source,
                    Constants.by_basis[hint.basis],
                )
            return Constants.by_basis[hint.basis]
    return Constants.by_fix.get(fix.key, Constants.fallback)
