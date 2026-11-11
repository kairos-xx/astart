"""Object-oriented orchestration of the checkpoint inference backend.

The heavy inference logic lives in :mod:`engine`, :mod:`refiner`, and
:mod:`finalizer`. This module composes those phases into a single
:class:`CheckpointBackend` whose ``convert`` method runs the pipeline:

    parse -> index -> infer -> transform -> collect facts -> refine
    -> finalize -> unparse

"""

from __future__ import annotations

from ast import Module, fix_missing_locations, parse
from typing import cast

from astart.graph.backend.engine import (
    GraphIndexer,
    InferenceEngine,
    StrictAstTransformer,
    custom_unparse,
)
from astart.graph.backend.finalizer import finalize_module
from astart.graph.backend.refiner import (
    FactCollector,
    GenericGraphRefiner,
    SignaturePreScanner,
)


class CheckpointBackend:
    """Strongest graph-inference backend, orchestrated as discrete phases.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "checkpoint-graph-backend"

    def convert(self, *, source: str, module: Module | None = None) -> str:
        """Convert untyped ``source`` into strictly typed source.

        Args:
            module (Module | None): The module examined while convert untyped
                ``source`` into strictly typed source.
            source (str): The source examined while convert untyped
                ``source`` into strictly typed source.

        Returns:
            str: Rendered source text produced by this operation.

        """
        inferred: Module = self._infer(source=source, module=module)
        refined: Module = self._refine(module=inferred)
        finalize_module(module=refined)
        return custom_unparse(node=refined) + "\n"

    def convert_module(
        self,
        *,
        source: str,
        module: Module | None = None,
    ) -> Module:
        """Convert untyped ``source`` into strictly typed AST module.

        Args:
            module (Module | None): The module examined while convert untyped
                ``source`` into strictly typed AST module.
            source (str): The source examined while convert untyped
                ``source`` into strictly typed AST module.

        Returns:
            Module: Module produced by this operation.

        """
        inferred: Module = self._infer(source=source, module=module)
        refined: Module = self._refine(module=inferred)
        finalize_module(module=refined)
        return refined

    @staticmethod
    def _infer(*, source: str, module: Module | None = None) -> Module:
        """Parse, index, and run inference, returning the typed module.

        Args:
            module (Module | None): The module examined while parse, index, and
                run inference, returning the typed module.
            source (str): The source examined while parse, index, and
                run inference, returning the typed module.

        Returns:
            Module: Module produced by this operation.

        """
        if module is None:
            module = parse(
                source=source,
                filename="<graph-v18>",
                mode="exec",
            )
        index: GraphIndexer = GraphIndexer()
        index.visit(node=module)
        inference: InferenceEngine = InferenceEngine(
            module=module,
            index=index,
            source=source,
        )
        inference.run()
        return cast(
            typ="Module",
            val=StrictAstTransformer(engine=inference).visit(node=module),
        )

    @staticmethod
    def _refine(*, module: Module) -> Module:
        """Collect graph facts and apply generic graph refinements.

        Args:
            module (Module): The module examined while collect graph
                facts and apply generic graph refinements.

        Returns:
            Module: Module produced by this operation.

        """
        collector: FactCollector = FactCollector()
        SignaturePreScanner(facts=collector.facts).visit(node=module)
        collector.visit(node=module)
        refined: Module = cast(
            typ="Module",
            val=GenericGraphRefiner(facts=collector.facts).visit(node=module),
        )
        fix_missing_locations(node=refined)
        return refined
