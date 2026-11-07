"""From-scratch graph inference backend.

A clean, sound, soundness-first converter: it annotates parameters, return
types, and instance attributes from direct evidence and falls back to
``object`` whenever evidence is insufficient, so the output is always
internally consistent under a strict type checker. Only import-free builtin
type forms are emitted.
"""

from __future__ import annotations

from astart._graph.backend.finalizer import finalize


class FromScratchBackend:
    """Sound, evidence-based source-to-source inference backend.

    Attributes:
        name: Identifier used to refer to the name.

    """

    name: str = "from-scratch-engine"

    @staticmethod
    def convert(*, source: str) -> str:
        """Return strictly typed source for the given untyped ``source``.

        Args:
            source: The source examined while return strictly typed source for
                the given untyped ``source``.

        Returns:
            Rendered source text produced by this operation.

        """
        return finalize(source=source)
