"""``--stub-docstrings`` writes stubs for undocumented public definitions."""

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

from tests.support.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str, stub: bool = True) -> str:
    """Run the fix pipeline, optionally stubbing missing docstrings.

    Args:
        source (str): Python source text.
        stub (bool): Whether ``--stub-docstrings`` is enabled.

    Returns:
        str: The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            stub_docstrings=stub,
        ),
    ).source


def test_a_function_without_parameters_gets_a_one_line_stub() -> None:
    """Check the simplest stub."""
    out: str = _fixed(
        source="""
        def run() -> None:
            pass
        """,
    )
    expect_in(item="Describe run.", container=out)


def test_parameters_are_listed_in_an_args_section() -> None:
    """Check that a function with parameters gets entries."""
    out: str = _fixed(
        source="""
        def run(a: int, *rest: int) -> None:
            pass
        """,
    )
    expect_in(
        item="""\
Args:
        a (int): TODO.""",
        container=out,
    )
    expect_in(item="rest (int): TODO.", container=out)


def test_classes_get_a_stub() -> None:
    """Check classes."""
    out: str = _fixed(
        source="""
        class Box:
            size = 1
        """,
    )
    expect_in(item="Describe Box.", container=out)


def test_private_names_and_documented_ones_are_left_alone() -> None:
    """Check the exemptions."""
    source: str = '''
        def _helper() -> None:
            pass


        def run() -> None:
            """Run."""
        '''
    expect_equal(actual=_fixed(source=source), expected=dedent(text=source))


def test_overloads_and_one_line_defs_are_left_alone() -> None:
    """Check that ``@overload`` and ``def f(): ...`` are never stubbed."""
    source: str = """
        from typing import overload


        @overload
        def run(a: int) -> int: ...
        @overload
        def run(a: str) -> str: ...
        def run(a):
            return a


        def short() -> int: return 1
        """
    out: str = _fixed(source=source)
    expect_not_in(item="Describe short", container=out)
    expect_not_in(
        item='"""Describe run',
        container=out.split(sep="def run(a):", maxsplit=1)[0],
    )


def test_nothing_happens_unless_asked() -> None:
    """Check that the fix is opt-in."""
    source: str = """\
def run() -> None:
    pass
"""
    expect_equal(actual=_fixed(source=source, stub=False), expected=source)


def test_a_second_run_changes_nothing() -> None:
    """Check idempotence."""
    once: str = _fixed(
        source="""
        def run(a: int) -> None:
            pass
        """,
    )
    expect_equal(actual=_fixed(source=once), expected=once)
