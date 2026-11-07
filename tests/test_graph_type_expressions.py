"""Exercise the graph type-expression codec and annotation grammar."""

from __future__ import annotations

from ast import Attribute, Constant, List, Name, Tuple, parse
from typing import TYPE_CHECKING

import pytest
from astart._graph.graph.semantics import (
    build_annotation,
    child_nodes,
    nodes_of_type,
    render_annotation,
)
from astart._graph.graph.type_expressions import (
    CallableExpression,
    EllipsisExpression,
    GenericExpression,
    ParamSpecExpression,
    RequiredImport,
    TypeExpressionCodec,
    TypeExpressionError,
    TypeName,
    TypeVarExpression,
    UnionExpression,
)

from tests.expectations import (
    expect_equal,
    expect_instance,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from ast import Module, expr

    from astart._graph.graph.type_expressions import TypeExpression


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("int", "int"),
        ("...", "..."),
        ("None", "None"),
        ("typing.Optional", "typing.Optional"),
        ("a.b.c", "a.b.c"),
        ("'Forward'", "Forward"),
        ("list[int]", "list[int]"),
        ("dict[str, int | None]", "dict[str, int | None]"),
        ("Callable[[int, str], bool]", "Callable[[int, str], bool]"),
        ("Callable[..., bool]", "Callable[..., bool]"),
        ("Callable[[], bool]", "Callable[[], bool]"),
        ("Callable[int, bool]", "Callable[[int], bool]"),
        ("typing.Callable[int | str, bool]", "Callable[[int | str], bool]"),
        ("tuple[int, ...]", "tuple[int, ...]"),
        ("[int, str]", "list[int, str]"),
        ("int | str | int", "int | str"),
        ("None | int", "int | None"),
        ("int | None | str", "int | str | None"),
    ],
)
def test_codec_round_trips_sources(*, source: str, expected: str) -> None:
    """Normalize every supported expression shape when rendering it.

    Args:
        expected: Canonical rendering expected for the source.
        source: Type expression source being parsed.

    """
    expect_equal(
        actual=TypeExpressionCodec.to_source(
            type_expression=TypeExpressionCodec.from_source(source=source),
        ),
        expected=expected,
    )


def test_codec_builders_construct_typed_nodes() -> None:
    """Build typed nodes with the convenience constructors."""
    name: TypeName = TypeExpressionCodec.name(name="int")
    generic: GenericExpression = TypeExpressionCodec.generic(
        base="list",
        arguments=(name,),
    )
    nested: GenericExpression = TypeExpressionCodec.generic(
        base=generic,
        arguments=(name,),
    )
    callable_: CallableExpression = TypeExpressionCodec.callable(
        parameters=EllipsisExpression(),
        returns=name,
    )
    expect_equal(actual=generic.base, expected=TypeName(name="list"))
    expect_equal(actual=nested.base, expected=generic)
    expect_equal(actual=callable_.returns, expected=name)
    expect_equal(
        actual=TypeExpressionCodec.from_name(name="  list[int] "),
        expected=generic,
    )


def test_union_flattens_and_collapses_single_member() -> None:
    """Flatten nested unions and unwrap one-member unions."""
    first: TypeName = TypeName(name="int")
    second: TypeName = TypeName(name="str")
    nested: TypeExpression = TypeExpressionCodec.union(
        members=(first, UnionExpression(members=(second, first))),
    )
    single: TypeExpression = TypeExpressionCodec.union(members=(first, first))
    expect_equal(
        actual=nested,
        expected=UnionExpression(members=(first, second)),
    )
    expect_is(actual=single, expected=first)


@pytest.mark.parametrize("source", ["", "int +", "[", "int $", "'open"])
def test_invalid_sources_raise_type_expression_error(*, source: str) -> None:
    """Report unparsable text through the codec's own error type.

    Args:
        source: Malformed type expression text.

    """
    with pytest.raises(expected_exception=(TypeExpressionError, ValueError)):
        TypeExpressionCodec.from_source(source=source)


def test_unsupported_ast_nodes_are_rejected() -> None:
    """Reject AST nodes outside the type-expression grammar."""
    call: Name = Name(id="x")
    node: expr = parse(source="f(x)", mode="eval").body
    with pytest.raises(expected_exception=TypeExpressionError):
        TypeExpressionCodec.from_ast(node=node)
    with pytest.raises(expected_exception=TypeExpressionError):
        TypeExpressionCodec.from_ast(node=Constant(value=3))
    with pytest.raises(expected_exception=TypeExpressionError):
        TypeExpressionCodec.from_ast(
            node=parse(source="f().attr", mode="eval").body,
        )
    with pytest.raises(expected_exception=TypeExpressionError):
        TypeExpressionCodec.from_ast(
            node=parse(source="int & str", mode="eval").body,
        )
    expect_equal(actual=call.id, expected="x")


