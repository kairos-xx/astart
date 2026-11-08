"""``docs/rules.md`` covers every catalog rule code."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final, final

from astart.rules.catalog import load_default_catalog
from astart.rules.facts import default_registries

from tests.expectations import expect_in

if TYPE_CHECKING:
    from astart.rules.model import Catalog


@final
class Constants:
    """Constants for the test.

    Attributes:
        docs: Path of the generated rule documentation.

    """

    docs: Final[Path] = Path(__file__).parent.parent / "docs" / "rules.md"


def test_every_catalog_code_appears_in_rule_docs() -> None:
    """Check that each rule code has a section in ``docs/rules.md``."""
    text: str = Constants.docs.read_text(encoding="utf-8")
    catalog: Catalog = load_default_catalog(registries=default_registries())
    for rule in catalog.rules:
        expect_in(item=f"## {rule.code} ", container=text)
