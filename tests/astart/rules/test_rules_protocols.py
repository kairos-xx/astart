"""Verify structural-usage analysis and Protocol rendering."""

from __future__ import annotations

from ast import (
    ClassDef,
    Compare,
    Module,
    Name,
    arg,
    parse,
    walk,
)
from textwrap import dedent

import pytest
from astart.rules.protocols import (
    Member,
    ProtocolEmit,
    StructuralUsage,
    abstract_parameter,
    builtin_protocol,
    callable_annotation,
    compare_members,
    parameter_has_default,
    protocol_isinstanced,
    protocol_source,
    structural_usage,
    vacuous_usage,
)

from tests.support.expectations import (
    FunctionStatement,
    expect_equal,
    expect_false,
    expect_function_node,
    expect_in,
    expect_not_in,
    expect_not_none,
    expect_true,
)


def _usage(*, source: str, parameter: str) -> StructuralUsage | None:
    """Return the structural usage of one parameter.

    Args:
        source (str): Python source holding one function.
        parameter (str): Parameter name to analyse.

    Returns:
        StructuralUsage | None: The structural usage, or ``None``.

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
        "attribute store of unknown type": """\
def f(p, v):
    p.x = v
""",
        "conflicting attribute stores": """\
def f(p):
    p.x = 1
    p.x = "a"
""",
        "augmented store": """\
def f(p):
    p.x += 1
""",
        "attribute delete": """\
def f(p):
    del p.x
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
        "awaited attribute read": """\
async def f(p):
    x = await p.data
    return x
""",
        "global": """\
def f(p):
    global p
    return p.x
""",
        "identity test": """\
def f(p):
    if p is None:
        return None
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


def test_subscript_now_yields_getitem_member() -> None:
    """Check that ``p[0]`` maps to a ``__getitem__`` member."""
    usage: StructuralUsage | None = _usage(
        source="""
        def pick(p):
            return p[0]
        """,
        parameter="p",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="__getitem__",
                is_method=True,
                positional=("int",),
                keywords=(),
            ),
        ),
    )


def test_writable_attribute_becomes_plain_annotation() -> None:
    """Check that ``p.x = 1`` renders ``x: int``, not a property."""
    usage: StructuralUsage | None = _usage(
        source="""
        def fill(p):
            p.x = 1
        """,
        parameter="p",
    )
    expect_equal(
        actual=expect_not_none(value=usage).members,
        expected=(
            Member(
                name="x",
                is_method=False,
                positional=(),
                keywords=(),
                returns="int",
                writable=True,
            ),
        ),
    )
    text: str = protocol_source(
        name="FillPProtocol",
        function="fill",
        parameter="p",
        usage=expect_not_none(value=usage),
    )
    expect_in(
        item="""\
    x: int
