"""``SlotTable`` settles only when every claim names one kind."""

from __future__ import annotations

from astart.rules.slots import SlotTable

from tests.support.expectations import expect_equal, expect_true


def test_an_empty_slot_settles_to_none() -> None:
    """Check that a slot with no deposits has no answer."""
    table: SlotTable = SlotTable()
    expect_equal(actual=table.settle(slot="s"), expected=None)
    expect_equal(actual=table.claims(slot="s"), expected={})


def test_two_sources_for_one_kind_settle_to_it() -> None:
    """Check that agreeing sources settle to their shared kind."""
    table: SlotTable = SlotTable()
    table.deposit(slot="s", kind="int", source="call-site")
    table.deposit(slot="s", kind="int", source="body")
    expect_equal(actual=table.settle(slot="s"), expected="int")
    expect_equal(
        actual=table.claims(slot="s"),
        expected={"int": {"call-site", "body"}},
    )


def test_two_kinds_leave_the_slot_unsettled() -> None:
    """Check that disagreeing kinds never settle."""
    table: SlotTable = SlotTable()
    table.deposit(slot="s", kind="int", source="call-site")
    table.deposit(slot="s", kind="str", source="body")
    expect_equal(actual=table.settle(slot="s"), expected=None)


def test_the_same_source_twice_counts_once() -> None:
    """Check that a repeated deposit does not duplicate its source."""
    table: SlotTable = SlotTable()
    table.deposit(slot="s", kind="int", source="call-site")
    table.deposit(slot="s", kind="int", source="call-site")
    expect_equal(
        actual=table.claims(slot="s"),
        expected={"int": {"call-site"}},
    )


def test_slots_do_not_leak_into_each_other() -> None:
    """Check that deposits stay inside their own slot."""
    table: SlotTable = SlotTable()
    table.deposit(slot="a", kind="int", source="s1")
    table.deposit(slot="b", kind="str", source="s2")
    expect_equal(actual=table.settle(slot="a"), expected="int")
    expect_equal(actual=table.settle(slot="b"), expected="str")
    expect_true(condition=table.claims(slot="a")["int"] == {"s1"})
