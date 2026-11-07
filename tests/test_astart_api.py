"""Validate astart's sole supported public package API."""

from __future__ import annotations

from ast import Assign, Call, FunctionDef, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart import (
    BoundCall,
    CommentedModule,
    GraphConversion,
    Module,
    ParameterKind,
    Types,
    TypeShape,
    convert,
    parse,
    unparse,
)
from astart.__main__ import main
from astart.semantic import LiteralValue

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        min_walked_nodes: Grouped module constant.

    """

    min_walked_nodes: Final[int] = 2


def test_public_parse_and_type_shape() -> None:
    """Expose native source and typing through one top-level module."""
    tree: Module = expect_instance(
        value=parse(
            source="""\
a=1
b=a+2
""",
        ),
        kind=Module,
    )
    tree = expect_instance(value=tree, kind=CommentedModule)
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="int",
    )
    inferred: LiteralValue = expect_instance(
        value=tree.infer(node="b"),
        kind=LiteralValue,
    )
    expect_equal(actual=inferred.value, expected=3)
    expect_equal(
        actual=unparse(tree=tree),
        expected="""\
a=1
b=a+2
""",
    )
    expect_is_not(
        actual=TypeShape(name="list", arguments=(TypeShape(name="int"),)),
        unexpected=None,
    )
    expect_is_not(actual=Types, unexpected=None)
    expect_true(
        condition=len(tuple(walk(node=tree))) > Constants.min_walked_nodes,
    )


def test_single_signature_binding_api() -> None:
    """Bind positional input to its named contract without parallel engines."""
    tree: Module = expect_instance(
        value=parse(
            source=dedent(
                text=(
                    """\
    def calculate(x: int, /, y: str = "z") -> str:
        return y
    result = calculate(3)
    """
                ),
            ),
        ),
        kind=Module,
    )
    expect_instance(value=tree.body[0], kind=FunctionDef)
    expect_equal(
        actual=tree.signature(name="calculate")[0].parameters[0].kind,
        expected=ParameterKind.POSITIONAL_ONLY,
    )
    call_statement: Assign = expect_instance(value=tree.body[1], kind=Assign)
    call: Call = expect_instance(value=call_statement.value, kind=Call)
    binding: BoundCall | None = tree.bind_call(node=call)
    binding = expect_not_none(value=binding)
    expect_equal(
        actual={entry.parameter.name for entry in binding.arguments},
        expected={"x", "y"},
    )
    expect_equal(actual=tree.typing_diagnostics, expected=())


def test_integrated_converter_in_main_package(tmp_path: Path) -> None:
    """Execute internal graph conversion through the supported module API.

    Args:
        tmp_path: Filesystem path identifying the tmp.

    """
    tree: Module = expect_instance(
        value=parse(
            source="""\
def add(x, y):
    return x + y
result = add(1, 2)
""",
        ),
        kind=Module,
    )
    result: GraphConversion = convert(tree=tree, stubs_path=tmp_path)
    result = expect_instance(value=result, kind=GraphConversion)
    expect_true(condition=bool(result.stages))
    expect_true(condition=bool(tree.graph_document().source))
    expect_is(actual=tree.types, expected=tree.semantic.types)
    tree.configure_graph(stubs_path=None)


def test_cli_uses_same_safe_conversion_api(tmp_path: Path) -> None:
    """The package CLI applies source annotations through the public API.

    Args:
        tmp_path: Filesystem path identifying the tmp.

    """
    source: Path = tmp_path / "example.py"
    output: Path = tmp_path / "edited.py"
    report: Path = tmp_path / "report.json"
    source.write_text(
        data="""\
def inc(value):
    return value + 1
""",
        encoding="utf-8",
    )
    expect_equal(
        actual=main(
            argv=[
                "convert",
                "--source",
                str(object=source),
                "--stubs",
                str(object=tmp_path),
                "--output",
                str(object=output),
                "--report",
                str(object=report),
            ],
        ),
        expected=0,
    )
    expect_true(condition=output.is_file())
    expect_true(condition=report.is_file())
    expect_in(item="def inc", container=output.read_text(encoding="utf-8"))
    expect_in(item="stages", container=report.read_text(encoding="utf-8"))


def test_cli_preserves_declared_source_encoding_and_crlf(
    tmp_path: Path,
) -> None:
    """Retain encoding metadata and newline conventions on safe AST edits.

    Args:
        tmp_path: Filesystem path identifying the tmp.

    """
    source: Path = tmp_path / "latin1.py"
    output: Path = tmp_path / "latin1-edited.py"
    source.write_bytes(data=b"# coding: latin-1\r\ntext: str = '\xe9'\r\n")
    expect_equal(
        actual=main(
            argv=[
                "convert",
                "--source",
                str(object=source),
                "--stubs",
                str(object=tmp_path),
                "--output",
                str(object=output),
            ],
        ),
        expected=0,
    )
    expect_in(item=b"\xe9", container=output.read_bytes())
    expect_in(item=b"\r\n", container=output.read_bytes())
