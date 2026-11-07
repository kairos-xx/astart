"""Verify Protocol synthesis through the fix runner."""

from __future__ import annotations

import ast
from textwrap import dedent

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)


def _fix(*, source: str) -> FixResult:
    registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def test_unannotated_structural_parameter_gets_a_protocol() -> None:
    """Check that unannotated structural parameter gets a protocol."""
    result = _fix(
        source="""
        def load(src):
            return src.read(1)
        """,
    )
    ast.parse(source=result.source)
    expect_in(item="from typing import Protocol", container=result.source)
    expect_in(item="class LoadSrcProtocol(Protocol):", container=result.source)
    expect_in(item="def load(src: LoadSrcProtocol)", container=result.source)
    expect_in(item="def read(self, arg0: int, /)", container=result.source)


def test_protocol_precedes_the_function_that_uses_it() -> None:
    """Check that protocol precedes the function that uses it."""
    result = _fix(
        source="""
        def load(src):
            return src.read(1)
        """,
    )
    expect_true(
        condition=result.source.index("class LoadSrcProtocol")
        < result.source.index("def load("),
    )


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first = _fix(source="def load(src):\n    return src.read(1)\n")
    second = _fix(source=first.source)
    expect_equal(actual=second.source, expected=first.source)


def test_identical_usage_shares_one_protocol() -> None:
    """Check that identical usage shares one protocol."""
    result = _fix(
        source="""
        def a(src):
            return src.read(1)


        def b(stream):
            return stream.read(2)
        """,
    )
    expect_equal(actual=result.source.count("(Protocol):"), expected=1)
    expect_in(item="def b(stream: ASrcProtocol", container=result.source)


def test_existing_protocol_import_is_reused() -> None:
    """Check that existing protocol import is reused."""
    result = _fix(
        source="""
        from typing import Protocol


        def load(src):
            return src.read(1)
        """,
    )
    expect_equal(actual=result.source.count("import Protocol"), expected=1)


def test_value_use_gets_no_protocol() -> None:
    """Check that value use gets no protocol."""
    result = _fix(source="def load(src):\n    return src\n")
    expect_not_in(item="Protocol", container=result.source)


def test_default_value_gets_no_protocol() -> None:
    """Check that default value gets no protocol."""
    result = _fix(source="def load(src=None):\n    return src.read(1)\n")
    expect_not_in(item="Protocol", container=result.source)


def test_method_parameter_protocol_precedes_the_class() -> None:
    """Check that method parameter protocol precedes the class."""
    result = _fix(
        source="""
        class Loader:
            def load(self, src):
                return src.read(1)
        """,
    )
    ast.parse(source=result.source)
    expect_true(
        condition=result.source.index("(Protocol):")
        < result.source.index("class Loader"),
    )
    expect_in(
        item="def load(self, src: LoadSrcProtocol",
        container=result.source,
    )


def test_proven_ceiling_does_not_synthesize() -> None:
    """Check that proven ceiling does not synthesize."""
    registries = default_registries()
    result = fix_source(
        source="def load(src):\n    return src.read(1)\n",
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.proven),
    )
    expect_not_in(item="Protocol", container=result.source)
