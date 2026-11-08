"""Verify the whole-project index: call graph, escapes and refresh."""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.project.builder import build_index
from astart.project.index import CallRecord, ProjectConfig, ProjectIndex
from astart.project.scan import ModuleScan, scan_module

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from astart.project.table import ResolvedSymbol


def _index(*, sources: dict[str, str], closed: bool = False) -> ProjectIndex:
    """Build an index over named sources in a temporary tree.

    Args:
        sources: Dotted module name to source text.
        closed: Whether to disable the external-caller assumption.

    Returns:
        The index.

    """
    root: Path = Path(mkdtemp())
    files: list[Path] = []
    for name, source in sources.items():
        is_init: bool = name.endswith(".__pkg__")
        real: str = name.removesuffix(".__pkg__")
        parts: list[str] = real.split(sep=".")
        for depth in range(1, len(parts)):
            init: Path = root.joinpath(*parts[:depth], "__init__.py")
            if not init.exists():
                init.parent.mkdir(parents=True, exist_ok=True)
                init.write_text(data="", encoding="utf-8")
                files.append(init)
        file: Path = (
            root.joinpath(*parts, "__init__.py")
            if is_init
            else root.joinpath(*parts).with_suffix(suffix=".py")
        )
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(data=dedent(text=source), encoding="utf-8")
        if (is_init and file not in files) or not is_init:
            files.append(file)
    return build_index(
        files=files,
        config=ProjectConfig(assume_external_callers=not closed),
    ).index


def test_call_graph_records() -> None:
    """Check that calls across modules land on the callee's record."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
    )
    records: tuple[CallRecord, ...] = index.records_for(qualified="core.f")
    expect_equal(actual=len(records), expected=1)
    expect_equal(actual=records[0].module, expected="user")
    expect_equal(actual=records[0].caller, expected="user.run")
    expect_equal(
        actual=index.callers(qualified="core.f"),
        expected=frozenset({"user.run"}),
    )


def test_call_graph_dotted() -> None:
    """Check that ``pkg.mod.f()`` attribute calls resolve."""
    index: ProjectIndex = _index(
        sources={
            "pkg.core": "def f(x): return x\n",
            "pkg.user": (
                "import pkg.core\ndef run():\n    return pkg.core.f(1)\n"
            ),
        },
    )
    records: tuple[CallRecord, ...] = index.records_for(qualified="pkg.core.f")
    expect_equal(actual=len(records), expected=1)


def test_call_graph_external_ignored() -> None:
    """Check that calls to libraries produce no project records."""
    index: ProjectIndex = _index(
        sources={
            "user": "import os\ndef run():\n    return os.getcwd()\n",
        },
    )
    expect_equal(actual=index.defined(), expected=frozenset({"user.run"}))
    for qualified in index.defined():
        expect_equal(
            actual=index.records_for(qualified=qualified),
            expected=(),
        )


def test_definitions_nested() -> None:
    """Check that methods and nested functions are defined qualified."""
    index: ProjectIndex = _index(
        sources={
            "mod": (
                "class C:\n"
                "    def m(self): ...\n"
                "def outer():\n"
                "    def inner(): ...\n"
            ),
        },
    )
    defined: frozenset[str] = index.defined()
    expect_in(item="mod.C", container=defined)
    expect_in(item="mod.C.m", container=defined)
    expect_in(item="mod.outer", container=defined)
    expect_in(item="mod.outer.inner", container=defined)


def test_escape_detection() -> None:
    """Check that a function used as a value is marked escaped."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\ndef g(): return f\n",
            "user": (
                "from core import f\n"
                "alias = f\n"
                "def run():\n"
                "    return alias(1)\n"
            ),
        },
    )
    expect_true(condition=index.escaped(qualified="core.f"))
    expect_true(condition=index.open_world(qualified="core.f"))


def test_private_not_escaped_by_call() -> None:
    """Check that a private callee is closed-world when unexported."""
    index: ProjectIndex = _index(
        sources={
            "core": "def _f(x): return x\n",
            "user": "from core import _f\ndef run():\n    return _f(1)\n",
        },
    )
    expect_false(condition=index.escaped(qualified="core._f"))
    expect_false(condition=index.open_world(qualified="core._f"))


def test_exported_open_world() -> None:
    """Check that exported functions are open-world by default."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
    )
    expect_true(condition=index.exported(qualified="core.f"))
    expect_true(condition=index.open_world(qualified="core.f"))


def test_exported_closed_world() -> None:
    """Check that ``assume_external_callers=False`` closes exports."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
        closed=True,
    )
    expect_false(condition=index.open_world(qualified="core.f"))


