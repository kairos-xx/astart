"""Annotations from the inference engine, for conversion mode.

The engine (``astart.graph``, descended from the author's earlier converter)
annotates far more than the evidence-based pipeline will accept: it needs no
second signal. Conversion mode (``--engine``) takes its result for the nodes
nothing else decided, at the lowest confidence tier, and leaves it to the
type checker's gate to veto the ones that cause new errors.

"""

from __future__ import annotations

from ast import AnnAssign, Name, unparse
from ast import parse as ast_parse
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, final

from astart.rules.hints import (
    Hint,
    HintBasis,
    allowed_names,
    is_allowed_source,
    node_key,
)
from astart.rules.negotiation.builders import walk_functions
from astart.rules.negotiation.run import function_nodes
from astart.rules.negotiation.supplement import (
    bound_when_evaluated,
    class_boundaries,
    parents_of,
)
from astart.rules.provable import own_nodes
from astart.source.api import parse

if TYPE_CHECKING:
    from ast import AST, expr

    from astart import CommentedModule
    from astart.rules.hints import Key


@final
class Constants:
    """Group module-level constants.

    Attributes:
        failures (Final[tuple[type[Exception], ...]]): Exceptions the engine
            may raise on odd input; the
            module is then left to the evidence-based pipeline.

    """

    failures: Final[tuple[type[Exception], ...]] = (
        AttributeError,
        IndexError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
        SyntaxError,
    )


@final
class LazyConversion:
    """Run the engine on a module once, when first asked."""

    def __init__(self, *, module: CommentedModule) -> None:
        """Remember the module.

        Args:
            module (CommentedModule): The original, unannotated module.

        """
        self._module: CommentedModule = module
        self._done: bool = False
        self._text: str | None = None

    @property
    def text(self) -> str | None:
        """Give the engine's output.

        Returns:
            str | None: The converted source, or ``None``
                when the engine fails on the module.

        """
        if not self._done:
            self._done = True
            with TemporaryDirectory() as scratch:
                try:
                    self._text = self._module.convert(
                        stubs_path=Path(scratch),
                        apply=False,
                    ).converted_source
                except Constants.failures:
                    self._text = None
        return self._text


def engine_variables(*, converted: str) -> dict[str, str]:
    """List the annotated locals of the engine's output by variable path.

    Args:
        converted (str): The engine's output text.

    Returns:
        dict[str, str]: Annotation text by ``function.variable``
            (the path negotiation uses).

    """
    tree: AST = ast_parse(source=converted)
    found: dict[str, str] = {}
    for qual, function, _in_class in walk_functions(
        node=tree,
        trail=(),
        in_class=False,
    ):
        for node in own_nodes(function=function):
            if isinstance(node, AnnAssign) and isinstance(node.target, Name):
                found.setdefault(
                    f"{qual}.{node.target.id}",
                    unparse(ast_obj=node.annotation),
                )
    return found


def engine_hints(
    *,
    module: CommentedModule,
    conversion: LazyConversion,
) -> dict[Key, Hint]:
    """Turn the engine's parameter and return annotations into hints.

    Args:
        module (CommentedModule): The original, unannotated module.
        conversion (LazyConversion): The engine's lazily computed output.

    Returns:
        dict[Key, Hint]: A hint per parameter or function the engine annotated
            and whose
            annotation is allowed in this module and valid when evaluated.

    """
    text: str | None = conversion.text
    if text is None:
        return {}
    theirs: dict[str, AST] = function_nodes(module=parse(source=text))
    ours: dict[str, AST] = function_nodes(module=module)
    known: frozenset[str] = allowed_names(module=module)
    parents: dict[int, AST] = parents_of(module=module)
    classes: dict[str, int] = class_boundaries(module=module)
    found: dict[Key, Hint] = {}
    for path, node in sorted(ours.items()):
        source: str | None = _annotation(node=theirs.get(path))
        if (
            source is not None
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
                basis=HintBasis.engine,
            )
    return found


def _annotation(*, node: AST | None) -> str | None:
    """Read the annotation written on a parameter or a function's return.

    Args:
        node (AST | None): An ``arg`` or function definition of the converted
            module.

    Returns:
        str | None: The annotation text, or ``None``.

    """
    annotation: expr | None = getattr(node, "annotation", None)
    if annotation is None:
        annotation = getattr(node, "returns", None)
    return None if annotation is None else unparse(ast_obj=annotation)
