"""Load, dump and validate rule catalogs."""

from __future__ import annotations

from importlib.resources import files
from json import loads
from typing import TYPE_CHECKING

from astart.rules.jsonvalue import JsonValue, canonical_dumps
from astart.rules.model import (
    Catalog,
    Profile,
    RelationKind,
    catalog_from_json,
    to_json,
)
from astart.rules.predicate import Predicate, predicate_facts
from astart.rules.registry import Registries, rule_cost
from astart.rules.vocabulary import Cost, Expressible, FixSafety

if TYPE_CHECKING:
    from collections.abc import Iterable


class CatalogError(ValueError):
    """Raised when a catalog violates one or more invariants.

    Attributes:
        problems: Every violation found, in a stable order.

    """

    def __init__(self, *, problems: tuple[str, ...]) -> None:
        """Create the error.

        Args:
            problems: Every violation found.

        """
        super().__init__("; ".join(problems))
        self.problems: tuple[str, ...] = problems


def dump_catalog(*, catalog: Catalog) -> str:
    """Serialize a catalog to canonical JSON.

    Args:
        catalog: Catalog to serialize.

    Returns:
        Canonical text.

    """
    return canonical_dumps(value=to_json(item=catalog))


def load_catalog(*, text: str, registries: Registries) -> Catalog:
    """Parse and validate a catalog.

    Args:
        text: Catalog JSON.
        registries: Vocabulary the catalog is validated against.

    Returns:
        The validated catalog.

    """
    value: JsonValue = loads(s=text)
    catalog: Catalog = catalog_from_json(value=value)
    validate_catalog(catalog=catalog, registries=registries)
    return catalog


def load_default_catalog(*, registries: Registries) -> Catalog:
    """Load and validate the catalog shipped with astart.

    Every ``catalog/*.json`` file is a partial catalog; they are merged in
    file-name order before validation.

    Args:
        registries: Vocabulary the catalog is validated against.

    Returns:
        The validated seed catalog.

    """
    parts: list[Catalog] = []
    folder = files("astart.rules").joinpath("catalog")
    for entry in sorted(folder.iterdir(), key=lambda item: item.name):
        if entry.name.endswith(".json"):
            value: JsonValue = loads(s=entry.read_text(encoding="utf-8"))
            parts.append(catalog_from_json(value=value))
    catalog: Catalog = Catalog(
        rules=tuple(rule for part in parts for rule in part.rules),
        fixes=tuple(fix for part in parts for fix in part.fixes),
        profiles=tuple(item for part in parts for item in part.profiles),
        relations=tuple(item for part in parts for item in part.relations),
    )
    validate_catalog(catalog=catalog, registries=registries)
    return catalog


def validate_catalog(*, catalog: Catalog, registries: Registries) -> None:
    """Check the data invariants of a catalog.

    Covers uniqueness, references, ordering cycles, conflicts, proven-fix
    purity, declared requirements, alias uniqueness and example presence.
    The behavioural invariants (examples trigger, fixes are idempotent) need
    the engine; see ``astart.rules.engine.verify_catalog``.

    Args:
        catalog: Catalog to check.
        registries: Declared node kinds, facts, procedures and appliers.

    Raises:
        CatalogError: With every problem found.

    """
    problems: list[str] = []
    problems.extend(_uniqueness(catalog=catalog))
    problems.extend(_references(catalog=catalog, registries=registries))
    problems.extend(_ordering(catalog=catalog))
    problems.extend(_conflicts(catalog=catalog))
    problems.extend(_purity(catalog=catalog, registries=registries))
    problems.extend(_requirements(catalog=catalog, registries=registries))
    problems.extend(_aliases(catalog=catalog))
    problems.extend(_examples(catalog=catalog))
    if problems:
        raise CatalogError(problems=tuple(problems))


def _duplicates(*, values: Iterable[str]) -> list[str]:
    """Return values that occur more than once, in first-seen order.

    Args:
        values: Values to inspect.

    Returns:
        The repeated values.

    """
    seen: set[str] = set()
    repeated: list[str] = []
    for value in values:
        if value in seen and value not in repeated:
            repeated.append(value)
        seen.add(value)
    return repeated


