"""Regression tests for exact and conservative syntax-preserving AST edits."""

from __future__ import annotations

from ast import (
    Assign,
    Attribute,
    Constant,
    Load,
    Name,
    Return,
    Store,
    arg,
    dump,
    parse,
)
from ast import (
    List as ListNode,
)
from ast import (
    Tuple as TupleNode,
)
from dataclasses import FrozenInstanceError
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.ast import (
    CommentedModule,
    CommentGroup,
    SingleLineComment,
    SuppressionComment,
)
from astart.formatting import (
    FormatPreservationError,
    FormatPreserver,
    Patch,
    preserve_docstring_content,
)

from tests.expectations import (
    expect_call_expr,
    expect_constant_expr,
    expect_equal,
    expect_false,
    expect_function_node,
    expect_in,
    expect_instance,
    expect_named_node,
    expect_not_none,
    expect_suite_node,
    expect_true,
    expect_value_stmt,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.tokens import TokenSnapshot


@pytest.mark.parametrize(
    ("source", "changed", "expected"),
    [
        (
            """\
x  =  "old"   # keep
y = (1, 2,)
""",
            "new",
            """\
x  =  "new"   # keep
y = (1, 2,)
""",
        ),
        (
            (
                (
                    """\
x='old'  __ASTART_FIXTURE_DIRECTIVE_4__
"""
                ).replace(
                    "__ASTART_FIXTURE_DIRECTIVE_4__",
                    "# n" + "oqa",
                )
            ),
            "new",
            (
                (
                    """\
x='new'  __ASTART_FIXTURE_DIRECTIVE_4__
"""
                ).replace(
                    "__ASTART_FIXTURE_DIRECTIVE_4__",
                    "# n" + "oqa",
                )
            ),
        ),
        (
            """\
x = '''old'''
""",
            "new",
            """\
x = '''new'''
""",
        ),
        (
            """\
x = 0x1a  # hex
""",
            31,
            """\
x = 0x1f  # hex
""",
        ),
        (
            """\
x = 0b101
""",
            6,
            """\
x = 0b110
""",
        ),
        (
            """\
x = 0o17
""",
            8,
            """\
x = 0o10
""",
        ),
        (
            """\
x  =  [1, 2, 3,] # trailing
""",
            10,
            """\
x  =  [10, 2, 3,] # trailing
""",
        ),
        (
            """\
café  =   "olá"
""",
            "sim",
            """\
café  =   "sim"
""",
        ),
        (
            """\
x = 1\r
y = 2\r
""",
            4,
            """\
x = 4\r
y = 2\r
""",
        ),
    ],
)
def test_leaf_value_retains_lexical_layout(
    source: str,
    changed: str | int,
    expected: str,
) -> None:
    """Patch a single literal without altering adjacent formatting.

    Args:
        changed: Changed supplied as str | int for this operation.
        expected: Expected supplied as str for this operation.
        source: The source examined while patch a single literal without
            altering adjacent formatting.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    if isinstance(assignment.value, Constant):
        assignment.value.value = changed
    else:
        sequence: ListNode = expect_instance(
            value=assignment.value,
            kind=ListNode,
        )
        element: Constant = expect_instance(
            value=sequence.elts[0],
            kind=Constant,
        )
        element.value = changed
    result: str = tree.unparse(preserve_formatting=True)
    expect_equal(actual=result, expected=expected)
    expect_equal(actual=tree.token_source, expected=expected)
    expect_equal(
        actual=dump(node=parse(source=result)),
        expected=dump(node=parse(source=expected)),
    )


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (
            """\
def original( x :int,):
    return x
""",
            "renamed",
            """\
def renamed( x :int,):
    return x
""",
        ),
        (
            """\
@decorate
def original(x):
    return x
""",
            "renamed",
            """\
@decorate
def renamed(x):
    return x
""",
        ),
        (
            """\
class Original:
    pass
""",
            "Renamed",
            """\
class Renamed:
    pass
""",
        ),
    ],
)
def test_definition_renames_preserve_header_layout(
    source: str,
    target: str,
    expected: str,
) -> None:
    """Definition-name edits retain decorators and header punctuation.

    Args:
        expected: Expected supplied as str for this operation.
        source: The source examined while definition-name edits retain
            decorators and header punctuation.
        target: The target examined while definition-name edits retain
            decorators and header punctuation.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_named_node(value=tree.body[0]).name = target
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )


