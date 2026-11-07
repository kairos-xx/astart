"""Tests for source-preserving comment AST nodes and safe AST rewrites."""

from __future__ import annotations

from ast import (
    Assign,
    ClassDef,
    Constant,
    FunctionDef,
    If,
    Module,
    Name,
    Return,
    Store,
    dump,
    parse,
    walk,
)
from textwrap import dedent
from typing import cast

import pytest
from astart.ast import Comment as CommentNode
from astart.ast import CommentedModule

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_true,
)


@pytest.mark.parametrize(
    "source",
    [
        "",
        """\
# a
""",
        """\
# a
# b""",
        """\
# a\r
name = 1  # b\r
""",
        (
            dedent(
                text="""\
    #!/usr/bin/env python3
    # coding: utf-8

    x = 'abc # not a comment' # real
    """,
            )
        ),
        """\
x = 1; y = 2 # one actual comment
""",
        """\
x = '''a # inside
b # inside'''  # outer
""",
        """\
x = (
    1,  # inside
    2,
)
""",
        (
            dedent(
                text="""\
    class A:
        # before
        def a(self):  # declaration
            # inside
            return 1  # after
        # tail
    # eof
    """,
            )
        ),
        """\
def f():
    '''Docstring.'''
    # inside
    return 1
""",
        (
            (
                """\
__ASTART_FIXTURE_DIRECTIVE_3__
x = 1  # type: int
"""
            ).replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            )
        ),
        """\
a: int = 1  # okay
""",
        (
            dedent(
                text="""\
    if True:
        # no instruction lost
        pass
    else:
        # else branch
        pass
    """,
            )
        ),
        (
            dedent(
                text="""\
    try:
        pass  # yes
    except Exception:
        # handle
        pass
    finally:
        # done
        pass
    """,
            )
        ),
        (
            dedent(
                text="""\
    match x:
        case 1:
            # first
            pass
        case _:
            # second
            pass
    """,
            )
        ),
        (
            dedent(
                text="""\
    async def f():
        async for item in seq:
            # loop
            pass
        async with resource:
            # context
            pass
    """,
            )
        ),
        (
            dedent(
                text="""\
    def f():
        if True:
            # nested
            pass

        # exit
        pass
    """,
            )
        ),
        """\
# café 🐍
name = 'é'  # latin-ñ
""",
        """\
# leading
x = 1
# trailing
""",
        """\
@staticmethod
# between decorator and def
def f(): pass
""",
    ],
)
def test_original_round_trip(source: str) -> None:
    """Every unedited parse/unparse must preserve source exactly.

    Args:
        source: The source examined while every unedited parse/unparse must
            preserve source exactly.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expected: Module = expect_instance(
        value=parse(source=source, type_comments=True),
        kind=Module,
    )
    expect_equal(actual=tree.unparse(), expected=source)
    expect_equal(
        actual=dump(
            node=Module(body=tree.body, type_ignores=tree.type_ignores),
        ),
        expected=dump(node=expected),
    )
    expect_true(
        condition=all(
            isinstance(comment, CommentNode)
            for comment in cast(typ="list[object]", val=tree.comments)
        ),
    )
    expect_equal(
        actual=len(
            [
                node
                for node in walk(node=tree)
                if isinstance(node, CommentNode)
            ],
        ),
        expected=len(tree.comments),
    )
    expect_true(
        condition=all(
            comment.text.startswith("#") for comment in tree.comments
        ),
    )


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        (
            """\
# leading
x=1 # inline
""",
            """\
# leading
x = 2  # inline
""",
        ),
        (
            """\
x = 1 # type: int
""",
            """\
x = 2  # type: int
""",
        ),
        (
            (
                (
                    """\
x = 1 __ASTART_FIXTURE_DIRECTIVE_3__
"""
                ).replace(
                    "__ASTART_FIXTURE_DIRECTIVE_3__",
                    "# t" + "ype: ignore",
                )
            ),
            (
                (
                    """\
