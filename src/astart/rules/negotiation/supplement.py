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
        module (AST): Parsed module.

    Returns:
        dict[int, AST]: Parent node by child identity.

    """
    found: dict[int, AST] = {}
    for parent in walk(node=module):
        for child in iter_child_nodes(node=parent):
            found[id(child)] = parent
    return found


def class_boundaries(*, module: AST) -> dict[str, int]:
    """Index the latest definition end for each class name in one walk.

    Keep the existing conservative treatment of duplicate and nested class
    names. The index belongs to this module snapshot and must be rebuilt
    after structural edits; no module-global cache is retained.

    Args:
        module (AST): Parsed module to index.

    Returns:
        dict[str, int]: Last definition end line per class name, across all
            scopes.

    """
    found: dict[str, int] = {}
    for node in walk(node=module):
        if isinstance(node, ClassDef):
            found[node.name] = max(
                found.get(node.name, 0),
                node.end_lineno or 0,
            )
    return found


def bound_when_evaluated(
    *,
    node: AST,
    source: str,
    module: AST,
    parents: dict[int, AST],
    classes: Mapping[str, int] | None = None,
) -> bool:
    """Tell whether an annotation's class names exist when it is evaluated.

    A signature annotation runs when its ``def`` runs. For a function at
    module or class level that is while the module loads, so it may only name
    module classes that are completely defined before the ``def`` and that do
    not contain it. Functions nested in function bodies run later.

    Args:
        node (AST): The parameter or function the annotation belongs to.
        source (str): The annotation text.
        module (AST): Parsed module.
        parents (dict[int, AST]): Parent map of the module.
        classes (Mapping[str, int] | None): Class-definition ends for this
            module
            snapshot; ``None`` builds a private index.

    Returns:
        bool: ``True`` when every module class named is already bound.

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
    boundaries: Mapping[str, int] = (
        class_boundaries(module=module) if classes is None else classes
    )
    return all(boundaries.get(name, 0) < function.lineno for name in named)


def negotiated_hints(
    *,
    module: CommentedModule,
    proposals: Mapping[Key, str],
) -> dict[Key, Hint]:
    """Find the parameter and return annotations negotiation justifies.

    Args:
        module (CommentedModule): Parsed module.
        proposals (Mapping[Key, str]): The inference engine's proposals by node
            identity, used
            only to corroborate types other evidence supports.

    Returns:
        dict[Key, Hint]: A hint per parameter or function, by node identity.

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
    classes: dict[str, int] = class_boundaries(module=module)
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
                classes=classes,
            )
        ):
            found[node_key(node=node)] = Hint(
                source=source,
                basis=HintBasis.negotiated,
            )
    return found
