"""External type-checker gate: reject fixes that make the checker unhappy."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from os import pathsep
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from tomllib import TOMLDecodeError
from tomllib import loads as load_toml
from typing import Final, Protocol, cast, final

from astart.rules.environment import (
    Environment,
    absolutize_relative_imports,
    detect_environment,
)
from astart.rules.process import Completed, run_command

type Json = str | int | float | bool | None | list[Json] | dict[str, Json]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        executables (Final[tuple[str, ...]]): Pyright-compatible executables,
            preferred first.
        mypy_executable (Final[str]): Fallback executable.
        mypy_flags (Final[tuple[str, ...]]): Flags that make mypy print one
            JSON object per error.
        timeout_seconds (Final[float]): Seconds a checker run may take.
        error (Final[str]): Severity that counts as a regression.
        scratch_prefix (Final[str]): Prefix of the transient file written
            beside a source.
        scratch_alias (Final[str]): Stable stand-in for the scratch module's
            name in
            messages, so identical errors compare equal across texts.
        pyright_config (Final[str]): Pyright's own configuration file name.
        pyproject (Final[str]): File that may hold ``[tool.pyright]``.
        path_keys (Final[frozenset[str]]): Pyright settings whose relative
            paths are re-based onto
            the project root when the configuration is copied.
        incomplete_prefix (Final[str]): Rule prefix of strict-mode "partially
            unknown" reports;
            they name missing information, not a wrong type, and their
            text quotes signatures that fixes legitimately change.

    """

    executables: Final[tuple[str, ...]] = ("basedpyright", "pyright")
    mypy_executable: Final[str] = "mypy"
    mypy_flags: Final[tuple[str, ...]] = (
        "--output",
        "json",
        "--no-error-summary",
        "--no-color-output",
        "--hide-error-context",
    )
    timeout_seconds: Final[float] = 120.0
    error: Final[str] = "error"
    scratch_prefix: Final[str] = "astart_check_"
    scratch_alias: Final[str] = "astart_check"
    incomplete_prefix: Final[str] = "reportUnknown"
    pyright_config: Final[str] = "pyrightconfig.json"
    pyproject: Final[str] = "pyproject.toml"
    path_keys: Final[frozenset[str]] = frozenset(
        {"venvPath", "stubPath", "typeshedPath"},
    )


class Checker(Protocol):
    """Something that can veto a change to a source file."""

    def regresses(self, *, filename: str, before: str, after: str) -> bool:
        """Tell whether ``after`` is worse than ``before`` for the checker.

        Args:
            filename (str): Path of the file the texts belong to.
            before (str): Original source text.
            after (str): Changed source text.

        Returns:
            ``True`` when the change introduces a new error, or when the
                checker could not give an answer.

        """
        ...


