"""Load the ``[tool.astart]`` table of a ``pyproject.toml``.

The loader resolves ``select``/``ignore`` rule selections, path
``exclude`` patterns, per-path ``overrides``, a safety ceiling, a target
version, rule ``params`` and extra library tables into one immutable
:class:`AstartConfig`.  It is deliberately not wired into the CLI yet;
callers build settings from :func:`effective` and expand named profiles
through :func:`astart.cli.ignores.resolve`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time
from fnmatch import fnmatch
from re import fullmatch
from tomllib import load as toml_load
from typing import TYPE_CHECKING, Final, final

from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from astart.rules.predicate import FactValue


def _no_params() -> dict[str, FactValue]:
    """Build the empty params mapping.

    Returns:
        An empty dict typed for ``Selection.params``.

    """
    return {}


type TomlScalar = str | int | float | bool | date | datetime | time
type TomlValue = (
    TomlScalar | list[TomlValue] | dict[str, TomlValue] | tuple[TomlValue, ...]
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        pyproject: The file the loader searches upward for.
        section: Dotted path inside ``tool`` for this tool's table.
        scalar_keys: Allowed scalar keys of ``[tool.astart]``.
        list_keys: Allowed string-list keys of ``[tool.astart]``.
        table_keys: Allowed sub-table keys of ``[tool.astart]``.
        override_scalar_keys: Allowed scalar keys of an override table.
        override_list_keys: Allowed string-list keys of an override table.

    """

    pyproject: Final[str] = "pyproject.toml"
    section: Final[tuple[str, str]] = ("tool", "astart")
    scalar_keys: Final[frozenset[str]] = frozenset(
        {
            "profile",
            "min-confidence",
            "checker",
            "safety-ceiling",
            "target-version",
        },
    )
    list_keys: Final[frozenset[str]] = frozenset(
        {"select", "ignore", "exclude", "library-tables"},
    )
    table_keys: Final[frozenset[str]] = frozenset({"params"})
    override_scalar_keys: Final[frozenset[str]] = frozenset(
        {"profile", "min-confidence", "safety-ceiling", "target-version"},
    )
    override_list_keys: Final[frozenset[str]] = frozenset(
        {"select", "ignore"},
    )


@final
class ConfigError(ValueError):
    """Raised when ``[tool.astart]`` exists but is malformed."""


@final
@dataclass(frozen=True, slots=True)
class Selection:
    """Rule selection shared by the root table and each override.

    Attributes:
        select: Codes or prefixes to include; empty means all.
        ignore: Codes or prefixes to exclude after selection.
        profile: Catalog profile key, or ``None`` for the default.
        min_confidence: Offer floor, or ``None`` to use the command's.
        safety_ceiling: Highest fix safety applied automatically, or
            ``None`` to defer to the profile or the command's default.
        target_version: Python version rules should target, or ``None``.
        params: Rule parameter overrides, merged over catalog and
            profile parameters; later overrides win per key.

    """

    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    profile: str | None = None
    min_confidence: float | None = None
    safety_ceiling: FixSafety | None = None
    target_version: str | None = None
    params: Mapping[str, FactValue] = field(default_factory=_no_params)

    def selected(self, *, code: str) -> bool:
        """Answer whether a rule code survives select and ignore.

        Args:
            code: Rule or fix code or key to test.

        Returns:
            ``True`` when the code is selected and not ignored.

        """
        if self.select and not _matches_any(code=code, prefixes=self.select):
            return False
        return not _matches_any(code=code, prefixes=self.ignore)


@final
@dataclass(frozen=True, slots=True)
class PathOverride:
    """A ``[tool.astart.overrides.<pattern>]`` table.

    Attributes:
        pattern: ``fnmatch``-style path pattern, relative to the
            pyproject directory.
        selection: The overrides that apply to matching paths.

    """

    pattern: str
    selection: Selection


@final
@dataclass(frozen=True, slots=True)
class AstartConfig:
    """The resolved ``[tool.astart]`` table.

    Attributes:
        root: Directory containing the ``pyproject.toml``.
        selection: Root selection and defaults.
        exclude: Path patterns the CLI should skip during discovery.
        overrides: Per-path tables, in file order; later wins.
        checker: Checker mode string, or ``None`` for the default.
        library_tables: Extra signature-table files rules may consult,
            relative to the pyproject directory.

    """

    root: Path
    selection: Selection
    exclude: tuple[str, ...] = ()
    overrides: tuple[PathOverride, ...] = ()
    checker: str | None = None
    library_tables: tuple[str, ...] = ()


def find_pyproject(*, start: Path) -> Path | None:
    """Walk upward from ``start`` for a ``pyproject.toml``.

    Args:
        start: File or directory the search begins at.

    Returns:
        The found file, or ``None``.

    """
    directory: Path = start if start.is_dir() else start.parent
    for ancestor in (directory, *directory.parents):
        candidate: Path = ancestor / Constants.pyproject
        if candidate.is_file():
            return candidate
    return None


