"""Exercise docstring AST nodes, suppression rules and comment blocks."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Constant,
    Expr,
    FunctionDef,
    Pass,
    arg,
    arguments,
    walk,
)
from textwrap import dedent
from typing import Final, final

import pytest
from astart.docstrings import (
    DocEntry,
    DocstringLayout,
    DocstringNode,
    parse_docstring,
)
from astart.source.ast import (
    Comment,
    CommentedModule,
    CommentGroup,
    MultilineComment,
    SingleLineComment,
    SuppressionComment,
    SuppressionRule,
)

from tests.support.expectations import (
    expect_constant_expr,
    expect_equal,
    expect_false,
    expect_function_node,
    expect_in,
    expect_instance,
    expect_is,
    expect_suite_node,
    expect_true,
    expect_value_stmt,
    expression_of_stmt,
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        google (Final[str]): Grouped module constant.
        numpy (Final[str]): Grouped module constant.
        rest (Final[str]): Grouped module constant.
        epytext (Final[str]): Grouped module constant.
        pep257 (Final[str]): Grouped module constant.

    """

    google: Final[str] = '''\
"""Calculate a sum.

    Aggregate integer values.

    Args:
        left (int): First value.
        right (int): Second value.

    Returns:
        int: Computed total.

    Raises:
        ValueError: Negative input.
    """'''
    numpy: Final[str] = '''\
"""Calculate a sum.

    Parameters
    ----------
    left : int
        First value.
    right : int
        Second value.

    Returns
    -------
    int
        Computed total.

    Raises
    ------
    ValueError
        Negative input.
    """'''
    rest: Final[str] = '''\
"""Calculate a sum.

    :param left: First value.
    :type left: int
    :param right: Second value.
    :type right: int
    :returns: Computed total.
    :rtype: int
    :raises ValueError: Negative input.
    """'''
    epytext: Final[str] = '''\
"""Calculate a sum.

    @param left: First value.
    @type left: int
    @param right: Second value.
    @type right: int
    @return: Computed total.
    @rtype: int
    @raise ValueError: Negative input.
    """'''
    pep257: Final[str] = '''\
"""Calculate a sum.

    Aggregate integer values.
    """'''


@pytest.mark.parametrize(
    ("doc", "style", "expected_count"),
    [
        (Constants.google, "google", 4),
        (Constants.numpy, "numpy", 4),
        (Constants.rest, "rest", 4),
        (Constants.epytext, "epytext", 4),
        (Constants.pep257, "pep257", 0),
    ],
)
def test_all_styles_parse_into_shared_entries(
    doc: str,
    style: str,
    expected_count: int,
) -> None:
    """Five supported formats normalize to same typed semantic field kinds.

    Args:
        doc (str): Doc supplied as str for this operation.
        expected_count (int): Expected count supplied as int for this
            operation.
        style (str): Style supplied as str for this operation.

    """
    source: str = f"""\
def calculate(left: int, right: int) -> int:
    {doc}
    if left < 0:
        raise ValueError('negative')
    return left + right
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=tree.unparse(), expected=source)
    expect_equal(actual=len(tree.docstrings), expected=1)
    node: DocstringNode = tree.docstrings[0]
    expect_equal(actual=node.style, expected=style)
    expect_equal(actual=node.summary, expected="Calculate a sum.")
    expect_equal(actual=len(node.entries()), expected=expected_count)
    expect_is(actual=node.owner, expected=tree.body[0])
    expect_is(
        actual=node.expression,
        expected=expect_suite_node(value=tree.body[0]).body[0],
    )
    if expected_count:
        expect_is(
            actual=node.entries(kind="parameters")[0].target,
            expected=expect_function_node(value=tree.body[0]).args.args[0],
        )
        expect_is(
            actual=node.entries(kind="parameters")[1].target,
            expected=expect_function_node(value=tree.body[0]).args.args[1],
        )
        expect_is(
            actual=node.entries(kind="returns")[0].target,
            expected=expect_function_node(value=tree.body[0]).returns,
        )
        expect_instance(value=node.entries(kind="raises")[0].target, kind=AST)
        expect_true(
            condition=all(
                entry.link_role is not None for entry in node.entries()
            ),
        )
    else:
        expect_equal(
            actual=node.description,
            expected="Aggregate integer values.",
        )
    expect_equal(
        actual=len(
            [n for n in walk(node=tree) if isinstance(n, DocstringNode)],
        ),
        expected=1,
    )


def test_docstring_style_conversion_preserves_schema() -> None:
    """Styles share a normalized form, including type-bearing fields."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(left: int) -> int:
    """
        + Constants.rest.replace("right", "unused")
        + """\

    return left
