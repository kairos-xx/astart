"""Protocols for conversion backends and pipeline stages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ast import Module

    from astart.graph.conversion.context import ConversionContext


class ConversionStage(Protocol):
    """One immutable stage in the graph-only conversion pipeline."""

    @property
    def name(self) -> str:
        """Return the stable stage name.

        Returns:
            str produced by this operation.

        Raises:
            NotImplementedError: If this operation cannot satisfy its
                documented contract.

        """
        raise NotImplementedError

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Run the stage and return the updated context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext produced by this operation.

        Raises:
            NotImplementedError: If this operation cannot satisfy its
                documented contract.

        """
        raise NotImplementedError


class ConversionBackend(Protocol):
    """Backend turning source and graph context into a converted AST."""

    @property
    def name(self) -> str:
        """Return the stable backend name.

        Returns:
            str produced by this operation.

        Raises:
            NotImplementedError: If this operation cannot satisfy its
                documented contract.

        """
        raise NotImplementedError

    @staticmethod
    def convert(*, context: ConversionContext) -> Module:
        """Return converted AST module for the supplied context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            Module produced by this operation.

        Raises:
            NotImplementedError: If this operation cannot satisfy its
                documented contract.

        """
        raise NotImplementedError
