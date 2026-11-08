"""Formatter phase: run ruff once on the final text."""

from __future__ import annotations

from dataclasses import dataclass
from shutil import which
from sys import executable
from typing import TYPE_CHECKING, Final, final

from astart.rules.process import Completed, run_command
from astart.rules.runner import fix_source

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.model import Catalog
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult, FixSettings


@final
class Constants:
    """Group module-level constants.

    Attributes:
        timeout_seconds: Grouped module constant.
        executable_name: Grouped module constant.

    """

    timeout_seconds: Final[int] = 30
    executable_name: Final[str] = "ruff"


@final
@dataclass(frozen=True, slots=True)
class FormatTarget:
    """Where a file lives, for formatting purposes.

    Attributes:
        filename: Name passed to ruff for configuration and rule lookup.
        cwd: Directory ruff runs in, so project configuration applies.

    """

    filename: str
    cwd: Path


@final
@dataclass(frozen=True, slots=True)
class FormatOutcome:
    """Result of the formatter phase.

    Attributes:
        source: The formatted text, or the input when nothing was done.
        formatted: Whether ruff ran successfully.
        note: Why nothing was formatted, empty on success.

    """

    source: str
    formatted: bool
    note: str


def _command(*, filename: str) -> tuple[str, ...]:
    """Resolve how to invoke ruff.

    Args:
        filename: Name ruff uses to pick configuration and rules.

    Returns:
        The argument vector.

    """
    found: str | None = which(cmd=Constants.executable_name)
    base: tuple[str, ...] = (
        (found,) if found else (executable, "-m", Constants.executable_name)
    )
    return (*base, "format", "--stdin-filename", filename, "-")


def format_source(
    *,
    source: str,
    target: FormatTarget,
    command: tuple[str, ...] | None = None,
) -> FormatOutcome:
    """Format a source text with a single ruff invocation.

    Args:
        source: Python source text.
        target: File name and working directory for ruff.
        command: Argument vector override; ``None`` resolves ruff.

    Returns:
        The formatted text, or the input with a note when ruff is missing,
        fails, or times out.

    """
    arguments: tuple[str, ...] = command or _command(filename=target.filename)
    try:
        completed: Completed = run_command(
            arguments=arguments,
            cwd=target.cwd,
            stdin=source,
            timeout=Constants.timeout_seconds,
        )
    except FileNotFoundError:
        return FormatOutcome(
            source=source,
            formatted=False,
            note=(f"{arguments[0]} not found"),
        )
    except TimeoutError:
        return FormatOutcome(
            source=source,
            formatted=False,
            note=(f"ruff timed out after {Constants.timeout_seconds}s"),
        )
    if completed.code != 0:
        detail: str = (completed.stderr or completed.stdout).strip()
        return FormatOutcome(
            source=source,
            formatted=False,
            note=detail.splitlines()[0] if detail else "ruff failed",
        )
    return FormatOutcome(source=completed.stdout, formatted=True, note="")


def fix_and_format(
    *,
    source: str,
    target: FormatTarget,
    catalog: Catalog,
    registries: Registries,
    settings: FixSettings,
) -> tuple[FixResult, FormatOutcome]:
    """Fix a file, then format the result once.

    Args:
        source: Python source text.
        target: File name and working directory.
        catalog: Rules and fixes.
        registries: Declared vocabulary.
        settings: Safety ceiling and options.

    Returns:
        The fix result and the formatter outcome for its final source.

    """
    fixed: FixResult = fix_source(
        source=source,
        filename=target.filename,
        catalog=catalog,
        registries=registries,
        settings=settings,
    )
    if fixed.parse_error is not None:
        return (
            fixed,
            FormatOutcome(
                source=fixed.source,
                formatted=False,
                note=fixed.parse_error,
            ),
        )
    return (fixed, format_source(source=fixed.source, target=target))
