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
from astart.rules.constants_grouping import is_constant_name
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from astart.rules.registry import Registries

from tests.support.expectations import expect_equal, expect_in, expect_not_in


@final
class Constants:
    """Constants for the test.

    Attributes:
        class_source (Final[str]): Source text the constants-grouping fix
            rewrites.

    """

    class_source: Final[str] = '''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants."""

    depth: Final[int] = 2
'''


def _fixed(
    *,
    source: str,
    ceiling: FixSafety = FixSafety.guarded,
    create: bool = False,
) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source (str): Module source to fix.
        ceiling (FixSafety): Highest fix safety level allowed.
        create (bool): Whether creating new declarations is allowed.

    Returns:
        str: Fixed source text.

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
    expect_in(item="    limit: Final[int] = 3  # how many", container=out)
    expect_in(item="return value < Constants.limit", container=out)
    expect_not_in(
        item="""\

LIMIT""",
        container=out,
    )


def test_without_a_constants_class_the_safe_ceiling_keeps_the_global() -> None:
    """Check that without a class the safe ceiling keeps the global."""
    out: str = _fixed(
        source="""\
LIMIT = 3


def f():
    return LIMIT
""",
        ceiling=FixSafety.proven,
    )
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_in(item="return LIMIT", container=out)
    expect_not_in(item="Constants", container=out)


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: str = _fixed(
        source=Constants.class_source
        + """\


LIMIT = 3


def f():
    return LIMIT
""",
    )
    expect_equal(actual=_fixed(source=first), expected=first)


