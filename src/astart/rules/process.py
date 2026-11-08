"""Run an external command and capture its output."""

from __future__ import annotations

from asyncio import create_subprocess_exec, run, timeout
from asyncio.subprocess import PIPE
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from os import environ
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import Mapping
    from pathlib import Path


@final
@dataclass(frozen=True, slots=True)
class Completed:
    """Raw outcome of an external command.

    Attributes:
        code: Exit status.
        stdout: Standard output text.
        stderr: Standard error text.

    """

    code: int
    stdout: str
    stderr: str


async def _spawn(
    *,
    arguments: tuple[str, ...],
    stdin: str,
    cwd: Path,
    limit: float,
    environment: Mapping[str, str] | None,
) -> Completed:
    """Run a command with text on standard input.

    Args:
        arguments: Argument vector.
        stdin: Text written to standard input.
        cwd: Working directory.
        limit: Seconds before the process is killed.
        environment: Variables added to the inherited environment.

    Returns:
        The exit status and captured output.

    Raises:
        TimeoutError: The command did not finish in time.

    """
    process: Process = await create_subprocess_exec(
        *arguments,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        cwd=cwd,
        env=None if environment is None else {**environ, **environment},
    )
    try:
        async with timeout(delay=limit):
            out, err = await process.communicate(input=stdin.encode())
    except TimeoutError:
        process.kill()
        _ = await process.wait()
        raise
    return Completed(
        code=process.returncode or 0,
        stdout=out.decode(),
        stderr=err.decode(),
    )


def run_command(
    *,
    arguments: tuple[str, ...],
    cwd: Path,
    stdin: str = "",
    timeout: float = 60.0,
    environment: Mapping[str, str] | None = None,
) -> Completed:
    """Run a command on a private event loop in a worker thread.

    A worker thread keeps this usable from code that already runs an event
    loop.

    Args:
        arguments: Argument vector.
        cwd: Working directory.
        stdin: Text written to standard input.
        timeout: Seconds before the process is killed.
        environment: Variables added to the inherited environment.

    Returns:
        The exit status and captured output.

    Raises:
        FileNotFoundError: The executable does not exist.
        TimeoutError: The command did not finish in time.

    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(
            run,
            _spawn(
                arguments=arguments,
                stdin=stdin,
                cwd=cwd,
                limit=timeout,
                environment=environment,
            ),
        ).result()
