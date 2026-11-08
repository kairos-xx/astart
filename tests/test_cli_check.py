"""Verify the check command."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, Final, final

from astart.cli.commands import CheckSettings, run_check, severity_reaches
from astart.rules.vocabulary import Severity

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        bad: Grouped module constant.
        good: Grouped module constant.

    """

    bad: Final[str] = """\
from typing import Any


def f(x: Any):
    return x
"""
    good: Final[str] = """\
def f(x: int) -> int:
    return x
"""


def _run(
    *,
    paths: list[Path],
    output_format: str = "text",
    fail_on: Severity = Severity.error,
    exclude: tuple[str, ...] = (),
) -> tuple[int, str]:
    """Run the check command while capturing its output.

    Args:
        paths: Files or directories to check.
        output_format: Output format for the findings.
        fail_on: Minimum severity that fails the run.
        exclude: Discovery globs to skip.

    Returns:
        The exit code and the captured output.

    """
    out: StringIO = StringIO()
    code: int = run_check(
        settings=CheckSettings(
            paths=tuple(paths),
            output_format=output_format,
            fail_on=fail_on,
            stubs_path=None,
            exclude=exclude,
        ),
        out=out,
    )
    return (code, out.getvalue())


def test_clean_file_exits_zero(*, tmp_path: Path) -> None:
    """Check that clean file exits zero.

    Args:
        tmp_path: Directory holding the sample files.

    """
    path: Path = tmp_path / "ok.py"
    path.write_text(data=Constants.good, encoding="utf-8")
    code, text = _run(paths=[path])
    expect_equal(actual=code, expected=0)
    expect_equal(actual=text, expected="")


def test_finding_exits_one_and_prints_location(*, tmp_path: Path) -> None:
    """Check that finding exits one and prints location.

    Args:
        tmp_path: Directory holding the sample files.

    """
    path: Path = tmp_path / "bad.py"
    path.write_text(data=Constants.bad, encoding="utf-8")
    code, text = _run(paths=[path])
    expect_equal(actual=code, expected=1)
    expect_in(item=f"{path}:4:9: TYP001", container=text)


def test_exclude_skips_matching_files(*, tmp_path: Path) -> None:
    """Check that ``exclude`` keeps a bad file out of the report.

    Args:
        tmp_path: Directory holding the sample files.

    """
    skipped: Path = tmp_path / "skip" / "bad.py"
    skipped.parent.mkdir(parents=True)
    skipped.write_text(data=Constants.bad, encoding="utf-8")
    code, text = _run(paths=[tmp_path], exclude=("skip/*",))
    expect_equal(actual=code, expected=0)
    expect_equal(actual=text, expected="")


def test_severity_threshold_orders_levels() -> None:
    """Check that severity threshold orders levels."""
    expect_true(
        condition=severity_reaches(
            severity=Severity.error,
            threshold=Severity.warning,
        ),
    )
    expect_false(
        condition=severity_reaches(
            severity=Severity.warning,
            threshold=Severity.error,
        ),
    )
    expect_true(
        condition=severity_reaches(
            severity=Severity.info,
            threshold=Severity.info,
        ),
    )


def test_syntax_error_exits_two_and_continues(*, tmp_path: Path) -> None:
    """Check that syntax error exits two and continues.

    Args:
        tmp_path: Directory holding the sample files.

    """
    broken: Path = tmp_path / "a_broken.py"
    broken.write_text(
        data="""\
def (:
""",
        encoding="utf-8",
    )
    bad: Path = tmp_path / "b_bad.py"
    bad.write_text(data=Constants.bad, encoding="utf-8")
    code, text = _run(paths=[broken, bad])
    expect_equal(actual=code, expected=2)
    expect_in(item="a_broken.py", container=text)
    expect_in(item="TYP001", container=text)


def test_missing_path_exits_two(*, tmp_path: Path) -> None:
    """Check that missing path exits two.

    Args:
        tmp_path: Directory holding the sample files.

    """
    code, text = _run(paths=[tmp_path / "gone.py"])
    expect_equal(actual=code, expected=2)
    expect_in(item="gone.py", container=text)


def test_latin1_source_is_decoded(*, tmp_path: Path) -> None:
    """Check that latin1 source is decoded.

    Args:
        tmp_path: Directory holding the sample files.

    """
    path: Path = tmp_path / "l.py"
    path.write_bytes(
        data="""\
# coding: latin-1
NAME = 'café'
""".encode(encoding="latin-1"),
    )
    code, _ = _run(paths=[path])
    expect_equal(actual=code, expected=1)


def test_json_format_is_valid_json(*, tmp_path: Path) -> None:
    """Check that json format is valid json.

    Args:
        tmp_path: Directory holding the sample files.

    """
    path: Path = tmp_path / "bad.py"
    path.write_text(data=Constants.bad, encoding="utf-8")
    code, text = _run(paths=[path], output_format="json")
    expect_equal(actual=code, expected=1)
    expect_equal(actual=loads(s=text)[0]["path"], expected=str(object=path))
