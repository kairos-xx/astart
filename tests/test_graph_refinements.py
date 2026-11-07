"""Exercise the document-based refiner and the refinement service."""

from __future__ import annotations

from ast import (
    BinOp,
    Call,
    Constant,
    FunctionDef,
    List,
    Load,
    Module,
    Name,
    Subscript,
    Tuple,
    expr,
    parse,
    unparse,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Final, cast, final

from astart._graph import AstDocument
from astart._graph.inference.graph_refinements import (
    GraphRefinementStats,
    GraphRefiner,
)
from astart._graph.inference.refinement import PostRefinementService
from astart._graph.inference.refinement.service import (
    PostRefinementService as ServiceFromModule,
)

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_instance,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from astart._graph.inference.post_refinements import RefinementResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        property_source: Grouped module constant.

    """

    property_source: Final[str] = dedent(
        text="""\
    class Account:
        def __init__(self, balance: int, owner: str) -> None:
            self._balance = 0
            self._owner = ''

        @property
        def balance(self):
            return self._balance

        @balance.setter
        def balance(self, value):
            self._balance = value

        @property
        def owner(self) -> object:
            return self._owner

        @owner.setter
        def owner(self, name: object):
            self._owner = name

        @property
        def missing(self):
            return self._unknown

        @property
        def unrelated(self):
            return 3

        @helper.setter
        def other(self, value):
            self._other = value

        def plain(self, x):
            return x

    def call_it(account):
        return Account(1, 'a')
    """,
    )


def _name(*, identifier: str) -> Name:
    """Create a loaded name node.

    Args:
        identifier: Name text.

    Returns:
        Name node.

    """
    return Name(id=identifier, ctx=Load())


def test_stats_report_changes() -> None:
    """Report whether any counter recorded a change."""
    expect_false(condition=GraphRefinementStats().changed())
    for field in ("changed_annotations", "changed_returns", "changed_calls"):
        stats: GraphRefinementStats = GraphRefinementStats()
        setattr(stats, field, 1)
        expect_true(condition=stats.changed())


def test_refiner_updates_property_types_and_calls() -> None:
    """Refine property getters, setters and keyword calls."""
    document: AstDocument = AstDocument.from_source(
        source=Constants.property_source,
        filename="account.py",
    )
    refiner: GraphRefiner = GraphRefiner(document=document)
    refiner.refine()
    expect_true(condition=refiner.stats.changed())
    expect_true(
        condition=refiner.stats.changed_returns
        + refiner.stats.changed_annotations
        + refiner.stats.changed_calls
        > 0,
    )
    again: GraphRefiner = GraphRefiner(document=document)
    again.refine()


def test_typevar_replacement_walks_every_expression_kind() -> None:
    """Rename type variables through names, subscripts, calls and sequences."""
    document: AstDocument = AstDocument.from_source(
        source="""\
x = 1
""",
        filename="x.py",
    )
    refiner: GraphRefiner = GraphRefiner(document=document)
    tree: expr = parse(
        source="dict[T, list[T] | Call(T, key=T)] + [T, (T, U)]",
        mode="eval",
    ).body
    refiner.replace_all_typevars_in_node(node=tree, old_name="T", new_name="V")
    expect_equal(
        actual=parse(source="1").body[0].__class__.__name__,
        expected="Expr",
    )
    expect_equal(
        actual=unparse(ast_obj=tree),
        expected="dict[V, list[V] | Call(V, key=V)] + [V, (V, U)]",
    )
    constant: Constant = Constant(value=1)
    refiner.replace_all_typevars_in_node(
        node=constant,
        old_name="T",
        new_name="V",
    )
    expect_equal(actual=constant.value, expected=1)
    binop: BinOp = cast(
        typ="BinOp",
        val=parse(source="T | T", mode="eval").body,
    )
    refiner.replace_in_binop(node=binop, old_name="T", new_name="V")
    call: Call = cast(typ="Call", val=parse(source="f(T)", mode="eval").body)
    refiner.replace_in_call(node=call, old_name="f", new_name="g")
    sequence: List | Tuple = cast(
        typ="List | Tuple",
        val=parse(source="[T]", mode="eval").body,
    )
    refiner.replace_in_sequence(node=sequence, old_name="T", new_name="W")
    expect_equal(actual=unparse(ast_obj=sequence), expected="[W]")


def test_slice_helpers_handle_tuples_and_names() -> None:
    """Replace and detect type variables inside raw slice values."""
    document: AstDocument = AstDocument.from_source(
        source="""\
x = 1
""",
        filename="x.py",
    )
    refiner: GraphRefiner = GraphRefiner(document=document)
    target: Name = _name(identifier="T")
    refiner.replace_in_slice(slice_value=target, old_name="T", new_name="V")
    expect_equal(actual=target.id, expected="V")
    members: tuple[expr, ...] = (
        _name(identifier="T"),
        parse(source="list[T]", mode="eval").body,
    )
    refiner.replace_in_slice(slice_value=members, old_name="T", new_name="V")
    first_member: Name = expect_instance(value=members[0], kind=Name)
    expect_equal(actual=first_member.id, expected="V")
    refiner.replace_in_slice(
        slice_value=parse(source="list[T]", mode="eval").body,
        old_name="T",
        new_name="V",
    )
    expect_true(
        condition=GraphRefiner.slice_tuple_contains_typevar(
            slice_tuple=members,
            typevar_name="V",
        ),
    )
    expect_false(
        condition=GraphRefiner.slice_tuple_contains_typevar(
            slice_tuple=members,
            typevar_name="Z",
        ),
    )
    GraphRefiner.replace_typevar_in_slice_tuple(
        slice_tuple=members,
        old_name="V",
        new_name="Q",
    )
    expect_equal(actual=first_member.id, expected="Q")


def test_annotation_typevar_queries_and_replacement() -> None:
    """Detect and rename type variables in annotations."""
    document: AstDocument = AstDocument.from_source(
        source="""\
x = 1
""",
        filename="x.py",
    )
    refiner: GraphRefiner = GraphRefiner(document=document)
    plain: Name = _name(identifier="T")
    expect_true(
        condition=refiner.annotation_uses_typevar(
            annotation=plain,
            typevar_name="T",
        ),
    )
    subscript: Subscript = cast(
        typ="Subscript",
        val=parse(source="T[int]", mode="eval").body,
    )
    expect_true(
        condition=refiner.annotation_uses_typevar(
            annotation=subscript,
            typevar_name="T",
        ),
    )
    inner: Subscript = cast(
        typ="Subscript",
        val=parse(source="list[T]", mode="eval").body,
    )
    expect_true(
        condition=refiner.annotation_uses_typevar(
            annotation=inner,
            typevar_name="T",
        ),
    )
    vars(inner)["slice"] = (_name(identifier="T"), _name(identifier="U"))
    expect_true(
        condition=refiner.annotation_uses_typevar(
            annotation=inner,
            typevar_name="T",
        ),
    )
    expect_false(
        condition=refiner.annotation_uses_typevar(
            annotation=Constant(value=1),
            typevar_name="T",
        ),
    )
    refiner.replace_typevar_in_annotation(
        annotation=inner,
        old_name="T",
        new_name="V",
    )
    refiner.replace_typevar_in_annotation(
        annotation=subscript,
        old_name="T",
        new_name="V",
    )
    refiner.replace_typevar_in_annotation(
        annotation=plain,
        old_name="T",
        new_name="V",
    )
    named: Subscript = cast(
        typ="Subscript",
        val=parse(source="list[T]", mode="eval").body,
    )
    refiner.replace_typevar_in_annotation(
        annotation=named,
        old_name="T",
        new_name="V",
    )
    expect_equal(actual=plain.id, expected="V")
    subscript_value: Name = cast(typ="Name", val=subscript.value)
    expect_equal(actual=subscript_value.id, expected="V")


def test_decorator_detection_matches_names_and_attributes() -> None:
    """Match decorators spelled as names or attribute accesses."""
    module: Module = parse(
        source=dedent(
            text="""\
            @property
            def a(): ...
            @x.setter
            def b(): ...
            @other(1)
            def c(): ...
            """,
        ),
    )
    functions: list[FunctionDef] = [
        cast(typ="FunctionDef", val=item) for item in module.body
    ]
    first: FunctionDef = functions[0]
    second: FunctionDef = functions[1]
    third: FunctionDef = functions[2]
    expect_true(
        condition=GraphRefiner.has_decorator(
            function=first,
            decorator_name="property",
        ),
    )
    expect_true(
        condition=GraphRefiner.has_decorator(
            function=second,
            decorator_name="setter",
        ),
    )
    expect_false(
        condition=GraphRefiner.has_decorator(
            function=third,
            decorator_name="property",
        ),
    )


def test_post_refinement_service_formats_messages() -> None:
    """Refine a module and describe the outcome."""
    service: PostRefinementService = PostRefinementService.create()
    expect_is(actual=PostRefinementService, expected=ServiceFromModule)
    module: Module = parse(
        source="""\
def f(x):
    return x
f(1)
""",
    )
    result: RefinementResult = service.refine(module=module)
    message: str = service.message_for(result=result)
    expect_true(condition=message.startswith("generic-refinements: "))
