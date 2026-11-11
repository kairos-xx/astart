"""Tests for the ``[tool.astart]`` configuration loader."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.cli.config import (
    AstartConfig,
    ConfigError,
    Selection,
    effective,
    excluded,
    load_config,
    load_project,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        basic (Final[str]): A config exercising every root key.
        nested (Final[str]): A config exercising overrides.

    """

    basic: Final[str] = """\
[project]
name = "demo"

[tool.astart]
profile = "default"
select = ["TYP", "CAL"]
ignore = ["TYP001"]
min-confidence = 0.9
checker = "auto"
safety-ceiling = "guarded"
target-version = "3.12"
library-tables = ["tables/extra.json"]
exclude = ["build/**", "vendor/*"]

[tool.astart.params]
protocol-style = "explicit"
typevar-style = "new"
max-rounds = 3
strict-mode = true
"""
    nested: Final[str] = """\
[tool.astart]
profile = "default"
select = ["TYP"]

[tool.astart.overrides."src/legacy/**"]
ignore = ["TYP003", "CAL001"]
min-confidence = 0.5
safety-ceiling = "proven"
target-version = "3.10"
params = { strict-mode = false }

[tool.astart.overrides."src/legacy/deep/**"]
profile = "strict"
"""


def _write(tmp_path: Path, name: str, text: str) -> Path:
    """Write one fixture file.

    Args:
        tmp_path (Path): Directory holding the fixture.
        name (str): File name below ``tmp_path``.
        text (str): File contents.

    Returns:
        Path: The written file's path.

    """
    target: Path = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data=text, encoding="utf-8")
    return target


def test_load_config_reads_root_keys(tmp_path: Path) -> None:
    """Every root key lands on the config.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    path: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text=Constants.basic,
    )
    config: AstartConfig = expect_not_none(
        value=load_config(path=path),
    )
    expect_equal(actual=config.selection.profile, expected="default")
    expect_equal(actual=config.selection.select, expected=("TYP", "CAL"))
    expect_equal(actual=config.selection.ignore, expected=("TYP001",))
    expect_equal(actual=config.selection.min_confidence, expected=0.9)
    expect_equal(actual=config.checker, expected="auto")
    expect_equal(actual=config.exclude, expected=("build/**", "vendor/*"))
    expect_equal(
        actual=config.library_tables,
        expected=("tables/extra.json",),
    )
    expect_equal(
        actual=config.selection.safety_ceiling,
        expected=FixSafety.guarded,
    )
    expect_equal(actual=config.selection.target_version, expected="3.12")
    expect_equal(
        actual=config.selection.params,
        expected={
            "protocol-style": "explicit",
            "typevar-style": "new",
            "max-rounds": 3,
            "strict-mode": True,
        },
    )
    expect_equal(actual=config.root, expected=tmp_path)


def test_load_config_missing_table(tmp_path: Path) -> None:
    """A pyproject without the table loads as None.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    path: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[project]
name='x'
""",
    )
    expect_equal(actual=load_config(path=path), expected=None)


def test_load_project_walks_up(tmp_path: Path) -> None:
    """The search climbs from a nested file to the pyproject.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    _: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text=Constants.basic,
    )
    nested: Path = _write(
        tmp_path=tmp_path / "pkg" / "deep",
        name="x.py",
        text="""\
x = 1
""",
    )
    config: AstartConfig = expect_not_none(
        value=load_project(start=nested),
    )
    expect_equal(actual=config.root, expected=tmp_path)


def test_selection_prefix_semantics(tmp_path: Path) -> None:
    """Select and ignore act on prefixes.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    selection: AstartConfig = expect_not_none(
        value=load_config(
            path=_write(
                tmp_path=tmp_path,
                name="pyproject.toml",
                text=Constants.basic,
            ),
        ),
    )
    sel: Selection = selection.selection
    expect_true(condition=sel.selected(code="TYP003"))
    expect_false(condition=sel.selected(code="TYP001"))
    expect_false(condition=sel.selected(code="DOC001"))
    expect_true(condition=sel.selected(code="CAL001"))


def test_effective_overrides_later_wins(tmp_path: Path) -> None:
    """Later overrides replace earlier ones.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    config: AstartConfig = expect_not_none(
        value=load_config(
            path=_write(
                tmp_path=tmp_path,
                name="pyproject.toml",
                text=Constants.nested,
            ),
        ),
    )
    plain: Selection = effective(
        config=config,
        path=tmp_path / "src" / "ok.py",
    )
    expect_equal(actual=plain.profile, expected="default")
    legacy: Selection = effective(
        config=config,
        path=tmp_path / "src" / "legacy" / "old.py",
    )
    expect_equal(actual=legacy.min_confidence, expected=0.5)
    expect_equal(actual=legacy.profile, expected="default")
    expect_equal(actual=legacy.ignore, expected=("TYP003", "CAL001"))
    expect_equal(
        actual=legacy.safety_ceiling,
        expected=FixSafety.proven,
    )
    expect_equal(actual=legacy.target_version, expected="3.10")
    expect_equal(actual=legacy.params, expected={"strict-mode": False})
    deep: Selection = effective(
        config=config,
        path=tmp_path / "src" / "legacy" / "deep" / "old.py",
    )
    expect_equal(actual=deep.profile, expected="strict")
    expect_equal(actual=deep.min_confidence, expected=0.5)
    expect_equal(actual=deep.target_version, expected="3.10")
    expect_equal(actual=deep.params, expected={"strict-mode": False})


