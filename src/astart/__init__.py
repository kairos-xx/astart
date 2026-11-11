"""Astart: mutable Python AST, preserved source, semantic analysis and typing.

Use :func:`parse` to build an editable module, then query ``tree.semantic``
for types, values, signatures, conversion and immutable evidence. All advanced
features use one imported package; the source graph is an internal subsystem.

"""

from __future__ import annotations

from ast import AST
from typing import TYPE_CHECKING

from astart.api import check_source, fix_source
from astart.docstrings import (
    DocDescription,
    DocEntry,
    DocSection,
    DocstringNode,
    DocStyle,
    DocSummary,
    ModuleDocstringNode,
)
from astart.files import FileOutcome, fix_file, fix_paths
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
from astart.settings import Settings
from astart.source.api import parse, unparse
from astart.source.ast import (
    Comment,
    CommentedModule,
    CommentGroup,
    MultilineComment,
    ShebangNode,
    SingleLineComment,
    SuppressionComment,
    SuppressionRule,
)
from astart.source.formatting import FormatPreservationError
from astart.source.tokens import LexicalToken, SourceSpan, TokenSnapshot

if TYPE_CHECKING:
    from pathlib import Path


Module: type[CommentedModule] = CommentedModule


def convert(
    *,
    tree: CommentedModule,
    stubs_path: Path | None = None,
    filename: str = "<memory>",
    apply: bool = False,
) -> GraphConversion:
    """Merge graph-based type conclusions into the same mutable AST.

    Args:
        tree (CommentedModule): Editable module.
        stubs_path (Path | None): Typeshed root for stub lookups, or ``None``
            for the
            ``ASTART_TYPESHED`` override and then the bundled snapshot.
        filename (str): Source identity.
        apply (bool): Apply verified annotation updates when true.

    Returns:
        GraphConversion:
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
    "FileOutcome",
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
    "Settings",
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
    "check_source",
    "convert",
    "fix_file",
    "fix_paths",
    "fix_source",
    "parse",
    "unparse",
)
