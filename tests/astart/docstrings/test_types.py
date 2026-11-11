"""Typed documentation generation through the public fix pipeline."""

from __future__ import annotations

from ast import walk
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.docstrings import (
    DocEntry,
    DocstringNode,
    DocTodo,
    parse_docstring,
)
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.docstrings import DocstringNode
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult


def _fixed(*, source: str, include_types: bool = True) -> str:
    """Generate documentation with the selected type policy.

    Args:
        source (str): Python fixture.
        include_types (bool): Whether documentation should contain types.

    Returns:
        str: Converted source.

    """
    registries: Registries = default_registries()
    result: FixResult = fix_source(
        source=dedent(text=source),
        filename="example.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.proven,
            docstring_types=include_types,
        ),
    )
    expect_equal(actual=result.parse_error, expected=None)
    expect_equal(
        actual=any(
            item.rule_key == "docs.annotation-types"
            for item in result.remaining
        ),
        expected=False,
    )
    return result.source


def test_parameter_return_prose_and_idempotence() -> None:
    """Refresh types, retain descriptions and use TODO for new fields."""
    output: str = _fixed(
        source='''
        def convert(value: int, *, label: str = "x") -> str:
            """Convert.

            Args:
                value (float): Keep this description.
            """
            return label
    ''',
    )
    expect_in(item="value (int): Keep this description.", container=output)
    expect_in(item="label (str): TODO.", container=output)
    expect_in(item="str: TODO.", container=output)
    expect_equal(actual=_fixed(source=output), expected=output)


def test_generator_components_and_raises() -> None:
    """Document yielded and terminal values separately from exceptions."""
    output: str = _fixed(
        source='''
        from collections.abc import Generator

        def stream() -> Generator[int, None, str]:
            """Stream."""
            yield 1
            if False:
                raise ValueError("bad")
            return "done"
    ''',
    )
    expect_in(
        item="""Yields:
        int: TODO.""",
        container=output,
    )
    expect_in(
        item="""Returns:
        str: TODO.""",
        container=output,
    )
    expect_in(
        item="""Raises:
        ValueError: TODO.""",
        container=output,
    )


def test_async_yields_and_nested_raise_ownership() -> None:
    """Nested bodies do not supply the outer function's exceptions."""
    output: str = _fixed(
        source='''
        from collections.abc import AsyncIterator

        async def stream() -> AsyncIterator[bytes]:
            """Stream."""
            def inner():
                raise RuntimeError("inner")
            yield b"data"
    ''',
    )
    expect_in(
        item="""Yields:
        bytes: TODO.""",
        container=output,
    )
    expect_not_in(item="Raises:", container=output)
    expect_not_in(item="Returns:", container=output)


def test_noreturn_documents_raises_without_returns() -> None:
    """NoReturn functions describe their explicit exceptions."""
    output: str = _fixed(
        source='''
        from typing import NoReturn

        def fail() -> NoReturn:
            """Fail."""
            raise ValueError("bad")
    ''',
    )
    expect_in(
        item="""Raises:
        ValueError: TODO.""",
        container=output,
    )
    expect_not_in(item="Returns:", container=output)


def test_disabled_type_policy() -> None:
    """The opt-out retains untyped documentation generation."""
    output: str = _fixed(
        source='''
            def run(value: int) -> None:
                """Run."""
        ''',
        include_types=False,
    )
    expect_in(item="value: Describe value.", container=output)
    expect_not_in(item="value (int)", container=output)


def test_generator_import_alias_uses_symbol_identity() -> None:
    """Resolve aliased generator constructors without rewriting annotations."""
    output: str = _fixed(
        source='''
        from collections.abc import Generator as Stream

        def stream() -> Stream[int, None, str]:
            """Stream."""
            yield 1
            return "done"
    ''',
    )
    expect_in(
        item="""Yields:
        int: TODO.""",
        container=output,
    )
    expect_in(
        item="""Returns:
        str: TODO.""",
        container=output,
    )
    expect_in(item="-> Stream[int, None, str]", container=output)


def test_returns_prose_with_colon_keeps_full_text() -> None:
    """A colon inside Returns prose is not a type boundary."""
    output: str = _fixed(
        source='''
        def stamp() -> str:
            """Current local time.

            Returns:
                An ISO 8601 timestamp such as ``2026-11-08T18:37:12+00:00``.
            """
            return "x"
    ''',
    )
    expect_in(
        item=(
            "str: An ISO 8601 timestamp such as ``2026-11-08T18:37:12+00:00``."
        ),
        container=output,
    )
    expect_equal(actual=_fixed(source=output), expected=output)


def test_class_attributes_receive_types() -> None:
    """Class-level annotations type existing and missing Attributes entries."""
    output: str = _fixed(
        source='''
        class Constants:
            """Group module-level constants.

            Attributes:
                suite_name: Name of the emitted test suite.
            """

            suite_name: str = "astart"
            internal: int = 3
    ''',
    )
    expect_in(
        item="suite_name (str): Name of the emitted test suite.",
        container=output,
    )
    expect_in(item="internal (int): TODO.", container=output)
    expect_equal(actual=_fixed(source=output), expected=output)


