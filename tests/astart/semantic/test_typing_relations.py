"""Direct, conservative generic/ABC/protocol compatibility regressions."""

from __future__ import annotations

from ast import Module, parse
from typing import TYPE_CHECKING

import pytest
from astart.semantic import (
    ContractIndex,
    TypeShape,
    join_types,
    method_compatible,
    protocol_compatible,
    specialize,
    subtype,
    unify,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_instance,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from astart.semantic.typing_contracts import CallableContract


def _shape(*, name: str, args: tuple[TypeShape, ...] = ()) -> TypeShape:
    """Construct one immutable type shape for a matrix case.

    Args:
        args (tuple[TypeShape, ...]): Collection of args supplied for this
            operation.
        name (str): Identifier of the name being resolved.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    return TypeShape(name=name, arguments=args)


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("int", "int", True),
        ("int", "Any", True),
        ("int", "typing.Any", True),
        ("Unknown", "str", None),
        ("int", "Unknown", None),
        ("Never", "float", True),
        ("int", "object", True),
        ("int", "float", True),
        ("bool", "int", True),
        ("bool", "float", True),
        ("float", "complex", True),
        ("str", "int", False),
        ("str", "bytes", False),
        ("bytes", "str", False),
        ("None", "None", True),
        ("None", "str", False),
        ("dict", "Mapping", True),
        ("list", "MutableSequence", True),
        ("list", "Sequence", True),
        ("list", "Iterable", True),
        ("set", "Set", True),
        ("set", "MutableSet", True),
        ("tuple", "Sequence", True),
        ("str", "Sequence", True),
        ("range", "Iterable", True),
        ("Generator", "Iterator", True),
        ("Iterator", "Iterable", True),
        ("UserClass", "ExternalClass", None),
    ],
)
def test_atomic_assignability(
    *,
    source: str,
    target: str,
    expected: bool | None,
) -> None:
    """Never infer subtype evidence through unrelated builtin types.

    Args:
        expected (bool | None): Expected supplied as bool | None for this
            operation.
        source (str): The source examined while never infer subtype evidence
            through unrelated builtin types.
        target (str): The target examined while never infer subtype evidence
            through unrelated builtin types.

    """
    actual: TypeShape = _shape(name=source)
    wanted: TypeShape = _shape(name=target)
    expect_is(
        actual=subtype(actual=actual, expected=wanted).compatible,
        expected=expected,
    )


def test_union_actual_requires_every_member() -> None:
    """A union is assignable only if all alternatives are assignable."""
    actual: TypeShape = _shape(
        name="union",
        args=(_shape(name="int"), _shape(name="bool")),
    )
    expect_is(
        actual=subtype(
            actual=actual,
            expected=_shape(name="float"),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(actual=actual, expected=_shape(name="int")).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(actual=actual, expected=_shape(name="str")).compatible,
        expected=False,
    )


def test_union_expected_accepts_one_member() -> None:
    """At least one compatible destination alternative is sufficient."""
    target: TypeShape = _shape(
        name="union",
        args=(_shape(name="str"), _shape(name="float")),
    )
    expect_is(
        actual=subtype(actual=_shape(name="int"), expected=target).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="bytes"),
            expected=target,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="Unknown"),
            expected=target,
        ).compatible,
        expected=None,
    )


def test_annotated_wrappers_and_nested_generic_covariance() -> None:
    """Ignore non-runtime metadata without discarding source type meaning."""
    actual: TypeShape = _shape(
        name="Annotated",
        args=(_shape(name="int"), _shape(name="'meta'")),
    )
    expected: TypeShape = _shape(name="Final", args=(_shape(name="float"),))
    expect_is(
        actual=subtype(actual=actual, expected=expected).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="int"),
            expected=_shape(name="NotRequired", args=(_shape(name="int"),)),
        ).compatible,
        expected=True,
    )


def test_mapping_value_covariance_but_key_invariance() -> None:
    """Mapping values covary; key types do not."""
    actual: TypeShape = _shape(
        name="dict",
        args=(_shape(name="str"), _shape(name="int")),
    )
    covariant: TypeShape = _shape(
        name="Mapping",
        args=(_shape(name="str"), _shape(name="float")),
    )
    invariant: TypeShape = _shape(
        name="Mapping",
        args=(_shape(name="object"), _shape(name="int")),
    )
    expect_is(
        actual=subtype(actual=actual, expected=covariant).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(actual=actual, expected=invariant).compatible,
        expected=False,
    )


def test_invariant_lists_reject_numeric_element_promotion() -> None:
    """Mutable generic containers stay invariant even with numeric subtypes."""
    left: TypeShape = _shape(name="list", args=(_shape(name="int"),))
    right: TypeShape = _shape(name="list", args=(_shape(name="float"),))
    expect_is(
        actual=subtype(actual=left, expected=right).compatible,
        expected=False,
    )


def test_malformed_generic_arity_is_unknown() -> None:
    """Inconsistent generic arity cannot be pronounced compatible."""
    actual: TypeShape = _shape(name="dict", args=(_shape(name="str"),))
    target: TypeShape = _shape(
        name="Mapping",
        args=(_shape(name="str"), _shape(name="int")),
    )
    expect_is(
        actual=subtype(actual=actual, expected=target).compatible,
        expected=None,
    )


def test_callable_variance_of_parameters_and_result() -> None:
    """Callables have contravariant parameters and covariant results."""
    superset: TypeShape = _shape(
        name="Callable",
        args=(
            _shape(name="parameters", args=(_shape(name="float"),)),
            _shape(name="bool"),
        ),
    )
    subset: TypeShape = _shape(
        name="Callable",
        args=(
            _shape(name="parameters", args=(_shape(name="int"),)),
            _shape(name="int"),
        ),
    )
    expect_is(
        actual=subtype(actual=superset, expected=subset).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(actual=subset, expected=superset).compatible,
        expected=False,
    )


def test_nominal_inheritance_transitivity() -> None:
    """Resolve a local nominal subtype through several source parents."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source=(
                """\
class A: pass
class B(A): pass
class C(B): pass
class D: pass"""
            ),
        ),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="C"),
            expected=_shape(name="A"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="C"),
            expected=_shape(name="D"),
            index=index,
        ).compatible,
        expected=False,
    )


