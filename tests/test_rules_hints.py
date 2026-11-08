"""Verify the corroborated type-hint engine."""

from __future__ import annotations

from ast import AST, AsyncFunctionDef, FunctionDef, arg, walk
from textwrap import dedent
from typing import TYPE_CHECKING

from astart import parse
from astart.ast import CommentedModule
from astart.rules.hints import (
    Hint,
    HintBasis,
    HintCache,
    HintIndex,
    LazyHints,
    is_allowed_source,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest
    from astart import GraphConversion


def _index(
    *,
    source: str,
) -> tuple[HintIndex, list[FunctionDef | AsyncFunctionDef]]:
    """Build the hint index of a snippet.

    Args:
        source: Python source.

    Returns:
        The index and the function definitions in source order.

    """
    module: CommentedModule = parse(
        source=dedent(text=source),
        filename="s.py",
    )
    functions: list[FunctionDef | AsyncFunctionDef] = [
        node
        for node in walk(node=module)
        if isinstance(node, (FunctionDef, AsyncFunctionDef))
    ]
    return HintIndex.create(module=module, stubs_path=None), functions


def _first_parameter(*, function: FunctionDef | AsyncFunctionDef) -> arg:
    """Return the first parameter that is not self or cls.

    Args:
        function: Function definition.

    Returns:
        The parameter node.

    """
    parameters: list[arg] = [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]
    return next(p for p in parameters if p.arg not in {"self", "cls"})


def test_default_literal_corroborates_parameter() -> None:
    """Accept a hint that matches the default's literal type."""
    index, functions = _index(
        source="""\
        def f(sep=" "):
            return sep.join([])
        """,
    )
    hint: Hint | None = index.hint_for(
        node=_first_parameter(function=functions[0]),
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="str", basis=HintBasis.default_literal),
    )


def test_call_sites_corroborate_parameter() -> None:
    """Accept a hint every in-module call site agrees with."""
    index, functions = _index(
        source="""\
        def scale(x):
            return x * 2


        scale(3)
        scale(4)
        """,
    )
    hint: Hint | None = index.hint_for(
        node=_first_parameter(function=functions[0]),
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="int", basis=HintBasis.call_sites),
    )


def test_uncorroborated_candidate_is_refused() -> None:
    """Refuse an operator-only guess."""
    index, functions = _index(
        source="""\
        def greet(name):
            return "hi " + name
        """,
    )
    node: arg = _first_parameter(function=functions[0])
    expect_is(actual=index.hint_for(node=node), expected=None)
    expect_equal(
        actual=index.rejection_for(node=node),
        expected="uncorroborated",
    )


def test_disagreeing_call_sites_give_no_hint() -> None:
    """Refuse when call sites pass different types."""
    index, functions = _index(
        source="""\
        def f(x):
            return x


        f(1)
        f("a")
        """,
    )
    node: arg = _first_parameter(function=functions[0])
    expect_is(actual=index.hint_for(node=node), expected=None)
    expect_equal(
        actual=index.rejection_for(node=node),
        expected="call sites disagree",
    )


def test_candidates_with_object_or_unknown_names_are_refused() -> None:
    """Never write object, Any or names that are not available."""
    index, functions = _index(
        source="""\
        def count(items):
            return len(items)
        """,
    )
    node: arg = _first_parameter(function=functions[0])
    expect_is(actual=index.hint_for(node=node), expected=None)
    expect_equal(
        actual=index.rejection_for(node=node),
        expected="contains object",
    )


def test_container_call_sites_are_corroborated() -> None:
    """Accept a generic hint that the call site confirms."""
    index, functions = _index(
        source="""\
        def count(items):
            return len(items)


        count([1])
        """,
    )
    hint: Hint | None = index.hint_for(
        node=_first_parameter(function=functions[0]),
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="list[int]", basis=HintBasis.call_sites),
    )


