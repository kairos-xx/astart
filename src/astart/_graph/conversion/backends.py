"""Inference backend adapters used by the conversion pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from astart._graph.backend import CheckpointBackend

if TYPE_CHECKING:
    from ast import Module

    from astart._graph.backend import InferenceBackend
    from astart._graph.conversion.context import ConversionContext
    from astart._graph.graph.document import AstDocument


@dataclass(frozen=True, slots=True)
class CheckpointGraphBackend:
    """Adapter for the current strongest graph inference checkpoint.

    The adapter is deliberately small.  All orchestration, document indexing,
    usage graph construction, stub loading, and reporting live in the public
    package API.  The backend itself is the replaceable OOP
    :class:`CheckpointBackend` that performs the source-to-source graph edit.


    Attributes:
        backend: Backend retained as InferenceBackend by this instance.
        name: Identifier used to refer to the name.

    """

    name: str = "checkpoint-graph-backend"
    backend: InferenceBackend = field(default_factory=CheckpointBackend)

    def convert(self, *, context: ConversionContext) -> Module:
        """Return AST module converted by the graph inference backend.

        Args:
            context: Context supplied as ConversionContext for this operation.

        Returns:
            Module produced by this operation.

        """
        input_document: AstDocument | None = context.input_document
        module: Module | None = input_document.tree if input_document else None
        return self.backend.convert_module(
            source=context.source,
            module=module,
        )
