"""Direct, conservative generic/ABC/protocol compatibility regressions."""

from __future__ import annotations

from ast import Module, parse
from typing import TYPE_CHECKING

import pytest
from astart.semantic import (
    ContractIndex,
    TypeShape,
    method_compatible,
    protocol_compatible,
    specialize,
    subtype,
    unify,
)

from tests.expectations import (
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
        args: Collection of args supplied for this operation.
        name: Identifier of the name being resolved.

    Returns:
        TypeShape produced by this operation.

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
        expected: Expected supplied as bool | None for this operation.
        source: The source examined while never infer subtype evidence
            through unrelated builtin types.
        target: The target examined while never infer subtype evidence
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
        abstraction: Abstraction supplied as str for this operation.
        implementation: Implementation supplied as str for this operation.

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
