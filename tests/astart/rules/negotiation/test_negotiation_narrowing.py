"""Reading tests, patterns and handlers into per-arm constraints."""

from __future__ import annotations

from ast import (
    ExceptHandler,
    If,
    Match,
    Try,
    expr,
    pattern,
    stmt,
)
from textwrap import dedent
from typing import TYPE_CHECKING, ClassVar, final

from astart import parse
from astart.rules.negotiation.narrowing import (
    Arms,
    CaseArms,
    exception_types,
    read_case,
    read_test,
)

from tests.support.expectations import expect_equal, expect_instance

if TYPE_CHECKING:
    from astart import CommentedModule


@final
class Constants:
    """Shared fixtures for the tests.

    Attributes:
        counts (ClassVar[dict[str, int]]): No module-level bindings, so
            builtins stay resolvable.
        classes (ClassVar[frozenset[str]]): No module classes.

    """

    counts: ClassVar[dict[str, int]] = {}
    classes: ClassVar[frozenset[str]] = frozenset()


def _test(*, source: str) -> expr:
    """Parse the test expression of an ``if`` statement.

    Args:
        source (str): The ``if`` header text.

    Returns:
        expr: The test expression.

    """
    module: CommentedModule = parse(
        source=dedent(text=f"if {source}:\n    pass\n"),
    )
    first: stmt = module.body[0]
    return expect_instance(value=first, kind=If).test


def _arms(*, source: str) -> tuple[Arms, ...]:
    """Read the arms of an ``if`` test.

    Args:
        source (str): The ``if`` header text.

    Returns:
        tuple[Arms, ...]: The arms the test establishes.

    """
    return read_test(
        test=_test(source=source),
        counts=Constants.counts,
    )


def _pattern(*, source: str) -> pattern:
    """Parse the pattern of the first ``case`` of a ``match``.

    Args:
        source (str): The ``case`` line text.

    Returns:
        pattern: The case pattern.

    """
    module: CommentedModule = parse(
        source=dedent(
            text=f"match x:\n    case {source}:\n        pass\n",
        ),
    )
    first: stmt = module.body[0]
    return expect_instance(value=first, kind=Match).cases[0].pattern


def _case(
    *,
    source: str,
    classes: frozenset[str] = frozenset(),
) -> CaseArms:
    """Read one case pattern.

    Args:
        source (str): The ``case`` line text.
        classes (frozenset[str]): Module class names the pattern may resolve.

    Returns:
        CaseArms: The case's positive constraint and exclusions.

    """
    return read_case(
        node=_pattern(source=source),
        counts=Constants.counts,
        classes=classes,
    )


def _handler(*, source: str) -> ExceptHandler:
    """Parse the handler of a ``try`` statement.

    Args:
        source (str): The ``except`` line text.

    Returns:
        ExceptHandler: The exception handler.

    """
    module: CommentedModule = parse(
        source=dedent(
            text=f"try:\n    pass\nexcept {source}:\n    pass\n",
        ),
    )
    first: stmt = module.body[0]
    return expect_instance(value=first, kind=Try).handlers[0]


def test_is_none_gives_both_arms() -> None:
    """Check ``x is None`` and ``x is not None``."""
    expect_equal(
        actual=_arms(source="x is None"),
        expected=(Arms(name="x", when_true="None", when_false="!None"),),
    )
    expect_equal(
        actual=_arms(source="x is not None"),
        expected=(Arms(name="x", when_true="!None", when_false="None"),),
    )


def test_isinstance_gives_the_complement_on_the_false_arm() -> None:
    """Check ``isinstance`` narrows both arms, tuples included."""
    expect_equal(
        actual=_arms(source="isinstance(x, int)"),
        expected=(Arms(name="x", when_true="int", when_false="!int"),),
    )
    expect_equal(
        actual=_arms(source="isinstance(x, (int, str))"),
        expected=(
            Arms(name="x", when_true="int | str", when_false="!int & !str"),
        ),
    )


def test_not_swaps_the_arms() -> None:
    """Check ``not isinstance`` exchanges the constraints."""
    expect_equal(
        actual=_arms(source="not isinstance(x, int)"),
        expected=(Arms(name="x", when_true="!int", when_false="int"),),
    )


def test_bare_name_removes_none_when_true() -> None:
    """Check that ``if x:`` only constrains the true arm."""
    expect_equal(
        actual=_arms(source="x"),
        expected=(Arms(name="x", when_true="!None", when_false=None),),
    )


def test_and_conjoins_the_true_sides() -> None:
    """Check ``and`` merges known constraints and drops the false side."""
    expect_equal(
        actual=_arms(source="isinstance(x, int) and x"),
        expected=(Arms(name="x", when_true="int & !None", when_false=None),),
    )


def test_or_unions_the_true_sides_and_conjoins_the_false() -> None:
    """Check ``or`` merges positive types and every false side."""
    expect_equal(
        actual=_arms(source="isinstance(x, int) or isinstance(x, str)"),
        expected=(
            Arms(name="x", when_true="int | str", when_false="!int & !str"),
        ),
    )


