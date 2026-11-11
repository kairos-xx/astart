"""Lightweight type-source model for the from-scratch inference engine.

Types are represented as their rendered annotation source (e.g. ``"int"``,
``"list[int]"``, ``"int | None"``). ``object`` is the sound top type used
whenever evidence is insufficient, so the engine never emits a contradictory
annotation.

"""

from __future__ import annotations

from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        none (Final[str]): Grouped module constant.
        object (Final[str]): Grouped module constant.
        int (Final[str]): Grouped module constant.
        float (Final[str]): Grouped module constant.
        bool (Final[str]): Grouped module constant.
        bytes (Final[str]): Grouped module constant.
        str (Final[str]): Grouped module constant.

    """

    none: Final[str] = "None"
    object: Final[str] = "object"
    int: Final[str] = "int"
    float: Final[str] = "float"
    bool: Final[str] = "bool"
    bytes: Final[str] = "bytes"
    str: Final[str] = "str"


def optional(source: str) -> str:
    """Return ``source | None`` without duplicating an existing ``None``.

    Args:
        source (str): The source examined while return ``source | None``
            without duplicating an existing ``None``.

    Returns:
        str: Rendered source text produced by this operation.

    """
    if source == Constants.none:
        return Constants.none
    members: list[str] = split_union(source=source)
    if Constants.none in members:
        return source
    return union(*members, Constants.none)


def union(*sources: str) -> str:
    """Combine type sources into a normalized union string.

    ``object`` absorbs everything; duplicates collapse; ``None`` sorts last.

    Args:
        sources (str): Sources supplied as str for this operation.

    Returns:
        str: Rendered source text produced by this operation.

    """
    members: list[str] = []
    for source in sources:
        for member in split_union(source=source):
            if member and member not in members:
                members.append(member)
    if Constants.object in members:
        return Constants.object
    if not members:
        return Constants.object
    if len(members) == 1:
        return members[0]
    ordered: list[str] = sorted(
        members,
        key=lambda m: (m == Constants.none, m),
    )
    return " | ".join(ordered)


def split_union(source: str) -> list[str]:
    """Split a PEP 604 union source at top-level ``|`` boundaries.

    Args:
        source (str): The source examined while split a PEP 604 union source at
            top-level ``|`` boundaries.

    Returns:
        list[str]: list[str] produced by this operation.

    """
    parts: list[str] = []
    depth: int = 0
    current: list[str] = []
    for char in source:
        if char in "[(":
            depth += 1
        elif char in "])":
            depth = max(0, depth - 1)
        if char == "|" and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    tail: str = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts
