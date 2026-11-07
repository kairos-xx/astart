"""Generate the JSON Schema of the rule catalog from the entity model."""

from __future__ import annotations

from dataclasses import MISSING, fields
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

from astart.rules.jsonvalue import JsonValue, canonical_dumps
from astart.rules.model import (
    EvidenceSlot,
    Example,
    Fix,
    Profile,
    Relation,
    RelationKind,
    Rule,
)
from astart.rules.vocabulary import (
    Domain,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

if TYPE_CHECKING:
    from enum import StrEnum


@final
class Constants:
    """Group module-level constants.

    Attributes:
        enums: Grouped module constant.
        entities: Grouped module constant.
        scalar: Grouped module constant.
        primitives: Grouped module constant.

    """

    enums: Final[dict[str, type[StrEnum]]] = {
        "Domain": Domain,
        "Severity": Severity,
        "Maturity": Maturity,
        "Owner": Owner,
        "FixSafety": FixSafety,
        "RelationKind": RelationKind,
    }
    entities: Final[dict[str, type]] = {
        "Rule": Rule,
        "Fix": Fix,
        "Profile": Profile,
        "Relation": Relation,
        "EvidenceSlot": EvidenceSlot,
        "Example": Example,
    }
    scalar: Final[dict[str, JsonValue]] = {
        "type": ["string", "number", "boolean", "null"],
    }
    primitives: Final[dict[str, str]] = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
    }


def _type_schema(*, text: str) -> JsonValue:
    """Translate one annotation string to a schema fragment.

    Args:
        text: Annotation as written in the dataclass.

    Returns:
        The schema fragment.

    Raises:
        ValueError: If the annotation is not supported.

    """
    text = text.strip()
    if text.endswith(" | None"):
        return {
            "anyOf": [
                _type_schema(text=text.removesuffix(" | None")),
                {"type": "null"},
            ],
        }
    if text in Constants.primitives:
        return {"type": Constants.primitives[text]}
    if text in Constants.enums:
        names: list[JsonValue] = [
            m.value
            for m in sorted(Constants.enums[text], key=lambda m: m.value)
        ]
        return {"enum": names}
    if text in Constants.entities or text == "Predicate":
        return {"$ref": f"#/$defs/{text}"}
    if text.startswith("tuple[") and text.endswith(", ...]"):
        inner: str = text.removeprefix("tuple[").removesuffix(", ...]")
        return {"type": "array", "items": _type_schema(text=inner)}
    if text.startswith("Mapping[str, ") and text.endswith("]"):
        inner = text.removeprefix("Mapping[str, ").removesuffix("]")
        values: JsonValue = (
            Constants.scalar
            if inner == "FactValue"
            else _type_schema(text=inner)
        )
        return {"type": "object", "additionalProperties": values}
    msg: str = f"unsupported annotation {text!r}"
    raise ValueError(msg)


def _entity_schema(*, kind: type) -> JsonValue:
    """Describe one dataclass as a JSON object schema.

    Args:
        kind: Dataclass to describe.

    Returns:
        The object schema.

    """
    properties: dict[str, JsonValue] = {}
    required: list[str] = []
    for field in fields(class_or_instance=kind):
        properties[field.name] = _type_schema(text=str(object=field.type))
        if field.default is MISSING and field.default_factory is MISSING:
            required.append(field.name)
    mandatory: list[JsonValue] = list(required)
    return {
        "type": "object",
        "properties": properties,
        "required": mandatory,
        "additionalProperties": False,
    }


def _predicate_schema() -> JsonValue:
    """Describe the predicate algebra.

    Returns:
        The schema of a predicate object.

    """
    ref: JsonValue = {"$ref": "#/$defs/Predicate"}
    return {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "op": {"enum": ["all", "any"]},
                    "of": {"type": "array", "items": ref},
                },
                "required": ["op", "of"],
            },
            {
                "type": "object",
                "properties": {"op": {"const": "not"}, "of": ref},
                "required": ["op", "of"],
            },
            {
                "type": "object",
                "properties": {
                    "op": {"const": "compare"},
                    "fact": {"type": "string"},
                    "cmp": {"enum": ["eq", "ne", "lt", "le", "gt", "ge"]},
                    "value": Constants.scalar,
                },
                "required": ["op", "fact", "cmp", "value"],
            },
            {
                "type": "object",
                "properties": {
                    "op": {"const": "exists"},
                    "selector": {"type": "string"},
                    "where": ref,
                },
                "required": ["op", "selector", "where"],
            },
        ],
    }


def catalog_schema() -> JsonValue:
    """Build the JSON Schema of a catalog.

    Returns:
        A draft 2020-12 schema generated from the entity dataclasses.

    """
    definitions: dict[str, JsonValue] = {
        name: _entity_schema(kind=kind)
        for name, kind in Constants.entities.items()
    }
    definitions["Predicate"] = _predicate_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "astart rule catalog",
        "type": "object",
        "required": ["rules"],
        "properties": {
            "rules": {"type": "array", "items": {"$ref": "#/$defs/Rule"}},
            "fixes": {"type": "array", "items": {"$ref": "#/$defs/Fix"}},
            "profiles": {
                "type": "array",
                "items": {"$ref": "#/$defs/Profile"},
            },
            "relations": {
                "type": "array",
                "items": {"$ref": "#/$defs/Relation"},
            },
        },
        "$defs": definitions,
    }


def schema_text() -> str:
    """Render the schema as canonical JSON.

    Returns:
        Canonical text ending with a newline.

    """
    return canonical_dumps(value=catalog_schema())


def main() -> None:
    """Write ``schema.json`` next to this module."""
    target: Path = Path(__file__).with_name(name="schema.json")
    _ = target.write_text(data=schema_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
