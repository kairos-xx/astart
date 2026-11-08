"""DOC001 ``docs.missing-docstring``: definitions without docstrings.

Flags modules, classes and functions whose first statement is not a
docstring.  Private names (``_leading``) are exempt, matching the
convention that internal helpers do not owe prose.
"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    Module,
    get_docstring,
    walk,
)
from typing import final

from astart.rules.procedural import Candidate, span_of


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the undocumented name.
        evidence_kind: Evidence key for the definition kind.

    """

    evidence_subject: str = "subject"
    evidence_kind: str = "kind"


def find_missing_docstrings(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag documented-definition nodes that carry no docstring.

    Args:
        module: Parsed module.
        filename: Name used in spans.

    Returns:
        Candidates in source order.

    """
    candidates: list[Candidate] = []
    if get_docstring(node=module) is None:
        candidates.append(
            Candidate(
                span=span_of(node=module, filename=filename),
                evidence={
                    Constants.evidence_subject: "<module>",
                    Constants.evidence_kind: "module",
                },
            ),
        )
    for node in walk(node=module):
        if not isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            continue
        if node.name.startswith("_") or get_docstring(node=node) is not None:
            continue
        kind: str = (
            "class"
            if isinstance(node, ClassDef)
            else (
                "async function"
                if isinstance(node, AsyncFunctionDef)
                else "function"
            )
        )
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
