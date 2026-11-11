"""Verify project builds: naming, collisions and skipped files."""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING

from astart.project.builder import BuildResult, build_index

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from astart.project.scan import ModuleScan


def test_build_index_scans_package() -> None:
    """Check that files become named module scans."""
    root: Path = Path(mkdtemp())
    package: Path = root / "pkg"
    package.mkdir()
    init: Path = package / "__init__.py"
    init.write_text(data="", encoding="utf-8")
    module: Path = package / "mod.py"
    module.write_text(
        data="""\
X = 1
""",
        encoding="utf-8",
    )
    result: BuildResult = build_index(files=(init, module))
    expect_in(item="pkg", container=result.index.scans)
    expect_in(item="pkg.mod", container=result.index.scans)
    expect_equal(actual=result.skipped, expected=())
    expect_equal(actual=result.collisions, expected=())


def test_build_index_skips_unnamed() -> None:
    """Check that a file outside any package root is skipped."""
    root: Path = Path(mkdtemp())
    bad: Path = root / "bad-name.py"
    bad.write_text(
        data="""\
X = 1
""",
        encoding="utf-8",
    )
    result: BuildResult = build_index(
        files=(bad,),
        source_roots=(root,),
    )
    expect_equal(actual=len(result.skipped), expected=1)
    expect_equal(actual=result.index.scans, expected={})


def test_build_index_collision_first_wins() -> None:
    """Check that two files claiming one name keep the first sorted."""
    root: Path = Path(mkdtemp())
    package: Path = root / "pkg"
    package.mkdir()
    init_file: Path = package / "__init__.py"
    init_file.write_text(data="", encoding="utf-8")
    module_file: Path = package / "mod.py"
    module_file.write_text(
        data="""\
X = 1
""",
        encoding="utf-8",
    )
    package_dir: Path = package / "mod"
    package_dir.mkdir()
    sub_init: Path = package_dir / "__init__.py"
    sub_init.write_text(
        data="""\
Y = 2
""",
        encoding="utf-8",
    )
    result: BuildResult = build_index(files=(module_file, sub_init))
    expect_in(item="pkg.mod", container=result.collisions)
    scan: ModuleScan | None = result.index.module_scan(module="pkg.mod")
    expect_true(condition=scan is not None)
    if scan is not None:
        expect_equal(actual=scan.path, expected=sub_init.resolve())


def test_build_index_skips_unreadable(*, tmp_path: Path) -> None:
    """Check that an unreadable file is skipped with a reason.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    blocked: Path = tmp_path / "blocked.py"
    blocked.write_text(
        data="""\
X = 1
""",
        encoding="utf-8",
    )
    blocked.chmod(mode=0)
    try:
        result: BuildResult = build_index(files=(blocked,))
    finally:
        blocked.chmod(mode=0o644)
    expect_equal(actual=len(result.skipped), expected=1)
    expect_in(item="unreadable", container=result.skipped[0][1])


def test_build_index_skips_unparseable() -> None:
    """Check that a syntax-error file is skipped with a reason."""
    root: Path = Path(mkdtemp())
    broken: Path = root / "broken.py"
    broken.write_text(
        data="""\
def broken(:
""",
        encoding="utf-8",
    )
    result: BuildResult = build_index(files=(broken,))
    expect_equal(actual=len(result.skipped), expected=1)
    expect_in(item="unparseable", container=result.skipped[0][1])
