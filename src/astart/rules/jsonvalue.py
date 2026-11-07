"""JSON value type and canonical serialization for the rule catalog."""

from __future__ import annotations

from json import dumps

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)


def canonical_dumps(*, value: JsonValue) -> str:
    """Serialize a value with sorted keys and a trailing newline.

    Args:
        value: JSON-compatible value to serialize.

    Returns:
        Stable text, two-space indented, ending with a newline.

    """
    return (
        dumps(obj=value, indent=2, sort_keys=True, ensure_ascii=False)
        + """\

"""
    )