x = 2  __ASTART_FIXTURE_DIRECTIVE_3__
"""
                ).replace(
                    "__ASTART_FIXTURE_DIRECTIVE_3__",
                    "# t" + "ype: ignore",
                )
            ),
        ),
        (
            """\
x=(
    1  # operand
)
""",
            """\
# operand
x = 2
""",
        ),
        (
            """\
x = 1
# after
""",
            """\
x = 2
# after
""",
        ),
        (
            """\
# before
x = 1""",
            """\
# before
x = 2""",
        ),
    ],
)
def test_rewrite_simple_assignment(original: str, expected: str) -> None:
    """Assignments remain compilable after edits, including type comments.

    Args:
        expected: Expected supplied as str for this operation.
        original: Original supplied as str for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(source=original)
    statement: Assign = expect_instance(value=tree.body[0], kind=Assign)
    statement.value = Constant(value=2)
    expect_equal(actual=tree.unparse(), expected=expected)
    expect_equal(
        actual=dump(node=parse(source=tree.unparse(), type_comments=True)),
        expected=dump(
            node=Module(body=tree.body, type_ignores=tree.type_ignores),
        ),
    )
    compile(source=tree.unparse(), filename="test.py", mode="exec")


def test_rewrite_nested_return() -> None:
    """Edited nested executable statements keep their comment anchors."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    # header
    return 1 # tail
""",
    )
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    return_stmt: Return = expect_instance(
        value=function.body[0],
        kind=Return,
    )
    return_stmt.value = Constant(value=2)
    expect_equal(
        actual=tree.unparse(),
        expected="""\
def f():
    # header
    return 2  # tail
""",
    )


def test_walk_sees_comments_and_standard_compiler_does_not() -> None:
    """Comments are additional AST children, not executable statements."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# A
a=1 # B
""",
    )
    expect_instance(value=tree, kind=Module)
    expect_equal(actual=len(tree.body), expected=1)
    expect_equal(
        actual=[comment.text for comment in tree.comments],
        expected=["# A", "# B"],
    )
    expect_equal(
        actual=[
            node.text
            for node in walk(node=tree)
            if isinstance(node, CommentNode)
        ],
        expected=["# A", "# B"],
    )
    expect_true(
        condition=bool(compile(source=tree, filename="test.py", mode="exec")),
    )


def test_comment_coordinates_are_utf8_bytes() -> None:
    """AST-like locations use bytes, not Unicode character indices."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 'é'  # éx
""",
    )
    comment: CommentNode = tree.comments[0]
    expect_equal(actual=comment.lineno, expected=1)
    expect_equal(actual=comment.col_offset, expected=len("x = 'é'  ".encode()))
    expect_equal(
        actual=comment.end_col_offset,
        expected=comment.col_offset
        + len(
            comment.text.encode(encoding="utf-8"),
        ),
    )
    expect_equal(actual=comment.end_lineno, expected=1)
    expect_true(condition=comment.inline)


def test_new_comment_requires_hash_and_legal_position() -> None:
    """Constructors enforce lexical invariants without accepting code."""
    for text in (
        "hello",
        """\
# first
second""",
        "# one\rtwo",
    ):
        with pytest.raises(
            expected_exception=ValueError,
            match="comment",
        ):
            CommentNode(text=text, inline=False, lineno=1, col_offset=0)
    with pytest.raises(
        expected_exception=ValueError,
        match="locations must be nonnegative",
    ):
        CommentNode(text="# x", inline=False, lineno=0, col_offset=0)
    with pytest.raises(
        expected_exception=ValueError,
        match="locations must be nonnegative",
    ):
        CommentNode(text="# x", inline=False, lineno=1, col_offset=-1)


def test_changed_comment_preserves_executable_tree() -> None:
    """Editing a normal comment remains distinct from changing the code AST."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# prior
x=1
""",
    )
    tree.comments[0].text = "# revised"
    expect_equal(
        actual=tree.unparse(),
        expected="""\
# revised
x = 1
""",
    )