""",
        container=text,
    )


def test_dunder_members_for_protocol_syntax() -> None:
    """Check iteration, ``len``, ``with``, truthiness and operators."""
    usage: StructuralUsage | None = _usage(
        source="""
        def use(p):
            with p as x:
                total = len(p)
                for item in p:
                    pass
                if p and p > 1:
                    return x
            return total
        """,
        parameter="p",
    )
    names: tuple[str, ...] = tuple(
        member.name for member in expect_not_none(value=usage).members
    )
    expect_equal(
        actual=names,
        expected=(
            "__bool__",
            "__enter__",
            "__exit__",
            "__gt__",
            "__iter__",
            "__len__",
        ),
    )
    text: str = protocol_source(
        name="UsePProtocol",
        function="use",
        parameter="p",
        usage=expect_not_none(value=usage),
    )
    expect_in(item="def __len__(self) -> int: ...", container=text)
    expect_in(item="def __bool__(self) -> bool: ...", container=text)
    expect_in(item="def __iter__(self): ...", container=text)
    expect_in(
        item="def __exit__(self, arg0, arg1, arg2, /) -> bool | None: ...",
        container=text,
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


def _member(
    name: str,
    *,
    positional: tuple[str | None, ...] = (),
    returns: str | None = None,
    writable: bool = False,
) -> Member:
    """Build one method protocol member for direct table tests.

    Args:
        name (str): Member name.
        positional (tuple[str | None, ...]): Positional argument annotations.
        returns (str | None): Return annotation.
        writable (bool): ``True`` for a stored member.

    Returns:
        Member: The member.

    """
    return Member(
        name=name,
        is_method=True,
        positional=positional,
        keywords=(),
        returns=returns,
        is_async=False,
        writable=writable,
    )


def _usage_of(*names: str) -> StructuralUsage:
    """Build a usage of method members with the given names.

    Args:
        names (str): Member names.

    Returns:
        StructuralUsage: The usage.

    """
    return StructuralUsage(
        members=tuple(_member(name=name) for name in names),
    )


def test_builtin_protocol_reuses_exact_standard_names() -> None:
    """Check that exact member sets reuse standard protocol names."""
    cases: tuple[tuple[tuple[str, ...], str, str], ...] = (
        (("__len__",), "Sized", "collections.abc"),
        (("__iter__",), "Iterable", "collections.abc"),
        (("__aiter__",), "AsyncIterable", "collections.abc"),
        (("__iter__", "__next__"), "Iterator", "collections.abc"),
        (("__aiter__", "__anext__"), "AsyncIterator", "collections.abc"),
        (("__contains__",), "Container", "collections.abc"),
        (("__hash__",), "Hashable", "collections.abc"),
        (("__await__",), "Awaitable", "collections.abc"),
        (("__reversed__", "__len__"), "Reversible", "collections.abc"),
        (
            ("__contains__", "__iter__", "__len__"),
            "Collection",
            "collections.abc",
        ),
        (
            ("__enter__", "__exit__"),
            "AbstractContextManager",
            "contextlib",
        ),
        (
            ("__aenter__", "__aexit__"),
            "AbstractAsyncContextManager",
            "contextlib",
        ),
        (("__fspath__",), "PathLike", "os"),
    )
    for names, expected_name, module in cases:
        expect_equal(
            actual=builtin_protocol(usage=_usage_of(*names)),
            expected=(expected_name, ((module, expected_name),)),
            message=", ".join(names),
        )
    expect_equal(
        actual=builtin_protocol(
            usage=_usage_of("__iter__", "__next__", "__len__"),
        ),
        expected=None,
    )
    expect_equal(
        actual=builtin_protocol(usage=_usage_of("__len__", "__iter__")),
        expected=None,
    )


def test_builtin_protocol_spells_callable_members() -> None:
    """Check ``__call__`` spellings: exact ``Callable`` or the wildcard."""
    provable: StructuralUsage = StructuralUsage(
        members=(
            _member(
                name="__call__",
                positional=("int", "str"),
                returns="bool",
            ),
        ),
    )
    expect_equal(
        actual=builtin_protocol(usage=provable),
        expected=(
            "Callable[[int, str], bool]",
            (("collections.abc", "Callable"),),
        ),
    )
    keyworded: StructuralUsage = StructuralUsage(
        members=(
            Member(
                name="__call__",
                is_method=True,
                positional=("int",),
                keywords=(("mode", "str"),),
                returns="bool",
            ),
        ),
    )
    expect_equal(
        actual=builtin_protocol(usage=keyworded),
        expected=(
            "Callable[..., object]",
            (("collections.abc", "Callable"),),
        ),
    )
    unproven: StructuralUsage = StructuralUsage(
        members=(_member(name="__call__", positional=("int",)),),
    )
    expect_equal(
        actual=builtin_protocol(usage=unproven),
        expected=(
            "Callable[..., object]",
            (("collections.abc", "Callable"),),
        ),
    )
    async_call: StructuralUsage = StructuralUsage(
        members=(
            Member(
                name="__call__",
                is_method=True,
                positional=("int",),
                keywords=(),
                returns="int",
                is_async=True,
            ),
        ),
    )
    expect_equal(
        actual=builtin_protocol(usage=async_call),
        expected=(
            "Callable[..., object]",
            (("collections.abc", "Callable"),),
        ),
    )


def test_callable_annotation_requires_a_plain_callee() -> None:
    """Check ``callable_annotation`` only spells fully provable calls."""
    provable: StructuralUsage = StructuralUsage(
        members=(
            _member(
                name="__call__",
                positional=("int",),
                returns="str",
            ),
        ),
    )
    expect_equal(
        actual=callable_annotation(usage=provable),
        expected=(
            "Callable[[int], str]",
            (("collections.abc", "Callable"),),
        ),
    )
    keyworded: StructuralUsage = StructuralUsage(
        members=(
            Member(
                name="__call__",
                is_method=True,
                positional=("int",),
                keywords=(("mode", "str"),),
                returns="str",
            ),
        ),
    )
    expect_equal(actual=callable_annotation(usage=keyworded), expected=None)
    two_members: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__call__", positional=("int",), returns="str"),
            _member(name="__len__"),
        ),
    )
    expect_equal(actual=callable_annotation(usage=two_members), expected=None)
    non_call: StructuralUsage = StructuralUsage(
        members=(_member(name="__len__"),),
    )
    expect_equal(actual=callable_annotation(usage=non_call), expected=None)


def test_vacuous_usage_detects_object_satisfied_members() -> None:
    """Check that only-``object`` member sets count as vacuous."""
    vacuous: StructuralUsage = StructuralUsage(
        members=tuple(
            _member(name=name)
            for name in (
                "__bool__",
                "__eq__",
                "__format__",
                "__hash__",
                "__ne__",
                "__repr__",
                "__str__",
            )
        ),
    )
    expect_true(condition=vacuous_usage(usage=vacuous))
    expect_true(condition=vacuous_usage(usage=StructuralUsage(members=())))
    mixed: StructuralUsage = StructuralUsage(
        members=(_member(name="__bool__"), _member(name="__len__")),
    )
    expect_false(condition=vacuous_usage(usage=mixed))
    substantive: StructuralUsage = _usage_of("__len__")
    expect_false(condition=vacuous_usage(usage=substantive))


def test_abstract_parameter_spells_read_only_containers() -> None:
    """Check abstract spellings for iteration, indexing and key lookup."""
    iterable: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__iter__"),
            _member(name="__len__"),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=iterable),
        expected=(
            "Iterable[Any]",
            (("collections.abc", "Iterable"), ("typing", "Any")),
        ),
    )
    int_index: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__getitem__", positional=("int",)),
            _member(name="__len__"),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=int_index),
        expected=(
            "Sequence[Any]",
            (("collections.abc", "Sequence"), ("typing", "Any")),
        ),
    )
    str_index: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__getitem__", positional=("str",)),
            _member(name="__len__"),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=str_index),
        expected=(
            "Mapping[str, Any]",
            (
                ("collections.abc", "Mapping"),
                ("typing", "Any"),
            ),
        ),
    )
    mutable_int: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__getitem__", positional=("int",)),
            _member(name="__len__"),
            _member(name="__setitem__", positional=("int", "int")),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=mutable_int),
        expected=(
            "MutableSequence[Any]",
            (("collections.abc", "MutableSequence"), ("typing", "Any")),
        ),
    )
    mutable_str: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__getitem__", positional=("str",)),
            _member(name="__len__"),
            _member(name="__setitem__", positional=("str", "int")),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=mutable_str),
        expected=(
            "MutableMapping[str, Any]",
            (
                ("collections.abc", "MutableMapping"),
                ("typing", "Any"),
            ),
        ),
    )
    key_only: StructuralUsage = StructuralUsage(
        members=(_member(name="__getitem__", positional=("str",)),),
    )
    expect_equal(
        actual=abstract_parameter(usage=key_only),
        expected=(
            "Mapping[str, Any]",
            (
                ("collections.abc", "Mapping"),
                ("typing", "Any"),
            ),
        ),
    )
    ambiguous: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__getitem__", positional=("bytes",)),
            _member(name="__len__"),
        ),
    )
    expect_equal(actual=abstract_parameter(usage=ambiguous), expected=None)
    writable_member: StructuralUsage = StructuralUsage(
        members=(
            _member(name="__iter__", writable=True),
            _member(name="__len__"),
        ),
    )
    expect_equal(
        actual=abstract_parameter(usage=writable_member),
        expected=None,
    )
    other: StructuralUsage = _usage_of("__len__", "__contains__")
    expect_equal(actual=abstract_parameter(usage=other), expected=None)


def test_protocol_source_emit_variants() -> None:
    """Check ``ProtocolEmit`` rendering for runtime and TYPE_CHECKING."""
    usage: StructuralUsage = StructuralUsage(
        members=(_member(name="__len__", returns="int"),),
    )
    plain: str = protocol_source(
        name="SizedX",
        function="f",
        parameter="x",
        usage=usage,
    )
    expect_in(item="class SizedX(Protocol):", container=plain)
    expect_not_in(item="@runtime_checkable", container=plain)
    expect_not_in(item="if TYPE_CHECKING:", container=plain)
    runtime: str = protocol_source(
        name="SizedX",
        function="f",
        parameter="x",
        usage=usage,
        emit=ProtocolEmit(runtime_checkable=True),
    )
    expect_in(item="@runtime_checkable", container=runtime)
    expect_in(item="class SizedX(Protocol):", container=runtime)
    guarded: str = protocol_source(
        name="SizedX",
        function="f",
        parameter="x",
        usage=usage,
        emit=ProtocolEmit(type_checking=True),
    )
    expect_in(item="if TYPE_CHECKING:", container=guarded)
    expect_in(item="class SizedX(Protocol):", container=guarded)
    both: str = protocol_source(
        name="SizedX",
        function="f",
        parameter="x",
        usage=usage,
        emit=ProtocolEmit(runtime_checkable=True, type_checking=True),
    )
    expect_in(item="if TYPE_CHECKING:", container=both)
    expect_in(item="@runtime_checkable", container=both)


def test_protocol_isinstanced_detects_isinstance_targets() -> None:
    """Check ``isinstance`` target detection for plain and tuple forms."""
    module: Module = parse(
        source=dedent(
            text="""
            def f(x):
                return isinstance(x, P) or isinstance(x, (P, Q))
            """,
        ),
    )
    expect_true(condition=protocol_isinstanced(module=module, names={"P"}))
    expect_true(condition=protocol_isinstanced(module=module, names={"Q"}))
    expect_false(condition=protocol_isinstanced(module=module, names={"R"}))
    skipped: Module = parse(
        source=dedent(
            text="""
            P(x)
            x.isinstance(P)
            isinstance(x)
            isinstance(x, P, extra)
            """,
        ),
    )
    expect_false(
        condition=protocol_isinstanced(module=skipped, names={"P"}),
    )


def test_parameter_has_default_detects_defaults() -> None:
    """Check default detection on positional and keyword-only params."""
    function: FunctionStatement = expect_function_node(
        value=parse(
            source=dedent(
                text="""\
