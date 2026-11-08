"""Pytest hooks shared by the whole suite.

The corpus-parametrized modules replay hundreds of real files and make up
almost all of the suite's run time. They are marked ``slow`` so that the edit
loop can run ``pytest -m "not slow"`` (a fast tier) while CI runs everything.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class Constants:
    """Constants used in the tests module.

    Attributes:
        slow_modules: Test module names marked as slow.

    """

    slow_modules: Final[frozenset[str]] = frozenset(
        {
            "test_cli_idempotence_corpus",
            "test_cli_idempotence_full",
            "test_format_annotations_corpus",
            "test_graph_corpus",
            "test_rules_idempotence",
            "test_rules_recovery",
            "test_rules_runner_corpus",
            "test_rules_synthesis_corpus",
            "test_rules_writer_fuzz",
            "test_semantic_corpus",
            "test_writer_fuzz",
        },
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: Sequence[pytest.Item],
) -> None:
    """Mark every test of a corpus-heavy module as ``slow``.

    Args:
        config: Pytest configuration (unused).
        items: The collected tests, marked in place.

    """
    _ = config
    for item in items:
        if item.path.stem in Constants.slow_modules:
            item.add_marker(marker=pytest.mark.slow)
