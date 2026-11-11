"""Apply many small AST edits and check source preservation fails closed."""

from __future__ import annotations

from ast import (
    Add,
    And,
    Attribute,
    AugAssign,
    BinOp,
    BoolOp,
    ClassDef,
    Compare,
    Constant,
    FormattedValue,
    Gt,
    Import,
    JoinedStr,
    Name,
    Not,
    Or,
    Sub,
    UAdd,
    UnaryOp,
    USub,
    alias,
    arg,
    dump,
    parse,
    walk,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Final, Literal, final

import pytest
from astart.source.ast import CommentedModule
from astart.source.formatting import (
    EmissionPlan,
    FormatPreservationError,
    Patch,
)

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from collections.abc import Callable
type Mutation = Callable[[CommentedModule], object]


def _first[T](*, tree: CommentedModule, kind: type[T], index: int = 0) -> T:
    """Return the n-th node of a given type.

    Args:
        tree (CommentedModule): Module to search.
        kind (type[T]): Node class to find.
        index (int): Zero-based match index.

    Returns:
        T: Matching node.

    """
    matches: list[T] = [
        node for node in walk(node=tree) if isinstance(node, kind)
    ]
    return matches[index]


def _set_conversion(
    *,
    tree: CommentedModule,
    code: int,
    index: int = 0,
) -> None:
    """Change an f-string conversion directive.

    Args:
        tree (CommentedModule): Module containing the f-string.
        code (int): New conversion code.
        index (int): Which replacement field to edit.

    """
    _first(tree=tree, kind=FormattedValue, index=index).conversion = code


def _rename_attribute(*, tree: CommentedModule) -> None:
    """Rename the outermost attribute.

    Args:
        tree (CommentedModule): Module containing an attribute chain.

    """
    _first(tree=tree, kind=Attribute).attr = "renamed"


@final
class Constants:
    """Group module-level constants.

    Attributes:
        edits (Final[dict[str, tuple[str, Mutation]]]): Grouped module
            constant.

    """

    edits: Final[dict[str, tuple[str, Mutation]]] = {
        "conversion_r_to_s": (
            """\
name = f"hi {user!r} there"
""",
            lambda tree: _set_conversion(tree=tree, code=115),
        ),
        "conversion_added": (
            """\
name = f"hi {user} there"
""",
            lambda tree: _set_conversion(tree=tree, code=114),
        ),
        "conversion_removed": (
            """\
name = f"hi {user!s} there"
""",
            lambda tree: _set_conversion(tree=tree, code=-1),
        ),
        "fstring_segment": (
            """\
name = f"hello {user} world"
""",
            lambda tree: setattr(
                _first(tree=tree, kind=JoinedStr).values[0],
                "value",
                "bye ",
            ),
        ),
        "alias_asname": (
            """\
import os as o
from a import b as c
""",
            lambda tree: setattr(_first(tree=tree, kind=alias), "asname", "p"),
        ),
        "alias_name": (
            """\
import os as o
from a import b as c
""",
            lambda tree: setattr(
                _first(tree=tree, kind=alias, index=1),
                "name",
                "z",
            ),
        ),
        "attribute_rename": (
            """\
value = first.second.third
""",
            lambda tree: _rename_attribute(tree=tree),
        ),
        "binop_operator": (
            """\
value = a + b
""",
            lambda tree: setattr(_first(tree=tree, kind=BinOp), "op", Sub()),
        ),
        "unary_operator": (
            """\
value = -a
""",
            lambda tree: setattr(
                _first(tree=tree, kind=UnaryOp),
                "op",
                UAdd(),
            ),
        ),
        "unary_to_not": (
            """\
value = -a
""",
            lambda tree: setattr(_first(tree=tree, kind=UnaryOp), "op", Not()),
        ),
        "compare_operator": (
            """\
ok = a < b <= c
""",
            lambda tree: setattr(
                _first(tree=tree, kind=Compare),
                "ops",
                [Gt(), Gt()],
            ),
        ),
        "boolop_operator": (
            """\
ok = a and b and c
""",
            lambda tree: setattr(_first(tree=tree, kind=BoolOp), "op", Or()),
        ),
        "augassign_operator": (
            """\
total += 1
""",
            lambda tree: setattr(
                _first(tree=tree, kind=AugAssign),
                "op",
                Add(),
            ),
        ),
        "constant_types": (
            """\
a = 1
b = 'x'
c = b'y'
d = 1.5
e = True
f = None
g = 2j
""",
            lambda tree: [
                setattr(node, "value", replacement)
                for node, replacement in zip(
                    [n for n in walk(node=tree) if isinstance(n, Constant)],
                    ["s", 2, "z", True, 3, "n", 1.5],
                    strict=True,
                )
            ],
        ),
        "name_rename": (
            """\
def f(a, b=1, *args, c, d=2, **kw):
    return a + b
""",
            lambda tree: [
                setattr(node, "id", node.id + "_x")
                for node in walk(node=tree)
                if isinstance(node, Name)
            ],
        ),
        "arg_rename": (
            """\
def f(a, b=1, /, c=2, *args, d, e=3, **kw): ...
""",
            lambda tree: [
                setattr(node, "arg", node.arg + "_x")
                for node in walk(node=tree)
                if isinstance(node, arg)
            ],
        ),
        "swap_statements": (
            """\
a = 1
b = 2
c = 3
""",
            lambda tree: tree.body.reverse(),
        ),
        "drop_statement": (
            """\
a = 1
b = 2
c = 3
""",
            lambda tree: tree.body.pop(1),
        ),
        "add_statement": (
            """\
a = 1
""",
            lambda tree: tree.body.append(parse(source="z = 2").body[0]),
        ),
        "import_name": (
            """\
import os, sys
""",
            lambda tree: setattr(
                _first(tree=tree, kind=Import).names[0],
                "name",
                "re",
            ),
        ),
        "nested_swap": (
            """\
class A:
    def a(self): ...
    def b(self): ...
    x = 1
""",
            lambda tree: _first(tree=tree, kind=ClassDef).body.reverse(),
        ),
        "default_change": (
            """\
def f(a=1, *, b=2): ...
""",
            lambda tree: [
                setattr(node, "value", 9)
                for node in walk(node=tree)
                if isinstance(node, Constant)
            ],
        ),
        "usub_to_uadd": (
            """\
value = +a
""",
            lambda tree: setattr(
                _first(tree=tree, kind=UnaryOp),
                "op",
                USub(),
            ),
        ),
        "bool_and": (
            """\
ok = a or b
""",
            lambda tree: setattr(_first(tree=tree, kind=BoolOp), "op", And()),
        ),
    }


@pytest.mark.parametrize("name", sorted(Constants.edits))
@pytest.mark.parametrize("policy", ["raise", "fallback"])
def test_edit_roundtrip_is_valid_or_fails_closed(
    *,
    name: str,
    policy: Literal["raise", "fallback"],
) -> None:
    """Either produce valid Python or raise the dedicated error.

    Args:
        name (str): Edit scenario key.
        policy (Literal['raise', 'fallback']): Conflict policy passed to
            ``unparse``.

    """
    source: str = Constants.edits[name][0]
    mutate: Mutation = Constants.edits[name][1]
    tree: CommentedModule = CommentedModule.parse(source=dedent(text=source))
    tuple(map(mutate, (tree,)))
    try:
        output: str = tree.unparse(
            preserve_formatting=True,
            on_format_conflict=policy,
        )
    except FormatPreservationError:
        expect_true(condition=policy == "raise")
        return
    parse(source=output)


@pytest.mark.parametrize(
    argnames=("start", "end", "expected"),
    argvalues=[
        (0, 2, (0, 2)),
        (4, 7, (7, 10)),
        (7, 10, (11, 14)),
        (2, 4, None),
        (1, 9, None),
        (5, 8, None),
        (7, 7, (11, 11)),
        (3, 3, None),
    ],
)
def test_emission_plan_rebases_only_untouched_ranges(
    *,
    start: int,
    end: int,
    expected: tuple[int, int] | None,
) -> None:
    """Insertion affinity and replaced ranges never guess new AST positions.

    Args:
        start (int): Original range start.
        end (int): Original range end.
        expected (tuple[int, int] | None): Rebased untouched range or explicit
            dirty-owner refusal.

    """
    plan: EmissionPlan = EmissionPlan(
        source="0123456789",
        revision=4,
        patches=(
            Patch(start=2, end=4, text="ABCDE"),
            Patch(start=7, end=7, text="!"),
        ),
    )
    expect_equal(actual=plan.rebase(start=start, end=end), expected=expected)
    expect_equal(
        actual=plan.render(source="0123456789", revision=4),
        expected="01ABCDE456!789",
    )


def test_emission_plan_rejects_stale_sources_and_overlaps() -> None:
    """Revision and source guards fail before source or AST mutation."""
    source: str = "é = 1\r\n"
    plan: EmissionPlan = EmissionPlan(
        source=source,
        revision=1,
        patches=(Patch(start=0, end=1, text="name"),),
    )
    expect_equal(
        actual=plan.render(source=source, revision=1),
        expected="""\
name = 1\r
""",
    )
    expect_equal(
        actual=plan.rebase(start=1, end=len(source)),
        expected=(4, len(source) + 3),
    )
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="stale",
    ):
        plan.render(source=source, revision=2)
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="stale",
    ):
        plan.render(source=source.replace("1", "2"), revision=1)
    with pytest.raises(
        expected_exception=FormatPreservationError,
        match="Overlapping",
    ):
        EmissionPlan(
            source=source,
            revision=1,
            patches=(
                Patch(start=0, end=3, text="x"),
                Patch(start=2, end=4, text="y"),
            ),
        )


