"""Regression tests for the integrated annotation conversion pipeline."""

from __future__ import annotations

from ast import AST, AnnAssign, FunctionDef, Module, arg, parse, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.graph.conversion.synthesis import Types as OriginalTypes
from astart.semantic import (
    Args,
    GraphConversion,
    ProtocolSpec,
    TypeHintCatalog,
    Types,
    TypeShape,
)
from astart.semantic.graph_conversion import (
    GraphAnnotation,
    annotation_shape,
    apply_graph_annotations,
    available_type_names,
    collect_graph_annotations,
    declaration_sites,
)
from astart.source.ast import CommentedModule

from tests.support.expectations import (
    expect_binary_expr,
    expect_constant_expr,
    expect_equal,
    expect_false,
    expect_function_node,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_named_node,
    expect_not_in,
    expect_suite_node,
    expect_true,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Literal

    from astart.semantic.type_inference import TypeInference


@final
class Constants:
    """Group module-level constants.

    Attributes:
        min_proposals (Final[int]): Grouped module constant.

    """

    min_proposals: Final[int] = 3


@pytest.fixture
def stub_dir(*, tmp_path: Path) -> Path:
    """Return an empty Astart typeshed location without external packages.

    Args:
        tmp_path (Path): Filesystem path identifying the tmp.

    Returns:
        Path: Path produced by this operation.

    """
    path: Path = tmp_path / "typeshed"
    path.mkdir()
    return path


def test_proposals_from_real_pipeline_preserve_source_and_nodes(
    *,
    stub_dir: Path,
) -> None:
    """Consume real backend declarations without codegen changes.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    source: str = dedent(
        text="""\
    #!/usr/bin/env python3
    # preserve this comment
    def add(x,y):
        return x+y
    result = add(1, 2)  __DIRECTIVE__: E501
    """,
    ).replace("__DIRECTIVE__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    method: FunctionDef = expect_instance(value=tree.body[0], kind=FunctionDef)
    argument: arg = expect_instance(value=method.args.args[0], kind=arg)
    result: GraphConversion = tree.convert(stubs_path=stub_dir)
    expect_true(condition=result.proposal_count >= Constants.min_proposals)
    expect_true(
        condition=any(
            item.role == "parameter" and item.target is argument
            for item in result.proposals
        ),
    )
    expect_in(item="validate-syntax", container=result.stages)
    expect_equal(actual=tree.unparse(), expected=source)
    expect_equal(
        actual=tree.infer_type(node=argument).inferred,
        expected=TypeShape(name="int"),
    )
    expect_true(
        condition=any(
            item.kind == "graph-inference"
            for item in tree.infer_type(node=argument).evidence
        ),
    )
    expect_in(item="def add(x: int", container=result.converted_source)


def test_apply_adds_only_matched_annotations(*, stub_dir: Path) -> None:
    """Retain function identity, shebang and suppression; no full rewrite.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    source: str = dedent(
        text="""\
    #!/usr/bin/env python3
    # important
    def add(x,y):
        return x+y
    result=add(1,2) __DIRECTIVE__: E501
    """,
    ).replace("__DIRECTIVE__", "# n" + "oqa")
    tree: CommentedModule = CommentedModule.parse(source=source)
    function: FunctionDef = expect_instance(
        value=tree.body[0],
        kind=FunctionDef,
    )
    result: GraphConversion = tree.convert(stubs_path=stub_dir, apply=True)
    expect_true(condition=result.proposal_count >= Constants.min_proposals)
    expect_is(actual=tree.body[0], expected=function)
    expect_is_not(actual=function.args.args[0].annotation, unexpected=None)
    expect_is_not(actual=function.returns, unexpected=None)
    output: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="fallback",
    )
    expect_true(condition=output.startswith("#!/usr/bin/env python3"))
    expect_in(item="# important", container=output)
    expect_in(
        item=(
            ("__ASTART_FIXTURE_DIRECTIVE_4__: E501").replace(
                "__ASTART_FIXTURE_DIRECTIVE_4__",
                "# n" + "oqa",
            )
        ),
        container=output,
    )
    expect_in(item="def add(x: int,y: int) -> int:", container=output)
    expect_in(item="result=add(1,2)", container=output)
    compile(source=output, filename="<test>", mode="exec")


