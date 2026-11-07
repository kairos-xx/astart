"""Backend interface for source-to-source graph type inference."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ast import Module


class InferenceBackend(Protocol):
    """A replaceable source-to-source inference backend.

    Implementations take untyped Python source and return strictly typed,
    keyword-normalized source produced by a graph inference pass.


    Attributes:
        name: Identifier used to refer to the name.

    """

    name: str

    def convert(self, *, source: str, module: Module | None = None) -> str:
        """Return strictly typed source for the given untyped ``source``.

        Args:
            module: The module examined while return strictly typed source for
                the given untyped ``source``.
            source: The source examined while return strictly typed source for
                the given untyped ``source``.

        Returns:
            Rendered source text produced by this operation.

        """
        ...

    def convert_module(
        self,
        *,
        source: str,
        module: Module | None = None,
    ) -> Module:
        """Return a strictly typed AST module for ``source``.

        Args:
            module: The module examined while return a strictly typed AST
                module for ``source``.
            source: The source examined while return a strictly typed AST
                module for ``source``.

        Returns:
            Module produced by this operation.

        """
        ...
