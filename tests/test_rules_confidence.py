"""Verify offer confidence and the minimum-confidence gate."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final

from astart.rules import (
    FixResult,
    FixSettings,
    check,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.engine import CheckResult
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult

SOURCE: Final[str] = dedent(
    text="""\
    def pad(text, width=10):
        print(text, width)


    pad("a")
    """,
)


def _fix(*, minimum: float) -> FixResult:
    """Fix the module under a confidence floor.

    Args:
        minimum: Minimum confidence for applying fixes.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=SOURCE,
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            min_confidence=minimum,
        ),
    )


def test_offers_carry_the_confidence_of_their_evidence() -> None:
    """Check that offers carry the confidence of their evidence."""
    registries: Registries = default_registries()
    found: CheckResult = check(
        source=SOURCE,
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
    )
    by_path: dict[tuple[str, str], float] = {
        (finding.subject_path, offer.fix_key): offer.confidence
        for finding in found.findings
        for offer in finding.fix_offers
    }
    expect_equal(
        actual=by_path[("pad.width", "typing.add-inferred-annotation")],
        expected=0.99,
    )
    expect_equal(
        actual=by_path[("pad.text", "typing.add-inferred-annotation")],
        expected=0.95,
    )
    expect_equal(
        actual=by_path[("pad", "typing.add-none-return")],
        expected=1.0,
    )


def test_minimum_confidence_filters_weaker_evidence() -> None:
    """Check that minimum confidence filters weaker evidence."""
    strict: FixResult = _fix(minimum=0.97)
    expect_in(item="width: int = 10", container=strict.source)
    expect_not_in(item="text: str", container=strict.source)
    relaxed: FixResult = _fix(minimum=0.0)
    expect_in(item="text: str", container=relaxed.source)