def test_emission_plan_preserves_noop_and_same_boundary_insertions() -> None:
    """Keep no-op ranges clean and ordered insertion affinity exact."""
    clean: EmissionPlan = EmissionPlan(
        source="abcd",
        revision=0,
        patches=(
            Patch(start=1, end=2, text="b"),
            Patch(start=3, end=3, text=""),
        ),
    )
    expect_equal(actual=clean.rebase(start=0, end=4), expected=(0, 4))
    inserted: EmissionPlan = EmissionPlan(
        source="abcd",
        revision=0,
        patches=(
            Patch(start=2, end=2, text="A"),
            Patch(start=2, end=2, text="B"),
        ),
    )
    expect_equal(
        actual=inserted.render(source="abcd", revision=0),
        expected="abABcd",
    )
    expect_equal(actual=inserted.rebase(start=2, end=4), expected=(4, 6))


@pytest.mark.parametrize(
    argnames="newline",
    argvalues=[
        "\n",
        """\
\r
""",
    ],
)
def test_fresh_nested_docstrings_preserve_literal_contents(
    *,
    newline: str,
) -> None:
    """Indent inserted code without inserting spaces into its string values.

    Args:
        newline (str): Outer source newline convention.

    """
    tree: CommentedModule = CommentedModule.parse(
        source=newline.join(("class Outer:", "    value = 1", "")),
    )
    owner: ClassDef = _first(tree=tree, kind=ClassDef)
    candidate: ClassDef = _first(
        tree=CommentedModule.parse(
            source=(
                'class Inner:\n    """Contract.\n\nAttributes:\n'
                '    value: TODO.\n"""\n    value: int\n'
            ),
        ),
        kind=ClassDef,
    )
    owner.body.insert(0, candidate)
    expected: str = dump(node=owner)
    emitted: str = tree.unparse(preserve_formatting=True)
    expect_equal(
        actual=dump(node=parse(source=emitted).body[0]),
        expected=expected,
    )
