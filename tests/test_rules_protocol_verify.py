"""A synthesized Protocol is dropped when a call site provably objects."""

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
        The fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_a_builtin_without_the_member_vetoes_the_protocol() -> None:
    """Check that passing a ``str`` to a ``.read()`` user is an objection."""
    out: str = _fixed(
        source="""
        def load(src):
            return src.read(1)

        load("abc")
        """,
    )
    expect_not_in(item="Protocol", container=out)


def test_none_vetoes_a_member_protocol() -> None:
    """Check that ``None`` has no ``read``."""
    out: str = _fixed(
        source="""
        def load(src):
            return src.read(1)

        load(None)
        """,
    )
    expect_not_in(item="Protocol", container=out)


def test_a_module_class_without_the_member_vetoes_it() -> None:
    """Check that a plain in-module class lacking ``read`` objects."""
    out: str = _fixed(
        source="""
        class Empty:
            pass

        def load(src):
            return src.read(1)

        load(Empty())
        """,
    )
    expect_not_in(item="LoadSrcProtocol", container=out)


def test_a_module_class_with_the_member_keeps_the_protocol() -> None:
    """Check that a conforming class does not object."""
    out: str = _fixed(
        source="""
        class Reader:
            def read(self, n):
                return n

        def load(src):
            return src.read(1)

        load(Reader())
        """,
    )
    expect_in(item="class LoadSrcProtocol(Protocol):", container=out)


def test_unknown_arguments_do_not_object() -> None:
    """Check that an argument of unknown type is inconclusive."""
    out: str = _fixed(
        source="""
        import io

        def load(src):
            return src.read(1)

        load(io.BytesIO(b"x"))
        """,
    )
    expect_in(item="LoadSrcProtocol", container=out)


def test_classes_with_bases_are_inconclusive() -> None:
    """Check that an inherited member cannot be ruled out."""
    out: str = _fixed(
        source="""
        import io

        class Child(io.BytesIO):
            pass

        def load(src):
            return src.read(1)

        load(Child())
        """,
    )
    expect_in(item="LoadSrcProtocol", container=out)
