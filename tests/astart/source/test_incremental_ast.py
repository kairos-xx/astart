"""Regression tests for incremental coordinates and PEP 701 f-string edits."""

from __future__ import annotations

from ast import (
    Assign,
    AugAssign,
    BinOp,
    BoolOp,
    Compare,
    Constant,
    Eq,
    FormattedValue,
    IsNot,
    JoinedStr,
    Load,
    Name,
    Or,
    Store,
    Sub,
    UnaryOp,
    USub,
    arg,
    dump,
    parse,
    stmt,
    walk,
)
from dataclasses import FrozenInstanceError
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.source.ast import CommentedModule, CommentGroup
from astart.source.delta import ChangeSet, NodeChange, SourceChange
from astart.source.formatting import FormatPreservationError
from astart.source.tokens import LexicalToken

from tests.support.expectations import (
    FunctionStatement,
    expect_binary_expr,
    expect_call_expr,
    expect_elements_expr,
    expect_equal,
    expect_function_node,
    expect_in,
    expect_instance,
    expect_is,
    expect_is_not,
    expect_name_expr,
    expect_not_equal,
    expect_not_in,
    expect_not_none,
    expect_suite_node,
    expect_true,
    expect_value_stmt,
    expect_values_expr,
    expression_of_stmt,
)

if TYPE_CHECKING:
    from astart.docstrings import DocEntry
    from astart.source.tokens import LexicalToken, TokenSnapshot


def _tree(*, source: str) -> CommentedModule:
    """Create and initialize a formatting-preserving source-map baseline.

    Args:
        source (str): The source examined while create and initialize a
            formatting-preserving source-map baseline.

    Returns:
        CommentedModule: CommentedModule produced by this operation.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source,
    )
    expect_equal(actual=tree.token_source, expected=source)
    return tree


def _first_field(*, tree: CommentedModule) -> FormattedValue:
    """Get the first embedded replacement expression from an assignment.

    Args:
        tree (CommentedModule): Tree supplied as CommentedModule for this
            operation.

    Returns:
        FormattedValue: FormattedValue produced by this operation.

    """
    statement: Assign = expect_instance(value=tree.body[0], kind=Assign)
    expect_instance(value=statement.value, kind=JoinedStr)
    return next(
        value
        for value in expect_values_expr(value=statement.value).values
        if isinstance(value, FormattedValue)
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
x=f'hello {user + 1!r:>{width}.{precision}f} done'
""",
            """\
x=f'hello {client + 1!r:>{width}.{precision}f} done'
""",
        ),
        (
            """\
x=f"value: {user + 1}"
""",
            """\
x=f"value: {client + 1}"
""",
        ),
        (
            """\
x=f'''start:{user + 1!s:{width}}:end'''
""",
            """\
x=f'''start:{client + 1!s:{width}}:end'''
""",
        ),
    ],
)
def test_embedded_ast_name_edit_retains_fstring_spelling(
    source: str,
    expected: str,
) -> None:
    """Edit PEP 701 code without rebuilding f-string quotes or punctuation.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while edit PEP 701 code without
            rebuilding f-string quotes or punctuation.

    """
    tree: CommentedModule = _tree(source=source)
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    expect_name_expr(value=expression.left).id = "client"
    before: ChangeSet = tree.token_changes
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.left).source_text,
        expected="client",
    )
    expect_equal(actual=tree.token_source, expected=expected)
    expect_is_not(
        actual=before.for_node(node=expression.left),
        unexpected=None,
    )
    expect_equal(
        actual=dump(node=parse(source=expected)),
        expected=dump(
            node=parse(source=tree.token_source),
        ),
    )


@pytest.mark.parametrize(
    ("field_value", "expected"),
    [(115, "!s"), (97, "!a"), (-1, "")],
)
def test_fstring_conversion_is_localized(
    field_value: int,
    expected: str,
) -> None:
    """Change only a conversion modifier, keeping the dynamic format spec.

    Args:
        expected (str): Expected supplied as str for this operation.
        field_value (int): Field value supplied as int for this operation.

    """
    source: str = """\
x = f'{n!r:>{width}}'
"""
    tree: CommentedModule = _tree(source=source)
    _first_field(tree=tree).conversion = field_value
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=f"""\
x = f'{{n{expected}:>{{width}}}}'
""",
    )


