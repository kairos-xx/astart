"""Verify the fix command."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from astart.cli.commands import FixCommandSettings, FixMode, run_fix
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path
SAMPLE = """\
# header
LIMIT = 3  # limit


def scale(x, k=2):  # scale
    print(x * k)


scale(2, 3)  # call
"""


def _run(
    *,
    paths: list[Path],
    ceiling: FixSafety = FixSafety.guarded,
    mode: FixMode = FixMode.write,
    run_formatter: bool = False,
) -> tuple[int, str]:
    out: StringIO = StringIO()
    code: int = run_fix(
        settings=FixCommandSettings(
            paths=tuple(paths),
            ceiling=ceiling,
            stubs_path=None,
            mode=mode,
            run_formatter=run_formatter,
        ),
        out=out,
    )
    return code, out.getvalue()


def _sample(*, tmp_path: Path, text: str = SAMPLE) -> Path:
    path: Path = tmp_path / "m.py"
    path.write_text(data=text, encoding="utf-8")
    return path


def test_write_mode_applies_proven_fixes_only(*, tmp_path: Path) -> None:
    """Check that write mode applies proven fixes only."""
    path: Path = _sample(tmp_path=tmp_path)
    code, _ = _run(paths=[path], ceiling=FixSafety.proven)
    text: str = path.read_text(encoding="utf-8")
    expect_equal(actual=code, expected=1)
    expect_in(item="LIMIT: Final[int] = 3  # limit", container=text)
    expect_in(item="-> None:  # scale", container=text)
    expect_in(item="scale(2, 3)  # call", container=text)


def test_guarded_ceiling_adds_keywords_and_hints(*, tmp_path: Path) -> None:
    """Check that guarded ceiling adds keywords and hints."""
    path: Path = _sample(tmp_path=tmp_path)
    _ = _run(paths=[path])
    text: str = path.read_text(encoding="utf-8")
    expect_in(item="scale(x=2, k=3)  # call", container=text)
    expect_in(item="k: int = 2", container=text)


def test_diff_mode_prints_diff_and_leaves_file(*, tmp_path: Path) -> None:
    """Check that diff mode prints diff and leaves file."""
    path: Path = _sample(tmp_path=tmp_path)
    code, text = _run(paths=[path], mode=FixMode.diff)
    expect_equal(actual=code, expected=1)
    expect_in(item="+LIMIT: Final[int] = 3", container=text)
    expect_equal(actual=path.read_text(encoding="utf-8"), expected=SAMPLE)


def test_check_mode_exits_one_without_writing(*, tmp_path: Path) -> None:
    """Check that check mode exits one without writing."""
    path: Path = _sample(tmp_path=tmp_path)
    code, _ = _run(paths=[path], mode=FixMode.check)
    expect_equal(actual=code, expected=1)
    expect_equal(actual=path.read_text(encoding="utf-8"), expected=SAMPLE)


def test_unchanged_file_not_rewritten(*, tmp_path: Path) -> None:
    """Check that unchanged file not rewritten."""
    path: Path = _sample(
        tmp_path=tmp_path,
        text="""\
x: int = 1
""",
    )
    before: int = path.stat().st_mtime_ns
    code, _ = _run(paths=[path])
    expect_equal(actual=code, expected=0)
    expect_equal(actual=path.stat().st_mtime_ns, expected=before)


def test_second_run_is_noop(*, tmp_path: Path) -> None:
    """Check that second run is noop."""
    path: Path = _sample(tmp_path=tmp_path)
    _ = _run(paths=[path])
    code, _ = _run(paths=[path])
    expect_equal(actual=code, expected=0)


def test_latin1_file_keeps_encoding(*, tmp_path: Path) -> None:
    """Check that latin1 file keeps encoding."""
    path: Path = tmp_path / "l.py"
    path.write_bytes(
        data="""\
# coding: latin-1
NAME = 3  # café
""".encode(encoding="latin-1"),
    )
    _ = _run(paths=[path])
    data: bytes = path.read_bytes()
    expect_in(item=b"caf\xe9", container=data)
    expect_in(item=b"NAME: Final[int] = 3", container=data)


def test_unparsable_file_untouched_exit_two(*, tmp_path: Path) -> None:
    """Check that unparsable file untouched exit two."""
    path: Path = _sample(
        tmp_path=tmp_path,
        text="""\
def (:
""",
    )
    code, _ = _run(paths=[path])
    expect_equal(actual=code, expected=2)
    expect_equal(
        actual=path.read_text(encoding="utf-8"),
        expected="""\
def (:
""",
    )


def test_summary_reports_counts_and_skips(*, tmp_path: Path) -> None:
    """Check that summary reports counts and skips."""
    path: Path = _sample(tmp_path=tmp_path)
    _, text = _run(paths=[path])
    expect_in(item="files changed", container=text)
    expect_in(item="fixes applied", container=text)


def test_formatter_runs_when_requested(*, tmp_path: Path) -> None:
    """Check that formatter runs when requested."""
    path: Path = _sample(
        tmp_path=tmp_path,
        text="""\
X  =  3
""",
    )
    _ = _run(paths=[path], run_formatter=True)
    text: str = path.read_text(encoding="utf-8")
    expect_not_in(item="X  =", container=text)
    expect_true(
        condition=text.endswith("""\

"""),
    )
