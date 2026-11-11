"""``astart check --write-baseline``/``--baseline`` wiring (H-03)."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, Final, cast, final

from astart.__main__ import main

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import pytest


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source (Final[str]): Module source producing exactly one ``TYP001``
            finding.
        other (Final[str]): Second module with its own ``TYP001`` finding.

    """

    source: Final[str] = """\
from typing import Any


def f(x: Any) -> int:
    return 1
"""
    other: Final[str] = """\
from typing import Any


def g(y: Any) -> str:
    return 'x'
"""


def _write(*, directory: Path, name: str, text: str) -> Path:
    """Write one module into ``directory``.

    Args:
        directory (Path): Parent directory.
        name (str): File name.
        text (str): File contents.

    Returns:
        Path: Path of the written module.

    """
    path: Path = directory / name
    _: int = path.write_text(data=text, encoding="utf-8")
    return path


def _check(
    *,
    args: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, str]:
    """Run ``astart check`` and return ``(exit code, stdout)``.

    Args:
        args (list[str]): Arguments after ``check``.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    Returns:
        tuple[int, str]: Exit code and captured stdout.

    """
    out: StringIO = StringIO()
    monkeypatch.setattr(target="astart.__main__.stdout", name=out)
    code: int = main(argv=["check", *args])
    return code, out.getvalue()


def test_write_baseline_then_clean_rerun_exits_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A recorded finding stays hidden on the next run.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    target: Path = _write(
        directory=tmp_path,
        name="m.py",
        text=Constants.source,
    )
    baseline: Path = tmp_path / "baseline.json"
    code, _ = _check(
        args=[str(object=target)],
        monkeypatch=monkeypatch,
    )
    expect_equal(actual=code, expected=1)
    code, _ = _check(
        args=[
            str(object=target),
            "--write-baseline",
            str(object=baseline),
        ],
        monkeypatch=monkeypatch,
    )
    expect_equal(actual=code, expected=1)
    expect_true(condition=baseline.exists())
    document: Mapping[str, object] = loads(
        s=baseline.read_text(encoding="utf-8"),
    )
    fingerprints: list[object] = cast(
        typ="list[object]",
        val=document.get("fingerprints"),
    )
    expect_equal(actual=len(fingerprints), expected=1)
    code, out = _check(
        args=[
            str(object=target),
            "--baseline",
            str(object=baseline),
        ],
        monkeypatch=monkeypatch,
    )
    expect_equal(actual=code, expected=0)
    expect_true(condition="TYP001" not in out)


def test_baseline_hides_only_recorded_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second file's finding still fails the run.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    first: Path = _write(
        directory=tmp_path,
        name="a.py",
        text=Constants.source,
    )
    second: Path = _write(
        directory=tmp_path,
        name="b.py",
        text=Constants.other,
    )
    baseline: Path = tmp_path / "baseline.json"
    _, _ = _check(
        args=[
            str(object=first),
            "--write-baseline",
            str(object=baseline),
        ],
        monkeypatch=monkeypatch,
    )
    code, out = _check(
        args=[
            str(object=first),
            str(object=second),
            "--baseline",
            str(object=baseline),
        ],
        monkeypatch=monkeypatch,
    )
    expect_equal(actual=code, expected=1)
    expect_true(condition="b.py" in out)
    expect_true(condition="a.py" not in out)


def test_missing_baseline_exits_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing baseline file is a usage error.

    Args:
        tmp_path (Path): pytest temporary directory.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    target: Path = _write(
        directory=tmp_path,
        name="m.py",
        text=Constants.source,
    )
    code, out = _check(
        args=[
            str(object=target),
            "--baseline",
            str(object=tmp_path / "none.json"),
        ],
        monkeypatch=monkeypatch,
    )
    expect_equal(actual=code, expected=2)
    expect_true(condition="baseline" in out)