def test_shadowed_callee_calls_are_ignored() -> None:
    """Do not let a shadowing parameter feed call-site evidence."""
    index, functions = _index(
        source="""\
        def f(x):
            return x


        def g(f):
            f(1)
        """,
    )
    expect_is(
        actual=index.hint_for(node=(_first_parameter(function=functions[0]))),
        expected=None,
    )


def test_self_cls_and_varargs_are_never_hinted() -> None:
    """Skip parameters that cannot or should not be annotated."""
    index, functions = _index(
        source="""\
        class K:
            def m(self, a=None, *args, **kw):
                return a


        K().m(1)
        """,
    )
    function: FunctionDef | AsyncFunctionDef = functions[0]
    nodes: list[AST] = [
        function.args.args[0],
        *[a for a in (function.args.vararg, function.args.kwarg) if a],
    ]
    for node in nodes:
        expect_is(actual=index.hint_for(node=node), expected=None)
    # A ``None`` default is hinted ``T | None`` once call sites prove ``T``.
    expect_equal(
        actual=index.hint_for(node=function.args.args[1]),
        expected=Hint(source="int | None", basis=HintBasis.optional_default),
    )


def test_is_allowed_source_accepts_builtins_and_imported_names() -> None:
    """Allow builtins and known names; refuse object and Any."""
    known: frozenset[str] = frozenset({"Sequence"})
    for source in (
        "int",
        "list[int]",
        "dict[str, int] | None",
        "Sequence[int]",
    ):
        expect_true(
            condition=is_allowed_source(source=source, known_names=known),
            message=source,
        )
    for source in (
        "object",
        "Any",
        "list[object]",
        "Mapping[str, int]",
        "not valid (",
    ):
        expect_false(
            condition=is_allowed_source(source=source, known_names=known),
            message=source,
        )
    expect_false(
        condition=is_allowed_source(
            source="Sequence[int]",
            known_names=frozenset(),
        ),
    )


def _return_hint(*, source: str, name: str) -> tuple[Hint | None, str | None]:
    """Return the hint and rejection for a function's return annotation.

    Args:
        source: Python source.
        name: Function name.

    Returns:
        The accepted hint and the rejection reason.

    """
    index, functions = _index(source=source)
    function: FunctionDef | AsyncFunctionDef = next(
        f for f in functions if f.name == name
    )
    return (
        index.hint_for(node=function),
        index.rejection_for(node=function),
    )


def test_function_without_return_value_gets_proven_none() -> None:
    """Prove ``None`` for sync and async functions."""
    for source in (
        """\
def f(a):
    print(a)
""",
        """\
async def f(a):
    print(a)
""",
        """\
def f():
    return
""",
        """\
def f():
    return None
""",
        """\
class K:
    def __init__(self):
        self.x = 1
""",
    ):
        name: str = "__init__" if "__init__" in source else "f"
        hint, _ = _return_hint(source=source, name=name)
        expect_equal(
            actual=hint,
            expected=Hint(source="None", basis=HintBasis.proven_none),
            message=source,
        )


def test_mixed_returns_and_generators_never_get_none() -> None:
    """Refuse None when any path yields or returns a value."""
    for source in (
        """\
def f(a):
    if a:
        return
    return 1
""",
        """\
def f():
    yield 1
""",
        """\
async def f():
    yield 1
""",
        """\
def f():
    yield from []
""",
    ):
        hint, _ = _return_hint(source=source, name="f")
        expect_true(
            condition=hint is None or hint.basis is not HintBasis.proven_none,
            message=source,
        )


def test_overload_abstract_and_stub_bodies_get_no_none() -> None:
    """Never claim None for functions that are declarations."""
    for source in (
        dedent(
            text="""\
    from typing import overload


    @overload
    def f(a: int) -> int: ...
    """,
        ),
        dedent(
            text="""\
    import abc


    class K:
        @abc.abstractmethod
        def f(self):
            pass
    """,
        ),
        """\
def f(): ...
""",
        """\
def f():
    pass
""",
        """\
def f():
    \"""Doc.\"""
""",
        """\
def f():
    raise NotImplementedError
""",
    ):
        hint, _ = _return_hint(source=source, name="f")
        expect_is(actual=hint, expected=None, message=source)


