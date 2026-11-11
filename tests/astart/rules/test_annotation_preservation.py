"""User-written annotations are never overwritten by ``fix`` (AF-19)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.recovery import annotation_map, variable_map
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

type DictStr = dict[str, str]

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules import FixResult
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        corpus_dirs (Final[tuple[str, str]]): Corpus directories checked for
            preservation.
        pattern (Final[str]): Corpus module file pattern.
        min_annotated (Final[int]): Sanity floor on annotated modules checked.

    """

    root: Final[Path] = Paths.root
    corpus_dirs: Final[tuple[str, str]] = ("corpus/base", "corpus/extended")
    pattern: Final[str] = "*.py"
    min_annotated: Final[int] = 100


def _corpus_paths() -> tuple[Path, ...]:
    """Collect every corpus module under both corpora.

    Returns:
        tuple[Path, ...]: Sorted tuple of corpus file paths.

    """
    paths: list[Path] = []
    for folder in Constants.corpus_dirs:
        directory: Path = Constants.root / "tests" / folder
        paths.extend(sorted(directory.glob(pattern=Constants.pattern)))
    return tuple(paths)


def _fix(*, source: str, name: str) -> FixResult:
    """Run the guarded fixer on one module.

    Args:
        source (str): Python source.
        name (str): File name.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=source,
        filename=name,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def _preserved(
    *,
    before: DictStr,
    after: DictStr,
    kind: str,
) -> list[str]:
    """List annotations present before but changed or removed after.

    Args:
        before (DictStr): ``key: annotation`` map of the original module.
        after (DictStr): ``key: annotation`` map of the fixed module.
        kind (str): Label used in violation messages.

    Returns:
        list[str]: One violation string per changed or removed annotation.

    """
    return [
        f"{kind} {key}: {text!r} -> {after.get(key)!r}"
        for key, text in before.items()
        if after.get(key) != text
    ]


@pytest.mark.slow
def test_fix_never_changes_an_existing_annotation() -> None:
    """Every corpus annotation survives ``fix`` byte-for-byte."""
    paths: tuple[Path, ...] = _corpus_paths()
    expect_true(condition=len(paths) > 0)
    violations: list[str] = []
    checked: int = 0
    for path in paths:
        source: str = path.read_text(encoding="utf-8")
        params_before: DictStr = annotation_map(source=source)
        vars_before: DictStr = variable_map(source=source)
        if not params_before and not vars_before:
            continue
        checked += 1
        result: FixResult = _fix(source=source, name=path.name)
        expect_equal(actual=result.parse_error, expected=None)
        params_after: DictStr = annotation_map(source=result.source)
        vars_after: DictStr = variable_map(source=result.source)
        violations.extend(
            f"{path.name}: {item}"
            for item in (
                *_preserved(
                    before=params_before,
                    after=params_after,
                    kind="param/return",
                ),
                *_preserved(
                    before=vars_before,
                    after=vars_after,
                    kind="variable",
                ),
            )
        )
    expect_true(condition=checked > Constants.min_annotated)
    expect_equal(actual=violations, expected=[])
