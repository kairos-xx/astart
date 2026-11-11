"""Danger-matrix tests for the IMP001 bare-import fixer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from astart import parse, unparse
from astart.rules.imports_bare_fix import rewrite_bare_imports

from tests.support.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart.rules.imports_bare_fix import ImportRewrite
    from astart.source.ast import CommentedModule


def _fix(source: str) -> tuple[str, tuple[ImportRewrite, ...]]:
    """Apply the fixer and return output source plus reports.

    Args:
        source (str): Python source.

    Returns:
        tuple[str, tuple[ImportRewrite, ...]]: ``(unparsed source, reports)``.

    """
    module: CommentedModule = parse(source=source)
    reports: tuple[ImportRewrite, ...] = rewrite_bare_imports(module=module)
    return unparse(tree=module), reports


@final
class Constants:
    """Source snippets for the danger matrix.

    Attributes:
        alias (Final[str]): ``import ast as tree`` with attribute use.
        augassign (Final[str]): Augmented assignment on a module attribute.
        bare_use (Final[str]): Module object referenced as a value.
        basic (Final[str]): Single import with one attribute use.
        collision (Final[str]): Local name collides with an attribute.
        delete (Final[str]): ``del`` on a module attribute.
        dotted (Final[str]): ``import a.c`` used through two attributes.
        dotted_bare (Final[str]): ``import a.c`` with the bare module
            referenced.
        existing_from (Final[str]): Existing ``from`` import alongside plain
            import.
        for_target (Final[str]): Attribute used as a ``for`` loop target.
        function_level (Final[str]): Import inside a function body.
        lambda_use (Final[str]): Attribute used inside a lambda.
        multi_attr (Final[str]): One import, several attribute uses.
        multi_name (Final[str]): ``import os, sys`` comma form.
        nested_scope (Final[str]): Attribute used inside a nested function.
        partial_store (Final[str]): Mix of reads and a store on one import.
        store (Final[str]): Store into a module attribute.
        try_import (Final[str]): Import guarded by ``try``/``except``.

    """

    basic: Final[str] = """\
import ast

x = ast.parse('1')
"""
    multi_attr: Final[str] = """\
import os

p = os.path.join('a')
q = os.getcwd()
"""
    collision: Final[str] = (
        "import re\n\ncompile = 1\nx = re.compile('a')\n"
        "y = re.match('b', 'c')\n"
    )
    existing_from: Final[str] = """\
from os import getcwd as gc
import os

x = os.getcwd()
"""
    store: Final[str] = """\
import pkg

pkg.value = 3
"""
    partial_store: Final[str] = """\
import pkg

x = pkg.read()
pkg.value = 3
"""
    bare_use: Final[str] = """\
import sys

print(sys)
x = sys.argv
"""
    delete: Final[str] = """\
import pkg

del pkg.cache
"""
    augassign: Final[str] = """\
import pkg

pkg.count += 1
"""
    for_target: Final[str] = """\
import pkg

for pkg.item in []:
    pass
"""
    alias: Final[str] = """\
import ast as tree

x = tree.parse('1')
"""
    multi_name: Final[str] = """\
import os, sys

x = os.getcwd()
"""
    try_import: Final[str] = (
        "try:\n    import json\nexcept ImportError:\n    pass\n"
        "\nx = json.loads('1')\n"
    )
    function_level: Final[str] = """\
def f():
    import json
    return json.loads('1')
"""
    dotted: Final[str] = """\
import a.c

x = a.c.foo(1)
y = a.c.bar(2)
"""
    dotted_bare: Final[str] = """\
import a.c

print(a.c)
x = a.c.foo
"""
    nested_scope: Final[str] = """\
import ast

def f():
    return ast.dump(ast.parse('1'))
"""
    lambda_use: Final[str] = """\
import ast

