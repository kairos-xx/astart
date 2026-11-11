"""Native insertion resolves bindings and preserves builtin print behavior."""

from __future__ import annotations

from ast import Call, FunctionDef, Name, fix_missing_locations, walk
from subprocess import CompletedProcess, run
from sys import executable
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from astart.__main__ import main
from astart.source.ast import CommentedModule
from astart.transforms.insertion import (
    InsertChanges,
    InsertSettings,
    insert_tree,
)

from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    from astart.transforms.constants import MagicScope


def _insert(*, source: str) -> tuple[CommentedModule, InsertChanges]:
    """Apply the native insertion pass with parsing disabled during mutation.

    Args:
        source (str): Python fixture, parsed once before the pass.

    Returns:
        tuple[CommentedModule, InsertChanges]: The same module and its actual
            change record.

    """
    tree: CommentedModule = CommentedModule.parse(source=source)
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        changes: InsertChanges = insert_tree(
            tree=tree,
            settings=InsertSettings(replace_print=True),
        )
    compile(
        source=fix_missing_locations(node=tree),
        filename="<native-insert>",
        mode="exec",
    )
    return tree, changes


def _output(*, tree: CommentedModule) -> str:
    """Execute only a controlled emitted test fixture in a child interpreter.

    Args:
        tree (CommentedModule): The fixture after insertion.

    Returns:
        str: Captured standard output.

    """
    result: CompletedProcess[str] = run(
        args=[executable, "-c", tree.unparse(preserve_formatting=True)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_print_insertion_is_opt_in() -> None:
    """Default insertion never changes runtime source."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
print("hello")
""",
    )
    changes: InsertChanges = insert_tree(tree=tree, settings=InsertSettings())
    expect_equal(actual=changes.print_calls_changed, expected=0)
    expect_equal(
        actual=tree.unparse(),
        expected="""\
print("hello")
""",
    )


def test_print_helper_is_native_and_idempotent() -> None:
    """Insert AST nodes directly and delegate standard formatting to print."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source="""\
print("a", 2, sep="/", end="!")
""",
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(actual=_output(tree=tree), expected="a/2!")
    expect_true(
        condition=any(
            isinstance(node, FunctionDef) and node.name == changes.helper_name
            for node in tree.body
        ),
    )
    again: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(replace_print=True),
    )
    expect_equal(actual=again.print_calls_changed, expected=0)


def test_print_shadowing_is_resolved_per_scope() -> None:
    """Preserve local print bindings and rewrite unrelated builtin calls."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source=(
            """\
def f(print):
    print("local")
print("builtin")
"""
        ),
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(actual=len(changes.skipped), expected=1)
    local: list[Call] = [
        node
        for node in walk(node=tree)
        if isinstance(node, Call)
        and isinstance(node.func, Name)
        and node.func.id == "print"
    ]
    expect_equal(actual=len(local), expected=1)
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
builtin
""",
    )


def test_print_helper_avoids_binding_collisions() -> None:
    """New helper/import names cannot capture an existing binding or read."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source=(
            "aprint = 1\n_astart_builtins = 2\n"
            "def f(_astart_pathlib):\n    return _astart_pathlib\n"
            'print("ok")\n'
        ),
    )
    expect_equal(actual=changes.helper_name, expected="aprint_2")
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
ok
""",
    )


def test_print_wildcard_import_is_preserved() -> None:
    """An unknown wildcard export could shadow print and prevents rewriting."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source="""\
from math import *
print("ok")
""",
    )
    expect_equal(actual=changes.print_calls_changed, expected=0)
    expect_true(condition=bool(changes.skipped))
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
ok
""",
    )


def test_print_path_output_uses_owned_file_context(tmp_path: Path) -> None:
    """Path output closes the file and respects mode, separator and encoding.

    Args:
        tmp_path (Path): Isolated output directory.

    """
    output: Path = tmp_path / "result.txt"
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source=(
            f'print("é", 2, sep="/", file={str(object=output)!r}, mode="w")\n'
        ),
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(actual=_output(tree=tree), expected="")
    expect_equal(actual=output.read_text(encoding="utf-8"), expected="é/2\n")