def test_fstring_conversion_insertion_and_removal() -> None:
    """Insert and later remove an explicit conversion from one field."""
    tree: CommentedModule = _tree(
        source="""\
x=f"{value:>8}"
""",
    )
    field: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    field.conversion = 114
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f"{value!r:>8}"
""",
    )
    field.conversion = -1
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f"{value:>8}"
""",
    )


def test_deep_format_spec_expression_preserves_original() -> None:
    """Preserve format alignment while modifying its nested Python syntax."""
    source: str = """\
x = f'{total!r:>{width + 2}.{precision}f}'
"""
    tree: CommentedModule = _tree(source=source)
    field: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    width: BinOp = expect_instance(
        value=expect_instance(
            value=expect_instance(
                value=expect_not_none(value=field.format_spec),
                kind=JoinedStr,
            ).values[1],
            kind=FormattedValue,
        ).value,
        kind=BinOp,
    )
    width.op = Sub()
    expect_name_expr(value=width.left).id = "size"
    result: str = tree.unparse(preserve_formatting=True)
    expect_equal(
        actual=result,
        expected="""\
x = f'{total!r:>{size - 2}.{precision}f}'
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=width.left).source_text,
        expected="size",
    )
    expect_equal(
        actual=tree.token_snapshot(node=width).source_text,
        expected="size - 2",
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
x=f'a {value} z'
""",
            """\
x=f'{{key}} {value} z'
""",
        ),
        (
            """\
x=f'hello {value} z'
""",
            """\
x=f'{{key}} {value} z'
""",
        ),
        (
            """\
x=f"a {value} z"
""",
            """\
x=f"{{key}} {value} z"
""",
        ),
    ],
)
def test_literal_segments_keep_original_fstring_quotes(
    source: str,
    expected: str,
) -> None:
    """Edit decoded FString_MIDDLE contents, escaping braces when required.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while edit decoded FString_MIDDLE
            contents, escaping braces when required.

    """
    tree: CommentedModule = _tree(source=source)
    statement: Assign = expect_instance(value=tree.body[0], kind=Assign)
    expect_instance(
        value=expect_values_expr(value=statement.value).values[0],
        kind=Constant,
    ).value = "{key} "
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )


def test_nested_fstrings_are_regular_ast_expressions() -> None:
    """Token-map and mutate embedded PEP 701 f-strings several levels deep."""
    source: str = """x = f'{f"deep {amount + (2 * factor)!r}"!s}'\n"""
    tree: CommentedModule = _tree(source=source)
    outer: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    expect_instance(value=outer.value, kind=JoinedStr)
    inner: FormattedValue = expect_instance(
        value=expect_values_expr(value=outer.value).values[1],
        kind=FormattedValue,
    )
    expect_name_expr(
        value=expect_binary_expr(
            value=expect_binary_expr(value=inner.value).right,
        ).right,
    ).id = "rate"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""x = f'{f"deep {amount + (2 * rate)!r}"!s}'\n""",
    )
    expect_equal(
        actual=tree.token_snapshot(
            node=expect_binary_expr(
                value=expect_binary_expr(value=inner.value).right,
            ).right,
        ).source_text,
        expected="rate",
    )
    expect_instance(
        value=expect_binary_expr(
            value=expect_binary_expr(value=inner.value).right,
        ).right,
        kind=Name,
    )


def test_pep701_comment_in_embedded_expression_survives() -> None:
    """Comments inside multiline f-string Python expressions remain intact."""
    source: str = """\
x = f'''{first # keep
+ second}'''
"""
    tree: CommentedModule = _tree(source=source)
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    expect_name_expr(value=expression.right).id = "other"
    result: str = tree.unparse(preserve_formatting=True)
    expect_equal(
        actual=result,
        expected="""\
x = f'''{first # keep
+ other}'''
""",
    )
    expect_true(
        condition=any(token.string == "# keep" for token in tree.token_stream),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """\
x = f'{value=}'
""",
            """\
x = f'value={other!r}'
""",
        ),
        (
            """\
x = f'{value = !r}'
""",
            """\
x = f'value = {other!r}'
""",
        ),
        (
            """\
x = f'{value= !s:>5}'
""",
            """\
x = f'value= {other!s:>5}'
""",
        ),
        (
            """\
