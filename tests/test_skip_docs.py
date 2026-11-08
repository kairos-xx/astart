"""The skip-reason docs cover every enum member value."""

from __future__ import annotations

from pathlib import Path
from typing import Final, final

from astart.rules.reasons import Rejection, SkipCode

from tests.expectations import expect_in


@final
class Constants:
    """Constants for the skip docs tests.

    Attributes:
        docs: Directory holding the skip-reason documentation.

    """

    docs: Final[Path] = Path(__file__).parent.parent / "docs"


def test_every_rejection_value_appears_in_skip_reasons() -> None:
    """Check that ``docs/skip-reasons.md`` names every ``Rejection``."""
    text: str = (Constants.docs / "skip-reasons.md").read_text(
        encoding="utf-8",
    )
    for member in Rejection:
        expect_in(item=f"`{member.value}`", container=text)


def test_every_skip_code_value_appears_in_skip_codes() -> None:
    """Check that ``docs/skip-codes.md`` names every ``SkipCode``."""
    text: str = (Constants.docs / "skip-codes.md").read_text(encoding="utf-8")
    for member in SkipCode:
        expect_in(item=f"`{member.value}`", container=text)
