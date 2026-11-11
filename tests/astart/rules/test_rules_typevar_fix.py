"""Verify TypeVar synthesis through the fix runner."""

from __future__ import annotations

from ast import parse
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str, ceiling: FixSafety = FixSafety.guarded) -> FixResult:
    """Run the fixer on a dedented snippet.

    Args:
        source (str): Python source.
        ceiling (FixSafety): Highest fix safety to apply.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling),
    )


def test_identity_function_becomes_generic() -> None:
    """Check that identity function becomes generic."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    parse(source=result.source)
    expect_in(item="from typing import TypeVar", container=result.source)
    expect_in(item="T = TypeVar(", container=result.source)
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_declaration_precedes_the_function() -> None:
    """Check that declaration precedes the function."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    expect_in(item="T = TypeVar", container=result.source)
    assert_order: bool = result.source.index(
        "T = TypeVar",
    ) < result.source.index(
        "def identity",
    )
    expect_equal(actual=assert_order, expected=True)


def test_container_of_the_parameter_keeps_the_variable() -> None:
    """Check that container of the parameter keeps the variable."""
    wrapped: FixResult = _fix(
        source="""\
def wrap(x):
    return [x]
""",
    )
    expect_in(item="def wrap(x: T) -> list[T]:", container=wrapped.source)
    paired: FixResult = _fix(
        source="""\
def pair(x):
    return (x, x)
""",
    )
    expect_in(item="-> tuple[T, T]:", container=paired.source)


def test_call_sites_do_not_override_the_variable() -> None:
    """Check that call sites do not override the variable."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x


identity(1)
""",
    )
    expect_in(item="def identity(x: T) -> T:", container=result.source)


def test_existing_declaration_is_reused() -> None:
    """Check that existing declaration is reused."""
    result: FixResult = _fix(
        source="""
        from typing import TypeVar

        T = TypeVar("T")


        def a(x):
            return x


        def b(y):
            return y
        """,
    )
    expect_equal(actual=result.source.count("TypeVar("), expected=1)
    expect_in(item="def b(y: T) -> T:", container=result.source)


def test_name_collision_picks_a_fresh_variable() -> None:
    """Check that name collision picks a fresh variable."""
    result: FixResult = _fix(
        source="""\
T = 3


def identity(x):
    return x
""",
    )
    expect_in(item="def identity(x: T2) -> T2:", container=result.source)


def test_constraining_uses_get_no_variable() -> None:
    """Check that constraining uses get no variable."""
    for source in (
        """\
def f(x):
    return x + 1
""",
        """\
def f(x):
    return x.name
""",
        """\
def f(x):
    print(x)
    return x
""",
        """\
def f(x):
    print(x)
""",
        """\
def f(x):
    return 1
""",
        """\
def f(x=1):
    return x
""",
        """\
def f(x):
    yield x
""",
    ):
        expect_not_in(
            item="TypeVar",
            container=_fix(source=source).source,
            message=source,
        )


def test_method_declaration_precedes_the_class() -> None:
    """Check that method declaration precedes the class."""
    result: FixResult = _fix(
        source="""
        class Box:
            def get(self, x):
                return x
        """,
    )
    parse(source=result.source)
    expect_equal(
        actual=result.source.index("T = TypeVar")
        < result.source.index("class Box"),
        expected=True,
    )
    expect_in(item="def get(self, x: T) -> T:", container=result.source)


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
    )
    expect_equal(
        actual=(_fix(source=first.source)).source,
        expected=first.source,
    )


def test_proven_ceiling_does_not_synthesize() -> None:
    """Check that proven ceiling does not synthesize."""
    result: FixResult = _fix(
        source="""\
def identity(x):
    return x
""",
        ceiling=FixSafety.proven,
    )
    expect_not_in(item="TypeVar", container=result.source)


def test_boolop_with_shared_type_still_passes_through() -> None:
    """Check that ``x or x`` keeps the passthrough type variable."""
    result: FixResult = _fix(
        source="""\
def either(x):
    return x or x
""",
    )
    expect_in(item="TypeVar", container=result.source)
    expect_in(item="-> T", container=result.source)


def test_boolop_with_mixed_types_stays_refused() -> None:
    """Check that ``x or 0`` gets no type variable (no shared ``T``)."""
    result: FixResult = _fix(
        source="""\
def either(x):
    return x or 0
""",
    )
    expect_not_in(item="TypeVar", container=result.source)


def test_bound_typevar_for_member_use_and_return() -> None:
    """Check that ``x.close(); return x`` gets a bound TypeVar."""
    result: FixResult = _fix(
        source="""\
def release(x):
    x.close()
    return x
""",
    )
    parse(source=result.source)
    expect_in(item="bound=", container=result.source)
    expect_in(item="def release(x: T) -> T:", container=result.source)
    expect_in(
        item="class SupportsClose(Protocol):",
        container=result.source,
    )


def test_bound_typevar_refuses_ambiguous_member_arity() -> None:
    """Check that mixed call arities get no bound TypeVar."""
    result: FixResult = _fix(
        source="""\
def write(x, flag):
    x.write(1)
    if flag:
        x.write(1, 2)
    return x
""",
    )
    expect_not_in(item="bound=", container=result.source)


def test_constrained_typevar_for_isinstance_branches() -> None:
    """Check that isinstance-guarded returns get a constrained TypeVar."""
    result: FixResult = _fix(
        source="""\
def convert(x):
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        return x
    raise ValueError
""",
    )
    parse(source=result.source)
    expect_in(
        item='TypeVar("T", int, str)',
        container=result.source.replace("'", '"'),
    )
    expect_in(item="def convert(x: T) -> T:", container=result.source)


def test_constrained_typevar_refuses_unguarded_return() -> None:
    """Check that an isinstance ``else`` return gets no constraint."""
    result: FixResult = _fix(
        source="""\