x = f'{value= :>5}'
""",
            """\
x = f'value= {other:>5}'
""",
        ),
    ],
)
def test_fstring_debug_label_does_not_change_when_code_renamed(
    source: str,
    expected: str,
) -> None:
    """Debug labels survive code replacement and expression renames.

    Args:
        expected (str): Expected supplied as str for this operation.
        source (str): The source examined while debug labels survive code
            replacement and expression renames.

    """
    tree: CommentedModule = _tree(source=source)
    expect_name_expr(value=_first_field(tree=tree).value).id = "other"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )


def test_nested_function_call_replacement_only_changes_expression() -> None:
    """A call-argument mutation localizes canonical fallback in the field."""
    source: str = """\
x = f'{foo(  12, 13, )!s:>6}'
"""
    tree: CommentedModule = _tree(source=source)
    expect_call_expr(value=_first_field(tree=tree).value).args.append(
        Constant(value=3),
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x = f'{foo(12, 13, 3)!s:>6}'
""",
    )


def test_move_classification_does_not_treat_insertion_as_move() -> None:
    """Inserting before siblings moves coordinates but not node identities."""
    tree: CommentedModule = _tree(
        source="""\
first=1
second=2
third=3
""",
    )
    first: Assign = expect_instance(value=tree.body[0], kind=Assign)
    second: Assign = expect_instance(value=tree.body[1], kind=Assign)
    third: Assign = expect_instance(value=tree.body[2], kind=Assign)
    prior: tuple[int, int] = (
        tree.token_snapshot(node=second).span.start_line,
        tree.token_snapshot(node=third).span.start_line,
    )
    tree.body.insert(
        0,
        Assign(
            targets=[Name(id="new", ctx=Store())],
            value=Constant(value=0),
        ),
    )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
new = 0
first=1
second=2
third=3
""",
    )
    delta: ChangeSet = tree.token_changes
    expect_not_in(item=id(first), container=delta.moved)
    expect_not_in(item=id(second), container=delta.moved)
    expect_not_in(item=id(third), container=delta.moved)
    expect_equal(
        actual=(
            tree.token_snapshot(node=second).span.start_line,
            tree.token_snapshot(node=third).span.start_line,
        ),
        expected=(
            prior[0] + 1,
            prior[1] + 1,
        ),
    )
    expect_equal(
        actual=expect_not_none(value=delta.for_node(node=second)).kind,
        expected="shifted",
    )
    expect_equal(
        actual=expect_not_none(value=delta.for_node(node=third)).line_shift,
        expected=1,
    )
    expect_equal(
        actual=delta.source_changes,
        expected=(
            SourceChange(old_start=1, old_end=1, new_start=1, new_end=2),
        ),
    )


def test_sibling_move_marks_only_moved_identity() -> None:
    """Structural LIS excludes merely shifted siblings from move events."""
    tree: CommentedModule = _tree(
        source="""\
a=1
b=2
c=3
d=4
""",
    )
    moved: Assign = expect_instance(value=tree.body.pop(1), kind=Assign)
    tree.body.append(moved)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
a=1
c=3
d=4
b=2
""",
    )
    report: ChangeSet = tree.token_changes
    expect_equal(actual=report.moved, expected=(id(moved),))
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=moved)).kind,
        expected="moved",
    )
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=tree.body[1])).kind,
        expected="shifted",
    )
    expect_equal(
        actual=expect_not_none(
            value=report.for_node(node=tree.body[2]),
        ).line_shift,
        expected=-1,
    )
    expect_is(actual=report.for_node(node=tree.body[0]), expected=None)


def test_nested_subtree_shift_propagates_to_all_required_descendants() -> None:
    """A multiline insertion moves enclosed AST coordinates without edits."""
    source: str = dedent(
        text="""\
    def f():
        return 2

    def g():
        result = [1, 2, 3,]
        return result
    """,
    )
    tree: CommentedModule = _tree(source=source)
    lower: Assign = expect_instance(
        value=expect_suite_node(value=tree.body[1]).body[0],
        kind=Assign,
    )
    constant: Constant = expect_instance(
        value=expect_elements_expr(value=lower.value).elts[1],
        kind=Constant,
    )
    previous_span: int = tree.token_snapshot(node=constant).span.start_line
    tree.body.insert(
        1,
        parse(
            source="""\
def middle():
    return 20
""",
        ).body[0],
    )
    result: str = tree.unparse(preserve_formatting=True)
    expect_in(item="result = [1, 2, 3,]", container=result)
    expect_equal(
        actual=tree.token_snapshot(node=constant).span.start_line,
        expected=previous_span + 2,
    )
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=constant),
        ).line_shift,
        expected=2,
    )
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=lower),
        ).kind,
        expected="shifted",
    )