@final
@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One checker error, without its position.

    Attributes:
        rule (str): Checker rule name, empty when the checker gives none.
        message (str): Error message.

    """

    rule: str
    message: str


def detect_checker() -> tuple[str, ...] | None:
    """Find an installed pyright-compatible checker.

    Returns:
        tuple[str, ...] | None:
            The argument vector prefix, or ``None`` when none is installed.

    """
    for name in Constants.executables:
        found: str | None = which(cmd=name)
        if found is not None:
            return (found,)
    return None


class _CommandChecker:
    """Compare a command-line type checker's errors before and after."""

    def __init__(
        self,
        *,
        command: tuple[str, ...],
        root: Path,
        source_roots: tuple[Path, ...] = (),
    ) -> None:
        """Remember how to run the checker.

        Args:
            command (tuple[str, ...]): Argument vector prefix of the checker.
            root (Path): Directory the checker runs in, for its configuration.
            source_roots (tuple[Path, ...]): Extra directories absolute imports
                resolve from.

        """
        self._command: tuple[str, ...] = command
        self._root: Path = root
        self._source_roots: tuple[Path, ...] = source_roots
        self._cache: dict[tuple[str, str], Counter[Diagnostic] | None] = {}

    def regresses(self, *, filename: str, before: str, after: str) -> bool:
        """Tell whether a change adds an error the original did not have.

        Args:
            filename (str): Path of the file the texts belong to.
            before (str): Original source text.
            after (str): Changed source text.

        Returns:
            bool: ``True`` for a new error, or when
                either run produced no answer.

        """
        old: Counter[Diagnostic] | None = self._diagnostics(
            filename=filename,
            text=before,
        )
        new: Counter[Diagnostic] | None = self._diagnostics(
            filename=filename,
            text=after,
        )
        if old is None or new is None:
            return True
        return bool(new - old)

    def _diagnostics(
        self,
        *,
        filename: str,
        text: str,
    ) -> Counter[Diagnostic] | None:
        """Run the checker on a text, with a cache by content.

        Args:
            filename (str): Path of the file the text belongs to.
            text (str): Source text.

        Returns:
            Counter[Diagnostic] | None:
                The errors found, or ``None`` when the checker failed.

        """
        key: tuple[str, str] = (
            filename,
            sha256(data=text.encode()).hexdigest(),
        )
        if key not in self._cache:
            self._cache[key] = self._run(filename=filename, text=text)
        return self._cache[key]

    def _run(
        self,
        *,
        filename: str,
        text: str,
    ) -> Counter[Diagnostic] | None:
        """Write the text beside the file, check it, and clean up.

        Args:
            filename (str): Path of the file the text belongs to.
            text (str): Source text.

        Returns:
            Counter[Diagnostic] | None:
                The errors found, or ``None`` when the checker failed.

        """
        environment: Environment = detect_environment(
            file=Path(filename),
            project=self._root,
            source_roots=self._source_roots,
        )
        checked: str = absolutize_relative_imports(
            source=text,
            package=environment.package,
        )
        try:
            with TemporaryDirectory(prefix=Constants.scratch_prefix) as made:
                staging: Path = Path(made)
                digest: str = sha256(data=text.encode()).hexdigest()[:12]
                scratch: Path = (
                    staging / f"{Constants.scratch_prefix}{digest}.py"
                )
                _ = scratch.write_text(data=checked, encoding="utf-8")
                completed: Completed = run_command(
                    arguments=(
                        *self._command,
                        *self._flags(),
                        *self._stage(staging=staging, roots=environment.roots),
                        str(object=scratch),
                    ),
                    cwd=self._root,
                    timeout=Constants.timeout_seconds,
                    environment=self._environment(roots=environment.roots),
                )
        except (OSError, TimeoutError):
            return None
        found: Counter[Diagnostic] | None = self._read(completed=completed)
        if found is None:
            return None
        renamed: Counter[Diagnostic] = Counter()
        for diagnostic, count in found.items():
            if diagnostic.rule.startswith(Constants.incomplete_prefix):
                continue
            renamed[
                Diagnostic(
                    rule=diagnostic.rule,
                    message=diagnostic.message.replace(
                        scratch.stem,
                        Constants.scratch_alias,
                    ),
                )
            ] += count
        return renamed

    def _stage(
        self,
        *,
        staging: Path,
        roots: tuple[Path, ...],
    ) -> tuple[str, ...]:
        """Prepare the scratch directory so imports resolve as for the file.

        Args:
            staging (Path): Temporary directory holding the scratch file.
            roots (tuple[Path, ...]): Directories absolute imports are resolved
                from.

        Returns:
            tuple[str, ...]: Extra flags placed before the scratch file's name.

        """
        _: tuple[Path, tuple[Path, ...]] = (staging, roots)
        return ()

    def _environment(
        self,
        *,
        roots: tuple[Path, ...],
    ) -> dict[str, str] | None:
        """Give the variables the checker needs to find the project's modules.

        Args:
            roots (tuple[Path, ...]): Directories absolute imports are resolved
                from.

        Returns:
            Variables added to the inherited environment, or ``None``.

        """
        _: tuple[Path, ...] = roots
        return None

    def _flags(self) -> tuple[str, ...]:
        """Give the flags that make the checker print machine output.

        Returns:
            The flags placed before the file name.

        Raises:
            NotImplementedError: Always; subclasses provide them.

        """
        raise NotImplementedError

    def _read(self, *, completed: Completed) -> Counter[Diagnostic] | None:
        """Read the errors out of a finished run.

        Args:
            completed (Completed): The checker's exit status and output.

        Returns:
            The errors, or ``None`` when the output is unusable.

        Raises:
            NotImplementedError: Always; subclasses provide the parser.

        """
        raise NotImplementedError

    def new_errors(
        self,
        *,
        filename: str,
        before: str,
        after: str,
    ) -> int | None:
        """Count the errors a change adds.

        Args:
            filename (str): Path of the file the texts belong to.
            before (str): Original source text.
            after (str): Changed source text.

        Returns:
            int | None: How many errors ``after`` has that ``before`` lacks,
                or ``None`` when either run produced no answer.

        """
        old: Counter[Diagnostic] | None = self._diagnostics(
            filename=filename,
            text=before,
        )
        new: Counter[Diagnostic] | None = self._diagnostics(
            filename=filename,
            text=after,
        )
        if old is None or new is None:
            return None
        return sum((new - old).values())


