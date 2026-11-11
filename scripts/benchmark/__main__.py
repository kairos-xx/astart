"""Run the integrated benchmark harness: ``python -m scripts.benchmark``."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from sys import path
from typing import Protocol, cast


class _Command(Protocol):
    """Callable entry point loaded after local source bootstrapping."""

    def main(self) -> int:
        """Execute the selected benchmark.

        Returns:
            Benchmark exit status.

        """
        ...


def main() -> int:
    """Load repository sources and dispatch the benchmark command.

    Returns:
        int: Benchmark exit status.

    """
    root: Path = Path(__file__).resolve().parents[2]
    path.insert(0, str(object=root / "src"))
    path.insert(0, str(object=root))
    command: _Command = cast(
        typ="_Command",
        val=import_module(name="scripts.benchmark.cli"),
    )
    return command.main()


if __name__ == "__main__":
    raise SystemExit(main())