def convert(x):
    if isinstance(x, int):
        return x
    else:
        return x
    raise ValueError
""",
    )
    expect_not_in(item="TypeVar(", container=result.source)


def test_constrained_typevar_refuses_bare_fallthrough_none() -> None:
    """Check that fallthrough still annotates ``T | None``."""
    result: FixResult = _fix(
        source="""\
def convert(x):
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        return x
""",
    )
    parse(source=result.source)
    expect_in(item="-> T | None:", container=result.source)


def test_element_subscript_gets_sequence_parameter() -> None:
    """Check that ``items[0]`` gets ``Sequence[T]`` and ``-> T``."""
    result: FixResult = _fix(
        source="""\
def first(items):
    return items[0]
""",
    )
    parse(source=result.source)
    expect_in(
        item="from collections.abc import Sequence",
        container=result.source,
    )
    expect_in(
        item="def first(items: Sequence[T]) -> T:",
        container=result.source,
    )


def test_element_constructor_gets_iterable_parameter() -> None:
    """Check that ``list(it)`` gets ``Iterable[T]`` and ``-> list[T]``."""
    result: FixResult = _fix(
        source="""\
def snapshot(it):
    return list(it)
""",
    )
    parse(source=result.source)
    expect_in(
        item="from collections.abc import Iterable",
        container=result.source,
    )
    expect_in(
        item="def snapshot(it: Iterable[T]) -> list[T]:",
        container=result.source,
    )


def test_element_constructor_tuple_is_variadic() -> None:
    """Check that ``tuple(it)`` spells ``tuple[T, ...]``."""
    result: FixResult = _fix(
        source="""\
def snapshot(it):
    return tuple(it)
""",
    )
    expect_in(item="-> tuple[T, ...]:", container=result.source)


def test_element_refuses_string_subscript() -> None:
    """Check that ``items['k']`` gets no element annotation."""
    result: FixResult = _fix(
        source="""\
def lookup(items):
    return items["k"]
""",
    )
    expect_not_in(item="Sequence", container=result.source)


def test_self_return_gets_self_annotation() -> None:
    """Check that ``return self`` gets ``-> Self``."""
    result: FixResult = _fix(
        source="""\
class Box:
    def copy(self):
        return self
""",
    )
    parse(source=result.source)
    expect_in(item="from typing import Self", container=result.source)
    expect_in(item="def copy(self) -> Self:", container=result.source)


def test_classmethod_constructor_gets_self_annotation() -> None:
    """Check that ``return cls()`` gets ``-> Self``."""
    result: FixResult = _fix(
        source="""\
class Box:
    @classmethod
    def create(cls):
        return cls()
""",
    )
    parse(source=result.source)
    expect_in(item="def create(cls) -> Self:", container=result.source)


def test_self_refuses_other_receiver_uses() -> None:
    """Check that ``self.x = 1; return self`` gets no ``Self``."""
    result: FixResult = _fix(
        source="""\
class Box:
    def fill(self):
        self.value = 1
        return self
""",
    )
    expect_not_in(item="-> Self", container=result.source)


def test_multi_parameter_list_gets_union_return() -> None:
    """Check that ``[a, b]`` gets two TypeVars and ``list[T | T2]``."""
    result: FixResult = _fix(
        source="""\
def pair(a, b):
    return [a, b]
""",
    )
    parse(source=result.source)
    expect_in(
        item="def pair(a: T, b: T2) -> list[T | T2]:",
        container=result.source,
    )


def test_multi_parameter_dict_gets_key_value_variables() -> None:
    """Check that ``{k: v}`` gets ``dict[T, T2]``."""
    result: FixResult = _fix(
        source="""\
def make(k, v):
    return {k: v}
""",
    )
    parse(source=result.source)
    expect_in(
        item="def make(k: T, v: T2) -> dict[T, T2]:",
        container=result.source,
    )


def test_multi_parameter_refuses_nested_containers() -> None:
    """Check that ``[[a], b]`` gets no multi-variable annotation."""
    result: FixResult = _fix(
        source="""\
def nested(a, b):
    return [[a], b]
""",
    )
    expect_not_in(item="TypeVar", container=result.source)


def test_shared_combination_gets_one_typevar() -> None:
    """Check that ``a + b`` shares one TypeVar."""
    result: FixResult = _fix(
        source="""\
def combine(a, b):
    return a + b
""",
    )
    parse(source=result.source)
    expect_equal(actual=result.source.count("= TypeVar("), expected=1)
    expect_in(item="def combine(a: T, b: T)", container=result.source)


def test_unrelated_parameters_get_no_shared_typevar() -> None:
    """Check that parameters never combined get no shared TypeVar."""
    result: FixResult = _fix(
        source="""\
def collect(a, b):
    return [a, b]
""",
    )
    expect_not_in(item="def collect(a: T, b: T)", container=result.source)


def test_forwarding_decorator_gets_paramspec() -> None:
    """Check that a forwarding decorator gets ``ParamSpec``."""
    result: FixResult = _fix(
        source="""\
def deco(f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper
""",
    )
    parse(source=result.source)
    expect_in(item="= ParamSpec(", container=result.source)
    expect_in(item="f: Callable[P, R]", container=result.source)
    expect_in(item="-> Callable[P, R]", container=result.source)


def test_mutating_wrapper_gets_no_paramspec() -> None:
    """Check that a wrapper altering arguments gets no ``ParamSpec``."""
    result: FixResult = _fix(
        source="""\
def deco(f):
    def wrapper(*args, **kwargs):
        return f(1, *args, **kwargs)
    return wrapper
""",
    )
    expect_not_in(item="ParamSpec", container=result.source)
