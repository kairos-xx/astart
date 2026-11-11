"""Build the wheel and verify its contents and entry point.

Checks that the wheel ships the typed marker, the rule catalog data and
the stub package, then installs it into a fresh virtual environment and
runs ``astart rules``.

"""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from subprocess import run
from sys import executable, stderr, stdout
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, final
from zipfile import ZipFile

if TYPE_CHECKING:
    from subprocess import CompletedProcess


@final
class Constants:
    """Group module-level constants.

    Attributes:
        wheel_pattern (Final[str]): Glob matching the built wheel.
        catalog_prefix (Final[str]): Wheel path prefix of the rule catalog.
        required_members (Final[tuple[str, ...]]): Wheel members that must
            ship.
        min_rule_lines (Final[int]): Fewest lines a working ``astart rules``
            prints.

    """

    wheel_pattern: Final[str] = "*.whl"
    catalog_prefix: Final[str] = "astart/rules/artifacts/catalog/"
    required_members: Final[tuple[str, ...]] = (
        "astart/py.typed",
        "astart/rules/artifacts/schema.json",
        "astart/docstrings/artifacts/catalog.json",
        "astart/stubs/__init__.py",
        "astart/stubs/artifacts/typeshed/stdlib/VERSIONS",
    )
    min_rule_lines: Final[int] = 10


def _wheel_path(*, outdir: Path) -> Path:
    """Return the single wheel ``python -m build`` wrote.

    Args:
        outdir (Path): Directory the build wrote into.

    Returns:
        Path: Path of the built wheel.

    Raises:
        SystemExit: When the build output does not contain exactly one
            wheel.

    """
    wheels: list[Path] = sorted(outdir.glob(pattern=Constants.wheel_pattern))
    if len(wheels) != 1:
        msg: str = f"expected one wheel in {outdir}, found {wheels}"
        raise SystemExit(msg)
    return wheels[0]


def _check_members(*, wheel: Path) -> list[str]:
    """Return the wheel members that failed the content checks.

    Args:
        wheel (Path): Wheel archive to inspect.

    Returns:
        list[str]: Missing required members and a marker when no catalog JSON
            ships.

    """
    with ZipFile(file=wheel) as archive:
        names: set[str] = set(archive.namelist())
    problems: list[str] = [
        f"missing {member}"
        for member in Constants.required_members
        if member not in names
    ]
    if not any(name.startswith(Constants.catalog_prefix) for name in names):
        problems.append("no astart/rules/artifacts/catalog/*.json member")
    return problems


def _check_entry_point(*, wheel: Path, workdir: Path) -> list[str]:
    """Install the wheel in a venv and run ``astart rules``.

    Args:
        wheel (Path): Wheel archive to install.
        workdir (Path): Temporary directory for the virtual environment.

    Returns:
        list[str]: Problem descriptions; empty when the entry point works.

    """
    venv: Path = workdir / "venv"
    interpreter: str = executable
    built: CompletedProcess[str] = run(
        args=[interpreter, "-m", "venv", str(object=venv)],
        check=False,
        text=True,
        capture_output=True,
    )
    if built.returncode != 0:
        return [f"venv creation failed: {built.stderr.strip()}"]
    pip: Path = venv / "bin" / "pip"
    installed: CompletedProcess[str] = run(
        args=[str(object=pip), "install", "--no-index", str(object=wheel)],
        check=False,
        text=True,
        capture_output=True,
    )
    if installed.returncode != 0:
        return [f"pip install failed: {installed.stderr.strip()}"]
    astart: Path = venv / "bin" / "astart"
    done: CompletedProcess[str] = run(
        args=[str(object=astart), "rules"],
        check=False,
        text=True,
        capture_output=True,
    )
    problems: list[str] = []
    if done.returncode != 0:
        problems.append(f"astart rules exited {done.returncode}")
    elif len(done.stdout.splitlines()) <= Constants.min_rule_lines:
        problems.append(
            f"astart rules printed {Constants.min_rule_lines} lines or fewer",
        )
    return problems


def main() -> int:
    """Build the wheel and run both checks.

    Returns:
        int: Zero when the wheel is complete and its entry point works.

    """
    root: Path = Path(__file__).resolve().parent.parent.parent
    rmtree(path=root / "build", ignore_errors=True)
    with TemporaryDirectory() as tmp:
        workdir: Path = Path(tmp)
        built: CompletedProcess[str] = run(
            args=[
                executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(object=workdir),
            ],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
        if built.returncode != 0:
            _ = stderr.write(f"wheel build failed: {built.stderr}\n")
            return 1
        wheel: Path = _wheel_path(outdir=workdir)
        problems: list[str] = _check_members(wheel=wheel) + _check_entry_point(
            wheel=wheel,
            workdir=workdir,
        )
    if problems:
        for problem in problems:
            _ = stdout.write(f"{problem}\n")
        return 1
    _ = stdout.write("""\
wheel check passed
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