def test_long_union_parameter_wraps_without_parentheses() -> None:
    """Over-budget ``name (type)`` labels stay parseable for docstring tools.

    Google-style ``name (type):`` labels must keep the whole head on one
    line; docstring checkers such as Ruff D417 do not rejoin wrapped
    parenthesized types. Long types therefore serialize as ``name:``
    followed by the type expression flowing across lines.

    """
    union_type: str = (
        "List | Set | Tuple | Dict | ListComp | SetComp | DictComp "
        "| GeneratorExp"
    )
    output: str = _fixed(
        source=f'''
        def collection_type(
            node: {union_type},
            index: Index,
        ) -> str | None:
            """Describe collection_type."""
            pass
    ''',
    )
    expect_in(
        item="node: List | Set | Tuple | Dict | ListComp | SetComp |"
        " DictComp |",
        container=output,
    )
    expect_in(item="GeneratorExp: TODO.", container=output)
    expect_not_in(item="node (", container=output)
    expect_equal(actual=_fixed(source=output), expected=output)


def test_wrapped_type_label_round_trips_through_parser() -> None:
    """A ``name: TYPE:`` entry re-parses with its type intact."""
    union_type: str = (
        "List | Set | Tuple | Dict | ListComp | SetComp | DictComp "
        "| GeneratorExp"
    )
    output: str = _fixed(
        source=f'''
        def collection_type(
            node: {union_type},
        ) -> None:
            """Describe collection_type."""
            pass
    ''',
    )
    reparsed: str = _fixed(source=output)
    expect_equal(actual=reparsed, expected=output)
    expect_in(
        item="node: List | Set | Tuple | Dict | ListComp | SetComp |"
        " DictComp |",
        container=reparsed,
    )


def test_long_type_wraps_description_to_continuation() -> None:
    """Over-budget entry lines reflow instead of exceeding the width."""
    output: str = _fixed(
        source='''
        def tally() -> tuple[tuple[int, ...], tuple[tuple[str, int], ...]]:
            """Break one module score down.

            Returns:
                ``(by_kind, by_basis)`` pair for the module, computed
                from the annotation map of the original source text.
            """
            return ()
    ''',
    )
    type_line: str = next(
        line
        for line in output.splitlines()
        if "tuple[tuple[int, ...]" in line and "def " not in line
    )
    description_line: str = next(
        line for line in output.splitlines() if "by_kind" in line
    )
    expect_equal(actual=type_line.rstrip().endswith(":"), expected=True)
    expect_equal(
        actual=len(description_line) - len(description_line.lstrip()),
        expected=len(type_line) - len(type_line.lstrip()) + 4,
    )
    expect_equal(actual=_fixed(source=output), expected=output)


def test_over_budget_entry_pulls_description_onto_label() -> None:
    """Entries never orphan the label when description words still fit."""
    document: DocstringNode = parse_docstring(
        source="""Summary.

Args:
    graph (ContractGraph):
        Existing contracts over the authoritative module AST nodes.
""",
    )
    rendered: str = document.render()
    label_line: str = next(
        line
        for line in rendered.splitlines()
        if "graph (ContractGraph)" in line
    )
    expect_in(item="Existing contracts", container=label_line)


def test_nested_paren_type_entries_do_not_duplicate() -> None:
    """``tuple[()]`` inside a parenthesized type stays a single entry."""
    output: str = _fixed(
        source='''
        def update(
            other: dict[str, int] | tuple[()] = (),
            *values,
            **kwargs,
        ) -> None:
            """Update.

            Args:
                other (dict[str, int] | tuple[()]): Merge mapping.
                values: Extra values.
                kwargs: Extra keyword values.
            """
    ''',
    )
    expect_equal(actual=output.count("other ("), expected=1)
    expect_equal(actual=_fixed(source=output), expected=output)


def test_nested_paren_type_splits_name_from_label() -> None:
    """The model parser separates ``name`` from a nested ``(type)``."""
    document: DocstringNode = parse_docstring(
        source="""Summary.

Args:
    other (dict[str, int] | tuple[()]): TODO.
""",
    )
    entry: DocEntry = document.sections[0].entries[0]
    expect_equal(actual=entry.name, expected="other")
    expect_equal(
        actual=entry.type_name,
        expected="dict[str, int] | tuple[()]",
    )


def test_todo_placeholder_is_a_traversable_node() -> None:
    """``TODO.`` descriptions surface as DocTodo nodes under ast.walk."""
    entry: DocEntry = DocEntry(
        kind="parameters",
        name="value",
        description="TODO.",
    )
    expect_equal(actual=entry.todo is not None, expected=True)
    document: DocstringNode = parse_docstring(
        source="""Summary.

Args:
    value (int): TODO.
    label (str): Keep this description.
""",
    )
    todos: list[DocTodo] = [
        node for node in walk(node=document) if isinstance(node, DocTodo)
    ]
    expect_equal(actual=len(todos), expected=1)
    entries: list[DocEntry] = [
        item for section in document.sections for item in section.entries
    ]
    by_name: dict[str, DocEntry] = {item.name or "": item for item in entries}
    expect_equal(actual=by_name["value"].todo is not None, expected=True)
    expect_equal(actual=by_name["label"].todo, expected=None)
    by_name["value"].description = "Describe value."
    by_name["value"].sync_todo()
    expect_equal(actual=by_name["value"].todo, expected=None)