def test_unsafe_moves_are_refused() -> None:
    """Check that unsafe moves are refused."""
    cases: dict[str, str] = {
        "name already in the class": (
            Constants.class_source
            + """\


DEPTH = 5


def f():
    return DEPTH
"""
        ),
        "exported": (
            Constants.class_source + '\n\n__all__ = ["LIMIT"]\nLIMIT = 3\n\n\n'
            "def f():\n    return LIMIT\n"
        ),
        "used at import time before the class": (
            """\
LIMIT = 3
TWICE = LIMIT * 2


"""
            + Constants.class_source.split(
                sep="\n\n\n",
                maxsplit=1,
            )[1]
        ),
        "used in the class body": (
            Constants.class_source.replace(
                "depth: Final[int] = 2",
                "depth: Final[int] = LIMIT",
            )
            + """\


LIMIT = 3
"""
        ),
        "declared global elsewhere": (
            Constants.class_source
            + """\


LIMIT = 3


def f():
    global LIMIT
    return 1
"""
        ),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_not_in(item="Constants.limit", container=out, message=label)
        expect_not_in(item="    limit:", container=out, message=label)


def test_a_default_after_the_class_uses_the_class() -> None:
    """Check that a default after the class uses the class."""
    out: str = _fixed(
        source=Constants.class_source
        + """\


LIMIT = 3


def f(n=LIMIT):
    return n
""",
    )
    expect_in(item="def f(n=Constants.limit)", container=out)


def test_several_new_constants_all_join_the_class() -> None:
    """Check that several new constants all join the class."""
    source: str = (
        Constants.class_source
        + """\


LIMIT = 3
NAME = 'x'
RATE = 0.5


"""
        + """\
def f(v):
    return v < LIMIT or NAME == v or RATE
"""
    )
    out: str = _fixed(source=source)
    for line in (
        "    limit: Final[int] = 3",
        "    name: Final[str] = 'x'",
        "    rate: Final[float] = 0.5",
        "Constants.limit",
        "Constants.name",
        "Constants.rate",
    ):
        expect_in(item=line, container=out)
    expect_equal(actual=_fixed(source=out), expected=out)


DOCUMENTED: Final[str] = '''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        depth: How deep to go.

    """

    depth: Final[int] = 2
'''


def test_the_attributes_section_documents_the_new_constant() -> None:
    """Check that the attributes section documents the new constant."""
    out: str = _fixed(
        source=DOCUMENTED
        + """\


LIMIT = 3


def f():
    return LIMIT
""",
    )
    expect_in(
        item=(
            "        depth (Final[int]): How deep to go.\n"
            "        limit (Final[int]): Grouped module constant.\n"
        ),
        container=out,
    )
    expect_equal(actual=_fixed(source=out), expected=out)


def test_a_class_without_an_attributes_section_is_left_documented_as_is() -> (
    None
):
    """Check that the new constant joins the documented attributes."""
    out: str = _fixed(
        source=Constants.class_source
        + """\


LIMIT = 3


def f():
    return LIMIT
""",
    )
    expect_in(
        item="""\
        limit (Final[int]): Grouped module constant.
""",
        container=out,
    )


def test_the_proven_ceiling_adds_final_but_does_not_move() -> None:
    """Check that the proven ceiling adds final but does not move."""
    out: str = _fixed(
        source=Constants.class_source
        + """\


LIMIT = 3


def f():
    return LIMIT
""",
        ceiling=FixSafety.proven,
    )
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_in(item="return LIMIT", container=out)
    expect_not_in(item="    limit:", container=out)


def test_an_already_final_global_moves_into_the_class() -> None:
    """Check that an already final global moves into the class."""
    out: str = _fixed(
        source=Constants.class_source
        + """\


LIMIT: Final[int] = 3


def f():
    return LIMIT
""",
    )
    expect_in(item="    limit: Final[int] = 3", container=out)
    expect_in(item="return Constants.limit", container=out)


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
    expect_in(
        item="""\
@final
class Constants:""",
        container=out,
    )
    expect_in(item="    limit: Final[int] = 3", container=out)
    expect_in(item="    name: Final[str] = 'x'", container=out)
    expect_in(
        item="limit (Final[int]): Grouped module constant.",
        container=out,
    )
    expect_in(item="Constants.limit", container=out)
    expect_in(item="from typing import Final, Protocol, final", container=out)
    settled: str = out
    for _ in range(4):
        again: str = _fixed(source=settled, create=True)
        if again == settled:
            break
        settled = again
    expect_equal(actual=_fixed(source=settled, create=True), expected=settled)


def test_no_class_is_created_over_another_binding() -> None:
    """Check that no class is created over another binding."""
    out: str = _fixed(
        source="""\
Constants = {}
LIMIT = 3


def f():
    return LIMIT
""",
        create=True,
    )
    expect_not_in(item="class Constants", container=out)
    expect_in(item="return LIMIT", container=out)


def test_no_class_is_created_unless_asked_for() -> None:
    """Check that no class is created unless asked for."""
    out: str = _fixed(
        source="""\
LIMIT = 3


def f():
    return LIMIT
""",
    )
    expect_in(item="LIMIT: Final[int] = 3", container=out)
    expect_not_in(item="class Constants", container=out)


def test_is_constant_name_table() -> None:
    """Pin the ``UPPER_SNAKE`` predicate against the old regex."""
    for name in ("MAX_VALUE", "A1", "A", "A_B", "X9_Z"):
        expect_equal(actual=is_constant_name(name=name), expected=True)
    for name in ("_X", "x", "A_b", "É", "", "9A", "A-B", "Any"):
        expect_equal(actual=is_constant_name(name=name), expected=False)


def test_uppercase_attributes_are_renamed_to_snake_case() -> None:
    """Check that ``Constants`` attributes take lowercase snake_case."""
    out: str = _fixed(
        source='''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        _CASES (Final[list[int]]): Grouped module constant.
        limit (Final[int]): Grouped module constant.

    """

    _CASES: Final[list[int]] = []
    limit: Final[int] = 3


def collect() -> None:
    Constants._CASES.append(1)
    print(Constants._CASES, Constants.limit)
''',
    )
    expect_in(item="    cases: Final[list[int]] = []", container=out)
    expect_in(item="Constants.cases.append(1)", container=out)
    expect_in(item="print(Constants.cases, Constants.limit)", container=out)
    expect_in(item="        cases (Final[list[int]]):", container=out)
    expect_not_in(item="_CASES", container=out)
    expect_equal(actual=_fixed(source=out), expected=out)


def test_snake_case_rename_is_refused_over_a_string_reference() -> None:
    """Check that a string reference to the old name blocks the rename."""
    out: str = _fixed(
        source='''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants."""

    _CASES: Final[list[int]] = []


name = getattr(Constants, "_CASES")
''',
    )
    expect_in(item="    _CASES: Final[list[int]] = []", container=out)
    expect_in(item='getattr(Constants, "_CASES")', container=out)


def test_snake_case_rename_is_refused_on_a_name_clash() -> None:
    """Check that a taken snake_case name blocks the rename."""
    out: str = _fixed(
        source='''\
from typing import Final, final


@final
class Constants:
    """Group module-level constants."""

    cases: Final[list[int]] = []
    _CASES: Final[list[int]] = []
''',
    )
    expect_in(item="    _CASES: Final[list[int]] = []", container=out)
