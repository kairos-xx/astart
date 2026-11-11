"""Check annotation transaction identity and rollback safety."""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    Call,
    Constant,
    FunctionDef,
    ImportFrom,
    Load,
    Name,
    Store,
    alias,
    arg,
    dump,
    expr,
    keyword,
    stmt,
)
from copy import copy
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from astart.source.ast import CommentedModule
from astart.source.formatting import FormatPreserver

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_instance,
    expect_is,
    expect_true,
)

if TYPE_CHECKING:
    from astart.docstrings import DocEntry
    from astart.source.formatting import EmissionPlan
    from astart.source.transactions import AnnotationTransaction


def _function(*, tree: CommentedModule, index: int = 0) -> FunctionDef:
    """Get a fixture function without coercing the native node type.

    Args:
        tree (CommentedModule): Existing native module.
        index (int): Function's statement position.

    Returns:
        FunctionDef: The same function node.

    """
    return expect_instance(value=tree.body[index], kind=FunctionDef)


def test_annotation_batch_commits_without_parsing_or_cloning() -> None:
    """Validate a batch on one AST and retain executable identities."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x
""",
    )
    owner: FunctionDef = _function(tree=tree)
    parameter: arg = owner.args.args[0]
    transaction: AnnotationTransaction = tree.annotation_transaction()
    annotation: Name = Name(id="int", ctx=Load())
    transaction.replace(owner=parameter, field="annotation", value=annotation)
    transaction.replace(
        owner=owner,
        field="returns",
        value=Name(id="int", ctx=Load()),
    )
    expect_is(actual=parameter.annotation, expected=None)
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        changed: tuple[AST, ...] = transaction.commit()
    expect_equal(actual=changed, expected=(parameter, owner))
    expect_is(actual=tree.body[0], expected=owner)
    expect_is(actual=parameter.annotation, expected=annotation)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
def f(x: int) -> int:
    return x
""",
    )


def test_failed_annotation_batch_restores_original_references() -> None:
    """Roll back every staged field after a compiler rejection."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x: str):
    return x
""",
    )
    owner: FunctionDef = _function(tree=tree)
    parameter: arg = owner.args.args[0]
    original: expr | None = parameter.annotation
    before: str = dump(node=tree, include_attributes=True)
    invalid: Name = Name(id="int", ctx=Store())
    proposal: str = dump(node=invalid, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(
        owner=parameter,
        field="annotation",
        value=Name(id="int", ctx=Load()),
    )
    transaction.replace(owner=owner, field="returns", value=invalid)
    with pytest.raises(expected_exception=ValueError, match="Load"):
        transaction.commit()
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )
    expect_is(actual=parameter.annotation, expected=original)
    expect_equal(
        actual=dump(node=invalid, include_attributes=True),
        expected=proposal,
    )


def test_stale_transaction_preserves_external_edits() -> None:
    """Never restore over an external mutation made after staging began."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x
""",
    )
    owner: FunctionDef = _function(tree=tree)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(
        owner=owner,
        field="returns",
        value=Name(id="int", ctx=Load()),
    )
    owner.name = "renamed"
    with pytest.raises(expected_exception=ValueError, match="stale"):
        transaction.commit()
    expect_equal(actual=owner.name, expected="renamed")
    expect_is(actual=owner.returns, expected=None)


def test_annotation_import_cannot_capture_a_builtin_call() -> None:
    """A new dependency must not replace an existing builtin operation."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
result = pow(2, 3, 5)
""",
    )
    before: str = dump(node=tree, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(
        declaration=ImportFrom(
            module="math",
            names=[alias(name="pow")],
            level=0,
        ),
    )
    with pytest.raises(expected_exception=ValueError, match="conflicts"):
        transaction.commit()
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


def test_unresolved_existing_annotation_can_receive_its_import() -> None:
    """Unbound annotation dependencies remain eligible for explicit import."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(value: Sequence):
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    annotation: expr | None = owner.args.args[0].annotation
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(
        declaration=ImportFrom(
            module="collections.abc",
            names=[alias(name="Sequence")],
            level=0,
        ),
    )
    transaction.commit()
    expect_is(actual=owner.args.args[0].annotation, expected=annotation)


