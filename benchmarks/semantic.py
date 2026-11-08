"""Semantic-equivalence runs: fixing a package must not change what it does.

A pinned, pure-Python package is copied twice. One copy is left alone, the
other goes through the real ``astart fix`` pipeline. Both are then imported in
fresh interpreters: every submodule must import (or fail) the same way and a
smoke snippet must give the same result.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from io import StringIO
from json import dumps, loads
from pathlib import Path
from re import compile as compile_pattern
from shutil import copytree, ignore_patterns
from sys import executable
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, Self, TypedDict, final

from astart.cli.commands import FixCommandSettings, FixMode, run_fix
from astart.rules.process import Completed, run_command
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.machinery import ModuleSpec
    from re import Match


@final
class Constants:
    """Group module-level constants.

    Attributes:
        timeout_seconds: Time limit of one interpreter run.
        summary: Pattern of the fixer's last output line.
        probe: Program run in a fresh interpreter for each copy.

    """

    timeout_seconds: Final[float] = 120.0
    summary: Final = compile_pattern(
        pattern=r"(\d+) files changed, (\d+) fixes applied",
    )
    probe: Final[str] = """\
import importlib, json, pkgutil, sys
package, smoke = sys.argv[1], sys.argv[2]
status = {}
root = importlib.import_module(package)
status[package] = "ok"
for info in pkgutil.walk_packages(root.__path__, prefix=package + "."):
    try:
        importlib.import_module(info.name)
        status[info.name] = "ok"
    except BaseException as error:
        status[info.name] = type(error).__name__
scope = {}
exec(smoke, scope)
print(json.dumps({"status": status, "result": repr(scope.get("result"))}))
"""


@final
@dataclass(frozen=True, slots=True)
class Project:
    """A pinned package and the snippet that exercises it.

    Attributes:
        name: Distribution name.
        version: Exact version the run is valid for.
        package: Top-level import name.
        smoke: Code that sets ``result``.

    """

    name: str
    version: str
    package: str
    smoke: str


@final
@dataclass(frozen=True, slots=True)
class ProjectResult:
    """Outcome of one project.

    Attributes:
        name: Distribution name.
        files_changed: Files the fixer rewrote.
        fixes: Fixes applied.
        same_imports: Whether every submodule imported the same way.
        same_result: Whether the smoke snippet gave the same result.
        note: Why the project was skipped or failed, empty when it passed.

    """

    name: str
    files_changed: int
    fixes: int
    same_imports: bool
    same_result: bool
    note: str

    @classmethod
    def skipped(cls, *, name: str, note: str) -> Self:
        """Build a result for a project that could not be run.

        Args:
            name: Distribution name.
            note: Why it was skipped.

        Returns:
            A failing result carrying the note.

        """
        return cls(
            name=name,
            files_changed=0,
            fixes=0,
            same_imports=False,
            same_result=False,
            note=note,
        )

    @property
    def passed(self) -> bool:
        """Tell whether the project is equivalent after fixing.

        Returns:
            ``True`` when imports and smoke result are unchanged.

        """
        return not self.note and self.same_imports and self.same_result


def load_projects(*, path: Path) -> tuple[Project, ...]:
    """Read the pinned project list.

    Args:
        path: JSON file with ``name``, ``version``, ``package``, ``smoke``.

    Returns:
        The projects, in file order.

    """
    return tuple(
        Project(
            name=item["name"],
            version=item["version"],
            package=item["package"],
            smoke=item["smoke"],
        )
        for item in loads(s=path.read_text(encoding="utf-8"))
    )


class _ProbeReport(TypedDict):
    """Decoded output of the probe interpreter.

    Attributes:
        status: ``"ok"`` or the exception name per imported module.
        result: ``repr`` of the smoke snippet's ``result`` variable.

    """

    status: dict[str, str]
    result: str


def _probe(*, root: Path, project: Project) -> _ProbeReport | None:
    """Import a package copy and exercise it in a fresh interpreter.

    Args:
        root: Directory holding the package copy; it is put on the path.
        project: The project.

    Returns:
        The decoded report, or ``None`` when the interpreter failed.

    """
    completed: Completed = run_command(
        arguments=(
            executable,
            "-c",
            Constants.probe,
            project.package,
            project.smoke,
        ),
        cwd=root,
        timeout=Constants.timeout_seconds,
        environment={"PYTHONPATH": str(object=root), "PYTHONHASHSEED": "0"},
    )
    if completed.code != 0:
        return None
    return loads(s=completed.stdout.splitlines()[-1])


def _locate(*, project: Project) -> Path | str:
    """Find the installed package directory of a pinned project.

    Args:
        project: The project.

    Returns:
        The directory, or the reason it cannot be used.

    """
    try:
        installed: str = version(distribution_name=project.name)
    except PackageNotFoundError:
        return "not installed"
    if installed != project.version:
        return f"version {installed} differs from the pinned {project.version}"
    spec: ModuleSpec | None = find_spec(name=project.package)
    locations: Sequence[str] | None = (
        None if spec is None else spec.submodule_search_locations
    )
    return Path(next(iter(locations))) if locations else "no package dir"


def run_project(
    *,
    project: Project,
    source: Path | None = None,
) -> ProjectResult:
    """Fix a copy of a package and compare its behaviour with the original's.

    Args:
        project: The pinned project.
        source: The package directory; located through the import system
            when ``None``.

    Returns:
        The result; a skipped project carries a note.

    """
    where: Path | str = _locate(project=project) if source is None else source
    if isinstance(where, str):
        return ProjectResult.skipped(name=project.name, note=where)
    with TemporaryDirectory() as scratch:
        original: Path = Path(scratch) / "original"
        fixed: Path = Path(scratch) / "fixed"
        for target in (original, fixed):
            _ = copytree(
                src=where,
                dst=target / project.package,
                ignore=ignore_patterns("__pycache__", "*.pyc"),
            )
        out: StringIO = StringIO()
        _ = run_fix(
            settings=FixCommandSettings(
                paths=(fixed / project.package,),
                ceiling=FixSafety.guarded,
                stubs_path=None,
                mode=FixMode.write,
                run_formatter=False,
                use_checker=False,
            ),
            out=out,
        )
        before: _ProbeReport | None = _probe(root=original, project=project)
        after: _ProbeReport | None = _probe(root=fixed, project=project)
    if before is None or after is None:
        return ProjectResult.skipped(name=project.name, note="probe failed")
    counts: Match[str] | None = Constants.summary.search(string=out.getvalue())
    return ProjectResult(
        name=project.name,
        files_changed=int(counts[1]) if counts else 0,
        fixes=int(counts[2]) if counts else 0,
        same_imports=before["status"] == after["status"],
        same_result=before["result"] == after["result"],
        note="",
    )


def run_semantic(*, projects: Sequence[Project]) -> tuple[ProjectResult, ...]:
    """Run every project.

    Args:
        projects: The pinned projects.

    Returns:
        One result per project, in order.

    """
    return tuple(run_project(project=item) for item in projects)


def to_json(*, results: Sequence[ProjectResult]) -> str:
    """Render the results as JSON.

    Args:
        results: One result per project.

    Returns:
        A JSON document with a pass count and each project.

    """
    return dumps(
        obj={
            "passed": sum(1 for item in results if item.passed),
            "total": len(results),
            "projects": [
                {
                    "name": item.name,
                    "files_changed": item.files_changed,
                    "fixes": item.fixes,
                    "same_imports": item.same_imports,
                    "same_result": item.same_result,
                    "note": item.note,
                }
                for item in results
            ],
        },
        indent=2,
    )
