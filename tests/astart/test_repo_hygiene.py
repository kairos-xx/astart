"""Repository hygiene: no generated paths or oversized files are tracked."""

from __future__ import annotations

from json import loads
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING, Final, final

import pytest

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Shared fixtures for the repository hygiene checks.

    Attributes:
        root (Final[Path]): Repository root directory.
        forbidden (Final[tuple[str, ...]]): Path prefixes that must never be
            tracked.
        max_bytes (Final[int]): Largest allowed tracked file size.
        rev_parse (Final[tuple[str, ...]]): Read-only git probe proving a work
            tree.

    """

    root: Final[Path] = Paths.root
    forbidden: Final[tuple[str, ...]] = (
        "__pycache__",
        ".coverage",
        ".ruff_cache",
        ".pytest_cache",
        "EXACTUS_RESULTS",
        ".remember",
        ".history",
        "dist",
    )
    max_bytes: Final[int] = 5 * 1024 * 1024
    rev_parse: Final[tuple[str, ...]] = ("rev-parse", "--is-inside-work-tree")


def _git(*, args: tuple[str, ...]) -> CompletedProcess[str]:
    """Run a read-only git command at the repository root.

    Args:
        args (tuple[str, ...]): Git arguments after ``git``.

    Returns:
        CompletedProcess[str]: The completed process.

    """
    return run(
        args=["git", *args],
        cwd=Constants.root,
        capture_output=True,
        text=True,
        check=False,
    )


def _is_git_repo() -> bool:
    """Check whether the root sits inside a git work tree.

    Returns:
        bool: True when ``git rev-parse`` reports a work tree.

    """
    try:
        probe: CompletedProcess[str] = _git(args=Constants.rev_parse)
    except OSError:
        return False
    return probe.returncode == 0 and probe.stdout.strip() == "true"


def _tracked_files() -> list[str]:
    """List the paths git tracks at the repository root.

    Returns:
        list[str]: Tracked paths, one per line of ``git ls-files``.

    """
    listing: CompletedProcess[str] = _git(args=("ls-files",))
    expect_equal(actual=listing.returncode, expected=0)
    return listing.stdout.splitlines()


def _forbidden_hit(*, path: str) -> str | None:
    """Return the forbidden prefix covering ``path``, if any.

    Args:
        path (str): A tracked path from ``git ls-files``.

    Returns:
        str | None: The matching prefix or ``None``.

    """
    for prefix in Constants.forbidden:
        if path == prefix or path.startswith(
            (f"{prefix}/", f"{prefix}."),
        ):
            return prefix
    return None


def _size_of(*, path: str) -> int:
    """Return the byte size of a tracked file, or zero when absent.

    Args:
        path (str): A tracked path from ``git ls-files``.

    Returns:
        int: File size in bytes.

    """
    target: Path = Constants.root / path
    return target.stat().st_size if target.is_file() else 0


pytestmark: pytest.MarkDecorator = pytest.mark.skipif(
    condition=not _is_git_repo(),
    reason="not a git work tree",
)


def test_generated_paths_stay_untracked() -> None:
    """Generated and cache paths are absent from ``git ls-files``."""
    offenders: list[str] = []
    for path in _tracked_files():
        hit: str | None = _forbidden_hit(path=path)
        if hit is not None:
            offenders.append(f"{path} matches {hit}")
    expect_equal(actual=offenders, expected=[])


def test_no_tracked_file_over_five_megabytes() -> None:
    """No tracked file exceeds the size budget."""
    oversized: list[str] = [
        f"{path} ({size} bytes)"
        for path in _tracked_files()
        if (size := _size_of(path=path)) > Constants.max_bytes
    ]
    expect_equal(actual=oversized, expected=[])


def test_every_corpus_distribution_has_a_licence() -> None:
    """Each ``tests/corpus/extended`` distribution has a ``LICENSES`` entry."""
    corpus: Path = Constants.root / "tests" / "corpus" / "extended"
    manifest: Path = corpus / "MANIFEST.json"
    entries: list[dict[str, str]] = loads(
        s=manifest.read_text(encoding="utf-8"),
    )
    distributions: set[str] = {entry["distribution"] for entry in entries}
    missing: list[str] = sorted(
        name
        for name in distributions
        if not (corpus / "LICENSES" / f"{name}.txt").is_file()
    )
    expect_equal(actual=missing, expected=[])
