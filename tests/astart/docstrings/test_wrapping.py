"""Native wrapping preserves executable syntax and lexical boundaries."""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    Module,
    dump,
    get_docstring,
    parse,
    walk,
)
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from astart.docstrings.prose import balanced_lines, reflow_text
from astart.docstrings.wrapping import (
    WrapChanges,
    WrapResult,
    WrapSettings,
    wrap_source,
    wrap_tree,
)
from astart.source.ast import Comment, CommentedModule, SingleLineComment
from astart.source.formatting import FormatPreserver, Patch

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_true,
)

if TYPE_CHECKING:
    from astart.docstrings import DocstringNode, DocSummary


def _executable(*, source: str) -> str:
    """Provide an independent test oracle excluding documentation.

    Args:
        source (str): Source to inspect in the test, outside the production
            path.

    Returns:
        str: Position-independent executable structure.

    """
    tree: Module = parse(source=source)
    for node in walk(node=tree):
        if (
            isinstance(
                node,
                (Module, ClassDef, FunctionDef, AsyncFunctionDef),
            )
            and get_docstring(node=node) is not None
        ):
            node.body.pop(0)
    return dump(node=tree)


def test_wrapping_parses_input_once_and_preserves_code() -> None:
    """One parse, one edit batch, exact untouched code and Unicode values."""
    source: str = (
        'def café( x = "é" ):\n'
        '    """This is a long explanation with many words that should be '
        "wrapped without changing the executable statements.\n\n"
        '    Raises:\n        ValueError: TODO.\n    """\n'
        "    return  x  # keep trailing comment\n"
    )
    with patch.object(
        target=CommentedModule,
        attribute="parse",
        wraps=CommentedModule.parse,
    ) as parser:
        result: WrapResult = wrap_source(
            source=source,
            settings=WrapSettings(line_length=50),
        )
        expect_equal(actual=parser.call_count, expected=1)
    expect_equal(
        actual=_executable(source=result.source),
        expected=_executable(source=source),
    )
    expect_in(item='def café( x = "é" ):', container=result.source)
    expect_in(
        item="    return  x  # keep trailing comment",
        container=result.source,
    )
    expect_in(item="ValueError: TODO.", container=result.source)
    expect_equal(actual=result.docstrings_changed, expected=1)
    expect_equal(
        actual=wrap_source(
            source=result.source,
            settings=WrapSettings(line_length=50),
        ).source,
        expected=result.source,
    )


def test_comment_reflow_keeps_directives_code_and_crlf() -> None:
    """Only standalone prose changes; directives and code comments survive."""
    source: str = (
        "#!/usr/bin/env python\r\n"
        "# coding: utf-8\r\n"
        "# This is an extended prose comment that must be wrapped into "
        "several lines while preserving all its words.\r\n"
        "# fmt: off\r\n"
        "# x = call(argument)\r\n"
        "x  = 1  # unchanged inline text\r\n"
    )
    result: WrapResult = wrap_source(
        source=source,
        settings=WrapSettings(line_length=45),
    )
    expect_in(
        item="""\
# coding: utf-8\r
""",
        container=result.source,
    )
    expect_in(
        item="""\
# fmt: off\r
""",
        container=result.source,
    )
    expect_in(
        item="""\
# x = call(argument)\r
""",
        container=result.source,
    )
    expect_in(
        item="""\
x  = 1  # unchanged inline text\r
""",
        container=result.source,
    )
    expect_true(
        condition="\n"
        not in result.source.replace(
            """\
\r
""",
            "",
        ),
    )
    expect_equal(actual=result.comment_blocks_changed, expected=1)


def test_explicit_structural_options_use_header_tokens() -> None:
    """Lambda defaults and generic parameters cannot confuse the colon."""
    source: str = (
        "def f[T](x: T, g=lambda: 2):\n"
        '    """TODO."""\n'
        "    pass\n\n"
        "async def other():\n"
        "    pass\n"
    )
    result: WrapResult = wrap_source(
        source=source,
        settings=WrapSettings(
            add_return_none=True,
            remove_pass=True,
            boilerplate=True,
        ),
    )
    expect_in(item="g=lambda: 2) -> None:", container=result.source)
    expect_in(item="async def other() -> None:", container=result.source)
    expect_equal(actual=len(parse(source=result.source).body), expected=2)
    expect_equal(
        actual=[
            get_docstring(node=node)
            for node in parse(source=result.source).body
            if isinstance(node, (FunctionDef, AsyncFunctionDef))
        ],
        expected=["TODO.", "TODO."],
    )


def test_code_fences_doctests_and_literal_blocks_are_protected() -> None:
    """Protected regions bypass line breaking even when wider than budget."""
    text: str = (
        'Examples:\n    >>> a = "very long code example left intact"\n'
        "    expected output with its original   spacing\n\n"
        "Notes:\nA paragraph that needs wrapping across several short lines.\n"
        '```python\nx = "this code stays in its original long line"\n```\n'
        "Literal::\n\n    arbitrary literal   spacing remains unchanged\n"
    )
    result: str = reflow_text(text=text, width=25)
    expect_in(
        item='    >>> a = "very long code example left intact"',
        container=result,
    )
    expect_in(
        item="    expected output with its original   spacing",
        container=result,
    )
    expect_in(
        item='x = "this code stays in its original long line"',
        container=result,
    )
    expect_in(
        item="    arbitrary literal   spacing remains unchanged",
        container=result,
    )


