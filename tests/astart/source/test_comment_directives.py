"""Directive syntax becomes native comment metadata at token construction."""

from __future__ import annotations

from ast import walk
from typing import TYPE_CHECKING

import pytest
from astart import parse
from astart.docstrings.wrapping import WrapChanges, WrapSettings, wrap_tree
from astart.source.ast import (
    CommentControl,
    SingleLineComment,
    SuppressionComment,
)
from astart.source.comment_directives import DirectiveParser

from tests.support.expectations import expect_equal, expect_in, expect_instance

if TYPE_CHECKING:
    from astart import CommentedModule


@pytest.mark.parametrize(
    argnames=("body", "tool", "action", "scope", "codes"),
    argvalues=[
        (
            "noqa: E501, F401 # reason",
            "flake8/ruff",
            "ignore",
            "line",
            ("E501", "F401"),
        ),
        ("RUFF : NOQA: E501", "ruff", "ignore", "file", ("E501",)),
        (
            "pylint:disable=enable-feature",
            "pylint",
            "disable",
            "file",
            ("enable-feature",),
        ),
        (
            "local-checker:enable=old-rule",
            "local-checker",
            "enable",
            "file",
            ("old-rule",),
        ),
        (
            "type: ignore[assignment] # retained",
            "type",
            "ignore",
            "line",
            ("assignment",),
        ),
        (
            "pyright:ignore[reportArgumentType]",
            "pyright",
            "ignore",
            "line",
            ("reportArgumentType",),
        ),
        ("basedpyright: ignore", "basedpyright", "ignore", "line", ()),
        ("fmt:off", "fmt", "off", "block", ()),
        ("autopep8: on", "autopep8", "on", "block", ()),
        ("isort:skip_file", "isort", "skip", "file", ()),
        ("coverswitch:skip", "coverage", "skip", "line", ()),
        ("pragma: no cover", "coverage", "ignore", "line", ()),
        ("pragma: nomutate", "coverage", "skip", "line", ()),
        ("nosec: B101, B102", "bandit", "ignore", "line", ("B101", "B102")),
        (
            "sourcery skip: refactor-one",
            "sourcery",
            "skip",
            "line",
            ("refactor-one",),
        ),
        ("xenon: ignore", "xenon", "ignore", "block", ()),
    ],
)
def test_directive_fields_are_derived_from_grammar(
    *,
    body: str,
    tool: str,
    action: str,
    scope: str,
    codes: tuple[str, ...],
) -> None:
    """Selectors and explanations cannot be confused with action keywords.

    Args:
        body (str): Comment-token directive payload.
        tool (str): Expected canonical tool.
        action (str): Expected action.
        scope (str): Expected applicability.
        codes (tuple[str, ...]): Exact native selector values.

    """
    source: str = f"# {body}\nx = 1\n"
    tree: CommentedModule = parse(source=source)
    node: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    expect_equal(
        actual=(node.tool, node.action, node.scope),
        expected=(tool, action, scope),
    )
    expect_equal(
        actual=tuple(rule.code for rule in node.rules),
        expected=codes,
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )


@pytest.mark.parametrize(
    argnames="body",
    argvalues=[
        "a prose mention of noqa",
        "noqax: E501",
        "noqa: invalid",
        "noqa: E501,",
        "pyright: ignored",
        "type: ignore[missing",
        "fmt: offshore",
    ],
)
def test_prose_and_invalid_prefixes_are_not_suppressions(*, body: str) -> None:
    """Parse actual grammar boundaries rather than word substrings.

    Args:
        body (str): Ordinary or malformed control-like prose.

    """
    tree: CommentedModule = parse(source=f"# {body}\nx=1\n")
    expect_instance(value=tree.comments[0], kind=SingleLineComment)


def test_wrapping_consumes_native_control_nodes(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Already parsed controls need no source-pattern scan in the wrapper.

    Args:
        monkeypatch (pytest.MonkeyPatch): Local parser-boundary guard.

    """
    source: str = """\
# coding: utf-8
# region generated
# fmt: off
x=1
"""
    tree: CommentedModule = parse(source=source)
    controls: list[CommentControl] = [
        node for node in walk(node=tree) if isinstance(node, CommentControl)
    ]
    expect_equal(
        actual=[node.kind for node in controls],
        expected=["encoding", "region"],
    )

    def reject_reparse(_self: DirectiveParser) -> None:
        """Reject reparsing already classified directive contents.

        Args:
            _self (DirectiveParser): Existing parser instance, if incorrectly
                constructed.

        """
        pytest.fail(reason="wrapping reparsed an existing comment control")

    monkeypatch.setattr(
        target=DirectiveParser,
        name="parse",
        value=reject_reparse,
    )
    result: WrapChanges = wrap_tree(tree=tree, settings=WrapSettings())
    expect_equal(actual=result.comment_blocks_changed, expected=0)


def test_semantic_directive_edit_preserves_explanation_and_form() -> None:
    """Rendering reads AST fields, including coverage syntax family."""
    tree: CommentedModule = parse(
        source="""\
# NoQa: E501 # why
x=1
""",
    )
    node: SuppressionComment = expect_instance(
        value=tree.comments[0],
        kind=SuppressionComment,
    )
    node.rules[0].code = "F401"
    expect_in(
        item="noqa: F401 # why",
        container=tree.unparse(preserve_formatting=True),
    )
    tree = parse(
        source="""\
# COVERSWITCH: skip
x=1
""",
    )
    node = expect_instance(value=tree.comments[0], kind=SuppressionComment)
    expect_equal(actual=node.render(), expected="# coverswitch: skip")
