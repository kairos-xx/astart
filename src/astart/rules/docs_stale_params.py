"""DOC003 ``docs.stale-parameter``: documented name with no parameter.

A docstring that names a parameter the signature no longer has is worse
than none: it misleads readers.  The detector compares documented
``parameters`` entries against the declared signature.
"""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, Module, walk
from typing import TYPE_CHECKING, cast, final

from astart.rules.docs_shared import documented_names, parameter_names
from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the function name.
        evidence_parameters: Evidence key for the stale names.

    """

    evidence_subject: str = "function"
    evidence_parameters: str = "parameters"


def find_stale_parameters(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag docstring parameters missing from the signature.

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
        declared: frozenset[str] = frozenset(
            parameter_names(owner=node),
        )
        variadics: set[str] = {
            param.arg
            for param in (node.args.vararg, node.args.kwarg)
            if param is not None
        }
        stale: list[str] = [
            name
            for name in documented_names(
                module=module,
                owner=node,
                kind="parameters",
            )
            if name is not None
            and name not in declared
            and name not in variadics
        ]
        if stale:
            candidates.append(
                Candidate(
                    span=span_of(node=node, filename=filename),
                    evidence={
                        Constants.evidence_subject: node.name,
                        Constants.evidence_parameters: cast(
                            typ="list[JsonValue]",
                            val=stale,
                        ),
                    },
                ),
            )
    return tuple(candidates)
