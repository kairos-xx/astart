"""Guard: no new ``re`` imports in source-reading code (CC-08).

``src/astart`` must not read or rewrite Python source or comments with
regular expressions; decisions come from the AST, ``tokenize`` and ``str``
methods. ``tests/artifacts/regex_allowlist.txt`` lists the files that still do,
pending the CC-08 child tasks. A file leaves the list only when its last
``re`` import is gone — the second test fails on stale entries so the list
cannot silently rot.

"""

from ast import Import, ImportFrom, Module, parse, walk
from pathlib import Path
from typing import Final

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

REPO_ROOT: Final[Path] = Paths.root
SOURCE_ROOT: Final[Path] = REPO_ROOT / "src" / "astart"
ALLOWLIST_PATH: Final[Path] = (
    REPO_ROOT / "tests" / "artifacts" / "regex_allowlist.txt"
)
EXEMPT: Final[frozenset[str]] = frozenset({"rules/libkw.py"})


def _allowlist() -> set[str]:
    """Return the repo-relative paths allowed to import ``re``.

    Returns:
        set[str]: The allow-listed paths; blank lines and ``#`` comments
            skipped.

    """
    entries: set[str] = set()
    for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line: str = raw.strip()
        if line and not line.startswith("#"):
            entries.add(line)
    return entries


def _imports_re(path: Path) -> bool:
    """Return whether the module at ``path`` imports from ``re``.

    Args:
        path (Path): Python source file to parse.

    Returns:
        bool: True when an ``import re`` or ``from re import ...`` node exists.

    """
    tree: Module = parse(source=path.read_text(encoding="utf-8"))
    for node in walk(node=tree):
        if isinstance(node, Import) and any(
            alias.name == "re" or alias.name.startswith("re.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ImportFrom) and node.module == "re":
            return True
    return False


def _source_files() -> list[Path]:
    """Return every ``src/astart`` module except the exempt generated file.

    Returns:
        list[Path]: Sorted ``.py`` paths under ``src/astart``.

    """
    files: list[Path] = []
    for path in sorted(SOURCE_ROOT.rglob(pattern="*.py")):
        relative: str = path.relative_to(SOURCE_ROOT).as_posix()
        if relative not in EXEMPT:
            files.append(path)
    return files


def test_no_unlisted_re_imports() -> None:
    """Every ``re`` importer under ``src/astart`` is on the allow-list."""
    allowed: set[str] = _allowlist()
    offenders: list[str] = []
    for path in _source_files():
        relative: str = f"src/astart/{path.relative_to(SOURCE_ROOT)}"
        if _imports_re(path=path) and relative not in allowed:
            offenders.append(relative)
    expect_equal(
        actual=offenders,
        expected=[],
        message=(
            "new `re` imports in source-reading code; use the AST, "
            "tokenize or str methods instead (CC-08)"
        ),
    )


def test_allowlist_entries_are_live() -> None:
    """Every allow-listed path exists and still imports ``re``."""
    stale: list[str] = []
    for entry in sorted(_allowlist()):
        path: Path = REPO_ROOT / entry
        if not path.is_file() or not _imports_re(path=path):
            stale.append(entry)
    expect_equal(
        actual=stale,
        expected=[],
        message=(
            "allow-list entries no longer import `re`; remove them from "
            "tests/artifacts/regex_allowlist.txt"
        ),
    )
