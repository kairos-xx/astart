"""Verify filesystem-to-module-name mapping."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.project.naming import module_name, package_of

from tests.support.expectations import expect_equal, expect_is

if TYPE_CHECKING:
    from pathlib import Path


def _tree(*, tmp_path: Path, paths: tuple[str, ...]) -> Path:
    """Create a directory tree of empty files.

    Args:
        tmp_path (Path): Root of the tree.
        paths (tuple[str, ...]): Relative file paths to create.

    Returns:
        Path: The root.

    """
    for relative in paths:
        file: Path = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(data="", encoding="utf-8")
    return tmp_path


def test_module_name_package_chain(*, tmp_path: Path) -> None:
    """Check that ``__init__`` markers build the dotted name.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(
        tmp_path=tmp_path,
        paths=("pkg/__init__.py", "pkg/sub/__init__.py", "pkg/sub/mod.py"),
    )
    expect_equal(
        actual=module_name(path=root / "pkg" / "sub" / "mod.py"),
        expected="pkg.sub.mod",
    )


def test_module_name_init_is_package(*, tmp_path: Path) -> None:
    """Check that ``__init__.py`` names its directory, not ``__init__``.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(tmp_path=tmp_path, paths=("pkg/__init__.py",))
    expect_equal(
        actual=module_name(path=root / "pkg" / "__init__.py"),
        expected="pkg",
    )


def test_module_name_source_root_beats_chain(*, tmp_path: Path) -> None:
    """Check that an explicit source root anchors the name.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(
        tmp_path=tmp_path,
        paths=("src/pkg/__init__.py", "src/pkg/mod.py"),
    )
    expect_equal(
        actual=module_name(
            path=root / "src" / "pkg" / "mod.py",
            source_roots=(root / "src",),
        ),
        expected="pkg.mod",
    )


def test_module_name_root_without_init(*, tmp_path: Path) -> None:
    """Check that a source root names modules with no ``__init__``.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(tmp_path=tmp_path, paths=("src/plain.py",))
    expect_equal(
        actual=module_name(
            path=root / "src" / "plain.py",
            source_roots=(root / "src",),
        ),
        expected="plain",
    )


def test_module_name_bare_file(*, tmp_path: Path) -> None:
    """Check that a lone file names itself.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(tmp_path=tmp_path, paths=("top.py",))
    expect_equal(
        actual=module_name(path=root / "top.py"),
        expected="top",
    )


def test_module_name_outside_root_falls_back(*, tmp_path: Path) -> None:
    """Check that a file outside every root uses the package chain.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(
        tmp_path=tmp_path,
        paths=("pkg/__init__.py", "pkg/mod.py", "other/x.py"),
    )
    expect_equal(
        actual=module_name(
            path=root / "pkg" / "mod.py",
            source_roots=(root / "other",),
        ),
        expected="pkg.mod",
    )


def test_module_name_invalid_identifier(*, tmp_path: Path) -> None:
    """Check that a non-identifier stem resolves to ``None``.

    Args:
        tmp_path (Path): Directory holding the tree.

    """
    root: Path = _tree(tmp_path=tmp_path, paths=("src/my-mod.py",))
    expect_is(
        actual=module_name(
            path=root / "src" / "my-mod.py",
            source_roots=(root / "src",),
        ),
        expected=None,
    )


def test_package_of_member() -> None:
    """Check that a plain module's package is its parent."""
    expect_equal(
        actual=package_of(name="pkg.sub.mod", is_package=False),
        expected="pkg.sub",
    )


def test_package_of_package() -> None:
    """Check that a package resolves relatives against itself."""
    expect_equal(
        actual=package_of(name="pkg.sub", is_package=True),
        expected="pkg.sub",
    )


def test_package_of_top_level() -> None:
    """Check that a top-level module has no package."""
    expect_equal(
        actual=package_of(name="mod", is_package=False),
        expected="",
    )
