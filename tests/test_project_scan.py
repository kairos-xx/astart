"""Verify per-module scanning: imports, ``__all__`` and bound names."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from astart.project.scan import (
    ImportKind,
    ImportRecord,
    ModuleScan,
    scan_module,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_true,
)


def _scan(*, source: str, name: str = "pkg.mod") -> ModuleScan:
    """Scan a source string as one module.

    Args:
        source: Module source text.
        name: Dotted name to record.

    Returns:
        The scan.

    """
    return scan_module(
        source=dedent(text=source),
        name=name,
        path=Path(f"{name.replace('.', '/')}.py"),
    )


def test_scan_absolute_imports() -> None:
    """Check that absolute imports record their target module."""
    scan: ModuleScan = _scan(
        source="""\
        import os
        import pkg.sub as sub
        from pkg.other import f as g
        """,
    )
    records: set[tuple[str, str, str | None]] = {
        (r.local, r.module, r.symbol) for r in scan.imports
    }
    expect_in(item=("os", "os", None), container=records)
    expect_in(item=("sub", "pkg.sub", None), container=records)
    expect_in(item=("g", "pkg.other", "f"), container=records)


def test_scan_import_binds_top_level() -> None:
    """Check that ``import a.b`` binds ``a``, not ``a.b``."""
    scan: ModuleScan = _scan(source="import a.b.c\n")
    record: ImportRecord = scan.imports[0]
    expect_equal(actual=record.local, expected="a")
    expect_equal(actual=record.module, expected="a")
    expect_equal(actual=record.kind, expected=ImportKind.module)


def test_scan_relative_imports() -> None:
    """Check that relative imports resolve against the package."""
    scan: ModuleScan = _scan(
        source="""\
        from . import sibling
        from .sub import member
        from ..up import top
        from . import *
        """,
        name="pkg.inner.mod",
    )
    records: set[tuple[str, str, str | None]] = {
        (r.local, r.module, r.symbol) for r in scan.imports
    }
    expect_in(item=("sibling", "pkg.inner", "sibling"), container=records)
    expect_in(item=("member", "pkg.inner.sub", "member"), container=records)
    expect_in(item=("top", "pkg.up", "top"), container=records)
    expect_in(item=("*", "pkg.inner", None), container=records)
    expect_equal(
        actual=scan.star_modules,
        expected=("pkg.inner",),
    )


def test_scan_init_relative_imports() -> None:
    """Check that a package ``__init__`` resolves ``.`` to itself."""
    scan: ModuleScan = scan_module(
        source="from .mod import f\n",
        name="pkg",
        path=Path("pkg/__init__.py"),
    )
    record: ImportRecord = scan.imports[0]
    expect_equal(actual=record.module, expected="pkg.mod")
    expect_equal(actual=record.symbol, expected="f")


def test_scan_conditional_imports() -> None:
    """Check that imports inside ``try``/``if``/functions are flagged."""
    scan: ModuleScan = _scan(
        source="""\
        import top

        try:
            import guarded
        except ImportError:
            import fallback

        def helper():
            import nested
        """,
    )
    flagged: dict[str, bool] = {r.local: r.conditional for r in scan.imports}
    expect_false(condition=flagged["top"])
    expect_true(condition=flagged["guarded"])
    expect_true(condition=flagged["fallback"])
    expect_true(condition=flagged["nested"])


def test_scan_top_level_names() -> None:
    """Check that functions, classes and assignments are separated."""
    scan: ModuleScan = _scan(
        source="""\
        def f(): ...
        async def g(): ...
        class C: ...
        VALUE = 1
        other: int = 2

        def outer():
            def inner(): ...
        """,
    )
    expect_equal(actual=scan.functions, expected=("f", "g", "outer"))
    expect_equal(actual=scan.classes, expected=("C",))
    expect_in(item="VALUE", container=scan.defined_names)
    expect_in(item="other", container=scan.defined_names)


def test_scan_all_literal() -> None:
    """Check that a literal ``__all__`` is recorded."""
    scan: ModuleScan = _scan(
        source="""\
        __all__ = ["a", "b"]
        __all__ += ("c",)
        __all__.append("d")
        __all__.extend(["e", "f"])
        """,
    )
    expect_true(condition=scan.all_declared)
    expect_equal(
        actual=scan.all_names,
        expected=("a", "b", "c", "d", "e", "f"),
    )


def test_scan_all_dynamic() -> None:
    """Check that a computed ``__all__`` is declared but unknown."""
    scan: ModuleScan = _scan(
        source="__all__ = [name for name in dir() "
        "if not name.startswith('_')]\n",
    )
    expect_true(condition=scan.all_declared)
    expect_is(actual=scan.all_names, expected=None)


def test_scan_all_absent() -> None:
    """Check that no ``__all__`` means no declared exports."""
    scan: ModuleScan = _scan(source="def f(): ...\n")
    expect_false(condition=scan.all_declared)
    expect_is(actual=scan.all_names, expected=None)


def test_scan_bound_names() -> None:
    """Check that bound names cover definitions and imports."""
    scan: ModuleScan = _scan(
        source="""\
        import mod
        from other import thing as alias
        from star import *
        def f(): ...
        X = 1
        """,
    )
    names: frozenset[str] = scan.bound_names
    for expected in ("mod", "alias", "f", "X"):
        expect_in(item=expected, container=names)
    expect_not_in_star(scan=scan)


def expect_not_in_star(*, scan: ModuleScan) -> None:
    """Check that the star sentinel is not a bound name.

    Args:
        scan: The scan to inspect.

    Raises:
        AssertionError: When ``*`` is a bound name.

    """
    for name in scan.bound_names:
        if name == "*":
            msg: str = "star sentinel is bound"
            raise AssertionError(msg)


def test_scan_content_hash_changes() -> None:
    """Check that content hashes track the source text."""
    one: ModuleScan = _scan(source="X = 1\n")
    two: ModuleScan = _scan(source="X = 2\n")
    same: ModuleScan = _scan(source="X = 1\n")
    expect_equal(actual=one.content_hash, expected=same.content_hash)
    expect_false(condition=one.content_hash == two.content_hash)


def test_scan_is_package() -> None:
    """Check that ``__init__.py`` scans as a package."""
    package: ModuleScan = scan_module(
        source="X = 1\n",
        name="pkg",
        path=Path("pkg/__init__.py"),
    )
    module: ModuleScan = _scan(source="X = 1\n")
    expect_true(condition=package.is_package)
    expect_false(condition=module.is_package)
