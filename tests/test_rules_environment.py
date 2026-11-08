"""The checker environment is detected from where the file lives."""

from __future__ import annotations

from os import pathsep
from shutil import which
from typing import TYPE_CHECKING

import pytest
from astart.rules.checker import PyrightChecker, detect_checker
from astart.rules.environment import (
    Environment,
    absolutize_relative_imports,
    detect_environment,
)

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


def _write(*, path: Path, text: str = "") -> Path:
    """Write ``text`` to ``path``, creating parent directories.

    Args:
        path: File to write.
        text: File contents.

    Returns:
        The written path.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(data=text, encoding="utf-8")
    return path


def test_a_package_module_reports_its_package_and_source_root(
    *,
    tmp_path: Path,
) -> None:
    """Check that ``__init__.py`` files define the package chain.

    Args:
        tmp_path: pytest temporary directory.

    """
    _ = _write(path=tmp_path / "pkg" / "__init__.py")
    _ = _write(path=tmp_path / "pkg" / "sub" / "__init__.py")
    module: Path = _write(path=tmp_path / "pkg" / "sub" / "m.py")
    found: Environment = detect_environment(file=module, project=tmp_path)
    expect_equal(actual=found.package, expected=("pkg", "sub"))
    expect_in(item=tmp_path, container=found.roots)


def test_a_src_layout_adds_the_src_directory(*, tmp_path: Path) -> None:
    """Check that ``src/`` next to the project root is a source root.

    Args:
        tmp_path: pytest temporary directory.

    """
    _ = _write(path=tmp_path / "src" / "pkg" / "__init__.py")
    module: Path = _write(path=tmp_path / "src" / "pkg" / "m.py")
    found: Environment = detect_environment(file=module, project=tmp_path)
    expect_equal(actual=found.package, expected=("pkg",))
    expect_in(item=tmp_path / "src", container=found.roots)


def test_a_loose_script_uses_its_own_directory(*, tmp_path: Path) -> None:
    """Check that a module outside any package sees its siblings.

    Args:
        tmp_path: pytest temporary directory.

    """
    module: Path = _write(path=tmp_path / "scripts" / "run.py")
    found: Environment = detect_environment(file=module, project=tmp_path)
    expect_equal(actual=found.package, expected=())
    expect_in(item=tmp_path / "scripts", container=found.roots)


def test_relative_imports_become_absolute() -> None:
    """Check every relative form is rewritten against the package."""
    source: str = (
        "from . import a\n"
        "from .b import c\n"
        "from .. import d\n"
        "from ..e.f import g\n"
    )
    out: str = absolutize_relative_imports(
        source=source,
        package=("top", "sub"),
    )
    expect_in(item="from top.sub import a", container=out)
    expect_in(item="from top.sub.b import c", container=out)
    expect_in(item="from top import d", container=out)
    expect_in(item="from top.e.f import g", container=out)


def test_imports_that_escape_the_package_are_left_alone() -> None:
    """Check that ``from ... import x`` above the top stays as written."""
    source: str = "from ... import x\n"
    out: str = absolutize_relative_imports(source=source, package=("top",))
    expect_in(item="from ... import x", container=out)


def test_unparsable_text_is_returned_unchanged() -> None:
    """Check that broken source never raises."""
    source: str = "def (:\n"
    expect_equal(
        actual=absolutize_relative_imports(source=source, package=("p",)),
        expected=source,
    )


@pytest.mark.skipif(
    which(cmd="basedpyright") is None and which(cmd="pyright") is None,
    reason="needs pyright",
)
def test_the_checker_resolves_relative_imports_in_a_package(
    *,
    tmp_path: Path,
) -> None:
    """Check that ``from .helper import make`` is understood by the checker.

    Args:
        tmp_path: pytest temporary directory.

    """
    _ = _write(path=tmp_path / "pkg" / "__init__.py")
    _ = _write(
        path=tmp_path / "pkg" / "helper.py",
        text="def make() -> str:\n    return 'x'\n",
    )
    module: Path = _write(path=tmp_path / "pkg" / "m.py")
    checker: PyrightChecker = PyrightChecker(
        command=expect_not_none(value=detect_checker()),
        root=tmp_path,
    )
    name: str = str(object=module)
    expect_equal(
        actual=checker.regresses(
            filename=name,
            before="x = 1\n",
            after="from .helper import make\nx: str = make()\n",
        ),
        expected=False,
    )
    expect_true(
        condition=checker.regresses(
            filename=name,
            before="x = 1\n",
            after="from .helper import make\nx: int = make()\n",
        ),
    )


def test_explicit_source_roots_come_first(*, tmp_path: Path) -> None:
    """Check that user-given roots precede detected ones.

    Args:
        tmp_path: pytest temporary directory.

    """
    module: Path = _write(path=tmp_path / "app" / "m.py")
    extra: Path = tmp_path / "vendor"
    extra.mkdir()
    found: Environment = detect_environment(
        file=module,
        project=tmp_path,
        source_roots=(extra,),
    )
    expect_equal(actual=found.roots[0], expected=extra.resolve())


def test_pythonpath_entries_are_source_roots(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that ``PYTHONPATH`` directories join the roots.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    libs: Path = tmp_path / "libs"
    libs.mkdir()
    monkeypatch.setenv(
        name="PYTHONPATH",
        value=f"{libs}{pathsep}{tmp_path / 'missing'}",
    )
    module: Path = _write(path=tmp_path / "app" / "m.py")
    found: Environment = detect_environment(file=module, project=tmp_path)
    expect_in(item=libs.resolve(), container=found.roots)
    expect_not_in(item=(tmp_path / "missing").resolve(), container=found.roots)