def f(a, b=1, *, c=2, d):
    pass
""",
            ),
        ).body[0],
    )
    parameters: dict[str, arg] = {
        item.arg: item
        for item in [*function.args.args, *function.args.kwonlyargs]
    }
    expect_false(
        condition=parameter_has_default(
            function=function,
            parameter=parameters["a"],
        ),
    )
    expect_true(
        condition=parameter_has_default(
            function=function,
            parameter=parameters["b"],
        ),
    )
    expect_true(
        condition=parameter_has_default(
            function=function,
            parameter=parameters["c"],
        ),
    )
    expect_false(
        condition=parameter_has_default(
            function=function,
            parameter=parameters["d"],
        ),
    )


def test_compare_members_maps_operators_to_dunders() -> None:
    """Check comparison operators name the right dunder members."""
    function: FunctionStatement = expect_function_node(
        value=parse(
            source=dedent(
                text="""\
def f(x, y):
    return x < y < 3
""",
            ),
        ).body[0],
    )
    compare_node: Compare = next(
        node for node in walk(node=function) if isinstance(node, Compare)
    )
    x_node: Name = next(
        node
        for node in walk(node=function)
        if isinstance(node, Name) and node.id == "x"
    )
    y_node: Name = next(
        node
        for node in walk(node=function)
        if isinstance(node, Name) and node.id == "y"
    )
    expect_equal(
        actual=compare_members(
            compare=compare_node,
            node=x_node,
            counts={},
            env=None,
        ),
        expected=[("__lt__", (None,))],
    )
    expect_equal(
        actual=compare_members(
            compare=compare_node,
            node=y_node,
            counts={},
            env=None,
        ),
        expected=[("__gt__", (None,)), ("__lt__", ("int",))],
    )
    identity: FunctionStatement = expect_function_node(
        value=parse(
            source=dedent(
                text="""\
