"""New Final constants join an existing ``Constants`` class."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from astart.rules.registry import Registries

from tests.expectations import expect_equal, expect_in, expect_not_in


@final
class Constants:
    """Constants for the test.

    Attributes:
        class_source: Source text the constants-grouping fix rewrites.

    """

    class_source: Final[str] = '''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants."""

    DEPTH: Final[int] = 2
'''


def _fixed(
    *,
    source: str,
    ceiling: FixSafety = FixSafety.guarded,
    create: bool = False,
) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source: Module source to fix.
        ceiling: Highest fix safety level allowed.
        create: Whether creating new declarations is allowed.

    Returns:
        Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling, create_constants=create),
    ).source


def test_new_constant_is_added_to_the_existing_class() -> None:
    """Check that new constant is added to the existing class."""
    out: str = _fixed(
        source=Constants.class_source
        + """

LIMIT = 3  # how many


def check(value) -> bool:
    return value < LIMIT
""",
    )
    expect_in(item="    LIMIT: Final[int] = 3  # how many", container=out)
    expect_in(item="return value < Constants.LIMIT", container=out)
    expect_not_in(item="\nLIMIT", container=out)


def test_without_a_constants_class_the_safe_ceiling_keeps_the_global() -> None:
    """Check that without a class the safe ceiling keeps the global."""
    out: str = _fixed(
        source="LIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
        ceiling=FixSafety.proven,
    )
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_in(item="return LIMIT", container=out)
    expect_not_in(item="Constants", container=out)


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: str = _fixed(
        source=Constants.class_source
        + "\n\nLIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
    )
    expect_equal(actual=_fixed(source=first), expected=first)


def test_unsafe_moves_are_refused() -> None:
    """Check that unsafe moves are refused."""
    cases: dict[str, str] = {
        "name already in the class": (
            Constants.class_source
            + "\n\nDEPTH = 5\n\n\ndef f():\n    return DEPTH\n"
        ),
        "exported": (
            Constants.class_source + '\n\n__all__ = ["LIMIT"]\nLIMIT = 3\n\n\n'
            "def f():\n    return LIMIT\n"
        ),
        "used at import time before the class": (
            "LIMIT = 3\nTWICE = LIMIT * 2\n\n\n"
            + Constants.class_source.split(sep="\n\n\n", maxsplit=1)[1]
        ),
        "used in the class body": (
            Constants.class_source.replace(
                "DEPTH: Final[int] = 2",
                "DEPTH: Final[int] = LIMIT",
            )
            + "\n\nLIMIT = 3\n"
        ),
        "declared global elsewhere": (
            Constants.class_source
            + "\n\nLIMIT = 3\n\n\ndef f():\n    global LIMIT\n    return 1\n"
        ),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_not_in(item="Constants.LIMIT", container=out, message=label)
        expect_not_in(item="    LIMIT:", container=out, message=label)


def test_a_default_after_the_class_uses_the_class() -> None:
    """Check that a default after the class uses the class."""
    out: str = _fixed(
        source=Constants.class_source
        + "\n\nLIMIT = 3\n\n\ndef f(n=LIMIT):\n    return n\n",
    )
    expect_in(item="def f(n=Constants.LIMIT)", container=out)


def test_several_new_constants_all_join_the_class() -> None:
    """Check that several new constants all join the class."""
    source: str = (
        Constants.class_source
        + "\n\nLIMIT = 3\nNAME = 'x'\nRATE = 0.5\n\n\n"
        + "def f(v):\n    return v < LIMIT or NAME == v or RATE\n"
    )
    out: str = _fixed(source=source)
    for line in (
        "    LIMIT: Final[int] = 3",
        "    NAME: Final[str] = 'x'",
        "    RATE: Final[float] = 0.5",
        "Constants.LIMIT",
        "Constants.NAME",
        "Constants.RATE",
    ):
        expect_in(item=line, container=out)
    expect_equal(actual=_fixed(source=out), expected=out)


DOCUMENTED: Final[str] = '''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        DEPTH: How deep to go.

    """

    DEPTH: Final[int] = 2
'''


def test_the_attributes_section_documents_the_new_constant() -> None:
    """Check that the attributes section documents the new constant."""
    out: str = _fixed(
        source=DOCUMENTED + "\n\nLIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
    )
    expect_in(
        item=(
            "        DEPTH: How deep to go.\n"
            "        LIMIT: Grouped module constant.\n"
        ),
        container=out,
    )
    expect_equal(actual=_fixed(source=out), expected=out)


def test_a_class_without_an_attributes_section_is_left_documented_as_is() -> (
    None
):
    """Check that a class without an attributes section keeps its docstring."""
    out: str = _fixed(
        source=Constants.class_source
        + "\n\nLIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
    )
    expect_in(item='"""Group module-level constants."""', container=out)
    expect_not_in(item="LIMIT: Grouped", container=out)


def test_the_proven_ceiling_adds_final_but_does_not_move() -> None:
    """Check that the proven ceiling adds final but does not move."""
    out: str = _fixed(
        source=Constants.class_source
        + "\n\nLIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
        ceiling=FixSafety.proven,
    )
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_in(item="return LIMIT", container=out)
    expect_not_in(item="    LIMIT:", container=out)


def test_an_already_final_global_moves_into_the_class() -> None:
    """Check that an already final global moves into the class."""
    out: str = _fixed(
        source=Constants.class_source
        + "\n\nLIMIT: Final[int] = 3\n\n\ndef f():\n    return LIMIT\n",
    )
    expect_in(item="    LIMIT: Final[int] = 3", container=out)
    expect_in(item="return Constants.LIMIT", container=out)


def test_the_class_is_created_when_the_module_has_none() -> None:
    """Check that the class is created when the module has none."""
    out: str = _fixed(
        source="""
        import os

        LIMIT = 3
        NAME = "x"


        def f(v):
            return os.sep, v < LIMIT, NAME
        """,
        create=True,
    )
    compile(source=out, filename="m.py", mode="exec")
    expect_in(item="@final\nclass Constants:", container=out)
    expect_in(item="    LIMIT: Final[int] = 3", container=out)
    expect_in(item="    NAME: Final[str] = 'x'", container=out)
    expect_in(item="LIMIT: Grouped module constant.", container=out)
    expect_in(item="Constants.LIMIT", container=out)
    expect_in(item="from typing import Final, final", container=out)
    expect_equal(actual=_fixed(source=out, create=True), expected=out)


def test_no_class_is_created_over_another_binding() -> None:
    """Check that no class is created over another binding."""
    out: str = _fixed(
        source="Constants = {}\nLIMIT = 3\n\n\ndef f():\n    return LIMIT\n",
        create=True,
    )
    expect_not_in(item="class Constants", container=out)
    expect_in(item="return LIMIT", container=out)


def test_no_class_is_created_unless_asked_for() -> None:
    """Check that no class is created unless asked for."""
    out: str = _fixed(source="LIMIT = 3\n\n\ndef f():\n    return LIMIT\n")
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_not_in(item="class Constants", container=out)
