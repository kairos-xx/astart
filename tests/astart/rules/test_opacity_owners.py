"""G-03: every opacity reason reported on the pairs has a documented owner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from scripts.compare.opacity_report import Section, collect
from tests.support.expectations import expect_in, expect_not_in, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        owners_doc (Final[Path]): Path to ``docs/analysis/opacity-owners.md``.
        pairs_dir (Final[Path]): Directory containing untyped pair fixtures.

    """

    root: Final[Path] = Paths.root
    owners_doc: Final[Path] = (
        Paths.root / "docs" / "analysis" / "opacity-owners.md"
    )
    pairs_dir: Final[Path] = Paths.fixtures


def test_every_pair_opacity_reason_has_an_owner() -> None:
    """Check pair-file reason strings appear in ``opacity-owners.md``."""
    doc_text: str = Constants.owners_doc.read_text(encoding="utf-8")
    expect_not_in(item="| unowned", container=doc_text.lower())
    reasons: set[str] = set()
    targets: list[Path] = [
        Constants.root / "fixtures" / "untyped.py",
        *sorted(Constants.pairs_dir.glob(pattern="*_untyped.py.txt")),
    ]
    for path in targets:
        sections: list[Section] = collect(
            source=path.read_text(encoding="utf-8"),
            samples=0,
        )
        for section in sections:
            for row in section.rows:
                reasons.add(row.label)
    expect_true(condition=len(reasons) > 0)
    for reason in sorted(reasons):
        expect_in(item=f"| `{reason}` |", container=doc_text)