def test_nested_function_returns_do_not_count() -> None:
    """Look only at the function's own returns."""
    hint, _ = _return_hint(
        source="""\
def f():
    def g():
        return 1
    g()
""",
        name="f",
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="None", basis=HintBasis.proven_none),
    )


def test_derived_return_requires_untainted_returns() -> None:
    """Accept a derived return only once the parameters are typed."""
    hint, reason = _return_hint(
        source="""\
def f(x):
    return x * 2
""",
        name="f",
    )
    expect_is(actual=hint, expected=None)
    expect_equal(actual=reason, expected="tainted by parameter x")
    hint, _ = _return_hint(
        source="""\
def f(x):
    return x * 2


f(3)
""",
        name="f",
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="int", basis=HintBasis.derived_return),
    )


def test_taint_flows_through_locals() -> None:
    """Follow assignments, loops and walrus targets."""
    for body in (
        """\
y = x * 2
    return y""",
        """\
y = 0
    for y in x:
        pass
    return y""",
        """\
y = (z := x)
    return z""",
    ):
        hint, reason = _return_hint(
            source=f"""\
def f(x):
    {body}
""",
            name="f",
        )
        expect_is(actual=hint, expected=None, message=body)
        expect_equal(
            actual=reason,
            expected="tainted by parameter x",
            message=body,
        )


def test_return_not_depending_on_parameters_is_accepted() -> None:
    """Accept a concrete return that uses no untyped names."""
    hint, _ = _return_hint(
        source="""\
def one():
    return 1
""",
        name="one",
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="int", basis=HintBasis.syntax_proven),
    )


def test_receivers_taint_methods() -> None:
    """Treat self and cls as untyped sources."""
    hint, reason = _return_hint(
        source="""\
class K:
    def m(self):
        return self.x + 1
""",
        name="m",
    )
    expect_is(actual=hint, expected=None)
    expect_equal(actual=reason, expected="tainted by parameter self")


def test_derived_return_must_be_provable_not_just_plausible() -> None:
    """Refuse a return type the syntax does not establish."""
    hint, reason = _return_hint(
        source="""\
def keys(d):
    return list(d)


keys({'a': 1})
""",
        name="keys",
    )
    expect_is(actual=hint, expected=None)
    expect_equal(actual=reason, expected="return type not provable")


def test_derived_return_types_cover_common_expressions() -> None:
    """Prove returns from literals, operators and typed names."""
    cases: dict[str, str] = {
        "return 1": "int",
        "return 'a'": "str",
        "return 1.5": "float",
        "return True": "bool",
        "return b'x'": "bytes",
        "return not 1": "bool",
        "return [1, 2]": "list[int]",
        "return (1, 'a')": "tuple[int, str]",
        "return {'a': 1}": "dict[str, int]",
        "return 1 + 2": "int",
        "return 1 + 2.5": "float",
        "return 4 / 2": "float",
        "return 'a' + 'b'": "str",
        "return 'a' * 3": "str",
        "return 1 if True else 2": "int",
        "return len('a')": "int",
        "return str(1)": "str",
        "return 1 < 2": "bool",
    }
    for statement, expected in cases.items():
        hint, reason = _return_hint(
            source=f"""\
def f():
    {statement}
""",
            name="f",
        )
        expect_equal(
            actual=None if hint is None else hint.source,
            expected=expected,
            message=f"{statement} -> {reason}",
        )


def test_derived_return_uses_typed_parameters_and_locals() -> None:
    """Follow declared annotations and single-assignment locals."""
    for source, expected in (
        (
            """\
def f(a: int, b: int):
    return a + b
""",
            "int",
        ),
        (
            """\
def f(a: int, b: int):
    return a > b
""",
            "bool",
        ),
        (
            """\
def f(a: int):
    y = a * 2
    return y
""",
            "int",
        ),
        (
            """\
def f(a: int):
    y = a
    y = 'x'
    return y
""",
            None,
        ),
    ):
        hint, _ = _return_hint(source=source, name="f")
        expect_equal(
            actual=None if hint is None else hint.source,
            expected=expected,
            message=source,
        )