""",
    )
    node: DocstringNode = tree.docstrings[0]
    for style in ("google", "numpy", "rest", "epytext"):
        rendered: str = node.render(style=style)
        converted: DocstringNode = parse_docstring(source=rendered)
        expect_equal(actual=converted.style, expected=style)
        expect_equal(actual=converted.summary, expected=node.summary)
        expect_equal(
            actual=converted.entries(kind="parameters")[0].name,
            expected="left",
        )
    with pytest.raises(
        expected_exception=ValueError,
        match="Mixed syntax cannot be generated",
    ):
        node.render(style="mixed")


def test_edit_docstring_semantics_and_source() -> None:
    """Changing typed fields updates the executable string constant."""
    tree: CommentedModule = CommentedModule.parse(
        source=dedent(
            text="""\
    def f(x):
        \"""One.

        Args:
            x (int): Old.
        \"""
        return x
    """,
        ),
    )
    entry: DocEntry = tree.docstrings[0].entries(kind="parameters")[0]
    entry.description = "New explanation."
    result: str = tree.unparse()
    expect_in(item="New explanation.", container=result)
    docstring: Constant = expect_instance(
        value=expression_of_stmt(
            value=expect_suite_node(value=tree.body[0]).body[0],
        ),
        kind=Constant,
    )
    expect_in(item="New explanation.", container=str(object=docstring.value))
    expect_equal(
        actual=CommentedModule.parse(source=result)
        .docstrings[0]
        .entries()[0]
        .description,
        expected="New explanation.",
    )


def test_edited_docstring_with_code_transform() -> None:
    """Docstrings and executable AST can be edited simultaneously."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    \"""Original.\"""
    return x # last
""",
    )
    tree.docstrings[0].summary = "Revised."
    expect_value_stmt(
        value=expect_suite_node(value=tree.body[0]).body[1],
    ).value = Constant(value=3)
    result: str = tree.unparse()
    expect_in(item="Revised.", container=result)
    expect_in(item="return 3  # last", container=result)
    expect_equal(
        actual=CommentedModule.parse(source=result).docstrings[0].summary,
        expected="Revised.",
    )


def test_two_sided_doc_edit_conflict_fails() -> None:
    """Divergent direct AST and structured edits cannot silently overwrite."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    \"""Before.\"""
    pass
""",
    )
    tree.docstrings[0].summary = "Structured."
    expect_constant_expr(
        value=expression_of_stmt(
            value=expect_suite_node(value=tree.body[0]).body[0],
        ),
    ).value = "Other."
    with pytest.raises(expected_exception=ValueError, match="both changed"):
        tree.unparse()


