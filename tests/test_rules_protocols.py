"""Verify structural-usage analysis and Protocol rendering."""

from __future__ import annotations

from ast import (
    ClassDef,
    parse,
)
from textwrap import dedent

from astart.rules.protocols import (
    Member,
    StructuralUsage,
    protocol_source,
    structural_usage,
)

from tests.expectations import (
    FunctionStatement,
    expect_equal,
    expect_function_node,
    expect_in,
    expect_not_none,
    expect_true,
)


def _usage(*, source: str, parameter: str) -> StructuralUsage | None:
    """Return the structural usage of one parameter.

    Args:
        source: Python source holding one function.
        parameter: Parameter name to analyse.

    Returns:
        The structural usage, or ``None``.

    """
    function: FunctionStatement = expect_function_node(
        value=parse(source=dedent(text=source)).body[0],
    )
    return structural_usage(function=function, parameter=parameter, counts={})


def test_method_call_and_property_become_members() -> None:
    """Check that method call and property become members."""
    usage: StructuralUsage | None = _usage(
        source="""
        def load(src):
            data = src.read(1)
            return data, src.name
        """,
        parameter="src",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(name="name", is_method=False, positional=(), keywords=()),
            Member(
                name="read",
                is_method=True,
                positional=("int",),
                keywords=(),
            ),
        ),
    )


def test_keyword_arguments_become_keyword_only_slots() -> None:
    """Check that keyword arguments become keyword only slots."""
    usage: StructuralUsage | None = _usage(
        source="""
        def send(sink, payload):
            sink.write(payload, mode="w")
        """,
        parameter="sink",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="write",
                is_method=True,
                positional=(None,),
                keywords=(("mode", "str"),),
            ),
        ),
    )


def test_same_member_with_different_types_loses_the_type() -> None:
    """Check that same member with different types loses the type."""
    usage: StructuralUsage | None = _usage(
        source="""
        def f(src):
            src.read(1)
            src.read("a")
        """,
        parameter="src",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members[0].positional,
        expected=(None,),
    )


def test_refusals() -> None:
    """Check that unsafe uses give no protocol."""
    refused: dict[str, str] = {
        "bare use": """\
def f(p):
    return p
""",
        "passed on": """\
def f(p):
    return g(p)
""",
        "attribute store": """\
def f(p):
    p.x = 1
""",
        "augmented store": """\
def f(p):
    p.x += 1
""",
        "rebinding": """\
def f(p):
    p = 3
    return p.x
""",
        "loop binding": """\
def f(p):
    for p in q:
        p.x
""",
        "dunder": """\
def f(p):
    return p.__len__()
""",
        "star call": """\
def f(p, a):
    return p.m(*a)
""",
        "double star call": """\
def f(p, a):
    return p.m(**a)
""",
        "arity clash": """\
def f(p):
    p.m(1)
    p.m(1, 2)
""",
        "mixed awaited call": """\
async def f(p):
    await p.m()
    p.m()
""",
        "unused": """\
def f(p):
    return 1
""",
        "subscript": """\
def f(p):
    return p[0].x
""",
        "global": """\
def f(p):
    global p
    return p.x
""",
        "nested rebind": """\
def f(p):
    def g(p):
        return p
    return p.x
""",
    }
    for label, source in refused.items():
        function: FunctionStatement = expect_function_node(
            value=parse(source=source).body[0],
        )
        expect_equal(
            actual=structural_usage(
                function=function,
                parameter="p",
                counts={},
            ),
            expected=None,
            message=label,
        )


def test_member_returns_come_from_return_use() -> None:
    """Check that a member returned everywhere takes the function's return."""
    usage: StructuralUsage | None = _usage(
        source="""
        def load(src) -> bytes:
            return src.read()
        """,
        parameter="src",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="read",
                is_method=True,
                positional=(),
                keywords=(),
                returns="bytes",
            ),
        ),
    )


def test_member_returns_need_every_result_returned() -> None:
    """Check that mixed result uses leave the return unannotated."""
    usage: StructuralUsage | None = _usage(
        source="""
        def load(src) -> bytes:
            src.read()
            return src.read()
        """,
        parameter="src",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members[0].returns,
        expected=None,
    )


def test_property_returns_come_from_return_use() -> None:
    """Check that a returned-everywhere property takes the return type."""
    usage: StructuralUsage | None = _usage(
        source="""
        def size(box) -> int:
            return box.count
        """,
        parameter="box",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="count",
                is_method=False,
                positional=(),
                keywords=(),
                returns="int",
            ),
        ),
    )


def test_awaited_member_becomes_async() -> None:
    """Check that an awaited member renders as ``async def``."""
    usage: StructuralUsage | None = _usage(
        source="""
        async def fetch(client) -> bytes:
            return await client.get()
        """,
        parameter="client",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="get",
                is_method=True,
                positional=(),
                keywords=(),
                returns="bytes",
                is_async=True,
            ),
        ),
    )
    text: str = protocol_source(
        name="FetchClientProtocol",
        function="fetch",
        parameter="client",
        usage=expect_not_none(value=usage),
    )
    expect_in(item="async def get(self) -> bytes: ...", container=text)


def test_flow_typed_arguments_come_from_env() -> None:
    """Check that env types type member call arguments."""
    function: FunctionStatement = expect_function_node(
        value=parse(
            source=dedent(
                text="""
                def send(sink, payload):
                    sink.write(payload)
                """,
            ),
        ).body[0],
    )
    usage: StructuralUsage | None = structural_usage(
        function=function,
        parameter="sink",
        counts={},
        env={"payload": "str"},
    )
    expect_equal(
        actual=expect_not_none(value=usage).members[0].positional,
        expected=("str",),
    )


def test_direct_call_becomes_call_member() -> None:
    """Check that calling the parameter yields a ``__call__`` member."""
    usage: StructuralUsage | None = _usage(
        source="""
        def run(task) -> int:
            return task(1, mode="w")
        """,
        parameter="task",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="__call__",
                is_method=True,
                positional=("int",),
                keywords=(("mode", "str"),),
                returns="int",
            ),
        ),
    )
    text: str = protocol_source(
        name="RunTaskProtocol",
        function="run",
        parameter="task",
        usage=expect_not_none(value=usage),
    )
    expect_in(
        item="def __call__(self, arg0: int, /, *, mode: str) -> int: ...",
        container=text,
    )


def test_protocol_source_renders_members() -> None:
    """Check that protocol source renders members."""
    usage: StructuralUsage | None = _usage(
        source="""
        def load(src):
            src.write(1, mode="w")
            return src.name
        """,
        parameter="src",
    )
    text: str = protocol_source(
        name="LoadSrcProtocol",
        function="load",
        parameter="src",
        usage=expect_not_none(value=usage),
    )
    expect_true(
        condition=isinstance((parse(source=text)).body[0], ClassDef),
    )
    expect_in(item="class LoadSrcProtocol(Protocol):", container=text)
    expect_in(
        item="def write(self, arg0: int, /, *, mode: str)",
        container=text,
    )
    expect_in(item="@property", container=text)
    expect_in(item="def name(self)", container=text)
