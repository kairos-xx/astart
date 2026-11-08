"""Function-local variables get the annotation the evidence proves."""

from __future__ import annotations

from ast import parse
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fixed(*, source: str, variables: bool = True) -> str:
    """Fix a module at the guarded ceiling.

    Args:
        source: Module text.
        variables: Whether variable annotation is switched on.

    Returns:
        The fixed text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            annotate_variables=variables,
        ),
    ).source


def test_literals_comparisons_and_calls_are_annotated() -> None:
    """Check the shapes the prover and the call links can type."""
    fixed: str = _fixed(
        source="""
        def helper():
            return 1

        def use():
            count = 0
            label = "n"
            flag = count > 3
            h = helper()
            return count, label, flag, h
        """,
    )
    expect_in(item="count: int = 0", container=fixed)
    expect_in(item="label: str = ", container=fixed)
    expect_in(item="flag: bool = count > 3", container=fixed)
    expect_in(item="h: int = helper()", container=fixed)
    _ = parse(source=fixed)


def test_a_filled_list_is_annotated_with_its_elements() -> None:
    """Check ``names = []`` plus ``append`` gives ``list[str]``."""
    fixed: str = _fixed(
        source="""
        def collect(items):
            names = []
            for item in items:
                names.append(str(item))
            return names
        """,
    )
    expect_in(item="names: list[str] = []", container=fixed)


def test_nothing_is_written_without_the_option_or_a_local_style() -> None:
    """Check that variables are left alone by default."""
    source: str = "def f():\n    count = 0\n    return count\n"
    fixed: str = _fixed(source=source, variables=False)
    expect_not_in(item="count: int", container=fixed)


def test_a_module_that_annotates_locals_gets_the_rest() -> None:
    """Check that the author's style switches the rule on."""
    fixed: str = _fixed(
        source="""
        def f() -> int:
            a: int = 1
            b = 2
            return a + b
        """,
        variables=False,
    )
    expect_in(item="b: int = 2", container=fixed)


def test_unprovable_values_are_not_annotated() -> None:
    """Check that unknown calls and parameters give no annotation."""
    fixed: str = _fixed(
        source="""
        def f(x):
            a = x
            b = unknown()
            return a, b
        """,
    )
    expect_not_in(item="a:", container=fixed)
    expect_not_in(item="b:", container=fixed)


def test_a_rebound_local_is_not_annotated() -> None:
    """Check that two bindings of one name leave it alone."""
    fixed: str = _fixed(
        source="""
        def f():
            x = 1
            x = "s"
            return x
        """,
    )
    expect_not_in(item="x:", container=fixed)


def test_none_only_and_loop_variables_are_not_annotated() -> None:
    """Check that ``x = None`` and ``for`` targets get no annotation."""
    fixed: str = _fixed(
        source="""
        def f(items):
            x = None
            for y in items:
                print(y)
            return x
        """,
    )
    expect_not_in(item="x:", container=fixed)
    expect_not_in(item="y:", container=fixed)


def test_second_run_changes_nothing() -> None:
    """Check idempotence of the whole fix."""
    once: str = _fixed(
        source="""
        def f():
            count = 0
            return count
        """,
    )
    expect_equal(actual=_fixed(source=once), expected=once)


def test_comments_survive_the_rewrite() -> None:
    """Check that the statement keeps its comment."""
    fixed: str = _fixed(
        source="""
        def f():
            count = 0  # how many
            return count
        """,
    )
    expect_in(item="count: int = 0  # how many", container=fixed)


def test_a_dict_literal_that_is_later_stored_into_is_not_annotated() -> None:
    """Check that ``d[k] = v`` can widen the values, so no annotation."""
    fixed: str = _fixed(
        source="""
        def f():
            d = {"a": 1}
            d["b"] = "s"
            return d
        """,
    )
    expect_not_in(item="d:", container=fixed)