def test_class_attribute_links_and_nested_docstrings() -> None:
    """Class attribute docs and nested function docs map to true AST nodes."""
    source: str = """\
\"""Module documentation.\"""
class Service:
    \"""A service.

    Attributes:
        limit (int): Request limit.
    \"""
    limit: int = 5
    def compute(self, count: int) -> int:
        \"""Compute.

        Args:
            count (int): Number to process.
        \"""
        return count
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=len(tree.docstrings), expected=3)
    expect_is(actual=tree.docstrings[0].owner, expected=None)
    expect_instance(
        value=tree.docstrings[1].entries()[0].target,
        kind=AnnAssign,
    )
    expect_instance(value=tree.docstrings[2].entries()[0].target, kind=arg)
    expect_equal(actual=tree.unparse(), expected=source)


@pytest.mark.parametrize(
    ("token", "tool", "action", "rules", "scope"),
    [
        (
            "__ASTART_FIXTURE_DIRECTIVE_4__".replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            ),
            "flake8/ruff",
            "ignore",
            [],
            "line",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_4__: E501, F401".replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            ),
            "flake8/ruff",
            "ignore",
            ["E501", "F401"],
            "line",
        ),
        (
            "# pylint: disable=missing-docstring,too-many-lines",
            "pylint",
            "disable",
            ["missing-docstring", "too-many-lines"],
            "file",
        ),
        (
            "# pylint: enable=missing-docstring",
            "pylint",
            "enable",
            ["missing-docstring"],
            "file",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_3__".replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            ),
            "type",
            "ignore",
            [],
            "line",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_3__[assignment, arg-type]".replace(
                "__ASTART_FIXTURE_DIRECTIVE_3__",
                "# t" + "ype: ignore",
            ),
            "type",
            "ignore",
            ["assignment", "arg-type"],
            "line",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_1__[reportUnknownMemberType]".replace(
                "__ASTART_FIXTURE_DIRECTIVE_1__",
                "# p" + "yright: ignore",
            ),
            "pyright",
            "ignore",
            ["reportUnknownMemberType"],
            "line",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_0__[reportAny]".replace(
                "__ASTART_FIXTURE_DIRECTIVE_0__",
                "# b" + "asedpyright: ignore",
            ),
            "basedpyright",
            "ignore",
            ["reportAny"],
            "line",
        ),
        ("# fmt: off", "fmt", "off", [], "block"),
        ("# fmt: on", "fmt", "on", [], "block"),
        ("# fmt: skip", "fmt", "skip", [], "block"),
        ("# autopep8: off", "autopep8", "off", [], "block"),
        ("# autopep8: on", "autopep8", "on", [], "block"),
        ("# coverswitch: skip", "coverage", "skip", [], "line"),
        ("# pragma: no cover", "coverage", "ignore", [], "line"),
        ("# pragma: nomutate", "coverage", "skip", [], "line"),
        (
            "__ASTART_FIXTURE_DIRECTIVE_2__".replace(
                "__ASTART_FIXTURE_DIRECTIVE_2__",
                "# r" + "uff: noqa",
            ),
            "ruff",
            "ignore",
            [],
            "file",
        ),
        (
            "__ASTART_FIXTURE_DIRECTIVE_2__: F401, E402".replace(
                "__ASTART_FIXTURE_DIRECTIVE_2__",
                "# r" + "uff: noqa",
            ),
            "ruff",
            "ignore",
            ["F401", "E402"],
            "file",
        ),
        ("# isort: skip", "isort", "skip", [], "line"),
        ("# isort: skip_file", "isort", "skip", [], "file"),
        ("# isort: off", "isort", "off", [], "block"),
        ("# isort: on", "isort", "on", [], "block"),
        ("# nosec", "bandit", "ignore", [], "line"),
        ("# nosec: B101, B102", "bandit", "ignore", ["B101", "B102"], "line"),
        ("# sourcery skip: use-any", "sourcery", "skip", ["use-any"], "line"),
        ("# xenon: ignore", "xenon", "ignore", [], "block"),
        ("# local-checker: disable", "local-checker", "disable", [], "file"),
    ],
)
def test_all_suppression_forms(
    token: str,
    tool: str,
    action: str,
    rules: list[str],
    scope: str,
) -> None:
    """Recognize the listed directives and tokenize explicit codes.

    Args:
        action (str): Action supplied as str for this operation.
        rules (list[str]): Rules supplied as list[str] for this operation.
        scope (str): The scope examined while recognize the listed
            directives and tokenize explicit codes.
        token (str): Token supplied as str for this operation.
        tool (str): Tool supplied as str for this operation.

    """
    source: str = (
        token
        + """\

x = 1
"""
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    comment: Comment = tree.comments[0]
    comment = expect_instance(value=comment, kind=SuppressionComment)
    expect_equal(actual=comment.tool, expected=tool)
    expect_equal(actual=comment.action, expected=action)
    expect_equal(actual=comment.scope, expected=scope)
    expect_equal(actual=[rule.code for rule in comment.rules], expected=rules)
    expect_is(actual=comment.all_rules, expected=not rules)
    expect_equal(
        actual=len(
            [
                node
                for node in walk(node=tree)
                if isinstance(node, SuppressionRule)
            ],
        ),
        expected=len(rules),
    )
    expect_equal(actual=tree.unparse(), expected=source)


def test_regular_comments_and_group_separators() -> None:
    """Distinguish single, multiline and blank-separated comment clusters."""
    source: str = """\
# line1

# line3
# line4


