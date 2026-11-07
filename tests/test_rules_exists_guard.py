"""Verify that unsupported predicates fail at validation, not at check time."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from astart.rules import (
    CatalogError,
    default_registries,
    load_default_catalog,
    validate_catalog,
)
from astart.rules.predicate import Compare, CompareOp, Exists

from tests.expectations import expect_in

if TYPE_CHECKING:
    from astart.rules.model import Catalog, Rule
    from astart.rules.registry import Registries


def test_exists_predicate_is_rejected_when_validating() -> None:
    """Check that exists predicate is rejected when validating."""
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    first: Rule = catalog.rules[0]
    broken: Catalog = replace(
        catalog,
        rules=(
            replace(
                first,
                when=Exists(
                    selector="Call",
                    where=Compare(
                        fact="node.annotation_missing",
                        op=CompareOp.eq,
                        value=True,
                    ),
                ),
                procedure=None,
            ),
            *catalog.rules[1:],
        ),
    )
    with pytest.raises(expected_exception=CatalogError) as raised:
        validate_catalog(catalog=broken, registries=registries)
    expect_in(item="exists", container=str(object=raised.value))
