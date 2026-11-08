"""``self.x = value`` assignments get an annotation when all writes agree."""

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


def _fixed(*, source: str) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source: Module source to fix.

    Returns:
        Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_literals_and_typed_parameters_annotate_the_first_write() -> None:
    """Check that literals and typed parameters annotate the first write."""
    out: str = _fixed(
        source="""
        class Box:
            def __init__(self, size=3):
                self.size = size
                self.name = "box"
                self.ratio = 0.5
                self.open = False

            def reset(self):
                self.size = 0
        """,
    )
    for line in (
        "self.size: int = size",
        "self.name: str = 'box'",
        "self.ratio: float = 0.5",
        "self.open: bool = False",
    ):
        expect_in(item=line, container=out)
    expect_in(item="        self.size = 0", container=out)


def test_none_plus_one_type_becomes_optional() -> None:
    """Check that none plus one type becomes optional."""
    out: str = _fixed(
        source="""
        class Cache:
            def __init__(self):
                self.value = None

            def load(self):
                self.value = 5
        """,
    )
    expect_in(item="self.value: int | None = None", container=out)


def test_call_site_hints_flow_into_attributes() -> None:
    """Check that call site hints flow into attributes."""
    out: str = _fixed(
        source="""
        class Store:
            def __init__(self, path):
                self.path = path


        Store("a")
        """,
    )
    expect_in(item="self.path: str = path", container=out)


def test_augmented_assignment_must_keep_the_type() -> None:
    """Check that augmented assignment must keep the type."""
    ok: str = _fixed(
        source="""
        class Counter:
            def __init__(self):
                self.n = 0

            def hit(self):
                self.n += 1
        """,
    )
    expect_in(item="self.n: int = 0", container=ok)
    bad: str = _fixed(
        source="""
        class Counter:
            def __init__(self):
                self.n = 0

            def hit(self):
                self.n += 0.5
        """,
    )
    expect_not_in(item="self.n:", container=bad)


def test_refusals() -> None:
    """Check that unclear attributes stay unannotated."""
    cases: dict[str, str] = {
        "types disagree": (
            "class C:\n    def __init__(self):\n        self.x = 1\n"
            "    def f(self):\n        self.x = 'a'\n"
        ),
        "unprovable value": (
            "class C:\n    def __init__(self):\n        self.x = make()\n"
        ),
        "only none": (
            "class C:\n    def __init__(self):\n        self.x = None\n"
        ),
        "written from outside": (
            "class C:\n    def __init__(self):\n        self.x = 1\n\n\n"
            "c = C()\nc.x = 'a'\n"
        ),
        "already annotated": (
            "class C:\n    def __init__(self):\n        self.x: int = 1\n"
            "    def f(self):\n        self.x = 2\n"
        ),
        "class level binding": (
            "class C:\n    x = 0\n\n    def __init__(self):\n"
            "        self.x = 1\n"
        ),
        "external base": (
            "class C(Base):\n    def __init__(self):\n        self.x = 1\n"
        ),
        "dynamic writes": (
            "class C:\n    def __init__(self, k):\n        self.x = 1\n"
            "        setattr(self, k, 'a')\n"
        ),
        "tuple target": (
            "class C:\n    def __init__(self):\n"
            "        self.x, self.y = 1, 2\n"
        ),
        "property": (
            "class C:\n    def __init__(self):\n        self._x = 1\n"
            "    @property\n    def x(self):\n        return self._x\n"
            "    @x.setter\n    def x(self, v):\n        self._x = v\n"
        ),
        "mutated container": (
            "class C:\n    def __init__(self):\n        self.items = []\n"
        ),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_equal(
            actual=out.count("self.x:"),
            expected=source.count("self.x:"),
            message=f"{label}: {out}",
        )
        expect_not_in(
            item="self.items:",
            container=out,
            message=f"{label}: {out}",
        )


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: str = _fixed(
        source="""
        class Box:
            def __init__(self, size=3):
                self.size = size
                self.tag = None

            def retag(self):
                self.tag = "x"
        """,
    )
    expect_equal(actual=_fixed(source=first), expected=first)
