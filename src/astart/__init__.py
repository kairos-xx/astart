"""Astart: mutable Python AST, preserved source, semantic analysis and typing.

Use :func:`parse` to build an editable module, then query ``tree.semantic``
for types, values, signatures, conversion and immutable evidence. All advanced
features use one imported package; the source graph is an internal subsystem.
"""

from __future__ import annotations

from ast import AST
from typing import TYPE_CHECKING, Literal

from astart.ast import (
    Comment,
    CommentedModule,
    CommentGroup,
    MultilineComment,
    ShebangNode,
    SingleLineComment,
    SuppressionComment,
    SuppressionRule,
)
from astart.docstrings import (
    DocDescription,
    DocEntry,
    DocSection,
    DocstringNode,
    DocStyle,
    DocSummary,
    ModuleDocstringNode,
)
from astart.formatting import FormatPreservationError
from astart.semantic import (
    AnalysisBudgets,
    Args,
    ArgumentSpec,
    BoundArgument,
    BoundCall,
    CallableContract,
    ContractDiagnostic,
    GraphAnnotation,
    GraphConversion,
    ParameterContract,
    ParameterKind,
    ProtocolSpec,
    SemanticAnalyzer,
    TypeEvidence,
    TypeExpression,
    TypeExpressionCodec,
    TypeHintCatalog,
    TypeInference,
    Types,
    TypeShape,
    ValueEvidence,
)
from astart.tokens import LexicalToken, SourceSpan, TokenSnapshot

if TYPE_CHECKING:
    from pathlib import Path
Module = CommentedModule


def parse(*, source: str, filename: str = "<memory>") -> CommentedModule:
    """Parse Python source into an editable annotated module.

    Args:
        source: Python source text.
        filename: Source identity for Python's syntax diagnostics.

    Returns:
        Editable module retaining lexical and semantic information.

    """
    return CommentedModule.parse(source=source, filename=filename)


def unparse(
    *,
    tree: CommentedModule,
    preserve_formatting: bool = True,
    on_format_conflict: Literal["raise", "fallback"] = "raise",
) -> str:
    """Serialize an editable module, preserving original formatting by default.

    Args:
        tree: Editable module to serialize.
        preserve_formatting: Retain concrete source formatting where possible.
        on_format_conflict: Strategy for edits without safe lexical patches.

    Returns:
        Updated Python source.

    """
    return tree.unparse(
        preserve_formatting=preserve_formatting,
        on_format_conflict=on_format_conflict,
    )


def convert(
    *,
    tree: CommentedModule,
    stubs_path: Path,
    filename: str = "<memory>",
    apply: bool = False,
) -> GraphConversion:
    """Merge graph-based type conclusions into the same mutable AST.

    Args:
        tree: Editable module.
        stubs_path: Root of local stubs for graph inference.
        filename: Source identity.
        apply: Apply verified annotation updates when true.

    Returns:
        Conversion proposals, provenance, stage outcomes and diagnostics.

    """
    return tree.convert(
        stubs_path=stubs_path,
        filename=filename,
        apply=apply,
    )


__all__ = (
    "AST",
    "AnalysisBudgets",
    "Args",
    "ArgumentSpec",
    "BoundArgument",
    "BoundCall",
    "CallableContract",
    "Comment",
    "CommentGroup",
    "CommentedModule",
    "ContractDiagnostic",
    "DocDescription",
    "DocEntry",
    "DocSection",
    "DocStyle",
    "DocSummary",
    "DocstringNode",
    "FormatPreservationError",
    "GraphAnnotation",
    "GraphConversion",
    "LexicalToken",
    "Module",
    "ModuleDocstringNode",
    "MultilineComment",
    "ParameterContract",
    "ParameterKind",
    "ProtocolSpec",
    "SemanticAnalyzer",
    "ShebangNode",
    "SingleLineComment",
    "SourceSpan",
    "SuppressionComment",
    "SuppressionRule",
    "TokenSnapshot",
    "TypeEvidence",
    "TypeExpression",
    "TypeExpressionCodec",
    "TypeHintCatalog",
    "TypeInference",
    "TypeShape",
    "Types",
    "ValueEvidence",
    "convert",
    "parse",
    "unparse",
)
