"""The skip-reason docs cover every enum member value."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart.rules.reasons import Rejection, SkipCode

from tests.support.expectations import expect_in
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Constants for the skip docs tests.

    Attributes:
        docs (Final[Path]): Directory holding the skip-reason documentation.

    """

    docs: Final[Path] = Paths.root / "docs" / "guides"


def test_every_rejection_value_appears_in_skip_reasons() -> None:
    """Check that ``docs/guides/skip-reasons.md`` names every ``Rejection``."""
    text: str = (Constants.docs / "skip-reasons.md").read_text(
        encoding="utf-8",
    )
    for member in Rejection:
        expect_in(item=f"`{member.value}`", container=text)


def test_every_skip_code_value_appears_in_skip_codes() -> None:
    """Check that ``docs/guides/skip-codes.md`` names every ``SkipCode``."""
    text: str = (Constants.docs / "skip-codes.md").read_text(encoding="utf-8")
    for member in SkipCode:
        expect_in(item=f"`{member.value}`", container=text)
