"""Regression tests for signatures, overloads, generics and class types."""

from __future__ import annotations

from ast import Call, Name, walk
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.semantic import (
    ArgumentOrigin,
    ParameterKind,
    TypeExpressionCodec,
    TypeShape,
    subtype,
)
from astart.semantic.type_shapes import type_shape
from astart.source.ast import CommentedModule
from astart.source.node_attributes import read_attribute

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_function_node,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from astart.semantic.type_expressions import TypeExpression
    from astart.semantic.type_inference import TypeSolveStatistics
    from astart.semantic.typing_contracts import (
        BoundArgument,
        BoundCall,
        ContractDiagnostic,
        ContractIndex,
    )


@final
class Constants:
    """Group module-level constants.

    Attributes:
        small_visit_budget (Final[int]): Grouped module constant.
        large_visit_budget (Final[int]): Grouped module constant.

    """

    small_visit_budget: Final[int] = 60
    large_visit_budget: Final[int] = 100


def _call(*, tree: CommentedModule, name: str) -> Call:
    """Find a named call node after performing lazy type inference.

    Args:
        name (str): Identifier of the name being resolved.
        tree (CommentedModule): Tree supplied as CommentedModule for this
            operation.

    Returns:
        Call: Call produced by this operation.

    """
    return next(
        node
        for node in walk(node=tree)
        if isinstance(node, Call)
        and getattr(node.func, "id", getattr(node.func, "attr", "")) == name
    )


def test_all_five_parameter_kinds_and_omitted_default() -> None:
    """Capture inspect-like binding for passed and omitted arguments."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

def f(a: int, /, b: str = 'x', *args: float, c: bool = True, **extras: int) \
-> str:
    return b
r = f(1, c=False)
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="r").inferred),
        expected="str",
    )
    call: Call = expect_instance(value=_call(tree=tree, name="f"), kind=Call)
    bound: BoundCall | None = tree.semantic.bind_call(node=call)
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.valid)
    expect_equal(
        actual=tuple(arg.name for arg in bound.arguments),
        expected=("a", "b", "args", "c", "extras"),
    )
    expect_equal(
        actual=tuple(arg.parameter.kind for arg in bound.arguments),
        expected=tuple(ParameterKind),
    )
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="b")).origin,
        expected=ArgumentOrigin.DEFAULT,
    )
    expect_equal(
        actual=expect_not_none(value=bound.parameter(name="args")).values,
        expected=(),
    )
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="c")).origin,
        expected=ArgumentOrigin.KEYWORD,
    )
    expect_equal(
        actual=expect_not_none(value=bound.parameter(name="extras")).values,
        expected=(),
    )
    expect_equal(
        actual=read_attribute(
            node=call.args[0],
            name="call_parameter_name",
            kind=str,
        ),
        expected="a",
    )
    expect_is(
        actual=read_attribute(
            node=call.args[0],
            name="call_parameter_kind",
            kind=ParameterKind,
        ),
        expected=ParameterKind.POSITIONAL_ONLY,
    )
    expect_true(
        condition=str(object=bound.signature.signature).startswith(
            "f(a: int, /, b: str",
        ),
    )


def test_invalid_positional_only_and_missing_argument() -> None:
    """Reject binding errors instead of fabricating a typed result."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x: int, /, *, y: str) -> bool: return True
z = f(x=2)
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="z").inferred),
        expected="Unknown",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="f"),
    )
    bound = expect_not_none(value=bound)
    expect_false(condition=bound.valid)
    expect_true(
        condition=any("positional-only" in error for error in bound.errors),
    )
    expect_true(condition=any("missing" in error for error in bound.errors))


def test_local_overloads_select_by_argument_type() -> None:
    """Match overload contracts without joining irrelevant return types."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\

from typing import overload
@overload
def transform(value: int) -> list[int]: ...
@overload
def transform(value: str) -> list[str]: ...
def transform(value: int | str) -> list[int] | list[str]: ...
a = transform(2)
b = transform('text')
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[int]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="list[str]",
    )
    expect_equal(
        actual=len(tree.semantic.signature(name="transform")),
        expected=3,
    )


def test_pep695_generic_return_specialization() -> None:
    """Substitute a bounded type parameter through the return contract."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

def identity[T](value: T) -> list[T]:
    return [value]
a = identity(5)
b = identity('hello')
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[int]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="list[str]",
    )