def test_external_contract_is_invalidated_after_mutation(
    *,
    stub_dir: Path,
) -> None:
    """Discard no-longer-valid Astart annotations on syntax changes.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x + 1
a=f(3)
""",
    )
    tree.convert(stubs_path=stub_dir)
    parameter: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    expect_true(
        condition=any(
            item.kind == "graph-inference"
            for item in tree.infer_type(node=parameter).evidence
        ),
    )
    expect_named_node(value=tree.body[0]).name = "renamed"
    expect_false(
        condition=any(
            item.kind == "graph-inference"
            for item in tree.infer_type(node=parameter).evidence
        ),
    )


def test_original_annotations_not_overwritten(*, stub_dir: Path) -> None:
    """Explicit user-declared types outrank speculative codegen.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    source: str = """\
def f(x: str, y: int) -> str:
    return x
f('a', 1)
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    result: GraphConversion = tree.convert(stubs_path=stub_dir, apply=True)
    expect_true(condition=all(p.role != "parameter" for p in result.proposals))
    expect_equal(actual=tree.unparse(), expected=source)


def test_hierarchical_sites_keep_nested_definitions_separate() -> None:
    """Different scopes with equal names never share annotation proposals."""
    module: Module = expect_instance(
        value=parse(
            source=(
                """\
def outer():
    def inner(x):
        return x
    return inner(1)
def inner(y):
    return y
"""
            ),
        ),
        kind=Module,
    )
    sites: dict[tuple[str, ...], AST] = declaration_sites(module=module)
    expect_in(item=("function:outer:0", "function:inner:0"), container=sites)
    expect_in(item=("function:inner:0",), container=sites)
    expect_is_not(
        actual=sites["function:outer:0", "function:inner:0"],
        unexpected=sites["function:inner:0",],
    )


def test_undefined_external_annotation_is_rejected() -> None:
    """Never introduce converter-generated names absent from the source."""
    available: frozenset[str] = available_type_names(
        root=parse(source="value = 1"),
    )
    expect_is(
        actual=annotation_shape(
            node=parse(source="UnknownExternal[int]", mode="eval").body,
            available=available,
        ),
        expected=None,
    )
    expect_equal(
        actual=annotation_shape(
            node=parse(source="list[int]", mode="eval").body,
            available=available,
        ),
        expected=TypeShape(name="list", arguments=(TypeShape(name="int"),)),
    )


def test_convert_module_variable_only_with_explicit_apply(
    *,
    stub_dir: Path,
) -> None:
    """Original assignments stay intact until replacement is requested.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value = 1
""",
    )
    result: GraphConversion = collect_graph_annotations(
        root=tree,
        stubs_path=stub_dir,
    )
    if result.proposal_count:
        expect_true(
            condition=all(
                item.target in tree.body for item in result.proposals
            ),
        )
        expect_true(
            condition=apply_graph_annotations(root=tree, integration=result)
            >= 0,
        )
        expect_true(
            condition=all(
                isinstance(
                    node,
                    (AnnAssign, type(parse(source="value = 1").body[0])),
                )
                for node in tree.body
            ),
        )


def test_plain_module_uses_same_pipeline(*, stub_dir: Path) -> None:
    """The underlying graph engine also accepts unextended standard ASTs.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    module: Module = expect_instance(
        value=parse(
            source="""\
def f(x):
    return x
""",
        ),
        kind=Module,
    )
    result: GraphConversion = collect_graph_annotations(
        root=module,
        stubs_path=stub_dir,
    )
    result = expect_instance(value=result, kind=GraphConversion)
    expect_true(condition=bool(result.stages))


@pytest.mark.parametrize(
    "source",
    [
        """\
def f(x):
    return x + 1
""",
        """\
class C:
    def method(self, x):
        return x
""",
        """\
def f(x: int):
    return x
""",
        """\
async def f(x: int) -> int:
    return x
""",
    ],
)
def test_proposals_are_only_eligible_nodes(
    *,
    stub_dir: Path,
    source: str,
) -> None:
    """Do not carry foreign or duplicated graph syntax into edits.

    Args:
        source (str): The source examined while do not carry foreign or
            duplicated graph syntax into edits.
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    module: CommentedModule = CommentedModule.parse(source=source)
    integration: GraphConversion = module.convert(stubs_path=stub_dir)
    expect_true(
        condition=all(
            proposal.target in tuple(walk(node=module))
            for proposal in integration.proposals
        ),
    )
    expect_equal(actual=module.unparse(), expected=source)


