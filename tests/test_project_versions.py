"""Verify Python-version target resolution and syntax gates."""

from __future__ import annotations

from sys import version_info
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.project.versions import (
    PythonTarget,
    find_pyproject,
    parse_version,
    requires_python_floor,
    resolve_target,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_version() -> None:
    """Check that ``major.minor`` strings parse."""
    expect_equal(actual=parse_version(text="3.10"), expected=(3, 10))
    expect_equal(actual=parse_version(text=" 3.9 "), expected=(3, 9))
    expect_equal(actual=parse_version(text="3.11.4"), expected=(3, 11))
    expect_is(actual=parse_version(text="3"), expected=None)
    expect_is(actual=parse_version(text="3.x"), expected=None)
    expect_is(actual=parse_version(text=""), expected=None)


def test_requires_python_floor_simple(*, tmp_path: Path) -> None:
    """Check that a plain ``>=`` specifier yields its floor.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data=dedent(
            text="""\
            [project]
            name = "demo"
            requires-python = ">=3.9"
            """,
        ),
        encoding="utf-8",
    )
    expect_equal(
        actual=requires_python_floor(pyproject=pyproject),
        expected=(3, 9),
    )


def test_requires_python_floor_compound(*, tmp_path: Path) -> None:
    """Check that compound specifiers take the lowest bound.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data=dedent(
            text="""\
            [project]
            requires-python = ">=3.9, !=3.10.*, <4"
            """,
        ),
        encoding="utf-8",
    )
    expect_equal(
        actual=requires_python_floor(pyproject=pyproject),
        expected=(3, 9),
    )


def test_requires_python_floor_missing(*, tmp_path: Path) -> None:
    """Check that absent keys and files resolve to ``None``.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(data="[project]\nname = 'x'\n", encoding="utf-8")
    expect_is(actual=requires_python_floor(pyproject=pyproject), expected=None)
    expect_is(
        actual=requires_python_floor(pyproject=tmp_path / "none.toml"),
        expected=None,
    )


def test_requires_python_floor_malformed(*, tmp_path: Path) -> None:
    """Check that malformed TOML resolves to ``None``.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(data="not [valid toml", encoding="utf-8")
    expect_is(actual=requires_python_floor(pyproject=pyproject), expected=None)


def test_find_pyproject_nearest(*, tmp_path: Path) -> None:
    """Check that the nearest ancestor ``pyproject.toml`` wins.

    Args:
        tmp_path: Directory holding the tree.

    """
    outer: Path = tmp_path / "pyproject.toml"
    outer.write_text(
        data="[project]\nrequires-python = '>=3.9'\n",
        encoding="utf-8",
    )
    inner_dir: Path = tmp_path / "pkg"
    inner_dir.mkdir()
    target: Path = inner_dir / "mod.py"
    target.write_text(data="X = 1\n", encoding="utf-8")
    expect_equal(
        actual=find_pyproject(paths=(target,)),
        expected=outer.resolve(),
    )


def test_resolve_target_configured_wins(*, tmp_path: Path) -> None:
    """Check that an explicit target beats ``requires-python``.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data="[project]\nrequires-python = '>=3.9'\n",
        encoding="utf-8",
    )
    target: PythonTarget = resolve_target(
        configured="3.12",
        pyproject=pyproject,
    )
    expect_equal(actual=target.floor, expected=(3, 12))


def test_resolve_target_pyproject_fallback(*, tmp_path: Path) -> None:
    """Check that ``requires-python`` is used without a configured one.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data="[project]\nrequires-python = '>=3.9'\n",
        encoding="utf-8",
    )
    target: PythonTarget = resolve_target(pyproject=pyproject)
    expect_equal(actual=target.floor, expected=(3, 9))


def test_resolve_target_interpreter_fallback(*, tmp_path: Path) -> None:
    """Check that the interpreter version is the last resort.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(data="[project]\nname = 'x'\n", encoding="utf-8")
    target: PythonTarget = resolve_target(pyproject=pyproject)
    expect_equal(
        actual=target.floor,
        expected=(version_info.major, version_info.minor),
    )


def test_resolve_target_bad_configured(*, tmp_path: Path) -> None:
    """Check that an unparseable configured target falls through.

    Args:
        tmp_path: Directory holding the pyproject.

    """
    pyproject: Path = tmp_path / "pyproject.toml"
    pyproject.write_text(
        data="[project]\nrequires-python = '>=3.9'\n",
        encoding="utf-8",
    )
    target: PythonTarget = resolve_target(
        configured="banana",
        pyproject=pyproject,
    )
    expect_equal(actual=target.floor, expected=(3, 9))


def test_target_syntax_gates() -> None:
    """Check that capability flags follow the floor."""
    low: PythonTarget = PythonTarget(floor=(3, 9))
    mid: PythonTarget = PythonTarget(floor=(3, 10))
    high: PythonTarget = PythonTarget(floor=(3, 12))
    expect_false(condition=low.union_syntax)
    expect_false(condition=low.self_type)
    expect_false(condition=low.type_alias_name)
    expect_true(condition=mid.union_syntax)
    expect_true(condition=mid.type_alias_name)
    expect_false(condition=mid.self_type)
    expect_false(condition=mid.pep695_generics)
    expect_true(condition=high.pep695_generics)
    expect_true(condition=high.type_statement)
    expect_true(condition=high.self_type)


def test_target_spelling_helpers() -> None:
    """Check that union spellings adapt to the floor."""
    low: PythonTarget = PythonTarget(floor=(3, 9))
    high: PythonTarget = PythonTarget(floor=(3, 10))
    expect_equal(
        actual=low.union(members="int | str"),
        expected="Union[int, str]",
    )
    expect_equal(
        actual=high.union(members="int | str"),
        expected="int | str",
    )
    expect_equal(
        actual=low.optional(inner="int"),
        expected="Optional[int]",
    )
    expect_equal(actual=high.optional(inner="int"), expected="int | None")
