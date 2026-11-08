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

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from ast import Module
    from collections.abc import Callable

    from astart.rules.jsonvalue import JsonValue
    from astart.rules.procedural import Candidate


def _hits(
    fn: Callable[..., tuple[Candidate, ...]],
    source: str,
) -> list[dict[str, JsonValue]]:
    """Run a detector and return evidence dicts.

    Args:
        fn: Detector function.
        source: Python source.

    Returns:
        Evidence mappings.

    """
    module: Module = parse(source=source)
    return [hit.evidence for hit in fn(module=module, filename="t.py")]


def test_missing_argument_flags_absent_required_param() -> None:
    """``f(1)`` against ``f(a, b)`` reports ``b`` missing."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_missing_arguments,
        source="def f(a, b, *, c=1):\n    pass\n\nf(1)\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["parameter"], expected="b")


def test_missing_argument_covers_methods() -> None:
    """``C().m()`` against ``m(self, x)`` reports ``x`` missing."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_missing_arguments,
        source="class C:\n    def m(self, x):\n        pass\n\nC().m()\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["parameter"], expected="x")


def test_missing_argument_skips_complete_calls() -> None:
    """A fully supplied call produces no candidate."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_missing_arguments,
        source="def f(a, b):\n    pass\n\nf(1, 2)\nf(1, b=2)\n",
    )
    expect_equal(actual=len(hits), expected=0)


def test_unexpected_argument_flags_unknown_keyword() -> None:
    """``f(1, 2, z=4)`` reports the unexpected keyword."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_unexpected_arguments,
        source="def f(a, b):\n    pass\n\nf(1, 2, z=4)\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0]["error"],
        expected="unexpected keyword arguments: z",
    )


def test_unexpected_argument_flags_surplus_positional() -> None:
    """``f(1, 2, 3)`` against two parameters reports surplus args."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_unexpected_arguments,
        source="def f(a, b):\n    pass\n\nf(1, 2, 3)\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0]["error"],
        expected="too many positional arguments",
    )


def test_unexpected_argument_skips_valid_calls() -> None:
    """Keyword and ``**kwargs`` calls are not flagged."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_unexpected_arguments,
        source="def f(a, **kw):\n    pass\n\nf(1, z=4)\n",
    )
    expect_equal(actual=len(hits), expected=0)


def test_ambiguous_flags_indeterminate_expansion() -> None:
    """``f(*xs)`` cannot decide arity — indeterminate binding."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_ambiguous_callees,
        source="def f(a, b):\n    pass\n\nxs = [1, 2]\nf(*xs)\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["callee"], expected="f")


def test_ambiguous_skips_determinate_calls() -> None:
    """Ordinary calls are never ambiguous."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_ambiguous_callees,
        source="def f(a, b):\n    pass\n\nf(1, 2)\n",
    )
    expect_equal(actual=len(hits), expected=0)


def test_unresolved_flags_redefined_function() -> None:
    """A twice-defined name cannot be trusted."""
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_unresolved_callees,
        source="def f(a):\n    pass\ndef f(a, b):\n    pass\n\nf(1)\n",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0]["callee"], expected="f")


def test_unresolved_flags_conditional_definition() -> None:
    """A def under ``if/else`` is ambiguous across branches."""
    hits: list[dict[str, JsonValue]] = _hits(
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
    hits: list[dict[str, JsonValue]] = _hits(
        fn=find_unresolved_callees,
        source=(
            "def h(a):\n    pass\n\nh(1)\nprint(1)\nlen('a')\nunknown_fn(2)\n"
        ),
    )
    expect_equal(actual=len(hits), expected=0)
