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
    parse,
    walk,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Final, Literal, final

import pytest
from astart.ast import CommentedModule
from astart.formatting import FormatPreservationError

from tests.expectations import expect_true

if TYPE_CHECKING:
    from collections.abc import Callable
type Mutation = Callable[[CommentedModule], object]


def _first[T](*, tree: CommentedModule, kind: type[T], index: int = 0) -> T:
    """Return the n-th node of a given type.

    Args:
        tree: Module to search.
        kind: Node class to find.
        index: Zero-based match index.

    Returns:
        Matching node.

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
        tree: Module containing the f-string.
        code: New conversion code.
        index: Which replacement field to edit.

    """
    _first(tree=tree, kind=FormattedValue, index=index).conversion = code


def _rename_attribute(*, tree: CommentedModule) -> None:
    """Rename the outermost attribute.

    Args:
        tree: Module containing an attribute chain.

    """
    _first(tree=tree, kind=Attribute).attr = "renamed"


@final
class Constants:
    """Group module-level constants.

    Attributes:
        edits: Grouped module constant.

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
        name: Edit scenario key.
        policy: Conflict policy passed to ``unparse``.

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