def test_nested_literal_edit_propagates_to_enclosing_fstring_nodes() -> None:
    """An expression edit invalidates f-string and module snapshots."""
    tree: CommentedModule = _tree(
        source="""\
value = f'{a + (b * 2)!r}'
""",
    )
    root: JoinedStr = expect_instance(
        value=expression_of_stmt(value=tree.body[0]),
        kind=JoinedStr,
    )
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    target: Constant = expect_instance(
        value=expect_binary_expr(value=expression.right).right,
        kind=Constant,
    )
    old_root: TokenSnapshot = tree.token_snapshot(node=root)
    old_target: TokenSnapshot = tree.token_snapshot(node=target)
    target.value = 7
    result: str = tree.unparse(preserve_formatting=True)
    expect_equal(
        actual=result,
        expected="""\
value = f'{a + (b * 7)!r}'
""",
    )
    report: ChangeSet = tree.token_changes
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=target)).kind,
        expected="modified",
    )
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=expression)).kind,
        expected="modified",
    )
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=root)).kind,
        expected="modified",
    )
    expect_is_not(
        actual=tree.token_snapshot(node=target),
        unexpected=old_target,
    )
    expect_is_not(actual=tree.token_snapshot(node=root), unexpected=old_root)
    expect_equal(actual=old_target.source_text, expected="2")


def test_new_revision_does_not_mutate_old_frozen_token_info() -> None:
    """Snapshots remain stable even when newer generations shift positions."""
    tree: CommentedModule = _tree(
        source="""\
x=1
y=2
""",
    )
    right: Assign = expect_instance(value=tree.body[-1], kind=Assign)
    old: TokenSnapshot = tree.token_snapshot(node=right)
    tree.body.insert(
        0,
        Assign(
            targets=[Name(id="z", ctx=Store())],
            value=Constant(value=9),
        ),
    )
    expect_true(condition=bool(tree.token_source))
    expect_equal(actual=old.span.start_line, expected=2)
    expect_equal(
        actual=tree.token_snapshot(node=right).span.start_line,
        expected=3,
    )
    expect_true(
        condition=tree.token_snapshot(node=right).source_revision
        > old.source_revision,
    )
    span_field: str = "start_line"
    with pytest.raises(expected_exception=FrozenInstanceError):
        setattr(old.span, span_field, 100)


def test_sibling_tokens_on_same_line_refresh_line_text() -> None:
    """TokenInfo.line is refreshed when an adjacent token stays in place."""
    tree: CommentedModule = _tree(
        source="""\
x = f'{left}-{right}'
""",
    )
    text: JoinedStr = expect_instance(
        value=expression_of_stmt(value=tree.body[0]),
        kind=JoinedStr,
    )
    before: tuple[LexicalToken, ...] = tree.token_snapshot(
        node=text.values[-1],
    ).tokens
    expect_name_expr(
        value=expect_instance(value=text.values[0], kind=FormattedValue).value,
    ).id = "longer"
    expect_true(condition=bool(tree.token_source))
    after: tuple[LexicalToken, ...] = tree.token_snapshot(
        node=text.values[-1],
    ).tokens
    expect_not_equal(actual=before, unexpected=after)
    expect_in(item="longer", container=after[0].line)


def test_cpython_interned_load_contexts_have_distinct_lexical_owners() -> None:
    """Shared AST context singleton must not conflate unrelated locations."""
    tree: CommentedModule = _tree(
        source="""\
first = second
third = fourth
""",
    )
    a: Load = expect_instance(
        value=expect_name_expr(
            value=expression_of_stmt(value=tree.body[0]),
        ).ctx,
        kind=Load,
    )
    b: Load = expect_instance(
        value=expect_name_expr(
            value=expression_of_stmt(value=tree.body[1]),
        ).ctx,
        kind=Load,
    )
    expect_is_not(actual=a, unexpected=b)
    expect_equal(
        actual=tree.token_snapshot(node=a).span.start_line,
        expected=1,
    )
    expect_equal(
        actual=tree.token_snapshot(node=b).span.start_line,
        expected=2,
    )
    expect_equal(actual=tree.token_changes.moved, expected=())


