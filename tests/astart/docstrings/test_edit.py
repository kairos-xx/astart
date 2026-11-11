"""Pure text edits for Google-style docstrings."""

from __future__ import annotations

from textwrap import dedent
from typing import Final, final

from astart.docstrings.edit import (
    add_parameter_entries,
    entry_names,
    remove_parameter_entries,
    tidy_docstring,
)

from tests.support.expectations import expect_equal, expect_in, expect_not_in


@final
class Constants:
    """Constants for the test.

    Attributes:
        ind (Final[str]): Indentation prefix re-applied to docstring body
            lines.

    """

    ind: Final[str] = "    "


def _doc(*, text: str) -> str:
    """Build a docstring value the way the parser stores it.

    Args:
        text (str): Dedented docstring body.

    Returns:
        str: The stored docstring value.

    """
    lines: list[str] = (
        dedent(text=text)
        .strip("\n")
        .split(
            sep="\n",
        )
    )
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
        item="""\
a: First.
"""
        + Constants.ind * 2
        + """\
b: Describe b.
"""
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
        item="""\
Args:
"""
        + Constants.ind * 2
        + """\
a: Describe a.
""",
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
    expect_equal(
        actual=out,
        expected="""\
Run.
"""
        + Constants.ind,
    )


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
        expected="""\
Run.

"""
        + Constants.ind
        + """\
More.

"""
        + Constants.ind,
    )


def test_tidy_reindents_the_body() -> None:
    """Check that an over- or under-indented body is aligned."""
    messy: str = """\
Run.

  Args:
      a: First.
  """
    out: str = tidy_docstring(doc=messy, indent=Constants.ind)
    expect_equal(
        actual=out,
        expected="""\
Run.

"""
        + Constants.ind
        + """\
Args:
"""
        + Constants.ind
        + """\
    a: First.

"""
        + Constants.ind,
    )


def test_tidy_is_idempotent_and_leaves_clean_text_alone() -> None:
    """Check the fixed point."""
    clean: str = (
        """\
Run.

"""
        + Constants.ind
        + """\
Args:
"""
        + Constants.ind
        + """\
    a: First.

"""
        + Constants.ind
    )
    expect_equal(
        actual=tidy_docstring(doc=clean, indent=Constants.ind),
        expected=clean,
    )
    once: str = tidy_docstring(
        doc="Run.  \n\n\n  x\n ",
        indent=Constants.ind,
    )
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


