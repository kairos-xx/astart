"""Tests for the shared docstring helpers of the DOC rule family."""

from __future__ import annotations

from ast import Module
from ast import parse as ast_parse
from textwrap import dedent
from typing import TYPE_CHECKING

from astart import parse
from astart.docstrings.missing_returns import result_kinds
from astart.docstrings.shared import (
    documented_names,
    owner_docstring,
    parameter_names,
)

from tests.support.expectations import (
    FunctionStatement,
    NamedStatement,
    expect_equal,
    expect_function_node,
    expect_named_node,
)

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.docstrings import DocstringNode


def _function(*, source: str) -> FunctionStatement:
    """Parse a plain module and return its first function.

    Args:
        source (str): Module source text.

    Returns:
        FunctionStatement: The first definition.

    """
    tree: Module = ast_parse(source=dedent(text=source))
    return expect_function_node(value=tree.body[0])


def _module_function(
    *,
    source: str,
    index: int = 0,
) -> tuple[CommentedModule, NamedStatement]:
    """Parse a commented module and return a function inside it.

    Args:
        source (str): Module source text.
        index (int): Body position of the function.

    Returns:
        tuple[CommentedModule, NamedStatement]: The parsed module and the
            chosen function node.

    """
    module: CommentedModule = parse(
        source=dedent(text=source),
        filename="m.py",
    )
    return module, expect_named_node(value=module.body[index])


def test_plain_module_reads_parameter_names() -> None:
    """A Google-style ``Args:`` section lists its entry names."""
    owner: FunctionStatement = _function(
        source='''
        def f(a, b):
            """Do it.

            Args:
                a: first
                b (int): second
            """
            return a
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a", "b"),
    )


def test_plain_module_without_docstring() -> None:
    """A definition with no docstring yields no names."""
    owner: FunctionStatement = _function(
        source="""
        def f(a):
            return a
        """,
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=(),
    )


def test_plain_module_returns_entry_is_nameless() -> None:
    """A ``Returns:`` description counts as one un-named entry."""
    owner: FunctionStatement = _function(
        source='''
        def f():
            """Do it.

            Returns:
                the result
            """
            return 1
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="returns"),
        expected=(None,),
    )


def test_plain_module_yields_entry_is_nameless() -> None:
    """A ``Yields:`` section behaves like ``Returns:``."""
    owner: FunctionStatement = _function(
        source='''
        def f():
            """Do it.

            Yields:
                values
            """
            yield 1
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="yields"),
        expected=(None,),
    )


def test_plain_module_section_ends_on_dedent() -> None:
    """A non-indented line ends the active section."""
    owner: FunctionStatement = _function(
        source='''
        def f(a, b):
            """Do it.

            Args:
                a: first
            trailing prose outside sections.
                b: not an entry
            """
            return a
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a",),
    )


def test_plain_module_later_section_replaces_active() -> None:
    """A different title turns off the active section."""
    owner: FunctionStatement = _function(
        source='''
        def f(a):
            """Do it.

            Args:
                a: first

            Raises:
                ValueError: always
            """
            return a
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a",),
    )
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="raises"),
        expected=("ValueError",),
    )


def test_plain_module_starred_names_are_stripped() -> None:
    """``*args`` and ``**kwargs`` entries lose their stars."""
    owner: FunctionStatement = _function(
        source='''
        def f(*args, **kwargs):
            """Do it.

            Args:
                *args: positional
                **kwargs: keyword
            """
            return args
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("args", "kwargs"),
    )


def test_plain_module_non_entry_lines_are_skipped() -> None:
    """Continuation prose inside ``Args:`` is not an entry."""
    owner: FunctionStatement = _function(
        source='''
        def f(a):
            """Do it.

            Args:
                a: first
                  continued description, no colon-start
            """
            return a
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a",),
    )


def test_plain_module_title_variants() -> None:
    """``Arguments:`` and ``Exceptions:`` are recognised titles."""
    owner: FunctionStatement = _function(
        source='''
        def f(a):
            """Do it.

            Arguments:
                a: first

            Exceptions:
                OSError: always
            """
            return a
        ''',
    )
    module: Module = ast_parse(source="x = 1")
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a",),
    )
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="raises"),
        expected=("OSError",),
    )


def test_commented_module_reads_structured_entries() -> None:
    """Structured docstrings are preferred over section parsing."""
    module, owner = _module_function(
        source='''
        def f(a, b):
            """Do it.

            Args:
                a: first
                b: second
            """
            return a
        ''',
    )
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=("a", "b"),
    )


def test_commented_module_owner_without_document() -> None:
    """A documented module still reports nothing for other owners."""
    module, owner = _module_function(
        source='''
        def documented():
            """Has a docstring."""

        def undocumented():
            return 1
        ''',
        index=1,
    )
    expect_equal(
        actual=documented_names(module=module, owner=owner, kind="parameters"),
        expected=(),
    )


def test_owner_docstring() -> None:
    """``owner_docstring`` returns the docstring text or ``None``."""
    documented: FunctionStatement = _function(
        source='''
        def f():
            """Hello."""
        ''',
    )
    undocumented: FunctionStatement = _function(
        source="""
        def g():
            return 1
        """,
    )
    expect_equal(actual=owner_docstring(owner=documented), expected="Hello.")
    expect_equal(actual=owner_docstring(owner=undocumented), expected=None)


def test_parameter_names_skips_receiver() -> None:
    """``self``/``cls`` are excluded and keyword-only names kept."""
    owner: FunctionStatement = _function(
        source="""
        def f(self, cls, a, b, *, c):
            return a
        """,
    )
    expect_equal(
        actual=parameter_names(owner=owner),
        expected=("a", "b", "c"),
    )


def test_missing_results_respect_scope_and_both_generator_channels() -> None:
    """Separate yielded values from returns and exclude nested bodies."""
    cases: dict[str, tuple[str, ...]] = {
        "def f():\n yield 1\n return 'done'\n": ("yields", "returns"),
        "def f():\n yield from []\n": ("yields",),
        "def f():\n yield\n return None\n": ("yields",),
        "async def f():\n yield 1\n": ("yields",),
        "def f():\n callback = lambda: (yield 1)\n return callback\n": (
            "returns",
        ),
        "def f():\n def inner():\n  yield 1\n return inner\n": ("returns",),
        "def f():\n def inner(value=(yield 1)):\n  pass\n": ("yields",),
    }
    for source, expected in cases.items():
        owner: FunctionStatement = _function(source=source)
        expect_equal(actual=result_kinds(node=owner), expected=expected)


def test_generator_documentation_links_to_components() -> None:
    """Yield and return types link to their own generic type arguments."""
    module: CommentedModule = parse(
        source='''
from collections.abc import Generator


def emit() -> Generator[int, None, str]:
    """Emit.

    Yields:
        TODO.

    Returns:
        TODO.
    """
    yield 1
    return "done"
''',
    )
    document: DocstringNode = next(
        doc for doc in module.docstrings if doc.owner is not None
    )
    document.synchronize_symbols(include_types=True)
    expect_equal(
        actual=document.entries(kind="yields")[0].type_name,
        expected="int",
    )
    expect_equal(
        actual=document.entries(kind="returns")[0].type_name,
        expected="str",
    )
    expect_equal(
        actual=document.entries(kind="yields")[0].link_role,
        expected="yield_annotation",
    )