@final
class PyrightChecker(_CommandChecker):
    """Compare pyright (or basedpyright) errors before and after a change."""

    def _stage(
        self,
        *,
        staging: Path,
        roots: tuple[Path, ...],
    ) -> tuple[str, ...]:
        """Write a project file that sees the file's import roots.

        The project's own pyright settings are kept, so the verdict matches
        what the user's checker would say about the real file.

        Args:
            staging (Path): Temporary directory holding the scratch file.
            roots (tuple[Path, ...]): Directories absolute imports are resolved
                from.

        Returns:
            tuple[str, ...]: ``--project`` pointing at the generated
                configuration.

        """
        settings: dict[str, Json] = _project_settings(root=self._root)
        paths: list[Json] = [str(object=root) for root in roots]
        existing: Json = settings.get("extraPaths")
        if isinstance(existing, list):
            paths = [*existing, *paths]
        settings["extraPaths"] = paths
        config: Path = staging / Constants.pyright_config
        _ = config.write_text(data=dumps(obj=settings), encoding="utf-8")
        return ("--project", str(object=config))

    def _flags(self) -> tuple[str, ...]:
        """Ask pyright for JSON and errors only.

        Returns:
            tuple[str, ...]: The flags placed before the file name.

        """
        return ("--outputjson", "--level", Constants.error)

    def _read(self, *, completed: Completed) -> Counter[Diagnostic] | None:
        """Read pyright's JSON report from stdout, or stderr.

        Args:
            completed (Completed): The checker's exit status and output.

        Returns:
            Counter[Diagnostic] | None:
                The errors, or ``None`` when the output is unusable.

        """
        parsed: Counter[Diagnostic] | None = _parse(output=completed.stdout)
        return (
            parsed if parsed is not None else _parse(output=completed.stderr)
        )


@final
class MypyChecker(_CommandChecker):
    """Compare mypy errors before and after a change."""

    def _environment(
        self,
        *,
        roots: tuple[Path, ...],
    ) -> dict[str, str] | None:
        """Let mypy find the project's modules.

        Args:
            roots (tuple[Path, ...]): Directories absolute imports are resolved
                from.

        Returns:
            dict[str, str] | None: ``MYPYPATH`` naming those directories.

        """
        return {"MYPYPATH": pathsep.join(str(object=root) for root in roots)}

    def _flags(self) -> tuple[str, ...]:
        """Ask mypy for one JSON object per error.

        Returns:
            tuple[str, ...]: The flags placed before the file name.

        """
        return Constants.mypy_flags

    def _read(self, *, completed: Completed) -> Counter[Diagnostic] | None:
        """Read mypy's JSON lines.

        Args:
            completed (Completed): The checker's exit status and output.

        Returns:
            Counter[Diagnostic] | None:
                The errors, or ``None`` when a line is not JSON.

        """
        return parse_mypy(output=completed.stdout)