def _uniqueness(*, catalog: Catalog) -> list[str]:
    """Check invariant 1: keys and codes are unique.

    Args:
        catalog: Catalog to check.

    Returns:
        Problems found.

    """
    problems: list[str] = [
        f"duplicate rule key {key!r}"
        for key in _duplicates(values=(r.key for r in catalog.rules))
    ]
    problems.extend(
        f"duplicate rule code {code!r}"
        for code in _duplicates(values=(r.code for r in catalog.rules))
    )
    problems.extend(
        f"duplicate fix key {key!r}"
        for key in _duplicates(values=(f.key for f in catalog.fixes))
    )
    problems.extend(
        f"duplicate profile key {key!r}"
        for key in _duplicates(values=(p.key for p in catalog.profiles))
    )
    return problems


def _predicate_problems(
    *,
    owner: str,
    predicate: Predicate | None,
    registries: Registries,
) -> list[str]:
    """Report undeclared facts read by a predicate.

    Args:
        owner: Description of the entity owning the predicate.
        predicate: Predicate to inspect.
        registries: Declared facts.

    Returns:
        Problems found.

    """
    if predicate is None:
        return []
    return [
        f"{owner}: unknown fact {name!r}"
        for name in sorted(predicate_facts(predicate=predicate))
        if name not in registries.facts
    ]


def _references(*, catalog: Catalog, registries: Registries) -> list[str]:
    """Check invariant 2: every reference resolves.

    Args:
        catalog: Catalog to check.
        registries: Declared vocabulary.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    fix_keys: frozenset[str] = frozenset(f.key for f in catalog.fixes)
    rule_keys: frozenset[str] = frozenset(r.key for r in catalog.rules)
    for rule in catalog.rules:
        owner: str = f"rule {rule.key!r}"
        problems.extend(
            f"{owner}: unknown node kind {kind!r}"
            for kind in rule.subject
            if kind not in registries.node_kinds
        )
        problems.extend(
            f"{owner}: unknown fact {name!r}"
            for name in rule.requires
            if name not in registries.facts
        )
        problems.extend(
            _predicate_problems(
                owner=owner,
                predicate=rule.when,
                registries=registries,
            ),
        )
        if (
            rule.procedure is not None
            and rule.procedure not in registries.procedures
        ):
            problems.append(
                f"{owner}: unknown procedure {rule.procedure!r}",
            )
        problems.extend(
            f"{owner}: unknown fix {key!r}"
            for key in rule.fixes
            if key not in fix_keys
        )
    for fix in catalog.fixes:
        owner = f"fix {fix.key!r}"
        problems.extend(
            f"{owner}: unknown applier {key!r}"
            for key in fix.edits
            if key not in registries.appliers
        )
        problems.extend(
            f"{owner}: unknown rule {key!r}"
            for key in fix.rules
            if key not in rule_keys
        )
        problems.extend(
            _predicate_problems(
                owner=owner,
                predicate=fix.preconditions,
                registries=registries,
            ),
        )
    for profile in catalog.profiles:
        problems.extend(
            f"profile {profile.key!r}: unknown rule {key!r}"
            for key in profile.rules
            if key not in rule_keys
        )
    return problems


def _ordering(*, catalog: Catalog) -> list[str]:
    """Check invariant 3: ordering relations have no cycle.

    Args:
        catalog: Catalog to check.

    Returns:
        Problems found.

    """
    edges: dict[str, set[str]] = {}
    for relation in catalog.relations:
        if relation.kind is RelationKind.ordered_before:
            edges.setdefault(relation.source, set()).add(relation.target)
    for fix in catalog.fixes:
        for later in fix.before:
            edges.setdefault(fix.key, set()).add(later)
        for earlier in fix.after:
            edges.setdefault(earlier, set()).add(fix.key)
    done: set[str] = set()
    for start in sorted(edges):
        path: list[str] = []
        if _cycle(node=start, edges=edges, path=path, done=done):
            return [f"ordering cycle through {' -> '.join(path)}"]
    return []


def _cycle(
    *,
    node: str,
    edges: dict[str, set[str]],
    path: list[str],
    done: set[str],
) -> bool:
    """Depth-first search for a cycle.

    Args:
        node: Node being visited.
        edges: Adjacency sets.
        path: Nodes on the current path, extended in place.
        done: Nodes already proven acyclic.

    Returns:
        Whether a cycle was found; ``path`` then ends in the repeated node.

    """
    if node in path:
        path.append(node)
        return True
    if node in done:
        return False
    path.append(node)
    for target in sorted(edges.get(node, ())):
        if _cycle(node=target, edges=edges, path=path, done=done):
            return True
    path.pop()
    done.add(node)
    return False


def _conflicts(*, catalog: Catalog) -> list[str]:
    """Check invariant 3: conflicting rules never share a profile.

    Args:
        catalog: Catalog to check.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    for relation in catalog.relations:
        if relation.kind is not RelationKind.conflicts_with:
            continue
        problems.extend(
            f"profile {profile.key!r} enables conflicting rules "
            f"{relation.source!r} and {relation.target!r}"
            for profile in _profiles_with(
                profiles=catalog.profiles,
                keys=(relation.source, relation.target),
            )
        )
    return problems