def test_semantic_link_change_is_reported_when_argument_changes() -> None:
    """DocEntry links follow their owning argument's AST identity."""
    source: str = dedent(
        text="""\
    def f(value: int) -> int:
        \"""Summary.

        Args:
            value (int): Number.
        \"""
        return value
    """,
    )
    tree: CommentedModule = _tree(source=source)
    parameter: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    entry: DocEntry = tree.docstrings[0].entries(kind="parameters")[0]
    expect_equal(
        actual=tree.semantic_dependents(node=parameter),
        expected=(entry,),
    )
    parameter.arg = "amount"
    expect_in(
        item="def f(amount: int)",
        container=tree.unparse(preserve_formatting=True),
    )
    changes: ChangeSet = tree.token_changes
    expect_in(
        item=(id(parameter), id(entry)),
        container=changes.semantic_links,
    )
    expect_is(actual=entry.target, expected=parameter)
    expect_equal(
        actual=tree.semantic_dependents(node=parameter),
        expected=(entry,),
    )


def test_detached_nodes_lose_token_owner_after_reconciliation() -> None:
    """An object removed from the live AST cannot return stale positions."""
    tree: CommentedModule = _tree(
        source="""\
a=1
b=2
""",
    )
    removed: Assign = expect_instance(value=tree.body.pop(), kind=Assign)
    expect_true(condition=bool(tree.token_source))
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=removed),
        ).kind,
        expected="removed",
    )
    with pytest.raises(expected_exception=ReferenceError):
        _ = tree.token_snapshot(node=removed)


def test_invalid_fstring_structural_rewrite_is_explicit_conflict() -> None:
    """Changing f-string value-list structure is never silently reformatted."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{a} end'
""",
    )
    expect_values_expr(
        value=expression_of_stmt(value=tree.body[0]),
    ).values.append(Constant(value=" new"))
    with pytest.raises(expected_exception=FormatPreservationError):
        tree.unparse(preserve_formatting=True)


def test_repeated_nested_edits_resolve_against_original_source() -> None:
    """Revisions must neither accumulate offset errors nor mutate old trees."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{alpha + beta!r}'
""",
    )
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    expect_name_expr(value=expression.left).id = "long_identifier"
    expect_in(item="long_identifier + beta", container=tree.token_source)
    expect_name_expr(value=expression.right).id = "other"
    expression.op = Sub()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f'{long_identifier - other!r}'
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.right).source_text,
        expected="other",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression).source_text,
        expected="long_identifier - other",
    )


def test_abstract_node_types_remain_native_ast_after_mutation() -> None:
    """PEP 701 objects retain native AST subclasses and remain compilable."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{a + b!r}'
""",
    )
    field: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    expect_instance(value=field.value, kind=BinOp)
    expect_binary_expr(value=field.value).op = Sub()
    result: str = tree.unparse(preserve_formatting=True)
    compile(source=result, filename="<fstring>", mode="exec")
    expect_true(
        condition=any(
            isinstance(node, FormattedValue) for node in walk(node=tree)
        ),
    )


def test_nested_arithmetic_operator_owns_exact_token_span() -> None:
    """Source ownership of a location-less ast.operator is token-precise."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{ a+((b *2))!r}'
""",
    )
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.op).source_text,
        expected="+",
    )
    before: TokenSnapshot = tree.token_snapshot(node=expression.op)
    expression.op = Sub()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f'{ a-((b *2))!r}'
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.op).source_text,
        expected="-",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.op).span.start_column,
        expected=before.span.start_column,
    )
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=expression.op),
        ).kind,
        expected="inserted",
    )


def test_nested_boolean_operation_preserves_noncanonical_spaces() -> None:
    """Change every logical connector without modifying surrounding trivia."""
    tree: CommentedModule = _tree(
        source="""\
x=f"{ alpha   and beta and   gamma }"
""",
    )
    expression: BoolOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BoolOp,
    )
    expression.op = Or()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f"{ alpha   or beta or   gamma }"
