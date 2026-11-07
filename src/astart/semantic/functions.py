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
        function_id: Function definition syntax identity.
        context_id: Unique abstract call-analysis context.
        result: Return abstraction.
        value_updates: Changes to symbols observable by the caller.
        heap_updates: Modified abstract heap objects.
        exceptions: Possible raised exception names.
        dependencies: Syntax or symbol identities used by the call.
        unknown_side_effects: Whether unsupported effects were encountered.

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
            int produced by this operation.

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
            function_id: Function syntax identity.
            caller_id: Call-site syntax identity.
            args: Evaluated abstract arguments.
            values: Current lexical abstract environment.
            heap: Current abstract heap snapshots.

        Returns:
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
            caller_id: Call-site syntax identity.
            args: Abstract positional arguments.
            values: Input symbol environment, before the call.
            heap: Input heap, before the call.
            summary: Complete analyzed result and observable effects.

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
