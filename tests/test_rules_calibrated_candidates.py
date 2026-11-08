"""The one inference-engine candidate category measured as reliable."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Fix a module at the guarded ceiling.

    Args:
        source: Module text.

    Returns:
        The fixed text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_a_bool_result_of_untyped_operands_is_accepted() -> None:
    """Check that comparing two untyped values returns ``bool``."""
    out: str = _fixed(
        source="""
        def same(a, b):
            return a == b
        """,
    )
    expect_in(item="def same(a, b) -> bool:", container=out)


def test_membership_and_negation_are_bool() -> None:
    """Check ``in`` and ``not`` over untyped values."""
    out: str = _fixed(
        source="""
        def has(items, x):
            return x in items

        def lacks(items, x):
            return not has(items, x)
        """,
    )
    expect_in(item="def has(items, x) -> bool:", container=out)


def test_other_candidates_stay_refused() -> None:
    """Check that only the measured category is accepted."""
    out: str = _fixed(
        source="""
        def pick(a, flag=None):
            return a

        def pair(a):
            return a, a
        """,
    )
    expect_not_in(item="-> bool", container=out)
    expect_not_in(item="flag:", container=out)


def test_a_mixed_return_is_not_a_bool() -> None:
    """Check that a ``bool | None`` result is not narrowed to ``bool``."""
    out: str = _fixed(
        source="""
        def maybe(a):
            if a:
                return a == 1
            return None
        """,
    )
    expect_not_in(item="def maybe(a) -> bool:", container=out)


def test_a_bare_name_carrying_a_bool_is_not_covered() -> None:
    """Check that ``return p`` is not accepted because a caller passes True."""
    out: str = _fixed(
        source="""
        def f(p=1.5):
            return p

        f(True)
        """,
    )
    expect_not_in(item="-> bool", container=out)


def test_a_predicate_call_is_covered() -> None:
    """Check ``isinstance`` over an untyped value."""
    out: str = _fixed(
        source="""
        def is_text(x):
            return isinstance(x, str)
        """,
    )
    expect_in(item="def is_text(x) -> bool:", container=out)
