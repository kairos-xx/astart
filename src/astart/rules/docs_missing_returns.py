"""DOC004 ``docs.missing-returns``: value-returning function, no section.

A function that returns a value (or yields) should say what comes back.
The detector flags documented functions that produce values but have no
``returns``/``yields`` entries; undocumented functions are DOC001's job.
"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Constant,
    FunctionDef,
    Module,
    Return,
    Yield,
    YieldFrom,
    get_docstring,
    walk,
)
from typing import TYPE_CHECKING, final

from astart.rules.docs_shared import documented_names

if TYPE_CHECKING:
    from astart.docstrings import DocKind
from astart.rules.procedural import Candidate, span_of


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the function name.
        evidence_kind: Evidence key for ``returns`` vs ``yields``.

    """

    evidence_subject: str = "function"
    evidence_kind: str = "kind"


def find_missing_returns(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag value-producing functions lacking returns/yields entries.

    Args:
        module: Parsed module.
        filename: Name used in spans.

    Returns:
        Candidates in source order.

    """
    candidates: list[Candidate] = []
    for node in walk(node=module):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
            continue
        produces: str | None = _produces(node=node)
        if produces is None or not _documented(
            module=module,
            owner=node,
        ):
            continue
        kind: DocKind = "yields" if produces == "yields" else "returns"
        if documented_names(
            module=module,
            owner=node,
            kind=kind,
        ):
            continue
        candidates.append(
            Candidate(
                span=span_of(node=node, filename=filename),
                evidence={
                    Constants.evidence_subject: node.name,
                    Constants.evidence_kind: kind,
                },
            ),
        )
    return tuple(candidates)


def _produces(*, node: FunctionDef | AsyncFunctionDef) -> str | None:
    """Classify what a function produces, if anything.

    Args:
        node: Function definition.

    Returns:
        ``"yields"``, ``"returns"`` or ``None``.

    """
    yields: bool = False
    returns: bool = False
    nested: set[int] = set()
    for child in walk(node=node):
        if child is not node and isinstance(
            child,
            (FunctionDef, AsyncFunctionDef),
        ):
            nested.update(id(item) for item in walk(node=child))
    for child in walk(node=node):
        if id(child) in nested:
            continue
        if isinstance(child, (Yield, YieldFrom)):
            yields = True
        elif (
            isinstance(child, Return)
            and child.value is not None
            and not (
                isinstance(child.value, Constant) and child.value.value is None
            )
        ):
            returns = True
    if yields:
        return "yields"
    return "returns" if returns else None


def _documented(
    *,
    module: Module,
    owner: FunctionDef | AsyncFunctionDef,
) -> bool:
    """Answer whether the owner has any docstring entries.

    Args:
        module: Parsed module.
        owner: Function definition.

    Returns:
        ``True`` when the function is documented at all.

    """
    return any(
        documented_names(module=module, owner=owner, kind=kind)
        for kind in ("parameters", "returns", "yields", "raises")
    ) or _has_prose(owner=owner)


def _has_prose(*, owner: FunctionDef | AsyncFunctionDef) -> bool:
    """Answer whether the owner carries a docstring.

    Args:
        owner: Function definition.

    Returns:
        ``True`` when a docstring exists.

    """
    return get_docstring(node=owner) is not None
