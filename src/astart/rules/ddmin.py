"""Deterministic delta debugging over stable change identifiers."""

from __future__ import annotations

from typing import Final, Protocol, final


@final
class Constants:
    """Delta-debugging algorithm parameters.

    Attributes:
        initial_granularity (Final[int]): Smallest useful partition count.

    """

    initial_granularity: Final[int] = 2


class SubsetTest(Protocol):
    """Decide whether an ordered subset of changes is acceptable."""

    def __call__(self, *, changes: tuple[int, ...]) -> bool:
        """Test changes against the same baseline on every invocation.

        Args:
            changes (tuple[int, ...]): Unique identifiers in their original
                order.

        Returns:
            Whether the subset passes. Unavailable checks must fail.

        """
        ...


def ddmin(*, changes: tuple[int, ...], test: SubsetTest) -> tuple[int, ...]:
    """Find a deterministic 1-minimal failing subset using Zeller's ddmin.

    A passing batch or a failing empty baseline returns no attributable
    core. Otherwise every single deletion from the returned core passes.
    Results are cached by identifier set for this invocation only. The
    predicate must be deterministic and preserve the original baseline.
    Worst-case test cost is quadratic; no global minimum is guaranteed.

    Args:
        changes (tuple[int, ...]): Unique change IDs, in application order.
        test (SubsetTest): Passing-subset predicate; exceptions propagate
            unchanged.

    Returns:
        tuple[int, ...]: Failing identifiers in original order, or an empty
            tuple.

    Raises:
        ValueError: If identifiers are duplicated.

    """
    if len(frozenset(changes)) != len(changes):
        msg: str = "change identifiers must be unique"
        raise ValueError(msg)
    cache: dict[frozenset[int], bool] = {}

    def passes(*, subset: tuple[int, ...]) -> bool:
        """Memoize a deterministic test without changing subset order.

        Args:
            subset (tuple[int, ...]): Change IDs to evaluate.

        Returns:
            bool: Whether the subset passes.

        """
        key: frozenset[int] = frozenset(subset)
        if key not in cache:
            cache[key] = test(changes=subset)
        return cache[key]

    if not changes or not passes(subset=()) or passes(subset=changes):
        return ()
    current: tuple[int, ...] = changes
    granularity: int = Constants.initial_granularity
    while len(current) >= Constants.initial_granularity:
        chunks: tuple[tuple[int, ...], ...] = tuple(
            current[
                index * len(current) // granularity : (index + 1)
                * len(current)
                // granularity
            ]
            for index in range(granularity)
        )
        reduced: tuple[int, ...] | None = next(
            (chunk for chunk in chunks if not passes(subset=chunk)),
            None,
        )
        if reduced is not None:
            current = reduced
            granularity = Constants.initial_granularity
            continue
        complements: tuple[tuple[int, ...], ...] = tuple(
            _complement(changes=current, excluded=frozenset(chunk))
            for chunk in chunks
        )
        reduced = next(
            (subset for subset in complements if not passes(subset=subset)),
            None,
        )
        if reduced is not None:
            current = reduced
            granularity = max(
                granularity - 1,
                Constants.initial_granularity,
            )
            continue
        if granularity == len(current):
            break
        granularity = min(2 * granularity, len(current))
    return current


def _complement(
    *,
    changes: tuple[int, ...],
    excluded: frozenset[int],
) -> tuple[int, ...]:
    """Remove a chunk without rebuilding its membership set per element.

    Args:
        changes (tuple[int, ...]): Change IDs in application order.
        excluded (frozenset[int]): IDs of one partition chunk.

    Returns:
        tuple[int, ...]: The ordered complement.

    """
    return tuple(item for item in changes if item not in excluded)