def test_falsey_stream_is_not_replaced_by_stdout() -> None:
    """Preserve an explicitly supplied falsey stream."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source=(
            "from io import StringIO\nfrom sys import stdout\n"
            "class Falsey(StringIO):\n"
            "    def __bool__(self):\n        return False\n"
            'stream = Falsey()\nprint("retained", file=stream, flush=True)\n'
            "stdout.write(stream.getvalue())\n"
        ),
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
retained
""",
    )
    expect_in(item="file=stream", container=tree.unparse())


@pytest.mark.parametrize(
    argnames="scope",
    argvalues=["module", "function", "class"],
)
def test_numeric_comparison_extraction_preserves_behavior(
    scope: MagicScope,
) -> None:
    """Typed constants retain signed values and lexical evaluation scopes.

    Args:
        scope (MagicScope): Explicit extraction mode.

    """
    tree: CommentedModule = CommentedModule.parse(
        source=(
            "class Box:\n"
            "    threshold = 9 > 2\n"
            "    def check(self, value):\n"
            "        return -2.5 < value < 9\n"
            "def f(value, default=(9 > 2)):\n"
            "    return value == 9 and default\n"
            "print(Box().check(3), f(9), Box.threshold)\n"
        ),
    )
    with patch(target="astart.source.ast.parse", side_effect=AssertionError):
        changes: InsertChanges = insert_tree(
            tree=tree,
            settings=InsertSettings(
                magic_scope=scope,
            ),
        )
    expect_true(condition=changes.numeric_values_changed > 0)
    expect_true(condition=changes.numeric_constants_added > 0)
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
True True True
""",
    )
    again: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            magic_scope=scope,
        ),
    )
    expect_equal(actual=again.numeric_values_changed, expected=0)


def test_numeric_extraction_preserves_booleans_and_nonfinite_values() -> None:
    """Preserve bool, unit sentinels and overflowing float literals."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            """\
x = True == 1 and 0 < 1 and -1 < 1e999
"""
        ),
    )
    changes: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            magic_scope="module",
        ),
    )
    expect_equal(actual=changes.numeric_values_changed, expected=0)


def test_class_body_comprehensions_refuse_unsafe_class_cells() -> None:
    """An eager class comprehension cannot read an uninitialized class cell."""
    tree: CommentedModule = CommentedModule.parse(
        source=(
            "class Box:\n    values = [x > 2 for x in range(4)]\n"
            "print(Box.values)\n"
        ),
    )
    changes: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            magic_scope="class",
        ),
    )
    expect_equal(actual=changes.numeric_values_changed, expected=0)
    expect_true(condition=bool(changes.skipped))
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
[False, False, False, True]
""",
    )


def test_numeric_and_print_passes_share_the_same_tree() -> None:
    """Both insertion features compose without parsing another module."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
print(9 > 2)
""",
    )
    changes: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            replace_print=True,
            magic_scope="module",
        ),
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(actual=changes.numeric_values_changed, expected=2)
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
True
""",
    )


@pytest.mark.parametrize(
    argnames="body",
    argvalues=[
        "flag = (lambda: 9 > 2)()",
        """\
def f():
        return 9 > 2
    flag = f()""",
    ],
)
def test_class_construction_callables_keep_uninitialized_cells_safe(
    *,
    body: str,
) -> None:
    """Preserve comparisons when a callable can run before class creation.

    Args:
        body (str): Controlled class-body fixture with an eager callable.

    """
    tree: CommentedModule = CommentedModule.parse(
        source=(f"class C:\n    {body}\nprint(C.flag)\n"),
    )
    changes: InsertChanges = insert_tree(
        tree=tree,
        settings=InsertSettings(
            magic_scope="class",
        ),
    )
    expect_true(condition=bool(changes.skipped))
    expect_equal(
        actual=_output(tree=tree),
        expected="""\
