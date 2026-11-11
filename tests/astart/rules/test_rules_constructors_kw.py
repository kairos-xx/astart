"""Verify keyword fixes on constructor calls (M2-03)."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, LiteralString

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the fixer on ``source``.

    Args:
        source (str): Module source to fix.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def test_init_parameters_become_keywords() -> None:
    """Check that init parameters become keywords."""
    result: FixResult = _fix(
        source="""
        class P:
            def __init__(self, x, y):
                self.x = x
                self.y = y


        P(1, 2)
        """,
    )
    expect_in(item="P(x=1, y=2)", container=result.source)


def test_dataclass_fields_become_keywords() -> None:
    """Check that dataclass fields become keywords."""
    result: FixResult = _fix(
        source="""
        from dataclasses import dataclass


        @dataclass(frozen=True)
        class D:
            a: int
            b: str = "s"


        D(1, "t")
        """,
    )
    expect_in(item="D(a=1, b='t')", container=result.source)


def test_dataclass_with_a_skipped_field_keeps_the_rest_aligned() -> None:
    """Check that dataclass with a skipped field keeps the rest aligned."""
    result: FixResult = _fix(
        source="""
        from dataclasses import dataclass, field


        @dataclass
        class D:
            a: int
            hidden: int = field(init=False, default=0)
            c: int = 2


        D(1, 3)
        """,
    )
    expect_in(item="D(a=1, c=3)", container=result.source)


def test_unclear_dataclasses_are_left_alone() -> None:
    """Check that unclear dataclasses are left alone."""
    for body in (
        """\
@dataclass(init=False)
class D:
    a: int
    b: int = 0
""",
        """\
@dataclass(kw_only=True)
class D:
    a: int
    b: int = 0
""",
        """\
@dataclass
class D(Base):
    a: int
    b: int = 0
""",
        """\
@other
@dataclass
class D:
    a: int
    b: int = 0
""",
        (
            "@dataclass\nclass D:\n    _: KW_ONLY\n"
            "    a: int = 0\n    b: int = 0\n"
        ),
    ):
        source: LiteralString = (
            "from dataclasses import dataclass, KW_ONLY\n\n\n"
            "class Base:\n    pass\n\n\n"
            "def other(cls):\n    return cls\n\n\n"
            + body
            + """\


D(1, 2)
"""
        )
        expect_in(
            item="D(1, 2)",
            container=_fix(source=source).source,
            message=body,
        )
