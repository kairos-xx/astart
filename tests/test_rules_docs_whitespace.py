"""Tests for the DOC/WSP/Constants standalone rule detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart import parse
from astart.rules.constants_grouping import find_loose_constants
from astart.rules.docs_missing import find_missing_docstrings
from astart.rules.docs_missing_raises import find_missing_raises
from astart.rules.docs_missing_returns import find_missing_returns
from astart.rules.docs_stale_params import find_stale_parameters
from astart.rules.whitespace_rules import (
    find_blank_line_runs,
    find_trailing_space,
)

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from collections.abc import Callable

    from astart.rules.procedural import Candidate


@final
class Constants:
    """Group module-level constants.

    Attributes:
        undocumented: Definitions without docstrings.
        stale_params: Docstring naming a removed parameter.
        missing_returns: Documented function returning undocumented.
        missing_raises: Documented function raising undocumented.
        whitespace: Blank runs and trailing space.
        loose_constants: Module constants outside a Constants class.

    """

    undocumented: Final[str] = (
        "def public_fn(a):\n    return a\n"
        "def _private():\n    return 1\n"
        "class Open:\n    pass\n"
    )
    stale_params: Final[str] = (
        "def f(a, b):\n"
        '    """Do.\n\n'
        "    Args:\n"
        "        a: kept.\n"
        "        gone: removed.\n"
        '    """\n'
        "    return a + b\n"
    )
    missing_returns: Final[str] = (
        "def f():\n"
        '    """Give a number.\n\n'
        "    Args:\n"
        "        none-arg: x.\n"
        '    """\n'
        "    return 1\n"
        "def g():\n"
        '    """Give.\n\n'
        "    Returns:\n"
        "        The value.\n"
        '    """\n'
        "    return 2\n"
    )
    missing_raises: Final[str] = (
        "def f(x):\n"
        '    """Do.\n\n'
        "    Raises:\n"
        "        ValueError: documented.\n"
        '    """\n'
        "    if x:\n"
        '        raise ValueError("x")\n'
        '    raise KeyError("k")\n'
    )
    whitespace: Final[str] = "x = 1\n\n\n\n\ny = 2  \nz = 3\n"
    loose_constants: Final[str] = (
        "LIMIT = 10\n"
        "name = 'x'\n"
        "OTHER: int = 5\n"
        "__all__ = ['x']\n\n"
        "class Constants:\n"
        "    INNER = 1\n"
    )


def _candidates(
    func: Callable[..., tuple[Candidate, ...]],
    source: str,
) -> tuple[Candidate, ...]:
    """Run a module-level detector on source text.

    Args:
        func: Detector taking ``module`` and ``filename`` keywords.
        source: Module source text.

    Returns:
        The detector's candidates.

    """
    return func(
        module=parse(source=source, filename="t.py"),
        filename="t.py",
    )


def test_doc001_flags_undocumented() -> None:
    """Public definitions without docstrings are flagged."""
    hits: tuple[Candidate, ...] = _candidates(
        func=find_missing_docstrings,
        source=Constants.undocumented,
    )
    subjects: list[str] = [str(object=hit.evidence["subject"]) for hit in hits]
    expect_true(condition="public_fn" in subjects)
    expect_true(condition="Open" in subjects)
    expect_true(condition="<module>" in subjects)
    expect_true(condition="_private" not in subjects)


def test_doc003_flags_stale_parameter() -> None:
    """A documented name missing from the signature is flagged."""
    hits: tuple[Candidate, ...] = _candidates(
        func=find_stale_parameters,
        source=Constants.stale_params,
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0].evidence["parameters"],
        expected=["gone"],
    )


def test_doc003_clean_signature_quiet() -> None:
    """Docstrings matching the signature stay quiet."""
    source: str = (
        "def f(a):\n"
        '    """Do.\n\n'
        "    Args:\n"
        "        a: kept.\n"
        '    """\n'
        "    return a\n"
    )
    expect_equal(
        actual=_candidates(func=find_stale_parameters, source=source),
        expected=(),
    )


def test_doc004_flags_missing_returns() -> None:
    """A value-returning documented function is flagged."""
    hits: tuple[Candidate, ...] = _candidates(
        func=find_missing_returns,
        source=Constants.missing_returns,
    )
    subjects: list[str] = [
        str(object=hit.evidence["function"]) for hit in hits
    ]
    expect_true(condition="f" in subjects)
    expect_true(condition="g" not in subjects)


def test_doc006_flags_missing_raises() -> None:
    """An undocumented raise is flagged; documented stays quiet."""
    hits: tuple[Candidate, ...] = _candidates(
        func=find_missing_raises,
        source=Constants.missing_raises,
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(
        actual=hits[0].evidence["exceptions"],
        expected=["KeyError"],
    )


def test_wsp001_flags_blank_runs() -> None:
    """Three-plus blank lines are flagged once per run."""
    hits: tuple[Candidate, ...] = find_blank_line_runs(
        source=Constants.whitespace,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].span.start_line, expected=4)


def test_wsp002_flags_trailing_space() -> None:
    """Lines ending in whitespace are flagged."""
    hits: tuple[Candidate, ...] = find_trailing_space(
        source=Constants.whitespace,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].span.start_line, expected=6)


def test_constants_grouping_flags_loose() -> None:
    """Loose UPPER_SNAKE assignments are flagged; grouped are not."""
    hits: tuple[Candidate, ...] = _candidates(
        func=find_loose_constants,
        source=Constants.loose_constants,
    )
    subjects: list[str] = [
        str(object=hit.evidence["constant"]) for hit in hits
    ]
    expect_equal(actual=sorted(subjects), expected=["LIMIT", "OTHER"])
