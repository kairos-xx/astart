"""Visitors that dispatch on lowercase handler names.

The standard ``ast`` visitors look up ``visit_<ClassName>``, which forces
mixed-case method names such as ``visit_AsyncFunctionDef``. The base classes
here look up ``visit_<classname>`` instead, so handlers stay lowercase:
``visit_asyncfunctiondef`` handles ``ast.AsyncFunctionDef``.
"""

from __future__ import annotations

from ast import AST, NodeTransformer, NodeVisitor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def handler_name(*, node: AST) -> str:
    """Return the lowercase visitor method name for ``node``.

    Args:
        node: Node about to be visited.

    Returns:
        ``visit_`` followed by the lowercased node class name.

    """
    return f"visit_{type(node).__name__.lower()}"


class LowercaseVisitor(NodeVisitor):
    """A :class:`ast.NodeVisitor` dispatching to lowercase handlers."""

    def visit(self, node: AST) -> None:
        """Run the lowercase handler for ``node`` or visit its children.

        Args:
            node: Node to visit.

        """
        handler: Callable[..., None] = getattr(
            self,
            handler_name(node=node),
            self.generic_visit,
        )
        handler(node=node)


class LowercaseTransformer(NodeTransformer):
    """A :class:`ast.NodeTransformer` dispatching to lowercase handlers."""

    def visit(self, node: AST) -> AST | list[AST] | None:
        """Run the lowercase handler for ``node`` or transform its children.

        Args:
            node: Node to transform.

        Returns:
            The replacement node, a list of nodes, or ``None`` to delete it.

        """
        handler: Callable[..., AST | list[AST] | None] = getattr(
            self,
            handler_name(node=node),
            self.generic_visit,
        )
        return handler(node=node)


def handler_names(*, node: AST, prefix: str) -> Iterator[str]:
    """Yield lowercase handler names for ``node`` and each base class.

    Walking the MRO keeps ``isinstance`` semantics: a handler for a base
    class also serves its subclasses.

    Args:
        node: Node being dispatched.
        prefix: Handler name prefix, such as ``"_step_"``.

    Yields:
        ``prefix`` followed by each lowercased class name, most derived first.

    """
    for kind in type(node).__mro__:
        yield f"{prefix}{kind.__name__.lower()}"
