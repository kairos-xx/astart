"""Tests for the M8-24 string literal normalisation fixer."""

from __future__ import annotations

from ast import Assign, Constant, Module, parse
from typing import Final, final

from astart.rules.strings_normalize import normalize_strings

from tests.support.expectations import (
    expect_equal,
    expect_instance,
    expect_true,
)


@final
class Constants:
    """Constants for the strings normalize tests.

    Attributes:
        line_length (Final[int]): Width the string normalizer wraps literals
            to.
        max_line_length (Final[int]): TODO.

    """

    line_length: Final[int] = 60
    max_line_length: Final[int] = 79


def _normalize(
    source: str,
    *,
    line_length: int = Constants.line_length,
) -> str:
    """Return rewritten source for ``source``.

    Args:
        source (str): Python source.
        line_length (int): Emitted line budget.

    Returns:
        str: Normalised source.

    """
    return normalize_strings(source=source, line_length=line_length).output


def test_escaped_newline_becomes_triple_quoted() -> None:
    r"""``"a\\nb"`` gains real newlines inside triple quotes."""
    source: str = """\
x = "line one\\nline two"
"""
    output: str = _normalize(source=source)
    expect_true(condition='"""\\\nline one\nline two"""' in output)


def test_triple_body_preserves_other_escapes() -> None:
    """Non-newline escapes survive the triple-quote conversion."""
    source: str = """\
x = "a\\tb\\nc"
"""
    output: str = _normalize(source=source)
    expect_true(condition='"""\\\na\\tb\nc"""' in output)


def test_overlong_string_splits_at_word_boundaries() -> None:
    """A long literal becomes a parenthesised implicit concatenation."""
    words: str = " ".join(["word"] * 30)
    source: str = f'x = "{words}"\n'
    output: str = _normalize(source=source, line_length=Constants.line_length)
    expect_true(
        condition="""\
(
"""
        in output,
    )
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= Constants.line_length,
            message=f"overlong: {line!r}",
        )
    # The value round-trips through the AST.
    tree: Module = parse(source=output)
    assign: Assign = expect_instance(value=tree.body[0], kind=Assign)
    constant: Constant = expect_instance(value=assign.value, kind=Constant)
    expect_equal(actual=constant.value, expected=words)


def test_fstring_short_untouched() -> None:
    """F-strings inside the line budget keep their exact form."""
    source: str = """\
x = f"value {1} more text here"
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_fstring_overlong_splits_keeping_fields() -> None:
    """An overlong f-string becomes pieces whose ``{...}`` fields survive."""
    source: str = (
        'x = f"Machine-readable evidence: [{Constants.json_name}]'
        '({Constants.json_name}) and trailing words to overflow the line"\n'
    )
    output: str = _normalize(source=source)
    expect_true(
        condition="""\
(
"""
        in output,
    )
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= Constants.line_length,
            message=f"overlong: {line!r}",
        )
    output_count: int = 2
    expect_true(
        condition=output.count("{Constants.json_name}") == output_count,
    )
    expect_true(condition='f"Machine-readable evidence: [' in output)
    # A second pass changes nothing.
    expect_equal(
        actual=_normalize(source=output),
        expected=output,
    )


def test_fstring_nested_refused() -> None:
    """An f-string inside another f-string's field is never rewritten."""
    source: str = (
        "x = f\"outer {f'{1}'} and a whole lot more text "
        'to make this line definitely too long ok"\n'
    )
    output: str = _normalize(source=source)
    # The outer string may split; the inner ``f'{1}'`` stays verbatim.
    expect_true(condition="f'{1}'" in output)


def test_fstring_raw_refused() -> None:
    """Raw f-strings keep their literal backslashes."""
    source: str = (
        'x = rf"raw {value} and a whole lot more text '
        'to make this line definitely too long ok"\n'
    )
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_bytes_refused() -> None:
    """Byte literals are never touched."""
    source: str = """\
x = b"a\\nb"
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_raw_string_refused() -> None:
    """Raw strings keep their literal backslashes."""
    source: str = """\
x = r"a\\nb"
"""
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
    source: str = """\
d = {"ke\\ny": 1}
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_all_members_refused() -> None:
    """``__all__`` elements are semantic names."""
    source: str = """\
__all__ = ["na\\nme"]
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_match_pattern_refused() -> None:
    """Match-value literals are pattern semantics."""
    source: str = """\
match x:
    case "a\\nb":
        pass
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_implicit_concatenation_refused() -> None:
    """Strings already split stay untouched."""
    source: str = """\
x = "part " "more"
"""
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_triple_refused_when_value_contains_delimiter() -> None:
    """A value containing ``\"\"\"`` keeps the escaped form."""
    source: str = 'x = \'has """ inside\\nend\'\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)


def test_split_balances_last_line() -> None:
    """A repairable one-word tail moves a companion word down."""
    source: str = (
        "command.add_argument(\n"
        '    "--runtime-protocols",\n'
        '    action="store_true",\n'
        '    help="Emit @runtime_checkable on synthesized protocols '
        'used under isinstance",\n'
        ")\n"
    )
    output: str = _normalize(
        source=source,
        line_length=Constants.max_line_length,
    )
    expect_true(condition='"under isinstance"' in output)
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= Constants.max_line_length,
            message=f"overlong: {line!r}",
        )
    expect_equal(
        actual=_normalize(
            source=output,
            line_length=Constants.max_line_length,
        ),
        expected=output,
    )


def test_split_keeps_widow_when_unfixable() -> None:
    """A final word too wide for a companion stays on its own line."""
    tail: str = "H" * 48
    source: str = f'x = "aaaa aaaa aaaa aaaa aaaa aaaa aaaa ii jj {tail}"\n'
    output: str = _normalize(source=source)
    expect_true(condition=f'"{tail}"' in output)
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= Constants.line_length,
            message=f"overlong: {line!r}",
        )


def test_fstring_split_balances_last_line() -> None:
    """F-string literal pieces get the same widow repair."""
    source: str = (
        "command.add_argument(\n"
        '    "--runtime-protocols",\n'
        '    help=f"Emit @runtime_checkable on synthesized protocols '
        'used under isinstance",\n'
        ")\n"
    )
    output: str = _normalize(
        source=source,
        line_length=Constants.max_line_length,
    )
    expect_true(condition='f"under isinstance"' in output)
    for line in output.splitlines():
        expect_true(
            condition=len(line) <= Constants.max_line_length,
            message=f"overlong: {line!r}",
        )


def test_idempotent_second_run() -> None:
    """Normalising twice yields no further changes."""
    source: str = """\
x = "line one\\nline two"
"""
    first: str = _normalize(source=source)
    second: str = _normalize(source=first)
    expect_equal(actual=second, expected=first)


def test_whitespace_only_triple_collapses_to_escapes() -> None:
    """A triple literal holding only newlines returns to escape form."""
    source: str = 'x = """\\\n\n"""\n'
    output: str = _normalize(source=source)
    expect_equal(
        actual=output,
        expected="""\
x = "\\n"
""",
    )


def test_whitespace_only_triple_with_content_is_kept() -> None:
    """A triple literal with real content is left alone."""
    source: str = 'x = """\\\nreal\n"""\n'
    output: str = _normalize(source=source)
    expect_equal(actual=output, expected=source)