def test_unprovable_expressions_are_refused() -> None:
    """Decline containers of unknown contents and attribute access."""
    for statement in (
        "return []",
        "return {}",
        "return list('ab')",
        "return a.b",
        "return a[0]",
    ):
        hint, _ = _return_hint(
            source=f"""\
def f(a: int):
    {statement}
""",
            name="f",
        )
        expect_is(actual=hint, expected=None, message=statement)


def test_falling_off_the_end_adds_none() -> None:
    """Include None when a path returns nothing."""
    hint, _ = _return_hint(
        source="""\
def f(a: int):
    if a:
        return
    return 1
""",
        name="f",
    )
    expect_equal(
        actual=None if hint is None else hint.source,
        expected="int | None",
    )
    # The syntax proves ``int | None`` (the path that falls off returns
    # ``None``) even though the inference says ``int``; the language guarantees
    # it, so the hint is accepted.
    hint, _ = _return_hint(
        source="""\
def f(a: int):
    if a:
        return 1
""",
        name="f",
    )
    expect_equal(
        actual=hint,
        expected=Hint(source="int | None", basis=HintBasis.syntax_proven),
    )
    hint, _ = _return_hint(
        source="""\
def f(a: int):
    if a:
        return 1
    return 2
""",
        name="f",
    )
    expect_equal(
        actual=None if hint is None else hint.source,
        expected="int",
    )


def test_hints_survive_reparsing_the_same_source() -> None:
    """Look hints up by position, not by node identity."""
    source: str = dedent(
        text="""\
        def scale(x):
            return x * 2


        scale(3)
        """,
    )
    index: HintIndex = HintIndex.create(
        module=(parse(source=source, filename="s.py")),
        stubs_path=None,
    )
    second: CommentedModule = parse(source=source, filename="s.py")
    function: FunctionDef = next(
        n for n in walk(node=second) if isinstance(n, FunctionDef)
    )
    expect_equal(
        actual=index.hint_for(node=function.args.args[0]),
        expected=Hint(source="int", basis=HintBasis.call_sites),
    )
    expect_equal(
        actual=index.hint_for(node=function),
        expected=Hint(source="int", basis=HintBasis.derived_return),
    )


def test_cache_shares_one_inference_across_parses(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Infer once per distinct source text.

    Args:
        monkeypatch: Fixture replacing ``CommentedModule.convert``.

    """
    calls: dict[str, int] = {"convert": 0}
    original: Callable[..., GraphConversion] = CommentedModule.convert

    def counting(
        self: CommentedModule,
        *,
        stubs_path: Path,
        filename: str = "<memory>",
        apply: bool = False,
    ) -> GraphConversion:
        """Count the call and delegate to the real conversion.

        Args:
            self: Module being converted.
            stubs_path: Stub directory.
            filename: Reported filename.
            apply: Whether to apply the conversion.

        Returns:
            The conversion result.

        """
        calls["convert"] += 1
        return original(
            self=self,
            stubs_path=stubs_path,
            filename=filename,
            apply=apply,
        )

    monkeypatch.setattr(target=CommentedModule, name="convert", value=counting)
    cache: HintCache = HintCache()
    source: str = """\
def f(a=1):
    return a
"""
    for _ in range(3):
        module: CommentedModule = parse(source=source, filename="s.py")
        LazyHints(
            module=module,
            stubs_path=None,
            source=source,
            cache=cache,
        ).index()
    expect_equal(actual=calls["convert"], expected=1)
    other: str = """\
def g(a=1):
    return a
"""
    LazyHints(
        module=parse(source=other, filename="s.py"),
        stubs_path=None,
        source=other,
        cache=cache,
    ).index()
    expect_equal(actual=calls["convert"], expected=2)
