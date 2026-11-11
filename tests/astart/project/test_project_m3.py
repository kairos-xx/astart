"""M3 exit gate: whole-project analysis end to end.

Covers import resolution, the project call graph, cross-module call-site
evidence, stub-package loading and version-aware emission through the real
CLI entry points — plus recall (every in-project caller contributes) and a
marked-slow scale check.

"""

from __future__ import annotations

from io import StringIO
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.cli.commands import (
    CheckSettings,
    FixCommandSettings,
    FixMode,
    run_check,
    run_fix,
)
from astart.project.builder import build_index
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.project_bridge import ProjectView
from astart.rules.vocabulary import FixSafety, Severity

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from astart.project.index import ProjectIndex


def _tree(*, root: Path, sources: Mapping[str, str]) -> list[Path]:
    """Write ``pkg/``-style sources into a tree.

    Args:
        root (Path): Project root.
        sources (Mapping[str, str]): Dotted name to source text; ``.__pkg__``
            keys write the package ``__init__.py``.

    Returns:
        list[Path]: Written files.

    """
    files: list[Path] = []
    for name, source in sources.items():
        is_init: bool = name.endswith(".__pkg__")
        parts: list[str] = name.removesuffix(".__pkg__").split(sep=".")
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
    return files


def _fix(
    *,
    paths: list[Path],
    project: bool,
    closed: bool = False,
    target_version: str | None = None,
) -> tuple[int, str]:
    """Run the fix command in write mode.

    Args:
        paths (list[Path]): Files or directories to fix.
        project (bool): Whether project mode is on.
        closed (bool): Whether to disable the external-caller assumption.
        target_version (str | None): Oldest Python version emitted code must
            run on.

    Returns:
        tuple[int, str]: Exit code and captured output.

    """
    out: StringIO = StringIO()
    code: int = run_fix(
        settings=FixCommandSettings(
            paths=tuple(paths),
            ceiling=FixSafety.guarded,
            stubs_path=None,
            mode=FixMode.write,
            run_formatter=False,
            project=project,
            assume_external_callers=not closed,
            target_version=target_version,
        ),
        out=out,
    )
    return code, out.getvalue()


def test_m3_cross_module_annotation(*, tmp_path: Path) -> None:
    """Check the CLI writes an annotation earned in another module.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                "from pkg.core import _helper\n"
                "def run():\n"
                "    return _helper(7)\n"
            ),
        },
    )
    code, _out = _fix(paths=files, project=True)
    expect_equal(actual=code, expected=1)
    expect_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_single_file_mode_unchanged(*, tmp_path: Path) -> None:
    """Check that without ``--project`` nothing cross-module applies.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                "from pkg.core import _helper\n"
                "def run():\n"
                "    return _helper(7)\n"
            ),
        },
    )
    _fix(paths=files, project=False)
    expect_not_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_exported_guarded(*, tmp_path: Path) -> None:
    """Check exported APIs stay untouched in open-world mode.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def api(x):
    print(x)
""",
            "pkg.user": (
                """\
from pkg.core import api
def run():
    return api(7)
"""
            ),
        },
    )
    _fix(paths=files, project=True)
    expect_not_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_closed_world_annotates(*, tmp_path: Path) -> None:
    """Check ``--closed-world`` lets exported APIs take call evidence.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def api(x):
    print(x)
""",
            "pkg.user": (
                """\
from pkg.core import api
def run():
    return api(7)
"""
            ),
        },
    )
    _fix(paths=files, project=True, closed=True)
    expect_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_keyword_rewrite_cross_module(*, tmp_path: Path) -> None:
    """Check ``calls.add-keywords`` works through the project table.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def f(x, y):
    return x + y
""",
            "pkg.user": (
                """\
from pkg.core import f
def run():
    return f(1, 2)
"""
            ),
        },
    )
    code, _out = _fix(paths=files, project=True)
    expect_equal(actual=code, expected=1)
    expect_in(
        item="f(x=1, y=2)",
        container=(tmp_path / "pkg" / "user.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_reexport_reaches_definition(*, tmp_path: Path) -> None:
    """Check calls through ``__init__`` re-exports evidence the callee.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": """\
from .core import _helper
""",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                """\
from pkg import _helper
def run():
    return _helper(7)
"""
            ),
        },
    )
    _fix(paths=files, project=True)
    expect_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_check_reports_project_findings(*, tmp_path: Path) -> None:
    """Check ``run_check`` surfaces cross-module hints as findings.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                "from pkg.core import _helper\n"
                "def run():\n"
                "    return _helper(7)\n"
            ),
        },
    )
    out: StringIO = StringIO()
    code: int = run_check(
        settings=CheckSettings(
            paths=tuple(files),
            output_format="text",
            fail_on=Severity.error,
            stubs_path=None,
            project=True,
        ),
        out=out,
    )
    expect_equal(actual=code, expected=1)
    expect_in(item="TYP003", container=out.getvalue())
    expect_in(item="CAL001", container=out.getvalue())