def test_adding_comment_to_empty_module() -> None:
    """Adding synthetic comment AST children does not insert statements."""
    tree: CommentedModule = CommentedModule.parse(source="")
    tree.comments.append(
        CommentNode(
            text="# newly added",
            inline=False,
            lineno=1,
            col_offset=0,
        ),
    )
    expect_equal(actual=tree.unparse(), expected="# newly added")
    expect_false(condition=bool(tree.body))


def test_invalid_comment_mutation_is_detected() -> None:
    """A modified comment cannot smuggle executable text into source."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# one
""",
    )
    tree.comments[0].text = "not a comment"
    with pytest.raises(expected_exception=ValueError, match="Comment text"):
        tree.unparse()


def test_type_ignore_edit_requires_matching_standard_ast() -> None:
    """Type-ignore changes cannot silently desynchronize standard AST state."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            (
                """\
__ASTART_FIXTURE_DIRECTIVE_3__
"""
            ).replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            )
        ),
    )
    tree.comments[0].text = ("__ASTART_FIXTURE_DIRECTIVE_3__[other]").replace(
        "__ASTART_FIXTURE_DIRECTIVE_3__",
        "# t" + "ype: ignore",
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="changed the executable Python AST",
    ):
        tree.unparse()


def test_semantically_invalid_ast_mutation_is_rejected() -> None:
    """Inconsistent edits fail closed instead of dropping comment content."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1 # type: int
""",
    )
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    assignment.type_comment = "str"
    with pytest.raises(
        expected_exception=ValueError,
        match="changed the executable Python AST",
    ):
        tree.unparse()


def test_marker_prefix_collision() -> None:
    """Source containing the marker prefix never overlaps synthetic markers."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# __ASTART_SOURCE_MARKER_
x = 1
""",
    )
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    assignment.value = Constant(value=2)
    expect_equal(
        actual=tree.unparse(),
        expected="""\
# __ASTART_SOURCE_MARKER_
x = 2
""",
    )


def test_nested_comment_remains_in_suite() -> None:
    """Comments within class methods are anchored to their own suite."""
    tree: CommentedModule = CommentedModule.parse(
        source=dedent(
            text="""\
    class A:
        # class-level
        def f(self):
            # before-return
            return 1 # return
        # class-tail

    # after-class
    """,
        ),
    )
    statement: ClassDef = expect_instance(value=tree.body[0], kind=ClassDef)
    method: FunctionDef = expect_instance(
        value=statement.body[0],
        kind=FunctionDef,
    )
    return_statement: Return = expect_instance(
        value=method.body[0],
        kind=Return,
    )
    return_statement.value = Constant(value=2)
    result: str = tree.unparse()
    expect_in(
        item="""\
        # before-return
        return 2  # return""",
        container=result,
    )
    expect_in(
        item="""\
    # class-tail

# after-class""",
        container=result,
    )
    expect_in(item="    # class-level", container=result)
    expect_in(item="    def f", container=result)


