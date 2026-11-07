"""Python typing specification refinements for the unified semantic engine."""

from __future__ import annotations

from ast import parse

import pytest
from astart.semantic import ContractIndex, TypeShape, subtype

from tests.expectations import expect_in, expect_is


def shape(*, name: str, args: tuple[TypeShape, ...] = ()) -> TypeShape:
    """Build a precise immutable shape for a subtype test.

    Args:
        args: Collection of args supplied for this operation.
        name: Identifier of the name being resolved.

    Returns:
        TypeShape produced by this operation.

    """
    return TypeShape(name=name, arguments=args)


@pytest.mark.parametrize(
    ("actual", "expected", "compatible"),
    [
        ("'hello'", "str", True),
        ("1", "int", True),
        ("True", "bool", True),
        ("True", "int", True),
        ("'hello'", "int", False),
        ("None", "None", True),
    ],
)
def test_literal_values_use_their_nominal_types(
    *,
    actual: str,
    expected: str,
    compatible: bool,
) -> None:
    """Compare real constant types rather than matching string spelling.

    Args:
        actual: Actual supplied as str for this operation.
        compatible: Compatible supplied as bool for this operation.
        expected: Expected supplied as str for this operation.

    """
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name=actual),)),
            expected=shape(name=expected),
        ).compatible,
        expected=compatible,
    )


def test_bool_literal_is_not_equal_to_integer_one() -> None:
    """PEP 586 literal equality distinguishes true and the integer one."""
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name="True"),)),
            expected=shape(name="Literal", args=(shape(name="1"),)),
        ).compatible,
        expected=False,
    )


def test_literal_subsets_and_nominal_to_literal() -> None:
    """An unrestricted int cannot satisfy a literal with one exact value."""
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name="1"),)),
            expected=shape(
                name="Literal",
                args=(shape(name="1"), shape(name="2")),
            ),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="int"),
            expected=shape(name="Literal", args=(shape(name="1"),)),
        ).compatible,
        expected=False,
    )


def test_literal_string_specificity() -> None:
    """Arbitrary str values cannot be inferred to originate from literals."""
    expect_is(
        actual=subtype(
            actual=shape(name="LiteralString"),
            expected=shape(name="str"),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="str"),
            expected=shape(name="LiteralString"),
        ).compatible,
        expected=False,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name="'x'"),)),
            expected=shape(name="LiteralString"),
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name="1"),)),
            expected=shape(name="LiteralString"),
        ).compatible,
        expected=False,
    )


def test_unsupported_literal_member_stays_unknown() -> None:
    """Never infer a scalar type from unrecognized source expressions."""
    expect_is(
        actual=subtype(
            actual=shape(name="Literal", args=(shape(name="external.VALUE"),)),
            expected=shape(name="int"),
        ).compatible,
        expected=None,
    )


def test_inherited_protocol_fields_and_methods() -> None:
    """Both protocol and implementation inheritance contribute contracts."""
    source: str = """
from typing import Protocol
class Base(Protocol):
    title: str
    def read(self, index: int) -> str: ...
class Combined(Base, Protocol):
    count: int
class ImplBase:
    title: str
    def read(self, index: int) -> str: ...
class Impl(ImplBase):
    count: int
class Missing:
    count: int
"""
    index: ContractIndex = ContractIndex(root=parse(source=source))
    expect_is(
        actual=subtype(
            actual=shape(name="Impl"),
            expected=shape(name="Combined"),
            index=index,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="Missing"),
            expected=shape(name="Combined"),
            index=index,
        ).compatible,
        expected=False,
    )


def test_property_satisfies_protocol_data_member() -> None:
    """An annotated property provides a read-only protocol field type."""
    source: str = """
from typing import Protocol
class P(Protocol):
    value: int
class C:
    @property
    def value(self) -> int:
        return 3
"""
    index: ContractIndex = ContractIndex(root=parse(source=source))
    expect_is(
        actual=subtype(
            actual=shape(name="C"),
            expected=shape(name="P"),
            index=index,
        ).compatible,
        expected=True,
    )


def test_final_class_and_final_method_diagnostics() -> None:
    """Recognize final-decorator inheritance bans without executing code."""
    source: str = """
from typing import final
@final
class Closed: pass
class Child(Closed): pass
class Base:
    @final
    def f(self, x: int) -> int: ...
class Derived(Base):
    def f(self, x: int) -> int: ...
"""
    index: ContractIndex = ContractIndex(root=parse(source=source))
    codes: set[str] = {item.code for item in index.diagnostics}
    expect_in(item="final_class_inherited", container=codes)
    expect_in(item="final_method_overridden", container=codes)


def test_static_cannot_override_instance_binding() -> None:
    """Different descriptors do not have an interchangeable call contract."""
    source: str = """
class Base:
    def f(self, x: int) -> int: ...
class Derived(Base):
    @staticmethod
    def f(x: int) -> int: ...
"""
    index: ContractIndex = ContractIndex(root=parse(source=source))
    expect_in(
        item="override_incompatible",
        container={item.code for item in index.diagnostics},
    )


def test_union_of_identical_literals_preserves_exact_membership() -> None:
    """Union dispatch must precede nominal-to-literal non-assignability."""
    exact: TypeShape = shape(name="Literal", args=(shape(name="1"),))
    expect_is(
        actual=subtype(
            actual=shape(name="union", args=(exact, exact)),
            expected=exact,
        ).compatible,
        expected=True,
    )
    expect_is(
        actual=subtype(
            actual=shape(name="union", args=(exact, shape(name="int"))),
            expected=exact,
        ).compatible,
        expected=False,
    )
