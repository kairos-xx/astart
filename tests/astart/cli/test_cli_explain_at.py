"""Verify ``astart explain CODE path:line[:col]``."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

from astart.__main__ import main
from astart.cli.commands import run_explain_at

from tests.support.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


@final
class Constants:
    """Group module-level constants.

    Attributes:
        bad (Final[str]): Source that triggers ``TYP001`` on line 4, column 9.
        code (Final[str]): Grouped module constant.

    """

    bad: Final[str] = """\
from typing import Any


def f(x: Any):
    return x
"""
    code: Final[str] = "TYP001"


def _run_at(
    *,
    location: str,
    code: str = Constants.code,
) -> tuple[int, str, str]:
    """Run ``run_explain_at`` while capturing its streams.

    Args:
        location (str): ``path:line[:col]`` text.
        code (str): Rule code to explain.

    Returns:
        tuple[int, str, str]: The exit code and the captured stdout and stderr.

    """
    out: StringIO = StringIO()
    err: StringIO = StringIO()
    status: int = run_explain_at(
        code=code,
        location=location,
        out=out,
        err=err,
    )
    return status, out.getvalue(), err.getvalue()


def _write_bad(*, tmp_path: Path) -> Path:
    """Write the ``TYP001`` sample and return its path.

    Args:
        tmp_path (Path): Directory holding the sample file.

    Returns:
        Path: The written file's path.

    """
    path: Path = tmp_path / "bad.py"
    path.write_text(data=Constants.bad, encoding="utf-8")
    return path


def test_matching_location_prints_header_and_message(
    *,
    tmp_path: Path,
) -> None:
    """A ``path:line:col`` match prints the rule header and message.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _write_bad(tmp_path=tmp_path)
    status, out, err = _run_at(location=f"{path}:4:9")
    expect_equal(actual=status, expected=0)
    expect_equal(actual=err, expected="")
    expect_in(item="TYP001", container=out)
    expect_in(item="typing.no-any", container=out)
    expect_in(item="`Any` is used", container=out)
    expect_in(item="name:", container=out)


def test_line_only_location_matches_any_column(
    *,
    tmp_path: Path,
) -> None:
    """A ``path:line`` location matches the finding on that line.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _write_bad(tmp_path=tmp_path)
    status, out, _err = _run_at(location=f"{path}:4")
    expect_equal(actual=status, expected=0)
    expect_in(item="`Any` is used", container=out)


def test_wrong_line_returns_one(*, tmp_path: Path) -> None:
    """A location with no matching finding exits one.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _write_bad(tmp_path=tmp_path)
    status, out, err = _run_at(location=f"{path}:2")
    expect_equal(actual=status, expected=1)
    expect_equal(actual=out, expected="")
    expect_in(item="no TYP001 finding", container=err)


def test_bad_location_returns_two(*, tmp_path: Path) -> None:
    """A malformed location exits with the usage error.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    _: Path = _write_bad(tmp_path=tmp_path)
    status, _out, err = _run_at(location="not-a-location")
    expect_equal(actual=status, expected=2)
    expect_in(item="bad location", container=err)


def test_unknown_code_returns_two(*, tmp_path: Path) -> None:
    """An unknown rule code exits with the usage error.

    Args:
        tmp_path (Path): Directory holding the sample file.

    """
    path: Path = _write_bad(tmp_path=tmp_path)
    status, _out, err = _run_at(location=f"{path}:4", code="NOPE99")
    expect_equal(actual=status, expected=2)
    expect_in(item="unknown rule code", container=err)


def test_main_dispatches_location(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``astart explain CODE path:line[:col]`` prints the located finding.

    Args:
        tmp_path (Path): Directory holding the sample file.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    path: Path = _write_bad(tmp_path=tmp_path)
    out: StringIO = StringIO()
    err: StringIO = StringIO()
    monkeypatch.setattr(target="astart.__main__.stdout", name=out)
    monkeypatch.setattr(target="astart.__main__.stderr", name=err)
    status: int = main(argv=["explain", Constants.code, f"{path}:4:9"])
    expect_equal(actual=status, expected=0)
    expect_in(item="typing.no-any", container=out.getvalue())
    expect_in(item="`Any` is used", container=out.getvalue())
    expect_equal(actual=err.getvalue(), expected="")


def test_main_explain_without_location_still_works(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``astart explain CODE`` keeps printing the plain explanation.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    out: StringIO = StringIO()
    monkeypatch.setattr(target="astart.__main__.stdout", name=out)
    status: int = main(argv=["explain", Constants.code])
    expect_equal(actual=status, expected=0)
    text: str = out.getvalue()
    expect_in(item="typing.no-any", container=text)
    expect_in(item="flagged:", container=text)