def test_argument_renames_preserve_trailing_comma() -> None:
    """Arg renames do not regenerate or normalize signature syntax."""
    source: str = """\
def f(  value : str, ) :  # note
    return value
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    argument: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    argument.arg = "amount"
    expected: str = source.replace("value :", "amount :", count=1)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(
        actual=tree.token_snapshot(node=argument).source_text,
        expected="amount : str",
    )


def test_mutated_comment_and_shebang_retain_source_whitespace() -> None:
    """Edited comments and shebang components keep unaffected bytes."""
    source: str = (
        dedent(
            text="""\
    #!/usr/bin/env python3

    value  = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501
    """,
        )
    ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_not_none(value=tree.shebang).interpreter.path = "python3.13"
    suppression: SuppressionComment = expect_instance(
        value=tree.comments[-1],
        kind=SuppressionComment,
    )
    suppression.rules[0].code = "F841"
    expected: str = (
        dedent(
            text="""\
    #!/usr/bin/env python3.13

    value  = 1  __ASTART_FIXTURE_DIRECTIVE_4__: F841
    """,
        )
    ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_moving_top_level_nodes_keeps_attached_comments_and_empty_lines() -> (
    None
):
    """The lexical prefix of a moved statement travels with the statement."""
    source: str = """\
#!/usr/bin/env python3
# header
x=1

# attached
y  =  2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.reverse()
    expected: str = """\
#!/usr/bin/env python3
# header

# attached
y  =  2
x=1
"""
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_nested_sibling_move_keeps_spacing_and_comments() -> None:
    """Nested suite reorder keeps trivia and avoids whole-function print."""
    source: str = dedent(
        text="""\
    def f():  # header
        first  =  1

        # second
        second = (2, 3,)
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_suite_node(value=tree.body[0]).body.reverse()
    expected: str = dedent(
        text="""\
    def f():  # header

        # second
        second = (2, 3,)
        first  =  1
    """,
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_inserting_new_nodes_preserves_surrounding_source() -> None:
    """Canonical printing applies only to newly introduced statements."""
    source: str = """\
#!/usr/bin/env python3
x  =  0x1A  # trailing
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.append(
        Assign(
            targets=[Name(id="new_value", ctx=Store())],
            value=Constant(value=3),
        ),
    )
    result: str = tree.unparse(preserve_formatting=True)
    expect_equal(
        actual=result,
        expected=source
        + """\
new_value = 3
""",
    )
    expect_equal(actual=tree.token_source, expected=result)


def test_inserting_statement_into_nested_suite() -> None:
    """New nested statements inherit a suite's indentation."""
    source: str = """\
def f():
    value  =  2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_suite_node(value=tree.body[0]).body[:0] = [
        Return(value=Constant(value=7)),
    ]
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
def f():
    return 7
    value  =  2
""",
    )


def test_replacing_expression_preserves_statement_format() -> None:
    """Replacing an expression changes only its AST lexical span."""
    source: str = """\
target   =  (1, 2, 3,)  # untouched
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_value_stmt(value=tree.body[0]).value = TupleNode(
        elts=[Constant(value=5), Constant(value=6)],
        ctx=Load(),
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
target   =  (5, 6)  # untouched
""",
    )


def test_module_docstring_summary_keeps_original_multiline_indentation() -> (
    None
):
    """Structured summary changes do not normalize untouched prose margins."""
    source: str = dedent(
        text="""\
    '''Original.

        A prose paragraph.

        Args:
            name (str): A value.
        '''
    value  =  (1, 2,)
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_not_none(value=tree.module_docstring).summary_node.text = "Updated."
    expected: str = source.replace("Original.", "Updated.")
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_description_edit_keeps_section_markup_and_quote_preference() -> None:
    """Description-only edits preserve the rest of a Google docstring."""
    source: str = dedent(
        text="""\
    def f():
        \"""Summary.

        Before.

        Returns:
            int: Number.
        \"""
        return 1
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.docstrings[0].description_node.text = "After."
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source.replace(
            "Before.",
            "After.",
        ),
    )


def test_no_op_formatting_mode_is_exact_and_token_revision_is_stable() -> None:
    """Unmodified input round-trips exactly, incl. CRLF and trailing space."""
    source: str = """\
# hello  \r
x=(1,2,)\r
\r
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )
    expect_equal(actual=tree.token_source, expected=source)


def test_repeated_edits_and_undo_use_original_format_baseline() -> None:
    """Preservation never advances to a previously regenerated baseline."""
    source: str = """\
x   =   "original"
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = "first"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x   =   "first"
""",
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = "second"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x   =   "second"
""",
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = "original"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )


def test_same_line_statement_reordering_fails_closed() -> None:
    """Ambiguous semicolon statements must not duplicate their source line."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a = 1; b = 2
