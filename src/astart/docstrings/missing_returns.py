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

from astart.docstrings import function_body_nodes
from astart.docstrings.shared import documented_names
from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from astart.docstrings import DocKind


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject (str): Evidence key for the function name.
        evidence_kind (str): Evidence key for ``returns`` vs ``yields``.

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
        module (Module): Parsed module.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: Candidates in source order.

    """
    candidates: list[Candidate] = []
    for node in walk(node=module):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
            continue
        if not _documented(module=module, owner=node):
            continue
        for kind in result_kinds(node=node):
            if documented_names(module=module, owner=node, kind=kind):
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


def result_kinds(
    *,
    node: FunctionDef | AsyncFunctionDef,
) -> tuple[DocKind, ...]:
    """Classify yielded values and explicit non-None terminal results.

    Nested function, lambda and class bodies own their yields and returns.
    Their defaults, decorators and bases execute in the enclosing scope.

    Args:
        node (FunctionDef | AsyncFunctionDef): Function definition to inspect.

    Returns:
        tuple[DocKind, ...]: Required result documentation kinds, in
            yields-then-returns order.

    """
    yields: bool = False
    returns: bool = False
    for child in function_body_nodes(owner=node):
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
    kinds: list[DocKind] = []
    if yields:
        kinds.append("yields")
    if returns:
        kinds.append("returns")
    return tuple(kinds)


def _documented(
    *,
    module: Module,
    owner: FunctionDef | AsyncFunctionDef,
) -> bool:
    """Answer whether the owner has any docstring entries.

    Args:
        module (Module): Parsed module.
        owner (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        bool: ``True`` when the function is documented at all.

    """
    return any(
        documented_names(module=module, owner=owner, kind=kind)
        for kind in ("parameters", "returns", "yields", "raises")
    ) or _has_prose(owner=owner)


def _has_prose(*, owner: FunctionDef | AsyncFunctionDef) -> bool:
    """Answer whether the owner carries a docstring.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        bool: ``True`` when a docstring exists.

    """
    return get_docstring(node=owner) is not None