def test_known_protocol_missing_field_and_wrong_field() -> None:
    """Distinguish structural absence from a present but incompatible field."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from typing import Protocol
class P(Protocol):
    name: str
class X: pass
class Y:
    name: int
class Z:
    name: str
""",
        ),
    )
    expect_is(
        actual=protocol_compatible(
            actual=_shape(name="X"),
            protocol=index.classes["P"],
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=protocol_compatible(
            actual=_shape(name="Y"),
            protocol=index.classes["P"],
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=protocol_compatible(
            actual=_shape(name="Z"),
            protocol=index.classes["P"],
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=protocol_compatible(
            actual=_shape(name="External"),
            protocol=index.classes["P"],
            index=index,
        ).compatible,
        expected=None,
    )


def test_protocol_method_requires_call_compatibility() -> None:
    """Matching method names are insufficient when signatures disagree."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from typing import Protocol
class P(Protocol):
    def convert(self, count: int) -> str: ...
class A:
    def convert(self, count: int) -> str: ...
class B:
    def convert(self, count: str) -> str: ...
class C:
    def other(self, count: int) -> str: ...
""",
        ),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="A"),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="B"),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="C"),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=False,
    )


def test_method_compatibility_parameter_narrowing_and_return_covariance() -> (
    None
):
    """Override shape checks cover required keywords and return covariance."""
    module: Module = expect_instance(
        value=parse(
            source="""
class Base:
    def f(self, x: int = 1) -> int: ...
class Derived(Base):
    def f(self, x: float = 1.0) -> bool: ...
""",
        ),
        kind=Module,
    )
    index: ContractIndex = ContractIndex(root=module)
    original: CallableContract = index.variants(qualified_name="Base.f")[0]
    rewritten: CallableContract = index.variants(qualified_name="Derived.f")[0]
    expect_is(
        actual=method_compatible(
            implementation=rewritten,
            inherited=original,
            index=index,
        ).compatible,
        expected=True,
    )


