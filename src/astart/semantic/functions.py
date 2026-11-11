"""Soundly keyed abstract call summaries with explicit observable effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from astart.semantic.heap import HeapObject
    from astart.semantic.values import AbstractValue


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FunctionSummary:
    """Immutable analyzed call result with possible visible effects.

    Attributes:
        function_id (int): Function definition syntax identity.
        context_id (int): Unique abstract call-analysis context.
        result (AbstractValue): Return abstraction.
        value_updates (tuple[tuple[int, AbstractValue], ...]): Changes to
            symbols observable by the caller.
        heap_updates (tuple[HeapObject, ...]): Modified abstract heap objects.
        exceptions (tuple[str, ...]): Possible raised exception names.
        dependencies (tuple[int, ...]): Syntax or symbol identities used by the
            call.
        unknown_side_effects (bool): Whether unsupported effects were
            encountered.

    """

    function_id: int
    context_id: int
    result: AbstractValue
    value_updates: tuple[tuple[int, AbstractValue], ...] = ()
    heap_updates: tuple[HeapObject, ...] = ()
    exceptions: tuple[str, ...] = ()
    dependencies: tuple[int, ...] = ()
    unknown_side_effects: bool = False


@final
class CallSummaryCache:
    """Caches complete call effects keyed by arguments and input state."""

    def __init__(self) -> None:
        """Start an empty per-interpreter summary registry."""
        self._summaries: dict[
            tuple[
                int,
                int,
                tuple[AbstractValue, ...],
                tuple[tuple[int, AbstractValue], ...],
                tuple[HeapObject, ...],
            ],
            FunctionSummary,
        ] = {}

    @property
    def size(self) -> int:
        """Number of cached complete call summaries.

        Returns:
            int: int produced by this operation.

        """
        return len(self._summaries)

    def get(
        self,
        *,
        function_id: int,
        caller_id: int,
        args: tuple[AbstractValue, ...],
        values: dict[int, AbstractValue],
        heap: dict[int, HeapObject],
    ) -> FunctionSummary | None:
        """Find a summary using complete observable abstract state.

        Args:
            function_id (int): Function syntax identity.
            caller_id (int): Call-site syntax identity.
            args (tuple[AbstractValue, ...]): Evaluated abstract arguments.
            values (dict[int, AbstractValue]): Current lexical abstract
                environment.
            heap (dict[int, HeapObject]): Current abstract heap snapshots.

        Returns:
            FunctionSummary | None:
                Matching cached summary, if previously analyzed.

        """
        return self._summaries.get(
            (
                function_id,
                caller_id,
                args,
                tuple(sorted(values.items())),
                tuple(heap[identity] for identity in sorted(heap)),
            ),
        )

    def add(
        self,
        *,
        caller_id: int,
        args: tuple[AbstractValue, ...],
        values: dict[int, AbstractValue],
        heap: dict[int, HeapObject],
        summary: FunctionSummary,
    ) -> None:
        """Store a complete effects summary for the precise input state.

        Args:
            caller_id (int): Call-site syntax identity.
            args (tuple[AbstractValue, ...]): Abstract positional arguments.
            values (dict[int, AbstractValue]): Input symbol environment, before
                the call.
            heap (dict[int, HeapObject]): Input heap, before the call.
            summary (FunctionSummary): Complete analyzed result and observable
                effects.

        """
        self._summaries[
            (
                summary.function_id,
                caller_id,
                args,
                tuple(sorted(values.items())),
                tuple(heap[identity] for identity in sorted(heap)),
            )
        ] = summary
