"""Validate real ``astart check --format json`` output against the schemas.

``docs/schema/report.json`` and ``docs/schema/finding.json`` describe the
native JSON report (API-06). The validator below implements the small
subset of JSON Schema 2020-12 the schemas use — ``type``, ``required``,
``properties``, ``items``, ``enum``, ``minimum``, ``additionalProperties``
and ``$ref`` — so no dependency is needed.

"""

from json import loads
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

from astart.cli.render import FileReport, render_json
from astart.rules import (
    Catalog,
    CheckResult,
    check,
    default_registries,
    load_default_catalog,
)

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source (Final[str]): Grouped module constant.
        broken (Final[str]): Grouped module constant.
        schema_dir (Final[Path]): Grouped module constant.

    """

    source: Final[str] = """\
from typing import Any


def f(x: Any):
    return x
"""
    broken: Final[str] = """\
def broken(:
"""

    schema_dir: Final[Path] = Paths.root / "docs" / "schema"


Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None


def _type_name(value: Json) -> str:
    """Return the JSON Schema type name of a decoded value.

    Args:
        value (Json): Decoded JSON value.

    Returns:
        str: One of ``null``, ``boolean``, ``integer``, ``number``, ``string``,
            ``array``, ``object``.

    """
    name: str = "object"
    if value is None:
        name = "null"
    elif isinstance(value, bool):
        name = "boolean"
    elif isinstance(value, int):
        name = "integer"
    elif isinstance(value, float):
        name = "number"
    elif isinstance(value, str):
        name = "string"
    elif isinstance(value, list):
        name = "array"
    return name


def _scalar_problems(*, value: Json, schema: dict[str, Json]) -> list[str]:
    """Check ``type``, ``enum`` and ``minimum`` against a scalar value.

    Args:
        value (Json): Decoded JSON instance.
        schema (dict[str, Json]): Schema object holding the scalar keywords.

    Returns:
        list[str]: Violations found; empty when the scalar conforms.

    """
    problems: list[str] = []
    kind: Json = schema.get("type")
    allowed: list[str] = (
        [kind]
        if isinstance(kind, str)
        else [str(object=item) for item in kind]
        if isinstance(kind, list)
        else []
    )
    if allowed and _type_name(value=value) not in allowed:
        return [f"type {_type_name(value=value)} not in {allowed}"]
    enum: Json = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        problems.append(f"{value!r} not in enum {enum!r}")
    minimum: Json = schema.get("minimum")
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and isinstance(minimum, int)
        and value < minimum
    ):
        problems.append(f"{value} < minimum {minimum}")
    return problems


def _object_problems(
    *,
    value: dict[str, Json],
    schema: dict[str, Json],
    base: Path,
) -> list[str]:
    """Check ``required``, ``properties`` and ``additionalProperties``.

    Args:
        value (dict[str, Json]): Decoded JSON object.
        schema (dict[str, Json]): Schema object holding the object keywords.
        base (Path): Directory used to resolve relative ``$ref`` targets.

    Returns:
        list[str]: Violations found; empty when the object conforms.

    """
    problems: list[str] = []
    required: Json = schema.get("required")
    if isinstance(required, list):
        problems.extend(
            f"missing required key {key!r}"
            for key in required
            if key not in value
        )
    properties: Json = schema.get("properties")
    props: dict[str, Json] = properties if isinstance(properties, dict) else {}
    for key, subschema in props.items():
        if key in value:
            problems.extend(
                _validate(value=value[key], schema=subschema, base=base),
            )
    if schema.get("additionalProperties") is False:
        problems.extend(
            f"unexpected key {key!r}"
            for key in sorted(value)
            if key not in props
        )
    return problems


def _array_problems(
    *,
    value: list[Json],
    schema: dict[str, Json],
    base: Path,
) -> list[str]:
    """Check every element of an array against the ``items`` schema.

    Args:
        value (list[Json]): Decoded JSON array.
        schema (dict[str, Json]): Schema object holding the ``items`` keyword.
        base (Path): Directory used to resolve relative ``$ref`` targets.

    Returns:
        list[str]: Violations found; empty when every element conforms.

    """
    items: Json = schema.get("items")
    if not isinstance(items, dict):
        return []
    problems: list[str] = []
    for index, item in enumerate(iterable=value):
        problems.extend(
            f"[{index}] {problem}"
            for problem in _validate(value=item, schema=items, base=base)
        )
    return problems


def _validate(*, value: Json, schema: Json, base: Path) -> list[str]:
    """Check ``value`` against the schema subset, returning problems.

    Args:
        value (Json): Decoded JSON instance.
        schema (Json): Schema object (may contain ``$ref`` resolved against
            ``base``).
        base (Path): Directory used to resolve relative ``$ref`` targets.

    Returns:
        list[str]: Human-readable violations; empty when the value conforms.

    """
    if not isinstance(schema, dict):
        return []
    ref: Json = schema.get("$ref")
    if isinstance(ref, str):
        target: Path = (base / ref).resolve()
        resolved: Json = loads(s=target.read_text(encoding="utf-8"))
        return _validate(value=value, schema=resolved, base=target.parent)
    problems: list[str] = _scalar_problems(value=value, schema=schema)
    if problems:
        return problems
    if isinstance(value, dict):
        problems.extend(
            _object_problems(value=value, schema=schema, base=base),
        )
    elif isinstance(value, list):
        problems.extend(_array_problems(value=value, schema=schema, base=base))
    return problems


def _document() -> Json:
    """Render a real check run as the JSON report document.

    Returns:
        Json: One file report with findings plus one file report carrying a
            parse error, decoded from ``render_json``.

    """
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    result: CheckResult = check(
        source=Constants.source,
        filename="a.py",
        catalog=catalog,
        registries=registries,
    )
    reports: list[FileReport] = [
        FileReport(path="a.py", findings=result.findings, error=None),
        FileReport(path="broken.py", findings=(), error="cannot parse"),
    ]
    return loads(s=render_json(results=reports, catalog=catalog))


def _schema(name: str) -> Json:
    """Load one schema file from ``docs/schema``.

    Args:
        name (str): Schema file name.

    Returns:
        Json: The decoded schema object.

    """
    return loads(s=(Constants.schema_dir / name).read_text(encoding="utf-8"))


def test_report_matches_schema() -> None:
    """Real JSON output conforms to ``docs/schema/report.json``."""
    problems: list[str] = _validate(
        value=_document(),
        schema=_schema(name="report.json"),
        base=Constants.schema_dir,
    )
    expect_equal(actual=problems, expected=[])


def test_finding_schema_rejects_bad_shapes() -> None:
    """The validator catches a finding missing keys and wrong types."""
    bad: Json = {"rule": 1, "severity": "fatal", "fixes": "TYP001"}
    problems: list[str] = _validate(
        value=bad,
        schema=_schema(name="finding.json"),
        base=Constants.schema_dir,
    )
    expect_equal(actual=len(problems) > 0, expected=True)