def test_recursive_type_substitution_and_unification() -> None:
    """Type parameters propagate through nested containers predictably."""
    declared: TypeShape = _shape(name="list", args=(_shape(name="T"),))
    provided: TypeShape = _shape(name="list", args=(_shape(name="int"),))
    mapping: dict[str, TypeShape] = {}
    expect_true(
        condition=unify(
            declared=declared,
            actual=provided,
            parameters=frozenset({"T"}),
            bindings=mapping,
        ),
    )
    expect_equal(
        actual=specialize(declared=declared, bindings=mapping),
        expected=provided,
    )
    expect_false(
        condition=unify(
            declared=_shape(name="dict"),
            actual=_shape(name="list"),
            parameters=frozenset({"T"}),
            bindings=mapping,
        ),
    )


def test_unknown_implementation_method_return_unresolved() -> None:
    """Return an uncertainty marker when an implementation cannot be proved."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class Base:
    def f(self, x: int) -> int: ...
class Child(Base):
    def f(self, x: int) -> External: ...
""",
        ),
    )
    base: CallableContract = index.variants(qualified_name="Base.f")[0]
    child: CallableContract = index.variants(qualified_name="Child.f")[0]
    expect_is(
        actual=method_compatible(
            implementation=child,
            inherited=base,
            index=index,
        ).compatible,
        expected=None,
    )


@pytest.mark.parametrize(
    ("implementation", "abstraction"),
    [
        ("deque", "MutableSequence"),
        ("defaultdict", "MutableMapping"),
        ("OrderedDict", "Mapping"),
        ("Counter", "Mapping"),
        ("ChainMap", "Mapping"),
        ("UserDict", "MutableMapping"),
        ("UserList", "Sequence"),
        ("UserString", "Sequence"),
        ("bytearray", "Buffer"),
        ("memoryview", "Buffer"),
        ("KeysView", "Set"),
        ("ValuesView", "Collection"),
        ("ItemsView", "MappingView"),
        ("AsyncGenerator", "AsyncIterable"),
        ("Coroutine", "Awaitable"),
    ],
)
def test_additional_collection_abc_relationships(
    *,
    implementation: str,
    abstraction: str,
) -> None:
    """Provide standard ABC mappings without importing analyzed code.

    Args:
        abstraction (str): Abstraction supplied as str for this operation.
        implementation (str): Implementation supplied as str for this
            operation.

    """
    expect_is(
        actual=subtype(
            actual=_shape(name=implementation),
            expected=_shape(name=abstraction),
        ).compatible,
        expected=True,
    )


def test_string_sequence_element_projection() -> None:
    """String iteration yields str and bytes iteration yields integers."""
    expect_is(
        actual=subtype(
            actual=_shape(name="str"),
            expected=_shape(name="Sequence", args=(_shape(name="str"),)),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="bytes"),
            expected=_shape(name="Iterable", args=(_shape(name="int"),)),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="range"),
            expected=_shape(name="Sequence", args=(_shape(name="int"),)),
        ).compatible,
        expected=True,
    )


def _literal(*members: str) -> TypeShape:
    """Build a ``Literal[...]`` shape from member source texts.

    Args:
        members (str): Literal member spellings, e.g. ``"'a'"`` or ``"1"``.

    Returns:
        TypeShape: The literal type shape.

    """
    return TypeShape(
        name="Literal",
        arguments=tuple(TypeShape(name=member) for member in members),
    )