def test_identical_external_clone_still_invalidates_transaction() -> None:
    """Equal syntax does not imply stable source or ownership identity."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    pass
""",
    )
    transaction: AnnotationTransaction = tree.annotation_transaction()
    tree.body[0] = copy(x=tree.body[0])
    with pytest.raises(expected_exception=ValueError, match="stale"):
        transaction.commit()


def test_executable_fields_and_owned_aliases_are_rejected() -> None:
    """An annotation contract cannot rename bindings or alias syntax."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x: str):
    return x
""",
    )
    owner: FunctionDef = _function(tree=tree)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    with pytest.raises(expected_exception=ValueError, match="executable"):
        transaction.replace(owner=owner, field="name", value=None)
    transaction.replace(
        owner=owner,
        field="returns",
        value=owner.args.args[0].annotation,
    )
    with pytest.raises(expected_exception=ValueError, match="aliases"):
        transaction.commit()
    expect_is(actual=owner.returns, expected=None)


def test_cancelled_transaction_and_invalid_identifiers_do_not_mutate() -> None:
    """Cancelled or unspellable proposals never reach the real tree."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    cancelled: AnnotationTransaction = tree.annotation_transaction()
    cancelled.replace(
        owner=owner,
        field="returns",
        value=Name(id="int", ctx=Load()),
    )
    cancelled.cancel()
    with pytest.raises(expected_exception=ValueError, match="closed"):
        cancelled.commit()
    invalid: AnnotationTransaction = tree.annotation_transaction()
    invalid.replace(
        owner=owner,
        field="returns",
        value=Name(id="not valid", ctx=Load()),
    )
    with pytest.raises(expected_exception=ValueError, match="identifier"):
        invalid.commit()
    expect_is(actual=owner.returns, expected=None)


def test_live_emitter_publishes_rebase_plan_for_untouched_nodes() -> None:
    """Expose validated untouched-span shifts on the live lexical path."""
    source: str = """\
x = 1
unchanged = 2
"""
    tree: CommentedModule = CommentedModule.parse(source=source)
    assignment: Assign = expect_instance(value=tree.body[0], kind=Assign)
    value: Constant = expect_instance(value=assignment.value, kind=Constant)
    value.value = 1234
    output: str = tree.unparse(preserve_formatting=True)
    plan: EmissionPlan | None = tree.emission_plan
    if plan is None:
        pytest.fail(reason="lexical emission did not publish a plan")
    start: int = source.index("unchanged")
    expect_equal(
        actual=plan.rebase(start=start, end=len(source)),
        expected=(start + 3, len(source) + 3),
    )
    expect_equal(
        actual=output,
        expected="""\
x = 1234
unchanged = 2
""",
    )


def test_interrupted_validation_rolls_back_every_applied_field() -> None:
    """Cancellation propagates while the original tree remains intact."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    before: str = dump(node=tree, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(
        owner=owner,
        field="returns",
        value=Name(id="int", ctx=Load()),
    )
    with (
        pytest.raises(expected_exception=KeyboardInterrupt),
        patch(target="builtins.compile", side_effect=KeyboardInterrupt),
    ):
        transaction.commit()
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


@pytest.mark.parametrize(
    argnames="name",
    argvalues=["not valid", "class", "\u212a"],
)
def test_unspellable_keyword_annotations_fail_before_mutation(
    *,
    name: str,
) -> None:
    """AST compiler permissiveness must not admit invalid source keywords.

    Args:
        name (str): Invalid or noncanonical keyword identifier.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    proposal: Call = Call(
        func=Name(id="T", ctx=Load()),
        args=[],
        keywords=[
            keyword(arg=name, value=Constant(value=1)),
        ],
    )
    before: str = dump(node=proposal, include_attributes=True)
    transaction.replace(owner=owner, field="returns", value=proposal)
    with pytest.raises(expected_exception=ValueError, match="identifier"):
        transaction.commit()
    expect_is(actual=owner.returns, expected=None)
    expect_equal(
        actual=dump(node=proposal, include_attributes=True),
        expected=before,
    )


def test_noop_batch_needs_no_compilation() -> None:
    """Skip compilation for no-op batches while retaining identity."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f() -> int:
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(owner=owner, field="returns", value=owner.returns)
    with patch(target="builtins.compile", side_effect=AssertionError):
        expect_equal(actual=transaction.commit(), expected=())


