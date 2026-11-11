"""Write inferred annotations back into real modules without losing source.

Every vendored standard-library module receives its inferred parameter and
return annotations. The output must parse, keep every comment, and, once the
annotations are stripped again, equal the original syntax tree.

"""

from __future__ import annotations

from ast import AST, AsyncFunctionDef, FunctionDef, arg, dump, expr, walk
from ast import parse as parse_python
from io import StringIO
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, Final, final

import pytest
from astart import parse, unparse

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.source.ast import CommentedModule


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_files (Final[tuple[Path, ...]]): Grouped module constant.
        applied_roles (Final[frozenset[str]]): Grouped module constant.

    """

    corpus_files: Final[tuple[Path, ...]] = tuple(
        sorted((Paths.tests / "corpus" / "base").glob(pattern="*.py")),
    )
    applied_roles: Final[frozenset[str]] = frozenset({"parameter", "return"})


def _comments(*, text: str) -> list[str]:
    """List the comments of a source in order.

    Args:
        text (str): Python source.

    Returns:
        list[str]: The comment tokens.

    """
    return [
        token.string
        for token in generate_tokens(
            readline=StringIO(initial_value=text).readline,
        )
        if token.type == COMMENT
    ]


def _stripped_dump(*, source: str) -> str:
    """Dump a tree after removing parameter and return annotations.

    Args:
        source (str): Python source.

    Returns:
        str: The textual dump of the stripped tree.

    """
    tree: AST = parse_python(source=source)
    for node in walk(node=tree):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            node.returns = None
        if isinstance(node, arg):
            node.annotation = None
    return dump(node=tree)


def _annotate(*, module: CommentedModule, stubs_path: Path) -> int:
    """Write inferred parameter and return annotations into a module.

    Args:
        module (CommentedModule): Parsed module.
        stubs_path (Path): Empty stub directory.

    Returns:
        int: How many annotations were written.

    """
    written: int = 0
    for proposal in module.convert(
        stubs_path=stubs_path,
        apply=False,
    ).proposals:
        if proposal.role not in Constants.applied_roles:
            continue
        if proposal.source == "object":
            continue
        annotation: expr = parse_python(
            source=proposal.source,
            mode="eval",
        ).body
        target: AST = proposal.target
        if isinstance(target, (FunctionDef, AsyncFunctionDef)):
            if target.returns is None:
                target.returns = annotation
                written += 1
        elif isinstance(target, arg) and target.annotation is None:
            target.annotation = annotation
            written += 1
    return written


@pytest.fixture(scope="module")
def stubs_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide one empty stub directory shared by the module.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Factory for the directory.

    Returns:
        Path: The directory.

    """
    return tmp_path_factory.mktemp(basename="annotation_stubs")


@pytest.mark.parametrize(
    "path",
    Constants.corpus_files,
    ids=[path.name for path in Constants.corpus_files],
)
def test_annotations_round_trip_through_real_modules(
    *,
    path: Path,
    stubs_path: Path,
) -> None:
    """Keep syntax, comments and layout while annotations are added.

    Args:
        path (Path): Vendored module under test.
        stubs_path (Path): Empty stub directory.

    """
    source: str = path.read_text(encoding="utf-8")
    module: CommentedModule = parse(source=source, filename=path.name)
    _ = _annotate(module=module, stubs_path=stubs_path)
    output: str = unparse(tree=module, preserve_formatting=True)
    expect_equal(
        actual=_stripped_dump(source=output),
        expected=_stripped_dump(source=source),
    )
    expect_equal(
        actual=_comments(text=output),
        expected=_comments(text=source),
    )


def test_corpus_receives_annotations() -> None:
    """Guard against a vacuous pass where nothing is annotated."""
    expect_true(condition=len(Constants.corpus_files) > 0)
