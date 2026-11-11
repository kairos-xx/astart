"""The stub reader: locate, evaluate, parse, resolve, state returns."""

from __future__ import annotations

from ast import expr, parse, unparse
from textwrap import dedent
from typing import TYPE_CHECKING, Final, cast, final

import pytest
from astart import parse as parse_module
from astart.rules.hints import escaped_function_names
from astart.rules.negotiation.run import Verdicts, negotiate_module
from astart.stubs import (
    CallArguments,
    Resolver,
    Target,
    bundled_typeshed,
    class_typevars,
    evaluate,
    find_typeshed,
    function_return,
    method_return,
    module_available,
    parse_stub,
    parse_versions,
    receiver_parts,
    select_overload,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from astart.source.ast import CommentedModule
    from astart.stubs.parser import ImportedName, StubModule
    from astart.stubs.resolver import Resolved


@final
class Constants:
    """Group module-level constants.

    Attributes:
        files (Final[dict[str, str]]): Grouped module constant.

    """

    files: Final[dict[str, str]] = {
        "stdlib/VERSIONS": "builtins: 3.0-\nos: 3.0-\nposixpath: 3.0-\n"
        "newmod: 3.12-\noldmod: 3.0-3.9\nre: 3.0-\nmymod: 3.0-\n",
        "stdlib/builtins.pyi": "def len(obj) -> int: ...\n"
        "class str:\n    def upper(self) -> str: ...\n",
        "stdlib/os/__init__.pyi": dedent(
            text="""\
        import sys
        from typing import TypeVar, overload
        from . import path as _path

        T = TypeVar("T")
        path = _path

        def getcwd() -> str: ...
        def generic(x: T) -> T: ...
        def many() -> list[str]: ...
        def other() -> Other: ...

        if sys.platform == "win32":
            def startfile(name: str) -> None: ...
        else:
            def fork() -> int: ...

        if sys.version_info >= (3, 12):
            def modern() -> bool: ...
        else:
            def modern() -> int: ...

        @overload
        def getenv(key: str) -> str | None: ...
        @overload
        def getenv(key: str, default: str) -> str: ...
        """,
        ),
        "stdlib/os/path.pyi": """\
from posixpath import *
""",
        "stdlib/posixpath.pyi": dedent(
            text="""\
        __all__ = ["exists", "join"]
        def exists(path: str) -> bool: ...
        def join(a: str, b: str) -> str: ...
        def _hidden() -> int: ...
        def unlisted() -> int: ...
        """,
        ),
        "stdlib/newmod.pyi": """\
def f() -> int: ...
""",
        "stdlib/oldmod.pyi": """\
def f() -> int: ...
""",
        "stdlib/re.pyi": dedent(
            text="""\
        from typing import Generic, TypeVar, overload

        AnyStr = TypeVar("AnyStr")

        class Match(Generic[AnyStr]):
            @overload
            def group(self, group: int = 0) -> AnyStr: ...
            @overload
            def group(self, group: int) -> AnyStr | None: ...

        def match(pattern: str, string: str) -> Match[str] | None: ...
        """,
        ),
        "stdlib/mymod.pyi": dedent(
            text="""\
        from typing import Generic, TypeVar

        T = TypeVar("T")

        class Box(Generic[T]):
            def get(self) -> T: ...
            def put(self, value: T) -> None: ...
        """,
        ),
        "stubs/types-foo/foo/__init__.pyi": """\
def bar() -> bytes: ...
""",
        "stubs/types-foo/METADATA.toml": """\
version = '1.0'
""",
    }


@pytest.fixture
def typeshed(tmp_path: Path) -> Path:
    """Write a small fake typeshed.

    Args:
        tmp_path (Path): Pytest's temporary directory.

    Returns:
        Path: Its root.

    """
    for name, text in Constants.files.items():
        path: Path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(data=text, encoding="utf-8")
    return tmp_path


def _resolver(*, root: Path, version: tuple[int, int] = (3, 13)) -> Resolver:
    """Build a resolver over the fake typeshed.

    Args:
        root (Path): The typeshed root.
        version (tuple[int, int]): Python version to read the stubs for.

    Returns:
        Resolver: The resolver.

    """
    return Resolver(
        typeshed=root,
        target=Target(version=version, platform="darwin"),
    )


def test_a_typeshed_is_found_by_path_and_by_environment(
    typeshed: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that an explicit path and ``ASTART_TYPESHED`` are honoured.

    Args:
        typeshed (Path): Root of the fake typeshed.
        tmp_path_factory (pytest.TempPathFactory): Factory for an empty
            directory.
        monkeypatch (pytest.MonkeyPatch): Fixture setting environment
            variables.

    """
    expect_equal(actual=find_typeshed(explicit=typeshed), expected=typeshed)
    empty: Path = tmp_path_factory.mktemp(basename="empty")
    monkeypatch.setenv(name="ASTART_TYPESHED", value=str(object=typeshed))
    expect_equal(actual=find_typeshed(explicit=empty), expected=typeshed)


def test_find_typeshed_falls_back_to_the_bundled_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without overrides the shipped typeshed is the answer.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture clearing the environment
            override.

    """
    monkeypatch.delenv(name="ASTART_TYPESHED", raising=False)
    bundled: Path | None = bundled_typeshed()
    bundled = expect_not_none(value=bundled)
    expect_equal(actual=find_typeshed(), expected=bundled)
    expect_true(condition=bundled.joinpath("stdlib", "VERSIONS").is_file())
    expect_true(
        condition=bundled.joinpath("stubs").is_dir(),
    )


def test_versions_gate_modules_by_python_version() -> None:
    """Check ``VERSIONS`` ranges, open ends and inherited submodules."""
    table: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = (
        parse_versions(
            text="""\
a: 3.9-3.11
b: 3.12-
# note
b.c: 3.13-
""",
        )
    )
    expect_true(
        condition=module_available(table=table, module="a", version=(3, 10)),
    )
    expect_false(
        condition=module_available(table=table, module="a", version=(3, 12)),
    )
    expect_true(
        condition=module_available(table=table, module="b", version=(3, 14)),
    )
    expect_false(
        condition=module_available(table=table, module="b.c", version=(3, 12)),
    )
    expect_true(
        condition=module_available(table=table, module="b.x", version=(3, 12)),
    )
    expect_true(
        condition=module_available(table=table, module="zz", version=(3, 1)),
    )


@pytest.mark.parametrize(
    ("test", "expected"),
    [
        ("sys.version_info >= (3, 12)", True),
        ("sys.version_info < (3, 12)", False),
        ("sys.version_info[0] == 3", True),
        ("sys.platform == 'win32'", False),
        ("sys.platform != 'win32'", True),
        ("sys.platform.startswith('dar')", True),
        ("not sys.platform == 'win32'", True),
        ("sys.version_info >= (3, 14) or sys.platform == 'darwin'", True),
        ("sys.version_info >= (3, 14) and mystery", False),
        ("sys.version_info >= (3, 1) and mystery", None),
        ("sys.version_info[0] == 'x'", None),
        ("sys.platform == 3", None),
        ("TYPE_CHECKING", True),
        ("mystery()", None),
    ],
)
def test_conditions(*, test: str, expected: bool | None) -> None:
    """Check that stub conditions are decided for a target.

    Args:
        test (str): Condition source.
        expected (bool | None): Decision, or ``None`` when it depends on the
            unknown.

    """
    target: Target = Target(version=(3, 13), platform="darwin")
    node: expr = parse(source=test, mode="eval").body
    expect_equal(actual=evaluate(test=node, target=target), expected=expected)


def test_the_parser_follows_branches_overloads_and_exports() -> None:
    """Check branch selection, overload groups, ``__all__`` and re-exports."""
    module: StubModule = parse_stub(
        source=Constants.files["stdlib/os/__init__.pyi"],
        module="os",
        package=True,
        target=Target(version=(3, 13), platform="darwin"),
    )
    expect_true(condition="fork" in module.names)
    expect_false(condition="startfile" in module.names)
    expect_true(condition=module.names["getenv"].overloaded)
    expect_equal(actual=len(module.names["getenv"].nodes), expected=2)
    expect_equal(actual=module.typevars, expected={"T"})
    expect_false(condition=module.names["_path"].exported)
    expect_equal(actual=module.names["path"].alias_of, expected="_path")
    older: StubModule = parse_stub(
        source=Constants.files["stdlib/os/__init__.pyi"],
        module="os",
        package=True,
        target=Target(version=(3, 11), platform="win32"),
    )
    expect_true(condition="startfile" in older.names)
    expect_false(condition="fork" in older.names)


def test_underscore_and_dunder_all_decide_what_is_public() -> None:
    """Check the export rules for plain names and ``__all__``."""
    plain: StubModule = parse_stub(
        source="""\
import a
import b as b
from c import d
x = 1
_y = 2
""",
        module="m",
        package=False,
        target=Target(),
    )
    expect_false(condition=plain.names["a"].exported)
    expect_true(condition=plain.names["b"].exported)
    expect_false(condition=plain.names["d"].exported)
    expect_true(condition=plain.names["x"].exported)
    expect_false(condition=plain.names["_y"].exported)
    listed: StubModule = parse_stub(
        source="""\
__all__ = ['x']
__all__ += ['y']
x = 1
y = 2
z = 3
""",
        module="m",
        package=False,
        target=Target(),
    )
    expect_equal(actual=listed.dunder_all, expected=["x", "y"])
    expect_false(condition=listed.names["z"].exported)


def test_relative_imports_are_made_absolute() -> None:
    """Check ``from . import x`` in a package and in a plain module."""
    package: StubModule = parse_stub(
        source="""\
from . import path
from .. import up
""",
        module="a.b",
        package=True,
        target=Target(),
    )
    path_imported: ImportedName | None = package.names["path"].imported
    if path_imported:
        expect_equal(
            actual=path_imported.module,
            expected="a.b",
        )
    up_imported: ImportedName | None = package.names["up"].imported
    if up_imported:
        expect_equal(actual=up_imported.module, expected="a")
    plain: StubModule = parse_stub(
        source="""\
from . import sib
""",
        module="a.b",
        package=False,
        target=Target(),
    )
    sib_imported: ImportedName | None = plain.names["sib"].imported
    if sib_imported:
        expect_equal(actual=sib_imported.module, expected="a")


def test_resolution_follows_aliases_and_star_imports(typeshed: Path) -> None:
    """Check ``os.path.exists`` through an alias and a star import.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    resolver: Resolver = _resolver(root=typeshed)
    found: Resolved | None = resolver.resolve(qualified="os.path.exists")
    expect_equal(actual=found.name.name if found else None, expected="exists")
    expect_equal(
        actual=found.module.name if found else None,
        expected="posixpath",
    )
    expect_equal(
        actual=resolver.resolve(qualified="os.path._hidden"),
        expected=None,
    )
    expect_equal(
        actual=resolver.resolve(qualified="os.missing"),
        expected=None,
    )


def test_modules_exist_only_in_their_python_versions(typeshed: Path) -> None:
    """Check that ``VERSIONS`` hides modules the target does not have.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    modern: Resolver = _resolver(root=typeshed, version=(3, 13))
    old: Resolver = _resolver(root=typeshed, version=(3, 9))
    expect_true(condition=modern.resolve(qualified="newmod.f") is not None)
    expect_true(condition=modern.resolve(qualified="oldmod.f") is None)
    expect_true(condition=old.resolve(qualified="newmod.f") is None)
    expect_true(condition=old.resolve(qualified="oldmod.f") is not None)


def test_third_party_stub_distributions_are_found(typeshed: Path) -> None:
    """Check ``stubs/<dist>/<package>`` lookup.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    found: Resolved | None = _resolver(root=typeshed).resolve(
        qualified="foo.bar",
    )
    expect_equal(
        actual=function_return(resolved=found) if found else None,
        expected="bytes",
    )


def test_only_certain_return_types_are_stated(typeshed: Path) -> None:
    """Check overloads, type variables and imports are refused.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    resolver: Resolver = _resolver(root=typeshed)

    def returns(name: str) -> str | None:
        """Resolve a qualified name and state its return type.

        Args:
            name (str): Qualified function name.

        Returns:
            str | None: The stated return type, or ``None``.

        """
        found: Resolved | None = resolver.resolve(qualified=name)
        return None if found is None else function_return(resolved=found)

    expect_equal(actual=returns(name="os.getcwd"), expected="str")
    expect_equal(actual=returns(name="os.path.exists"), expected="bool")
    expect_equal(actual=returns(name="os.many"), expected="list[str]")
    expect_equal(actual=returns(name="builtins.len"), expected="int")
    expect_equal(actual=returns(name="os.modern"), expected="bool")
    expect_equal(actual=returns(name="os.getenv"), expected=None)
    expect_equal(actual=returns(name="os.generic"), expected=None)
    expect_equal(actual=returns(name="os.other"), expected=None)
    expect_equal(actual=returns(name="builtins.str.upper"), expected="str")
    older: Resolver = _resolver(root=typeshed, version=(3, 11))
    found: Resolved | None = older.resolve(qualified="os.modern")
    expect_equal(
        actual=function_return(resolved=found) if found else None,
        expected="int",
    )


def test_import_cycles_do_not_loop(tmp_path: Path) -> None:
    """Check that a name imported in a circle resolves to nothing.

    Args:
        tmp_path (Path): Directory the stub files are written to.

    """
    files: dict[str, str] = {
        "stdlib/VERSIONS": """\
a: 3.0-
b: 3.0-
""",
        "stdlib/a.pyi": """\
from b import x as x
""",
        "stdlib/b.pyi": """\
from a import x as x
""",
    }
    for name, text in files.items():
        path: Path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(data=text, encoding="utf-8")
    expect_equal(
        actual=_resolver(root=tmp_path).resolve(qualified="a.x"),
        expected=None,
    )


def test_negotiation_types_a_library_call_from_the_stub(
    typeshed: Path,
) -> None:
    """Check that ``os.getcwd()`` types the caller through the resolver.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    module: CommentedModule = parse_module(
        source=dedent(
            text="""\
            import os

            def here():
                d = os.getcwd()
                return d

            def either(key):
                return os.getenv(key)
            """,
        ),
    )
    found: Verdicts = negotiate_module(
        module=module,
        corroboration={},
        escaped=escaped_function_names(module=module),
        library=_resolver(root=typeshed),
    )
    expect_equal(actual=found.accepted["here->"], expected="str")
    expect_false(condition="either->" in found.accepted)


def test_overloads_are_selected_by_argument_types(typeshed: Path) -> None:
    """Check ``select_overload`` picks the fitting signature.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    resolver: Resolver = _resolver(root=typeshed)
    found: Resolved | None = resolver.resolve(qualified="os.getenv")
    expect_true(condition=found is not None)
    found = cast(typ="Resolved", val=found)

    def picked(*, positional: list[str | None]) -> str | None:
        """Select with positional argument types only.

        Args:
            positional (list[str | None]): Argument types, ``None`` when
                unknown.

        Returns:
            str | None: The selected return type.

        """
        return select_overload(
            resolved=found,
            positional=positional,
            keywords={},
        )

    expect_equal(actual=picked(positional=["str"]), expected="str | None")
    expect_equal(
        actual=picked(positional=["str", "str"]),
        expected="str",
    )
    expect_equal(actual=picked(positional=[None]), expected=None)
    expect_equal(actual=picked(positional=["int"]), expected=None)


def test_receiver_parts_and_class_typevars(typeshed: Path) -> None:
    """Check receiver types split into head and bound arguments.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    head, args = receiver_parts(source="mymod.Box[int]") or (None, None)
    expect_equal(actual=head, expected="mymod.Box")
    expect_equal(
        actual=None if args is None else [unparse(ast_obj=a) for a in args],
        expected=["int"],
    )
    expect_equal(actual=receiver_parts(source="int | None"), expected=None)
    parts: tuple[str, list[expr]] | None = receiver_parts(
        source="tuple[int, ...]",
    )
    expect_equal(
        actual=None if parts is None else parts[0],
        expected="tuple",
    )

    resolver: Resolver = _resolver(root=typeshed)
    box: Resolved | None = resolver.resolve(qualified="mymod.Box")
    expect_true(condition=box is not None)
    box = cast(typ="Resolved", val=box)
    expect_equal(
        actual=class_typevars(owner=box.name),
        expected=["T"],
    )


def test_method_return_binds_class_typevars(typeshed: Path) -> None:
    """Check ``Box[int].get()`` states ``int`` through the stub.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    resolver: Resolver = _resolver(root=typeshed)
    method: Resolved | None = resolver.resolve_method(
        class_name="mymod.Box",
        method="get",
    )
    expect_true(condition=method is not None)
    method = cast(typ="Resolved", val=method)
    arg: expr = parse(source="int", mode="eval").body
    expect_equal(
        actual=method_return(
            resolved=method,
            receiver=[arg],
            call=CallArguments(),
        ),
        expected="int",
    )
    expect_equal(
        actual=method_return(
            resolved=method,
            receiver=[],
            call=CallArguments(),
        ),
        expected=None,
    )


def test_negotiation_types_optional_and_method_calls(typeshed: Path) -> None:
    """Check lookups stay optional and narrowed methods type.

    Args:
        typeshed (Path): Root of the fake typeshed.

    """
    module: CommentedModule = parse_module(
        source=dedent(
            text="""\
            import os
            import re

            def opt(key: str):
                return os.getenv(key)

            def optd(key: str):
                return os.getenv(key, "d")

            def find(pattern: str, text: str):
                m = re.match(pattern, text)
                if m:
                    return m.group()
                return None

            def find_raw(pattern: str, text: str):
                return re.match(pattern, text)
            """,
        ),
    )
    found: Verdicts = negotiate_module(
        module=module,
        corroboration={},
        escaped=escaped_function_names(module=module),
        library=_resolver(root=typeshed),
    )
    expect_equal(actual=found.accepted["opt->"], expected="str | None")
    expect_equal(actual=found.accepted["optd->"], expected="str")
    expect_equal(actual=found.accepted["find->"], expected="str | None")
    expect_equal(
        actual=found.accepted["find_raw->"],
        expected="Match[str] | None",
    )
