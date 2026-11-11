"""Generate the JSON Schema of the rule catalog from the entity model."""

from __future__ import annotations

from ast import BinOp, BitOr, Constant, Name, Subscript, Tuple, expr, parse
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
        enums (Final[dict[str, type[StrEnum]]]): Grouped module constant.
        entities (Final[dict[str, type]]): Grouped module constant.
        scalar (Final[dict[str, JsonValue]]): Grouped module constant.
        primitives (Final[dict[str, str]]): Grouped module constant.
        variadic_tuple_arity (Final[int]): Element count of ``tuple[X, ...]``.

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
    variadic_tuple_arity: Final[int] = 2


def _schema_node(*, node: expr, source: str) -> JsonValue:
    """Translate one annotation AST node to a schema fragment.

    Args:
        node (expr): Parsed annotation expression.
        source (str): Original annotation text, for error messages.

    Returns:
        JsonValue: The schema fragment.

    Raises:
        ValueError: If the annotation is not supported.

    """
    match node:
        case BinOp(op=BitOr(), left=left, right=right):
            arms: list[JsonValue] = [
                {"type": "null"}
                if isinstance(side, Constant) and side.value is None
                else _schema_node(node=side, source=source)
                for side in (left, right)
            ]
            return _union_schema(arms=arms)
        case Name(id=name):
            return _named_schema(name=name, source=source)
        case Subscript(value=Name(id="tuple"), slice=slice_node):
            elements: list[expr] = (
                list(slice_node.elts)
                if isinstance(slice_node, Tuple)
                else [slice_node]
            )
            if (
                len(elements) == Constants.variadic_tuple_arity
                and isinstance(elements[1], Constant)
                and elements[1].value is Ellipsis
            ):
                return {
                    "type": "array",
                    "items": _schema_node(
                        node=elements[0],
                        source=source,
                    ),
                }
        case Subscript(
            value=Name(id="Mapping"),
            slice=Tuple(elts=[Name(id="str"), inner]),
        ):
            values: JsonValue = (
                Constants.scalar
                if isinstance(inner, Name) and inner.id == "FactValue"
                else _schema_node(node=inner, source=source)
            )
            return {"type": "object", "additionalProperties": values}
        case _:
            pass
    msg: str = f"unsupported annotation {source!r}"
    raise ValueError(msg)


def _union_schema(*, arms: list[JsonValue]) -> JsonValue:
    """Flatten a multi-arm union into one ``anyOf`` fragment.

    Args:
        arms (list[JsonValue]): Schema fragments of each union arm.

    Returns:
        JsonValue: The combined ``anyOf`` fragment.

    """
    flattened: list[JsonValue] = []
    for arm in arms:
        nested: JsonValue | None = (
            arm.get("anyOf") if isinstance(arm, dict) else None
        )
        if isinstance(nested, list):
            flattened.extend(nested)
        else:
            flattened.append(arm)
    return {"anyOf": flattened}


def _named_schema(*, name: str, source: str) -> JsonValue:
    """Translate one bare annotation name to a schema fragment.

    Args:
        name (str): Annotation identifier.
        source (str): Original annotation text, for error messages.

    Returns:
        JsonValue: The schema fragment.

    Raises:
        ValueError: If the annotation is not supported.

    """
    if name in Constants.primitives:
        return {"type": Constants.primitives[name]}
    if name in Constants.enums:
        names: list[JsonValue] = [
            m.value
            for m in sorted(Constants.enums[name], key=lambda m: m.value)
        ]
        return {"enum": names}
    if name in Constants.entities or name == "Predicate":
        return {"$ref": f"#/$defs/{name}"}
    msg: str = f"unsupported annotation {source!r}"
    raise ValueError(msg)


def _type_schema(*, text: str) -> JsonValue:
    """Translate one annotation string to a schema fragment.

    Args:
        text (str): Annotation as written in the dataclass.

    Returns:
        JsonValue: The schema fragment.

    Raises:
        ValueError: If the annotation is not supported.

    """
    source: str = text.strip()
    node: expr = parse(source=source, mode="eval").body
    return _schema_node(node=node, source=source)


def _entity_schema(*, kind: type) -> JsonValue:
    """Describe one dataclass as a JSON object schema.

    Args:
        kind (type): Dataclass to describe.

    Returns:
        JsonValue: The object schema.

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
        JsonValue: The schema of a predicate object.

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
        JsonValue:
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
        str: Canonical text ending with a newline.

    """
    return canonical_dumps(value=catalog_schema())


def main() -> None:
    """Write the canonical schema into the package artifacts directory."""
    target: Path = Path(__file__).parent / "artifacts" / "schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = target.write_text(data=schema_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
