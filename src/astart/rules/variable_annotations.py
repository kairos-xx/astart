"""TYP005 ``typing.missing-variable-annotation`` detector.

Flags simple-name assignments whose value has a stable, known inferred
type but which carry no annotation — candidates for an annotation the
tool could propose.  Refuses whenever inference is ``Unknown``,
unstable, or the name is already annotated, private, or a dunder.

Standalone detector; catalog wiring is deferred (M8-22).
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    Name,
    Store,
    arg,
    iter_child_nodes,
)
from typing import TYPE_CHECKING

from astart.rules.procedural import Candidate, span_of

if TYPE_CHECKING:
    from astart.ast import CommentedModule
    from astart.semantic.type_inference import TypeInference, TypeShape


def _annotated_names(*, module: CommentedModule) -> set[str]:
    """Names that already carry an annotation anywhere in the module.

    Args:
        module: Parsed module.

    Returns:
        Annotated binding names.

    """
    names: set[str] = set()
    stack: list[AST] = list(module.body)
    while stack:
        current: AST = stack.pop()
        if isinstance(current, AnnAssign):
            target: AST = current.target
            if isinstance(target, Name):
                names.add(target.id)
            elif isinstance(target, Attribute) and isinstance(
                target.value,
                Name,
            ):
                names.add(f"{target.value.id}.{target.attr}")
        elif isinstance(current, (arg,)):
            if current.annotation is not None:
                names.add(current.arg)
        stack.extend(iter_child_nodes(node=current))
    return names


def _assignments(*, module: CommentedModule) -> list[Assign]:
    """Every ``Assign`` node, including nested scopes.

    Args:
        module: Parsed module.

    Returns:
        Assign nodes in source order.

    """
    found: list[Assign] = []
    stack: list[AST] = list(module.body)
    while stack:
        current: AST = stack.pop()
        if isinstance(current, Assign):
            found.append(current)
        stack.extend(iter_child_nodes(node=current))
    found.reverse()
    return found


def _eligible_name(*, name: str, annotated: set[str]) -> bool:
    """Whether ``name`` may be flagged for a missing annotation.

    Args:
        annotated: Names already annotated in the module.
        name: Candidate binding name.

    Returns:
        ``True`` when the name is a plain public identifier.

    """
    return (
        name not in annotated
        and not name.startswith("_")
        and name.isidentifier()
    )


def find_missing_variable_annotations(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag unannotated assignments with a known inferred type.

    Args:
        filename: Source name for spans.
        module: Parsed module.

    Returns:
        Candidates for each annotatable assignment.

    """
    annotated: set[str] = _annotated_names(module=module)
    candidates: list[Candidate] = []
    for node in _assignments(module=module):
        names: list[str] = [
            target.id
            for target in node.targets
            if isinstance(target, Name) and isinstance(target.ctx, Store)
        ]
        if not names or any(
            not _eligible_name(name=name, annotated=annotated)
            for name in names
        ):
            continue
        inference: TypeInference = module.infer_type(node=node.value)
        actual: TypeShape = inference.inferred
        if str(object=actual) == "Unknown" or not inference.stable:
            continue
        candidates.extend(
            Candidate(
                span=span_of(node=node, filename=filename),
                evidence={
                    "name": name,
                    "inferred": str(object=actual),
                },
            )
            for name in names
        )
    return tuple(candidates)
