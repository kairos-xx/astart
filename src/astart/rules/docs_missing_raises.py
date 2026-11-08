"""DOC006 ``docs.missing-raises``: raised exception not documented.

A documented function should name the exceptions callers can see.  The
detector flags ``raise X`` statements whose exception is absent from the
docstring's ``raises`` entries; undocumented functions are DOC001's job.
"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Attribute,
    Call,
    FunctionDef,
    Module,
    Name,
    Raise,
    expr,
    get_docstring,
    walk,
)
from typing import TYPE_CHECKING, cast, final

from astart.rules.docs_shared import documented_names
from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the function name.
        evidence_exceptions: Evidence key for undocumented raises.

    """

    evidence_subject: str = "function"
    evidence_exceptions: str = "exceptions"


def find_missing_raises(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag raised exceptions missing from ``raises`` entries.

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
        if get_docstring(node=node) is None:
            continue
        raised: set[str] = _raised_names(node=node)
        if not raised:
            continue
        documented: frozenset[str] = frozenset(
            name
            for name in documented_names(
                module=module,
                owner=node,
                kind="raises",
            )
            if name is not None
        )
        missing: list[str] = sorted(raised - documented)
        if missing:
            candidates.append(
                Candidate(
                    span=span_of(node=node, filename=filename),
                    evidence={
                        Constants.evidence_subject: node.name,
                        Constants.evidence_exceptions: cast(
                            typ="list[JsonValue]",
                            val=missing,
                        ),
                    },
                ),
            )
    return tuple(candidates)


def _raised_names(*, node: FunctionDef | AsyncFunctionDef) -> set[str]:
    """Collect exception names raised directly in a function body.

    Args:
        node: Function definition.

    Returns:
        Raised exception names, nested functions excluded.

    """
    nested: set[int] = set()
    for child in walk(node=node):
        if child is not node and isinstance(
            child,
            (FunctionDef, AsyncFunctionDef),
        ):
            nested.update(id(item) for item in walk(node=child))
    names: set[str] = set()
    for child in walk(node=node):
        if id(child) in nested or not isinstance(child, Raise):
            continue
        name: str | None = _exception_name(exc=child.exc)
        if name is not None:
            names.add(name)
    return names


def _exception_name(*, exc: expr | None) -> str | None:
    """Spell the exception class a ``raise`` target names.

    Args:
        exc: The ``raise`` expression.

    Returns:
        The exception's name, or ``None`` when indeterminate.

    """
    match exc:
        case Name(id=name):
            return name
        case Attribute(attr=name):
            return name
        case Call(func=func):
            return _exception_name(exc=func)
        case _:
            return None