def test_dataclass_synthesized_constructor_and_field() -> None:
    """Bind constructor parameters and infer field reads without imports."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from dataclasses import dataclass
@dataclass
class Person:
    name: str
    age: int = 40
person = Person('Ada')
result = person.age
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="person").inferred),
        expected="Person",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="int",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="Person"),
    )
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.valid)
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="age")).origin,
        expected=ArgumentOrigin.DEFAULT,
    )


def test_instance_method_receiver_and_property() -> None:
    """Resolve implicit self and independently annotated properties."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

class Record:
    def update(self, n: int, /, *, force: bool = False) -> str:
        return 'ok'
    @property
    def title(self) -> str:
        return 'label'
r = Record()
a = r.update(3)
b = r.title
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="str",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="str",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="update"),
    )
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.valid)
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="self")).origin,
        expected=ArgumentOrigin.IMPLICIT_RECEIVER,
    )
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="force")).origin,
        expected=ArgumentOrigin.DEFAULT,
    )


def test_enum_member_nominal_type() -> None:
    """Enum members are their enum class, not the literal underlying value."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from enum import Enum
class Color(Enum):
    RED = 'red'
selected = Color.RED
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="selected").inferred),
        expected="Color",
    )


def test_protocol_structural_members_and_method() -> None:
    """Reject missing members and accept matching structural classes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\

from typing import Protocol
class Named(Protocol):
    name: str
    def label(self, prefix: str) -> str: ...
class Person:
    name: str
    def label(self, prefix: str) -> str: return prefix
class Empty:
    pass
""",
    )
    index: ContractIndex = tree.semantic.types.contracts
    expect_is(
        actual=subtype(
            actual=TypeShape(name="Person"),
            expected=TypeShape(name="Named"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=TypeShape(name="Empty"),
            expected=TypeShape(name="Named"),
            index=index,
        ).compatible,
        expected=False,
    )


def test_override_return_variance_diagnostic() -> None:
    """Inspect source-defined override compatibility without execution."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from typing import override
class Base:
    def f(self, x: int) -> int: return x
class Good(Base):
    @override
    def f(self, x: int) -> bool: return True
class Bad(Base):
    @override
    def f(self, x: str) -> int: return 1
"""
        ),
    )
    issues: tuple[ContractDiagnostic, ...] = tree.semantic.typing_diagnostics
    expect_false(
        condition=any("Good.f" in item.description for item in issues),
    )
    expect_true(condition=any("Bad.f" in item.description for item in issues))


def test_collection_abc_generic_covariance_and_mutability() -> None:
    """Recognize ABC projections, with invariance for mutable containers."""
    expect_is(
        actual=subtype(
            actual=TypeShape(name="list", arguments=(TypeShape(name="int"),)),
            expected=TypeShape(
                name="Sequence",
                arguments=(TypeShape(name="float"),),
            ),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=TypeShape(name="list", arguments=(TypeShape(name="int"),)),
            expected=TypeShape(
                name="MutableSequence",
                arguments=(TypeShape(name="float"),),
            ),
        ).compatible,
        expected=False,
    )


def test_stub_overloads_resolve_by_argument(*, tmp_path: Path) -> None:
    """Use all declaration arguments from external stubs for specialization.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    (tmp_path / "demo.pyi").write_text(
        data=(
            """\

from typing import overload
@overload
def parse(text: str) -> bytes: ...
@overload
def parse(text: bytes) -> str: ...
"""
        ),
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(
        source="""\
import demo
a = demo.parse('x')
b = demo.parse(b'x')
""",
    )
    tree.configure_stubs(root=tmp_path)
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="bytes",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="str",
    )
    expect_is_not(
        actual=tree.semantic.bind_call(node=_call(tree=tree, name="parse")),
        unexpected=None,
    )


def test_unknown_call_does_not_execute_user_program() -> None:
    """Do not evaluate imported decorators, function calls or methods."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
from missing_module import dangerous
x = dangerous(5)
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="x").inferred),
        expected="Unknown",
    )


def test_dataclass_default_factory_and_init_exclusion() -> None:
    """Distinguish default factories and fields excluded from __init__."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from dataclasses import dataclass, field
from typing import ClassVar
@dataclass
class Options:
    names: list[str] = field(default_factory=list)
    count: int = field(init=False)
    shared: ClassVar[int] = 3