def load_config(*, path: Path) -> AstartConfig | None:
    """Parse ``[tool.astart]`` from a ``pyproject.toml``.

    Args:
        path: The ``pyproject.toml`` to read.

    Returns:
        The config, or ``None`` when the file has no table.

    Raises:
        ConfigError: If a present table is malformed.

    """
    with path.open(mode="rb") as handle:
        document: dict[str, TomlValue] = toml_load(handle)
    tool: TomlValue | None = document.get(Constants.section[0])
    table: TomlValue | None = (
        tool.get(Constants.section[1]) if isinstance(tool, dict) else None
    )
    if table is None:
        return None
    if not isinstance(table, dict):
        msg: str = f"{Constants.section[1]} must be a table"
        raise ConfigError(msg)
    unknown: frozenset[str] = (
        frozenset(table)
        - Constants.scalar_keys
        - Constants.list_keys
        - Constants.table_keys
        - {"overrides"}
    )
    if unknown:
        msg = f"unknown [tool.astart] keys: {sorted(unknown)}"
        raise ConfigError(msg)
    selection: Selection = _selection(
        table=table,
        list_keys=Constants.list_keys - {"exclude"},
        where="[tool.astart]",
    )
    checker: TomlValue | None = table.get("checker")
    if checker is not None and not isinstance(checker, str):
        msg = "[tool.astart] checker must be a string"
        raise ConfigError(msg)
    overrides: tuple[PathOverride, ...] = _overrides(
        table=table.get("overrides"),
    )
    return AstartConfig(
        root=path.parent,
        selection=selection,
        exclude=_string_list(
            table=table,
            key="exclude",
            where="[tool.astart]",
        ),
        overrides=overrides,
        checker=checker if isinstance(checker, str) else None,
        library_tables=_string_list(
            table=table,
            key="library-tables",
            where="[tool.astart]",
        ),
    )


def load_project(*, start: Path) -> AstartConfig | None:
    """Find and load the nearest ``pyproject.toml`` config.

    Args:
        start: File or directory the search begins at.

    Returns:
        The config, or ``None`` when none exists.

    """
    found: Path | None = find_pyproject(start=start)
    return None if found is None else load_config(path=found)


def effective(*, config: AstartConfig, path: Path) -> Selection:
    """Resolve the selection a path runs under.

    Overrides whose pattern matches ``path`` relative to the config root
    apply in file order, later entries winning.

    Args:
        config: The loaded config.
        path: File the selection applies to.

    Returns:
        The effective selection for the path.

    """
    try:
        relative: str = path.relative_to(config.root).as_posix()
    except ValueError:
        relative = path.as_posix()
    resolved: Selection = config.selection
    for override in config.overrides:
        if not fnmatch(name=relative, pat=override.pattern):
            continue
        resolved = replace(
            resolved,
            select=override.selection.select or resolved.select,
            ignore=(*resolved.ignore, *override.selection.ignore),
            profile=override.selection.profile or resolved.profile,
            min_confidence=(
                override.selection.min_confidence
                if override.selection.min_confidence is not None
                else resolved.min_confidence
            ),
            safety_ceiling=(
                override.selection.safety_ceiling
                if override.selection.safety_ceiling is not None
                else resolved.safety_ceiling
            ),
            target_version=(
                override.selection.target_version
                if override.selection.target_version is not None
                else resolved.target_version
            ),
            params={**resolved.params, **override.selection.params},
        )
    return resolved


def excluded(*, config: AstartConfig, path: Path) -> bool:
    """Answer whether discovery should skip ``path``.

    Args:
        config: The loaded config.
        path: Candidate file.

    Returns:
        ``True`` when an ``exclude`` pattern matches.

    """
    try:
        relative: str = path.relative_to(config.root).as_posix()
    except ValueError:
        relative = path.as_posix()
    return any(fnmatch(name=relative, pat=pat) for pat in config.exclude)


def _matches_any(*, code: str, prefixes: tuple[str, ...]) -> bool:
    """Answer whether ``code`` equals or starts with a prefix.

    Args:
        code: Rule code or fix key.
        prefixes: Candidate prefixes.

    Returns:
        ``True`` on any match.

    """
    return any(code.startswith(prefix) for prefix in prefixes)


def _overrides(*, table: TomlValue | None) -> tuple[PathOverride, ...]:
    """Parse the ``overrides`` sub-table.

    Args:
        table: Raw ``overrides`` value.

    Returns:
        The overrides, in file order.

    Raises:
        ConfigError: If the table is malformed.

    """
    if table is None:
        return ()
    if not isinstance(table, dict):
        msg: str = "[tool.astart.overrides] must be a table"
        raise ConfigError(msg)
    resolved: list[PathOverride] = []
    for pattern, value in table.items():
        where: str = f"[tool.astart.overrides.{pattern!r}]"
        if not isinstance(value, dict):
            msg = f"{where} must be a table"
            raise ConfigError(msg)
        unknown: frozenset[str] = frozenset(value) - (
            Constants.override_scalar_keys
            | Constants.override_list_keys
            | Constants.table_keys
        )
        if unknown:
            msg = f"unknown {where} keys: {sorted(unknown)}"
            raise ConfigError(msg)
        resolved.append(
            PathOverride(
                pattern=pattern,
                selection=_selection(
                    table=value,
                    list_keys=Constants.override_list_keys,
                    where=where,
                ),
            ),
        )
    return tuple(resolved)