def test_balanced_wrapping_preserves_inline_code_and_hanging_lists() -> None:
    """Word order and indivisible code spans survive optimal line breaking."""
    result: list[str] = balanced_lines(
        text="alpha beta `an inline code span` gamma delta epsilon",
        width=22,
    )
    expect_in(
        item="`an inline code span`",
        container="\n".join(result),
    )
    expect_equal(
        actual=" ".join(result),
        expected="alpha beta `an inline code span` gamma delta epsilon",
    )
    wrapped: str = reflow_text(
        text="10) A numbered paragraph with enough words to wrap twice.",
        width=28,
    )
    expect_true(condition=wrapped.startswith("10. "))
    expect_true(
        condition=all(
            line.startswith("    ") for line in wrapped.splitlines()[1:]
        ),
    )


def test_overlapping_lexical_edits_are_rejected() -> None:
    """A failed edit plan cannot silently corrupt the original source."""
    with pytest.raises(expected_exception=ValueError, match="Overlapping"):
        FormatPreserver.apply(
            source="abcdef",
            begin=0,
            end=6,
            patches=[
                Patch(start=1, end=4, text="x"),
                Patch(start=3, end=5, text="y"),
            ],
        )


def test_wrap_tree_mutates_native_nodes_without_parsing() -> None:
    """Edit the authoritative AST without reading source again."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            "# This is a long comment with enough words "
            "to require several lines.\n"
            'def f():\n    """A summary with enough prose to need line breaks '
            'while keeping the same structured documentation node."""\n'
            "    return 2\n"
        ),
    )
    document: DocstringNode = tree.docstrings[0]
    summary: DocSummary = document.summary_node
    comment: Comment = tree.comments[0]
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        changes: WrapChanges = wrap_tree(
            tree=tree,
            settings=WrapSettings(line_length=35),
        )
    expect_equal(actual=changes.docstrings_changed, expected=1)
    expect_equal(actual=changes.comment_blocks_changed, expected=1)
    expect_true(condition=tree.docstrings[0] is document)
    expect_true(condition=document.summary_node is summary)
    expect_true(condition=tree.comments[0] is comment)
    expect_true(condition=len(tree.comments) > 1)
    expect_true(
        condition="\n" in summary.text,
    )
    emitted: str = tree.unparse(preserve_formatting=True)
    expect_equal(actual=len(parse(source=emitted).body), expected=1)


def test_partial_shared_comment_replacement_is_atomic() -> None:
    """Reflowed anchors cannot be partially merged with another block."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
# first
# second
# third
x=1
""",
    )
    a: SingleLineComment = expect_instance(
        value=tree.comments[0],
        kind=SingleLineComment,
    )
    b: SingleLineComment = expect_instance(
        value=tree.comments[1],
        kind=SingleLineComment,
    )
    c: SingleLineComment = expect_instance(
        value=tree.comments[2],
        kind=SingleLineComment,
    )
    tree.replace_comment_lines(
        comments=(a, b),
        lines=("# new first", "# new second"),
    )
    before: tuple[str, ...] = tuple(node.text for node in tree.comments)
    with pytest.raises(expected_exception=ValueError, match="shared"):
        tree.replace_comment_lines(comments=(b, c), lines=("# merged",))
    expect_equal(
        actual=tuple(node.text for node in tree.comments),
        expected=before,
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
# new first
# new second
# third
x=1
""",
    )


def test_docstring_moves_relink_existing_nodes_to_new_owners() -> None:
    """Retain doc identities while repairing changed executable ownership."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            'def f(x):\n    """First.\n\n    Args:\n        x: TODO.\n'
            '    """\n    return x\n'
            'def g(y):\n    """Second.\n\n    Args:\n        y: TODO.\n'
            '    """\n    return y\n'
        ),
    )
    first: DocstringNode = tree.docstrings[0]
    second: DocstringNode = tree.docstrings[1]
    f: FunctionDef = expect_instance(value=tree.body[0], kind=FunctionDef)
    g: FunctionDef = expect_instance(value=tree.body[1], kind=FunctionDef)
    f.body[0], g.body[0] = g.body[0], f.body[0]
    tree.index_docstrings()
    expect_true(condition=first.owner is g)
    expect_true(condition=second.owner is f)
    expect_true(condition=first in tree.docstrings)
    expect_true(condition=second in tree.docstrings)
    expect_true(condition=first.entries()[0].target is None)
    expect_true(condition=second.entries()[0].target is None)


def test_docstring_moves_to_module_reclassify_and_clear_targets() -> None:
    """The module-doc view and semantic links follow real ownership moves."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            '"""Module."""\n'
            'def f(x):\n    """Function.\n\n    Args:\n        x: TODO.\n'
            '    """\n    return x\n'
        ),
    )
    first: DocstringNode = tree.docstrings[0]
    second: DocstringNode = tree.docstrings[1]
    function: FunctionDef = expect_instance(
        value=tree.body[1],
        kind=FunctionDef,
    )
    tree.body[0], function.body[0] = function.body[0], tree.body[0]
    tree.index_docstrings()
    expect_true(condition=tree.module_docstring is second)
    expect_true(condition=first.owner is function)
    expect_true(condition=second.owner is None)
    expect_true(condition=second.entries()[0].target is None)
