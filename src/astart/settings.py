"""Public ``Settings`` object shared by the CLI and the API (API-04).

``[tool.astart]`` tables are parsed by :func:`astart.cli.config.load_config`
and mapped onto this frozen dataclass; :meth:`Settings.to_fix_settings`
turns it back into the engine's :class:`astart.rules.runner.FixSettings`.
Fields that need runtime objects (the checker itself, the project view,
libraries, custom appliers) are injected by the caller at conversion
time, mirroring how ``astart fix`` resolves ``--checker`` separately.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.cli.config import load_config
from astart.project.versions import resolve_target
from astart.rules import FixSettings
from astart.rules.confidence import Constants as ConfidenceConstants
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from astart.cli.config import AstartConfig, Selection
    from astart.project.libraries import LibraryIndex
    from astart.rules.checker import Checker
    from astart.rules.facts import Applier
    from astart.rules.project_bridge import ProjectView


@final
@dataclass(frozen=True, slots=True)
class Settings:
    """User-facing fix configuration, serializable to ``[tool.astart]``.

    Mirrors every :class:`FixSettings` field a ``pyproject.toml`` can
    express. ``target`` is spelled ``target_version`` (the config
    string); ``to_fix_settings`` resolves it through
    :func:`astart.project.versions.resolve_target`. ``checker`` holds the
    configured mode string — the ``Checker`` object itself is injected
    into :meth:`to_fix_settings` by the caller, exactly like the CLI's
    ``use_checker`` split.

    Attributes:
        ceiling: Highest fix safety applied automatically.
        stubs_path: Stub directory for type hints, or ``None``.
        max_rounds: Upper bound on repeat passes.
        appliers: Custom applier table, or ``None`` for built-ins.
        create_constants: Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        docstring_types: Include annotation types in generated documentation.
        stub_docstrings: Whether undocumented public definitions get a
            stub docstring.
        annotate_variables: Whether function-local variables get a type
            annotation.
        negotiate: Whether negotiated annotations supplement the hint
            index.
        engine: Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        min_confidence: Fixes below this confidence are skipped.
        checker: Checker mode string from ``[tool.astart] checker``, or
            ``None`` for the default.
        project: Cross-module view, or ``None`` for single-module runs.
        libraries: External signature index, or ``None``.
        target_version: Oldest Python version emitted code must run on,
            or ``None`` for ``requires-python``/the interpreter.
        excluded_prefixes: Fix-key prefixes never applied.
        runtime_protocols: Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general: Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement: Where synthesized protocols land.
        optimize_aliases: Whether repeated type patterns are extracted into
            PEP 695 ``type`` aliases after the fixes settle.

    """

    ceiling: FixSafety = FixSafety.guarded
    stubs_path: Path | None = None
    max_rounds: int = 8
    appliers: Mapping[str, Applier] | None = None
    create_constants: bool = False
    stub_docstrings: bool = False
    docstring_types: bool = True
    annotate_variables: bool = False
    negotiate: bool = True
    engine: bool = False
    min_confidence: float = ConfidenceConstants.default_minimum
    checker: str | None = None
    project: ProjectView | None = None
    libraries: LibraryIndex | None = None
    target_version: str | None = None
    excluded_prefixes: tuple[str, ...] = ()
    runtime_protocols: bool = False
    accept_general: bool = False
    protocol_placement: str = "module"
    optimize_aliases: bool = True

    @classmethod
    def from_pyproject(cls, *, path: Path) -> Settings:
        """Build settings from a ``pyproject.toml`` file.

        Args:
            path (Path): The ``pyproject.toml`` to read; its ``[tool.astart]``
                table supplies ``safety-ceiling``, ``min-confidence``,
                ``target-version``, ``checker`` and
                ``protocol-placement`` when present.

        Returns:
            Settings: Settings populated from the table, or defaults
                when the file has no ``[tool.astart]`` table.

        Raises:
            ConfigError: If the table exists but is malformed.

        """
        config: AstartConfig | None = load_config(path=path)
        if config is None:
            return cls()
        selection: Selection = config.selection
        return cls(
            ceiling=(
                selection.safety_ceiling
                if selection.safety_ceiling is not None
                else FixSafety.guarded
            ),
            min_confidence=(
                selection.min_confidence
                if selection.min_confidence is not None
                else ConfidenceConstants.default_minimum
            ),
            checker=config.checker,
            target_version=selection.target_version,
            protocol_placement=config.protocol_placement,
        )

    def to_fix_settings(
        self,
        *,
        checker: Checker | None = None,
    ) -> FixSettings:
        """Convert to the engine's :class:`FixSettings`.

        Args:
            checker (Checker | None): Resolved type-checker gate, or ``None`` —
                the same injection point the CLI uses after
                interpreting the ``checker`` mode string.

        Returns:
            FixSettings: Fix settings with ``target_version`` resolved through
                :func:`astart.project.versions.resolve_target`.

        """
        return FixSettings(
            ceiling=self.ceiling,
            stubs_path=self.stubs_path,
            max_rounds=self.max_rounds,
            appliers=self.appliers,
            create_constants=self.create_constants,
            stub_docstrings=self.stub_docstrings,
            docstring_types=self.docstring_types,
            annotate_variables=self.annotate_variables,
            negotiate=self.negotiate,
            engine=self.engine,
            min_confidence=self.min_confidence,
            checker=checker,
            project=self.project,
            libraries=self.libraries,
            target=resolve_target(configured=self.target_version),
            excluded_prefixes=self.excluded_prefixes,
            runtime_protocols=self.runtime_protocols,
            accept_general=self.accept_general,
            protocol_placement=self.protocol_placement,
            optimize_aliases=self.optimize_aliases,
        )
