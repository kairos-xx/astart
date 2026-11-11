"""Tests for the standalone IMP001/SUP001/PRS001/TYP002 detectors."""

from __future__ import annotations

from ast import parse
from typing import TYPE_CHECKING, Final, final

from astart import parse as astart_parse
from astart.rules.imports_bare import find_bare_imports
from astart.rules.object_annotations import find_object_annotations
from astart.rules.parse_module import find_parse_error
from astart.rules.suppressions import find_suppressions

from tests.support.expectations import (
    expect_equal,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart.rules.procedural import Candidate
    from astart.source.ast import CommentedModule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        bare_import (Final[str]): ``import ast`` only used through attributes.
        dotted_import (Final[str]): ``import os.path`` used as ``os.path.join``
            .
        escaped_import (Final[str]): ``import sys`` also read bare.
        reimported (Final[str]): ``import json`` bound twice.
        aliased (Final[str]): ``import ast as tree``.
        suppressions (Final[str]): Suppression comments of several tools.
        unparseable (Final[str]): Source with a syntax error.
        object_marks (Final[str]): ``object`` annotations in every position.

    """

    bare_import: Final[str] = """\
import ast

for n in ast.walk(ast.parse('x=1')):
    pass
"""
    dotted_import: Final[str] = """\
import os.path

p = os.path.join('a', 'b')
"""
    escaped_import: Final[str] = """\
import sys

name = sys
sys.exit(0)
"""
    reimported: Final[str] = """\
import json
import json

json.loads('{}')
"""
    aliased: Final[str] = """\
import ast as tree
tree.walk(x)
"""
    suppressions: Final[str] = (
        "x = 1  @ noqa: F401\n"
        "y = 2  @ type: ignore[assignment]\n"
        "@ pylint: enable=all\n"
        "z = bad  @ pylint: disable=undefined-variable\n"
        "w = plain  # just a comment\n"
    ).replace("@", "#")
    unparseable: Final[str] = """\
def broken(:
    pass
"""
    object_marks: Final[str] = (
        "x: object = thing\n"
        "y: builtins.object = other\n"
        "z: 'object' = third\n"
        "plain: int = 1\n"
        "def f(a: object, b: str) -> object:\n"
        "    return a\n"
    )


def _find(source: str) -> tuple[Candidate, ...]:
    """Run the bare-import detector on source text.

    Args:
        source (str): Module source text.

    Returns:
        tuple[Candidate, ...]: The flagged candidates.

    """
    return find_bare_imports(
        module=parse(source=source),
        filename="t.py",
    )


def test_imp001_flags_bare_import() -> None:
    """An import used only via attributes is flagged."""
    hits: tuple[Candidate, ...] = _find(source=Constants.bare_import)
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["module"], expected="ast")
    expect_equal(
        actual=hits[0].evidence["attributes"],
        expected=["parse", "walk"],
    )
    expect_equal(actual=hits[0].span.start_line, expected=1)


def test_imp001_dotted_import() -> None:
    """``import a.b`` used as ``a.b.c`` is flagged with ``c``."""
    hits: tuple[Candidate, ...] = _find(source=Constants.dotted_import)
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["module"], expected="os.path")
    expect_equal(
        actual=hits[0].evidence["attributes"],
        expected=["join"],
    )


def test_imp001_escaped_name_skipped() -> None:
    """A name also read bare is not a rewrite candidate."""
    expect_equal(actual=_find(source=Constants.escaped_import), expected=())


def test_imp001_rebound_name_skipped() -> None:
    """A name bound by two imports is not a candidate."""
    expect_equal(actual=_find(source=Constants.reimported), expected=())


def test_imp001_aliased_skipped() -> None:
    """``import x as y`` is not a bare import."""
    expect_equal(actual=_find(source=Constants.aliased), expected=())


def test_imp001_unused_import_quiet() -> None:
    """An import never used through attributes stays quiet."""
    expect_equal(
        actual=_find(
            source="""\
import ast
""",
        ),
        expected=(),
    )


def test_sup001_flags_suppressions() -> None:
    """Suppressive directives are flagged; enable stays quiet."""
    module: CommentedModule = astart_parse(
        source=Constants.suppressions,
        filename="t.py",
    )
    hits: tuple[Candidate, ...] = find_suppressions(
        module=module,
        filename="t.py",
    )
    actions: list[str] = [str(object=hit.evidence["action"]) for hit in hits]
    expect_equal(actual=len(hits), expected=3)
    expect_true(condition="enable" not in actions)


def test_prs001_reports_syntax_error() -> None:
    """Unparseable source yields one candidate at the error."""
    hit: Candidate = expect_not_none(
        value=find_parse_error(
            source=Constants.unparseable,
            filename="bad.py",
        ),
    )
    expect_equal(actual=hit.span.file, expected="bad.py")
    expect_true(condition=hit.span.start_line >= 1)


def test_prs001_clean_source_quiet() -> None:
    """Parseable source produces no candidate."""
    expect_equal(
        actual=find_parse_error(
            source="""\
x = 1
""",
            filename="ok.py",
        ),
        expected=None,
    )


def test_typ002_flags_object_annotations() -> None:
    """``object`` is flagged in every annotation position."""
    hits: tuple[Candidate, ...] = find_object_annotations(
        module=parse(source=Constants.object_marks),
        filename="t.py",
    )
    subjects: set[str] = {str(object=hit.evidence["subject"]) for hit in hits}
    expect_equal(
        actual=subjects,
        expected={"x", "y", "z", "a", "f"},
    )


def test_typ002_plain_annotation_quiet() -> None:
    """A precise annotation produces no candidate."""
    expect_equal(
        actual=find_object_annotations(
            module=parse(
                source="""\
x: int = 1
""",
            ),
            filename="t.py",
        ),
        expected=(),
    )