True
""",
    )


def test_private_mangled_helper_name_is_rejected_before_mutation() -> None:
    """A module helper cannot acquire class-private name mangling."""
    tree: CommentedModule = CommentedModule.parse(
        source="""\
print("ok")
""",
    )
    with pytest.raises(expected_exception=ValueError, match="identifier"):
        insert_tree(
            tree=tree,
            settings=InsertSettings(
                replace_print=True,
                helper_name="__aprint",
            ),
        )
    expect_equal(
        actual=tree.unparse(),
        expected="""\
print("ok")
""",
    )


def test_transform_cli_preserves_input_and_writes_new_artifacts(
    *,
    tmp_path: Path,
) -> None:
    """Expose the opt-in passes without changing normal annotation defaults.

    Args:
        tmp_path (Path): Isolated input/output/report directory.

    """
    source: Path = tmp_path / "input.py"
    output: Path = tmp_path / "output.py"
    report: Path = tmp_path / "report.json"
    original: str = """\
print(9 > 2)
"""
    source.write_text(data=original, encoding="utf-8")
    expect_equal(
        actual=main(
            argv=[
                "transform",
                str(object=source),
                "--replace-print",
                "--magic-scope",
                "module",
                "--wrap",
                "--output",
                str(object=output),
                "--report",
                str(object=report),
            ],
        ),
        expected=0,
    )
    expect_equal(actual=source.read_text(encoding="utf-8"), expected=original)
    expect_true(condition=report.is_file())
    expect_in(
        item="ComparisonConstants",
        container=output.read_text(
            encoding="utf-8",
        ),
    )
    result: CompletedProcess[str] = run(
        args=[executable, str(object=output)],
        capture_output=True,
        text=True,
        check=True,
    )
    expect_equal(
        actual=result.stdout,
        expected="""\
True
""",
    )
    expect_equal(
        actual=main(
            argv=[
                "transform",
                str(object=source),
                "--replace-print",
                "--check",
            ],
        ),
        expected=1,
    )
    expect_equal(actual=source.read_text(encoding="utf-8"), expected=original)


@pytest.mark.parametrize(
    argnames="alias_kind",
    argvalues=["same", "symlink", "hardlink"],
)
def test_report_cannot_alias_source_even_in_check_mode(
    *,
    tmp_path: Path,
    alias_kind: str,
) -> None:
    """Reject report aliases before writing source bytes or audit output.

    Args:
        tmp_path (Path): Isolated fixture directory.
        alias_kind (str): Direct, symbolic or hard-link path alias.

    """
    source: Path = tmp_path / "source.py"
    report: Path = tmp_path / "audit.json"
    original: str = """\
print("retained")
"""
    source.write_text(data=original, encoding="utf-8")
    if alias_kind == "same":
        report = source
    elif alias_kind == "symlink":
        report.symlink_to(target=source)
    else:
        report.hardlink_to(target=source)
    with pytest.raises(expected_exception=ValueError, match="alias"):
        main(
            argv=[
                "transform",
                str(object=source),
                "--check",
                "--report",
                str(object=report),
            ],
        )
    expect_equal(actual=source.read_text(encoding="utf-8"), expected=original)


def test_write_return_values_are_not_restricted_by_print_helper() -> None:
    """Builtin print ignores write's return, including nonnumeric values."""
    tree: CommentedModule
    changes: InsertChanges
    tree, changes = _insert(
        source=(
            "class Sink:\n"
            "    def write(self, text: str) -> str:\n        return text\n"
            'print("hello", file=Sink())\n'
        ),
    )
    expect_equal(actual=changes.print_calls_changed, expected=1)
    expect_equal(actual=_output(tree=tree), expected="")