@pytest.mark.parametrize(
    ("actual", "expected", "verdict"),
    [
        (_literal("'a'"), _literal("'a'", "'b'"), True),
        (_literal("'a'", "'c'"), _literal("'a'", "'b'"), False),
        (_literal("'a'"), _shape(name="str"), True),
        (_literal("1"), _shape(name="str"), False),
        (_literal("'a'"), _shape(name="LiteralString"), True),
        (_literal("1"), _shape(name="LiteralString"), False),
        (_shape(name="str"), _literal("'a'"), False),
        (_shape(name="Unknown"), _literal("'a'"), None),
        (_shape(name="Any"), _literal("'a'"), None),
        (_shape(name="LiteralString"), _shape(name="str"), True),
        (_shape(name="LiteralString"), _shape(name="int"), False),
        (_shape(name="str"), _shape(name="LiteralString"), False),
        (_shape(name="Unknown"), _shape(name="LiteralString"), None),
        (_shape(name="Literal"), _shape(name="str"), None),
        (_literal("'a'", "Weird.member"), _shape(name="str"), None),
    ],
)
def test_literal_relations(
    *,
    actual: TypeShape,
    expected: TypeShape,
    verdict: bool | None,
) -> None:
    """PEP 586 literals compare by value set, never by truthiness.

    Args:
        actual (TypeShape): Source shape.
        expected (TypeShape): Target shape.
        verdict (bool | None): Expected compatibility verdict.

    """
    expect_is(
        actual=subtype(actual=actual, expected=expected).compatible,
        expected=verdict,
    )


def test_enum_member_literals_use_their_owner() -> None:
    """Enum members satisfy their enum and ``object``, not other nominals."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from enum import Enum
class Color(Enum):
    RED = 1
""",
        ),
    )
    member: TypeShape = _literal("Color.RED")
    expect_is(
        actual=subtype(
            actual=member,
            expected=_shape(name="Color"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=member,
            expected=_shape(name="int"),
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=member,
            expected=_shape(name="object"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=member,
            expected=_shape(name="Color"),
        ).compatible,
        expected=None,
    )


def test_union_edges_and_alias_normalization() -> None:
    """All-true unions, unknown alternatives and dotted aliases resolve."""
    union_int_bool: TypeShape = _shape(
        name="union",
        args=(_shape(name="int"), _shape(name="bool")),
    )
    expect_is(
        actual=subtype(
            actual=union_int_bool,
            expected=_shape(name="float"),
        ).compatible,
        expected=True,
    )
    unknown_tail: TypeShape = _shape(
        name="union",
        args=(_shape(name="str"), _shape(name="Unknown")),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="int"),
            expected=unknown_tail,
        ).compatible,
        expected=None,
    )
    expect_is(
        actual=subtype(
            actual=TypeShape(
                name="typing.List",
                arguments=(_shape(name="int"),),
            ),
            expected=_shape(
                name="collections.abc.Sequence",
                args=(_shape(name="int"),),
            ),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=TypeShape(
                name="dict",
                arguments=(_shape(name="str"), _shape(name="int")),
            ),
            expected=_shape(name="Iterable", args=(_shape(name="str"),)),
        ).compatible,
        expected=True,
    )


def test_callable_parameter_and_result_edges() -> None:
    """Callable mismatches cover arity, unknown results and verdicts."""
    parameters_int: TypeShape = _shape(
        name="parameters",
        args=(_shape(name="int"),),
    )
    parameters_two: TypeShape = _shape(
        name="parameters",
        args=(_shape(name="int"), _shape(name="int")),
    )
    mismatched_arity: TypeShape = TypeShape(
        name="Callable",
        arguments=(parameters_int, _shape(name="int")),
    )
    other_arity: TypeShape = TypeShape(
        name="Callable",
        arguments=(parameters_two, _shape(name="int")),
    )
    expect_is(
        actual=subtype(
            actual=mismatched_arity,
            expected=other_arity,
        ).compatible,
        expected=None,
    )
    unknown_result: TypeShape = TypeShape(
        name="Callable",
        arguments=(
            _shape(name="parameters", args=()),
            _shape(name="Unknown"),
        ),
    )
    int_result: TypeShape = TypeShape(
        name="Callable",
        arguments=(
            _shape(name="parameters", args=()),
            _shape(name="int"),
        ),
    )
    expect_is(
        actual=subtype(actual=unknown_result, expected=int_result).compatible,
        expected=None,
    )
    expect_is(
        actual=subtype(
            actual=_shape(
                name="Sequence",
                args=(_shape(name="int"),),
            ),
            expected=_shape(name="Sequence", args=(_shape(name="str"),)),
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=_shape(
                name="Sequence",
                args=(_shape(name="Unknown"),),
            ),
            expected=_shape(name="Sequence", args=(_shape(name="int"),)),
        ).compatible,
        expected=None,
    )