""",
    )


def test_nested_comparison_operator_spans_are_exact() -> None:
    """Multi-token comparisons map exactly and can be changed locally."""
    source: str = """\
x=f"{ alpha   is not  beta  <  gamma}"
"""
    tree: CommentedModule = _tree(source=source)
    expression: Compare = expect_instance(
        value=_first_field(tree=tree).value,
        kind=Compare,
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.ops[0]).source_text,
        expected="is not",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.ops[1]).source_text,
        expected="<",
    )
    expression.ops[0] = Eq()
    expression.ops[1] = IsNot()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f"{ alpha   ==  beta  is not  gamma}"
""",
    )
    expect_equal(
        actual=[
            tree.token_snapshot(node=item).source_text
            for item in expression.ops
        ],
        expected=["==", "is not"],
    )


def test_unary_operator_token_span_remains_separate_from_operand() -> None:
    """Sign changes preserve the original spacing inside an f-string field."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{+ amount !s}'
""",
    )
    expression: UnaryOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=UnaryOp,
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.op).source_text,
        expected="+",
    )
    expression.op = USub()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=f'{- amount !s}'
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.op).source_text,
        expected="-",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.operand).source_text,
        expected="amount",
    )


def test_shared_user_nodes_are_rejected_before_positional_mapping() -> None:
    """Explicitly reused executable nodes cannot own two disjoint locations."""
    tree: CommentedModule = _tree(
        source="""\
left = alpha
right = beta
""",
    )
    expect_value_stmt(value=tree.body[1]).value = expression_of_stmt(
        value=tree.body[0],
    )
    with pytest.raises(
        expected_exception=TypeError,
        match="multiple source locations",
    ):
        expect_true(condition=bool(tree.token_source))


def test_comment_group_identity_survives_unrelated_executable_edits() -> None:
    """Comment grouping must not synthesize false inserted/removed events."""
    source: str = """\
# one
# two

x=1
y=2
"""
    tree: CommentedModule = _tree(source=source)
    group: CommentGroup = next(
        block
        for block in tree.comment_blocks
        if isinstance(block, CommentGroup)
    )
    expect_instance(
        value=expect_instance(value=tree.body[-1], kind=Assign).value,
        kind=Constant,
    ).value = 5
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=source.replace(
            "y=2",
            "y=5",
        ),
    )
    expect_true(
        condition=any(block is group for block in tree.comment_blocks),
    )
    expect_is(actual=tree.token_changes.for_node(node=group), expected=None)


def test_first_read_after_parse_already_has_valid_incremental_baseline() -> (
    None
):
    """A caller need not explicitly request token_info before editing nodes."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
a=1
b=2
c=3
""",
    )
    second: Assign = expect_instance(value=tree.body[1], kind=Assign)
    tree.body.insert(
        0,
        Assign(
            targets=[Name(id="preface", ctx=Store())],
            value=Constant(value=0),
        ),
    )
    expect_true(
        condition=tree.unparse(preserve_formatting=True).startswith("""\
preface = 0
"""),
    )
    report: ChangeSet = tree.token_changes
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=second)).kind,
        expected="shifted",
    )
    expect_equal(
        actual=expect_not_none(value=report.for_node(node=second)).line_shift,
        expected=1,
    )
    expect_not_in(item=id(second), container=report.moved)


def test_no_change_reuses_exact_immutable_snapshot_instances() -> None:
    """Change propagation excludes lexically untouched earlier AST siblings."""
    tree: CommentedModule = _tree(
        source="""\
first=1
second=2
third=3
""",
    )
    first: Assign = expect_instance(value=tree.body[0], kind=Assign)
    info: TokenSnapshot = tree.token_snapshot(node=first)
    expect_instance(
        value=expect_instance(value=tree.body[-1], kind=Assign).value,
        kind=Constant,
    ).value = 99
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
first=1
second=2
third=99
""",
    )
    expect_is(actual=tree.token_snapshot(node=first), expected=info)
    expect_is(actual=tree.token_changes.for_node(node=first), expected=None)


def test_four_line_block_shifts_following_nodes_by_four_lines() -> None:
    """Coordinate deltas apply transitively to nested nodes after insertion."""
    tree: CommentedModule = _tree(
        source="""\
