"""Loss-aware conversion between the internal graph engine and native types.

The two engines own independent identity maps: this bridge exchanges current
source and immutable type expressions, never foreign mutable graph identities.
The graph implementation is private to ``astart.graph``.

"""

from __future__ import annotations

from ast import Module, parse
from typing import final

from astart.graph.graph.document import AstDocument
from astart.graph.graph.type_expressions import (
    TypeExpression as GraphTypeExpression,
)
from astart.graph.graph.type_expressions import (
    TypeExpressionCodec as GraphTypeExpressionCodec,
)
from astart.semantic.type_expressions import TypeExpressionCodec
from astart.semantic.type_shapes import TypeShape, type_shape
from astart.source.node_attributes import render_source


@final
class GraphTypeBridge:
    """Convert the current AST into internal graph and type representations."""

    @staticmethod
    def document(*, tree: Module, filename: str = "<memory>") -> AstDocument:
        """Reparse current source as an internal graph document.

        Raises:
            SyntaxError: The mutable AST serializes to invalid Python
                syntax.
            FormatPreservationError: Source patching cannot be safely
                preserved.

        Args:
            filename (str): Filename supplied as str for this operation.
            tree (Module): Tree supplied as Module for this operation.

        Returns:
            AstDocument: AstDocument produced by this operation.

        """
        source: str = render_source(tree=tree)
        parse(source=source)
        return AstDocument.from_source(source=source, filename=filename)

    @staticmethod
    def to_graph(*, shape: TypeShape) -> GraphTypeExpression:
        """Translate a known shape to the internal immutable type algebra.

        Args:
            shape (TypeShape): Shape supplied as TypeShape for this operation.

        Returns:
            GraphTypeExpression:
                GraphTypeExpression produced by this operation.

        """
        return GraphTypeExpressionCodec.from_ast(
            node=parse(source=str(object=shape), mode="eval").body,
        )

    @staticmethod
    def from_graph(*, expression: GraphTypeExpression) -> TypeShape:
        """Translate the internal type representation to the native lattice.

        Args:
            expression (GraphTypeExpression): The expression examined while
                translate the
                internal type representation to the native lattice.

        Returns:
            TypeShape: TypeShape produced by this operation.

        """
        rendered: str = GraphTypeExpressionCodec.to_source(
            type_expression=expression,
        )
        return type_shape(
            expression=TypeExpressionCodec.from_source(source=rendered),
        )