x = Options()
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="x").inferred),
        expected="Options",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="Options"),
    )
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.valid)
    expect_equal(
        actual=tuple(item.name for item in bound.arguments),
        expected=("names",),
    )
    names: BoundArgument | None = bound.parameter(name="names")
    names = expect_not_none(value=names)
    expect_is(actual=names.origin, expected=ArgumentOrigin.DEFAULT_FACTORY)
    expect_equal(actual=str(object=names.types[0]), expected="list[str]")
    expect_equal(
        actual=tuple(
            field.name
            for field in tree.semantic.types.contracts.classes[
                "Options"
            ].fields
        ),
        expected=("names", "count", "shared"),
    )


def test_keyword_only_dataclass_and_typed_dict_optional() -> None:
    """Constructor shape covers kw_only and optional TypedDict members."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from dataclasses import dataclass
from typing import TypedDict, NotRequired
@dataclass(kw_only=True)
class User:
    name: str
class Data(TypedDict):
    identifier: int
    comment: NotRequired[str]
u = User(name='Ada')
d = Data(identifier=1)
message = d['comment']
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="u").inferred),
        expected="User",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="d").inferred),
        expected="Data",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="message").inferred),
        expected="str",
    )
    expect_is(
        actual=expect_not_none(
            value=expect_not_none(
                value=tree.semantic.bind_call(
                    node=_call(tree=tree, name="User"),
                ),
            ).parameter(name="name"),
        ).parameter.kind,
        expected=ParameterKind.KEYWORD_ONLY,
    )
    expect_is(
        actual=expect_not_none(
            value=expect_not_none(
                value=tree.semantic.bind_call(
                    node=_call(tree=tree, name="Data"),
                ),
            ).parameter(name="comment"),
        ).origin,
        expected=ArgumentOrigin.DEFAULT,
    )


def test_literal_overload_and_bound_typevar() -> None:
    """Overloaded Literal arguments and bounded generics reject bad input."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from typing import Literal, overload, TypeVar
@overload
def choose(value: Literal[1]) -> str: ...
@overload
def choose(value: Literal[2]) -> bytes: ...
def choose(value: int) -> str | bytes: ...
T = TypeVar('T', bound=int)
def number(value: T) -> T: return value
a = choose(1)
b = choose(2)
c = number(3)
d = number('bad')
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="str",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="bytes",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="c").inferred),
        expected="int",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="d").inferred),
        expected="Unknown",
    )


def test_callable_annotation_and_variance() -> None:
    """Use Callable annotations and contravariant argument compatibility."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from collections.abc import Callable
callback: Callable[[int], str]
result = callback(5)
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="str",
    )
    actual: TypeExpression = TypeExpressionCodec.from_source(
        source="Callable[[float], str]",
    )
    expected: TypeExpression = TypeExpressionCodec.from_source(
        source="Callable[[int], str]",
    )
    expect_is(
        actual=subtype(
            actual=type_shape(expression=actual),
            expected=type_shape(expression=expected),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=type_shape(expression=expected),
            expected=type_shape(expression=actual),
        ).compatible,
        expected=False,
    )


def test_newtype_rejects_incompatible_input() -> None:
    """NewType constructors keep nominal identity distinct from primitives."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from typing import NewType
Identifier = NewType('Identifier', int)
good = Identifier(1)
bad = Identifier('string')
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="good").inferred),
        expected="Identifier",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="bad").inferred),
        expected="Unknown",
    )


def test_chained_class_calls_and_async_results() -> None:
    """Infer receiver types for chained calls and deferred coroutine output."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

class Calculator:
    def add(self, n: int) -> int: return n+1
result = Calculator().add(4)
async def get(n: int) -> int: return n
pending = get(1)
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="int",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="pending").inferred),
        expected="Coroutine[Unknown, Unknown, int]",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="add"),
    )
    bound = expect_not_none(value=bound)
    expect_is(
        actual=expect_not_none(value=bound.parameter(name="self")).origin,
        expected=ArgumentOrigin.IMPLICIT_RECEIVER,
    )


def test_starred_arguments_and_keyword_expansions() -> None:
    """Expand only known source literals, retaining names for all arguments."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

def f(a: int, b: int, *, c: int = 4) -> int: return a+b+c
value = f(*[1,2], **{'c':3})
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="value").inferred),
        expected="int",
    )
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="f"),
    )
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.valid)
    expect_equal(
        actual=[argument.name for argument in bound.arguments],
        expected=["a", "b", "c"],
    )
    expect_true(condition=all(argument.types for argument in bound.arguments))


