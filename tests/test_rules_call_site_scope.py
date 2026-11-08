"""Call-site arguments that are variables are typed from their scope."""

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


def test_a_local_assigned_once_from_a_literal_types_the_site() -> None:
    """Check that a local assigned once from a literal types the site."""
    out: str = _fixed(
        source="""
        def show(name):
            print(name)


        def main():
            label = "apple"
            show(label)
        """,
    )
    expect_in(item="def show(name: str)", container=out)


def test_locals_built_from_typed_expressions_type_the_site() -> None:
    """Check that locals built from typed expressions type the site."""
    out: str = _fixed(
        source="""
        def show(total):
            print(total)


        def main():
            base = 1
            total = base + 2
            show(total)
        """,
    )
    expect_in(item="def show(total: int)", container=out)


def test_uppercase_module_constants_type_the_site() -> None:
    """Check that uppercase module constants type the site."""
    out: str = _fixed(
        source="""
        LIMIT = 10


        def show(n):
            print(n)


        def main():
            show(LIMIT)
        """,
    )
    expect_in(item="def show(n: int)", container=out)


def test_annotated_parameters_type_the_site() -> None:
    """Check that annotated parameters type the site."""
    out: str = _fixed(
        source="""
        def show(n):
            print(n)


        def main(count: int):
            show(count)
        """,
    )
    expect_in(item="def show(n: int)", container=out)


def test_unreliable_names_give_no_evidence() -> None:
    """Check that unreliable names give no evidence."""
    cases: dict[str, str] = {
        "reassigned": (
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    v = 1\n    v = 'a'\n    show(v)\n"
        ),
        "loop variable": (
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    for v in range(3):\n        show(v)\n"
        ),
        "widening augmented": (
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    v = 1\n    v += 0.5\n    show(v)\n"
        ),
        "lowercase module variable": (
            "limit = 10\n\n\ndef show(n):\n    print(n)\n\n\n"
            "def main():\n    show(limit)\n"
        ),
        "unknown call result": (
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    v = input()\n    show(v)\n"
        ),
        "global rebinding": (
            "LIMIT = 10\n\n\ndef show(n):\n    print(n)\n\n\n"
            "def change():\n    global LIMIT\n    LIMIT = 'x'\n\n\n"
            "def main():\n    show(LIMIT)\n"
        ),
        "nonlocal rebinding": (
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    v = 1\n\n    def inner():\n        nonlocal v\n"
            "        v = 'a'\n\n    inner()\n    show(v)\n"
        ),
    }
    for label, source in cases.items():
        out: str = _fixed(source=source)
        expect_not_in(item="n: int", container=out, message=label)
        expect_not_in(item="n: str", container=out, message=label)


def test_an_int_counter_with_augmented_updates_types_the_site() -> None:
    """Check that ``v = 1; v += 1`` is still an int at the call."""
    out: str = _fixed(
        source=(
            "def show(n):\n    print(n)\n\n\ndef main():\n"
            "    v = 1\n    v += 1\n    show(v)\n"
        ),
    )
    expect_in(item="n: int", container=out)
