"""Tests adapted from the Astart project's structured-annotation design."""

from __future__ import annotations

from ast import Name, walk
from textwrap import dedent
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pytest
from astart.semantic.type_expressions import TypeExpressionCodec
from astart.source.ast import CommentedModule

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    from astart.semantic.type_expressions import TypeExpression
    from astart.semantic.type_inference import TypeInference


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("typing.Optional[int]", "int | None"),
        ("typing.Union[str, int, None]", "int | str | None"),
        ("Callable[[int, str], bool]", "Callable[[int, str], bool]"),
        ("typing.Callable[..., int]", "typing.Callable[..., int]"),
        ("dict[str, list[float | None]]", "dict[str, list[float | None]]"),
        ("Annotated[int, 'metadata']", "Annotated[int, 'metadata']"),
        ("ClassVar[tuple[str, ...]]", "ClassVar[tuple[str, ...]]"),
        ("'list[str]'", "list[str]"),
        ("int | str | int", "int | str"),
        ("Literal['a', 'b']", "Literal['a', 'b']"),
    ],
)
def test_structured_annotation(*, source: str, expected: str) -> None:
    """Keep nested annotations typed without evaluating their contents.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while keep nested annotations typed
            without evaluating their contents.

    """
    expect_equal(
        actual=str(object=TypeExpressionCodec.from_source(source=source)),
        expected=expected,
    )


def test_required_imports() -> None:
    """Identify dependencies for imported typing constructors."""
    expression: TypeExpression = TypeExpressionCodec.from_source(
        source="Callable[[str], Annotated[int, 'x']]",
    )
    expect_equal(
        actual=TypeExpressionCodec.required_imports(
            expression=expression,
        ),
        expected=frozenset(("Callable", "Annotated")),
    )


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        ("Optional[int]", "int | None"),
        ("Union[str, float]", "float | str"),
        ("Callable[[int], bool]", "Callable[[int], bool]"),
        ("dict[str, tuple[int, ...]]", "dict[str, tuple[int, ...]]"),
    ],
)
def test_annotation_in_declaration(*, annotation: str, expected: str) -> None:
    """Expose structured contract shape through the existing public API.

    Args:
        annotation (str): The annotation examined while expose structured
            contract shape through the existing public API.
        expected (str): Expected supplied as str for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source=f"""\
value: {annotation}
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="value").declared),
        expected=expected,
    )


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("'  text  '.strip()", "str"),
        ("'word'.upper()", "str"),
        ("'word'.startswith('w')", "bool"),
        ("'word'.count('o')", "int"),
        ("repr(4)", "str"),
        ("len([1])", "int"),
        ("all([True])", "bool"),
        ("ord('a')", "int"),
    ],
)
def test_known_builtins(*, expression: str, expected: str) -> None:
    """Infer only explicitly modeled safe built-ins and string methods.

    Args:
        expected (str): Expected supplied as str for this operation.
        expression (str): The expression examined while infer only explicitly
            modeled safe built-ins and string methods.

    """
    tree: CommentedModule = CommentedModule.parse(
        source=f"""\
result = {expression}
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected=expected,
    )


def test_type_evidence_preserved() -> None:
    """Keep causal evidence attached to the affected AST names."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
name: str = 'abc'
result = name.upper()
""",
    )
    result: TypeInference = tree.infer_type(node="result")
    expect_equal(actual=str(object=result.inferred), expected="str")
    expect_true(condition=bool(result.evidence))
    expect_true(
        condition=any(
            isinstance(node, Name) and hasattr(node, "inferred_type_hint")
            for node in walk(node=tree)
        ),
    )


def test_shadowed_builtin_is_not_assumed_standard() -> None:
    """A source-defined replacement invalidates built-in return assumptions."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
len = other_function
result = len([])
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="Unknown",
    )


def test_lazy_stub_functions_and_aliases(*, tmp_path: Path) -> None:
    """Source imports acquire return contracts from external `.pyi` stubs.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    root: Path = tmp_path
    stdlib: Path = root / "stdlib"
    stdlib.mkdir()
    (stdlib / "demo.pyi").write_text(
        data=dedent(
            text="""\
    def function(value: int) -> list[str]: ...
    def function(value: str) -> list[bytes]: ...
    class Widget:
        def read(self) -> int: ...
    """,
        ),
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(
        source=(
            dedent(
                text="""\
    import demo as dm
    from demo import function as execute
    a = dm.function(1)
    b = execute('x')
    w: demo.Widget
    c = w.read()
    """,
            )
        ),
    )
    tree.configure_stubs(root=root)
    expect_equal(
        actual=str(object=tree.infer_type(node="a").inferred),
        expected="list[str]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="b").inferred),
        expected="list[bytes]",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="c").inferred),
        expected="int",
    )
    expect_true(
        condition=any(
            "stub:" in item.kind
            for item in tree.semantic.types.node_proofs.values()
            for item in item
        ),
    )


def test_lazy_stub_zip(*, tmp_path: Path) -> None:
    """Load archive-backed declarations without extracting them.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    root: Path = tmp_path / "stubs.zip"
    with ZipFile(file=root, mode="w") as archive:
        archive.writestr(
            zinfo_or_arcname="typeshed/stdlib/demo.pyi",
            data="""\
def parse(text: str) -> bool: ...
""",
        )
    tree: CommentedModule = CommentedModule.parse(
        source="""\
import demo
answer = demo.parse('x')
""",
    )
    tree.configure_stubs(root=root)
    expect_equal(
        actual=str(object=tree.infer_type(node="answer").inferred),
        expected="bool",
    )


def test_stub_invalidation_after_reconfiguration(*, tmp_path: Path) -> None:
    """Switching stub sources invalidates previously inferred contracts.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    root: Path = tmp_path
    (root / "demo.pyi").write_text(
        data="""\
def read() -> str: ...
""",
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(
        source="""\
import demo
result = demo.read()
""",
    )
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="Unknown",
    )
    tree.configure_stubs(root=root)
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="str",
    )
    tree.configure_stubs(root=None)
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="Unknown",
    )


def test_rebound_import_does_not_claim_stub_return(*, tmp_path: Path) -> None:
    """Imported signature evidence is revoked for lexically rebound imports.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    """
    (tmp_path / "demo.pyi").write_text(
        data="""\
def read() -> str: ...
""",
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(
        source="""\
import demo
demo = replacement
result = demo.read()
""",
    )
    tree.configure_stubs(root=tmp_path)
    expect_equal(
        actual=str(object=tree.infer_type(node="result").inferred),
        expected="Unknown",
    )
