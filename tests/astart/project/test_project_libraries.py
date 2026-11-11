"""Verify external signature loading: typeshed, ``py.typed``, stubs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.project.libraries import (
    LibraryIndex,
    PackageRoot,
    find_library_roots,
)

from tests.support.expectations import (
    expect_equal,
    expect_is,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from astart.semantic.typing_contracts import CallableContract


def _write(*, path: Path, text: str) -> Path:
    """Write a file, creating parents.

    Args:
        path (Path): File path.
        text (str): Contents.

    Returns:
        Path: The path.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data=text, encoding="utf-8")
    return path


def test_find_roots_stub_only(*, tmp_path: Path) -> None:
    """Check that ``pkg-stubs`` packages are discovered.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(
        path=tmp_path / "libx-stubs" / "libx" / "__init__.pyi",
        text="""\
def connect(host: str) -> bool: ...
""",
    )
    roots: tuple[PackageRoot, ...] = find_library_roots(
        site_packages=(tmp_path,),
    )
    expect_equal(actual=len(roots), expected=1)
    expect_equal(actual=roots[0].package, expected="libx")
    expect_true(condition=roots[0].allow_source is False)


def test_find_roots_py_typed(*, tmp_path: Path) -> None:
    """Check that ``py.typed`` packages are discovered with sources on.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(path=tmp_path / "inlinelib" / "py.typed", text="")
    _ = _write(
        path=tmp_path / "inlinelib" / "__init__.pyi",
        text="""\
def compute(x: int) -> float: ...
""",
    )
    roots: tuple[PackageRoot, ...] = find_library_roots(
        site_packages=(tmp_path,),
    )
    expect_equal(actual=len(roots), expected=1)
    expect_equal(actual=roots[0].package, expected="inlinelib")
    expect_true(condition=roots[0].allow_source)


def test_find_roots_loose_stub(*, tmp_path: Path) -> None:
    """Check that lone ``foo.pyi`` files become module roots.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(
        path=tmp_path / "single.pyi",
        text="""\
def go() -> None: ...
""",
    )
    roots: tuple[PackageRoot, ...] = find_library_roots(
        site_packages=(tmp_path,),
    )
    expect_equal(actual=len(roots), expected=1)
    expect_is(actual=roots[0].module_file is not None, expected=True)


def test_find_roots_typeshed_stubs(*, tmp_path: Path) -> None:
    """Check that typeshed ``stubs/<dist>/<pkg>`` layouts resolve.

    Args:
        tmp_path (Path): Directory acting as the typeshed root.

    """
    _ = _write(
        path=tmp_path / "stubs" / "requests" / "requests" / "__init__.pyi",
        text="""\
def get(url: str) -> bytes: ...
""",
    )
    roots: tuple[PackageRoot, ...] = find_library_roots(typeshed=tmp_path)
    expect_equal(actual=len(roots), expected=1)
    expect_equal(actual=roots[0].package, expected="requests")


def test_stub_package_beats_inline(*, tmp_path: Path) -> None:
    """Check that a ``-stubs`` package shadows its ``py.typed`` twin.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(
        path=tmp_path / "libx-stubs" / "libx" / "__init__.pyi",
        text="""\
def connect(host: str, port: int) -> bool: ...
""",
    )
    _ = _write(path=tmp_path / "libx" / "py.typed", text="")
    _ = _write(
        path=tmp_path / "libx" / "__init__.pyi",
        text="""\
def connect(a: int) -> str: ...
""",
    )
    roots: tuple[PackageRoot, ...] = find_library_roots(
        site_packages=(tmp_path,),
    )
    index: LibraryIndex = LibraryIndex(roots=roots)
    contract: CallableContract = expect_not_none(
        value=index.contract(qualified_name="libx.connect"),
    )
    names: tuple[str, ...] = tuple(p.name for p in contract.parameters)
    expect_equal(actual=names, expected=("host", "port"))


def test_typeshed_stdlib_lookup(*, tmp_path: Path) -> None:
    """Check that ``stdlib/`` stubs resolve through the typeshed root.

    Args:
        tmp_path (Path): Directory acting as the typeshed root.

    """
    _ = _write(
        path=tmp_path / "stdlib" / "os.pyi",
        text="""\
def getcwd() -> str: ...
""",
    )
    index: LibraryIndex = LibraryIndex(typeshed=tmp_path)
    expect_not_none(
        value=index.contract(qualified_name="os.getcwd"),
    )