""",
    )
    tree.body.reverse()
    with pytest.raises(expected_exception=FormatPreservationError):
        tree.unparse(preserve_formatting=True)
    fallback: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="fallback",
    )
    expect_equal(
        actual=dump(node=parse(source=fallback)),
        expected=dump(
            node=parse(
                source="""\
b = 2
a = 1
""",
            ),
        ),
    )


def test_unsupported_expression_list_uses_localized_canonical_printing() -> (
    None
):
    """Expression fallback may reformat locally; outer trivia is kept."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
call(  1, 2, )  # note
""",
    )
    expect_call_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).args.reverse()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
call(2, 1)  # note
""",
    )


def test_formatting_mode_validates_conflict_policy() -> None:
    """Invalid conflict-mode inputs fail before mutating source state."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
""",
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="on_format_conflict",
    ):
        tree.unparse(preserve_formatting=True, on_format_conflict="ignore")


def test_empty_file_can_receive_code_without_moving_shebang() -> None:
    """File-header comments remain ahead of newly inserted declarations."""
    source: str = """\
#!/usr/bin/env python3
# header
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.append(
        Assign(
            targets=[Name(id="number", ctx=Store())],
            value=Constant(value=9),
        ),
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source
        + """\
number = 9
""",
    )


def test_existing_type_ignore_remains_recognized() -> None:
    """No implicit removal of parser-level type ignore state is permitted."""
    source: str = (
        """\
x=1  __ASTART_FIXTURE_DIRECTIVE_3__[assignment]
"""
    ).replace("__ASTART_FIXTURE_DIRECTIVE_3__", "# t" + "ype: ignore")
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 3
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=(
            (
                """\
x=3  __ASTART_FIXTURE_DIRECTIVE_3__[assignment]
"""
            ).replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            )
        ),
    )
    expect_equal(actual=tree.type_ignores[0].tag, expected="[assignment]")


def test_new_node_does_not_mutate_caller_locations() -> None:
    """Fallback AST location fixing happens on private copies only."""
    source: str = """\
f=2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    inserted: Assign = Assign(
        targets=[Name(id="new", ctx=Store())],
        value=Constant(value=1),
    )
    tree.body.append(inserted)
    tree.unparse(preserve_formatting=True)
    expect_false(condition=hasattr(inserted, "lineno"))


def test_deep_comment_node_token_snapshots_remain_immutable() -> None:
    """Token snapshots are revisioned after editing code and comments."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1 # hi
""",
    )
    original: TokenSnapshot = tree.token_snapshot(
        node=expression_of_stmt(value=tree.body[0]),
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = 2
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=2 # hi
""",
    )
    refreshed: TokenSnapshot = tree.token_snapshot(
        node=expression_of_stmt(value=tree.body[0]),
    )
    expect_equal(actual=original.source_text, expected="1")
    expect_equal(actual=refreshed.source_text, expected="2")
    expect_true(condition=refreshed.source_revision > original.source_revision)
    field_name: str = "source_text"
    with pytest.raises(expected_exception=FrozenInstanceError):
        setattr(refreshed, field_name, "invalid")


@pytest.mark.parametrize(
    ("source", "operation", "expected"),
    [
        (
            """\
def f( x, y, ):
    return x
""",
            "reverse",
            """\
def f( y, x, ):
    return x
""",
        ),
        (
            """\
def f(x, y,):
    return x
""",
            "append",
            """\
def f(x, y, z,):
    return x
""",
        ),
        (
            """\
def f(x, y,):
    return x
""",
            "remove",
            """\
def f(x,):
    return x
""",
        ),
        (
            """\
def f():
    return 1
""",
            "append",
            """\
def f(z):
    return 1
""",
        ),
        (
            """\
def f( x: int,
       y: str,
):
    return x
""",
            "reverse",
            """\
def f( y: str,
       x: int,
):
    return x
""",
        ),
    ],
)
def test_signature_edits_preserve_commas_and_indentation(
    source: str,
    operation: str,
    expected: str,
) -> None:
    """Simple argument addition, deletion, and moves retain delimiter style.

    Args:
        expected: Expected supplied as str for this operation.
        operation: Operation supplied as str for this operation.
        source: The source examined while simple argument addition,
            deletion, and moves retain delimiter style.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    arguments: list[arg] = expect_function_node(value=tree.body[0]).args.args
    if operation == "reverse":
        arguments.reverse()
    elif operation == "remove":
        arguments.pop()
    else:
        arguments.append(arg(arg="z", annotation=None))
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_argument_edits_with_defaults_fail_explicitly() -> None:
    """A defaults-bearing signature requires broader source reconstruction."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x=1, y=2, ):
    return x
""",
    )
    expect_function_node(value=tree.body[0]).args.args.append(
        arg(arg="z", annotation=None),
    )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="simple",
    ):
        tree.unparse(preserve_formatting=True)


