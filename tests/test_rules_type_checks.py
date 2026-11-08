"""Tests for the M8-02 TYP005 and M8-06 mismatch detectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart import parse
from astart.rules.type_mismatch import (
    find_incompatible_defaults,
    find_return_mismatches,
)
from astart.rules.variable_annotations import (
    find_missing_variable_annotations,
)

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from astart.ast import CommentedModule
    from astart.rules.procedural import Candidate


def test_typ005_flags_known_literal_type() -> None:
    """``x = 1`` has a known inferred type and no annotation."""
    module: CommentedModule = parse(source="x = 1\n")
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["inferred"], expected="int")


def test_typ005_skips_annotated() -> None:
    """An annotated assignment is not a candidate."""
    module: CommentedModule = parse(source="x: int = 1\n")
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_typ005_refuses_unknown_inference() -> None:
    """``input()`` cannot be typed, so nothing is proposed."""
    module: CommentedModule = parse(source="x = input()\n")
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_typ005_skips_private_and_dunder() -> None:
    """``_x`` and ``__x__`` are not annotation candidates."""
    module: CommentedModule = parse(source="_x = 1\n__y__ = 2\n")
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_typ005_covers_function_locals() -> None:
    """Local assignments participate in the same check."""
    module: CommentedModule = parse(
        source="def f():\n    y = 2.5\n    return y\n",
    )
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["name"], expected="y")


def test_typ005_skips_attribute_and_unpacking_targets() -> None:
    """Only plain name targets are flagged."""
    module: CommentedModule = parse(
        source="import os\nos.sep = '/'\na, b = 1, 's'\n",
    )
    hits: tuple[Candidate, ...] = find_missing_variable_annotations(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_return_mismatch_flags_incompatible_literal() -> None:
    """``-> int`` returning ``"s"`` is a definitive mismatch."""
    module: CommentedModule = parse(source='def f() -> int:\n    return "s"\n')
    hits: tuple[Candidate, ...] = find_return_mismatches(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["declared"], expected="int")
    expect_equal(actual=hits[0].evidence["inferred"], expected="str")


def test_return_mismatch_accepts_compatible() -> None:
    """A matching return produces no candidate."""
    module: CommentedModule = parse(source="def f() -> int:\n    return 1\n")
    hits: tuple[Candidate, ...] = find_return_mismatches(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_return_mismatch_refuses_optional_none() -> None:
    """``-> int | None`` returning ``None`` is compatible."""
    module: CommentedModule = parse(
        source="def f() -> int | None:\n    return None\n",
    )
    hits: tuple[Candidate, ...] = find_return_mismatches(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_return_mismatch_scopes_nested_functions() -> None:
    """A nested function's returns are judged by its own signature."""
    module: CommentedModule = parse(
        source=(
            "def f() -> int:\n"
            "    def inner() -> str:\n"
            '        return "x"\n'
            "    return inner()\n"
        ),
    )
    hits: tuple[Candidate, ...] = find_return_mismatches(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_incompatible_default_flags_wrong_literal() -> None:
    """``p: int = "s"`` is a definitive mismatch."""
    module: CommentedModule = parse(
        source='def g(p: int = "s") -> None:\n    pass\n',
    )
    hits: tuple[Candidate, ...] = find_incompatible_defaults(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)
    expect_equal(actual=hits[0].evidence["parameter"], expected="p")


def test_incompatible_default_accepts_matching() -> None:
    """``p: int = 3`` produces no candidate."""
    module: CommentedModule = parse(
        source="def g(p: int = 3) -> None:\n    pass\n",
    )
    hits: tuple[Candidate, ...] = find_incompatible_defaults(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_incompatible_default_refuses_union_with_none() -> None:
    """``p: int | None = None`` is compatible."""
    module: CommentedModule = parse(
        source="def g(p: int | None = None) -> None:\n    pass\n",
    )
    hits: tuple[Candidate, ...] = find_incompatible_defaults(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)


def test_incompatible_default_covers_kwonly() -> None:
    """Keyword-only defaults are checked too."""
    module: CommentedModule = parse(
        source="def g(*, p: str = 1) -> None:\n    pass\n",
    )
    hits: tuple[Candidate, ...] = find_incompatible_defaults(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=1)


def test_incompatible_default_numeric_tower() -> None:
    """``bool`` is a subtype of ``int`` — no false positive."""
    module: CommentedModule = parse(
        source="def g(p: int = True) -> None:\n    pass\n",
    )
    hits: tuple[Candidate, ...] = find_incompatible_defaults(
        module=module,
        filename="t.py",
    )
    expect_equal(actual=len(hits), expected=0)
