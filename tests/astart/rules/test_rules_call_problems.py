"""Tests for the M6-05…M6-08 call-shape detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart import parse
from astart.rules.call_problems import (
    find_ambiguous_callees,
    find_missing_arguments,
    find_unexpected_arguments,
    find_unresolved_callees,
)

from tests.support.expectations import expect_equal

type ListDictJsonValue = list[dict[str, JsonValue]]

if TYPE_CHECKING:
    from ast import Module
    from collections.abc import Callable

    from astart.rules.jsonvalue import JsonValue
    from astart.rules.procedural import Candidate


def _hits(
    fn: Callable[..., tuple[Candidate, ...]],
    source: str,
) -> ListDictJsonValue:
    """Run a detector and return evidence dicts.

    Args:
        fn (Callable[..., tuple[Candidate, ...]]): Detector function.
        source (str): Python source.

    Returns:
        ListDictJsonValue: Evidence mappings.

    """
    module: Module = parse(source=source)
    return [hit.evidence for hit in fn(module=module, filename="t.py")]


def test_missing_argument_flags_absent_required_param() -> None:
    """``f(1)`` against ``f(a, b)`` reports ``b`` missing."""
    hits: ListDictJsonValue = _hits(
        fn=find_missing_arguments,
        source="""\
def f(a, b, *, c=1):
    pass

f(1)
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["parameter"], expected="b")


def test_missing_argument_covers_methods() -> None:
    """``C().m()`` against ``m(self, x)`` reports ``x`` missing."""
    hits: ListDictJsonValue = _hits(
        fn=find_missing_arguments,
        source="""\
class C:
    def m(self, x):
        pass

C().m()
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["parameter"], expected="x")


def test_missing_argument_skips_complete_calls() -> None:
    """A fully supplied call produces no candidate."""
    hits: ListDictJsonValue = _hits(
        fn=find_missing_arguments,
        source="""\
def f(a, b):
    pass

f(1, 2)
f(1, b=2)
""",
    )
    expect_equal(actual=len(hits), expected=0)


def test_unexpected_argument_flags_unknown_keyword() -> None:
    """``f(1, 2, z=4)`` reports the unexpected keyword."""
    hits: ListDictJsonValue = _hits(
        fn=find_unexpected_arguments,
        source="""\
def f(a, b):
    pass

f(1, 2, z=4)
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0]["error"],
        expected="unexpected keyword arguments: z",
    )


def test_unexpected_argument_flags_surplus_positional() -> None:
    """``f(1, 2, 3)`` against two parameters reports surplus args."""
    hits: ListDictJsonValue = _hits(
        fn=find_unexpected_arguments,
        source="""\
def f(a, b):
    pass

f(1, 2, 3)
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0]["error"],
        expected="too many positional arguments",
    )


def test_unexpected_argument_skips_valid_calls() -> None:
    """Keyword and ``**kwargs`` calls are not flagged."""
    hits: ListDictJsonValue = _hits(
        fn=find_unexpected_arguments,
        source="""\
def f(a, **kw):
    pass

f(1, z=4)
""",
    )
    expect_equal(actual=len(hits), expected=0)


def test_ambiguous_flags_indeterminate_expansion() -> None:
    """``f(*xs)`` cannot decide arity — indeterminate binding."""
    hits: ListDictJsonValue = _hits(
        fn=find_ambiguous_callees,
        source="""\
def f(a, b):
    pass

xs = [1, 2]
f(*xs)
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["callee"], expected="f")


def test_ambiguous_skips_determinate_calls() -> None:
    """Ordinary calls are never ambiguous."""
    hits: ListDictJsonValue = _hits(
        fn=find_ambiguous_callees,
        source="""\
def f(a, b):
    pass

f(1, 2)
""",
    )
    expect_equal(actual=len(hits), expected=0)


def test_unresolved_flags_redefined_function() -> None:
    """A twice-defined name cannot be trusted."""
    hits: ListDictJsonValue = _hits(
        fn=find_unresolved_callees,
        source="""\
def f(a):
    pass
def f(a, b):
    pass

f(1)
""",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["callee"], expected="f")


def test_unresolved_flags_conditional_definition() -> None:
    """A def under ``if/else`` is ambiguous across branches."""
    hits: ListDictJsonValue = _hits(
        fn=find_unresolved_callees,
        source=(
            "import os\n"
            "if os.name == 'posix':\n"
            "    def g(x):\n        pass\n"
            "else:\n"
            "    def g(x, y):\n        pass\n"
            "g(1)\n"
        ),
    )
    expect_equal(actual=len(hits), expected=1)


def test_unresolved_skips_builtins_and_unknown_names() -> None:
    """``print``/``len``/unknown externals are outside project scope."""
    hits: ListDictJsonValue = _hits(
        fn=find_unresolved_callees,
        source=(
            """\
def h(a):
    pass

h(1)
print(1)
len('a')
unknown_fn(2)
"""
        ),
    )
    expect_equal(actual=len(hits), expected=0)