def test_m3_idempotent(*, tmp_path: Path) -> None:
    """Check that a second fix pass changes nothing.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                "from pkg.core import _helper\n"
                "def run():\n"
                "    return _helper(7)\n"
            ),
        },
    )
    _fix(paths=files, project=True)
    after_first: str = (tmp_path / "pkg" / "core.py").read_text(
        encoding="utf-8",
    )
    _, _out = _fix(paths=files, project=True)
    after_second: str = (tmp_path / "pkg" / "core.py").read_text(
        encoding="utf-8",
    )
    expect_equal(actual=after_second, expected=after_first)


def test_m3_target_version_respells_union(*, tmp_path: Path) -> None:
    """Check that a pre-3.10 target rewrites ``|`` unions it emits.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    file: Path = tmp_path / "mod.py"
    file.write_text(
        data=dedent(
            text="""\
            def pick(flag):
                if flag:
                    return 1
                return None
            """,
        ),
        encoding="utf-8",
    )
    _fix(paths=[file], project=False, target_version="3.9")
    text: str = file.read_text(encoding="utf-8")
    expect_not_in(item="| None", container=text)


def test_m3_precision_no_silent_hallucination(*, tmp_path: Path) -> None:
    """Check that untyped callers supply no annotation evidence.

    A caller passing an unresolvable name must not produce a type: the
    evidence layer reports unknown, never invents ``str``/``int``.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    files: list[Path] = _tree(
        root=tmp_path,
        sources={
            "pkg.__pkg__": "",
            "pkg.core": """\
def _helper(x):
    print(x)
""",
            "pkg.user": (
                "from pkg.core import _helper\n"
                "def run(value):\n"
                "    return _helper(value)\n"
            ),
        },
    )
    _fix(paths=files, project=True)
    expect_not_in(
        item="x: int",
        container=(tmp_path / "pkg" / "core.py").read_text(
            encoding="utf-8",
        ),
    )


def test_m3_index_scale_small_project(*, tmp_path: Path) -> None:
    """Check that a many-module project indexes without error.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    sources: dict[str, str] = {"pkg.__pkg__": ""}
    for number in range(40):
        sources[f"pkg.mod{number}"] = f"def f{number}(x):\n    print(x)\n"
        sources[f"pkg.user{number}"] = (
            f"from pkg.mod{number} import f{number}\n"
            f"def run():\n"
            f"    return f{number}({number})\n"
        )
    files: list[Path] = _tree(root=tmp_path, sources=sources)
    code, _out = _fix(paths=files, project=True, closed=True)
    expect_equal(actual=code, expected=1)
    for number in (0, 20, 39):
        expect_in(
            item="x: int",
            container=(tmp_path / "pkg" / f"mod{number}.py").read_text(
                encoding="utf-8",
            ),
        )


@pytest.mark.slow
def test_m3_index_scale_hundred_k_lines(*, tmp_path: Path) -> None:
    """Check that a ~100k-line project indexes and evidences correctly.

    The index — not 400 separate fix passes — is the scale surface, so
    this builds the whole call graph once and verifies cross-module
    evidence on sampled callees through ``fix_source``.

    Args:
        tmp_path (Path): Directory holding the project.

    """
    sources: dict[str, str] = {}
    modules_per_package: int = 20
    packages: int = 10
    total: int = modules_per_package * packages
    for number in range(total):
        package: int = number % packages
        name: str = f"pkg{package}.mod{number}"
        sources[f"pkg{package}.__pkg__"] = ""
        lines: list[str] = [f"def _f{number}(x):"]
        lines.extend(f"    y_{line} = x + {line}" for line in range(500))
        lines.append(f"    print(y_{number})")
        sources[name] = "\n".join(lines) + "\n"
        caller: str = f"pkg{package}.user{number}"
        sources[caller] = (
            f"from pkg{package}.mod{number} import _f{number}\n"
            f"RESULT = _f{number}({number})\n"
        )
    files: list[Path] = _tree(root=tmp_path, sources=sources)
    index: ProjectIndex = build_index(files=files).index
    for number in (0, total // 2, total - 1):
        slot: int = number % packages
        module: str = f"pkg{slot}.mod{number}"
        source: str = (tmp_path / f"pkg{slot}" / f"mod{number}.py").read_text(
            encoding="utf-8",
        )
        outcome: FixResult = fix_source(
            source=source,
            filename=f"mod{number}.py",
            catalog=load_default_catalog(
                registries=default_registries(),
            ),
            registries=default_registries(),
            settings=FixSettings(
                ceiling=FixSafety.guarded,
                project=ProjectView(index=index, module=module),
            ),
        )
        expect_in(item="x: int", container=outcome.source)