def parse_mypy(*, output: str) -> Counter[Diagnostic] | None:
    """Read the error diagnostics from ``mypy --output json``.

    Args:
        output (str): Standard output, one JSON object per line.

    Returns:
        Counter[Diagnostic] | None: The errors counted by code and message,
            or ``None`` for a line that is not JSON.

    """
    found: Counter[Diagnostic] = Counter()
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            item: dict[str, str] = loads(s=line)
            severity: str = item["severity"]
            message: str = item["message"]
        except (JSONDecodeError, KeyError, TypeError):
            return None
        if severity == Constants.error:
            found[
                Diagnostic(rule=item.get("code") or "", message=message)
            ] += 1
    return found


def _project_settings(*, root: Path) -> dict[str, Json]:
    """Read the project's pyright settings, re-basing relative paths.

    Args:
        root (Path): Directory the checker runs in.

    Returns:
        dict[str, Json]: The settings of ``pyrightconfig.json`` or
            ``[tool.pyright]``
            ; empty when there are none or they cannot be read.

    """
    settings: dict[str, Json] = {}
    config: Path = root / Constants.pyright_config
    project: Path = root / Constants.pyproject
    try:
        if config.is_file():
            settings = {"extends": str(object=config.resolve())}
        elif project.is_file():
            table: dict[str, Json] = cast(
                typ="dict[str, Json]",
                val=load_toml(project.read_text(encoding="utf-8")),
            )
            tool: Json = table.get("tool")
            found: Json = (
                tool.get("pyright") if isinstance(tool, dict) else None
            )
            if isinstance(found, dict):
                settings = dict(found)
    except (OSError, TOMLDecodeError, JSONDecodeError):
        return {}
    for key in Constants.path_keys & settings.keys():
        value: Json = settings[key]
        if isinstance(value, str):
            settings[key] = str(object=(root / value).resolve())
    for key in ("include", "exclude", "ignore", "strict"):
        _ = settings.pop(key, None)
    return settings


def build_checker(
    *,
    root: Path,
    source_roots: tuple[Path, ...] = (),
) -> PyrightChecker | MypyChecker | None:
    """Create the best installed checker.

    Args:
        root (Path): Directory the checker runs in, for its configuration.
        source_roots (tuple[Path, ...]): Extra directories absolute imports
            resolve from.

    Returns:
        PyrightChecker | MypyChecker | None:
            A pyright-compatible checker when one is
            installed, otherwise mypy, otherwise ``None``.

    """
    command: tuple[str, ...] | None = detect_checker()
    if command is not None:
        return PyrightChecker(
            command=command,
            root=root,
            source_roots=source_roots,
        )
    found: str | None = which(cmd=Constants.mypy_executable)
    return (
        None
        if found is None
        else MypyChecker(
            command=(found,),
            root=root,
            source_roots=source_roots,
        )
    )


def _parse(*, output: str) -> Counter[Diagnostic] | None:
    """Read the error diagnostics from pyright's JSON output.

    Args:
        output (str): Standard output of ``pyright --outputjson``.

    Returns:
        Counter[Diagnostic] | None:
            The errors counted by rule and message, or ``None`` for bad output.

    """
    try:
        document: dict[str, list[dict[str, str]]] = cast(
            typ="dict[str, list[dict[str, str]]]",
            val=loads(s=output),
        )
        items: list[dict[str, str]] = document["generalDiagnostics"]
    except (JSONDecodeError, KeyError, TypeError):
        return None
    return Counter(
        Diagnostic(rule=item.get("rule", ""), message=item["message"])
        for item in items
        if item.get("severity") == Constants.error
    )
