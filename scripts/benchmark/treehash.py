"""Commit-independent hash of the ``astart`` source tree (task R-24).

Benchmark numbers are only meaningful next to the code that produced
them. ``tree_hash`` digests every ``src/astart`` Python file — path and
bytes — so two runs on the same tree agree regardless of git history,
while any source edit changes the stamp.

"""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from _hashlib import HASH
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source_dir (Final[str]): Package directory whose files are
            hashed, relative to the repository root.
        pattern (Final[str]): File pattern collected under the source
            directory.

    """

    source_dir: Final[str] = "src/astart"
    pattern: Final[str] = "**/*.py"


def tree_hash(*, root: Path) -> str:
    """Digest the ``src/astart`` tree under ``root``.

    Args:
        root (Path): Repository root containing ``src/astart``.

    Returns:
        str: A short SHA-256 hex digest over sorted ``(relative path, bytes)``
            pairs; empty string when the tree is absent.

    """
    base: Path = root / Constants.source_dir
    if not base.is_dir():
        return ""
    digest: HASH = sha256()
    for path in sorted(base.glob(pattern=Constants.pattern)):
        relative: str = path.relative_to(base).as_posix()
        digest.update(relative.encode(encoding="utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]
