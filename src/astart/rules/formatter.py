"""Formatter phase: run ruff once on the final text."""

from __future__ import annotations

from dataclasses import dataclass
from shutil import which
from sys import executable
from typing import TYPE_CHECKING, Final, final

from astart.rules.process import Completed, run_command
from astart.rules.runner import FixResult, fix_source

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.model import Catalog, Finding
    from astart.rules.registry import Registries
    from astart.rules.runner import (
        AppliedFix,
        FixSettings,
        SkippedFix,
    )


@final
class Constants:
    """Group module-level constants.

    Attributes:
        timeout_seconds (Final[int]): Grouped module constant.
        executable_name (Final[str]): Grouped module constant.
        max_format_iterations (Final[int]): TODO.

    """

    timeout_seconds: Final[int] = 30
    executable_name: Final[str] = "ruff"
    max_format_iterations: Final[int] = 4


@final
@dataclass(frozen=True, slots=True)
class FormatTarget:
    """Where a file lives, for formatting purposes.

    Attributes:
        filename (str): Name passed to ruff for configuration and rule lookup.
        cwd (Path): Directory ruff runs in, so project configuration applies.

    """

    filename: str
    cwd: Path


@final
@dataclass(frozen=True, slots=True)
class FormatOutcome:
    """Result of the formatter phase.

    Attributes:
        source (str): The formatted text, or the input when nothing was done.
        formatted (bool): Whether ruff ran successfully.
        note (str): Why nothing was formatted, empty on success.

    """

    source: str
    formatted: bool
    note: str


def _command(*, filename: str) -> tuple[str, ...]:
    """Resolve how to invoke ruff.

    Args:
        filename (str): Name ruff uses to pick configuration and rules.

    Returns:
        tuple[str, ...]: The argument vector.

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
        source (str): Python source text.
        target (FormatTarget): File name and working directory for ruff.
        command (tuple[str, ...] | None): Argument vector override; ``None``
            resolves ruff.

    Returns:
        FormatOutcome: The formatted text, or the input with a note
            when ruff is missing, fails, or times out.

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
    """Fix and format until the pair reaches a fixed point.

    Formatting can expose fixes the unformatted text hid, so a single
    fix-then-format pass is not always a fixed point. Each iteration feeds
    the formatted text back through ``fix_source`` and stops once formatting
    reproduces its input.

    Args:
        source (str): Python source text.
        target (FormatTarget): File name and working directory.
        catalog (Catalog): Rules and fixes.
        registries (Registries): Declared vocabulary.
        settings (FixSettings): Safety ceiling and options.

    Returns:
        tuple[FixResult, FormatOutcome]: The accumulated fix result and the
            formatter outcome for its final source.

    """
    fixed: FixResult = fix_source(
        source=source,
        filename=target.filename,
        catalog=catalog,
        registries=registries,
        settings=settings,
    )
    applied: list[AppliedFix] = list(fixed.applied)
    skipped: tuple[SkippedFix, ...] = fixed.skipped
    remaining: tuple[Finding, ...] = fixed.remaining
    rounds: int = fixed.rounds
    outcome: FormatOutcome
    if fixed.parse_error is not None:
        return (
            FixResult(
                source=fixed.source,
                applied=tuple(applied),
                skipped=skipped,
                remaining=remaining,
                parse_error=fixed.parse_error,
                rounds=rounds,
            ),
            FormatOutcome(
                source=fixed.source,
                formatted=False,
                note=fixed.parse_error,
            ),
        )
    outcome = format_source(source=fixed.source, target=target)
    text: str = source
    for _ in range(1, Constants.max_format_iterations):
        if not outcome.formatted or outcome.source == text:
            break
        text = outcome.source
        fixed = fix_source(
            source=text,
            filename=target.filename,
            catalog=catalog,
            registries=registries,
            settings=settings,
        )
        applied.extend(fixed.applied)
        skipped = fixed.skipped
        remaining = fixed.remaining
        rounds += fixed.rounds
        if fixed.parse_error is not None:
            return (
                FixResult(
                    source=fixed.source,
                    applied=tuple(applied),
                    skipped=skipped,
                    remaining=remaining,
                    parse_error=fixed.parse_error,
                    rounds=rounds,
                ),
                FormatOutcome(
                    source=fixed.source,
                    formatted=False,
                    note=fixed.parse_error,
                ),
            )
        outcome = format_source(source=fixed.source, target=target)
    return (
        FixResult(
            source=fixed.source,
            applied=tuple(applied),
            skipped=skipped,
            remaining=remaining,
            parse_error=fixed.parse_error,
            rounds=rounds,
        ),
        outcome,
    )