def _selection(
    *,
    table: Mapping[str, TomlValue],
    list_keys: frozenset[str],
    where: str,
) -> Selection:
    """Build a :class:`Selection` from a raw table.

    Args:
        table: Raw config table.
        list_keys: Allowed string-list keys.
        where: Dotted name used in errors.

    Returns:
        The parsed selection.

    Raises:
        ConfigError: On type mismatches.

    """
    profile: TomlValue | None = table.get("profile")
    if profile is not None and not isinstance(profile, str):
        msg: str = f"{where} profile must be a string"
        raise ConfigError(msg)
    confidence: TomlValue | None = table.get("min-confidence")
    if confidence is not None and not isinstance(confidence, (int, float)):
        msg = f"{where} min-confidence must be a number"
        raise ConfigError(msg)
    if isinstance(confidence, (int, float)) and not 0.0 <= confidence <= 1.0:
        msg = f"{where} min-confidence must be between 0 and 1"
        raise ConfigError(msg)
    return Selection(
        select=_string_list(table=table, key="select", where=where)
        if "select" in list_keys
        else (),
        ignore=_string_list(table=table, key="ignore", where=where)
        if "ignore" in list_keys
        else (),
        profile=profile if isinstance(profile, str) else None,
        min_confidence=(
            float(confidence) if isinstance(confidence, (int, float)) else None
        ),
        safety_ceiling=_safety_ceiling(
            value=table.get("safety-ceiling"),
            where=where,
        ),
        target_version=_target_version(
            value=table.get("target-version"),
            where=where,
        ),
        params=_params(table=table, where=where),
    )


def _safety_ceiling(
    *,
    value: TomlValue | None,
    where: str,
) -> FixSafety | None:
    """Parse the ``safety-ceiling`` key.

    Args:
        value: Raw TOML value.
        where: Dotted name used in errors.

    Returns:
        The ceiling, or ``None`` when absent.

    Raises:
        ConfigError: If the value is not a known safety level.

    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return FixSafety(value)
        except ValueError:
            pass
    levels: str = ", ".join(member.value for member in FixSafety)
    msg: str = f"{where} safety-ceiling must be one of: {levels}"
    raise ConfigError(msg)


def _target_version(
    *,
    value: TomlValue | None,
    where: str,
) -> str | None:
    """Parse the ``target-version`` key.

    Args:
        value: Raw TOML value.
        where: Dotted name used in errors.

    Returns:
        The version string, or ``None`` when absent.

    Raises:
        ConfigError: If the value is not ``major[.minor[...]]`` digits.

    """
    if value is None:
        return None
    if isinstance(value, str) and fullmatch(
        pattern=r"\d+(\.\d+)*",
        string=value,
    ):
        return value
    msg: str = f"{where} target-version must look like '3.12'"
    raise ConfigError(msg)


def _params(
    *,
    table: Mapping[str, TomlValue],
    where: str,
) -> Mapping[str, FactValue]:
    """Parse the ``params`` sub-table of rule parameter overrides.

    Args:
        table: Raw config table.
        where: Dotted name used in errors.

    Returns:
        Parameter overrides keyed by name.

    Raises:
        ConfigError: If the table or a value is malformed.

    """
    value: TomlValue | None = table.get("params")
    if value is None:
        return {}
    if not isinstance(value, dict):
        msg: str = f"{where} params must be a table"
        raise ConfigError(msg)
    resolved: dict[str, FactValue] = {}
    for key, item in value.items():
        if not isinstance(item, (str, int, float, bool)):
            msg = f"{where} params.{key} must be a string, number or boolean"
            raise ConfigError(
                msg,
            )
        resolved[key] = item
    return resolved


def _string_list(
    *,
    table: Mapping[str, TomlValue],
    key: str,
    where: str,
) -> tuple[str, ...]:
    """Read a string list key, or ``()`` when absent.

    Args:
        table: Raw config table.
        key: The list key.
        where: Dotted name used in errors.

    Returns:
        The strings.

    Raises:
        ConfigError: If the value is not a list of strings.

    """
    value: TomlValue | None = table.get(key)
    if value is None:
        return ()
    items: Iterable[TomlValue]
    if isinstance(value, tuple):
        items = value
    elif isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            msg: str = f"{where} {key} must be a list of strings"
            raise ConfigError(msg)
        items = value
    else:
        msg = f"{where} {key} must be a list of strings"
        raise ConfigError(msg)
    return tuple(item for item in items if isinstance(item, str))