def test_a_dict_literal_that_is_only_read_is_annotated() -> None:
    """Check that a read-only dict keeps the literal's type."""
    fixed: str = _fixed(
        source="""
        def f():
            d = {"a": 1}
            return d.get("a")
        """,
    )
    expect_in(item="d: dict[str, int] = ", container=fixed)


def test_appended_elements_join_a_list_literal() -> None:
    """Check that ``[1]`` plus ``append("s")`` is ``list[int | str]``."""
    fixed: str = _fixed(
        source="""
        def f():
            xs = [1]
            xs.append("s")
            return xs
        """,
    )
    expect_in(item="xs: list[int | str] = [1]", container=fixed)


def test_extend_blocks_a_list_literal() -> None:
    """Check that an unmodelled mutation leaves the list alone."""
    fixed: str = _fixed(
        source="""
        def f(more):
            xs = [1]
            xs.extend(more)
            return xs
        """,
    )
    expect_not_in(item="xs:", container=fixed)


def test_a_list_attribute_mutated_elsewhere_is_not_followed() -> None:
    """Check that ``self.items.append("s")`` keeps ``self.items`` unknown."""
    fixed: str = _fixed(
        source="""
        class Box:
            def __init__(self):
                self.items = [1]

            def add(self):
                self.items.append("s")

            def first(self):
                items = self.items
                return items
        """,
    )
    expect_not_in(item="items: list[int]", container=fixed)


def test_constructor_calls_of_module_classes_are_typed() -> None:
    """Check ``p = Point(1)`` is annotated with the class."""
    fixed: str = _fixed(
        source="""
        class Point:
            def __init__(self, x):
                self.x = x

        def make():
            p = Point(1)
            return p
        """,
    )
    expect_in(item="p: Point = Point(", container=fixed)


def test_a_dict_that_is_only_unpacked_keeps_its_type() -> None:
    """Check that ``{**d1, **d2}`` and ``f(**d)`` only read the dicts."""
    fixed: str = _fixed(
        source="""
        def merge():
            d1 = {"a": 1}
            d2 = {"b": 2}
            return {**d1, **d2}
        """,
    )
    expect_in(item="d1: dict[str, int] = ", container=fixed)
    expect_in(item="d2: dict[str, int] = ", container=fixed)


def test_a_generic_class_is_not_named_bare() -> None:
    """Check that ``Box(1)`` of a ``Generic[T]`` class gets no annotation."""
    fixed: str = _fixed(
        source="""
        from typing import Generic, TypeVar

        T = TypeVar("T")

        class Box(Generic[T]):
            def __init__(self, item):
                self.item = item

        def make():
            b = Box(1)
            return b
        """,
    )
    expect_not_in(item="b: Box", container=fixed)


def test_a_comprehension_over_a_typed_list_is_annotated() -> None:
    """Check that ``[x ** 2 for x in items]`` is ``list[int]``."""
    fixed: str = _fixed(
        source="""
        def squares(items):
            out = [x ** 2 for x in items]
            return out

        squares([1, 2, 3])
        """,
    )
    expect_in(item="out: list[int] = ", container=fixed)


def test_a_method_call_on_a_typed_string_is_annotated() -> None:
    """Check that ``name.strip()`` is ``str`` once ``name`` is known."""
    fixed: str = _fixed(
        source="""
        def clean(name):
            tidy = name.strip()
            return tidy

        clean("  a ")
        """,
    )
    expect_in(item="tidy: str = ", container=fixed)


def test_a_comprehension_over_an_unknown_iterable_is_not_annotated() -> None:
    """Check that an unprovable iterable gives no annotation."""
    fixed: str = _fixed(
        source="""
        def squares(items):
            out = [x ** 2 for x in items]
            return out
        """,
    )
    expect_not_in(item="out:", container=fixed)


def test_a_comprehension_variable_does_not_capture_an_outer_name() -> None:
    """Check that the loop variable shadows a local of the same name."""
    fixed: str = _fixed(
        source="""
        def f(items):
            x = "s"
            out = [x for x in items]
            return out, x

        f([1, 2])
        """,
    )
    expect_in(item="out: list[int] = ", container=fixed)