def test_declared_inheritance_diamond_and_external_bases() -> None:
    """Diamond bases revisit nodes; external bases stay unresolved."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
class E(ExternalBase): pass
class Unrelated: pass
""",
        ),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="D"),
            expected=_shape(name="A"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="D"),
            expected=_shape(name="B"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="D"),
            expected=_shape(name="Unrelated"),
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="E"),
            expected=_shape(name="A"),
            index=index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="D"),
            expected=_shape(name="Missing"),
            index=index,
        ).compatible,
        expected=None,
    )


def test_protocol_property_satisfies_field() -> None:
    """A read-only property getter satisfies a protocol field."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from typing import Protocol
class P(Protocol):
    name: str
class Z:
    @property
    def name(self) -> str: ...
""",
        ),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="Z"),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="P"),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=True,
    )


def test_protocol_diamond_inheritance_visited_once() -> None:
    """Shared protocol bases are collected without duplicates."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from typing import Protocol
class Base(Protocol):
    tag: int
class Left(Base, Protocol): pass
class Right(Base, Protocol): pass
class Both(Left, Right, Protocol): pass
class Impl:
    tag: int
""",
        ),
    )
    expect_is(
        actual=subtype(
            actual=_shape(name="Impl"),
            expected=_shape(name="Both"),
            index=index,
        ).compatible,
        expected=True,
    )


def test_method_override_parameter_violations() -> None:
    """Kind changes, renames, dropped defaults and narrowing fail."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class Base:
    def a(self, x: float) -> int: ...
    def b(self, x: int = 1) -> int: ...
    def c(self, x: int) -> int: ...
    def d(self, x: int) -> int: ...
class KindChange(Base):
    def a(self, *, x: float) -> int: ...
class Renamed(Base):
    def c(self, y: int) -> int: ...
class DroppedDefault(Base):
    def b(self, x: int) -> int: ...
class Narrowed(Base):
    def d(self, x: int) -> int: ...
""",
        ),
    )
    base_a: CallableContract = index.variants(qualified_name="Base.a")[0]
    impl_a: CallableContract = index.variants(qualified_name="KindChange.a")[0]
    expect_is(
        actual=method_compatible(
            implementation=impl_a,
            inherited=base_a,
            index=index,
        ).compatible,
        expected=False,
    )
    base_c: CallableContract = index.variants(qualified_name="Base.c")[0]
    impl_c: CallableContract = index.variants(qualified_name="Renamed.c")[0]
    expect_is(
        actual=method_compatible(
            implementation=impl_c,
            inherited=base_c,
            index=index,
        ).compatible,
        expected=False,
    )
    base_b: CallableContract = index.variants(qualified_name="Base.b")[0]
    impl_b: CallableContract = index.variants(
        qualified_name="DroppedDefault.b",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=impl_b,
            inherited=base_b,
            index=index,
        ).compatible,
        expected=False,
    )
    base_d: CallableContract = index.variants(qualified_name="Base.d")[0]
    impl_d: CallableContract = index.variants(qualified_name="Narrowed.d")[0]
    narrowed_index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class Base2:
    def d(self, x: str) -> int: ...
class Narrowed2(Base2):
    def d(self, x: int) -> int: ...
""",
        ),
    )
    base2: CallableContract = narrowed_index.variants(
        qualified_name="Base2.d",
    )[0]
    impl2: CallableContract = narrowed_index.variants(
        qualified_name="Narrowed2.d",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=impl2,
            inherited=base2,
            index=narrowed_index,
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=method_compatible(
            implementation=impl_d,
            inherited=base_d,
            index=index,
        ).compatible,
        expected=True,
    )


def test_method_kind_and_arity_mismatch() -> None:
    """Static-vs-instance binding and parameter counts are incompatible."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class Base:
    def f(self, x: int) -> int: ...
class StaticImpl(Base):
    @staticmethod
    def f(x: int) -> int: ...
class FewerParams(Base):
    def f(self) -> int: ...
