"""Tests for the typeshed-generated library keyword-safety table."""

from __future__ import annotations

from typing import Final, final

from astart.rules.libkw import (
    SIGNATURES,
    KwSignature,
    accepts_keyword,
    keyword_names,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_not_none,
    expect_true,
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        minimum_entries: Lower bound on table size for stdlib coverage.
        spot_posonly: Callees whose signature is fully positional-only.
        spot_keywordable: ``name -> param`` pairs that must be passable.
        spot_any: Callees known to carry ``**kwargs``.

    """

    minimum_entries: Final[int] = 5000
    spot_posonly: Final[tuple[str, ...]] = (
        "builtins.len",
        "builtins.list.append",
        "builtins.str.join",
    )
    spot_keywordable: Final[tuple[tuple[str, str], ...]] = (
        ("builtins.open", "mode"),
        ("builtins.open", "encoding"),
        ("os.makedirs", "exist_ok"),
        ("json.loads", "parse_float"),
        ("textwrap.wrap", "width"),
    )
    spot_any: Final[str] = "ast.AnnAssign.__init__"


def test_table_is_sorted_and_sized() -> None:
    """Entries are sorted and cover the stdlib broadly."""
    keys: list[str] = list(SIGNATURES)
    expect_equal(actual=keys, expected=sorted(keys))
    expect_true(condition=len(keys) >= Constants.minimum_entries)


def test_no_entry_is_positional_only() -> None:
    """Every listed name is keyword-passable by construction."""
    for callee, signature in SIGNATURES.items():
        for name in signature.names:
            expect_false(
                condition=name.startswith("__"),
                message=f"{callee} lists posonly-ish {name}",
            )
            expect_false(
                condition=name in {"self", "cls"},
                message=f"{callee} lists receiver {name}",
            )


def test_posonly_builtins_have_no_names() -> None:
    """C posonly builtins exist but offer no keyword names."""
    for callee in Constants.spot_posonly:
        signature: KwSignature = expect_not_none(
            value=SIGNATURES.get(callee),
            message=callee,
        )
        expect_equal(actual=signature.names, expected=())


def test_keywordable_spot_checks() -> None:
    """Known keyword-passable parameters are accepted."""
    for callee, name in Constants.spot_keywordable:
        expect_true(
            condition=accepts_keyword(callee=callee, name=name),
            message=f"{callee} should accept {name}=",
        )


def test_any_keyword_accepts_arbitrary() -> None:
    """A ``**kwargs`` callee accepts any name."""
    expect_true(
        condition=accepts_keyword(
            callee=Constants.spot_any,
            name="whatever",
        ),
    )


def test_unknown_callee_rejected() -> None:
    """Missing entries do not accept keywords."""
    expect_equal(
        actual=keyword_names(callee="no.such.callee"),
        expected=None,
    )
    expect_false(
        condition=accepts_keyword(callee="no.such.callee", name="x"),
    )


def test_posonly_name_rejected() -> None:
    """A param before ``/`` is never accepted."""
    expect_false(
        condition=accepts_keyword(callee="builtins.len", name="obj"),
    )


def test_lookup_round_trip() -> None:
    """keyword_names returns the stored tuple."""
    names: tuple[str, ...] = expect_not_none(
        value=keyword_names(callee="builtins.open"),
    )
    expect_true(condition="encoding" in names)
