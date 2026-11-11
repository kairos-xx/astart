"""Run all source-conversion comparisons and publish one report pair.

Usage: ``python scripts/compare [options]`` or ``python -m scripts.compare``.

"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from sys import path
from typing import Protocol, cast


class _EntryPoint(Protocol):
    """Command interface of the unified report producer."""

    def main(self) -> int:
        """Generate the report pair and update TODO information.

        Returns:
            Command exit status.

        """
        ...


def main() -> int:
    """Load the local source tree and run the shared comparison command.

    Returns:
        int: Report generator exit status.

    """
    root: Path = Path(__file__).resolve().parents[2]
    path.insert(0, str(object=root / "src"))
    path.insert(0, str(object=root))
    entry: _EntryPoint = cast(
        typ="_EntryPoint",
        val=import_module(name="scripts.compare.conversion_report"),
    )
    return entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
