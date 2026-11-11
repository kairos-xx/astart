"""``astart fix --check`` reports clean, pending and missing inputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.__main__ import main

from tests.support.expectations import expect_equal

if TYPE_CHECKING:
    from pathlib import Path


def test_fix_check_exit_codes(tmp_path: Path) -> None:
    """Check 0 on a clean file, 1 on pending fixes, 2 on bad paths.

    ``--checker off`` keeps the result independent of whether a type
    checker is installed.

    Args:
        tmp_path (Path): pytest temporary directory.

    """
    clean: Path = tmp_path / "clean.py"
    clean.write_text(
        data="""\
x: int = 1
""",
        encoding="utf-8",
    )
    pending: Path = tmp_path / "pending.py"
    pending.write_text(
        data="""\
def f(a, b):
    pass

f(1, 2)
""",
        encoding="utf-8",
    )
    expect_equal(
        actual=main(
            argv=["fix", "--check", "--checker", "off", str(object=clean)],
        ),
        expected=0,
    )
    expect_equal(
        actual=main(
            argv=["fix", "--check", "--checker", "off", str(object=pending)],
        ),
        expected=1,
    )
    expect_equal(
        actual=main(
            argv=[
                "fix",
                "--check",
                "--checker",
                "off",
                str(object=tmp_path / "gone.py"),
            ],
        ),
        expected=2,
    )
    expect_equal(
        actual=main(
            argv=[
                "fix",
                "--check",
                "--checker",
                "off",
                str(object=tmp_path / "nodir" / "x.py"),
            ],
        ),
        expected=2,
    )