def test_or_with_an_unreadable_operand_keeps_the_false_side() -> None:
    """Check that ``or`` stays sound when one operand says nothing."""
    expect_equal(
        actual=_arms(source="isinstance(x, int) or compute()"),
        expected=(Arms(name="x", when_true=None, when_false="!int"),),
    )


def test_other_tests_say_nothing() -> None:
    """Check that non-``isinstance`` tests are opaque to narrowing."""
    expect_equal(actual=_arms(source="x > 3"), expected=())
    expect_equal(actual=_arms(source="len(x)"), expected=())
    expect_equal(actual=_arms(source="x == y"), expected=())


def test_isinstance_with_a_non_name_subject_is_opaque() -> None:
    """Check that ``isinstance(self.x, int)`` narrows nothing."""
    expect_equal(actual=_arms(source="isinstance(self.x, int)"), expected=())


def test_isinstance_with_a_non_name_class_is_opaque() -> None:
    """Check that ``isinstance(x, mod.C)`` narrows nothing."""
    expect_equal(actual=_arms(source="isinstance(x, mod.C)"), expected=())


def test_class_pattern() -> None:
    """Check ``case int()`` narrows positively and subtracts later."""
    expect_equal(
        actual=_case(source="int()"),
        expected=CaseArms(positive="int", excluded=("int",)),
    )


def test_module_class_pattern() -> None:
    """Check ``case A()`` resolves against the module's classes."""
    expect_equal(
        actual=_case(source="A()", classes=frozenset({"A"})),
        expected=CaseArms(positive="A", excluded=("A",)),
    )
    expect_equal(
        actual=_case(source="A()"),
        expected=CaseArms(positive=None, excluded=()),
    )


def test_literal_patterns() -> None:
    """Check literal values give their builtin type without subtracting."""
    expect_equal(
        actual=_case(source="1"),
        expected=CaseArms(positive="int", excluded=()),
    )
    expect_equal(
        actual=_case(source='"a"'),
        expected=CaseArms(positive="str", excluded=()),
    )
    expect_equal(
        actual=_case(source="-1"),
        expected=CaseArms(positive="int", excluded=()),
    )


def test_none_and_bool_singletons() -> None:
    """Check ``case None`` subtracts while ``case True`` only narrows."""
    expect_equal(
        actual=_case(source="None"),
        expected=CaseArms(positive="None", excluded=("None",)),
    )
    expect_equal(
        actual=_case(source="True"),
        expected=CaseArms(positive="bool", excluded=()),
    )


def test_or_pattern_unions_the_positives() -> None:
    """Check ``case int() | str()`` gives the union."""
    expect_equal(
        actual=_case(source="int() | str()"),
        expected=CaseArms(positive="int | str", excluded=("int", "str")),
    )


def test_capture_and_sequence_patterns_stay_opaque() -> None:
    """Check ``case x``, ``case [a]`` and ``case {"k": v}`` say nothing."""
    expect_equal(
        actual=_case(source="x"),
        expected=CaseArms(positive=None, excluded=()),
    )
    expect_equal(
        actual=_case(source="[a, b]"),
        expected=CaseArms(positive=None, excluded=()),
    )
    expect_equal(
        actual=_case(source='{"k": v}'),
        expected=CaseArms(positive=None, excluded=()),
    )


def test_as_pattern_delegates() -> None:
    """Check ``case int() as n`` reads like ``case int()``."""
    expect_equal(
        actual=_case(source="int() as n"),
        expected=CaseArms(positive="int", excluded=("int",)),
    )


def test_exception_types_single_and_tuple() -> None:
    """Check ``except E`` and ``except (E, F)`` resolve to names."""
    handler: ExceptHandler = _handler(source="ValueError as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=Constants.classes,
        ),
        expected="ValueError",
    )
    handler = _handler(source="(ValueError, TypeError) as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=Constants.classes,
        ),
        expected="ValueError | TypeError",
    )


def test_exception_types_module_class_and_bare() -> None:
    """Check module classes resolve and a bare ``except`` binds nothing."""
    handler: ExceptHandler = _handler(source="MyError as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=frozenset({"MyError"}),
        ),
        expected="MyError",
    )
    handler = _handler(source="")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=Constants.classes,
        ),
        expected=None,
    )


def test_exception_types_refuses_unresolvable_names() -> None:
    """Check an unknown or shadowed name stays opaque."""
    handler: ExceptHandler = _handler(source="Weird as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=Constants.classes,
        ),
        expected=None,
    )
    handler = _handler(source="int as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts={"int": 1},
            classes=Constants.classes,
        ),
        expected=None,
    )
    handler = _handler(source="mod.Error as e")
    expect_equal(
        actual=exception_types(
            node=handler.type,
            counts=Constants.counts,
            classes=Constants.classes,
        ),
        expected=None,
    )
