"""Verify graph type synthesis without executing source code."""

from __future__ import annotations

from ast import Assign, Constant, parse
from typing import TYPE_CHECKING

from astart.graph import AstDocument, ConversionPipeline, TypeExpressionCodec
from astart.graph.conversion.synthesis import TypeHintCatalog, Types
from astart.semantic import GraphTypeBridge, TypeShape
from astart.source.ast import CommentedModule

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_is_not,
)

if TYPE_CHECKING:
    from astart.graph.graph.type_expressions import (
        TypeExpression as GraphTypeExpression,
    )


def test_original_graph_conversion_packages_are_importable() -> None:
    """Keep established AST graph and synthesis APIs available to callers."""
    expect_is_not(actual=AstDocument, unexpected=None)
    expect_is_not(actual=ConversionPipeline, unexpected=None)
    expect_is_not(actual=TypeExpressionCodec, unexpected=None)
    expect_is_not(actual=TypeHintCatalog, unexpected=None)
    expect_is_not(actual=Types, unexpected=None)


def test_graph_document_tracks_current_edited_code() -> None:
    """Bridge edits through source, not foreign graph node identities."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=a
""",
    )
    first: Assign = expect_instance(value=tree.body[0], kind=Assign)
    literal: Constant = expect_instance(value=first.value, kind=Constant)
    literal.value = 5
    doc: AstDocument = tree.semantic.graph_document(filename="updated.py")
    doc = expect_instance(value=doc, kind=AstDocument)
    expect_in(item="5", container=str(object=doc.source))


def test_type_expression_interoperation() -> None:
    """Preserve nested immutable generic type shapes across both engines."""
    original: TypeShape = TypeShape(
        name="list",
        arguments=(TypeShape(name="int"),),
    )
    expression: GraphTypeExpression = GraphTypeBridge.to_graph(shape=original)
    expect_equal(
        actual=GraphTypeBridge.from_graph(expression=expression),
        expected=original,
    )


def test_plain_ast_module_can_be_bridged() -> None:
    """Accept standard-library ast.Module as well as CommentedModule."""
    document: AstDocument = GraphTypeBridge.document(
        tree=parse(source="number = 3"),
        filename="plain.py",
    )
    document = expect_instance(value=document, kind=AstDocument)