def test_annotation_commit_updates_derived_doc_links_without_reparsing() -> (
    None
):
    """A new return annotation replaces an existing Return-statement link."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            'def f(x):\n    """Return a value.\n\n    Returns:\n'
            '        TODO.\n    """\n    return x\n'
        ),
    )
    owner: FunctionDef = _function(tree=tree)
    entry: DocEntry = tree.docstrings[0].entries(kind="returns")[0]
    annotation: Name = Name(id="int", ctx=Load())
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(owner=owner, field="returns", value=annotation)
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        transaction.commit()
    expect_is(actual=entry.target, expected=annotation)
    expect_equal(actual=entry.link_role, expected="return_annotation")
    expect_equal(actual=entry.description, expected="TODO.")


def test_annotation_import_batch_preserves_preamble_and_owned_lists() -> None:
    """Commit dependencies and annotations together without parsing."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            '"""Module documentation."""\n'
            "from __future__ import annotations\n"
            "# Keep this function comment.\n"
            "def f(x):\n    return x\n"
        ),
    )
    owner: FunctionDef = _function(tree=tree, index=2)
    body: list[stmt] = tree.body
    declaration: ImportFrom = ImportFrom(
        module="collections.abc",
        names=[alias(name="Sequence")],
        level=0,
    )
    proposal: str = dump(node=declaration, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(declaration=declaration)
    transaction.replace(
        owner=owner.args.args[0],
        field="annotation",
        value=Name(id="Sequence", ctx=Load()),
    )
    expect_equal(actual=len(body), expected=3)
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        changed: tuple[AST, ...] = transaction.commit()
    expect_equal(actual=changed, expected=(declaration, owner.args.args[0]))
    expect_is(actual=tree.body, expected=body)
    expect_is(actual=tree.body[2], expected=declaration)
    expect_is(actual=tree.body[3], expected=owner)
    expect_equal(
        actual=dump(node=declaration, include_attributes=True),
        expected=proposal,
    )
    output: str = tree.unparse(preserve_formatting=True)
    expect_true(
        condition=output.index("from __future__")
        < output.index("from collections.abc"),
    )
    expect_in(item="# Keep this function comment.", container=output)
    expect_in(item="def f(x: Sequence):", container=output)


@pytest.mark.parametrize(
    argnames="source",
    argvalues=[
        """\
# Header
value  = '\u00e9'
# Footer
""",
        """\
value = '\u00e9'\r
""",
        "value = 1",
        "# Header",
        "",
        """\
from __future__ import annotations

value = 1
""",
    ],
)
def test_import_emission_rebases_original_spans_without_parsing(
    *,
    source: str,
) -> None:
    """Import insertion keeps source fragments and their rebase mappings.

    Args:
        source (str): Original lexical boundary, encoding and newline cases.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    formatter: FormatPreserver = FormatPreserver(source=source, body=tree.body)
    existing: tuple[stmt, ...] = tuple(tree.body)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(
        declaration=ImportFrom(
            module="typing",
            names=[alias(name="Self")],
            level=0,
        ),
    )
    transaction.commit()
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        plan: EmissionPlan = formatter.plan(
            body=tree.body,
            comments=[],
            revision=0,
        )
        output: str = plan.render(source=source, revision=0)
    expect_in(item="from typing import Self", container=output)
    for node in existing:
        original: tuple[int, int] | None = formatter.original_span(node=node)
        if original is None:
            pytest.fail(reason="original statement has no source span")
        rebased: tuple[int, int] | None = plan.rebase(
            start=original[0],
            end=original[1],
        )
        if rebased is None:
            pytest.fail(reason="import insertion replaced untouched syntax")
        expect_equal(
            actual=output[rebased[0] : rebased[1]],
            expected=source[original[0] : original[1]],
        )
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=output,
    )


