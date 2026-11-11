"""Entities of the rule ontology and their JSON conversion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import TYPE_CHECKING, final

from astart.rules.jsonvalue import JsonValue, canonical_dumps
from astart.rules.predicate import (
    FactValue,
    Predicate,
    predicate_from_json,
    predicate_to_json,
)
from astart.rules.vocabulary import (
    Domain,
    Expressible,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class RelationKind(StrEnum):
    """Typed edge between ontology entities.

    Attributes:
        implies: Source holding implies target holds.
        supersedes: Source replaces target.
        conflicts_with: Source and target cannot be enabled together.
        requires_fact: Source needs the target fact.
        ordered_before: Source runs before target.
        delegates_to: Source is delegated to the target tool.
        equivalent_to: Source is the same as an external target.

    """

    implies = "implies"
    supersedes = "supersedes"
    conflicts_with = "conflicts_with"
    requires_fact = "requires_fact"
    ordered_before = "ordered_before"
    delegates_to = "delegates_to"
    equivalent_to = "equivalent_to"


def _no_aliases() -> dict[str, str]:
    """Create an empty alias mapping.

    Returns:
        dict[str, str]: A new empty dictionary.

    """
    return {}


def _no_params() -> dict[str, FactValue]:
    """Create an empty parameter mapping.

    Returns:
        dict[str, FactValue]: A new empty dictionary.

    """
    return {}


@final
@dataclass(frozen=True, slots=True)
class EvidenceSlot:
    """Typed value a finding must provide.

    Attributes:
        name (str): Slot name used in the message template.
        type (str): Value type name.

    """

    name: str
    type: str


@final
@dataclass(frozen=True, slots=True)
class Example:
    """Snippet that does or does not trigger a rule.

    Attributes:
        source (str): Python source of the snippet.
        triggers (bool): Whether the rule must report it.
        note (str): Optional explanation.

    """

    source: str
    triggers: bool
    note: str = ""


@final
@dataclass(frozen=True, slots=True)
class Rule:
    """Describe one check.

    Attributes:
        key (str): Stable slug, never reused.
        code (str): Short unique display id.
        title (str): One-line name.
        rationale (str): Why the rule exists.
        domain (Domain): Subject area.
        severity (Severity): Default severity.
        maturity (Maturity): Lifecycle stage.
        owner (Owner): Tool responsible for the rule.
        subject (tuple[str, ...]): Node kinds the rule inspects.
        message (str): Template with named evidence slots.
        when (Predicate | None): Declarative trigger.
        procedure (str | None): Registered procedure key for a procedural
            trigger.
        requires (tuple[str, ...]): Facts needed to evaluate the rule.
        evidence (tuple[EvidenceSlot, ...]): Values every finding provides.
        fixes (tuple[str, ...]): Fix keys offered for this rule.
        examples (tuple[Example, ...]): Snippets that double as the rule's
            tests.
        aliases (Mapping[str, str]): External ids by system name.
        params (Mapping[str, FactValue]): Typed parameters a profile may
            override.

    """

    key: str
    code: str
    title: str
    rationale: str
    domain: Domain
    severity: Severity
    maturity: Maturity
    owner: Owner
    subject: tuple[str, ...]
    message: str
    when: Predicate | None = None
    procedure: str | None = None
    requires: tuple[str, ...] = ()
    evidence: tuple[EvidenceSlot, ...] = ()
    fixes: tuple[str, ...] = ()
    examples: tuple[Example, ...] = ()
    aliases: Mapping[str, str] = field(default_factory=_no_aliases)
    params: Mapping[str, FactValue] = field(default_factory=_no_params)

    @property
    def expressible(self) -> Expressible:
        """How the trigger is expressed.

        Returns:
            Expressible:
                Procedural when a procedure is named, else declarative.

        """
        if self.procedure is not None:
            return Expressible.procedural
        return Expressible.declarative

    def __post_init__(self) -> None:
        """Require exactly one trigger.

        Raises:
            ValueError: If both or neither of ``when`` and ``procedure`` set.

        """
        if (self.when is None) == (self.procedure is None):
            msg: str = (
                f"rule {self.key!r} needs exactly one of"
                " 'when' and 'procedure'"
            )
            raise ValueError(msg)


@final
@dataclass(frozen=True, slots=True)
class Fix:
    """Describe one automatic edit plan.

    Attributes:
        key (str): Stable slug.
        rules (tuple[str, ...]): Rules the fix resolves.
        safety (FixSafety): How far it may be applied unreviewed.
        min_confidence (float): Inference confidence required when guarded.
        edits (tuple[str, ...]): Applier keys, in order.
        preconditions (Predicate | None): Predicate that must hold when
            applied.
        idempotent (bool): Whether applying twice equals applying once.
        before (tuple[str, ...]): Fix keys this fix must run before.
        after (tuple[str, ...]): Fix keys this fix must run after.

    """

    key: str
    rules: tuple[str, ...]
    safety: FixSafety
    min_confidence: float
    edits: tuple[str, ...]
    preconditions: Predicate | None
    idempotent: bool
    before: tuple[str, ...] = ()
    after: tuple[str, ...] = ()


@final
@dataclass(frozen=True, slots=True)
class Profile:
    """Named selection and parameterisation of rules.

    Attributes:
        key (str): Stable slug.
        rules (tuple[str, ...]): Enabled rule keys.
        severities (Mapping[str, Severity]): Severity overrides by rule key.
        params (Mapping[str, FactValue]): Parameter overrides.
        safety_ceiling (FixSafety): Highest fix safety applied automatically.

    """

    key: str
    rules: tuple[str, ...]
    severities: Mapping[str, Severity]
    params: Mapping[str, FactValue]
    safety_ceiling: FixSafety


@final
@dataclass(frozen=True, slots=True)
class Relation:
    """Typed edge between two ontology entities.

    Attributes:
        kind (RelationKind): Edge type.
        source (str): Source entity key.
        target (str): Target entity key.

    """

    kind: RelationKind
    source: str
    target: str


@final
@dataclass(frozen=True, slots=True)
class Span:
    """Source range of a finding.

    Attributes:
        file (str): File name.
        start_line (int): First line, one-based.
        start_column (int): First column, zero-based.
        end_line (int): Last line, one-based.
        end_column (int): Last column, zero-based.

    """

    file: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int


@final
@dataclass(frozen=True, slots=True)
class FixOffer:
    """Fix proposed for a finding.

    Attributes:
        fix_key (str): Offered fix.
        safety (FixSafety): Its safety class.
        confidence (float): Inference confidence for this finding.

    """

    fix_key: str
    safety: FixSafety
    confidence: float


@final
@dataclass(frozen=True, slots=True)
class Finding:
    """One reported violation.

    Attributes:
        rule_key (str): Rule that fired.
        severity (Severity): Severity after profile overrides.
        span (Span): Source range.
        subject_path (str): Dotted qualified path of the subject.
        evidence (Mapping[str, JsonValue]): Values for the rule's evidence
            slots.
        fix_offers (tuple[FixOffer, ...]): Fixes that apply.
        fingerprint (str): Stable identity that ignores line numbers.

    """

    rule_key: str
    severity: Severity
    span: Span
    subject_path: str
    evidence: Mapping[str, JsonValue]
    fix_offers: tuple[FixOffer, ...]
    fingerprint: str


@final
@dataclass(frozen=True, slots=True)
class Catalog:
    """All rules, fixes, profiles and relations.

    Attributes:
        rules (tuple[Rule, ...]): Rules.
        fixes (tuple[Fix, ...]): Fixes.
        profiles (tuple[Profile, ...]): Profiles.
        relations (tuple[Relation, ...]): Relations.

    """

    rules: tuple[Rule, ...]
    fixes: tuple[Fix, ...]
    profiles: tuple[Profile, ...]
    relations: tuple[Relation, ...]

    def rule(self, *, key: str) -> Rule:
        """Look up a rule.

        Args:
            key (str): Rule key.

        Returns:
            Rule: The rule.

        Raises:
            KeyError: If no rule has the key.

        """
        for candidate in self.rules:
            if candidate.key == key:
                return candidate
        msg: str = f"rule {key!r} is missing from the catalog"
        raise KeyError(msg)

    def fix(self, *, key: str) -> Fix:
        """Look up a fix.

        Args:
            key (str): Fix key.

        Returns:
            Fix: The fix.

        Raises:
            KeyError: If no fix has the key.

        """
        for candidate in self.fixes:
            if candidate.key == key:
                return candidate
        msg: str = f"fix {key!r} is missing from the catalog"
        raise KeyError(msg)


def make_fingerprint(
    *,
    rule_key: str,
    subject_path: str,
    evidence: Mapping[str, JsonValue],
) -> str:
    """Hash a finding's identity without line numbers.

    Args:
        rule_key (str): Rule that fired.
        subject_path (str): Dotted qualified path of the subject.
        evidence (Mapping[str, JsonValue]): Evidence values.

    Returns:
        str: The first 16 hexadecimal characters of a SHA-256 digest.

    """
    payload: str = canonical_dumps(
        value={
            "rule": rule_key,
            "subject": subject_path,
            "evidence": dict(evidence),
        },
    )
    return sha256(data=payload.encode()).hexdigest()[:16]


def to_json(*, item: Rule | Fix | Profile | Relation | Catalog) -> JsonValue:
    """Convert an entity to its JSON form.

    Args:
        item (Rule | Fix | Profile | Relation | Catalog): Entity to convert.

    Returns:
        JsonValue: JSON-compatible value.

    """
    match item:
        case Rule():
            return _rule_to_json(rule=item)
        case Fix():
            return _fix_to_json(fix=item)
        case Profile():
            return {
                "key": item.key,
                "rules": list(item.rules),
                "severities": {
                    key: value.value for key, value in item.severities.items()
                },
                "params": dict(item.params),
                "safety_ceiling": item.safety_ceiling.value,
            }
        case Relation():
            return {
                "kind": item.kind.value,
                "source": item.source,
                "target": item.target,
            }
        case Catalog():
            return {
                "rules": [to_json(item=rule) for rule in item.rules],
                "fixes": [to_json(item=fix) for fix in item.fixes],
                "profiles": [to_json(item=p) for p in item.profiles],
                "relations": [to_json(item=r) for r in item.relations],
            }


def _rule_to_json(*, rule: Rule) -> JsonValue:
    """Convert a rule to JSON.

    Args:
        rule (Rule): Rule to convert.

    Returns:
        JsonValue: JSON-compatible value.

    """
    return {
        "key": rule.key,
        "code": rule.code,
        "title": rule.title,
        "rationale": rule.rationale,
        "domain": rule.domain.value,
        "severity": rule.severity.value,
        "maturity": rule.maturity.value,
        "owner": rule.owner.value,
        "subject": list(rule.subject),
        "message": rule.message,
        "when": (
            None
            if rule.when is None
            else predicate_to_json(predicate=rule.when)
        ),
        "procedure": rule.procedure,
        "requires": list(rule.requires),
        "evidence": [
            {"name": slot.name, "type": slot.type} for slot in rule.evidence
        ],
        "fixes": list(rule.fixes),
        "examples": [
            {
                "source": example.source,
                "triggers": example.triggers,
                "note": example.note,
            }
            for example in rule.examples
        ],
        "aliases": dict(rule.aliases),
        "params": dict(rule.params),
    }


def _fix_to_json(*, fix: Fix) -> JsonValue:
    """Convert a fix to JSON.

    Args:
        fix (Fix): Fix to convert.

    Returns:
        JsonValue: JSON-compatible value.

    """
    return {
        "key": fix.key,
        "rules": list(fix.rules),
        "safety": fix.safety.value,
        "min_confidence": fix.min_confidence,
        "edits": list(fix.edits),
        "preconditions": (
            None
            if fix.preconditions is None
            else predicate_to_json(predicate=fix.preconditions)
        ),
        "idempotent": fix.idempotent,
        "before": list(fix.before),
        "after": list(fix.after),
    }


@final
class _Reader:
    """Typed access to one JSON object, with errors that name the key."""

    def __init__(self, *, value: JsonValue, what: str) -> None:
        """Wrap a JSON object.

        Args:
            value (JsonValue): Value expected to be an object.
            what (str): Entity name used in error messages.

        Raises:
            ValueError: If the value is not an object.

        """
        match value:
            case dict():
                self._data: dict[str, JsonValue] = value
            case _:
                msg: str = f"{what} must be a JSON object, got {value!r}"
                raise ValueError(msg)
        self._what: str = what

    def raw(self, *, key: str) -> JsonValue:
        """Return a mandatory value.

        Args:
            key (str): Object key.

        Returns:
            JsonValue: The stored value.

        Raises:
            ValueError: If the key is absent.

        """
        if key not in self._data:
            msg: str = f"{self._what} is missing key {key!r}"
            raise ValueError(msg)
        return self._data[key]

    def text(self, *, key: str) -> str:
        """Return a mandatory string.

        Args:
            key (str): Object key.

        Returns:
            str: The string.

        Raises:
            ValueError: If the value is not a string.

        """
        match self.raw(key=key):
            case str() as text:
                return text
            case other:
                msg: str = (
                    f"{self._what}.{key} must be a string, got {other!r}"
                )
                raise ValueError(msg)

    def optional_text(self, *, key: str) -> str | None:
        """Return a string that may be null or absent.

        Args:
            key (str): Object key.

        Returns:
            str | None: The string or ``None``.

        Raises:
            ValueError: If the value is neither a string nor null.

        """
        match self._data.get(key):
            case None:
                return None
            case str() as text:
                return text
            case other:
                msg: str = (
                    f"{self._what}.{key} must be a string, got {other!r}"
                )
                raise ValueError(msg)

    def number(self, *, key: str) -> float:
        """Return a mandatory number.

        Args:
            key (str): Object key.

        Returns:
            float: The number.

        Raises:
            ValueError: If the value is not a number.

        """
        match self.raw(key=key):
            case bool():
                msg: str = f"{self._what}.{key} must be a number"
                raise ValueError(msg)
            case int() | float() as number:
                return float(number)
            case other:
                msg = f"{self._what}.{key} must be a number, got {other!r}"
                raise ValueError(msg)

    def flag(self, *, key: str) -> bool:
        """Return a mandatory boolean.

        Args:
            key (str): Object key.

        Returns:
            bool: The boolean.

        Raises:
            ValueError: If the value is not a boolean.

        """
        match self.raw(key=key):
            case bool() as flag:
                return flag
            case other:
                msg: str = (
                    f"{self._what}.{key} must be a boolean, got {other!r}"
                )
                raise ValueError(msg)

    def items(self, *, key: str) -> list[JsonValue]:
        """Return a list that may be absent.

        Args:
            key (str): Object key.

        Returns:
            list[JsonValue]: The list, empty when absent.

        Raises:
            ValueError: If the value is not a list.

        """
        match self._data.get(key, []):
            case list() as items:
                return items
            case other:
                msg: str = f"{self._what}.{key} must be a list, got {other!r}"
                raise ValueError(msg)

    def strings(self, *, key: str) -> tuple[str, ...]:
        """Return a list of strings that may be absent.

        Args:
            key (str): Object key.

        Returns:
            tuple[str, ...]: The strings.

        Raises:
            ValueError: If any item is not a string.

        """
        result: list[str] = []
        for item in self.items(key=key):
            match item:
                case str() as text:
                    result.append(text)
                case _:
                    msg: str = f"{self._what}.{key} must hold strings"
                    raise ValueError(msg)
        return tuple(result)

    def mapping(self, *, key: str) -> dict[str, JsonValue]:
        """Return an object that may be absent.

        Args:
            key (str): Object key.

        Returns:
            dict[str, JsonValue]: The object, empty when absent.

        Raises:
            ValueError: If the value is not an object.

        """
        match self._data.get(key, {}):
            case dict() as mapping:
                return mapping
            case other:
                msg: str = (
                    f"{self._what}.{key} must be an object, got {other!r}"
                )
                raise ValueError(msg)

    def predicate(self, *, key: str) -> Predicate | None:
        """Return a predicate that may be null or absent.

        Args:
            key (str): Object key.

        Returns:
            Predicate | None: The predicate or ``None``.

        """
        match self._data.get(key):
            case None:
                return None
            case value:
                return predicate_from_json(value=value)


def _scalars(
    *,
    values: dict[str, JsonValue],
    what: str,
) -> dict[str, FactValue]:
    """Check that every value of an object is a scalar.

    Args:
        values (dict[str, JsonValue]): Object to check.
        what (str): Entity name used in error messages.

    Returns:
        dict[str, FactValue]: The same entries typed as fact values.

    Raises:
        ValueError: If a value is a list or an object.

    """
    result: dict[str, FactValue] = {}
    for key, value in values.items():
        match value:
            case list() | dict():
                msg: str = f"{what}.{key} must be a scalar"
                raise ValueError(msg)
            case scalar:
                result[key] = scalar
    return result


def rule_from_json(*, value: JsonValue) -> Rule:
    """Restore a rule from JSON.

    Args:
        value (JsonValue): JSON-compatible value.

    Returns:
        Rule: The rule.

    Raises:
        ValueError: If the value does not describe a valid rule.

    """
    reader: _Reader = _Reader(value=value, what="rule")
    evidence: list[EvidenceSlot] = []
    for entry in reader.items(key="evidence"):
        slot: _Reader = _Reader(value=entry, what="evidence slot")
        evidence.append(
            EvidenceSlot(
                name=slot.text(key="name"),
                type=slot.text(key="type"),
            ),
        )
    examples: list[Example] = []
    for entry in reader.items(key="examples"):
        example: _Reader = _Reader(value=entry, what="example")
        examples.append(
            Example(
                source=example.text(key="source"),
                triggers=example.flag(key="triggers"),
                note=example.optional_text(key="note") or "",
            ),
        )
    aliases: dict[str, str] = {}
    for system, alias in reader.mapping(key="aliases").items():
        match alias:
            case str():
                aliases[system] = alias
            case _:
                msg: str = f"rule alias for {system!r} must be a string"
                raise ValueError(msg)
    return Rule(
        key=reader.text(key="key"),
        code=reader.text(key="code"),
        title=reader.text(key="title"),
        rationale=reader.text(key="rationale"),
        domain=Domain(reader.text(key="domain")),
        severity=Severity(reader.text(key="severity")),
        maturity=Maturity(reader.text(key="maturity")),
        owner=Owner(reader.text(key="owner")),
        subject=reader.strings(key="subject"),
        message=reader.text(key="message"),
        when=reader.predicate(key="when"),
        procedure=reader.optional_text(key="procedure"),
        requires=reader.strings(key="requires"),
        evidence=tuple(evidence),
        fixes=reader.strings(key="fixes"),
        examples=tuple(examples),
        aliases=aliases,
        params=_scalars(
            values=reader.mapping(key="params"),
            what="rule.params",
        ),
    )


def fix_from_json(*, value: JsonValue) -> Fix:
    """Restore a fix from JSON.

    Args:
        value (JsonValue): JSON-compatible value.

    Returns:
        Fix: The fix.

    """
    reader: _Reader = _Reader(value=value, what="fix")
    return Fix(
        key=reader.text(key="key"),
        rules=reader.strings(key="rules"),
        safety=FixSafety(reader.text(key="safety")),
        min_confidence=reader.number(key="min_confidence"),
        edits=reader.strings(key="edits"),
        preconditions=reader.predicate(key="preconditions"),
        idempotent=reader.flag(key="idempotent"),
        before=reader.strings(key="before"),
        after=reader.strings(key="after"),
    )


def profile_from_json(*, value: JsonValue) -> Profile:
    """Restore a profile from JSON.

    Args:
        value (JsonValue): JSON-compatible value.

    Returns:
        Profile: The profile.

    Raises:
        ValueError: If a severity override is not a string.

    """
    reader: _Reader = _Reader(value=value, what="profile")
    severities: dict[str, Severity] = {}
    for rule_key, level in reader.mapping(key="severities").items():
        match level:
            case str():
                severities[rule_key] = Severity(level)
            case _:
                msg: str = (
                    f"profile severity for {rule_key!r} must be a string"
                )
                raise ValueError(msg)
    return Profile(
        key=reader.text(key="key"),
        rules=reader.strings(key="rules"),
        severities=severities,
        params=_scalars(
            values=reader.mapping(key="params"),
            what="profile.params",
        ),
        safety_ceiling=FixSafety(reader.text(key="safety_ceiling")),
    )


def relation_from_json(*, value: JsonValue) -> Relation:
    """Restore a relation from JSON.

    Args:
        value (JsonValue): JSON-compatible value.

    Returns:
        Relation: The relation.

    """
    reader: _Reader = _Reader(value=value, what="relation")
    return Relation(
        kind=RelationKind(reader.text(key="kind")),
        source=reader.text(key="source"),
        target=reader.text(key="target"),
    )


def catalog_from_json(*, value: JsonValue) -> Catalog:
    """Restore a catalog from JSON.

    Args:
        value (JsonValue): JSON-compatible value.

    Returns:
        Catalog: The catalog.

    """
    reader: _Reader = _Reader(value=value, what="catalog")
    reader.raw(key="rules")
    return Catalog(
        rules=tuple(
            rule_from_json(value=v) for v in reader.items(key="rules")
        ),
        fixes=tuple(fix_from_json(value=v) for v in reader.items(key="fixes")),
        profiles=tuple(
            profile_from_json(value=v) for v in reader.items(key="profiles")
        ),
        relations=tuple(
            relation_from_json(value=v) for v in reader.items(key="relations")
        ),
    )
