"""mypy support and the floor that applies when no checker is installed."""

from __future__ import annotations

from collections import Counter
from io import StringIO
from typing import TYPE_CHECKING, Final

from astart.cli import commands
from astart.cli.commands import FixCommandSettings, FixMode, run_fix
from astart.rules import checker as checker_module
from astart.rules.checker import (
    MypyChecker,
    PyrightChecker,
    build_checker,
    parse_mypy,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_not_in,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

MYPY_OUTPUT: Final[str] = (
    '{"file": "m.py", "line": 1, "column": 0, "message": "Incompatible '
    'return value", "hint": null, "code": "return-value", '
    '"severity": "error"}\n'
    '{"file": "m.py", "line": 1, "column": 0, "message": "defined here", '
    '"hint": null, "code": null, "severity": "note"}\n'
)


def test_mypy_json_lines_are_read() -> None:
    """Check that mypy json lines are read."""
    found: Counter[checker_module.Diagnostic] | None = parse_mypy(
        output=MYPY_OUTPUT,
    )
    expect_equal(actual=sum((found or {}).values()), expected=1)
    expect_equal(
        actual=parse_mypy(output=""),
        expected=Counter[checker_module.Diagnostic](),
    )
    expect_equal(actual=parse_mypy(output="not json\n"), expected=None)


def test_a_pyright_compatible_checker_is_preferred_then_mypy(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Check that a pyright compatible checker is preferred then mypy.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        tmp_path: pytest temporary directory.

    """
    installed: dict[str, str] = {"basedpyright": "/x/basedpyright"}

    def fake_which(*, cmd: str) -> str | None:
        """Return the fake install location for ``cmd``.

        Args:
            cmd: Executable name.

        Returns:
            The fake path, or ``None``.

        """
        return installed.get(cmd)

    monkeypatch.setattr(target=checker_module, name="which", value=fake_which)
    expect_instance(
        value=build_checker(root=tmp_path),
        kind=PyrightChecker,
    )
    installed.clear()
    installed["mypy"] = "/x/mypy"
    expect_instance(value=build_checker(root=tmp_path), kind=MypyChecker)
    installed.clear()
    expect_equal(actual=build_checker(root=tmp_path), expected=None)


def _no_checker(*, root: Path, source_roots: tuple[Path, ...] = ()) -> None:
    """Pretend that no type checker is installed.

    Args:
        root: Unused directory.
        source_roots: Unused import roots.

    """
    _ = (root, source_roots)


SOURCE: Final[str] = (
    "def twice(a: int):\n    return a * 2\n\n\ndef label(x=1):\n    print(x)\n"
)


def _fix(*, path: Path, use_checker: bool) -> str:
    """Run the fixer on the module at ``path``.

    Args:
        path: Module file to fix.
        use_checker: Whether to enable the external checker.

    Returns:
        The fixed source text.

    """
    out: StringIO = StringIO()
    _ = run_fix(
        settings=FixCommandSettings(
            paths=(path,),
            ceiling=FixSafety.guarded,
            stubs_path=None,
            mode=FixMode.write,
            run_formatter=False,
            use_checker=use_checker,
        ),
        out=out,
    )
    return out.getvalue()


def test_without_any_checker_weaker_evidence_is_refused(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Check that without any checker weaker evidence is refused.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        tmp_path: pytest temporary directory.

    """
    monkeypatch.setattr(
        target=commands,
        name="build_checker",
        value=_no_checker,
    )
    path: Path = tmp_path / "m.py"
    path.write_text(data=SOURCE, encoding="utf-8")
    report: str = _fix(path=path, use_checker=True)
    text: str = path.read_text(encoding="utf-8")
    expect_in(item="x: int = 1", container=text)
    expect_not_in(item="def twice(a: int) -> int", container=text)
    expect_in(item="no type checker", container=report)


def test_the_floor_is_not_applied_when_the_checker_is_switched_off(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Check that the floor is not applied when the checker is switched off.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        tmp_path: pytest temporary directory.

    """
    monkeypatch.setattr(
        target=commands,
        name="build_checker",
        value=_no_checker,
    )
    path: Path = tmp_path / "m.py"
    path.write_text(data=SOURCE, encoding="utf-8")
    report: str = _fix(path=path, use_checker=False)
    expect_in(
        item="def twice(a: int) -> int",
        container=path.read_text(encoding="utf-8"),
    )
    expect_not_in(item="no type checker", container=report)