class NoReturn(Base):
    def f(self, x: int): ...
class StaticBase:
    @staticmethod
    def g(x: int) -> int: ...
class StaticPair(StaticBase):
    @staticmethod
    def g(x: int) -> int: ...
""",
        ),
    )
    base_f: CallableContract = index.variants(qualified_name="Base.f")[0]
    static_f: CallableContract = index.variants(
        qualified_name="StaticImpl.f",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=static_f,
            inherited=base_f,
            index=index,
        ).compatible,
        expected=False,
    )
    fewer_f: CallableContract = index.variants(
        qualified_name="FewerParams.f",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=fewer_f,
            inherited=base_f,
            index=index,
        ).compatible,
        expected=False,
    )
    no_return_f: CallableContract = index.variants(
        qualified_name="NoReturn.f",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=no_return_f,
            inherited=base_f,
            index=index,
        ).compatible,
        expected=True,
    )
    static_base: CallableContract = index.variants(
        qualified_name="StaticBase.g",
    )[0]
    static_pair: CallableContract = index.variants(
        qualified_name="StaticPair.g",
    )[0]
    expect_is(
        actual=method_compatible(
            implementation=static_pair,
            inherited=static_base,
            index=index,
        ).compatible,
        expected=True,
    )


def test_unify_rebinds_parameters_with_joined_types() -> None:
    """Repeated unification of one parameter joins the bindings."""
    bindings: dict[str, TypeShape] = {}
    parameters: frozenset[str] = frozenset({"T"})
    declared: TypeShape = _shape(name="T")
    expect_true(
        condition=unify(
            declared=declared,
            actual=_shape(name="int"),
            parameters=parameters,
            bindings=bindings,
        ),
    )
    expect_true(
        condition=unify(
            declared=declared,
            actual=_shape(name="bool"),
            parameters=parameters,
            bindings=bindings,
        ),
    )
    expect_equal(
        actual=bindings["T"],
        expected=join_types(
            left=_shape(name="int"),
            right=_shape(name="bool"),
            promote=False,
        ),
    )
    expect_false(
        condition=unify(
            declared=_shape(name="list", args=(_shape(name="T"),)),
            actual=_shape(
                name="dict",
                args=(_shape(name="str"), _shape(name="int")),
            ),
            parameters=parameters,
            bindings=bindings,
        ),
    )


def test_unparseable_literal_members_stay_unresolved() -> None:
    """Literal members that are not syntax literals never guess."""
    expect_is(
        actual=subtype(
            actual=_literal("'a'", "??"),
            expected=_literal("'a'", "'b'"),
        ).compatible,
        expected=None,
    )
    expect_is(
        actual=subtype(
            actual=_literal("'a'"),
            expected=_literal("'a'", "??"),
        ).compatible,
        expected=None,
    )
    expect_is(
        actual=subtype(
            actual=_shape(
                name="union",
                args=(_shape(name="int"), _shape(name="Unknown")),
            ),
            expected=_shape(name="float"),
        ).compatible,
        expected=None,
    )


def test_same_protocol_with_different_arguments() -> None:
    """A generic spelling of the protocol still matches itself."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
from typing import Protocol
class P(Protocol):
    name: str
""",
        ),
    )
    expect_is(
        actual=subtype(
            actual=TypeShape(name="P", arguments=(_shape(name="int"),)),
            expected=_shape(name="P"),
            index=index,
        ).compatible,
        expected=True,
    )


def test_unannotated_override_parameters_are_skipped() -> None:
    """Missing annotations on either side defer the parameter check."""
    index: ContractIndex = ContractIndex(
        root=parse(
            source="""
class Base:
    def f(self, x) -> int: ...
class Impl(Base):
    def f(self, x: int) -> int: ...
""",
        ),
    )
    base_f: CallableContract = index.variants(qualified_name="Base.f")[0]
    impl_f: CallableContract = index.variants(qualified_name="Impl.f")[0]
    expect_is(
        actual=method_compatible(
            implementation=impl_f,
            inherited=base_f,
            index=index,
        ).compatible,
        expected=True,
    )