def test_reexported_is_exported() -> None:
    """Check that ``__init__`` re-exports mark the symbol exported."""
    index: ProjectIndex = _index(
        sources={
            "pkg.__pkg__": "",
            "pkg.mod": "def f(x): return x\n",
        },
    )
    scan: ModuleScan | None = index.module_scan(module="pkg")
    expect_is_not_none_scan(scan=scan)
    # rewrite pkg/__init__ to re-export f
    if scan:
        path: Path = scan.path
        path.write_text(data="from .mod import f\n", encoding="utf-8")
        index.refresh(
            scan=scan_module(
                source="from .mod import f\n",
                name="pkg",
                path=path,
            ),
        )
        expect_true(condition=index.exported(qualified="pkg.mod.f"))


def expect_is_not_none_scan(*, scan: object) -> None:
    """Require a scan to exist.

    Args:
        scan: The scan.

    Raises:
        AssertionError: When the scan is ``None``.

    """
    if scan is None:
        msg: str = "module was not scanned"
        raise AssertionError(msg)


def test_refresh_same_hash_noop() -> None:
    """Check that refreshing unchanged content is free."""
    index: ProjectIndex = _index(
        sources={"mod": "X = 1\n"},
    )
    scan: ModuleScan | None = index.module_scan(module="mod")
    expect_is_not_none_scan(scan=scan)
    if scan:
        version: int = index.version
        affected: frozenset[str] = index.refresh(
            scan=scan_module(
                source="X = 1\n",
                name="mod",
                path=scan.path,
            ),
        )
        expect_equal(actual=affected, expected=frozenset())
        expect_equal(actual=index.version, expected=version)


def test_refresh_updates_callers() -> None:
    """Check that a changed caller invalidates its old callees."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\ndef g(x): return x\n",
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
    )
    scan: ModuleScan | None = index.module_scan(module="user")
    expect_is_not_none_scan(scan=scan)
    if scan:
        affected: frozenset[str] = index.refresh(
            scan=scan_module(
                source="from core import g\ndef run():\n    return g(1)\n",
                name="user",
                path=scan.path,
            ),
        )
        expect_in(item="core.f", container=affected)
        expect_in(item="core.g", container=affected)
        expect_equal(actual=index.records_for(qualified="core.f"), expected=())
        expect_equal(
            actual=len(index.records_for(qualified="core.g")),
            expected=1,
        )


def test_refresh_reresolution() -> None:
    """Check that a removed export re-resolves existing call records."""
    index: ProjectIndex = _index(
        sources={
            "pkg.__pkg__": "from .a import f\n",
            "pkg.a": "def f(x): return x\n",
            "pkg.b": "def f(x): return x\n",
            "user": "from pkg import f\ndef run():\n    return f(1)\n",
        },
    )
    expect_equal(
        actual=len(index.records_for(qualified="pkg.a.f")),
        expected=1,
    )
    scan: ModuleScan | None = index.module_scan(module="pkg")
    expect_is_not_none_scan(scan=scan)
    if scan:
        index.refresh(
            scan=scan_module(
                source="from .b import f\n",
                name="pkg",
                path=scan.path,
            ),
        )
        expect_equal(
            actual=index.records_for(qualified="pkg.a.f"),
            expected=(),
        )
        expect_equal(
            actual=len(index.records_for(qualified="pkg.b.f")),
            expected=1,
        )


def test_remove_module() -> None:
    """Check that removing a module drops its records."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
    )
    affected: frozenset[str] = index.remove(name="user")
    expect_in(item="core.f", container=affected)
    expect_equal(actual=index.records_for(qualified="core.f"), expected=())
    expect_is(actual=index.module_scan(module="user"), expected=None)


def test_imported_names() -> None:
    """Check that bound names report their resolutions."""
    index: ProjectIndex = _index(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\nLOCAL = 1\n",
        },
    )
    names: dict[str, ResolvedSymbol] = index.imported_names(module="user")
    expect_in(item="f", container=names)
    expect_equal(actual=names["f"].qualified, expected="core.f")
    expect_in(item="LOCAL", container=names)


def test_constructor_method_shape() -> None:
    """Check that ``C().m()`` resolves to the method."""
    index: ProjectIndex = _index(
        sources={
            "core": "class C:\n    def m(self, x): return x\n",
            "user": ("from core import C\ndef run():\n    return C().m(1)\n"),
        },
    )
    records: tuple[CallRecord, ...] = index.records_for(qualified="core.C.m")
    expect_equal(actual=len(records), expected=1)


def test_method_call_records() -> None:
    """Check that ``C.m()`` static-style calls resolve too."""
    index: ProjectIndex = _index(
        sources={
            "core": "class C:\n    @staticmethod\n    def m(x): return x\n",
            "user": ("from core import C\ndef run():\n    return C.m(1)\n"),
        },
    )
    records: tuple[CallRecord, ...] = index.records_for(qualified="core.C.m")
    expect_equal(actual=len(records), expected=1)