# line7
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=len(tree.comments), expected=4)
    expect_equal(actual=len(tree.comment_blocks), expected=2)
    first_group: CommentGroup = expect_instance(
        value=tree.comment_blocks[0],
        kind=CommentGroup,
    )
    expect_true(
        condition=not isinstance(tree.comment_blocks[0], MultilineComment),
    )
    expect_equal(actual=first_group.blank_lines, expected=[1, 0])
    expect_instance(value=tree.comment_blocks[1], kind=SingleLineComment)
    expect_equal(
        actual=tree.comment_blocks[0].text,
        expected="""\
# line1

# line3
# line4""",
    )
    expect_equal(
        actual=len(
            [node for node in walk(node=tree) if isinstance(node, Comment)],
        ),
        expected=4,
    )
    expect_equal(actual=tree.unparse(), expected=source)


def test_multiline_comment_class() -> None:
    """Adjacent full comment lines become a dedicated multiline AST node."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# first
# second
""",
    )
    expect_equal(actual=len(tree.comment_blocks), expected=1)
    expect_instance(value=tree.comment_blocks[0], kind=MultilineComment)
    expect_equal(
        actual=tree.comment_blocks[0].text,
        expected="""\
# first
# second""",
    )


def test_suppressions_survive_ast_edit() -> None:
    """Reconstruction keeps inline and file-level suppression tokens."""
    source: str = (
        (
            """\
__ASTART_FIXTURE_DIRECTIVE_2__: F401
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501
"""
        )
        .replace("__ASTART_FIXTURE_DIRECTIVE_2__", "# r" + "uff: noqa")
        .replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_value_stmt(value=tree.body[0]).value = Constant(value=2)
    expect_equal(
        actual=tree.unparse(),
        expected=(
            """\
__ASTART_FIXTURE_DIRECTIVE_2__: F401
x = 2  __ASTART_FIXTURE_DIRECTIVE_4__: E501
"""
        )
        .replace("__ASTART_FIXTURE_DIRECTIVE_2__", "# r" + "uff: noqa")
        .replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )


def test_append_comment_rebuilds_ast_walk() -> None:
    """Derived comment blocks remain in sync when comments are appended."""
    tree: CommentedModule = CommentedModule.parse(source="")
    tree.comments.append(
        SingleLineComment(text="# new", inline=False, lineno=1, col_offset=0),
    )
    expect_equal(actual=tree.unparse(), expected="# new")
    expect_equal(
        actual=[
            node.text for node in walk(node=tree) if isinstance(node, Comment)
        ],
        expected=["# new"],
    )


def test_edit_structured_noqa_rules_then_emit_twice() -> None:
    """Editing suppression rule nodes rewrites tokens and is idempotent."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    directive: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    directive.rules[0].code = "F401"
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: F401
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: F401
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )


def test_edit_type_ignore_rule_and_standard_ast() -> None:
    """A modified type-ignore updates type_ignores as well as comment text."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_3__[assignment]
""".replace("__ASTART_FIXTURE_DIRECTIVE_3__", "# t" + "ype: ignore"),
    )
    directive: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    directive.rules[0].code = "arg-type"
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_3__[arg-type]
""".replace("__ASTART_FIXTURE_DIRECTIVE_3__", "# t" + "ype: ignore"),
    )
    expect_equal(actual=tree.type_ignores[0].tag, expected="[arg-type]")


def test_edit_structured_pylint_rules() -> None:
    """Pylint rule lists can change independently of lexical comment text."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# pylint: disable=missing-docstring
x = 1
""",
    )
    directive: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    directive.rules.append(SuppressionRule(code="unused-import"))
    expect_equal(
        actual=tree.unparse(),
        expected="""\
# pylint: disable=missing-docstring, unused-import
x = 1
""",
    )


def test_repeated_docstring_emission_is_idempotent() -> None:
    """Structured docstring edits do not conflict with their first emission."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    \"""Old.\"""
    pass
""",
    )
    tree.docstrings[0].summary = "New."
    result: str = tree.unparse()
    expect_equal(actual=tree.unparse(), expected=result)


def test_directly_modified_docstring_without_structured_edit() -> None:
    """Direct AST editing works while semantic fields stay intact."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    \"""Old.\"""
    pass
""",
    )
    expect_constant_expr(
        value=expression_of_stmt(
            value=expect_suite_node(value=tree.body[0]).body[0],
        ),
    ).value = "New direct documentation."
    expect_in(item="New direct documentation.", container=tree.unparse())


def test_header_comments_across_styles_and_rewrite() -> None:
    """All recognized suppression types are preserved when code mutates."""
    source: str = (
        """\
# fmt: off
__ASTART_FIXTURE_DIRECTIVE_4__: E501
# pragma: no cover
# fmt: on
x=1
"""
    ).replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_value_stmt(value=tree.body[0]).value = Constant(value=2)
    transformed: str = tree.unparse()
    for comment in tree.comments:
        expect_equal(actual=transformed.count(comment.text), expected=1)
    expect_true(
        condition=transformed.endswith("""\
x = 2
"""),
    )


