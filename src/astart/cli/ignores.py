"""Apply a config's per-path selections to reports.

Files matching the config's ``exclude`` patterns drop out entirely;
every other file's findings are filtered through the effective
:class:`~astart.cli.config.Selection` for its path, expanded through its
named catalog profile by :func:`resolve`, so per-path
``select``/``ignore`` overrides, profile rule sets, severity overrides
and safety ceilings hold.

"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, final

from astart.cli.config import ConfigError, Selection, effective, excluded

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart.cli.config import AstartConfig
    from astart.cli.render import FileReport
    from astart.rules.model import Catalog, Finding, Profile, Rule
    from astart.rules.predicate import FactValue
    from astart.rules.vocabulary import FixSafety, Severity


@final
@dataclass(frozen=True, slots=True)
class ResolvedSelection:
    """A selection expanded through its catalog profile.

    Attributes:
        selection (Selection): The effective selection.
        profile (Profile | None): The catalog profile the selection names, or
            ``None``.

    """

    selection: Selection
    profile: Profile | None

    @property
    def ceiling(self) -> FixSafety | None:
        """Highest fix safety this selection allows, if configured.

        Returns:
            FixSafety | None:
                The explicit ceiling, else the profile's, else ``None``.

        """
        if self.selection.safety_ceiling is not None:
            return self.selection.safety_ceiling
        if self.profile is None:
            return None
        return self.profile.safety_ceiling

    def enabled(self, *, rule: Rule) -> bool:
        """Answer whether a rule runs under this selection.

        Args:
            rule (Rule): Catalog rule.

        Returns:
            bool: ``True`` when the profile enables the rule and select/ignore
                keep its code.

        """
        if self.profile is not None and rule.key not in self.profile.rules:
            return False
        return self.selection.selected(code=rule.code)

    def severity(self, *, rule: Rule) -> Severity:
        """Resolve a rule's severity under this selection.

        Args:
            rule (Rule): Catalog rule.

        Returns:
            Severity: The profile's override, else the rule's default.

        """
        if self.profile is None:
            return rule.severity
        return self.profile.severities.get(rule.key, rule.severity)

    def params(self, *, rule: Rule) -> Mapping[str, FactValue]:
        """Resolve a rule's parameters under this selection.

        Catalog defaults are overridden by profile params, which are
        overridden by the selection's own ``params`` table.

        Args:
            rule (Rule): Catalog rule.

        Returns:
            Mapping[str, FactValue]: Effective parameters keyed by name.

        """
        merged: dict[str, FactValue] = dict(rule.params)
        if self.profile is not None:
            merged.update(self.profile.params)
        merged.update(self.selection.params)
        return merged


def resolve(*, selection: Selection, catalog: Catalog) -> ResolvedSelection:
    """Expand a selection through the catalog's profiles.

    Args:
        selection (Selection): Effective selection, possibly naming a profile.
        catalog (Catalog): Catalog holding the profiles.

    Returns:
        ResolvedSelection: The resolved selection.

    Raises:
        ConfigError: If the named profile does not exist.

    """
    if selection.profile is None:
        return ResolvedSelection(selection=selection, profile=None)
    profile: Profile | None = next(
        (item for item in catalog.profiles if item.key == selection.profile),
        None,
    )
    if profile is None:
        msg: str = f"unknown [tool.astart] profile {selection.profile!r}"
        raise ConfigError(msg)
    return ResolvedSelection(selection=selection, profile=profile)


def apply_ignores(
    *,
    results: Sequence[FileReport],
    config: AstartConfig,
    catalog: Catalog,
) -> tuple[FileReport, ...]:
    """Filter reports through the config's path selections.

    Args:
        results (Sequence[FileReport]): Reports to filter.
        config (AstartConfig): The loaded ``[tool.astart]`` config.
        catalog (Catalog): Catalog that resolves rule keys to codes and
            profiles.

    Returns:
        tuple[FileReport, ...]: Reports with excluded files and unselected
            findings
            removed, severities rewritten by profile overrides.

    """
    kept: list[FileReport] = []
    for report in results:
        if excluded(config=config, path=Path(report.path)):
            continue
        resolved: ResolvedSelection = resolve(
            selection=effective(config=config, path=Path(report.path)),
            catalog=catalog,
        )
        findings: tuple[Finding, ...] = tuple(
            replace(
                finding,
                severity=resolved.severity(
                    rule=catalog.rule(key=finding.rule_key),
                ),
            )
            for finding in report.findings
            if resolved.enabled(rule=catalog.rule(key=finding.rule_key))
        )
        kept.append(replace(report, findings=findings))
    return tuple(kept)


def selected_rules(
    *,
    rules: Sequence[Rule],
    config: AstartConfig,
    catalog: Catalog,
) -> tuple[Rule, ...]:
    """Apply the root selection and profile to a catalog's rules.

    Args:
        rules (Sequence[Rule]): Catalog rules.
        config (AstartConfig): The loaded config.
        catalog (Catalog): Catalog holding the profiles.

    Returns:
        tuple[Rule, ...]: Rules the root selection keeps.

    """
    resolved: ResolvedSelection = resolve(
        selection=config.selection,
        catalog=catalog,
    )
    return tuple(rule for rule in rules if resolved.enabled(rule=rule))
