"""Add and remove annotations while preserving the surrounding source."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    FunctionDef,
    Lambda,
    Load,
    Name,
    arg,
    parse,
    walk,
)
from textwrap import dedent

import pytest
from astart.ast import CommentedModule
from astart.formatting import FormatPreservationError

from tests.expectations import expect_equal, expect_in, expect_not_none


def _annotation(*, name: str) -> Name:
    """Build a simple annotation expression.

    Args:
        name: Identifier of the annotation.

    Returns:
        A loaded name node.

    """
    return Name(id=name, ctx=Load())


def _tree(*, source: str) -> CommentedModule:
    """Parse a dedented snippet into a mutable module.

    Args:
        source: Python source.

    Returns:
        The parsed module.

    """
    return CommentedModule.parse(source=dedent(text=source))


def _function(
    *,
    tree: CommentedModule,
    index: int = 0,
) -> FunctionDef | AsyncFunctionDef:
    """Return the n-th function definition.

    Args:
        tree: Module to search.
        index: Zero-based match index.

    Returns:
        The function node.

    Raises:
        TypeError: If the matched node is not a function definition.

    """
    matches: list[AST] = [
        node
        for node in walk(node=tree)
        if isinstance(node, (FunctionDef, AsyncFunctionDef))
    ]
    found: AST = matches[index]
    match found:
        case FunctionDef() | AsyncFunctionDef():
            return found
        case _:
            msg: str = f"expected a function definition, got {found!r}"
            raise TypeError(msg)


def _render(*, tree: CommentedModule) -> str:
    """Render with strict format preservation and check it still parses.

    Args:
        tree: Edited module.

    Returns:
        The regenerated source.

    """
    text: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="raise",
    )
    parse(source=text)
    return text


def test_return_annotation_is_inserted_in_place() -> None:
    """Add ``-> int`` without touching comments or neighbours."""
    tree: CommentedModule = _tree(
        source="""\
        # lead
        def f(a, b):  # trailing
            return a


        x = 1
        """,
    )
    _function(tree=tree).returns = _annotation(name="int")
    expect_equal(
        actual=_render(tree=tree),
        expected=dedent(
            text="""\
            # lead
            def f(a, b) -> int:  # trailing
                return a


            x = 1
            """,
        ),
    )


def test_return_annotation_with_decorator_type_params_and_multiline() -> None:
    """Find the real closing parenthesis of a complex header."""
    tree: CommentedModule = _tree(
        source="""\
        @deco(1)
        async def f[T: (int, str)](
            a,  # first
            b,
        ):
            return a
        """,
    )
    _function(tree=tree).returns = _annotation(name="int")
    expect_equal(
        actual=_render(tree=tree),
        expected=dedent(
            text="""\
            @deco(1)
            async def f[T: (int, str)](
                a,  # first
                b,
            ) -> int:
                return a
            """,
        ),
    )


def test_return_annotation_is_removed_and_replaced() -> None:
    """Remove and change an existing return annotation."""
    removed: CommentedModule = _tree(
        source="""\
def f(a) -> int:  # c
    return a
""",
    )
    _function(tree=removed).returns = None
    expect_equal(
        actual=_render(tree=removed),
        expected="""\
def f(a):  # c
    return a
""",
    )
    changed: CommentedModule = _tree(
        source="""\
def f(a) -> int:
    return a
""",
    )
    _function(tree=changed).returns = _annotation(name="str")
    expect_equal(
        actual=_render(tree=changed),
        expected="""\
def f(a) -> str:
    return a
""",
    )


def test_parameter_annotations_cover_every_parameter_kind() -> None:
    """Annotate positional, defaulted, variadic and keyword-only names."""
    tree: CommentedModule = _tree(
        source="""\
def f(a, b=1, /, c=2, *args, d=3, **kw): ...
""",
    )
    function: FunctionDef | AsyncFunctionDef = _function(tree=tree)
    parameters: list[arg] = [
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ]
    for item in (*parameters, function.args.vararg, function.args.kwarg):
        expect_not_none(value=item).annotation = _annotation(name="int")
    expect_equal(
        actual=_render(tree=tree),
        expected=(
            dedent(
                text=(
                    """\
    def f(a: int, b: int = 1, /, c: int = 2, *args: int, d: int = 3, **kw: \
int): ...
    """
                ),
            )
        ),
    )


def test_parameter_annotation_is_removed() -> None:
    """Drop an annotation, normalising the default's spacing."""
    tree: CommentedModule = _tree(
        source="""\
def f(a: int, b: str = "x", *args: int): ...
""",
    )
    function: FunctionDef | AsyncFunctionDef = _function(tree=tree)
    for item in (*function.args.args, function.args.vararg):
        expect_not_none(value=item).annotation = None
    expect_equal(
        actual=_render(tree=tree),
        expected="""\
def f(a, b="x", *args): ...
""",
    )


def test_adding_then_removing_restores_the_original_source() -> None:
    """Round-trip an edit and its undo."""
    source: str = """\
def f(a, b=1):  # keep
    return a
"""
    tree: CommentedModule = _tree(source=source)
    function: FunctionDef | AsyncFunctionDef = _function(tree=tree)
    function.returns = _annotation(name="int")
    function.args.args[0].annotation = _annotation(name="int")
    expect_in(item="-> int", container=_render(tree=tree))
    function.returns = None
    function.args.args[0].annotation = None
    expect_equal(actual=_render(tree=tree), expected=source)


def test_methods_and_crlf_are_preserved() -> None:
    """Edit a nested method in a CRLF file."""
    source: str = """\
class K:\r
    def m(self, x):\r
        return x\r
"""
    tree: CommentedModule = _tree(source=source)
    function: FunctionDef | AsyncFunctionDef = _function(tree=tree)
    function.returns = _annotation(name="int")
    function.args.args[1].annotation = _annotation(name="str")
    expect_equal(
        actual=_render(tree=tree),
        expected=(
            dedent(
                text="""\
    class K:\r
        def m(self, x: str) -> int:\r
            return x\r
    """,
            )
        ),
    )


def test_lambda_parameters_cannot_be_annotated() -> None:
    """Fail closed instead of writing invalid Python."""
    tree: CommentedModule = _tree(
        source="""\
f = lambda a: a
""",
    )
    next(n for n in walk(node=tree) if isinstance(n, Lambda)).args.args[
        0
    ].annotation = _annotation(name="int")
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="lambda",
    ):
        _render(tree=tree)


def test_complex_annotation_expressions_are_rendered() -> None:
    """Render subscripts and unions as source."""
    tree: CommentedModule = _tree(
        source="""\
def f(a): ...
""",
    )
    function: FunctionDef | AsyncFunctionDef = _function(tree=tree)
    function.args.args[0].annotation = parse(
        source="dict[str, list[int]] | None",
        mode="eval",
    ).body
    function.returns = parse(source="tuple[int, ...]", mode="eval").body
    expect_equal(
        actual=_render(tree=tree),
        expected=(
            """\
def f(a: dict[str, list[int]] | None) -> tuple[int, ...]: ...
"""
        ),
    )
