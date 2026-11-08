"""TYP002 ``typing.no-object-annotation``: annotations spelled ``object``.

``x: object`` says nothing — any value fits — so astart treats it as a
missing annotation.  The detector flags ``object`` (and
``builtins.object``) wherever it appears as a parameter, return or
variable annotation, including inside string annotations.
"""

from __future__ import annotations

from ast import (
    AnnAssign,
    Attribute,
    Constant,
    FunctionDef,
    Module,
    Name,
    arg,
    walk,
)
from typing import TYPE_CHECKING, final

from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from ast import AST, expr


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the annotated subject.
        evidence_annotation: Evidence key for the annotation text.

    """

    evidence_subject: str = "subject"
    evidence_annotation: str = "annotation"


def find_object_annotations(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag annotations whose meaning is exactly ``object``.

    Args:
        module: Parsed module.
        filename: Name used in spans.

    Returns:
        Candidates in source order.

    """
    candidates: list[Candidate] = []
    for node in walk(node=module):
        if (
            isinstance(node, arg)
            and _is_object(annotation=node.annotation)
            and node.annotation
        ):
            candidates.append(
                _candidate(
                    node=node.annotation,
                    filename=filename,
                    subject=node.arg,
                ),
            )
        elif (
            isinstance(node, FunctionDef)
            and _is_object(
                annotation=node.returns,
            )
            and node.returns
        ):
            candidates.append(
                _candidate(
                    node=node.returns,
                    filename=filename,
                    subject=node.name,
                ),
            )
        elif isinstance(node, AnnAssign) and _is_object(
            annotation=node.annotation,
        ):
            candidates.append(
                _candidate(
                    node=node.annotation,
                    filename=filename,
                    subject=_subject_name(target=node.target),
                ),
            )
    return tuple(candidates)


def _is_object(*, annotation: expr | None) -> bool:
    """Answer whether an annotation expression spells ``object``.

    Args:
        annotation: Annotation expression, or ``None``.

    Returns:
        ``True`` for ``object``, ``builtins.object`` or the string
        ``"object"``.

    """
    match annotation:
        case Name(id="object"):
            return True
        case Attribute(attr="object", value=Name(id="builtins")):
            return True
        case Constant(value=str() as text):
            return text.strip() in {"object", "builtins.object"}
        case _:
            return False


def _subject_name(*, target: expr) -> str:
    """Spell an annotated assignment's target for evidence.

    Args:
        target: The ``AnnAssign`` target.

    Returns:
        A readable subject name.

    """
    match target:
        case Name(id=name) | Attribute(attr=name):
            return name
        case _:
            return "<target>"


def _candidate(*, node: AST, filename: str, subject: str) -> Candidate:
    """Build the candidate for one flagged annotation.

    Args:
        node: Annotation node to span.
        filename: Name used in the span.
        subject: Annotated subject for evidence.

    Returns:
        The candidate.

    """
    return Candidate(
        span=span_of(node=node, filename=filename),
        evidence={
            Constants.evidence_subject: subject,
            Constants.evidence_annotation: "object",
        },
    )
