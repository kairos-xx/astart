"""Bind many calls with one revision check."""

from __future__ import annotations

from ast import Call, Name, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart import parse
from astart.semantic import SemanticAnalyzer

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    import pytest
    from astart.ast import CommentedModule
    from astart.semantic import MutationEvent


@final
class Constants:
    """Group module-level constants.

    Attributes:
        call_count: Grouped module constant.
        max_refreshes: Grouped module constant.

    """

    call_count: Final[int] = 200
    max_refreshes: Final[int] = 2


def _calls(*, module: CommentedModule) -> list[Call]:
    """Collect the call nodes of a module in source order.

    Args:
        module: Parsed module.

    Returns:
        The call nodes.

    """
    return [node for node in walk(node=module) if isinstance(node, Call)]


def test_bind_calls_matches_bind_call() -> None:
    """Return exactly what one-at-a-time binding returns."""
    module = parse(
        source=dedent(
            text="""\
            def f(a, b=1):
                return a


            f(1)
            f(1, 2)
            print(1)
            unknown(3)
            """,
        ),
    )
    calls = _calls(module=module)
    expect_equal(
        actual=module.bind_calls(nodes=calls),
        expected=[module.bind_call(node=call) for call in calls],
    )
    expect_equal(actual=module.bind_calls(nodes=[]), expected=[])


def test_bind_calls_costs_a_constant_number_of_revision_checks(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not re-fingerprint the tree once per call."""
    lines = [
        """\
def f(a):
    return a
""",
    ]
    lines.extend(
        f"""\
f({index})
"""
        for index in range(Constants.call_count)
    )
    module = parse(
        source="""\

""".join(lines),
    )
    calls = _calls(module=module)
    expect_equal(actual=len(calls), expected=Constants.call_count)
    counter = {"refreshes": 0}
    original = SemanticAnalyzer.refresh

    def counting(self: SemanticAnalyzer) -> tuple[MutationEvent, ...]:
        counter["refreshes"] += 1
        return original(self=self)

    monkeypatch.setattr(
        target=SemanticAnalyzer,
        name="refresh",
        value=counting,
    )
    bound = module.bind_calls(nodes=calls)
    expect_true(condition=counter["refreshes"] <= Constants.max_refreshes)
    expect_true(condition=all(item is not None for item in bound))


def test_bind_calls_sees_edits_made_before_the_batch() -> None:
    """Pick up a mutation through the single revision check."""
    module = parse(
        source=dedent(
            text="""\
            def f(a):
                return a


            def g(a, b):
                return a


            f(1)
            """,
        ),
    )
    call = _calls(module=module)[0]
    before = module.bind_calls(nodes=[call])[0]
    expect_equal(
        actual=None if before is None else len(before.arguments),
        expected=1,
    )
    match call.func:
        case Name() as func:
            func.id = "g"
        case _:
            msg = "expected a name callee"
            raise TypeError(msg)
    after = module.bind_calls(nodes=[call])[0]
    expect_equal(
        actual=None if after is None else after.signature.qualified_name,
        expected="g",
    )
