"""Verify cross-module evidence flowing into the hint engine."""

from __future__ import annotations

from ast import Call, Module, parse, walk
from pathlib import Path
from tempfile import mkdtemp
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.project.builder import build_index
from astart.project.index import ProjectConfig, ProjectIndex
from astart.project.libraries import LibraryIndex, find_library_roots
from astart.rules import (
    CheckOptions,
    CheckResult,
    FixResult,
    FixSettings,
    check,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.project_bridge import (
    CrossSite,
    ProjectView,
    qualified_names,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart import BoundCall
    from astart.project.scan import ModuleScan
    from astart.project.table import ResolvedSymbol
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


def _tree(
    *,
    sources: dict[str, str],
    closed: bool = False,
) -> tuple[Path, ProjectIndex]:
    """Write sources into a package tree and index them.

    Args:
        sources: Dotted module name to source text.
        closed: Whether to disable the external-caller assumption.

    Returns:
        The root path and the index.

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
        files.append(file)
    index: ProjectIndex = build_index(
        files=files,
        config=ProjectConfig(assume_external_callers=not closed),
    ).index
    return root, index


def _parse_module(*, index: ProjectIndex, name: str) -> Module:
    """Return the retained parse tree of a scanned module.

    Args:
        index: The project index.
        name: Dotted module name.

    Returns:
        The module AST.

    """
    scan: ModuleScan = expect_not_none(
        value=index.module_scan(module=name),
    )
    return scan.tree


def test_qualified_names_nested() -> None:
    """Check that every definition gets a qualified id mapping."""
    module: Module = parse(
        source=dedent(
            text="""\
            def f(): ...
            class C:
                def m(self):
                    def inner(): ...
            """,
        ),
    )
    names: dict[int, str] = qualified_names(module=module, name="mod")
    expect_equal(
        actual=frozenset(names.values()),
        expected=frozenset(
            {"mod.f", "mod.C", "mod.C.m", "mod.C.m.inner"},
        ),
    )


def test_sites_cross_module() -> None:
    """Check that a call in another module becomes site evidence."""
    _root, index = _tree(
        sources={
            "core": "def _helper(x): return x\n",
            "user": (
                "from core import _helper\ndef run():\n    return _helper(7)\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._helper"),
    )
    site: CrossSite = sites["x"][0]
    expect_true(condition=site.definite)
    expect_true(condition=site.proven)
    expect_equal(actual=site.types, expected=("int",))


def test_sites_unknown_expansion() -> None:
    """Check that unresolvable ``*args`` produce unknown evidence."""
    _root, index = _tree(
        sources={
            "core": "def _helper(x): return x\n",
            "user": (
                "from core import _helper\n"
                "def run(*args):\n"
                "    return _helper(*args)\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._helper"),
    )
    site: CrossSite = sites["x"][0]
    expect_false(condition=site.definite)


def test_sites_same_module_excluded() -> None:
    """Check that the analysed module's own calls are left local."""
    _root, index = _tree(
        sources={
            "core": (
                "def _helper(x): return x\n"
                "def local():\n"
                "    return _helper(7)\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] | None = view.sites(
        qualified="core._helper",
    )
    expect_false(condition=sites is not None and "x" in sites)


def test_resolve_local() -> None:
    """Check that a local name resolves through the project table."""
    _root, index = _tree(
        sources={
            "core": "def f(x): return x\n",
            "user": "from core import f\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    resolved: ResolvedSymbol = expect_not_none(
        value=view.resolve_local(name="f"),
    )
    expect_equal(actual=resolved.qualified, expected="core.f")


def test_sites_unbindable_none() -> None:
    """Check that a decorated callee yields ``None`` evidence."""
    _root, index = _tree(
        sources={
            "core": (
                "def deco(fn): return fn\n@deco\ndef _helper(x): return x\n"
            ),
            "user": "from core import _helper\ndef run():\n    _helper(7)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    expect_is(actual=view.sites(qualified="core._helper"), expected=None)


def test_sites_constructor_class() -> None:
    """Check that ``C(...)`` calls evidence ``__init__`` parameters."""
    _root, index = _tree(
        sources={
            "core": "class _C:\n    def __init__(self, count): ...\n",
            "user": "from core import _C\ndef run():\n    return _C(3)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._C"),
    )
    site: CrossSite = sites["count"][0]
    expect_equal(actual=site.types, expected=("int",))


def test_open_world_guards() -> None:
    """Check exported names are open-world and private ones are not."""
    _root, index = _tree(
        sources={
            "core": "def exported(x): ...\ndef _private(x): ...\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    expect_true(condition=view.open_world(qualified="core.exported"))
    expect_false(condition=view.open_world(qualified="core._private"))


def test_binding_project_function() -> None:
    """Check that an imported call binds through the project table."""
    _root, index = _tree(
        sources={
            "core": "def f(x, y): return x + y\n",
            "user": "from core import f\ndef run():\n    return f(1, 2)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    tree: Module = _parse_module(index=index, name="user")
    call: Call = next(n for n in walk(node=tree) if isinstance(n, Call))
    bound: BoundCall = expect_not_none(value=view.binding(call=call))
    names: tuple[str, ...] = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("x", "y"))


def test_binding_external_library(*, tmp_path: Path) -> None:
    """Check that a library call binds through the stub contract.

    Args:
        tmp_path: Directory acting as site-packages.

    """
    stub: Path = tmp_path / "libx-stubs" / "libx" / "__init__.pyi"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text(
        data="def connect(host: str, port: int) -> bool: ...\n",
        encoding="utf-8",
    )
    _root, index = _tree(
        sources={
            "user": "import libx\nok = libx.connect('h', 80)\n",
        },
    )
    libraries: LibraryIndex = LibraryIndex(
        roots=find_library_roots(site_packages=(tmp_path,)),
    )
    view: ProjectView = ProjectView(
        index=index,
        module="user",
        libraries=libraries,
    )
    tree: Module = _parse_module(index=index, name="user")
    call: Call = next(n for n in walk(node=tree) if isinstance(n, Call))
    bound: BoundCall = expect_not_none(value=view.binding(call=call))
    names: tuple[str, ...] = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("host", "port"))


def test_binding_unknown_none() -> None:
    """Check that an unresolvable callee binds to ``None``."""
    _root, index = _tree(
        sources={
            "user": "def run(callback):\n    return callback(1)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    tree: Module = _parse_module(index=index, name="user")
    call: Call = next(
        n
        for n in walk(node=tree)
        if isinstance(n, Call) and getattr(n.func, "id", "") == "callback"
    )
    expect_is(actual=view.binding(call=call), expected=None)


def test_check_cross_module_hint() -> None:
    """Check that ``check`` reports the hint another module earned."""
    root, index = _tree(
        sources={
            "core": "def _helper(x): return x\n",
            "user": (
                "from core import _helper\ndef run():\n    return _helper(7)\n"
            ),
        },
    )
    catalog: Catalog = load_default_catalog(registries=default_registries())
    registries: Registries = default_registries()
    source: str = (root / "core.py").read_text(encoding="utf-8")
    result: CheckResult = check(
        source=source,
        filename="core.py",
        catalog=catalog,
        registries=registries,
        options=CheckOptions(
            project=ProjectView(index=index, module="core"),
        ),
    )
    keys: set[str] = {finding.rule_key for finding in result.findings}
    expect_in(item="typing.missing-annotation", container=keys)


def test_fix_cross_module_hint() -> None:
    """Check that ``fix_source`` writes the cross-module annotation."""
    root, index = _tree(
        sources={
            "core": "def _helper(x):\n    print(x)\n",
            "user": (
                "from core import _helper\ndef run():\n    return _helper(7)\n"
            ),
        },
    )
    source: str = (root / "core.py").read_text(encoding="utf-8")
    outcome: FixResult = fix_source(
        source=source,
        filename="core.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            project=ProjectView(index=index, module="core"),
        ),
    )
    expect_in(item="x: int", container=outcome.source)


def test_fix_open_world_skips_exported() -> None:
    """Check that exported callees keep unannotated params by default."""
    root, index = _tree(
        sources={
            "core": "def exported(x):\n    print(x)\n",
            "user": (
                "from core import exported\n"
                "def run():\n"
                "    return exported(7)\n"
            ),
        },
    )
    source: str = (root / "core.py").read_text(encoding="utf-8")
    outcome: FixResult = fix_source(
        source=source,
        filename="core.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            project=ProjectView(index=index, module="core"),
        ),
    )
    expect_in(item="def exported(x)", container=outcome.source)


def test_fix_closed_world_annotates_exported() -> None:
    """Check that closed-world mode annotates exported callees."""
    root, index = _tree(
        sources={
            "core": "def exported(x):\n    print(x)\n",
            "user": (
                "from core import exported\n"
                "def run():\n"
                "    return exported(7)\n"
            ),
        },
        closed=True,
    )
    source: str = (root / "core.py").read_text(encoding="utf-8")
    outcome: FixResult = fix_source(
        source=source,
        filename="core.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            project=ProjectView(index=index, module="core"),
        ),
    )
    expect_in(item="x: int", container=outcome.source)


def _first_call(*, index: ProjectIndex, name: str) -> Call:
    """Return the first call of a scanned module.

    Args:
        index: The project index.
        name: Dotted module name.

    Returns:
        The first ``Call`` node found.

    """
    tree: Module = _parse_module(index=index, name=name)
    return next(n for n in walk(node=tree) if isinstance(n, Call))


def test_binding_decorated_returns_none() -> None:
    """Check that a decorated callee cannot be bound."""
    _root, index = _tree(
        sources={
            "core": ("def deco(fn): return fn\n@deco\ndef f(x): return x\n"),
            "user": "from core import f\ndef run():\n    return f(1)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    expect_is(
        actual=view.binding(call=_first_call(index=index, name="user")),
        expected=None,
    )


def test_binding_constructor() -> None:
    """Check that ``C(...)`` binds ``__init__`` parameters."""
    _root, index = _tree(
        sources={
            "core": "class C:\n    def __init__(self, count, name): ...\n",
            "user": "from core import C\ndef run():\n    return C(3, 'x')\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    bound: BoundCall = expect_not_none(
        value=view.binding(call=_first_call(index=index, name="user")),
    )
    names: tuple[str, ...] = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("self", "count", "name"))


def test_binding_constructor_method() -> None:
    """Check that ``C().m(...)`` binds the method's parameters."""
    _root, index = _tree(
        sources={
            "core": ("class C:\n    def m(self, value): return value\n"),
            "user": "from core import C\ndef run():\n    return C().m(1)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    bound: BoundCall = expect_not_none(
        value=view.binding(call=_first_call(index=index, name="user")),
    )
    names: tuple[str, ...] = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("self", "value"))


def test_binding_static_and_class_methods() -> None:
    """Check that ``C.sm``/``C.cm`` calls bind without a receiver."""
    _root, index = _tree(
        sources={
            "core": (
                "class C:\n"
                "    @staticmethod\n"
                "    def sm(value): return value\n"
                "    @classmethod\n"
                "    def cm(cls, other): return other\n"
            ),
            "user": (
                "from core import C\n"
                "def run():\n"
                "    C.sm(1)\n"
                "    return C.cm(2)\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="user")
    calls: list[Call] = [
        n
        for n in walk(node=_parse_module(index=index, name="user"))
        if isinstance(n, Call)
    ]
    bound: BoundCall = expect_not_none(value=view.binding(call=calls[0]))
    names: tuple[str, ...] = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("value",))
    bound = expect_not_none(value=view.binding(call=calls[1]))
    names = tuple(a.parameter.name for a in bound.arguments)
    expect_equal(actual=names, expected=("cls", "other"))


def test_sites_dataclass_constructor() -> None:
    """Check that a dataclass's generated ``__init__`` evidences fields."""
    _root, index = _tree(
        sources={
            "core": (
                "from dataclasses import dataclass\n"
                "@dataclass\n"
                "class _C:\n"
                "    count: int\n"
                "    name: str\n"
            ),
            "user": (
                "from core import _C\ndef run():\n    return _C(3, 'x')\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._C"),
    )
    site: CrossSite = sites["count"][0]
    expect_equal(actual=site.types, expected=("int",))


def test_sites_new_only_constructor() -> None:
    """Check that a ``__new__``-only class still binds calls."""
    _root, index = _tree(
        sources={
            "core": "class _C:\n    def __new__(cls, count): ...\n",
            "user": "from core import _C\ndef run():\n    return _C(3)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._C"),
    )
    site: CrossSite = sites["count"][0]
    expect_equal(actual=site.types, expected=("int",))


def test_sites_inherited_constructor_none() -> None:
    """Check that an inherited constructor yields ``None`` evidence."""
    _root, index = _tree(
        sources={
            "core": (
                "class Base:\n"
                "    def __init__(self, x): ...\n"
                "class _C(Base): ...\n"
            ),
            "user": "from core import _C\ndef run():\n    return _C(3)\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    expect_is(actual=view.sites(qualified="core._C"), expected=None)


def test_sites_decorated_class_none() -> None:
    """Check that a decorated class yields ``None`` evidence."""
    _root, index = _tree(
        sources={
            "core": ("def deco(cls): return cls\n@deco\nclass _C: ...\n"),
            "user": "from core import _C\ndef run():\n    return _C()\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    expect_is(actual=view.sites(qualified="core._C"), expected=None)


def test_sites_nondefinition_none() -> None:
    """Check that a non-definition name yields ``None`` evidence."""
    _root, index = _tree(
        sources={
            "core": "VALUE = 1\n",
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    expect_is(actual=view.sites(qualified="core.VALUE"), expected=None)


def test_sites_two_calls_share_env() -> None:
    """Check that two calls in one scope reuse the caller's env."""
    _root, index = _tree(
        sources={
            "core": "def _helper(x): return x\n",
            "user": (
                "from core import _helper\n"
                "def run():\n"
                "    _helper(1)\n"
                "    return _helper('s')\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._helper"),
    )
    expect_equal(actual=len(sites["x"]), expected=2)


def test_sites_top_level_call() -> None:
    """Check that a module-level call uses module constants as env."""
    _root, index = _tree(
        sources={
            "core": "def _helper(x): return x\n",
            "user": (
                "from core import _helper\n"
                "VALUE = 7\n"
                "RESULT = _helper(VALUE)\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._helper"),
    )
    site: CrossSite = sites["x"][0]
    expect_equal(actual=site.types, expected=("int",))


def test_sites_variadic_literal() -> None:
    """Check that ``*args`` with a literal expands to definite evidence."""
    _root, index = _tree(
        sources={
            "core": "def _helper(x, y): return x + y\n",
            "user": (
                "from core import _helper\n"
                "def run():\n"
                "    return _helper(*(1, 2))\n"
            ),
        },
    )
    view: ProjectView = ProjectView(index=index, module="core")
    sites: dict[str, tuple[CrossSite, ...]] = expect_not_none(
        value=view.sites(qualified="core._helper"),
    )
    site: CrossSite = sites["x"][0]
    expect_true(condition=site.definite)