def test_source_with_multiline_string_cannot_be_reindented_silently() -> None:
    """Changing physical string indentation can change runtime values."""
    source: str = """\
message = \"""First
 Second
\"""

def f():
    x=1
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_suite_node(value=tree.body[1]).body += tree.body[:1]
    del tree.body[:1]
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="multiline",
    ):
        tree.unparse(preserve_formatting=True)


def test_cross_indent_move_of_single_line_statement() -> None:
    """Source fragments may move from root indentation into a nested suite."""
    source: str = """\
x  =  (1, 2,)

def f():
    y=2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_suite_node(value=tree.body[1]).body[:0] = tree.body[:1]
    del tree.body[:1]
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\

def f():
    x  =  (1, 2,)
    y=2
""",
    )


def test_mutation_to_unsupported_syntax_fails_before_return() -> None:
    """Removing every statement from an existing suite must be rejected."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
if condition:
    work()
""",
    )
    expect_suite_node(value=tree.body[0]).body.clear()
    with pytest.raises(expected_exception=FormatPreservationError):
        tree.unparse(preserve_formatting=True)


def test_expression_rename_remains_byte_local() -> None:
    """Attribute renames leave parenthesized expressions and comments alone."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
answer = ( service.attribute  )  # inspect
""",
    )
    renamed: Attribute = expect_instance(
        value=expression_of_stmt(value=tree.body[0]),
        kind=Attribute,
    )
    renamed.attr = "updated"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
answer = ( service.updated  )  # inspect
""",
    )


def test_different_literal_type_remains_semantically_correct() -> None:
    """Changing a literal type keeps outer layout and validates the AST."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value   =  5  # keep
""",
    )
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = "hello"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
value   =  'hello'  # keep
""",
    )


def test_comments_added_after_capture_are_rejected() -> None:
    """New comments have no stable source anchors for reconstruction."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1
""",
    )
    tree.comments.append(
        SingleLineComment(
            text="# new",
            inline=False,
            lineno=1,
            col_offset=0,
        ),
    )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="New comments",
    ):
        tree.unparse(preserve_formatting=True)


def test_moved_comment_groups_recalculate_current_blank_line_gaps() -> None:
    """Comment block groups use current emitted positions, not stale lines."""
    source: str = """\
a=1

# beta
# gamma
b=2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.reverse()
    expected: str = """\

# beta
# gamma
b=2
a=1
"""
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_true(
        condition=any(
            isinstance(item, CommentGroup) and item.blank_lines == [0]
            for item in tree.comment_blocks
        ),
    )
    expect_equal(actual=tree.token_source, expected=expected)


def test_formatted_comment_can_be_edited_after_moving_its_statement() -> None:
    """Original comment anchors survive repeat source regeneration."""
    source: str = (
        """\
a=1

b=2  __ASTART_FIXTURE_DIRECTIVE_4__: E501
"""
    ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.reverse()
    expect_in(item="b=2", container=tree.unparse(preserve_formatting=True))
    edited: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    edited.rules[0].code = "F401"
    result: str = tree.unparse(preserve_formatting=True)
    expect_in(
        item=(
            ("b=2  __ASTART_FIXTURE_DIRECTIVE_4__: F401").replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            )
        ),
        container=result,
    )
    expect_equal(actual=tree.token_source, expected=result)


def test_removal_of_last_root_statement_keeps_footer_comment() -> None:
    """A trailing free-floating source comment remains in the file footer."""
    source: str = """\
x=1
# footer
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.clear()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
# footer
""",
    )


def test_docstring_summary_layout_conflict_can_fallback() -> None:
    """Unsupported summary markup raises, or converts with a fallback."""
    source: str = """\
def f():
    \"""Original.\"""
    pass
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.docstrings[0].summary_node.text = """\
New
summary"""
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="one physical line",
    ):
        tree.unparse(preserve_formatting=True)
    result: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="fallback",
    )
    expect_in(
        item="""\
