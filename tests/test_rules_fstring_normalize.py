"""Tests for the M8-25 f-string interior normalisation fixer."""

from __future__ import annotations

from astart.rules.fstring_normalize import normalize_fstrings

from tests.expectations import expect_equal, expect_true


def _normalize(source: str) -> str:
    """Return rewritten source.

    Args:
        source: Python source.

    Returns:
        Normalised output.

    """
    return normalize_fstrings(source=source).output


def test_padded_expression_is_trimmed() -> None:
    """``f"{ a }"`` becomes ``f"{a}"``."""
    expect_equal(
        actual=_normalize(source='x = f"{ a }"\n'),
        expected='x = f"{a}"\n',
    )


def test_conversion_flag_spacing_is_trimmed() -> None:
    """``f"{a !r}"`` becomes ``f"{a!r}"``."""
    expect_equal(
        actual=_normalize(source='x = f"{a !r}"\n'),
        expected='x = f"{a!r}"\n',
    )


def test_spec_separator_spacing_is_trimmed() -> None:
    """Whitespace around ``:`` is removed; spec text is preserved."""
    output: str = _normalize(source='x = f"{ a !s :>8 }"\n')
    expect_true(condition='f"{a!s:>8 }"' in output)


def test_spec_content_is_never_rewritten() -> None:
    """``f"{x:>8 }"`` keeps its spec byte-for-byte."""
    source: str = 'x = f"{ x:>8 }"\n'
    output: str = _normalize(source=source)
    expect_true(condition='f"{x:>8 }"' in output)


def test_nested_spec_fields_normalise_recursively() -> None:
    """Replacement fields inside format specs are normalised too."""
    expect_equal(
        actual=_normalize(source='x = f"{y:{ w }}"\n'),
        expected='x = f"{y:{w}}"\n',
    )


def test_internal_expression_spacing_is_preserved() -> None:
    """Only field-edge whitespace moves; interior spacing stays."""
    expect_equal(
        actual=_normalize(source='x = f"{ a  +  b }"\n'),
        expected='x = f"{a  +  b}"\n',
    )


def test_debug_equals_field_is_refused() -> None:
    """``f"{ x = }"`` prints its own text — never rewritten."""
    source: str = 'x = f"{ x = }"\n'
    expect_equal(actual=_normalize(source=source), expected=source)


def test_colon_inside_subscript_is_not_a_spec() -> None:
    """``f"{d['a:b']}"`` has no format spec."""
    source: str = "x = f\"{ d['a:b'] }\"\n"
    output: str = _normalize(source=source)
    expect_true(condition="d['a:b']" in output)


def test_non_fstring_braces_are_untouched() -> None:
    """Plain strings and dict displays are not fields."""
    source: str = 'x = "not f { a }"\nd = { "k": 1 }\n'
    expect_equal(actual=_normalize(source=source), expected=source)


def test_walrus_expression_is_preserved() -> None:
    """Parenthesised walrus fields keep their text."""
    source: str = 'x = f"{(k:=v)}"\n'
    expect_equal(actual=_normalize(source=source), expected=source)


def test_idempotent_second_run() -> None:
    """Normalising twice yields no further changes."""
    source: str = 'x = f"{ a !r :>8 }"\n'
    first: str = _normalize(source=source)
    second: str = _normalize(source=first)
    expect_equal(actual=second, expected=first)
