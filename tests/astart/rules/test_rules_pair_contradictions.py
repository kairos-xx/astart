"""G-04: every remaining dev-pair contradiction is root-caused and guarded."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in, expect_not_in
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        doc (Final[Path]): Path to ``docs/analysis/contradictions.md``.
        documented_nodes (Final[tuple[str, ...]]): Every contradiction node
            documented in G-04.

    """

    doc: Final[Path] = Paths.root / "docs" / "analysis" / "contradictions.md"
    documented_nodes: Final[tuple[str, ...]] = (
        "SupportsVector.__add__.other",
        "duplicate_scope_name.value",
        "function_with_generic_types.generic_function.container",
        "function_with_mutable_default_like_pattern.store",
        "HybridContainer.__or__.merged",
        "function_with_deep_attribute_assignment.child",
        "function_with_deep_attribute_assignment.leaf",
        "function_with_hybrid_container_stress.merged",
        "function_with_metaclass_registry_stress.registry",
        "function_with_nested_default_factories.tree",
        "function_with_partial_reduce_and_operator_stress.add_five",
    )


def _fix_default(*, source: str) -> str:
    """Fix ``source`` in default evidence-based mode (engine off, vars on).

    Args:
        source (str): Untyped Python snippet.

    Returns:
        str: Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="sample.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            annotate_variables=True,
            negotiate=True,
            engine=False,
        ),
    ).source


def test_contradictions_doc_lists_every_remaining_node_and_task() -> None:
    """Check ``contradictions.md`` lists all 11 remaining rows."""
    text: str = Constants.doc.read_text(encoding="utf-8")
    for node in Constants.documented_nodes:
        expect_in(item=f"| `{node}` |", container=text)


def test_mutable_default_like_store_stays_unannotated_without_engine() -> None:
    """Check ``store=None`` reassigned to ``[]`` is not typed as ``int``."""
    source: str = """\
    def collect(value, store=None):
        if store is None:
            store = []
        store.append(value)
        return store
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="store: int", container=fixed)


def test_custom_or_operator_local_stays_unannotated_without_engine() -> None:
    """Check ``left | right`` on custom objects is not typed ``int``."""
    source: str = """\
    class Box:
        def __init__(self, x: int) -> None:
            self.x: int = x

    def combine(left: Box, right: Box):
        merged = left | right
        return merged
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="merged: int", container=fixed)


def test_metaclass_registry_lookup_stays_unannotated_without_engine() -> None:
    """Check an unannotated metaclass attribute is not typed ``None``."""
    source: str = """\
    class Meta(type):
        registry = None

    def read_registry():
        registry = Meta.registry
        return registry
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="registry: None", container=fixed)


def test_local_class_method_return_is_not_typed_none() -> None:
    """Check ``child = root.add(...)`` is not typed ``None``."""
    source: str = """\
    def build():
        class Node:
            def add(self, child):
                return child

        root = Node()
        child = root.add(Node())
        return child
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="child: None", container=fixed)


def test_nested_defaultdict_lambda_stays_unannotated_without_engine() -> None:
    """Check nested ``defaultdict(lambda: ...)`` is not flattened."""
    source: str = """\
    from collections import defaultdict

    def build():
        tree = defaultdict(lambda: defaultdict(list))
        tree["a"]["x"].append(1)
        return tree
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="defaultdict[str, int]", container=fixed)


def test_functools_partial_local_stays_unannotated_without_engine() -> None:
    """Check ``partial(operator.add, 5)`` is not typed as ``int``."""
    source: str = """\
    from functools import partial
    import operator

    def apply_all(numbers: list[int]):
        add_five = partial(operator.add, 5)
        return [add_five(n) for n in numbers]
    """
    fixed: str = _fix_default(source=source)
    expect_not_in(item="add_five: int", container=fixed)
    expect_equal(actual="add_five:" in fixed, expected=False)