def test_no_false_positive_suppression() -> None:
    """Narrative text with lint-related words remains an ordinary comment."""
    for source in (
        """\
__ASTART_FIXTURE_DIRECTIVE_4__ should be added here
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
        """\
# pylint issues ahead
""",
        """\
# isort works on imports
""",
    ):
        tree: CommentedModule = CommentedModule.parse(source=source)
        expect_instance(value=tree.comments[0], kind=SingleLineComment)


def test_comment_group_blank_lines_survive_code_edits() -> None:
    """Keep one- and two-blank-line separators in reconstructed comments."""
    source: str = """\
# line1

# line3
# line4


# line7
x = 1
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_value_stmt(value=tree.body[0]).value = Constant(value=2)
    expect_equal(
        actual=tree.unparse(),
        expected=source.replace("x = 1", "x = 2"),
    )


def test_pep257_layout_nodes_are_traversable() -> None:
    """PEP 257 structural conventions remain inspectable AST children."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    \"""First sentence.

    Another paragraph.
    \"""
    pass
""",
    )
    layout: DocstringLayout = tree.docstrings[0].layout
    expect_false(condition=layout.is_one_line)
    expect_true(condition=layout.has_blank_after_summary)
    expect_true(condition=layout.summary_has_period)
    expect_equal(
        actual=len(
            [node for node in walk(node=tree) if type(node) is type(layout)],
        ),
        expected=1,
    )


