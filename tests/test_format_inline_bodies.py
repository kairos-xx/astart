"""Inline bodies belong to their statement; real semicolons stay ambiguous."""

from __future__ import annotations

from ast import Import, alias, parse, stmt
from textwrap import dedent

import pytest
from astart.ast import CommentedModule
from astart.formatting import FormatPreservationError

from tests.expectations import expect_equal


def _insert_import(*, source: str) -> str:
    """Insert ``import os`` as the first statement and render.

    Args:
        source: Python source.

    Returns:
        The regenerated source with formatting preserved.

    """
    tree: CommentedModule = CommentedModule.parse(source=dedent(text=source))
    body: list[stmt] = tree.body
    body.insert(0, Import(names=[alias(name="os")]))
    text: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="raise",
    )
    parse(source=text)
    return text


@pytest.mark.parametrize(
    "source",
    [
        """\
X = 1


def f(): ...
""",
        """\
X = 1


class K: pass
""",
        """\
X = 1


if X: print(X)
""",
        """\
X = 1


while False: break
""",
    ],
)
def test_inline_body_does_not_block_a_neighbouring_insert(
    *,
    source: str,
) -> None:
    """Keep the one-line compound statement exactly as written.

    Args:
        source: Source with a one-line compound statement.

    """
    expect_equal(
        actual=_insert_import(source=source),
        expected="""\
import os
"""
        + source,
    )


def test_real_semicolon_statements_still_fail_closed() -> None:
    """Refuse to guess how to move statements that share a line."""
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="semicolon",
    ):
        _insert_import(
            source="""\
a = 1; b = 2
""",
        )


def test_semicolons_inside_an_inline_body_still_fail_closed() -> None:
    """Treat siblings in an inline body as sharing the line."""
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="semicolon",
    ):
        _insert_import(
            source="""\
if True: a = 1; b = 2
""",
        )