New
summary""",
        container=str(
            object=expect_constant_expr(
                value=expression_of_stmt(
                    value=expect_suite_node(
                        value=parse(source=result).body[0],
                    ).body[0],
                ),
            ).value,
        ),
    )


def test_new_docstring_section_rejects_lossy_preservation() -> None:
    """A field-level doc edit needs either precise mapping or fallback mode."""
    source: str = dedent(
        text="""\
    def f(x: int):
        \"""Summary.

        Args:
            x (int): Existing.
        \"""
        return x
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.docstrings[0].entries(kind="parameters")[
        0
    ].description = "New description."
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="Structural docstring",
    ):
        tree.unparse(preserve_formatting=True)
    expect_in(
        item="New description.",
        container=tree.unparse(
            preserve_formatting=True,
            on_format_conflict="fallback",
        ),
    )


def test_docstring_summary_description_location_errors() -> None:
    """The prose patcher explicitly rejects ambiguous text anchors."""
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="summary must",
    ):
        preserve_docstring_content(
            original="Original.",
            old_summary="Original.",
            new_summary="""\
One
Two""",
            old_description="",
            new_description="",
        )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="no lexical representation",
    ):
        preserve_docstring_content(
            original="",
            old_summary="Original",
            new_summary="Changed",
            old_description="",
            new_description="",
        )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="unique source",
    ):
        preserve_docstring_content(
            original="Something else.",
            old_summary="Original",
            new_summary="Changed",
            old_description="",
            new_description="",
        )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="source anchor",
    ):
        preserve_docstring_content(
            original="Summary.",
            old_summary="Summary.",
            new_summary="Summary.",
            old_description="",
            new_description="New.",
        )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="unique span",
    ):
        preserve_docstring_content(
            original="""\
Summary.

Missing.""",
            old_summary="Summary.",
            new_summary="Summary.",
            old_description="Previous.",
            new_description="New.",
        )


def test_format_engine_rejects_overlapping_patch_ranges() -> None:
    """Conflicting lexical edits cannot overwrite one another silently."""
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="Overlapping",
    ):
        FormatPreserver.apply(
            source="abc",
            begin=0,
            end=3,
            patches=[
                Patch(start=0, end=2, text="X"),
                Patch(start=1, end=3, text="Y"),
            ],
        )


@pytest.mark.parametrize(
    ("source", "changed", "expected"),
    [
        (
            """\
x=1_000
""",
            2000,
            """\
x=2_000
""",
        ),
        (
            """\
x=0xAB_CD
""",
            0x12EF,
            """\
x=0x12_EF
""",
        ),
        (
            """\
x=0XAA_CC
""",
            0xFFE0,
            """\
x=0XFF_E0
""",
        ),
        (
            """\
x=0b1010_1000
""",
            0b11110000,
            """\
x=0b1111_0000
""",
        ),
        (
            """\
x=100
""",
            20000,
            """\
x=20000
""",
        ),
        (
            """\
x=r"old"
""",
            "new",
            """\
x="new"
""",
        ),
        (
            """\
x="old"
""",
            "a\\b",
            """\
x="a\\\\b"
""",
        ),
        (
            """\
x='old'
""",
            """\
line
one""",
            """\
x='line\\none'
""",
        ),
    ],
)
def test_styled_literals_remain_parseable_and_readable(
    source: str,
    changed: str | int,
    expected: str,
) -> None:
    """Keep numeric bases, grouping, quote style and escaped literals.

    Args:
        changed: Changed supplied as str | int for this operation.
        expected: Expected supplied as str for this operation.
        source: The source examined while keep numeric bases, grouping,
            quote style and escaped literals.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_constant_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).value = changed
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )


def test_moved_multiline_fstring_must_fail_closed() -> None:
    """Multiline f-strings with significant indentation are not reindented."""
    source: str = """\
text = f\"""Hello
{value}
\"""

def f():
    return 3
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_suite_node(value=tree.body[1]).body += tree.body[:1]
    del tree.body[:1]
    with pytest.raises(expected_exception=FormatPreservationError):
        tree.unparse(preserve_formatting=True)


def test_block_lint_directive_movement_requires_explicit_fallback() -> None:
    """Moving statements over block suppressions changes applicability."""
    source: str = """\
# fmt: off
first=1
# fmt: on
second=2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.reverse()
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="suppression scope",
    ):
        tree.unparse(preserve_formatting=True)


def test_line_lint_directive_moves_with_its_statement() -> None:
    """Line-specific lint controls remain on the same moved statement."""
    source: str = (
        """\
first=1
second=2  __ASTART_FIXTURE_DIRECTIVE_4__: F841
"""
    ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    tree.body.reverse()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=(
            (
                """\
second=2  __ASTART_FIXTURE_DIRECTIVE_4__: F841
first=1
"""
            ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
        ),
    )