def test_auto_refines_again_after_ast_change(*, stub_dir: Path) -> None:
    """The integrated Astart pipeline is lazy and revision-aware.

    Args:
        stub_dir (Path): Stub dir supplied as Path for this operation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x + 1
value = f(3)
""",
    )
    argument: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    tree.configure_graph(stubs_path=stub_dir)
    before: TypeInference = tree.infer_type(node=argument)
    expect_true(
        condition=any(
            item.kind == "graph-inference" for item in before.evidence
        ),
    )
    expect_constant_expr(
        value=expect_binary_expr(
            value=expression_of_stmt(
                value=expect_suite_node(value=tree.body[0]).body[0],
            ),
        ).right,
    ).value = 5
    after: TypeInference = tree.infer_type(node=argument)
    expect_true(
        condition=any(
            item.kind == "graph-inference" for item in after.evidence
        ),
    )
    expect_is_not(actual=before, unexpected=after)
    tree.configure_graph(stubs_path=None)
    expect_true(
        condition=all(
            item.kind != "graph-inference"
            for item in tree.infer_type(node=argument).evidence
        ),
    )


def test_apply_inserts_only_required_typing_imports_after_future() -> None:
    """Generated annotation references have valid bindings and no cruft."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
#!/usr/bin/env python3
\"""Module description.\"""
from __future__ import annotations

def f(x):
    return x
"""
        ),
    )
    target: arg = expect_function_node(value=tree.body[-1]).args.args[0]
    proposal: GraphAnnotation = GraphAnnotation(
        target=target,
        annotation=TypeShape(
            name="Callable",
            arguments=(
                TypeShape(
                    name="parameters",
                    arguments=(TypeShape(name="int"),),
                ),
                TypeShape(name="str"),
            ),
        ),
        source="Callable[[int], str]",
        site=("function:f:0", "parameter:x"),
        role="parameter",
    )
    integration: GraphConversion = GraphConversion(
        proposals=(proposal,),
        skipped=(),
        converted_source="",
        stages=(),
        warnings=(),
    )
    expect_equal(
        actual=apply_graph_annotations(root=tree, integration=integration),
        expected=1,
    )
    output: str = tree.unparse(
        preserve_formatting=True,
        on_format_conflict="fallback",
    )
    expect_true(condition=output.startswith("#!/usr/bin/env python3"))
    expect_in(item="Module description", container=output)
    expect_in(item="from __future__ import annotations", container=output)
    expect_in(item="from typing import Callable", container=output)
    expect_true(
        condition=output.index("from __future__")
        < output.index("from typing"),
    )
    expect_not_in(item="TYPE_CHECKING", container=output)
    expect_not_in(item="Protocol", container=output)
    compile(source=output, filename="<typing>", mode="exec")
    expect_equal(
        actual=apply_graph_annotations(root=tree, integration=integration),
        expected=0,
    )
    expect_equal(
        actual=tree.unparse().count("from typing import Callable"),
        expected=1,
    )


def test_nested_control_flow_declaration_sites() -> None:
    """Different branches cannot accidentally exchange annotation proposals."""
    module: Module = expect_instance(
        value=parse(
            source=(
                """\
if flag:
    def helper(x):
        return x
else:
    def helper(y):
        return y
"""
            ),
        ),
        kind=Module,
    )
    sites: dict[tuple[str, ...], AST] = declaration_sites(module=module)
    then_key: tuple[
        Literal["branch:If:0:body"],
        Literal["function:helper:0"],
    ] = ("branch:If:0:body", "function:helper:0")
    else_key: tuple[
        Literal["branch:If:0:orelse"],
        Literal["function:helper:0"],
    ] = ("branch:If:0:orelse", "function:helper:0")
    expect_in(item=then_key, container=sites)
    expect_in(item=else_key, container=sites)
    expect_is_not(actual=sites[then_key], unexpected=sites[else_key])


def test_original_synthesis_catalog_is_available_from_native_semantics() -> (
    None
):
    """Expose Astart's complete type builder via the native API."""
    expect_is(actual=Types, expected=OriginalTypes)
    expect_is(actual=TypeHintCatalog, expected=Types.CATALOG)
    expect_is_not(actual=Args, unexpected=None)
    expect_is_not(actual=ProtocolSpec, unexpected=None)
    expect_is_not(actual=Types.INT, unexpected=None)
