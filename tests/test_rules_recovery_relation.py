"""Recovery scoring tells contradictions from compatible differences."""

from __future__ import annotations

import pytest
from astart.rules.recovery import Context, module_context, relation

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    ("written", "truth", "expected"),
    [
        ("str", "str | None", "narrower"),
        ("bool", "bool | None", "narrower"),
        ("int", "float", "narrower"),
        ("int", "float | int", "narrower"),
        ("bool", "int", "narrower"),
        ("NoReturn", "None", "narrower"),
        ("None", "Any", "narrower"),
        ("bool | None", "None", "looser"),
        ("None", "NoReturn", "looser"),
        ("None", "te.NoReturn", "looser"),
        ("NoReturn", "te.NoReturn", None),
        ("str", "int", "contradiction"),
        ("list[int]", "list[str]", "contradiction"),
        ("int | str", "int | bytes", "contradiction"),
        ("float", "int", "looser"),
        ("list[int]", "Sequence[int]", "narrower"),
        ("list[int]", "Iterable[int]", "narrower"),
        ("list[int]", "Sequence[float]", "narrower"),
        ("tuple[int, ...]", "Sequence[int]", "narrower"),
        ("dict[str, int]", "Mapping[str, int]", "narrower"),
        ("dict[str, int]", "Mapping[str, float]", "narrower"),
        ("dict[str, int]", "MutableMapping[str, int]", "narrower"),
        ("Sequence[int]", "list[int]", "looser"),
        ("list[str]", "Sequence[int]", "contradiction"),
        ("dict[int, int]", "Mapping[str, int]", "contradiction"),
        ("dict[str, int]", "MutableMapping[str, object]", "contradiction"),
        ("dict[str, int]", "dict[str, object]", "contradiction"),
        ("set[int]", "Sequence[int]", "contradiction"),
        ("list[int]", "MutableSequence[object]", "contradiction"),
    ],
)
def test_relation(*, written: str, truth: str, expected: str | None) -> None:
    """Check how a written annotation relates to the original.

    Args:
        written: What the fixer wrote.
        truth: The original annotation.
        expected: ``None`` for equal, else the relation.

    """
    expect_equal(
        actual=relation(written=written, truth=truth),
        expected=expected,
    )


def test_aliases_of_the_original_module_are_unfolded() -> None:
    """Check ``StyleType = Union[str, Style]`` makes ``str`` narrower."""
    context: Context = module_context(
        source="StyleType = Union[str, Style]\nclass Style: ...\n",
    )
    expect_equal(
        actual=relation(written="str", truth="StyleType", context=context),
        expected="narrower",
    )
    expect_equal(
        actual=relation(written="int", truth="StyleType", context=context),
        expected="contradiction",
    )


def test_self_is_narrower_than_its_class() -> None:
    """Check ``-> Self`` against the original ``-> Element``."""
    context: Context = module_context(source="class Element: ...\n")
    expect_equal(
        actual=relation(written="Self", truth="Element", context=context),
        expected="narrower",
    )
    expect_equal(
        actual=relation(written="Self", truth="int", context=context),
        expected="contradiction",
    )


def test_literal_of_strings_fits_under_str() -> None:
    """Check ``Literal`` arms against a plain ``str``."""
    expect_equal(
        actual=relation(written="str", truth='Literal["a", "b"]'),
        expected="looser",
    )


def test_names_imported_from_elsewhere_are_unresolved() -> None:
    """Check that an alias this module does not define cannot be judged."""
    expect_equal(
        actual=relation(written="str", truth="StyleType"),
        expected="unresolved",
    )


def test_a_type_guard_is_a_bool() -> None:
    """Check that ``bool`` is looser than ``TypeGuard[...]``."""
    expect_equal(
        actual=relation(written="bool", truth="TypeGuard[int]"),
        expected="looser",
    )


def test_a_type_variable_of_the_module_accepts_any_element() -> None:
    """Check that ``Sequence[T]`` takes ``list[int]`` for a TypeVar ``T``."""
    context: Context = module_context(
        source="from typing import TypeVar\nT = TypeVar('T')\n",
    )
    expect_equal(
        actual=relation(
            written="list[int]",
            truth="Sequence[T]",
            context=context,
        ),
        expected="narrower",
    )


def test_a_class_with_an_imported_base_cannot_be_judged_against_abcs() -> None:
    """Check ``ByteStream(Imported)`` vs ``Iterable[bytes]`` is unresolved."""
    context: Context = module_context(
        source=(
            "from elsewhere import Base\n"
            "class ByteStream(Base):\n    pass\n"
            "class Local:\n    pass\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="AsyncIterable[bytes] | Iterable[bytes]",
            context=context,
        ),
        expected="unresolved",
    )
    expect_equal(
        actual=relation(
            written="Local",
            truth="Iterable[bytes]",
            context=context,
        ),
        expected="contradiction",
    )
    expect_equal(
        actual=relation(written="ByteStream", truth="int", context=context),
        expected="contradiction",
    )


def test_an_imported_name_cannot_be_judged_against_abcs() -> None:
    """Check that a name the module only imports is unresolved, not wrong."""
    context: Context = module_context(
        source="from elsewhere import ByteStream\n",
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="Iterable[bytes]",
            context=context,
        ),
        expected="unresolved",
    )