def _profiles_with(
    *,
    profiles: tuple[Profile, ...],
    keys: tuple[str, ...],
) -> list[Profile]:
    """Select profiles that enable every given rule.

    Args:
        profiles: Profiles to scan.
        keys: Rule keys that must all be enabled.

    Returns:
        The matching profiles.

    """
    return [p for p in profiles if all(key in p.rules for key in keys)]


def _purity(*, catalog: Catalog, registries: Registries) -> list[str]:
    """Check invariant 6: proven fixes need no inference.

    Args:
        catalog: Catalog to check.
        registries: Declared facts.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    for fix in catalog.fixes:
        if fix.safety is not FixSafety.proven or fix.preconditions is None:
            continue
        for name in sorted(predicate_facts(predicate=fix.preconditions)):
            spec = registries.facts.get(name)
            if spec is not None and spec.cost.rank() > Cost.scope.rank():
                problems.append(
                    f"proven fix {fix.key!r} depends on {spec.cost.value} "
                    f"fact {name!r}",
                )
    return problems


def _requirements(*, catalog: Catalog, registries: Registries) -> list[str]:
    """Check invariant 7: declarative requirements equal the facts read.

    Args:
        catalog: Catalog to check.
        registries: Declared facts.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    for rule in catalog.rules:
        if rule.expressible is not Expressible.declarative:
            continue
        if rule.when is None or any(
            name not in registries.facts for name in rule.requires
        ):
            continue
        read: frozenset[str] = predicate_facts(predicate=rule.when)
        if frozenset(rule.requires) != read:
            problems.append(
                f"rule {rule.key!r}: requires must equal the facts its "
                f"predicate reads ({', '.join(sorted(read))}); cost would be "
                f"{rule_cost(registries=registries, requires=read).value}",
            )
    return problems


def _aliases(*, catalog: Catalog) -> list[str]:
    """Check invariant 8: aliases are unique per external system.

    Args:
        catalog: Catalog to check.

    Returns:
        Problems found.

    """
    problems: list[str] = []
    owners: dict[tuple[str, str], str] = {}
    for rule in catalog.rules:
        for system, alias in rule.aliases.items():
            slot: tuple[str, str] = (system, alias)
            if slot in owners and owners[slot] != rule.key:
                problems.append(
                    f"duplicate alias {alias!r} for system {system!r} on "
                    f"{owners[slot]!r} and {rule.key!r}",
                )
            owners.setdefault(slot, rule.key)
    return problems


def _examples(*, catalog: Catalog) -> list[str]:
    """Check invariant 4 (data half): both kinds of example exist.

    Args:
        catalog: Catalog to check.

    Returns:
        Problems found.

    """
    return [
        f"rule {rule.key!r}: needs at least one triggering and one "
        "non-triggering example"
        for rule in catalog.rules
        if not any(example.triggers for example in rule.examples)
        or all(example.triggers for example in rule.examples)
    ]
