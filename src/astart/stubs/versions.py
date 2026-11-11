"""Which stdlib modules exist in which Python versions (``VERSIONS``)."""

from __future__ import annotations

from typing import Final, final

type Version = tuple[int, int]
type Span = tuple[Version, Version | None]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        comment (Final[str]): Character that starts a comment line.

    """

    comment: Final[str] = "#"


def _version(*, text: str) -> Version:
    """Read ``3.11`` as ``(3, 11)``.

    Args:
        text (str): A version such as ``3.9``.

    Returns:
        Version: The version tuple.

    """
    major, _, minor = text.strip().partition(".")
    return int(major), int(minor or 0)


def parse_versions(*, text: str) -> dict[str, Span]:
    """Parse typeshed's ``stdlib/VERSIONS`` file.

    Args:
        text (str): File contents: ``module: 3.9-3.12`` lines, the upper bound
            optional.

    Returns:
        dict[str, Span]: For each module, the first version that has it and the
            first
            that no longer has it (``None`` when it still exists).

    """
    table: dict[str, Span] = {}
    for raw in text.splitlines():
        line: str = raw.split(sep=Constants.comment, maxsplit=1)[0].strip()
        if ":" not in line:
            continue
        name, _, span = line.partition(":")
        low, _, high = span.strip().partition("-")
        table[name.strip()] = (
            _version(text=low),
            _version(text=high) if high.strip() else None,
        )
    return table


def module_available(
    *,
    table: dict[str, Span],
    module: str,
    version: Version,
) -> bool:
    """Tell whether a stdlib module exists in a Python version.

    A submodule inherits the entry of its nearest listed parent.

    Args:
        table (dict[str, Span]): The parsed ``VERSIONS``.
        module (str): Dotted module name.
        version (Version): The Python version asked about.

    Returns:
        bool: ``True`` when listed for that version, or not listed at all.

    """
    parts: list[str] = module.split(sep=".")
    for end in range(len(parts), 0, -1):
        span: Span | None = table.get(".".join(parts[:end]))
        if span is None:
            continue
        low, high = span
        return version >= low and (high is None or version <= high)
    return True
