"""Exercise native alias cost search, scope safety and atomic application."""

from __future__ import annotations

from ast import (
    FunctionDef,
    Subscript,
    TypeAlias,
    TypeVar,
    dump,
    walk,
)
from json import loads
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from astart.__main__ import main
from astart.project.versions import PythonTarget
from astart.rules import FixResult, FixSettings, fix_source
from astart.rules.catalog import load_default_catalog
from astart.rules.facts import default_registries
from astart.rules.vocabulary import FixSafety
from astart.source.ast import CommentedModule
from astart.transforms.aliases import (
    AliasChanges,
    AliasOptimizer,
    AliasSettings,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from ast import stmt
    from pathlib import Path

    from astart.rules.registry import Registries


def _repeated(
    *,
    annotation: str = "dict[str, list[tuple[int, str]]]",
    count: int = 4,
) -> str:
    """Build independent owners for a profitable repeated annotation.

    Args:
        annotation (str): Fixture type expression.
        count (int): Number of independently owned function signatures.

    Returns:
        str: Four functions with eight annotation sites.

    """
    return "\n".join(
        f"def f{index}(x: {annotation}) -> {annotation}:\n    return x\n"
        for index in range(count)
    )


def test_alias_extraction_uses_one_tree_and_preserves_executable_nodes() -> (
    None
):
    """Plan and commit aliases without cloning or reparsing the module."""
    tree: CommentedModule = CommentedModule.parse(source=_repeated())
    original: tuple[stmt, ...] = tuple(tree.body)
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        result: AliasChanges = AliasOptimizer(
            tree=tree,
            module_id="example",
        ).optimize()
    expect_equal(actual=len(result.declarations), expected=1)
    expect_equal(actual=result.annotations_changed, expected=8)
    expect_true(
        condition=result.source_savings >= AliasSettings().min_source_savings,
    )
    expect_true(condition=result.optimality_proven)
    expect_is(actual=tree.body[0], expected=result.declarations[0])
    expect_equal(actual=tuple(tree.body[1:]), expected=original)
    expect_equal(
        actual=result.declaration_ids,
        expected=(f"alias:example:{result.declarations[0].name.id}",),
    )
    emitted: str = tree.unparse(preserve_formatting=True)
    expect_in(item="type DictListTupleIntStr =", container=emitted)
    expect_equal(
        actual=AliasOptimizer(tree=tree).optimize().annotations_changed,
        expected=0,
    )


def test_generic_patterns_produce_specialized_native_references() -> None:
    """Anti-unification retains actual arguments at each annotation site."""
    source: str = "\n".join(
        f"def f{index}(x: dict[str, list[tuple[{name}, {name}, "
        f"dict[str, list[{name}]]]]]):\n"
        "    return x\n"
        for index, name in enumerate(iterable=["int", "str", "float"] * 5)
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: AliasChanges = AliasOptimizer(
        tree=tree,
        settings=AliasSettings(max_candidates=4),
    ).optimize()
    expect_true(
        condition=any(
            declaration.type_params for declaration in result.declarations
        ),
    )
    functions: list[FunctionDef] = [
        node for node in tree.body if isinstance(node, FunctionDef)
    ]
    expect_true(
        condition=all(
            isinstance(function.args.args[0].annotation, Subscript)
            for function in functions
        ),
    )
    expect_true(condition=result.source_savings > 0)
    tree.unparse(preserve_formatting=True)


@pytest.mark.parametrize(argnames="generic", argvalues=[False, True])
def test_existing_alias_is_reused_without_rewriting_its_declaration(
    *,
    generic: bool,
) -> None:
    """Reference existing ordinary and generic aliases by their real nodes.

    Args:
        generic (bool): Whether the existing declaration has a PEP 695 binder.

    """
    source: str = (
        """\
type Existing[T] = dict[str, list[T]]
"""
        if generic
        else """\
type Existing = dict[str, list[int]]
"""
    ) + _repeated(annotation="dict[str, list[int]]")
    tree: CommentedModule = CommentedModule.parse(source=source)
    declaration: TypeAlias = expect_instance(
        value=tree.body[0],
        kind=TypeAlias,
    )
    before: str = dump(node=declaration, include_attributes=True)
    result: AliasChanges = AliasOptimizer(tree=tree).optimize()
    expect_equal(actual=result.declarations, expected=())
    expect_equal(actual=result.annotations_changed, expected=8)
    expect_is(actual=tree.body[0], expected=declaration)
    expect_equal(
        actual=dump(node=declaration, include_attributes=True),
        expected=before,
    )
    expect_in(
        item="Existing[int]" if generic else "x: Existing",
        container=tree.unparse(preserve_formatting=True),
    )


@pytest.mark.parametrize(
    argnames="source",
    argvalues=[
        """\
from typing import Self
"""
        + _repeated(annotation="list[Self]"),
        """\
import typing
"""
        + _repeated(annotation="list[typing.Self]"),
        """\
from typing import Self as S
"""
        + _repeated(annotation="list[S]"),
        """\
from typing import Literal as L
"""
        + _repeated(annotation="L['x']"),
        _repeated(annotation="list['Local']"),
        """\
from unknown import *
"""
        + _repeated(),
        """\
from custom import dict
"""
        + _repeated(),
        """\
def f[T: int](x: dict[str, list[T]]):
    pass
"""
        * 4,
        """\
def f[*Ts](x: tuple[*Ts]):
    pass
"""
        * 4,
    ],
)
def test_unsafe_alias_hoisting_preserves_original_annotations(
    *,
    source: str,
) -> None:
    """Refuse unsupported binders, contextual types and unknown resolution.

    Args:
        source (str): A deliberately unsafe annotation context.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    before: str = dump(node=tree, include_attributes=True)
    result: AliasChanges = AliasOptimizer(tree=tree).optimize()
    expect_equal(actual=result.annotations_changed, expected=0)
    expect_equal(actual=result.declarations, expected=())
    expect_true(condition=bool(result.skipped))
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


def test_local_class_and_shadowed_existing_alias_are_not_hoisted() -> None:
    """Use native lexical visibility instead of matching name strings."""
    source: str = (
        "type Existing = dict[str, list[int]]\n"
        "def f(Existing):\n"
        "    class Local:\n        pass\n"
        "    a: list[Local]\n    b: list[Local]\n"
        "    c: dict[str, list[int]]\n    d: dict[str, list[int]]\n"
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: AliasChanges = AliasOptimizer(
        tree=tree,
        settings=AliasSettings(min_source_savings=1000),
    ).optimize()
    expect_equal(actual=result.annotations_changed, expected=0)
    expect_true(condition=bool(result.skipped))


def test_literal_and_annotated_payloads_keep_value_semantics() -> None:
    """Metadata never becomes a generic type-parameter position."""
    source: str = """\
from typing import Annotated, Literal
""" + _repeated(
        annotation="Annotated[dict[str, list[int]], 'keep me']",
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: AliasChanges = AliasOptimizer(tree=tree).optimize()
    expect_true(condition=bool(result.declarations))
    expect_in(
        item="'keep me'",
        container=tree.unparse(preserve_formatting=True),
    )
    expect_equal(
        actual=sum(
            isinstance(node, TypeVar)
            for declaration in result.declarations
            for node in walk(node=declaration)
        ),
        expected=0,
    )


def test_comments_inside_annotations_are_preserved_by_refusal() -> None:
    """Alias extraction must not drop comments owned by replaced syntax."""
    source: str = "\n".join(
        f"def f{index}(x: dict[\n    str,  # Keep this\n    list[int]\n]):\n"
        "    return x\n"
        for index in range(4)
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: AliasChanges = AliasOptimizer(tree=tree).optimize()
    expect_equal(actual=result.annotations_changed, expected=0)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )


def test_alias_search_respects_evaluation_budget_and_binding_collisions() -> (
    None
):
    """Exhaustion preserves a valid baseline and never claims an optimum."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
DictListTupleIntStr = 1
"""
        + _repeated(count=12),
    )
    limited: AliasChanges = AliasOptimizer(
        tree=tree,
        settings=AliasSettings(max_plan_evaluations=1),
    ).optimize()
    expect_equal(actual=limited.plans_evaluated, expected=1)
    expect_false(condition=limited.optimality_proven)
    result: AliasChanges = AliasOptimizer(tree=tree).optimize()
    expect_true(condition=bool(result.declarations))
    expect_true(
        condition=all(
            node.name.id != "DictListTupleIntStr"
            for node in result.declarations
        ),
    )


def test_alias_optimizer_rejects_stale_input_and_rolls_back_interruption() -> (
    None
):
    """Never overwrite external edits or publish partial alias declarations."""
    tree: CommentedModule = CommentedModule.parse(source=_repeated())
    optimizer: AliasOptimizer = AliasOptimizer(tree=tree)
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    function.name = "external_edit"
    with pytest.raises(expected_exception=ValueError, match="stale"):
        optimizer.optimize()
    expect_equal(actual=function.name, expected="external_edit")
    before: str = dump(node=tree, include_attributes=True)
    body: list[stmt] = tree.body
    optimizer = AliasOptimizer(tree=tree)
    with (
        pytest.raises(expected_exception=KeyboardInterrupt),
        patch(target="builtins.compile", side_effect=KeyboardInterrupt),
    ):
        optimizer.optimize()
    expect_is(actual=tree.body, expected=body)
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


def test_alias_transform_cli_writes_evidence_and_defaults_on(
    tmp_path: Path,
) -> None:
    """Extract aliases by default; ``--no-optimize-aliases`` opts out.

    Args:
        tmp_path (Path): Isolated input, output and JSON report directory.

    """
    source: Path = tmp_path / "input.py"
    output: Path = tmp_path / "output.py"
    report: Path = tmp_path / "report.json"
    source.write_text(data=_repeated(), encoding="utf-8")
    expect_equal(
        actual=main(
            argv=[
                "transform",
                str(object=source),
                "--no-optimize-aliases",
                "--output",
                str(object=output),
            ],
        ),
        expected=0,
    )
    expect_equal(
        actual=output.read_text(encoding="utf-8"),
        expected=_repeated(),
    )
    expect_equal(
        actual=main(
            argv=[
                "transform",
                str(object=source),
                "--output",
                str(object=output),
                "--report",
                str(object=report),
            ],
        ),
        expected=0,
    )
    expect_in(
        item="type DictListTupleIntStr =",
        container=output.read_text(encoding="utf-8"),
    )
    evidence: dict[str, int | str | bool | list[str]] = loads(
        s=report.read_text(encoding="utf-8"),
    )
    expect_equal(actual=evidence["aliases_added"], expected=1)
    expect_equal(actual=evidence["alias_annotations_changed"], expected=8)


def _fix(*, settings: FixSettings) -> FixResult:
    """Run the fix pipeline over the repeated-annotation fixture.

    Args:
        settings (FixSettings): Fix options under test.

    Returns:
        FixResult: The fix result for the repeated-annotation fixture.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=_repeated(),
        filename="input.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=settings,
    )


def test_fix_source_extracts_aliases_by_default() -> None:
    """The fix pipeline reuses repeated annotations unless opted out."""
    aliased: FixResult = _fix(
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    expect_in(
        item="type DictListTupleIntStr =",
        container=aliased.source,
    )
    plain: FixResult = _fix(
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            optimize_aliases=False,
        ),
    )
    expect_false(
        condition="type DictListTupleIntStr" in plain.source,
    )


def test_fix_source_skips_aliases_below_python_312() -> None:
    """The ``type`` statement is never emitted for older targets."""
    result: FixResult = _fix(
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            target=PythonTarget(floor=(3, 11)),
        ),
    )
    expect_false(
        condition="type DictListTupleIntStr" in result.source,
    )
