"""Verify the generated JSON Schema of the rule catalog."""

from __future__ import annotations

from dataclasses import fields
from importlib.resources import files
from json import loads
from typing import TYPE_CHECKING

from astart.rules.model import Fix, Profile, Relation, Rule
from astart.rules.schema import catalog_schema, schema_text
from astart.rules.vocabulary import Severity

from tests.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


def _object(*, value: JsonValue) -> dict[str, JsonValue]:
    """Narrow a JSON value to an object.

    Args:
        value: Value expected to be an object.

    Returns:
        The object.

    Raises:
        TypeError: If the value is not an object.

    """
    match value:
        case dict():
            return value
        case _:
            msg: str = f"expected a JSON object, got {value!r}"
            raise TypeError(msg)


def _list(*, value: JsonValue) -> list[JsonValue]:
    """Narrow a JSON value to a list.

    Args:
        value: Value expected to be a list.

    Returns:
        The list.

    Raises:
        TypeError: If the value is not a list.

    """
    match value:
        case list():
            return value
        case _:
            msg: str = f"expected a JSON list, got {value!r}"
            raise TypeError(msg)


def _definition(*, name: str) -> dict[str, JsonValue]:
    """Return one entry of the schema's definitions.

    Args:
        name: Definition name.

    Returns:
        The definition object.

    """
    schema: dict[str, JsonValue] = _object(value=catalog_schema())
    definitions: dict[str, JsonValue] = _object(value=schema["$defs"])
    return _object(value=definitions[name])


def test_schema_lists_every_entity_field() -> None:
    """Describe each dataclass field of each entity."""
    for name, kind in (
        ("Rule", Rule),
        ("Fix", Fix),
        ("Profile", Profile),
        ("Relation", Relation),
    ):
        properties: dict[str, JsonValue] = _object(
            value=_definition(name=name)["properties"],
        )
        for field in fields(class_or_instance=kind):
            expect_in(item=field.name, container=properties)


def test_committed_schema_matches_generated() -> None:
    """Keep the shipped schema file in sync with the model."""
    committed: str = (
        files("astart.rules").joinpath("schema.json").read_text("utf-8")
    )
    expect_equal(actual=committed, expected=schema_text())
    expect_true(condition=isinstance(loads(s=committed), dict))


def test_rule_requires_documented_enums() -> None:
    """Enumerate severities and mark mandatory fields."""
    rule: dict[str, JsonValue] = _definition(name="Rule")
    properties: dict[str, JsonValue] = _object(value=rule["properties"])
    severity: dict[str, JsonValue] = _object(value=properties["severity"])
    expect_equal(
        actual=severity["enum"],
        expected=sorted(member.value for member in Severity),
    )
    required: list[JsonValue] = _list(value=rule["required"])
    expect_in(item="key", container=required)
    expect_true(condition="fixes" not in required)
