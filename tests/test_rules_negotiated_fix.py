"""Negotiated annotations written by the fixer must be valid when evaluated."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
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
    from importlib.abc import Loader
    from importlib.machinery import ModuleSpec
    from pathlib import Path

    from astart.rules.registry import Registries


def _fixed(*, source: str) -> str:
    """Fix a module at the guarded ceiling with negotiation on.

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
        settings=FixSettings(ceiling=FixSafety.guarded, negotiate=True),
    ).source


def _runs(*, source: str, folder: Path) -> None:
    """Import a module from a file, so a bad annotation raises.

    Args:
        source: Module text.
        folder: Directory to write the module into.

    Raises:
        AssertionError: When the fixed module cannot be loaded.

    """
    path: Path = folder / "fixed_module.py"
    _ = path.write_text(data=source, encoding="utf-8")
    spec: ModuleSpec | None = spec_from_file_location(
        name="fixed_module",
        location=path,
    )
    if spec is None or spec.loader is None:
        msg: str = "cannot load the fixed module"
        raise AssertionError(msg)
    loader: Loader = spec.loader
    loader.exec_module(module=module_from_spec(spec=spec))


def test_a_method_never_names_its_own_class_unquoted(tmp_path: Path) -> None:
    """Check that ``-> URIBuilder`` inside ``URIBuilder`` is not written.

    Args:
        tmp_path: Directory the fixed module is imported from.

    """
    fixed: str = _fixed(
        source="""
        class URIBuilder:
            def __init__(self, scheme):
                self.scheme = scheme

            def add_scheme(self, scheme):
                return URIBuilder(scheme)
        """,
    )
    expect_not_in(item="-> URIBuilder", container=fixed)
    _runs(source=fixed, folder=tmp_path)


def test_a_function_before_a_class_does_not_name_it(tmp_path: Path) -> None:
    """Check that a class defined later cannot appear in a signature.

    Args:
        tmp_path: Directory the fixed module is imported from.

    """
    fixed: str = _fixed(
        source="""
        def make():
            return Late()

        class Late:
            pass
        """,
    )
    expect_not_in(item="-> Late", container=fixed)
    _runs(source=fixed, folder=tmp_path)


def test_a_function_after_a_class_may_name_it(tmp_path: Path) -> None:
    """Check that an earlier, complete class is fine.

    Args:
        tmp_path: Directory the fixed module is imported from.

    """
    fixed: str = _fixed(
        source="""
        class Early:
            pass

        def make():
            return Early()
        """,
    )
    expect_in(item="-> Early", container=fixed)
    _runs(source=fixed, folder=tmp_path)


def test_a_nested_function_may_name_any_module_class(tmp_path: Path) -> None:
    """Check that a def inside a function runs after every class exists.

    Args:
        tmp_path: Directory the fixed module is imported from.

    """
    fixed: str = _fixed(
        source="""
        def outer():
            def inner():
                return Later()
            return inner

        class Later:
            pass
        """,
    )
    expect_in(item="-> Later", container=fixed)
    _runs(source=fixed, folder=tmp_path)


def test_a_class_named_like_a_stdlib_type_is_not_imported_over() -> None:
    """Check that the module's own ``UUID`` is not shadowed by an import."""
    fixed: str = _fixed(
        source="""
        class UUID:
            def __init__(self, value):
                self.value = value

            def clone(self):
                twin = UUID(self.value)
                return twin
        """,
    )
    expect_not_in(item="import", container=fixed)
