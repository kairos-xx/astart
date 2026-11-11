"""M8-21: rule catalog exit-gate invariants and CLI rule surface."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Final, final

from astart.cli.commands import run_rules
from astart.rules import default_registries, load_default_catalog
from astart.rules.engine import verify_catalog
from astart.rules.libkw import SIGNATURES

from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        registered_codes (Final[tuple[str, ...]]): Catalog rule codes shipped
            in ``astart rules``.
        planned_codes (Final[tuple[str, ...]]): Spec §5 rule codes tracked by
            open M8 tasks.
        min_libkw_entries (Final[int]): Minimum number of library keyword
            signatures.

    """

    registered_codes: Final[tuple[str, ...]] = (
        "CAL001",
        "DOC001",
        "DOC002",
        "DOC003",
        "DOC007",
        "DOC014",
        "STR001",
        "TYP001",
        "TYP003",
        "TYP004",
        "TYP005",
        "TYP007",
        "TYP008",
        "WSP001",
        "WSP002",
    )
    planned_codes: Final[tuple[str, ...]] = (
        "CFG001",
        "DOC004",
        "DOC005",
        "DOC006",
        "DOC008",
        "DOC009",
        "DOC010",
        "DOC011",
        "DOC012",
        "DOC013",
        "IMP001",
        "NAM001",
        "OOP001",
        "OOP002",
        "OOP003",
        "OOP004",
        "PRS001",
        "SHB001",
        "SIM001",
        "SIM002",
        "SIM003",
        "SIM004",
        "SIM005",
        "SIM006",
        "SUP001",
        "SUP002",
        "SUP003",
        "TYP002",
        "TYP006",
    )
    min_libkw_entries: Final[int] = 5_000


def test_verify_catalog_reports_no_problems() -> None:
    """Check ``verify_catalog`` passes with no invariant breaches."""
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    expect_equal(
        actual=verify_catalog(catalog=catalog, registries=registries),
        expected=None,
    )


def test_astart_rules_lists_every_registered_code() -> None:
    """Check every registered code appears in ``astart rules`` output."""
    out: StringIO = StringIO()
    code: int = run_rules(out=out)
    expect_equal(actual=code, expected=0)
    text: str = out.getvalue()
    for rule_code in Constants.registered_codes:
        expect_in(item=rule_code, container=text)
    expect_true(condition=len(Constants.planned_codes) > 0)


def test_libkw_table_has_expected_stdlib_categories() -> None:
    """Check ``SIGNATURES`` covers core stdlib modules."""
    expect_true(condition=len(SIGNATURES) >= Constants.min_libkw_entries)
    top_modules: set[str] = {callee.split(sep=".")[0] for callee in SIGNATURES}
    for required in ("ast", "json", "pathlib", "re", "subprocess", "typing"):
        expect_in(item=required, container=top_modules)
