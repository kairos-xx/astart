"""Regression tests for the custom AST JSON exporter."""

from __future__ import annotations

from json import loads
from typing import TYPE_CHECKING

from astart.source.tree_dump import dump_file

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_dump_file_preserves_custom_nodes_and_tokens(tmp_path: Path) -> None:
    """Export comments, docstrings, executable nodes, and lexical tokens.

    Args:
        tmp_path (Path): Isolated pytest temporary directory.

    """
    source: Path = tmp_path / "example.py"
    output: Path = tmp_path / "nested" / "example.json"
    source.write_text(
        data="#!/usr/bin/env python3\n# comment\ndef f(x: int) -> int:\n"
        '    """Return x.\n\n    Args:\n        x (int): Value.\n\n'
        '    Returns:\n        int: Value.\n    """\n    return x\n',
        encoding="utf-8",
    )
    dump_file(source=source, output=output)
    result: dict[str, object] = loads(s=output.read_text(encoding="utf-8"))
    expect_equal(
        actual=result["format"],
        expected="astart-custom-ast-v1",
    )
    expect_true(condition=bool(result["token_stream"]))
    expect_in(item="comment", container=str(object=result["tree"]))
    expect_in(item="Docstring", container=str(object=result["tree"]))
    expect_in(item="token_info", container=str(object=result["tree"]))