f = lambda: ast.parse('1')
"""


def test_basic_rewrite_removes_import() -> None:
    """A fully-convertible import becomes a ``from`` import."""
    output, reports = _fix(source=Constants.basic)
    expect_true(condition="from ast import parse" in output)
    expect_true(condition="x = parse('1')" in output)
    expect_true(condition="import ast" not in output)
    expect_equal(actual=reports[0].complete, expected=True)


def test_multiple_attributes_share_one_from_import() -> None:
    """Several attributes become aliases of one ``from`` statement."""
    output, reports = _fix(source=Constants.multi_attr)
    expect_true(condition="from os import getcwd, path" in output)
    expect_true(condition="p = path.join('a')" in output)
    expect_true(condition="q = getcwd()" in output)
    expect_equal(actual=reports[0].converted, expected=("getcwd", "path"))


def test_name_collision_keeps_import_and_use() -> None:
    """A colliding attribute name refuses conversion for that attribute."""
    output, reports = _fix(source=Constants.collision)
    expect_true(condition="import re" in output)
    expect_true(condition="x = re.compile('a')" in output)
    expect_true(condition="y = match('b', 'c')" in output)
    expect_true(condition="from re import match" in output)
    expect_equal(actual=reports[0].kept, expected=("compile",))


def test_existing_from_import_alias_is_reused() -> None:
    """An existing ``from x import y as z`` supplies the bound name."""
    output, _reports = _fix(source=Constants.existing_from)
    expect_true(condition="x = gc()" in output)
    expect_true(condition="import os" not in output)


def test_attribute_store_keeps_import() -> None:
    """``pkg.value = 3`` cannot become a local rebinding."""
    output, reports = _fix(source=Constants.store)
    expect_true(condition="import pkg" in output)
    expect_true(condition="pkg.value = 3" in output)
    expect_equal(actual=reports[0].complete, expected=False)


def test_partial_conversion_keeps_import_for_store() -> None:
    """Safe attributes convert while the store keeps ``import pkg``."""
    output, reports = _fix(source=Constants.partial_store)
    expect_true(condition="import pkg" in output)
    expect_true(condition="x = read()" in output)
    expect_true(condition="pkg.value = 3" in output)
    expect_equal(actual=reports[0].kept, expected=("value",))


def test_bare_module_use_keeps_import() -> None:
    """A bare ``sys`` read survives while ``sys.argv`` converts."""
    output, reports = _fix(source=Constants.bare_use)
    expect_true(condition="import sys" in output)
    expect_true(condition="print(sys)" in output)
    expect_true(condition="x = argv" in output)
    expect_equal(actual=reports[0].complete, expected=False)


def test_delete_keeps_import() -> None:
    """``del pkg.cache`` refuses conversion."""
    output, _ = _fix(source=Constants.delete)
    expect_true(condition="import pkg" in output)
    expect_true(condition="del pkg.cache" in output)


def test_augassign_keeps_import() -> None:
    """``pkg.count += 1`` refuses conversion."""
    output, _reports = _fix(source=Constants.augassign)
    expect_true(condition="import pkg" in output)
    expect_true(condition="pkg.count += 1" in output)


def test_for_target_keeps_import() -> None:
    """An attribute for-target refuses conversion."""
    output, _reports = _fix(source=Constants.for_target)
    expect_true(condition="import pkg" in output)
    expect_true(condition="for pkg.item in []" in output)


def test_aliased_import_untouched() -> None:
    """``import ast as tree`` is out of scope."""
    output, reports = _fix(source=Constants.alias)
    expect_true(condition="import ast as tree" in output)
    expect_true(condition="tree.parse('1')" in output)
    expect_equal(actual=len(reports), expected=0)


def test_multi_name_import_untouched() -> None:
    """``import os, sys`` is out of scope."""
    output, reports = _fix(source=Constants.multi_name)
    expect_true(condition="import os, sys" in output)
    expect_equal(actual=len(reports), expected=0)


def test_try_import_untouched() -> None:
    """Imports inside ``try`` are not direct module body statements."""
    output, reports = _fix(source=Constants.try_import)
    expect_true(condition="import json" in output)
    expect_true(condition="json.loads('1')" in output)
    expect_equal(actual=len(reports), expected=0)


def test_function_level_import_untouched() -> None:
    """Function-local imports are out of scope."""
    output, reports = _fix(source=Constants.function_level)
    expect_true(condition="import json" in output)
    expect_true(condition="json.loads('1')" in output)
    expect_equal(actual=len(reports), expected=0)


def test_dotted_import_converts_leaf_attributes() -> None:
    """``import a.c`` uses become ``from a.c import ...``."""
    output, reports = _fix(source=Constants.dotted)
    expect_true(condition="from a.c import bar, foo" in output)
    expect_true(condition="x = foo(1)" in output)
    expect_true(condition="y = bar(2)" in output)
    expect_true(condition="import a.c" not in output)
    expect_equal(actual=reports[0].module, expected="a.c")


def test_dotted_import_bare_module_use_kept() -> None:
    """A bare ``a.c`` read keeps ``import a.c`` while attrs convert."""
    output, reports = _fix(source=Constants.dotted_bare)
    expect_true(condition="import a.c" in output)
    expect_true(condition="print(a.c)" in output)
    expect_true(condition="x = foo" in output)
    expect_equal(actual=reports[0].complete, expected=False)


def test_nested_function_uses_convert() -> None:
    """Uses inside nested functions rewrite at module scope."""
    output, reports = _fix(source=Constants.nested_scope)
    expect_true(condition="from ast import dump, parse" in output)
    expect_true(condition="return dump(parse('1'))" in output)
    expect_equal(actual=reports[0].complete, expected=True)


def test_lambda_uses_convert() -> None:
    """Lambda bodies participate in the same scope."""
    output, _reports = _fix(source=Constants.lambda_use)
    expect_true(condition="from ast import parse" in output)
    expect_true(condition="lambda: parse('1')" in output)


def test_idempotent_second_run_is_noop() -> None:
    """Running the fixer twice produces no further changes."""
    first, _ = _fix(source=Constants.multi_attr)
    second, reports = _fix(source=first)
    expect_true(condition="from os import getcwd, path" in second)
    expect_equal(actual=len(reports), expected=0)
