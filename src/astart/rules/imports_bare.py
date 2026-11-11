"""IMP001 ``imports.bare-import``: plain ``import mod`` used as ``mod.attr``.

A bare ``import ast`` that only ever appears as ``ast.walk`` can become
``from ast import walk`` plus rewritten use sites — proven safe when the
imported attributes collide with nothing already bound. This module
detects rewrite candidates; collision checks and the edit live in the
fix.

"""

from __future__ import annotations

from ast import (
    Attribute,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Store,
    expr,
    walk,
)
from typing import TYPE_CHECKING, cast, final

from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_module (str): Evidence key for the imported module.
        evidence_attributes (str): Evidence key for attributes in use.

    """

    evidence_module: str = "module"
    evidence_attributes: str = "attributes"


def find_bare_imports(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag ``import`` statements only used through attribute access.

    A candidate requires that every read of the bound name anchors an
    ``Attribute`` chain covering the import's dotted path
    (``import a.b`` needs ``a.b.something``) and that nothing else in
    the module binds the name, so the evidence is exhaustive.

    Args:
        module (Module): Parsed module.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: Candidates in source order.

    """
    bound: dict[str, int] = _binding_counts(module=module)
    uses: dict[str, _Use] = _uses(module=module)
    candidates: list[Candidate] = []
    for statement in walk(node=module):
        if not isinstance(statement, Import):
            continue
        for entry in statement.names:
            root: str = entry.name.split(sep=".", maxsplit=1)[0]
            if entry.asname is not None or bound.get(root, 0) != 1:
                continue
            prefix: tuple[str, ...] = tuple(entry.name.split(sep=".")[1:])
            use: _Use | None = uses.get(root)
            if use is None or use.bare or not use.chains:
                continue
            attributes: set[str] = set()
            covered: bool = True
            for chain in use.chains:
                if chain[: len(prefix)] != prefix or len(chain) <= len(
                    prefix,
                ):
                    covered = False
                    break
                attributes.add(chain[len(prefix)])
            if not covered or not attributes:
                continue
            candidates.append(
                Candidate(
                    span=span_of(node=statement, filename=filename),
                    evidence={
                        Constants.evidence_module: entry.name,
                        Constants.evidence_attributes: cast(
                            typ="list[JsonValue]",
                            val=sorted(attributes),
                        ),
                    },
                ),
            )
    return tuple(candidates)


@final
class _Use:
    """Attribute chains below a bound name.

    Attributes:
        chains: One full attribute chain per read of the name.
        bare: Whether the name is ever read without an attribute.

    """

    def __init__(self) -> None:
        """Start with no uses."""
        self.chains: list[tuple[str, ...]] = []
        self.bare: bool = False


def _binding_counts(*, module: Module) -> dict[str, int]:
    """Count how many times each name is bound module-wide.

    Args:
        module (Module): Parsed module.

    Returns:
        dict[str, int]: Binding name to number of binding sites.

    """
    counts: dict[str, int] = {}
    for node in walk(node=module):
        if isinstance(node, Name) and isinstance(node.ctx, Store):
            counts[node.id] = counts.get(node.id, 0) + 1
        elif isinstance(node, (Import, ImportFrom)):
            for entry in node.names:
                bound: str = (
                    entry.asname
                    if entry.asname is not None
                    else entry.name.split(sep=".", maxsplit=1)[0]
                )
                counts[bound] = counts.get(bound, 0) + 1
    return counts


def _uses(*, module: Module) -> dict[str, _Use]:
    """Classify every ``Name`` load as chain base or bare use.

    Args:
        module (Module): Parsed module.

    Returns:
        dict[str, _Use]: Bound name to its uses.

    """
    longest: dict[int, tuple[str, ...]] = {}
    roots: dict[int, str] = {}
    for node in walk(node=module):
        if not isinstance(node, Attribute):
            continue
        names: list[str] = []
        cursor: expr = node
        while isinstance(cursor, Attribute):
            names.append(cursor.attr)
            cursor = cursor.value
        if not isinstance(cursor, Name):
            continue
        chain: tuple[str, ...] = tuple(reversed(names))
        base: int = id(cursor)
        if len(chain) > len(longest.get(base, ())):
            longest[base] = chain
            roots[base] = cursor.id
    uses: dict[str, _Use] = {}
    for node in walk(node=module):
        if not (isinstance(node, Name) and isinstance(node.ctx, Load)):
            continue
        use: _Use = uses.setdefault(node.id, _Use())
        member: tuple[str, ...] | None = longest.get(id(node))
        if member is None:
            use.bare = True
        else:
            use.chains.append(member)
    return uses
