"""Native symbol edits share one graph and preserve reference scopes."""

from __future__ import annotations

from ast import AnnAssign, Constant, Load, Name, Store, arg, expr, walk
from ast import parse as parse_expression
from typing import TYPE_CHECKING

import pytest
from astart import parse
from astart.rules.appliers import annotation_expression

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_is,
    expect_not_none,
)

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.semantic.analyzer import SymbolRegistry
    from astart.semantic.identities import Symbol


def test_rebind_changes_only_resolved_reads_and_invalidates_inference() -> (
    None
):
    """Shadowed variables, attribute labels and string values are separate."""
    tree: CommentedModule = parse(
        source=(
            "old = 1\nnew = 2\na = old\nb = old\n"
            "text = 'old'\nlabel = obj.old\n"
            "def f(old):\n    return old\n"
        ),
    )
    symbols: SymbolRegistry = tree.semantic.symbols
    old: Symbol = expect_not_none(value=symbols.resolve(name="old"))
    new: Symbol = expect_not_none(value=symbols.resolve(name="new"))
    references: tuple[Name, ...] = tuple(
        node
        for node in symbols.references(symbol_id=old.id)
        if isinstance(node, Name)
    )
    before: tuple[int, ...] = tuple(id(node) for node in references)
    expect_equal(
        actual=symbols.rebind(symbol_id=old.id, target_id=new.id),
        expected=2,
    )
    expect_equal(
        actual=tuple(id(node) for node in references),
        expected=before,
    )
    output: str = tree.unparse(preserve_formatting=True)
    expect_in(
        item="""\
a = new
b = new""",
        container=output,
    )
    expect_in(item="text = 'old'", container=output)
    expect_in(item="obj.old", container=output)
    expect_in(item="return old", container=output)
    expect_equal(
        actual=tree.infer_type(node="a").inferred.name,
        expected="int",
    )


def test_native_binding_rejects_capture_atomically() -> None:
    """A conflicting inner scope cannot leave an earlier read half rebound."""
    tree: CommentedModule = parse(
        source=(
            """\
old = 1
new = 2
a = old
def f(new):
    return old
"""
        ),
    )
    old: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="old"),
    )
    new: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="new"),
    )
    before: str = tree.unparse(preserve_formatting=True)
    with pytest.raises(expected_exception=ValueError, match="capture"):
        tree.semantic.symbols.rebind(symbol_id=old.id, target_id=new.id)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=before,
    )


def test_annotation_bindings_preserve_payloads() -> None:
    """Later renaming the import updates every real generated reference."""
    tree: CommentedModule = parse(
        source=(
            """\
from typing import Self as Current
Self = 42
"""
        ),
    )
    expression: expr = annotation_expression(
        node=parse_expression(
            source=(
                'tuple[Self, Literal["Self"], '
                'Annotated[Self, "Self", Self], ns.Self]'
            ),
            mode="eval",
        ).body,
        names={"Self": "Current"},
        symbols=tree.semantic.symbols,
    )
    statement: AnnAssign = AnnAssign(
        target=Name(id="value", ctx=Store()),
        annotation=expression,
        value=None,
        simple=1,
    )
    tree.body.append(statement)
    imported: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="Current"),
    )
    selected: tuple[Name, ...] = tuple(
        node
        for node in walk(node=expression)
        if isinstance(node, Name) and node.id == "Current"
    )
    expect_equal(actual=len(selected), expected=2)
    tree.semantic.symbols.rename(symbol_id=imported.id, new_name="Renamed")
    for node in selected:
        expect_equal(actual=node.id, expected="Renamed")
        expect_equal(
            actual=expect_not_none(value=tree.semantic.symbol(node=node)).id,
            expected=imported.id,
        )
    expect_equal(
        actual=sum(
            isinstance(node, Constant) and node.value == "Self"
            for node in walk(node=expression)
        ),
        expected=2,
    )
    expect_equal(
        actual=sum(
            isinstance(node, Name) and node.id == "Self"
            for node in walk(node=expression)
        ),
        expected=1,
    )
    expect_is(actual=statement.annotation, expected=expression)


def test_foreign_subtree_is_rejected_before_reference_changes() -> None:
    """Selection uses owned node identities rather than matching text."""
    tree: CommentedModule = parse(
        source="""\
a=1
b=2
x=a
""",
    )
    first: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="a"),
    )
    second: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="b"),
    )
    with pytest.raises(expected_exception=ValueError, match="source graph"):
        tree.semantic.symbols.rebind(
            symbol_id=first.id,
            target_id=second.id,
            within=parse(
                source="""\
x=a
""",
            ),
        )


def test_parameter_rename_updates_only_bound_keyword_labels() -> None:
    """Calls to a different function with the same spelling stay untouched."""
    tree: CommentedModule = parse(
        source=(
            "def first(old):\n    return old\n"
            "def second(old):\n    return old\n"
            "a = first(old=1)\nb = second(old=2)\n"
        ),
    )
    parameter: arg = next(
        node
        for node in walk(node=tree.body[0])
        if isinstance(node, arg) and node.arg == "old"
    )
    symbol: Symbol = expect_not_none(
        value=tree.semantic.symbol(node=parameter),
    )
    tree.semantic.symbols.rename(symbol_id=symbol.id, new_name="value")
    output: str = tree.unparse(preserve_formatting=True)
    expect_in(item="def first(value):", container=output)
    expect_in(item="return value", container=output)
    expect_in(item="first(value=1)", container=output)
    expect_in(item="second(old=2)", container=output)


def test_expanded_keyword_call_is_rejected_before_renaming() -> None:
    """Unknown or expanded labels cannot be left stale after a rename."""
    tree: CommentedModule = parse(
        source=(
            """\
def f(old):
    return old
result=f(**{'old': 1})
"""
        ),
    )
    parameter: arg = next(
        node for node in walk(node=tree.body[0]) if isinstance(node, arg)
    )
    symbol: Symbol = expect_not_none(
        value=tree.semantic.symbol(node=parameter),
    )
    before: str = tree.unparse(preserve_formatting=True)
    with pytest.raises(expected_exception=ValueError, match="expansion"):
        tree.semantic.symbols.rename(symbol_id=symbol.id, new_name="value")
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected=before,
    )


def test_unindexed_foreign_reference_is_not_a_fresh_proposal() -> None:
    """Lexical ownership exists before the foreign semantic graph is built."""
    tree: CommentedModule = parse(
        source="""\
target=1
""",
    )
    foreign: CommentedModule = parse(
        source="""\
x=original
""",
    )
    reference: Name = next(
        node
        for node in walk(node=foreign)
        if isinstance(node, Name) and isinstance(node.ctx, Load)
    )
    target: Symbol = expect_not_none(
        value=tree.semantic.symbols.resolve(name="target"),
    )
    with pytest.raises(expected_exception=ValueError, match="source graph"):
        tree.semantic.symbols.bind_references(bindings={reference: target.id})
    expect_equal(actual=reference.id, expected="original")
