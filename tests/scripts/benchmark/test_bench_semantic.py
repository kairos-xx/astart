"""Semantic-equivalence runs on a synthetic package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from scripts.benchmark.semantic import (
    Project,
    ProjectResult,
    load_projects,
    run_project,
    to_json,
)
from tests.support.expectations import expect_equal, expect_in, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Constants used in the test_bench_semantic module.

    Attributes:
        pinned (Final[int]): Pinned benchmark entries the output must match.
        module (Final[str]): Source of the tiny benchmark module.
        smoke (Final[str]): Import-and-call snippet run against the package.

    """

    pinned: Final[int] = 15

    module: Final[str] = """\
LIMIT = 3


def scale(value, factor=2):
    return value * factor


def describe(items):
    return ", ".join(str(item) for item in items)


class Box:
    def __init__(self, content):
        self.content = content

    def get(self):
        return self.content


print_nothing = None
"""

    smoke: Final[str] = (
        "from tinypkg import core\n"
        "result = [core.scale(4), core.describe([1, 2]), core.Box(7).get(),"
        " core.LIMIT]"
    )


def _package(*, tmp_path: Path, extra: str = "") -> Path:
    """Create a tiny importable package under ``tmp_path``.

    Args:
        tmp_path (Path): pytest temporary directory.
        extra (str): Extra source appended to ``core.py``.

    Returns:
        Path: The package root directory.

    """
    root: Path = tmp_path / "tinypkg"
    root.mkdir()
    _ = (root / "__init__.py").write_text(data="", encoding="utf-8")
    _ = (root / "core.py").write_text(
        data=Constants.module + extra,
        encoding="utf-8",
    )
    _ = (root / "broken_import.py").write_text(
        data="""\
import definitely_missing_module
""",
        encoding="utf-8",
    )
    return root


def test_a_fixed_package_behaves_like_the_original(*, tmp_path: Path) -> None:
    """Check that a fixed package behaves like the original.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    result: ProjectResult = run_project(
        project=Project(
            name="tinypkg",
            version="0",
            package="tinypkg",
            smoke=Constants.smoke,
        ),
        source=_package(tmp_path=tmp_path),
    )
    expect_true(condition=result.passed, message=str(object=result))
    expect_true(condition=result.fixes > 0)
    expect_true(condition=result.files_changed >= 1)


def test_a_behaviour_change_is_detected() -> None:
    """Check that a behaviour change is detected."""
    differs: ProjectResult = ProjectResult(
        name="x",
        files_changed=1,
        fixes=1,
        same_imports=True,
        same_result=False,
        note="",
    )
    expect_equal(actual=differs.passed, expected=False)
    expect_equal(
        actual=ProjectResult.skipped(name="x", note="not installed").passed,
        expected=False,
    )


def test_missing_or_mismatched_projects_are_skipped_with_a_note() -> None:
    """Check that missing or mismatched projects are skipped with a note."""
    absent: ProjectResult = run_project(
        project=Project(
            name="definitely-not-installed-xyz",
            version="1",
            package="nothing",
            smoke="result = 1",
        ),
    )
    expect_equal(actual=absent.note, expected="not installed")
    wrong: ProjectResult = run_project(
        project=Project(
            name="pytest",
            version="0.0.0",
            package="_pytest",
            smoke="result = 1",
        ),
    )
    expect_in(item="differs from the pinned", container=wrong.note)


def test_the_pinned_list_is_well_formed_and_serialises() -> None:
    """Check that the pinned list is well formed and serialises."""
    projects: tuple[Project, ...] = load_projects(path=_projects_path())
    expect_equal(actual=len(projects), expected=Constants.pinned)
    for item in projects:
        expect_true(condition="result" in item.smoke, message=item.name)
    text: str = to_json(results=[ProjectResult.skipped(name="a", note="n")])
    expect_in(item='"passed": 0', container=text)


def _projects_path() -> Path:
    """Locate the pinned projects list.

    Returns:
        Path: Path to ``scripts/benchmark/artifacts/resources/projects.json``.

    """
    return (
        Paths.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "projects.json"
    )
