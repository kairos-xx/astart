"""Rule ontology: a typed, serializable catalog of checks and fixes.

The model modules (``vocabulary``, ``predicate``, ``model``, ``registry``,
``catalog`` and ``schema``) do not depend on the AST packages. ``engine``,
``facts`` and ``appliers`` are the reference implementation that evaluates
the catalog against Python source.
"""

from __future__ import annotations

from astart.rules.catalog import (
    CatalogError,
    dump_catalog,
    load_catalog,
    load_default_catalog,
    validate_catalog,
)
from astart.rules.engine import (
    CheckOptions,
    CheckResult,
    apply_fix,
    check,
    validate_behavior,
    verify_catalog,
)
from astart.rules.facts import default_registries
from astart.rules.formatter import (
    FormatOutcome,
    FormatTarget,
    fix_and_format,
    format_source,
)
from astart.rules.model import Catalog, Finding, Fix, Rule
from astart.rules.runner import FixResult, FixSettings, fix_source

__all__ = [
    "Catalog",
    "CatalogError",
    "CheckOptions",
    "CheckResult",
    "Finding",
    "Fix",
    "FixResult",
    "FixSettings",
    "FormatOutcome",
    "FormatTarget",
    "Rule",
    "apply_fix",
    "check",
    "default_registries",
    "dump_catalog",
    "fix_and_format",
    "fix_source",
    "format_source",
    "load_catalog",
    "load_default_catalog",
    "validate_behavior",
    "validate_catalog",
    "verify_catalog",
]
