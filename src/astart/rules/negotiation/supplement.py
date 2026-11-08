"""Negotiated parameter and return annotations for the hint index."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    Name,
    iter_child_nodes,
    parse,
    walk,
)
from typing import TYPE_CHECKING

from astart.rules.hints import (
    Hint,
    HintBasis,
    allowed_names,
    escaped_function_names,
    is_allowed_source,
    node_key,
)
from astart.rules.negotiation.run import (
    function_nodes,
    function_paths,
    negotiate_module,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import CommentedModule
    from astart.rules.hints import Key
    from astart.rules.negotiation.run import Verdicts


def parents_of(*, module: AST) -> dict[int, AST]:
    """Map each node of the module to its parent.

    Args:
        module: Parsed module.

    Returns:
        Parent node by child identity.

    """
    found: dict[int, AST] = {}
    for parent in walk(node=module):
        for child in iter_child_nodes(node=parent):
            found[id(child)] = parent
    return found


def bound_when_evaluated(
    *,
    node: AST,
    source: str,
    module: AST,
    parents: dict[int, AST],
) -> bool:
    """Tell whether an annotation's class names exist when it is evaluated.

    A signature annotation runs when its ``def`` runs. For a function at
    module or class level that is while the module loads, so it may only name
    module classes that are completely defined before the ``def`` and that do
    not contain it. Functions nested in function bodies run later.

    Args:
        node: The parameter or function the annotation belongs to.
        source: The annotation text.
        module: Parsed module.
        parents: Parent map of the module.

    Returns:
        ``True`` when every module class named is already bound.

    """
    function: AST | None = node
    while function is not None and not isinstance(
        function,
        (FunctionDef, AsyncFunctionDef),
    ):
        function = parents.get(id(function))
    if function is None:
        return True
    ancestor: AST | None = parents.get(id(function))
    while ancestor is not None:
        if isinstance(ancestor, (FunctionDef, AsyncFunctionDef)):
            return True
        ancestor = parents.get(id(ancestor))
    named: set[str] = {
        part.id
        for part in walk(node=parse(source=source, mode="eval"))
        if isinstance(part, Name)
    }
    return all(
        not (
            isinstance(cls, ClassDef)
            and cls.name in named
            and (cls.end_lineno or 0) >= function.lineno
        )
        for cls in walk(node=module)
    )


def negotiated_hints(
    *,
    module: CommentedModule,
    proposals: Mapping[Key, str],
) -> dict[Key, Hint]:
    """Find the parameter and return annotations negotiation justifies.

    Args:
        module: Parsed module.
        proposals: The inference engine's proposals by node identity, used
            only to corroborate types other evidence supports.

    Returns:
        A hint per parameter or function, by node identity.

    """
    paths: dict[Key, str] = function_paths(module=module)
    verdicts: Verdicts = negotiate_module(
        module=module,
        corroboration={
            paths[key]: text for key, text in proposals.items() if key in paths
        },
        escaped=escaped_function_names(module=module),
    )
    nodes: dict[str, AST] = function_nodes(module=module)
    known: frozenset[str] = allowed_names(module=module)
    parents: dict[int, AST] = parents_of(module=module)
    found: dict[Key, Hint] = {}
    for path, source in sorted(verdicts.accepted.items()):
        node: AST | None = nodes.get(path)
        if (
            node is not None
            and is_allowed_source(source=source, known_names=known)
            and bound_when_evaluated(
                node=node,
                source=source,
                module=module,
                parents=parents,
            )
        ):
            found[node_key(node=node)] = Hint(
                source=source,
                basis=HintBasis.negotiated,
            )
    return found