@pytest.mark.parametrize(argnames="interrupted", argvalues=[False, True])
def test_failed_import_batch_restores_body_and_proposals(
    *,
    interrupted: bool,
) -> None:
    """A compiler failure or interruption rolls back imports in place.

    Args:
        interrupted (bool): Whether cancellation interrupts compiler
            validation.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f():
    pass
""",
    )
    owner: FunctionDef = _function(tree=tree)
    body: list[stmt] = tree.body
    before: str = dump(node=tree, include_attributes=True)
    declaration: ImportFrom = ImportFrom(
        module="typing",
        names=[alias(name="Self")],
        level=0,
    )
    proposal: str = dump(node=declaration, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(declaration=declaration)
    transaction.replace(
        owner=owner,
        field="returns",
        value=Name(id="Self", ctx=Store()),
    )
    if interrupted:
        with (
            pytest.raises(expected_exception=KeyboardInterrupt),
            patch(target="builtins.compile", side_effect=KeyboardInterrupt),
        ):
            transaction.commit()
    else:
        with pytest.raises(expected_exception=ValueError, match="Load"):
            transaction.commit()
    expect_is(actual=tree.body, expected=body)
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )
    expect_equal(
        actual=dump(node=declaration, include_attributes=True),
        expected=proposal,
    )


@pytest.mark.parametrize(
    argnames="source",
    argvalues=[
        """\
Self = 1
""",
        """\
def f(Self):
    pass
""",
        """\
from typing import Self
""",
        """\
try:
    pass
except Exception as Self:
    pass
""",
        """\
match value:
    case {'x': Self}:
        pass
""",
        """\
match value:
    case {**Self}:
        pass
""",
        """\
def f[Self]():
    pass
""",
        """\
result = Self()
""",
        """\
from external import *
""",
    ],
)
def test_annotation_import_refuses_binding_conflicts(*, source: str) -> None:
    """Conservatively refuse existing bindings in any scope.

    Args:
        source (str): A binding that could capture the imported annotation
            name.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    before: str = dump(node=tree, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(
        declaration=ImportFrom(
            module="typing",
            names=[alias(name="Self")],
            level=0,
        ),
    )
    with pytest.raises(expected_exception=ValueError, match="conflicts"):
        transaction.commit()
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


@pytest.mark.parametrize(
    argnames=("module", "name", "asname", "level"),
    argvalues=[
        ("__future__", "annotations", None, 0),
        ("typing", "*", None, 0),
        ("typing", "Self", "Alias", 0),
        ("typing", "Self", None, 1),
        ("not valid", "Self", None, 0),
        ("typing", "\u212a", None, 0),
    ],
)
def test_unsupported_annotation_imports_leave_tree_unchanged(
    *,
    module: str,
    name: str,
    asname: str | None,
    level: int,
) -> None:
    """Reject undeclared binding or compiler-flag changes before commit.

    Args:
        module (str): Proposed dependency module.
        name (str): Proposed imported name.
        asname (str | None): Proposed alias.
        level (int): Relative import level.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
value = 1
""",
    )
    before: str = dump(node=tree, include_attributes=True)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.add_import(
        declaration=ImportFrom(
            module=module,
            names=[alias(name=name, asname=asname)],
            level=level,
        ),
    )
    with pytest.raises(expected_exception=ValueError, match="Unsupported"):
        transaction.commit()
    expect_equal(
        actual=dump(node=tree, include_attributes=True),
        expected=before,
    )


@pytest.mark.parametrize(argnames="nested", argvalues=[False, True])
def test_equal_list_replacement_still_invalidates_transaction(
    *,
    nested: bool,
) -> None:
    """Track container identities even when every child remains the same.

    Args:
        nested (bool): Whether the replaced list belongs to a function's
            arguments.

    """
    tree: CommentedModule = CommentedModule.parse(
        source="""\
def f(x):
    return x
""",
    )
    owner: FunctionDef = _function(tree=tree)
    transaction: AnnotationTransaction = tree.annotation_transaction()
    transaction.replace(
        owner=owner,
        field="returns",
        value=Name(id="int", ctx=Load()),
    )
    if nested:
        owner.args.args = list(owner.args.args)
    else:
        tree.body = list(tree.body)
    with pytest.raises(expected_exception=ValueError, match="stale"):
        transaction.commit()
    expect_is(actual=owner.returns, expected=None)
