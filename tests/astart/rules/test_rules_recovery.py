"""Verify the annotation-recovery benchmark."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, final

import pytest
from astart.rules.recovery import (
    RecoveryOptions,
    RecoveryScore,
    annotation_map,
    normalize_annotation,
    recover,
    strip_annotations,
)

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Constants for the recovery tests.

    Attributes:
        typed (Final[str]): Fully annotated module the recovery maps are read
            from.
        corpus (Final[Path]): Grouped module constant.
        typed_modules (Final[tuple[str, ...]]): Grouped module constant.

    """

    typed: Final[str] = """\
def total(items: list[int], scale: int = 2) -> int:
    return sum(items) * scale


def shout(name: str) -> str:
    return name.upper()
"""

    corpus: Final[Path] = Paths.tests / "corpus" / "base"
    typed_modules: Final[tuple[str, ...]] = (
        "tomllib__parser.py",
        "patterns.py",
        "statistics.py",
        "asyncio_selector_events.py",
        "configparser.py",
        "urllib_parse.py",
    )


def test_annotation_map_keys_by_qualified_name() -> None:
    """Check that annotation map keys by qualified name."""
    found: dict[str, str] = annotation_map(source=Constants.typed)
    expect_equal(actual=found["total.scale"], expected="int")
    expect_equal(actual=found["total->"], expected="int")
    expect_equal(actual=found["shout.name"], expected="str")


def test_strip_removes_every_annotation() -> None:
    """Check that strip removes every annotation."""
    stripped: str = strip_annotations(source=Constants.typed)
    expect_equal(actual=annotation_map(source=stripped), expected={})
    expect_in(item="def total(items, scale=2):", container=stripped)
    expect_not_in(item="->", container=stripped)


def test_recover_scores_precision_and_recall() -> None:
    """Check that recover scores precision and recall."""
    score: RecoveryScore = recover(
        source=Constants.typed,
        filename="typed.py",
        options=RecoveryOptions(min_confidence=0.0),
    )
    expect_equal(actual=score.wrong, expected=())
    expect_in(item="shout.name", container=score.synthesized)
    expect_equal(actual=score.precision, expected=1.0)
    expect_equal(actual=score.recall > 0.0, expected=True)
    expect_equal(
        actual=score.truth,
        expected=len(annotation_map(source=Constants.typed)),
    )


def test_score_arithmetic() -> None:
    """Check that score arithmetic."""
    score: RecoveryScore = RecoveryScore(
        truth=10,
        correct=3,
        wrong=("a",),
        missed=("b",),
        synthesized=(),
        seconds=0.0,
    )
    expect_equal(actual=score.precision, expected=0.75)
    expect_equal(actual=score.recall, expected=0.3)


@pytest.mark.parametrize("name", Constants.typed_modules)
def test_no_recovered_annotation_contradicts_the_original(
    *,
    name: str,
) -> None:
    """Check that no recovered annotation contradicts the original.

    Args:
        name (str): Typed corpus module name.

    """
    score: RecoveryScore = recover(
        source=(Constants.corpus / name).read_text(encoding="utf-8"),
        filename=name,
    )
    expect_equal(actual=score.wrong, expected=())


def test_equivalent_spellings_compare_equal() -> None:
    """Check that equivalent spellings compare equal."""
    pairs: tuple[
        tuple[Literal["Optional[bool]"], Literal["bool | None"]],
        tuple[Literal["Union[int, str]"], Literal["str | int"]],
        tuple[Literal["typing.Optional[int]"], Literal["int | None"]],
        tuple[Literal["List[int]"], Literal["list[int]"]],
        tuple[
            Literal["Dict[str, List[int]]"],
            Literal["dict[str, list[int]]"],
        ],
        tuple[Literal["'Foo'"], Literal["Foo"]],
        tuple[
            Literal["Optional[Union[int, str]]"],
            Literal["int | str | None"],
        ],
    ] = (
        ("Optional[bool]", "bool | None"),
        ("Union[int, str]", "str | int"),
        ("typing.Optional[int]", "int | None"),
        ("List[int]", "list[int]"),
        ("Dict[str, List[int]]", "dict[str, list[int]]"),
        ("'Foo'", "Foo"),
        ("Optional[Union[int, str]]", "int | str | None"),
    )
    for left, right in pairs:
        expect_equal(
            actual=normalize_annotation(text=left),
            expected=normalize_annotation(text=right),
            message=f"{left} vs {right}",
        )
    expect_equal(
        actual=normalize_annotation(text="list[int]")
        != normalize_annotation(
            text="list[str]",
        ),
        expected=True,
    )


def test_misses_are_attributed_to_the_refusal_reason() -> None:
    """Check that misses are attributed to the refusal reason."""
    source: str = (
        "def f(items: list[int], n: int = 2) -> int:\n"
        "    return sum(items) * n\n\n\n"
        "def g(label: str):\n    print(label)\n\n\ng('a')\n"
    )
    score: RecoveryScore = recover(
        source=source,
        filename="t.py",
        options=RecoveryOptions(attribute=True, min_confidence=0.0),
    )
    expect_equal(actual=score.missed, expected=("f->",))
    expect_equal(
        actual=dict(score.missed_reasons),
        expected={"return type not provable": 1},
    )
    expect_true(condition=score.rounds >= 1)


def test_attribution_is_off_unless_requested() -> None:
    """Check that attribution is off unless requested."""
    score: RecoveryScore = recover(
        source="""\
def f(items: list[int]) -> int:
    return sum(items)
""",
        filename="t.py",
    )
    expect_equal(actual=score.missed_reasons, expected=())


def test_the_empty_tuple_type_survives_normalization_twice() -> None:
    """Check that ``tuple[()]`` stays valid when normalized again."""
    once: str = normalize_annotation(text="dict[str, int] | tuple[()]")
    expect_equal(actual=normalize_annotation(text=once), expected=once)