def test_effective_unmatched_path_keeps_root(tmp_path: Path) -> None:
    """Paths matching nothing keep the root selection.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    config: AstartConfig = expect_not_none(
        value=load_config(
            path=_write(
                tmp_path=tmp_path,
                name="pyproject.toml",
                text=Constants.nested,
            ),
        ),
    )
    sel: Selection = effective(config=config, path=tmp_path / "docs" / "x.py")
    expect_equal(actual=sel.profile, expected="default")
    expect_equal(actual=sel.ignore, expected=())


def test_excluded_patterns(tmp_path: Path) -> None:
    """Exclude patterns match relative paths.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    config: AstartConfig = expect_not_none(
        value=load_config(
            path=_write(
                tmp_path=tmp_path,
                name="pyproject.toml",
                text=Constants.basic,
            ),
        ),
    )
    expect_true(
        condition=excluded(config=config, path=tmp_path / "build" / "x.py"),
    )
    expect_true(
        condition=excluded(
            config=config,
            path=tmp_path / "vendor" / "lib.py",
        ),
    )
    expect_false(
        condition=excluded(config=config, path=tmp_path / "src" / "x.py"),
    )


def test_malformed_table_raises(tmp_path: Path) -> None:
    """Type errors surface as ConfigError with the key path.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    bad: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[tool.astart]
select = "TYP"
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        load_config(path=bad)


def test_unknown_key_raises(tmp_path: Path) -> None:
    """Unknown keys are rejected, listing the offenders.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    bad: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[tool.astart]
profil = "x"
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        load_config(path=bad)


def test_bad_override_raises(tmp_path: Path) -> None:
    """Malformed override tables are rejected.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    bad: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[tool.astart.overrides."x/**"]
badkey = 1
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        load_config(path=bad)


def test_confidence_bounds(tmp_path: Path) -> None:
    """Confidence outside [0, 1] is rejected.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    bad: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[tool.astart]
min-confidence = 1.5
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        load_config(path=bad)


def test_safety_ceiling_must_be_known(tmp_path: Path) -> None:
    """Unknown safety levels are rejected.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    bad: Path = _write(
        tmp_path=tmp_path,
        name="pyproject.toml",
        text="""\
[tool.astart]
safety-ceiling = "yolo"
""",
    )
    with pytest.raises(expected_exception=ConfigError):
        load_config(path=bad)


def test_target_version_must_be_dotted_digits(tmp_path: Path) -> None:
    """Malformed target versions are rejected.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    for text in (
        """\
[tool.astart]
target-version = "three"
""",
        """\
[tool.astart]
target-version = 3.12
""",
        """\
[tool.astart]
target-version = "3."
""",
        """\
[tool.astart]
target-version = ".3"
""",
        """\
[tool.astart]
target-version = "3..4"
""",
        """\
[tool.astart]
target-version = ""
""",
        """\
[tool.astart]
target-version = "3-4"
""",
    ):
        bad: Path = _write(
            tmp_path=tmp_path,
            name="pyproject.toml",
            text=text,
        )
        with pytest.raises(expected_exception=ConfigError):
            load_config(path=bad)


def test_target_version_accepts_dotted_digits(tmp_path: Path) -> None:
    """Every ``digits(.digits)*`` spelling is accepted verbatim.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    for version in ("3", "3.12", "3.12.1", "0.0", "10.20.30.40"):
        good: Path = _write(
            tmp_path=tmp_path,
            name=f"pyproject-{version}.toml",
            text=f'[tool.astart]\ntarget-version = "{version}"\n',
        )
        config: AstartConfig | None = load_config(path=good)
        config = expect_not_none(
            value=config,
        )
        expect_equal(
            actual=config.selection.target_version,
            expected=version,
        )


def test_params_reject_non_scalars(tmp_path: Path) -> None:
    """Params accept scalars only; lists and tables are rejected.

    Args:
        tmp_path (Path): Directory holding the sample files.

    """
    for body in (
        """\
[tool.astart.params]
choices = ["a", "b"]
""",
        """\
[tool.astart.params.nested]
x = 1
""",
    ):
        bad: Path = _write(
            tmp_path=tmp_path,
            name="pyproject.toml",
            text=body,
        )
        with pytest.raises(expected_exception=ConfigError):
            load_config(path=bad)
