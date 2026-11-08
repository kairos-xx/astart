"""``astart fix --source-root`` reaches the type checker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart.__main__ import main

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_source_roots_are_passed_to_the_checker(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that each ``--source-root`` is handed to ``build_checker``.

    Args:
        tmp_path: pytest temporary directory.
        monkeypatch: pytest monkeypatch fixture.

    """
    seen: list[tuple[Path, ...]] = []

    def fake(*, root: Path, source_roots: tuple[Path, ...] = ()) -> None:
        """Record the source roots ``build_checker`` receives.

        Args:
            root: Project root passed by the command.
            source_roots: Source roots passed by the command.

        """
        _ = root
        seen.append(source_roots)

    monkeypatch.setattr(target="astart.cli.commands.build_checker", name=fake)
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data="x = 1\n", encoding="utf-8")
    first, second = tmp_path / "a", tmp_path / "b"
    _ = main(
        argv=[
            "fix",
            "--check",
            "--source-root",
            str(object=first),
            "--source-root",
            str(object=second),
            str(object=target),
        ],
    )
    expect_equal(actual=seen, expected=[(first, second)])
