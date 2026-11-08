"""Verify cross-module symbol resolution."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.project.scan import ModuleScan, scan_module
from astart.project.table import (
    ResolvedSymbol,
    SymbolKind,
    SymbolTable,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def _table(*, sources: Mapping[str, str]) -> SymbolTable:
    """Build a symbol table over named sources.

    Args:
        sources: Dotted module name to source text. ``__init__`` files use
            the bare package name as key.

    Returns:
        The table.

    """
    scans: dict[str, ModuleScan] = {}
    for name, source in sources.items():
        leaf: str = (
            "__init__"
            if name.endswith(".__pkg__")
            else name.rpartition(".")[2]
        )
        real_name: str = name.removesuffix(".__pkg__")
        scans[real_name] = scan_module(
            source=dedent(text=source),
            name=real_name,
            path=Path(f"{real_name.replace('.', '/')}/{leaf}.py")
            if leaf == "__init__"
            else Path(f"{real_name.replace('.', '/')}.py"),
        )
    return SymbolTable(scans=scans)


def test_resolve_local_definition() -> None:
    """Check that module-level names resolve to their own module."""
    table: SymbolTable = _table(
        sources={
            "pkg.mod": "def f(): ...\nclass C: ...\nX = 1\n",
        },
    )
    function: ResolvedSymbol | None = table.resolve(module="pkg.mod", name="f")
    expect_is_not_none_symbol(symbol=function)
    if function:
        expect_equal(actual=function.qualified, expected="pkg.mod.f")
        expect_equal(actual=function.kind, expected=SymbolKind.function)
        cls: ResolvedSymbol | None = table.resolve(module="pkg.mod", name="C")
        if cls:
            expect_equal(actual=cls.kind, expected=SymbolKind.class_)
            var: ResolvedSymbol | None = table.resolve(
                module="pkg.mod",
                name="X",
            )
            if var:
                expect_equal(actual=var.kind, expected=SymbolKind.variable)


def expect_is_not_none_symbol(*, symbol: ResolvedSymbol | None) -> None:
    """Require a resolution to exist.

    Args:
        symbol: The resolution.

    Raises:
        AssertionError: When the resolution is ``None``.

    """
    if symbol is None:
        msg: str = "symbol did not resolve"
        raise AssertionError(msg)


def test_resolve_member_import() -> None:
    """Check that ``from pkg.mod import f`` reaches the definition."""
    table: SymbolTable = _table(
        sources={
            "pkg.mod": "def f(): ...\n",
            "user": "from pkg.mod import f\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="f")
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="pkg.mod.f")
        expect_false(condition=symbol.external)


def test_resolve_module_import() -> None:
    """Check that ``import pkg.mod`` binds the module object."""
    table: SymbolTable = _table(
        sources={
            "pkg.__pkg__": "",
            "pkg.mod": "def f(): ...\n",
            "user": "import pkg.mod\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="pkg")
    expect_is_not_none_symbol(symbol=symbol)
    dotted: ResolvedSymbol | None = table.resolve_path(
        module="user",
        dotted="pkg.mod.f",
    )
    expect_is_not_none_symbol(symbol=dotted)
    if dotted:
        expect_equal(actual=dotted.qualified, expected="pkg.mod.f")


def test_resolve_module_import_alias() -> None:
    """Check that ``import pkg.mod as x`` binds the submodule."""
    table: SymbolTable = _table(
        sources={
            "pkg.__pkg__": "",
            "pkg.mod": "def f(): ...\n",
            "user": "import pkg.mod as x\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="x")
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="pkg.mod")
        expect_equal(actual=symbol.kind, expected=SymbolKind.module)
        dotted: ResolvedSymbol | None = table.resolve_path(
            module="user",
            dotted="x.f",
        )
        expect_is_not_none_symbol(symbol=dotted)
        if dotted:
            expect_equal(actual=dotted.qualified, expected="pkg.mod.f")


def test_resolve_reexport_chain() -> None:
    """Check that ``__init__`` re-exports resolve through the package."""
    table: SymbolTable = _table(
        sources={
            "pkg.__pkg__": "from .mod import f\n",
            "pkg.mod": "def f(): ...\n",
            "user": "from pkg import f\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="f")
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="pkg.mod.f")
        expect_false(condition=symbol.external)


def test_resolve_external_member() -> None:
    """Check that names from unscanned modules resolve external."""
    table: SymbolTable = _table(
        sources={
            "user": "import requests\nfrom libx import connect\n",
        },
    )
    module: ResolvedSymbol | None = table.resolve(
        module="user",
        name="requests",
    )
    expect_is_not_none_symbol(symbol=module)
    if module:
        expect_true(condition=module.external)
        member: ResolvedSymbol | None = table.resolve(
            module="user",
            name="connect",
        )
        expect_is_not_none_symbol(symbol=member)
        if member:
            expect_true(condition=member.external)
            expect_equal(actual=member.qualified, expected="libx.connect")
            dotted: ResolvedSymbol | None = table.resolve_path(
                module="user",
                dotted="requests.get",
            )
            expect_is_not_none_symbol(symbol=dotted)
            if dotted:
                expect_true(condition=dotted.external)
                expect_equal(actual=dotted.qualified, expected="requests.get")


def test_resolve_star_import() -> None:
    """Check that star imports bind the source's exports."""
    table: SymbolTable = _table(
        sources={
            "base": "def f(): ...\ndef _hidden(): ...\n",
            "user": "from base import *\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="f")
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="base.f")
        expect_is(
            actual=table.resolve(module="user", name="_hidden"),
            expected=None,
        )


def test_resolve_sibling_module() -> None:
    """Check that a package attribute can name a sibling submodule."""
    table: SymbolTable = _table(
        sources={
            "pkg.__pkg__": "",
            "pkg.mod": "X = 1\n",
            "pkg.user": "from pkg import mod\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(
        module="pkg.user",
        name="mod",
    )
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="pkg.mod")
        expect_equal(actual=symbol.kind, expected=SymbolKind.module)


def test_resolve_conditional_prefers_first() -> None:
    """Check that the earliest conditional binding wins."""
    table: SymbolTable = _table(
        sources={
            "real": "def f(): ...\n",
            "fallback": "def f(): ...\n",
            "user": """\
            try:
                from real import f
            except ImportError:
                from fallback import f
            """,
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="f")
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="real.f")


def test_exports_literal_all() -> None:
    """Check that a literal ``__all__`` bounds the export surface."""
    table: SymbolTable = _table(
        sources={"mod": "__all__ = ['a']\na = 1\nb = 2\n"},
    )
    expect_equal(
        actual=table.exports(module="mod"),
        expected=frozenset({"a"}),
    )


def test_exports_dynamic_all() -> None:
    """Check that a dynamic ``__all__`` falls back to public names."""
    table: SymbolTable = _table(
        sources={
            "mod": ("__all__ = [n for n in dir()]\na = 1\nb = 2\n_c = 3\n"),
        },
    )
    exports: frozenset[str] = table.exports(module="mod")
    expect_in(item="a", container=exports)
    expect_in(item="b", container=exports)
    expect_false(
        condition=any(name.startswith("_") for name in exports),
    )


def test_exports_star_chain() -> None:
    """Check that star imports re-export upstream public names."""
    table: SymbolTable = _table(
        sources={
            "leaf": "def f(): ...\n",
            "mid": "from leaf import *\n",
        },
    )
    exports: frozenset[str] = table.exports(module="mid")
    expect_in(item="f", container=exports)


def test_missing_imports_reported() -> None:
    """Check that absent imported modules land in ``missing``."""
    table: SymbolTable = _table(
        sources={"user": "import absent\nfrom gone import x\n"},
    )
    expect_in(item="absent", container=table.missing)
    expect_in(item="gone", container=table.missing)


def test_resolve_qualified() -> None:
    """Check that fully qualified paths resolve through packages."""
    table: SymbolTable = _table(
        sources={
            "pkg.__pkg__": "from .mod import f\n",
            "pkg.mod": "def f(): ...\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve_qualified(
        qualified="pkg.mod.f",
    )
    expect_is_not_none_symbol(symbol=symbol)
    if symbol:
        expect_equal(actual=symbol.qualified, expected="pkg.mod.f")


def test_resolve_cycle_safe() -> None:
    """Check that mutually re-exporting packages terminate."""
    table: SymbolTable = _table(
        sources={
            "a": "from b import g\n",
            "b": "from a import f\n",
            "user": "from a import f\n",
        },
    )
    symbol: ResolvedSymbol | None = table.resolve(module="user", name="f")
    expect_is(actual=symbol, expected=None)
