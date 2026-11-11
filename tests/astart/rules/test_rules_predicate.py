"""Verify the predicate algebra of the rule ontology."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from astart.rules.predicate import (
    AllOf,
    AnyOf,
    Compare,
    CompareOp,
    Exists,
    Not,
    Predicate,
    evaluate,
    predicate_facts,
    predicate_from_json,
    predicate_to_json,
)

from tests.support.expectations import expect_equal, expect_false, expect_true

if TYPE_CHECKING:
    from astart.rules.jsonvalue import JsonValue


def _flag(*, name: str, value: bool = True) -> Compare:
    """Build an equality comparison on a boolean fact.

    Args:
        name (str): Fact name.
        value (bool): Expected value.

    Returns:
        Compare: The comparison.

    """
    return Compare(fact=name, op=CompareOp.eq, value=value)


def test_round_trip_every_node_kind() -> None:
    """Serialize and restore each predicate kind."""
    predicate: Predicate = AllOf(
        items=(
            AnyOf(items=(_flag(name="a"), _flag(name="b", value=False))),
            Not(item=Compare(fact="n", op=CompareOp.gt, value=2)),
            Exists(selector="Call", where=_flag(name="c")),
        ),
    )
    payload: JsonValue = predicate_to_json(predicate=predicate)
    expect_equal(
        actual=predicate_from_json(value=payload),
        expected=predicate,
    )


def test_evaluate_all_any_not_compare() -> None:
    """Evaluate the boolean connectives over two facts."""
    for first in (True, False):
        for second in (True, False):
            facts: dict[str, bool] = {"a": first, "b": second}
            expect_equal(
                actual=evaluate(
                    predicate=AllOf(items=(_flag(name="a"), _flag(name="b"))),
                    facts=facts,
                ),
                expected=first and second,
            )
            expect_equal(
                actual=evaluate(
                    predicate=AnyOf(items=(_flag(name="a"), _flag(name="b"))),
                    facts=facts,
                ),
                expected=first or second,
            )
            expect_equal(
                actual=evaluate(
                    predicate=Not(item=_flag(name="a")),
                    facts=facts,
                ),
                expected=not first,
            )


def test_ordering_ops_on_ints() -> None:
    """Compare integers with every operator."""
    facts: dict[str, int] = {"n": 3}
    cases: dict[CompareOp, tuple[int, bool]] = {
        CompareOp.eq: (3, True),
        CompareOp.ne: (3, False),
        CompareOp.lt: (4, True),
        CompareOp.le: (3, True),
        CompareOp.gt: (3, False),
        CompareOp.ge: (3, True),
    }
    for op, (value, expected) in cases.items():
        expect_equal(
            actual=evaluate(
                predicate=Compare(fact="n", op=op, value=value),
                facts=facts,
            ),
            expected=expected,
        )


def test_ordering_ops_on_strings_and_mixed_types() -> None:
    """Order strings and reject unordered mixes."""
    expect_true(
        condition=evaluate(
            predicate=Compare(fact="s", op=CompareOp.lt, value="b"),
            facts={"s": "a"},
        ),
    )
    with pytest.raises(expected_exception=TypeError, match="cannot order"):
        evaluate(
            predicate=Compare(fact="s", op=CompareOp.lt, value=1),
            facts={"s": "a"},
        )


def test_missing_fact_raises_key_error() -> None:
    """Fail loudly when a fact was not computed."""
    with pytest.raises(expected_exception=KeyError, match="missing"):
        evaluate(predicate=_flag(name="missing"), facts={})


def test_exists_is_not_evaluable_here() -> None:
    """Leave quantification to the engine."""
    with pytest.raises(expected_exception=NotImplementedError, match="Call"):
        evaluate(
            predicate=Exists(selector="Call", where=_flag(name="a")),
            facts={"a": True},
        )


def test_from_json_rejects_unknown_op() -> None:
    """Name the offending operator."""
    with pytest.raises(expected_exception=ValueError, match="nand"):
        predicate_from_json(value={"op": "nand", "of": []})
    with pytest.raises(expected_exception=ValueError, match="object"):
        predicate_from_json(value=[])


def test_predicate_facts_collects_nested_names() -> None:
    """Gather every fact a predicate reads."""
    predicate: Predicate = AllOf(
        items=(
            _flag(name="a"),
            Not(item=AnyOf(items=(_flag(name="b"), _flag(name="c")))),
            Exists(selector="Call", where=_flag(name="d")),
        ),
    )
    expect_equal(
        actual=predicate_facts(predicate=predicate),
        expected=frozenset({"a", "b", "c", "d"}),
    )
    expect_false(
        condition=bool(predicate_facts(predicate=AllOf(items=()))),
    )
