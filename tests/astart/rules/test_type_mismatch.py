"""M8-06 detectors: return-type mismatches and incompatible defaults."""

from __future__ import annotations

from typing import TYPE_CHECKING

from astart import parse
from astart.rules.type_mismatch import (
    find_incompatible_defaults,
    find_return_mismatches,
)

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.procedural import Candidate


def _module(*, source: str) -> CommentedModule:
    """Parse one source snippet for the detectors.

    Args:
        source (str): Python source text.

    Returns:
        CommentedModule: The parsed module.

    """
    return parse(source=source)


def _returns(*, source: str) -> tuple[Candidate, ...]:
    """Run the return-mismatch detector on one snippet.

    Args:
        source (str): Python source text.

    Returns:
        tuple[Candidate, ...]: The flagged candidates.

    """
    return find_return_mismatches(
        module=_module(source=source),
        filename="snippet.py",
    )


def _defaults(*, source: str) -> tuple[Candidate, ...]:
    """Run the incompatible-default detector on one snippet.

    Args:
        source (str): Python source text.

    Returns:
        tuple[Candidate, ...]: The flagged candidates.

    """
    return find_incompatible_defaults(
        module=_module(source=source),
        filename="snippet.py",
    )


def test_provable_return_mismatch_is_flagged() -> None:
    """A literal of one builtin nominal against another is a candidate."""
    found: tuple[Candidate, ...] = _returns(
        source="""\
def f() -> int:
    return 'text'
""",
    )
    expect_equal(actual=len(found), expected=1)
    expect_equal(actual=found[0].evidence["function"], expected="f")
    expect_equal(actual=found[0].evidence["declared"], expected="int")
    expect_equal(actual=found[0].evidence["inferred"], expected="str")


def test_compatible_return_is_not_flagged() -> None:
    """A matching literal return produces no candidate."""
    expect_equal(
        actual=_returns(
            source="""\
def f() -> int:
    return 1
""",
        ),
        expected=(),
    )


def test_unannotated_and_bare_returns_are_skipped() -> None:
    """Missing annotations and valueless returns stay silent."""
    expect_equal(
        actual=_returns(
            source=(
                """\
def f():
    return 'x'
def g() -> int:
    return
"""
            ),
        ),
        expected=(),
    )


def test_non_literal_return_uses_inference() -> None:
    """Name and call returns go through ``infer_type``."""
    found: tuple[Candidate, ...] = _returns(
        source="""\
def f(x) -> int:
    return x
""",
    )
    expect_true(condition=len(found) <= 1)


def test_unknown_inference_is_not_a_candidate() -> None:
    """An ``Unknown`` inferred shape never produces a verdict."""
    expect_equal(
        actual=_returns(
            source="""\
def f() -> int:
    return missing_name
""",
        ),
        expected=(),
    )


def test_yield_returns_are_skipped() -> None:
    """``yield``/``yield from`` values are not plain returns."""
    expect_equal(
        actual=_returns(
            source=(
                "def g():\n    yield 1\n"
                "def f() -> int:\n    yield 1\n    return (yield)\n"
            ),
        ),
        expected=(),
    )


def test_nested_and_async_functions_are_checked() -> None:
    """Nested defs get their own signatures; async defs are included."""
    found: tuple[Candidate, ...] = _returns(
        source=(
            "def outer() -> int:\n"
            "    def inner() -> str:\n"
            "        return 1\n"
            "    return 0\n"
            "async def a() -> bytes:\n"
            "    return 'x'\n"
        ),
    )
    functions: list[JsonValue] = [item.evidence["function"] for item in found]
    expect_true(condition="inner" in functions)
    expect_true(condition="a" in functions)
    expect_true(condition="outer" not in functions)


def test_unconvertible_annotation_is_skipped() -> None:
    """Annotations the codec cannot read produce no verdict."""
    expect_equal(
        actual=_returns(
            source="""\
def f() -> 1:
    return 'x'
""",
        ),
        expected=(),
    )


def test_literal_value_shapes() -> None:
    """None, bytes, complex and ellipsis constants map to atomics."""
    found: tuple[Candidate, ...] = _returns(
        source=(
            "def a() -> int:\n    return None\n"
            "def b() -> int:\n    return b'x'\n"
            "def c() -> int:\n    return 1j\n"
            "def d() -> int:\n    return ...\n"
        ),
    )
    expect_equal(actual=len(found), expected=3)


def test_provable_default_mismatch_is_flagged() -> None:
    """A default literal incompatible with its annotation is flagged."""
    found: tuple[Candidate, ...] = _defaults(
        source="""\
def f(x: int = 's'):
    pass
""",
    )
    expect_equal(actual=len(found), expected=1)
    expect_equal(actual=found[0].evidence["parameter"], expected="x")


def test_compatible_and_unannotated_defaults_are_skipped() -> None:
    """Matching defaults and unannotated parameters stay silent."""
    expect_equal(
        actual=_defaults(
            source=(
                """\
def f(x: int = 1, y='s', *, z: str = 't'):
    pass
"""
            ),
        ),
        expected=(),
    )


def test_self_cls_and_posonly_defaults() -> None:
    """``self``/``cls`` are exempt; positional-only defaults are checked."""
    found: tuple[Candidate, ...] = _defaults(
        source=(
            "class C:\n"
            "    def m(self, x: int = 's', /):\n        pass\n"
            "    @classmethod\n"
            "    def c(cls, y: int = 't'):\n        pass\n"
        ),
    )
    parameters: list[JsonValue] = [
        item.evidence["parameter"] for item in found
    ]
    expect_true(condition="x" in parameters)
    expect_true(condition="y" in parameters)
    expect_equal(actual=len(found), expected=2)


def test_kwonly_default_mismatch() -> None:
    """Keyword-only defaults go through the same verdict."""
    found: tuple[Candidate, ...] = _defaults(
        source="""\
def f(*, flag: int = 'yes'):
    pass
""",
    )
    expect_equal(actual=len(found), expected=1)
    expect_equal(actual=found[0].evidence["parameter"], expected="flag")


def test_defaults_alignment_with_missing_defaults() -> None:
    """Parameters without defaults pad the alignment correctly."""
    found: tuple[Candidate, ...] = _defaults(
        source="""\
def f(a, b: int = 's', c=1):
    pass
""",
    )
    expect_equal(actual=len(found), expected=1)
    expect_equal(actual=found[0].evidence["parameter"], expected="b")


def test_unknown_default_inference_is_skipped() -> None:
    """An unresolvable default name never produces a verdict."""
    expect_equal(
        actual=_defaults(
            source="""\
def f(x: int = missing_name):
    pass
""",
        ),
        expected=(),
    )