def test_pyi_beats_py(*, tmp_path: Path) -> None:
    """Check that ``.pyi`` files win over ``.py`` in one package.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(path=tmp_path / "pkg" / "py.typed", text="")
    _ = _write(
        path=tmp_path / "pkg" / "__init__.pyi",
        text="""\
def f(a: str) -> int: ...
""",
    )
    _ = _write(
        path=tmp_path / "pkg" / "__init__.py",
        text="""\
def f(different, names): ...
""",
    )
    index: LibraryIndex = LibraryIndex(
        roots=(
            PackageRoot(
                package="pkg",
                directory=tmp_path / "pkg",
                allow_source=True,
            ),
        ),
    )
    contract: CallableContract = expect_not_none(
        value=index.contract(qualified_name="pkg.f"),
    )
    expect_equal(actual=contract.parameters[0].name, expected="a")


def test_py_source_when_no_pyi(*, tmp_path: Path) -> None:
    """Check that annotated ``.py`` files serve a ``py.typed`` package.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(path=tmp_path / "pkg" / "py.typed", text="")
    _ = _write(
        path=tmp_path / "pkg" / "__init__.py",
        text="""\
def f(a: str, b: int) -> int: ...
""",
    )
    index: LibraryIndex = LibraryIndex(
        roots=(
            PackageRoot(
                package="pkg",
                directory=tmp_path / "pkg",
                allow_source=True,
            ),
        ),
    )
    contract: CallableContract = expect_not_none(
        value=index.contract(qualified_name="pkg.f"),
    )
    expect_equal(
        actual=tuple(p.name for p in contract.parameters),
        expected=("a", "b"),
    )


def test_submodule_stubs(*, tmp_path: Path) -> None:
    """Check that ``pkg.sub.name`` resolves inside submodules.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(path=tmp_path / "pkg-stubs" / "pkg" / "__init__.pyi", text="")
    _ = _write(
        path=tmp_path / "pkg-stubs" / "pkg" / "sub.pyi",
        text="""\
def deep(x: int) -> int: ...
""",
    )
    index: LibraryIndex = LibraryIndex(
        roots=find_library_roots(site_packages=(tmp_path,)),
    )
    expect_not_none(
        value=index.contract(qualified_name="pkg.sub.deep"),
    )


def test_method_signatures(*, tmp_path: Path) -> None:
    """Check that class members resolve qualified by their class.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(
        path=tmp_path / "libx-stubs" / "libx" / "__init__.pyi",
        text="""\
class Session:
    def send(self, request: bytes) -> bytes: ...
""",
    )
    index: LibraryIndex = LibraryIndex(
        roots=find_library_roots(site_packages=(tmp_path,)),
    )
    expect_not_none(
        value=index.contract(qualified_name="libx.Session.send"),
    )


def test_unknown_returns_empty(*, tmp_path: Path) -> None:
    """Check that absent names return no contract, not an error.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(
        path=tmp_path / "libx-stubs" / "libx" / "__init__.pyi",
        text="""\
def connect(host: str) -> bool: ...
""",
    )
    index: LibraryIndex = LibraryIndex(
        roots=find_library_roots(site_packages=(tmp_path,)),
    )
    expect_is(
        actual=index.contract(qualified_name="libx.absent"),
        expected=None,
    )
    expect_is(
        actual=index.contract(qualified_name="other.thing"),
        expected=None,
    )


def test_oversized_stub_skipped(*, tmp_path: Path) -> None:
    """Check that stubs over the size cap are ignored.

    Args:
        tmp_path (Path): Directory acting as site-packages.

    """
    _ = _write(path=tmp_path / "big.pyi", text="x" * 1100000)
    index: LibraryIndex = LibraryIndex(
        roots=(
            PackageRoot(
                package="big",
                module_file=tmp_path / "big.pyi",
            ),
        ),
    )
    expect_is(
        actual=index.contract(qualified_name="big.f"),
        expected=None,
    )
