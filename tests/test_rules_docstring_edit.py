"""Pure text edits for Google-style docstrings."""

from __future__ import annotations

from textwrap import dedent
from typing import Final, final

from astart.rules.docstring_edit import (
    add_parameter_entries,
    remove_parameter_entries,
    tidy_docstring,
)

from tests.expectations import expect_equal, expect_in


@final
class Constants:
    """Constants for the test.

    Attributes:
        ind: Indentation prefix re-applied to docstring body lines.

    """

    ind: Final[str] = "    "


def _doc(*, text: str) -> str:
    """Build a docstring value the way the parser stores it.

    Args:
        text: Dedented docstring body.

    Returns:
        The stored docstring value.

    """
    lines: list[str] = dedent(text=text).strip("\n").split(sep="\n")
    body: list[str] = [
        lines[0],
        *((Constants.ind + line) if line else "" for line in lines[1:]),
    ]
    return "\n".join(body) + "\n" + Constants.ind


def test_missing_entry_is_appended_in_signature_order() -> None:
    """Check that a new entry lands after its predecessor."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            a: First.
            c: Third.
        """,
    )
    out: str = add_parameter_entries(
        doc=doc,
        names=("b",),
        order=("a", "b", "c"),
        indent=Constants.ind,
    )
    expect_in(
        item="a: First.\n"
        + Constants.ind * 2
        + "b: Describe b.\n"
        + Constants.ind * 2
        + "c: Third.",
        container=out,
    )


def test_entry_before_all_others_goes_first() -> None:
    """Check that a leading parameter is inserted before the first entry."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            b: Second.
        """,
    )
    out: str = add_parameter_entries(
        doc=doc,
        names=("a",),
        order=("a", "b"),
        indent=Constants.ind,
    )
    expect_in(
        item="Args:\n" + Constants.ind * 2 + "a: Describe a.\n",
        container=out,
    )


def test_missing_section_is_created_before_returns() -> None:
    """Check that an Args section is created ahead of Returns."""
    doc: str = _doc(
        text="""
        Run.

        Returns:
            Nothing.
        """,
    )
    out: str = add_parameter_entries(
        doc=doc,
        names=("a",),
        order=("a",),
        indent=Constants.ind,
    )
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        Args:
            a: Describe a.

        Returns:
            Nothing.
        """,
        ),
    )


def test_missing_section_is_appended_when_nothing_follows() -> None:
    """Check that a section is added at the end of a prose docstring."""
    doc: str = _doc(
        text="""
        Run.

        More prose.
        """,
    )
    out: str = add_parameter_entries(
        doc=doc,
        names=("a",),
        order=("a",),
        indent=Constants.ind,
    )
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        More prose.

        Args:
            a: Describe a.
        """,
        ),
    )


def test_one_line_docstring_becomes_multiline() -> None:
    """Check that ``Run.`` grows an Args section."""
    out: str = add_parameter_entries(
        doc="Run.",
        names=("a",),
        order=("a",),
        indent=Constants.ind,
    )
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        Args:
            a: Describe a.
        """,
        ),
    )


def test_star_parameters_keep_their_stars() -> None:
    """Check that ``*args`` is written with its star."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            a: First.
        """,
    )
    out: str = add_parameter_entries(
        doc=doc,
        names=("*args", "**kwargs"),
        order=("a", "args", "kwargs"),
        indent=Constants.ind,
    )
    expect_in(item="*args: Describe args.", container=out)
    expect_in(item="**kwargs: Describe kwargs.", container=out)


def test_stale_entry_and_its_continuation_are_removed() -> None:
    """Check that a removed entry takes its continuation lines along."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            a: First
                continued here.
            gone: Old.
            c: Third.
        """,
    )
    out: str = remove_parameter_entries(doc=doc, names=("gone",))
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        Args:
            a: First
                continued here.
            c: Third.
        """,
        ),
    )


def test_removing_the_last_entry_removes_the_section() -> None:
    """Check that an emptied Args section disappears."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            gone: Old.

        Returns:
            Value.
        """,
    )
    out: str = remove_parameter_entries(doc=doc, names=("gone",))
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        Returns:
            Value.
        """,
        ),
    )


def test_removing_the_only_section_leaves_the_summary() -> None:
    """Check that no blank line is left before the closing quotes."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            gone: Old.
        """,
    )
    out: str = remove_parameter_entries(doc=doc, names=("gone",))
    expect_equal(actual=out, expected="Run.\n" + Constants.ind)


def test_star_names_match_without_their_stars() -> None:
    """Check that ``*args`` is removed when asked for ``args``."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            a: First.
            *args: Extra.
        """,
    )
    out: str = remove_parameter_entries(doc=doc, names=("args",))
    expect_equal(
        actual=out,
        expected=_doc(
            text="""
        Run.

        Args:
            a: First.
        """,
        ),
    )


def test_tidy_strips_trailing_space_and_collapses_blank_runs() -> None:
    """Check trailing whitespace and repeated blank lines."""
    messy: str = (
        "Run.   \n\n\n\n" + Constants.ind + "More.  \n\n\n" + Constants.ind
    )
    expect_equal(
        actual=tidy_docstring(doc=messy, indent=Constants.ind),
        expected="Run.\n\n" + Constants.ind + "More.\n" + Constants.ind,
    )


def test_tidy_reindents_the_body() -> None:
    """Check that an over- or under-indented body is aligned."""
    messy: str = "Run.\n\n  Args:\n      a: First.\n  "
    out: str = tidy_docstring(doc=messy, indent=Constants.ind)
    expect_equal(
        actual=out,
        expected="Run.\n\n"
        + Constants.ind
        + "Args:\n"
        + Constants.ind
        + "    a: First.\n"
        + Constants.ind,
    )


def test_tidy_is_idempotent_and_leaves_clean_text_alone() -> None:
    """Check the fixed point."""
    clean: str = _doc(
        text="""
        Run.

        Args:
            a: First.
        """,
    )
    expect_equal(
        actual=tidy_docstring(doc=clean, indent=Constants.ind),
        expected=clean,
    )
    once: str = tidy_docstring(doc="Run.  \n\n\n  x\n ", indent=Constants.ind)
    expect_equal(
        actual=tidy_docstring(doc=once, indent=Constants.ind),
        expected=once,
    )


def test_tidy_leaves_a_one_line_docstring_alone() -> None:
    """Check that ``Run.`` is untouched."""
    expect_equal(
        actual=tidy_docstring(doc="Run.", indent=Constants.ind),
        expected="Run.",
    )
