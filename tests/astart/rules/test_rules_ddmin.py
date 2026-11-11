"""Verify minimal checker failures and original-source batch recovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import log2
from typing import final

import pytest
from astart.rules import default_registries, load_default_catalog
from astart.rules.ddmin import ddmin
from astart.rules.reasons import SkipCode
from astart.rules.runner import FixResult, FixSettings, fix_source
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true


@final
@dataclass(kw_only=True, slots=True)
class _Probe:
    """Accept subsets unless they contain a complete forbidden core.

    Attributes:
        cores (tuple[frozenset[int], ...]): Sets whose simultaneous presence
            fails.
        calls (list[frozenset[int]]): Subsets evaluated by the test, in order.

    """

    cores: tuple[frozenset[int], ...]
    calls: list[frozenset[int]] = field(default_factory=list)

    def __call__(self, *, changes: tuple[int, ...]) -> bool:
        """Test a subset and record calls so cache reuse is observable.

        Args:
            changes (tuple[int, ...]): Ordered change identifiers.

        Returns:
            bool: Whether the changes avoid every forbidden core.

        """
        subset: frozenset[int] = frozenset(changes)
        self.calls.append(subset)
        return not any(core <= subset for core in self.cores)


@pytest.mark.parametrize("core", [(3,), (3, 31), (0, 19, 39)])
def test_ddmin_finds_interacting_core(*, core: tuple[int, ...]) -> None:
    """Isolate jointly failing changes among forty unrelated edits.

    Args:
        core (tuple[int, ...]): Changes that must all occur to fail.

    """
    probe: _Probe = _Probe(cores=(frozenset(core),))
    result: tuple[int, ...] = ddmin(changes=tuple(range(40)), test=probe)
    expect_equal(actual=result, expected=core)
    expect_equal(actual=len(probe.calls), expected=len(set(probe.calls)))
    expect_true(condition=len(probe.calls) <= 2 * 40 * log2(40))


def test_ddmin_returns_no_core_for_passing_batch() -> None:
    """Handle empty and accepted input without inventing a failure."""
    probe: _Probe = _Probe(cores=(frozenset({9}),))
    expect_equal(actual=ddmin(changes=(), test=probe), expected=())
    expect_equal(actual=ddmin(changes=(1, 2), test=probe), expected=())


def test_ddmin_preserves_original_order() -> None:
    """Return input order even when identifiers are not sorted."""
    probe: _Probe = _Probe(cores=(frozenset({7, 2}),))
    expect_equal(
        actual=ddmin(changes=(9, 7, 4, 2, 5), test=probe),
        expected=(7, 2),
    )


def test_ddmin_rejects_duplicate_identifiers() -> None:
    """Reject ambiguous identities instead of aliasing cache entries."""
    probe: _Probe = _Probe(cores=())
    with pytest.raises(expected_exception=ValueError, match="unique"):
        _ = ddmin(changes=(1, 1), test=probe)


def test_ddmin_cannot_attribute_a_failing_empty_baseline() -> None:
    """Return no core when the predicate fails without any changes."""
    probe: _Probe = _Probe(cores=(frozenset(),))
    expect_equal(actual=ddmin(changes=(1, 2, 3), test=probe), expected=())
    expect_equal(actual=probe.calls, expected=[frozenset()])


def test_ddmin_handles_complement_only_failure() -> None:
    """Increase granularity when both initial halves pass."""
    probe: _Probe = _Probe(cores=(frozenset({0, 2}),))
    expect_equal(
        actual=ddmin(changes=(0, 1, 2, 3), test=probe),
        expected=(0, 2),
    )
    expect_equal(actual=len(probe.calls), expected=len(set(probe.calls)))


def test_ddmin_systematic_monotone_cores() -> None:
    """Isolate every nonempty forbidden combination of five changes."""
    size: int
    core: tuple[int, ...]
    for size in range(1, 6):
        for core in combinations(iterable=range(5), r=size):
            probe: _Probe = _Probe(cores=(frozenset(core),))
            expect_equal(
                actual=ddmin(changes=tuple(range(5)), test=probe),
                expected=core,
            )


@final
@dataclass(kw_only=True, slots=True)
class _BatchChecker:
    """Reject two annotations while recording the baseline of each probe.

    Attributes:
        calls (list[tuple[str, str]]): Original and transformed texts submitted
            for checking.
        cores (tuple[tuple[str, ...], ...]): Marker combinations rejected by
            this checker.
        partners (tuple[str, str] | None): Edits which pass together but fail
            individually.

    """

    calls: list[tuple[str, str]] = field(default_factory=list)
    cores: tuple[tuple[str, ...], ...] = (
        ("def f3(x: int",),
        ("def f31(x: int",),
    )
    partners: tuple[str, str] | None = None

    def regresses(self, *, filename: str, before: str, after: str) -> bool:
        """Reject configured marker combinations.

        Args:
            filename (str): Source name, checked for correct routing.
            before (str): Baseline source.
            after (str): Candidate source.

        Returns:
            bool: Whether a forbidden annotation was written.

        """
        expect_equal(actual=filename, expected="batch.py")
        self.calls.append((before, after))
        partial: bool = self.partners is not None and (
            (self.partners[0] in after) != (self.partners[1] in after)
        )
        return partial or any(
            all(marker in after for marker in core) for core in self.cores
        )


def test_checker_recovers_thirty_eight_of_forty_annotations() -> None:
    """Keep independent fixes and compare every subset to one original."""
    source: str = "\n".join(
        (f"def f{index}(x=1):\n    return x\n") for index in range(40)
    )
    checker: _BatchChecker = _BatchChecker()
    result: FixResult = fix_source(
        source=source,
        filename="batch.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            checker=checker,
            max_rounds=1,
            excluded_prefixes=("docs.",),
        ),
    )
    expect_equal(actual=result.source.count("x: int"), expected=38)
    expect_equal(actual=len(result.skipped), expected=2)
    expect_true(
        condition=all(
            skip.code is SkipCode.checker_rejected for skip in result.skipped
        ),
    )
    expect_true(condition=all(before == source for before, _ in checker.calls))
    expect_true(condition=len(checker.calls) <= 2 * 40 * log2(40))


def test_checker_keeps_coupled_edits_across_partition_boundaries() -> None:
    """Keep jointly valid annotations that sequential halving loses."""
    source: str = "\n".join(
        (f"def f{index}(x=1):\n    return x\n") for index in range(40)
    )
    checker: _BatchChecker = _BatchChecker(
        cores=(("def f0(x: int",), ("def f1(x: int",)),
        partners=("def f15(x: int", "def f35(x: int"),
    )
    result: FixResult = fix_source(
        source=source,
        filename="batch.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            checker=checker,
            max_rounds=1,
            excluded_prefixes=("docs.",),
        ),
    )
    expect_equal(actual=result.source.count("x: int"), expected=38)
    expect_equal(actual=len(result.skipped), expected=2)
    rejected: bool = checker.regresses(
        filename="batch.py",
        before=source,
        after=result.source,
    )
    expect_true(condition=not rejected)


@pytest.mark.parametrize(
    ("cores", "expected"),
    [
        ((("def f0(x: int", "def f2(x: int"),), 2),
        (((),), 0),
    ],
)
def test_checker_interactions_and_unavailability_are_conservative(
    *,
    cores: tuple[tuple[str, ...], ...],
    expected: int,
) -> None:
    """Refuse failing cores, preserve comments and settle idempotently.

    Args:
        cores (tuple[tuple[str, ...], ...]): Joint failures, or an empty core
            for an unavailable checker.
        expected (int): Number of accepted parameter annotations.

    """
    source: str = """\
# original
""" + "\n".join(
        (f"def f{index}(x=1):\n    return x  # keep\n") for index in range(4)
    )
    checker: _BatchChecker = _BatchChecker(cores=cores)
    settings: FixSettings = FixSettings(
        ceiling=FixSafety.guarded,
        checker=checker,
        max_rounds=1,
        excluded_prefixes=("docs.",),
    )
    first: FixResult = fix_source(
        source=source,
        filename="batch.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=settings,
    )
    expect_equal(actual=first.source.count("x: int"), expected=expected)
    expect_equal(actual=first.source.count("# keep"), expected=4)
    expect_true(
        condition=first.source.startswith("""\
# original
"""),
    )
    accepted: bool = not checker.regresses(
        filename="batch.py",
        before=source,
        after=first.source,
    )
    expect_true(condition=accepted or first.source == source)
    second: FixResult = fix_source(
        source=first.source,
        filename="batch.py",
        catalog=load_default_catalog(registries=default_registries()),
        registries=default_registries(),
        settings=settings,
    )
    expect_equal(actual=second.source, expected=first.source)
