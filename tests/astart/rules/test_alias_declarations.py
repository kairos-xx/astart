"""Legacy aliases become native declarations without variable annotations."""

from __future__ import annotations

from ast import Assign, TypeAlias, stmt
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart import parse
from astart.project.versions import PythonTarget
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.alias_declarations import AliasDeclarations
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.rules.registry import Registries


def _fix(*, source: str, target: tuple[int, int] = (3, 13)) -> str:
    """Exercise the public catalog pipeline with variable inference enabled.

    Args:
        source (str): Test module.
        target (tuple[int, int]): Oldest emitted Python version.

    Returns:
        str: Transformed source.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=source,
        filename="aliases.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            annotate_variables=True,
            target=PythonTarget(floor=target),
        ),
    ).source


@pytest.mark.parametrize(
    argnames="name",
    argvalues=["_ListInt", "lower", "WHATEVER", "UserSelectedName"],
)
def test_implicit_alias_names_are_preserved(*, name: str) -> None:
    """Never synthesize a new name or a variable annotation.

    Args:
        name (str): Arbitrary author-selected alias name.

    """
    expected: str = f"type {name} = list[int]\n"
    expect_equal(
        actual=_fix(source=f"{name} = list[int]\n"),
        expected=expected,
    )
    expect_equal(actual=_fix(source=expected), expected=expected)


@pytest.mark.parametrize(
    argnames="source",
    argvalues=[
        """\
from typing import TypeAlias
_ListInt: TypeAlias = list[int]
""",
        """\
from typing import TypeAlias as Alias
_ListInt: Alias = list[int]
""",
        """\
import typing as t
_ListInt: t.TypeAlias = list[int]
""",
        """\
_ListInt: type[list[int]] = list[int]
""",
    ],
)
def test_explicit_alias_markers_are_removed(*, source: str) -> None:
    """Replace the annotation with native alias syntax and clean its import.

    Args:
        source (str): Legacy declaration spelling.

    """
    expect_equal(
        actual=_fix(source=source),
        expected="""\
type _ListInt = list[int]
""",
    )


@pytest.mark.parametrize(
    argnames="source",
    argvalues=[
        """\
factory = list[int]
factory()
""",
        """\
Alias = list[int]
print(Alias)
""",
        """\
Alias = list[int]
isinstance([], Alias)
""",
        """\
Alias = list[int]
Alias = int
""",
        """\
list = {}
Alias = list[int]
""",
        """\
Alias = make_type()
""",
        """\
Alias = [int]
""",
        """\
Alias = None
""",
        """\
A = B
B = A
""",
        """\
from typing import Final
Alias: Final = list[int]
""",
        """\
A = list[int]
B = A
B()
""",
        """\
from unknown import *
Alias = list[int]
""",
    ],
)
def test_runtime_and_ambiguous_bindings_are_not_migrated(
    *,
    source: str,
) -> None:
    """Keep ordinary values, runtime identities and rebound names intact.

    Args:
        source (str): Unsafe or non-alias module.

    """
    expect_not_in(item="type ", container=_fix(source=source))


def test_target_version_and_alias_dependencies() -> None:
    """Gate syntax at 3.12 and migrate chained annotation-only aliases."""
    source: str = """\
A = list[int]
B = A
x: B
"""
    expect_in(item="type A = list[int]", container=_fix(source=source))
    expect_in(item="type B = A", container=_fix(source=source))
    expect_not_in(item="type ", container=_fix(source=source, target=(3, 11)))


def test_generic_alias_keeps_free_type_parameters() -> None:
    """Make legacy unconstrained type variables explicit on the new alias."""
    source: str = dedent(
        text="""
        from typing import TypeAlias, TypeVar
        T = TypeVar('T')
        Vector: TypeAlias = list[T]
        """,
    )
    output: str = _fix(source=source)
    expect_in(item="type Vector[T] = list[T]", container=output)
    expect_not_in(item="TypeAlias", container=output)


def test_owner_rhs_identity_and_original_trivia_survive() -> None:
    """Edit the owned AST and patch just the declaration's lexical header."""
    source: str = """\
# contract
_Alias  =  list[ int ]  # keep
"""
    tree: CommentedModule = parse(source=source)
    statement: Assign = next(
        node for node in tree.body if isinstance(node, Assign)
    )
    value_id: int = id(statement.value)
    declarations: AliasDeclarations = AliasDeclarations()
    declarations.apply(module=tree, statement=statement)
    expect_true(condition=tree.body[0] is statement)
    expect_true(
        condition=isinstance((body_or_none := tree.body[0]), TypeAlias),
    )
    body: stmt = expect_not_none(value=body_or_none)
    if isinstance(body, TypeAlias):
        expect_equal(actual=id(body.value), expected=value_id)
    expect_equal(
        actual=tree.unparse(preserve_formatting=True),
        expected="""\
# contract
type _Alias  =  list[ int ]  # keep
""",
    )
