"""Convert a corpus of real-world modules through the full graph pipeline.

The corpus under ``tests/corpus/base`` holds unmodified copies of CPython
standard
library modules (PSF licence, see ``tests/corpus/base/README.md``). They
exercise
the refiner, backend engine and post-refinement passes with realistic code.

"""

from __future__ import annotations

from ast import parse
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.graph import GraphOnlyConverter

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.graph.conversion.engine import ConversionResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_directory (Final[Path]): Grouped module constant.
        corpus_files (Final[tuple[Path, ...]]): Grouped module constant.

    """

    corpus_directory: Final[Path] = Paths.tests / "corpus" / "base"
    corpus_files: Final[tuple[Path, ...]] = tuple(
        sorted(corpus_directory.glob(pattern="*.py")),
    )


@pytest.fixture(scope="module")
def converter(tmp_path_factory: pytest.TempPathFactory) -> GraphOnlyConverter:
    """Build one converter shared by every corpus module.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Factory for the empty stub
            directory.

    Returns:
        GraphOnlyConverter:
            Converter configured with an empty local stub directory.

    """
    return GraphOnlyConverter.create(
        stubs_path=tmp_path_factory.mktemp(basename="corpus_stubs"),
    )


def test_corpus_is_present() -> None:
    """Fail loudly when the vendored corpus is missing."""
    expect_true(condition=len(Constants.corpus_files) > 0)


@pytest.mark.parametrize(
    "path",
    Constants.corpus_files,
    ids=[path.name for path in Constants.corpus_files],
)
def test_corpus_module_converts_to_valid_source(
    *,
    converter: GraphOnlyConverter,
    path: Path,
) -> None:
    """Keep every corpus module convertible into syntactically valid code.

    Args:
        converter (GraphOnlyConverter): Shared graph converter.
        path (Path): Corpus module under conversion.

    """
    result: ConversionResult = converter.convert_file(source_path=path)
    parse(source=result.output_source)
    expect_equal(actual=result.source_path, expected=path)
    expect_true(condition=len(result.stage_names) > 0)
