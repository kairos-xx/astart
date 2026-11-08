"""Docstring healing through the fixer: add, remove and tidy."""

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

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str, ceiling: FixSafety = FixSafety.guarded) -> str:
    """Run the fix pipeline on one source at the given safety ceiling.

    Args:
        source: Python source text.
        ceiling: Highest fix safety applied.

    Returns:
        The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling),
    ).source


def test_missing_parameter_gets_a_stub_entry_in_order() -> None:
    """Check that ``b`` is documented between ``a`` and ``c``."""
    out: str = _fixed(
        source='''
        def run(a: int, b: int, c: int) -> None:
            """Run.

            Args:
                a: First.
                c: Third.
            """
        ''',
    )
    expect_in(
        item="a: First.\n        b: Describe b.\n        c: Third.",
        container=out,
    )


def test_a_docstring_without_args_gets_a_section() -> None:
    """Check that a one-line docstring grows an Args section."""
    out: str = _fixed(
        source='''
        def run(a: int, *rest: int, **options: int) -> None:
            """Run."""
        ''',
    )
    expect_in(item="Args:\n        a: Describe a.", container=out)
    expect_in(item="*rest: Describe rest.", container=out)
    expect_in(item="**options: Describe options.", container=out)


def test_stale_entries_are_removed() -> None:
    """Check that a documented parameter that is gone disappears."""
    out: str = _fixed(
        source='''
        def run(a: int) -> None:
            """Run.

            Args:
                a: First.
                gone: Old.
            """
        ''',
    )
    expect_in(item="a: First.", container=out)
    expect_not_in(item="gone", container=out)


def test_untidy_docstrings_are_tidied() -> None:
    """Check trailing space and blank runs inside a docstring."""
    out: str = _fixed(
        source='''
        def run() -> None:
            """Run.


            More.
            """
        ''',
    )
    expect_in(item='"""Run.\n\n    More.\n    """', container=out)


def test_class_docstrings_are_tidied_too() -> None:
    """Check that classes are covered."""
    out: str = _fixed(
        source='''
        class Box:
            """Box.


            Holds things.
            """
        ''',
    )
    expect_in(item='"""Box.\n\n    Holds things.\n    """', container=out)


def test_numpy_style_docstrings_are_left_alone() -> None:
    """Check that a style the editor does not speak is never rewritten."""
    source: str = '''
        def run(a: int) -> None:
            """Run.

            Parameters
            ----------
            a : int
                First.
            gone : int
                Old.
            """
        '''
    expect_equal(actual=_fixed(source=source), expected=dedent(text=source))


def test_single_quoted_docstrings_are_left_alone() -> None:
    """Check that a one-line quoted docstring is not exploded into escapes."""
    source: str = "def run(a: int) -> None:\n    'Run.'\n"
    expect_equal(actual=_fixed(source=source), expected=source)


def test_async_functions_are_covered() -> None:
    """Check that ``async def`` gets entries as well."""
    out: str = _fixed(
        source='''
        async def run(a: int) -> None:
            """Run."""
        ''',
    )
    expect_in(item="a: Describe a.", container=out)


def test_a_second_run_changes_nothing() -> None:
    """Check idempotence of the three fixes together."""
    once: str = _fixed(
        source='''
        def run(a: int, b: int) -> None:
            """Run.

            Args:
                a: First.
                gone: Old.
            """
        ''',
    )
    expect_equal(actual=_fixed(source=once), expected=once)


def test_the_safe_ceiling_applies_them_too() -> None:
    """Check that docstring fixes are provably safe."""
    out: str = _fixed(
        source='''
        def run(a: int) -> None:
            """Run."""
        ''',
        ceiling=FixSafety.proven,
    )
    expect_in(item="a: Describe a.", container=out)


def test_a_module_docstring_is_tidied() -> None:
    """Check that DOC007 rewrites a module docstring at zero indent."""
    out: str = _fixed(
        source='''
        """Module doc.   \n

        More.
        """

        x = 1
        ''',
    )
    expect_in(item='"""Module doc.\n\nMore.\n"""', container=out)


def test_a_renamed_parameter_keeps_its_description() -> None:
    """Check that a stale entry at the missing slot is renamed.

    One stale entry and one undocumented parameter at the same position
    means the parameter was renamed, so its description is kept.
    """
    out: str = _fixed(
        source='''
        def run(alpha: int, beta: int) -> None:
            """Run.

            Args:
                alpha: First.
                gamma: Was second.
            """
        ''',
    )
    expect_in(item="beta: Was second.", container=out)
    expect_not_in(item="gamma", container=out)


def test_two_stale_or_mismatched_positions_fall_back() -> None:
    """Check that a misplaced stale entry falls back to remove and add.

    A stale entry away from the missing parameter's slot is removed and
    a stub entry is added instead of renaming.
    """
    out: str = _fixed(
        source='''
        def run(alpha: int, beta: int, gamma: int) -> None:
            """Run.

            Args:
                delta: Old first.
                alpha: First.
                beta: Second.
            """
        ''',
    )
    expect_not_in(item="delta", container=out)
    expect_in(item="gamma: Describe gamma.", container=out)
