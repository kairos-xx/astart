"""TODO dashboard, lint, status ledger and conversion comparison commands.

Usage: ``python -m scripts.todo_update`` runs every step in one pass —
the dashboard index, the status ledger render, the conversion comparison
and the lint audit. Pass ``--no-compare`` to skip the comparison.

Single tools remain available::

    python -m scripts.todo_update index docs/planning/TODO.md
    python -m scripts.todo_update lint
    python -m scripts.todo_update status render

Each tool also runs directly:
``python -m scripts.todo_update.todo_index docs/planning/TODO.md``.

"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from sys import argv, path, stderr, stdout
from typing import TYPE_CHECKING, Final, Protocol, cast, final

if TYPE_CHECKING:
    from types import ModuleType


@final
class Constants:
    """Shared command routing table.

    Attributes:
        tools (Final[dict[str, str]]): Subcommand name to module name.
        pipeline (Final[tuple[tuple[str, str, tuple[str, ...]], ...]]): Module
            and arguments for each step of the full run.
        usage (Final[str]): Help text shown for an unknown subcommand.

    """

    tools: Final[dict[str, str]] = {
        "index": "todo_index",
        "lint": "todo_lint",
        "status": "status_update",
    }
    pipeline: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
        (
            "index",
            "scripts.todo_update.todo_index",
            ("docs/planning/TODO.md",),
        ),
        ("status", "scripts.todo_update.status_update", ("render",)),
        ("compare", "scripts.compare.conversion_report", ()),
        ("lint", "scripts.todo_update.todo_lint", ()),
    )
    usage: Final[str] = (
        "usage: python -m scripts.todo_update [--no-compare]"
        " [index|lint|status] [arguments]"
    )


class _EntryPoint(Protocol):
    """Command interface of each TODO tool module."""

    def main(self) -> int:
        """Run the tool against ``sys.argv``.

        Returns:
            Command exit status.

        """
        ...


def _invoke(*, module: str, arguments: tuple[str, ...]) -> int:
    """Run one tool module with the given argument tail.

    Args:
        module (str): Dotted module name exposing ``main``.
        arguments (tuple[str, ...]): Arguments placed after the program name in
            ``sys.argv``.

    Returns:
        int: The tool's exit status.

    """
    entry: _EntryPoint = cast(
        typ="_EntryPoint",
        val=import_module(name=module),
    )
    argv[:] = [argv[0], *arguments]
    return entry.main()


def _run_all(*, run_compare: bool) -> int:
    """Run every pipeline step in order and report the worst status.

    Args:
        run_compare (bool): Whether the conversion comparison step is included.

    Returns:
        int: 1 when any step failed, otherwise 0.

    """
    failed: bool = False
    for name, module, arguments in Constants.pipeline:
        if name == "compare" and not run_compare:
            continue
        _ = stdout.write(f"== {name} ==\n")
        if _invoke(module=module, arguments=arguments) != 0:
            failed = True
    return 1 if failed else 0


def main() -> int:
    """Dispatch to the pipeline or a single TODO tool.

    Returns:
        int: Pipeline or tool exit status, or 2 for an unknown subcommand.

    """
    root: Path = Path(__file__).resolve().parents[2]
    path.insert(0, str(object=root / "src"))
    path.insert(0, str(object=root))
    raw: list[str] = argv[1:]
    run_compare: bool = "--no-compare" not in raw
    arguments: list[str] = [item for item in raw if item != "--no-compare"]
    if not arguments:
        return _run_all(run_compare=run_compare)
    tool: str = arguments[0]
    if tool not in Constants.tools:
        _ = stderr.write(f"{Constants.usage}\n")
        return 2
    module: ModuleType = import_module(
        name=f"scripts.todo_update.{Constants.tools[tool]}",
    )
    argv[:] = [argv[0], *arguments[1:]]
    return cast(typ="_EntryPoint", val=module).main()


if __name__ == "__main__":
    raise SystemExit(main())