def f(x):
    return x is None
""",
            ),
        ).body[0],
    )
    identity_compare: Compare = next(
        node for node in walk(node=identity) if isinstance(node, Compare)
    )
    identity_name: Name = next(
        node
        for node in walk(node=identity)
        if isinstance(node, Name) and node.id == "x"
    )
    expect_equal(
        actual=compare_members(
            compare=identity_compare,
            node=identity_name,
            counts={},
            env=None,
        ),
        expected=None,
    )


def _member_names(*, source: str, parameter: str = "x") -> tuple[str, ...]:
    """Return the member names one parameter use requires.

    Args:
        source (str): Python source holding one function.
        parameter (str): Parameter name to analyse.

    Returns:
        tuple[str, ...]: Sorted member names of the structural usage.

    """
    usage: StructuralUsage | None = _usage(source=source, parameter=parameter)
    return (
        () if usage is None else tuple(member.name for member in usage.members)
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
def f(x):
    return len(x)
""",
            ("__len__",),
        ),
        (
            """\
def f(x):
    return iter(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return next(x)
""",
            ("__next__",),
        ),
        (
            """\
def f(x):
    return x[0]
""",
            ("__getitem__",),
        ),
        (
            """\
def f(x):
    x[0] = 1
""",
            ("__setitem__",),
        ),
        (
            """\
def f(x):
    del x[0]
""",
            ("__delitem__",),
        ),
        (
            """\
def f(x):
    with x:
        pass
""",
            ("__enter__", "__exit__"),
        ),
        (
            """\
def f(x):
    for i in x:
        pass
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return [i for i in x]
""",
            ("__iter__",),
        ),
        (
            """\
async def f(x):
    return await x
""",
            ("__await__",),
        ),
        (
            """\
def f(x):
    return f'{x}'
""",
            ("__format__",),
        ),
        (
            """\
def f(x):
    return not x
""",
            ("__bool__",),
        ),
        (
            """\
def f(x):
    return -x
""",
            ("__neg__",),
        ),
        (
            """\
def f(x):
    return +x
""",
            ("__pos__",),
        ),
        (
            """\
def f(x):
    return ~x
""",
            ("__invert__",),
        ),
        (
            """\
def f(x):
    return x + 1
""",
            ("__add__",),
        ),
        (
            """\
def f(x):
    return x - 1
""",
            ("__sub__",),
        ),
        (
            """\
def f(x):
    return x * 2
""",
            ("__mul__",),
        ),
        (
            """\
def f(x):
    return x / 2
""",
            ("__truediv__",),
        ),
        (
            """\
def f(x):
    return x % 2
""",
            ("__mod__",),
        ),
        (
            """\
def f(x):
    return x ** 2
""",
            ("__pow__",),
        ),
        (
            """\
def f(x):
    return x << 1
""",
            ("__lshift__",),
        ),
        (
            """\
def f(x):
    return x & 1
""",
            ("__and__",),
        ),
        (
            """\
def f(x):
    return x | 1
""",
            ("__or__",),
        ),
        (
            """\
def f(x):
    return x ^ 1
""",
            ("__xor__",),
        ),
        (
            """\
def f(x):
    return x @ y
""",
            ("__matmul__",),
        ),
        (
            """\
def f(x):
    return x // 2
""",
            ("__floordiv__",),
        ),
        (
            """\
def f(x):
    return x >> 1
""",
            ("__rshift__",),
        ),
        (
            """\
def f(x):
    return x < 1
""",
            ("__lt__",),
        ),
        (
            """\
def f(x):
    return 1 < x
""",
            ("__gt__",),
        ),
        (
            """\
def f(x):
    return x == 1
""",
            ("__eq__",),
        ),
        (
            """\
def f(x):
    return x != 1
""",
            ("__ne__",),
        ),
        (
            """\
def f(x):
    return 1 in x
""",
            ("__contains__",),
        ),
        (
            """\
def f(x):
    return abs(x)
""",
            ("__abs__",),
        ),
        (
            """\
def f(x):
    return hash(x)
""",
            ("__hash__",),
        ),
        (
            """\
def f(x):
    return str(x)
""",
            ("__str__",),
        ),
        (
            """\
def f(x):
    return bool(x)
""",
            ("__bool__",),
        ),
        (
            """\
def f(x):
    return repr(x)
""",
            ("__repr__",),
        ),
        (
            """\
def f(x):
    return int(x)
""",
            ("__int__",),
        ),
        (
            """\
def f(x):
    return float(x)
""",
            ("__float__",),
        ),
        (
            """\
def f(x):
    return complex(x)
""",
            ("__complex__",),
        ),
        (
            """\
def f(x):
    return index(x)
""",
            ("__index__",),
        ),
        (
            """\
def f(x):
    return format(x, 'd')
""",
            ("__format__",),
        ),
        (
            """\
def f(x):
    return reversed(x)
""",
            ("__reversed__",),
        ),
        (
            """\
async def f(x):
    return aiter(x)
""",
            ("__aiter__",),
        ),
        (
            """\
async def f(x):
    return anext(x)
""",
            ("__anext__",),
        ),
        (
            """\
def f(x):
    return all(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return any(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return sum(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return min(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return max(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return sorted(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return list(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return tuple(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return set(x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    print(x)
""",
            ("__str__",),
        ),
        (
            """\
def f(x):
    return x.attr
""",
            ("attr",),
        ),
        (
            """\
def f(x):
    x.attr = 1
""",
            ("attr",),
        ),
        (
            """\
def f(x):
    return x.attr()
""",
            ("attr",),
        ),
        (
            """\
def f(x):
    return x.attr(1, k=2)
""",
            ("attr",),
        ),
        (
            """\
async def f(x):
    return await x.attr()
""",
            ("attr",),
        ),
        (
            """\
def f(x):
    yield from x
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return g(*x)
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    return [*x]
""",
            ("__iter__",),
        ),
        (
            """\
def f(x):
    while x:
        pass
""",
            ("__bool__",),
        ),
        (
            """\
def f(x):
    if x:
        pass
""",
            ("__bool__",),
        ),
        (
            """\
def f(x):
    return x is None
""",
            (),
        ),
        (
            """\
def f(x):
    return callable(x)
""",
            (),
        ),
        (
            """\
def f(x):
    return {**x}
""",
            (),
        ),
        (
            """\
def f(x):
    return x
""",
            (),
        ),
        (
            """\
def f(x):
    x.attr += 1
""",
            (),
        ),
        (
            """\
def f(x):
    del x.attr
""",
            (),
        ),
    ],
)
def test_structural_usage_dunder_members(
    *,
    source: str,
    expected: tuple[str, ...],
) -> None:
    """Check syntax-level uses map to the expected dunder members.

    Args:
        source (str): Python source holding one function.
        expected (tuple[str, ...]): Member names expected, empty for no
            structural usage.

    """
    expect_equal(actual=_member_names(source=source), expected=expected)