def test_docstrings_in_conditional_definitions() -> None:
    """Discover docstrings for definitions inside arbitrary Python suites."""
    source: str = dedent(
        text=(
            """\
    if flag:
        def nested(value):
            \"""Nested documentation.\"""
            return value
    """
        ),
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(actual=len(tree.docstrings), expected=1)
    expect_equal(
        actual=tree.docstrings[0].summary,
        expected="Nested documentation.",
    )
    expect_equal(actual=tree.unparse(), expected=source)


def test_linked_argument_and_return_types_follow_ast_renames() -> None:
    """Stable AST references let documented names and types synchronize."""
    tree: CommentedModule = CommentedModule.parse(
        source=dedent(
            text="""\
    def f(previous: int) -> int:
        \"""Compute.

        Args:
            previous (int): Input.
        Returns:
            int: Output.
        \"""
        return previous
    """,
        ),
    )
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    function.args.args[0].arg = "updated"
    function.args.args[0].annotation = Constant(value="Text")
    function.returns = Constant(value="Text")
    doc: DocstringNode = tree.docstrings[0]
    doc.synchronize_symbols(include_types=True)
    expect_equal(
        actual=doc.entries(kind="parameters")[0].name,
        expected="updated",
    )
    expect_equal(
        actual=doc.entries(kind="parameters")[0].type_name,
        expected="'Text'",
    )
    expect_equal(
        actual=doc.entries(kind="returns")[0].type_name,
        expected="'Text'",
    )
    expect_in(item="updated ('Text')", container=tree.unparse())


def test_suppression_trailing_explanation_survives_rule_edit() -> None:
    """Retain commentary after a suppressed diagnostic when editing codes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501  # generated input
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    comment: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    comment = expect_instance(value=comment, kind=SuppressionComment)
    comment.rules[0].code = "F401"
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: F401  # generated input
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )


def test_group_has_ast_coordinates() -> None:
    """Multiline grouping exposes AST-style beginning and end coordinates."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# a
# b
""",
    )
    block: MultilineComment = expect_instance(
        value=tree.comment_blocks[0],
        kind=MultilineComment,
    )
    expect_equal(actual=block.lineno, expected=1)
    expect_equal(actual=block.end_lineno, expected=2)
    expect_equal(actual=block.end_col_offset, expected=len("# b"))


def test_unknown_section_remains_accessible_and_conversion_fails_closed() -> (
    None
):
    """Unknown sections remain raw and cannot disappear in style conversion."""
    node: DocstringNode = parse_docstring(
        source="""\
Summary.

Customs:
    Preserve proprietary syntax.""",
    )
    expect_equal(actual=node.style, expected="pep257")
    expect_equal(
        actual=node.description,
        expected="""\
Customs:
    Preserve proprietary syntax.""",
    )
    numpy_doc: DocstringNode = parse_docstring(
        source="""\
Summary.

Customs
-------
secret markup""",
    )
    expect_equal(actual=numpy_doc.sections[0].kind, expected="unknown")
    expect_true(
        condition=numpy_doc.render(style="numpy").endswith("""\
Customs
-------
secret markup"""),
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="cannot be converted losslessly",
    ):
        numpy_doc.render(style="google")


def test_pep257_format_with_sections_retains_structured_parseability() -> None:
    """PEP 257 conversion can use Google fields without losing semantics."""
    doc: DocstringNode = parse_docstring(
        source="""\
Summary.

Args:
    value (int): Data.""",
    )
    converted: DocstringNode = parse_docstring(
        source=doc.render(style="pep257"),
    )
    expect_equal(
        actual=converted.entries(kind="parameters")[0].name,
        expected="value",
    )


def test_numpy_comma_separated_parameters_link_individually() -> None:
    """One NumPy declaration can document multiple named Python arguments."""
    source: str = dedent(
        text="""\
    def add(x: int, y: int) -> list[int]:
        \"""Add.

        Parameters
        ----------
        x, y : int
            Two operands.

        Returns
        -------
        list[int]
            Collection of results.
        \"""
        return [x + y]
    """,
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    document: DocstringNode = tree.docstrings[0]
    expect_equal(
        actual=[e.name for e in document.entries(kind="parameters")],
        expected=["x", "y"],
    )
    expect_true(
        condition=all(
            e.target is not None for e in document.entries(kind="parameters")
        ),
    )
    expect_equal(
        actual=document.entries(kind="returns")[0].type_name,
        expected="list[int]",
    )


def test_sphinx_typed_param_field() -> None:
    """Sphinx's inline type/name parameter syntax yields separate types."""
    document: DocstringNode = parse_docstring(
        source="""\
Summary.

:param list[int] values: Input sequence.""",
    )
    entry: DocEntry = document.entries(kind="parameters")[0]
    expect_equal(actual=entry.name, expected="values")
    expect_equal(actual=entry.type_name, expected="list[int]")
    expect_equal(actual=entry.description, expected="Input sequence.")


def test_raw_suppression_edits_reclassify_rule_nodes() -> None:
    """Editing raw suppression text updates the normalized diagnostic codes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: E501
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    comment: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    comment = expect_instance(value=comment, kind=SuppressionComment)
    comment.text = "__ASTART_FIXTURE_DIRECTIVE_4__: F401".replace(
        "__ASTART_FIXTURE_DIRECTIVE_4__",
        "# n" + "oqa",
    )
    expect_equal(
        actual=tree.unparse(),
        expected="""\
x = 1  __ASTART_FIXTURE_DIRECTIVE_4__: F401
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    expect_equal(
        actual=[item.code for item in comment.rules],
        expected=["F401"],
    )


def test_raw_suppression_cannot_downgrade_to_prose() -> None:
    """A suppression cannot silently lose semantic meaning on text edits."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
__ASTART_FIXTURE_DIRECTIVE_4__
x = 1
""".replace("__ASTART_FIXTURE_DIRECTIVE_4__", "# n" + "oqa"),
    )
    tree.comments[0].text = "# ordinary comment"
    with pytest.raises(
        expected_exception=TypeError,
        match="no longer a directive",
    ):
        tree.unparse()


def test_refresh_docstrings_detects_new_definitions() -> None:
    """Structural insertions can rebuild the associated semantic doc view."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x = 1
""",
    )
    tree.body.append(
        FunctionDef(
            name="added",
            args=arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[Expr(value=Constant(value="New documentation.")), Pass()],
            decorator_list=[],
            returns=None,
            type_comment=None,
        ),
    )
    tree.refresh_docstrings()
    expect_equal(actual=len(tree.docstrings), expected=1)
    expect_equal(
        actual=tree.docstrings[0].summary,
        expected="New documentation.",
    )
    expect_in(item="New documentation.", container=tree.unparse())


def test_refresh_docstrings_rejects_unapplied_edit() -> None:
    """Refreshing should never discard a pending semantic field mutation."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    \"""Old.\"""
    pass
""",
    )
    tree.docstrings[0].summary = "New."
    with pytest.raises(
        expected_exception=ValueError,
        match="Apply structured",
    ):
        tree.refresh_docstrings()