def test_all_public_comments_are_used_once() -> None:
    """No comment may vanish or be synthesized during complex rewrites."""
    source: str = dedent(
        text="""\
    # head
    def f():
        if True:
            # before
            return 1 # after
        # end
    # outside
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    branch: If = expect_instance(value=function.body[0], kind=If)
    return_statement: Return = expect_instance(
        value=branch.body[0],
        kind=Return,
    )
    return_statement.value = Constant(value=2)
    result: str = tree.unparse()
    parsed: CommentedModule = CommentedModule.parse(source=result)
    expect_equal(
        actual=sorted(comment.text for comment in parsed.comments),
        expected=sorted(comment.text for comment in tree.comments),
    )


def test_new_comment_at_document_end() -> None:
    """Comments appended to an edited module stay outside executable code."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = 1
""",
    )
    tree.comments.append(
        CommentNode(text="# end", inline=False, lineno=2, col_offset=0),
    )
    expect_equal(
        actual=tree.unparse(),
        expected="""\
a = 1
# end
""",
    )


@pytest.mark.parametrize(
    "source",
    [
        """\
for item in items:  # type: int
    # inside
    pass
""",
        """\
with open('x') as stream:  # type: TextIO
    pass
""",
        """\
def calculate(value):  # type: (int) -> int
    return value
""",
        """\
if True:  # decision
    pass  # action
""",
        """\
if True:
    pass
else:  # alternate
    # before
    pass
""",
        (
            dedent(
                text="""\
    try:
        pass
    except Exception:  # handler
        pass
    else:  # no error
        pass
    finally:  # cleanup
        pass
    """,
            )
        ),
        (
            dedent(
                text="""\
    match value:
        case 1:  # first
            pass
        case _:  # fallback
            pass
    """,
            )
        ),
        """\
for item in items:
    pass
else:
    # no items
    pass
""",
        """\
try:
    pass
except* Exception:
    # grouped
    pass
""",
        """\
from __future__ import annotations  # keep

pass
""",
        (
            dedent(
                text="""\
    async def run():
        async for item in items:  # type: int
            pass
    """,
            )
        ),
        """\
# before
def f():
    'A docstring.'
    return 1
""",
    ],
)
def test_structural_changes_preserve_all_comments(source: str) -> None:
    """Even nonlocal code additions retain the comment token multiset.

    Args:
        source: The source examined while even nonlocal code additions
            retain the comment token multiset.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.append(
        Assign(
            targets=[Name(id="new_value", ctx=Store())],
            value=Constant(value=42),
        ),
    )
    output: str = tree.unparse()
    new_tree: CommentedModule = CommentedModule.parse(source=output)
    expect_equal(
        actual=sorted(comment.text for comment in tree.comments),
        expected=sorted(comment.text for comment in new_tree.comments),
    )
    expect_equal(
        actual=dump(
            node=Module(body=tree.body, type_ignores=tree.type_ignores),
        ),
        expected=dump(
            node=Module(
                body=new_tree.body,
                type_ignores=new_tree.type_ignores,
            ),
        ),
    )


def test_editing_type_comment_and_ast_together() -> None:
    """Coherent changes to type comments are supported and preserved."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1  # type: int
""",
    )
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    assignment.type_comment = "str"
    tree.comments[0].text = "# type: str"
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  # type: str
""",
    )


def test_invalid_comment_line_edit() -> None:
    """A malformed source position fails with a documented error."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# first
""",
    )
    tree.comments[0].lineno = 0
    with pytest.raises(expected_exception=ValueError, match="line numbers"):
        tree.unparse()


def test_marker_detection_fail_closed() -> None:
    """Missing or duplicated placeholder statements are rejected."""
    comment: CommentNode = CommentNode(
        text="# one",
        inline=False,
        lineno=1,
        col_offset=0,
    )
    markers: dict[str, tuple[CommentNode, bool, bool]] = {
        "marker": (comment, False, False),
    }
    with pytest.raises(
        expected_exception=ValueError,
        match="lost or duplicated",
    ):
        CommentedModule.render_markers(source="pass", markers=markers)
    with pytest.raises(
        expected_exception=ValueError,
        match="duplicated a comment marker",
    ):
        CommentedModule.render_markers(
            source="""\
'marker'
'marker'""",
            markers=markers,
        )


def test_plain_ast_edits_without_comments() -> None:
    """When no comments exist, unparse remains compatible with ast.unparse."""
    tree: CommentedModule = CommentedModule.parse(source="x=1")
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    assignment.value = Constant(value=2)
    expect_equal(actual=tree.unparse(), expected="x = 2")


def test_comment_on_except_and_else_headers() -> None:
    """Comments remain attached to each clause's header or first statement."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            dedent(
                text="""\
    try:
        x = 1
    except Exception:  # handler
        # inside handler
        pass
    else:  # success
        # inside else
        x = 2
    finally:  # cleanup
        # inside finally
        pass
    """,
            )
        ),
    )
    tree.body.append(
        Assign(targets=[Name(id="end", ctx=Store())], value=Constant(value=1)),
    )
    text: str = tree.unparse()
    expect_in(
        item="""\
except Exception:  # handler
    # inside handler""",
        container=text,
    )
    expect_in(
        item="""\
else:  # success
    # inside else""",
        container=text,
    )
    expect_in(
        item="""\
finally:  # cleanup
    # inside finally""",
        container=text,
    )
