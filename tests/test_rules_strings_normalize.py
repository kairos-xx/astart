"""Tests for the M8-24 string literal normalisation fixer."""

from __future__ import annotations

from ast import Assign, Constant, Module, parse
from typing import Final

from astart.rules.strings_normalize import normalize_strings

from tests.expectations import expect_equal, expect_instance, expect_true

_LINE_LENGTH: Final[int] = 60


def _normalize(source: str, *, line_length: int = 88) -> str:
    """Return rewritten source for ``source``.

    Args:
        source: Python source.
        line_length: Emitted line budget.

    Returns:
        Normalised source.

    """
    return normalize_strings(source=source, line_length=line_length).output


def test_escaped_newline_becomes_triple_quoted() -> None:
    r"""``"a\\nb"`` gains real newlines inside triple quotes."""
    source: str = 'x = "line one\\nline two"\n'
    output: str = _normalize(source=source)
    expect_true(condition='"""line one\nline two"""' in output)


def test_triple_body_preserves_other_escapes() -> None:
    """Non-newline escapes survive the triple-quote conversion."""
    source: str = 'x = "a\\tb\\nc"\n'
    output: str = _normalize(source=source)
    expect_true(condition='"""a\\tb\nc"""' in output)


def test_overlong_string_splits_at_word_boundaries() -> None:
    """A long literal becomes a parenthesised implicit concatenation."""
    words: str = " ".join(["word"] * 30)
    source: str = f'x = "{words}"\n'
    output: str = _normalize(source=source, line_length=60)
    expect_true(condition="(\n" in output)
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= _LINE_LENGTH,
            message=f"overlong: {line!r}",
        )
    # The value round-trips through the AST.
    tree: Module = parse(source=output)
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    constant: Constant = expect_instance(value=assign.value, kind=Constant)
    expect_equal(actual=constant.value, expected=words)


def test_fstring_refused() -> None:
    """f-strings are never touched."""
    source: str = 'x = f"value {1} more text here"\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_bytes_refused() -> None:
    """Byte literals are never touched."""
    source: str = 'x = b"a\\nb"\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_raw_string_refused() -> None:
    """Raw strings keep their literal backslashes."""
    source: str = 'x = r"a\\nb"\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_triple_quoted_refused() -> None:
    """Existing triple-quoted strings are left alone."""
    source: str = 'x = """already\\ntriple"""\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_docstring_refused() -> None:
    """Module docstrings are never rewritten."""
    source: str = '"""Doc\\nstring."""\n\nx = 1\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_dict_key_refused() -> None:
    """Dictionary keys keep their exact literal form."""
    source: str = 'd = {"ke\\ny": 1}\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_all_members_refused() -> None:
    """``__all__`` elements are semantic names."""
    source: str = '__all__ = ["na\\nme"]\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_match_pattern_refused() -> None:
    """Match-value literals are pattern semantics."""
    source: str = 'match x:\n    case "a\\nb":\n        pass\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_implicit_concatenation_refused() -> None:
    """Strings already split stay untouched."""
    source: str = 'x = "part " "more"\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_triple_refused_when_value_contains_delimiter() -> None:
    """A value containing ``\"\"\"`` keeps the escaped form."""
    source: str = 'x = \'has """ inside\\nend\'\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_idempotent_second_run() -> None:
    """Normalising twice yields no further changes."""
    source: str = 'x = "line one\\nline two"\n'
    first: str = _normalize(source=source)
    second: str = _normalize(source=first)
    expect_equal(actual=second, expected=first)