def test_tidy_attaches_detached_punctuation() -> None:
    """Check `` ``name`` . `` and ``word.  Next`` normalize."""
    doc: str = (
        """\
Run.

"""
        + Constants.ind
        + """\
Return strictly typed source for the given untyped ``source`` .
"""
        + Constants.ind
        + """\
The adapter is small.  All work lives in the API.

"""
        + Constants.ind
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(item="``source``.", container=out)
    expect_in(item="small. All work", container=out)
    expect_not_in(item="``source`` .", container=out)
    expect_not_in(item="small.  All", container=out)


def test_tidy_preserves_literal_block_spacing() -> None:
    """Check code inside ``::`` blocks is not punctuation-normalized."""
    doc: str = (
        """\
Run.

"""
        + Constants.ind
        + """\
Example::

"""
        + Constants.ind
        + """\
    result = func( a, b )
"""
        + Constants.ind
        + """\
    s = "a . b"

"""
        + Constants.ind
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(item="func( a, b )", container=out)
    expect_in(item='"a . b"', container=out)


def test_tidy_keeps_type_expressions_on_one_line() -> None:
    """Check bracketed type text is not split at inner spaces."""
    doc: str = (
        """\
Run.

"""
        + Constants.ind
        + """\
Attributes:
"""
        + Constants.ind
        + """\
    protocol_attributes (DictDictAnnAssign): Protocol attributes
"""
        + Constants.ind
        + """\
        supplied as dict[str, dict[str, AnnAssign]] for this
"""
        + Constants.ind
        + """\
        operation and how it flows through the pipeline stages
"""
        + Constants.ind
        + """\
        described at some length to force a wrap decision here.

"""
        + Constants.ind
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(item="dict[str, dict[str, AnnAssign]]", container=out)
    expect_not_in(
        item="""\
dict[str,
""",
        container=out,
    )


def test_tidy_avoids_widow_lines_when_wrapping() -> None:
    """Check a lone trailing word rejoins the previous line if it fits."""
    doc: str = (
        """\
Run.

"""
        + Constants.ind
        + "This is a fairly long line of prose that will need wrapping at "
        + """\
the margin and might otherwise leave contract.

"""
        + Constants.ind
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_not_in(
        item="""\

            contract.""",
        container=out,
    )


def test_tidy_pulls_entry_description_onto_label_line() -> None:
    """Check ``name (type):`` plus indented prose merges when it fits."""
    doc: str = (
        """\
Run.

"""
        + Constants.ind
        + """\
Args:
"""
        + Constants.ind
        + """\
    graph (ContractGraph):
"""
        + Constants.ind
        + "        Existing contracts over the authoritative module AST "
        + """\
nodes.
"""
        + Constants.ind
        + """\
    values (tuple[int, ...]):
"""
        + Constants.ind
        + """\
        The collected values for later inspection steps.

"""
        + Constants.ind
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(item="graph (ContractGraph): Existing contracts", container=out)
    expect_in(item="tuple[int, ...]): The collected values", container=out)
    expect_equal(
        actual=tidy_docstring(doc=out, indent=Constants.ind),
        expected=out,
    )


def test_entry_names_sees_nested_paren_types() -> None:
    """``tuple[()]`` inside ``name (type):`` must not hide the entry."""
    doc: str = _doc(
        text="""
        Update.

        Args:
            other (dict[str, int] | tuple[()]): Merge mapping.
            values: Extra values.
        """,
    )
    names: frozenset[str] = entry_names(doc=doc)
    expect_in(item="other", container=names)
    expect_in(item="values", container=names)


def test_tidy_compacts_type_label_when_spaced_label_cannot_fit() -> None:
    """A tight ``name (type):`` label falls back to compact type spacing."""
    doc: str = _doc(
        text="""
        Run.

        Args:
                owner (Module | FunctionDef | AsyncFunctionDef | ClassDef):
                    Candidate docstring owner.
        """,
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(
        item="owner (Module|FunctionDef|AsyncFunctionDef|ClassDef): Candidate",
        container=out,
    )
    expect_not_in(item="owner (Module | FunctionDef", container=out)
    expect_equal(
        actual=tidy_docstring(doc=out, indent=Constants.ind),
        expected=out,
    )


def test_tidy_drops_type_when_no_label_form_fits() -> None:
    """An entry keeps ``name:`` plus description when types never fit."""
    label: str = (
        "table (dict[str, tuple[tuple[str, ...], bool, "
        "tuple[str, ...], bool]]):"
    )
    doc: str = _doc(
        text=f"""
        Run.

        Args:
            {label}
                Accumulating signature table.
        """,
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(item="table: Accumulating signature table.", container=out)
    expect_not_in(item="table (dict[str", container=out)
    expect_equal(
        actual=tidy_docstring(doc=out, indent=Constants.ind),
        expected=out,
    )


def test_tidy_name_only_fallback_preserves_code_span() -> None:
    """``name:`` fallback still pulls a leading inline code span."""
    doc: str = _doc(
        text="""
        Run.

        Args:
            params (list[tuple[str, expr | None, bool]]):
                ``(name, annotation, is_kwonly)`` in signature order.
        """,
    )
    out: str = tidy_docstring(doc=doc, indent=Constants.ind)
    expect_in(
        item="params: ``(name, annotation, is_kwonly)`` in signature order.",
        container=out,
    )
    expect_equal(
        actual=tidy_docstring(doc=out, indent=Constants.ind),
        expected=out,
    )