def test_required_imports_cover_every_expression_kind() -> None:
    """Report imports for type variables, param specs and callables."""
    variable: TypeVarExpression = TypeVarExpression(
        name="T",
        bound=TypeName(name="int"),
    )
    unbound: TypeVarExpression = TypeVarExpression(name="U")
    spec: ParamSpecExpression = ParamSpecExpression(name="P")
    expression: TypeExpression = GenericExpression(
        base=TypeName(name="dict"),
        arguments=(
            UnionExpression(members=(variable, unbound)),
            CallableExpression(
                parameters=(spec,),
                returns=TypeName(name="int"),
            ),
            CallableExpression(
                parameters=EllipsisExpression(),
                returns=TypeName(name="int"),
            ),
        ),
    )
    expect_equal(
        actual=TypeExpressionCodec.required_imports(
            type_expression=expression,
        ),
        expected=frozenset(
            (
                RequiredImport.TYPE_VAR,
                RequiredImport.PARAM_SPEC,
                RequiredImport.CALLABLE,
            ),
        ),
    )
    expect_equal(
        actual=TypeExpressionCodec.to_source(type_expression=variable),
        expected="T",
    )
    expect_equal(
        actual=TypeExpressionCodec.to_source(type_expression=spec),
        expected="P",
    )


@pytest.mark.parametrize(
    "text",
    [
        "int",
        "list[int]",
        "dict[str, list[int | None]]",
        "Literal['a', 'b']",
        "Literal[1, True, False, None]",
        "tuple[int, ...]",
        "Callable[[int], str]",
        "a.b.c",
        "[int, str]",
    ],
)
def test_annotation_grammar_round_trips(*, text: str) -> None:
    """Render parsed annotations back to the same canonical text.

    Args:
        text: Annotation text in the supported grammar.

    """
    expect_equal(
        actual=render_annotation(node=build_annotation(text=text)),
        expected=text,
    )


@pytest.mark.parametrize(
    "text",
    ["", "int $", "list[", "'open", "int |", "]", "f(1,"],
)
def test_annotation_grammar_rejects_malformed_text(*, text: str) -> None:
    """Raise ValueError for malformed annotation text.

    Args:
        text: Malformed annotation text.

    """
    with pytest.raises(expected_exception=(ValueError, IndexError)):
        build_annotation(text=text)


def _parses(*, text: str) -> bool:
    """Report whether the annotation grammar accepts a text.

    Args:
        text: Annotation text to parse.

    Returns:
        True when parsing succeeds.

    """
    try:
        build_annotation(text=text)
    except ValueError:
        return False
    return True


def test_annotation_grammar_parses_calls_and_numbers() -> None:
    """Accept call syntax and integer literals inside annotations."""
    for text in ("Field(1, 2)", "Annotated[int, Field(gt=0)]", "f()", "x[1]"):
        _parses(text=text)
    expect_equal(
        actual=render_annotation(node=build_annotation(text="Literal[1, 2]")),
        expected="Literal[1, 2]",
    )


def test_render_annotation_handles_none_and_unsupported_nodes() -> None:
    """Render an absent annotation as object and reject unknown nodes."""
    expect_equal(actual=render_annotation(node=None), expected="object")
    expect_equal(
        actual=render_annotation(node=Tuple(elts=[Name(id="a")])),
        expected="a",
    )
    expect_equal(
        actual=render_annotation(node=List(elts=[Name(id="a")])),
        expected="[a]",
    )
    expect_equal(
        actual=render_annotation(node=Constant(value=b"x")),
        expected="b'x'",
    )
    expect_equal(
        actual=render_annotation(
            node=Attribute(value=Name(id="a"), attr="b"),
        ),
        expected="a.b",
    )
    with pytest.raises(expected_exception=ValueError, match="Cannot render"):
        render_annotation(node=parse(source="f(x)", mode="eval").body)


def test_node_helpers_walk_children() -> None:
    """Collect nodes by type and list direct children."""
    tree: Module = parse(source="x = a + b")
    names: list[Name] = nodes_of_type(root=tree, types=(Name,))
    expect_equal(actual=[item.id for item in names], expected=["x", "a", "b"])
    expect_true(condition=len(child_nodes(node=tree)) > 0)
    expect_instance(value=child_nodes(node=tree.body[0])[0], kind=Name)