x=1
y=f'{a+2}'
z=3
""",
    )
    after: Assign = expect_instance(value=tree.body[1], kind=Assign)
    operand: Constant = expect_instance(
        value=expect_binary_expr(
            value=expect_instance(
                value=expect_values_expr(value=after.value).values[0],
                kind=FormattedValue,
            ).value,
        ).right,
        kind=Constant,
    )
    prior: int = tree.token_snapshot(node=operand).span.start_line
    tree.body.insert(
        1,
        parse(
            source=(
                """\
if True:
    one=1
    two=2
    three=3
"""
            ),
        ).body[0],
    )
    expect_true(
        condition=tree.unparse(preserve_formatting=True).startswith(
            """\
x=1
if True:
    one = 1
    two = 2
    three = 3
""",
        ),
    )
    expect_equal(
        actual=tree.token_snapshot(node=operand).span.start_line,
        expected=prior + 4,
    )
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=operand),
        ).line_shift,
        expected=4,
    )
    expect_equal(
        actual=expect_not_none(
            value=tree.token_changes.for_node(node=after),
        ).kind,
        expected="shifted",
    )


def test_semantic_links_repair_removed_argument_ownership() -> None:
    """Replacing a documented argument invalidates its stale AST reference."""
    source: str = dedent(
        text="""\
    def f(value: int):
        \"""Summary.

        Args:
            value (int): Number.
        \"""
        return 1
    """,
    )
    tree: CommentedModule = _tree(source=source)
    entry: DocEntry = tree.docstrings[0].entries(kind="parameters")[0]
    old: arg = expect_instance(
        value=expect_function_node(value=tree.body[0]).args.args[0],
        kind=arg,
    )
    expect_is(actual=entry.target, expected=old)
    expect_function_node(value=tree.body[0]).args.args[0] = arg(
        arg="replacement",
        annotation=None,
    )
    expect_true(condition=bool(tree.token_source))
    expect_is(actual=entry.target, expected=None)
    expect_equal(actual=tree.semantic_dependents(node=old), expected=())


def test_multiline_fstring_spec_edit_keeps_newlines_and_comments() -> None:
    """Multiline PEP 701 expression comments persist through nested changes."""
    source: str = """\
result=f'''{amount # explanation
+ more!r:>{width}}'''
"""
    tree: CommentedModule = _tree(source=source)
    field: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    expect_name_expr(
        value=expect_instance(
            value=expect_values_expr(
                value=expect_not_none(value=field.format_spec),
            ).values[1],
            kind=FormattedValue,
        ).value,
    ).id = "columns"
    expected: str = source.replace("{width}", "{columns}")
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=expected,
    )
    expect_equal(
        actual=tree.token_snapshot(
            node=expect_instance(
                value=expect_values_expr(
                    value=expect_not_none(value=field.format_spec),
                ).values[1],
                kind=FormattedValue,
            ).value,
        ).source_text,
        expected="columns",
    )


def test_deep_nested_fstring_literal_edit_fails_safely_when_unmappable() -> (
    None
):
    """An ambiguous constant is never emitted as quoted f-string syntax."""
    tree: CommentedModule = _tree(
        source="""\
x=f'{name=}'
""",
    )
    expect_instance(
        value=expect_values_expr(
            value=expression_of_stmt(value=tree.body[0]),
        ).values[0],
        kind=Constant,
    ).value = "arbitrary label="
    with pytest.raises(expected_exception=FormatPreservationError):
        tree.unparse(preserve_formatting=True)


def test_parse_baseline_reports_no_user_changes() -> None:
    """Parsing should establish the source baseline without mutation events."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
x=1
""",
    )
    expect_equal(actual=tree.token_changes.nodes, expected=())
    expect_equal(actual=tree.token_changes.source_changes, expected=())
    expect_equal(actual=tree.token_changes.moved, expected=())


def test_later_sibling_outside_move_region_keeps_snapshot_identity() -> None:
    """A move changes only intermediate siblings and the moved node."""
    tree: CommentedModule = _tree(
        source="""\
a=1
b=2
c=3
d=4
e=5
""",
    )
    last: Assign = expect_instance(value=tree.body[-1], kind=Assign)
    snapshot: TokenSnapshot = tree.token_snapshot(node=last)
    moving: Assign = expect_instance(value=tree.body.pop(1), kind=Assign)
    tree.body.insert(3, moving)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
