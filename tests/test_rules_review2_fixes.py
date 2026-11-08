"""Regression tests for wrong hints found by the second whole-branch review."""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, walk
from textwrap import dedent
from typing import TYPE_CHECKING

from astart import parse
from astart.rules.hints import HintIndex

from tests.expectations import expect_equal, expect_is

if TYPE_CHECKING:
    from astart.ast import CommentedModule
    from astart.rules.hints import Hint


def _index(*, source: str) -> tuple[HintIndex, dict[str, FunctionDef]]:
    """Build the hint index of a snippet.

    Args:
        source: Python source.

    Returns:
        The index and the function definitions by name.

    """
    module: CommentedModule = parse(
        source=dedent(text=source),
        filename="s.py",
    )
    functions: dict[str, FunctionDef] = {
        node.name: node
        for node in walk(node=module)
        if isinstance(node, FunctionDef)
    }
    return HintIndex.create(module=module, stubs_path=None), functions


def _parameter(*, source: str, function: str, name: str) -> str | None:
    """Return the accepted hint for one parameter.

    Args:
        source: Python source.
        function: Function name.
        name: Parameter name.

    Returns:
        The hint source, or ``None`` when refused.

    """
    index, functions = _index(source=source)
    hint: Hint | None = index.hint_for(
        node=(next(a for a in functions[function].args.args if a.arg == name)),
    )
    return None if hint is None else hint.source


def _returns(*, source: str, function: str) -> str | None:
    """Return the accepted return hint of a function.

    Args:
        source: Python source.
        function: Function name.

    Returns:
        The hint source, or ``None`` when refused.

    """
    index, functions = _index(source=source)
    hint: Hint | None = index.hint_for(node=functions[function])
    return None if hint is None else hint.source


def test_function_used_as_a_value_gets_no_call_site_hint() -> None:
    """Refuse when the name escapes through an alias or a callback."""
    for source in (
        """\
def f(a):
    return a


g = f
g('s')
f(1)
""",
        """\
def f(a):
    return a


list(map(f, ['s']))
f(1)
""",
        dedent(
            text="""\
    from functools import partial


    def f(a, b=0):
        return a


    p = partial(f, 's')
    p(1)
    f(1, 2)
    """,
        ),
        dedent(
            text="""\
    def f(a):
        return a


    def reg(fn):
        fn('s')


    reg(f)
    f(1)
    """,
        ),
        """\
def f(a):
    return a


cb = {'k': f}
cb['k']('s')
f(1)
""",
        dedent(
            text="""\
    def f(a):
        return a


    def outer():
        h = f
        h('s')


    f(1)
    """,
        ),
    ):
        expect_is(
            actual=_parameter(source=source, function="f", name="a"),
            expected=None,
            message=source,
        )
        expect_is(
            actual=_returns(source=source, function="f"),
            expected=None,
            message=source,
        )


def test_directly_called_function_is_still_hinted() -> None:
    """Keep the evidence when the name is only ever called."""
    expect_equal(
        actual=_parameter(
            source="""\
def f(a):
    return a


f(1)
f(2)
""",
            function="f",
            name="a",
        ),
        expected="int",
    )


def test_unknown_argument_types_are_unknown_not_absent() -> None:
    """Treat loop, with and comprehension variables as unknown evidence."""
    for source in (
        dedent(
            text="""\
    def j(a):
        print(a)


    def cw(items):
        for it in items:
            j(it)


    j(1)
    """,
        ),
        dedent(
            text="""\
    def j(a):
        print(a)


    def cw(items):
        with items as f:
            j(f)


    j(1)
    """,
        ),
        dedent(
            text="""\
    def j(a):
        print(a)


    def cw(items):
        [j(i) for i in items]


    j(1)
    """,
        ),
        """\
def j(a):
    print(a)


for it in [1, 2.5]:
    j(it)
j(1)
""",
    ):
        expect_is(
            actual=_parameter(source=source, function="j", name="a"),
            expected=None,
            message=source,
        )


def test_unary_operators_on_bool_give_int() -> None:
    """Only ``not`` yields bool; ``-True`` and ``~True`` are ``int``."""
    for source in (
        """\
def a():
    return -True
""",
        """\
def a():
    return ~True
""",
    ):
        expect_equal(
            actual=_returns(source=source, function="a"),
            expected="int",
            message=source,
        )
    expect_is(
        actual=_returns(
            source="""\
def a(x: bool):
    return -x
""",
            function="a",
        ),
        expected=None,
    )
    expect_equal(
        actual=_returns(
            source="""\
def a():
    return -1
""",
            function="a",
        ),
        expected="int",
    )
    expect_equal(
        actual=_returns(
            source="""\
def a():
    return not 1
""",
            function="a",
        ),
        expected="bool",
    )


def test_nonlocal_rebinding_defeats_single_assignment_typing() -> None:
    """Do not type a local that a nested function rebinds."""
    for value in ("'s'", "2.5"):
        source: str = f"""\
def outer():
    x = 1

    def inner():
        nonlocal x
        x = {value}

    inner()
    return x
"""
        expect_is(
            actual=_returns(source=source, function="outer"),
            expected=None,
            message=value,
        )


def test_bool_arithmetic_at_a_call_site_is_not_bool() -> None:
    """Cross-check the analyzer's argument types with the syntax."""
    expect_is(
        actual=_parameter(
            source="""\
def j(a):
    print(a)


j(True + True)
""",
            function="j",
            name="a",
        ),
        expected=None,
    )
    expect_equal(
        actual=_parameter(
            source="""\
def j(a):
    print(a)


j(True & False)
""",
            function="j",
            name="a",
        ),
        expected="bool",
    )


def test_async_functions_that_escape_are_also_refused() -> None:
    """Apply the escape rule to coroutines too."""
    module: CommentedModule = parse(
        source=dedent(
            text="""\
            async def f(a):
                return a


            handlers = [f]
            """,
        ),
        filename="s.py",
    )
    function: AsyncFunctionDef = next(
        n for n in walk(node=module) if isinstance(n, AsyncFunctionDef)
    )
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    expect_is(
        actual=index.hint_for(node=function.args.args[0]),
        expected=None,
    )