def test_untrusted_unknown_starred_expansion_remains_uncertain() -> None:
    """Unknown star shapes must not be accepted as definite bindings."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

def f(a: int, b: str) -> bool: return True
result = f(*external())
"""
        ),
    )
    tree.infer_type(node="result")
    bound: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="f"),
    )
    bound = expect_not_none(value=bound)
    expect_true(condition=bound.indeterminate)
    expect_true(condition=any(not entry.definite for entry in bound.arguments))


def test_typeguard_and_typeis_narrowing_on_expression_branches() -> None:
    """TypeGuard adds positive evidence and TypeIs also narrows false paths."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from typing import TypeGuard, TypeIs
def is_str(x: int | str) -> TypeGuard[str]: ...
def is_int(x: int | str) -> TypeIs[int]: ...
value: int | str = external()
a = value if is_str(value) else 'fallback'
b = value if is_int(value) else 'fallback'
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="str",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="int | str",
    )


def test_contract_index_is_rebuilt_after_mutation() -> None:
    """Invalidate signature and inference records after a direct AST edit."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x: int) -> str: ...
y = f(1)
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="y").inferred),
        expected="str",
    )
    expect_function_node(value=tree.body[0]).returns = Name(
        id="bytes",
        ctx=__import__(name="ast").Load(),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="y").inferred),
        expected="bytes",
    )


def test_inherited_dataclass_fields_and_namedtuple_constructor() -> None:
    """Retain base-class fields in a derived synthesized constructor."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from dataclasses import dataclass
from typing import NamedTuple
@dataclass
class Parent:
    name: str
@dataclass
class Child(Parent):
    age: int = 1
class Point(NamedTuple):
    x: int
    y: int
child = Child('Ada')
name = child.name
point = Point(1,2)
y = point.y
"""
        ),
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="child").inferred),
        expected="Child",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="name").inferred),
        expected="str",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="point").inferred),
        expected="Point",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="y").inferred),
        expected="int",
    )
    signature: BoundCall | None = tree.semantic.bind_call(
        node=_call(tree=tree, name="Child"),
    )
    signature = expect_not_none(value=signature)
    expect_equal(
        actual=tuple(arg.name for arg in signature.arguments),
        expected=("name", "age"),
    )


def test_enum_member_name_and_literal_value() -> None:
    """Infer enum instances and their underlying literal member types."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\

from enum import Enum, IntEnum, StrEnum
class Color(Enum):
    RED = 'red'
class Level(IntEnum):
    LOW = 1
class Text(StrEnum):
    YES = 'yes'
a = Color.RED
b = Color.RED.value
c = Level.LOW.value
d = Text.YES.name
"""
        ),
    )
    for key, expected in (
        ("a", "Color"),
        ("b", "str"),
        ("c", "int"),
        ("d", "str"),
    ):
        expect_equal(
            actual=str(object=tree.infer_type(node=key).inferred),
            expected=expected,
        )


def test_stub_submodule_and_typevar_overload(*, tmp_path: Path) -> None:
    """Find nested stub modules and keep scoped generic parameters.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    nested: Path = tmp_path / "package"
    nested.mkdir()
    (nested / "reader.pyi").write_text(
        data=(
            """\

from typing import TypeVar
T = TypeVar('T')
def identity(value: T) -> T: ...
"""
        ),
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(
        source="""\

from package.reader import identity
result = identity('abc')
""",
    )
    tree.configure_stubs(root=tmp_path)
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="str",
    )


@pytest.mark.parametrize(
    "source",
    [
        """\
def f(x:int)->int: return x
y=f(2)""",
        """\
def f(x): return x
y=f(2)""",
        """\
def f[T](x:T)->T: return x
y=f('ok')""",
        """\
def a(x): return b(x)
def b(x): return x
y=a(3)""",
    ],
)
def test_type_worklist_stabilizes_without_ping_pong(*, source: str) -> None:
    """A completed call must not repeatedly enqueue unchanged callers.

    Args:
        source (str): The source examined while a completed call must not
            repeatedly enqueue unchanged callers.

    """
    stats: TypeSolveStatistics = CommentedModule.parse(
        source=source,
    ).semantic.types.statistics
    expect_true(condition=stats.converged)
    expect_true(condition=stats.visits < Constants.small_visit_budget)


def test_recursive_type_contract_widens_and_terminates() -> None:
    """Recursive type growth reaches a conservative fixed point."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\

def wrap(x):
    return [wrap(x)]
result = wrap(1)
""",
    )
    stats: TypeSolveStatistics = tree.semantic.types.statistics
    expect_true(condition=stats.converged)
    expect_true(condition=stats.visits < Constants.large_visit_budget)
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="WidenedUnknown",
    )