a=1
c=3
d=4
b=2
e=5
""",
    )
    expect_is(actual=tree.token_snapshot(node=last), expected=snapshot)
    expect_equal(actual=tree.token_changes.moved, expected=(id(moving),))
    expect_is(actual=tree.token_changes.for_node(node=last), expected=None)


def test_operator_nodes_in_separate_expressions_are_distinct() -> None:
    """Interned ast.Add objects must not share token locations."""
    tree: CommentedModule = _tree(
        source="""\
a=x+y
b=p+q
""",
    )
    first: BinOp = expect_instance(
        value=expression_of_stmt(value=tree.body[0]),
        kind=BinOp,
    )
    second: BinOp = expect_instance(
        value=expression_of_stmt(value=tree.body[1]),
        kind=BinOp,
    )
    expect_is_not(actual=first.op, unexpected=second.op)
    expect_equal(
        actual=tree.token_snapshot(node=first.op).source_text,
        expected="+",
    )
    expect_equal(
        actual=tree.token_snapshot(node=second.op).source_text,
        expected="+",
    )
    expect_equal(
        actual=tree.token_snapshot(node=first.op).span.start_line,
        expected=1,
    )
    expect_equal(
        actual=tree.token_snapshot(node=second.op).span.start_line,
        expected=2,
    )


def test_utf8_positions_are_correct_after_nested_fstring_edit() -> None:
    """AST byte columns remain precise after non-ASCII f-string edits."""
    tree: CommentedModule = _tree(
        source="""\
résultat=f'café {montant+1}'
""",
    )
    expression: BinOp = expect_instance(
        value=_first_field(tree=tree).value,
        kind=BinOp,
    )
    before: int = tree.token_snapshot(node=expression.left).span.start_column
    expect_name_expr(value=expression.left).id = "somme"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
résultat=f'café {somme+1}'
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.left).span.start_column,
        expected=before,
    )
    expect_equal(
        actual=tree.token_snapshot(node=expression.left).source_text,
        expected="somme",
    )


def test_nested_python_string_quote_is_preserved_in_fstring() -> None:
    """A string constant in replacement-field code retains original quotes."""
    tree: CommentedModule = _tree(
        source="""\
x = f'{func("old", 2)!r}'
""",
    )
    field: FormattedValue = expect_instance(
        value=_first_field(tree=tree),
        kind=FormattedValue,
    )
    expect_instance(
        value=expect_call_expr(value=field.value).args[0],
        kind=Constant,
    ).value = "new"
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x = f'{func("new", 2)!r}'
""",
    )


def test_raw_fstring_literal_edit_keeps_raw_prefix_and_spelling() -> None:
    """Escaped newlines stay literal in an editable raw f-string segment."""
    tree: CommentedModule = _tree(
        source="""\
x=rf'raw {name}'
""",
    )
    expect_instance(
        value=expect_values_expr(
            value=expression_of_stmt(value=tree.body[0]),
        ).values[0],
        kind=Constant,
    ).value = r"path\segment "
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
x=rf'path\\segment {name}'
""",
    )


def test_augmented_assignment_operator_is_patchable_without_reformatting() -> (
    None
):
    """Source coordinates for an augmented operator cover the += token."""
    tree: CommentedModule = _tree(
        source="""\
count  +=  2
""",
    )
    assignment: AugAssign = expect_instance(value=tree.body[0], kind=AugAssign)
    expect_equal(
        actual=tree.token_snapshot(node=assignment.op).source_text,
        expected="+=",
    )
    assignment.op = Sub()
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
count  -=  2
""",
    )
    expect_equal(
        actual=tree.token_snapshot(node=assignment.op).source_text,
        expected="-=",
    )


def test_removed_nested_node_retains_old_parent_for_invalidation() -> None:
    """Deletion events preserve their original dependency owner."""
    tree: CommentedModule = _tree(
        source="""\
def f():
    x = 1
    return 2
""",
    )
    owner: FunctionStatement = expect_function_node(value=tree.body[0])
    removed: stmt = owner.body.pop(0)
    tree.refresh_token_index()
    change: NodeChange = expect_not_none(
        value=tree.token_changes.for_node(node=removed),
    )
    expect_equal(actual=change.kind, expected="removed")
    expect_equal(actual=change.parent_id, expected=id(owner))
