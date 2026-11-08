"""Precision and acceptance tests for the gated type-hint fixer."""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, Name, arg, dump, unparse, walk
from ast import parse as parse_python
from dataclasses import replace
from io import StringIO
from pathlib import Path
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, Final, final

import pytest
from astart import parse
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.hints import HintIndex
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_false, expect_true

if TYPE_CHECKING:
    from ast import Module

    from astart import CommentedModule
    from astart.rules.hints import Hint
    from astart.rules.model import Catalog
type Expected = dict[str, str | None]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_files: Grouped module constant.
        stable_check_lines: Grouped module constant.
        banned: Grouped module constant.
        gold: Grouped module constant.

    """

    corpus_files: Final[tuple[Path, ...]] = tuple(
        sorted((Path(__file__).parent / "corpus").glob(pattern="*.py.txt")),
    )
    stable_check_lines: Final[int] = 700
    banned: Final[frozenset[str]] = frozenset({"object", "Any"})
    gold: Final[dict[str, tuple[str, Expected]]] = {
        "default str": (
            """\
def f(sep=' '):
    return sep
""",
            {"f": "str", "f.sep": "str"},
        ),
        "default int": (
            """\
def f(n=3):
    return n
""",
            {"f": "int", "f.n": "int"},
        ),
        "default bool": (
            """\
def f(flag=False):
    return flag
""",
            {"f": "bool", "f.flag": "bool"},
        ),
        "default none is never hinted": (
            """\
def f(x=None):
    return x
""",
            {"f": None, "f.x": None},
        ),
        "default disagrees with the call site": (
            """\
def f(x=1):
    return x + 0.5


f(2.5)
""",
            {"f": None, "f.x": None},
        ),
        "keyword-only default": (
            """\
def f(*, sep=','):
    return sep
""",
            {"f": "str", "f.sep": "str"},
        ),
        "call site int": (
            """\
def scale(x):
    return x * 2


scale(3)
""",
            {"scale": "int", "scale.x": "int"},
        ),
        "call sites disagree": (
            """\
def f(x):
    return x


f(1)
f('a')
""",
            {"f": None, "f.x": None},
        ),
        "int and float call sites disagree": (
            """\
def f(x):
    return x


f(1)
f(1.5)
""",
            {"f": None, "f.x": None},
        ),
        "call site str, return not provable": (
            """\
def shout(t):
    return t.upper()


shout('a')
""",
            {"shout": None, "shout.t": "str"},
        ),
        "call site list": (
            """\
def count(items):
    return len(items)


count([1, 2])
""",
            {"count": "int", "count.items": "list[int]"},
        ),
        "call site dict, list(d) is not provable": (
            """\
def keys(d):
    return list(d)


keys({'a': 1})
""",
            {"keys": None, "keys.d": "dict[str, int]"},
        ),
        "keyword call sites": (
            """\
def f(a, b):
    return a


f(a=1, b='x')
""",
            {"f": "int", "f.a": "int", "f.b": "str"},
        ),
        "operator-only guess is refused": (
            """\
def greet(name):
    return 'hi ' + name
""",
            {"greet": None, "greet.name": None},
        ),
        "len result is guaranteed but the argument guess is refused": (
            """\
def count(items):
    return len(items)
""",
            {"count": "int", "count.items": None},
        ),
        "index-only guess is refused": (
            """\
def first(seq):
    return seq[0]
""",
            {"first": None, "first.seq": None},
        ),
        "multiplication-only guess is refused": (
            """\
def scale(x):
    return x * 2
""",
            {"scale": None, "scale.x": None},
        ),
        "procedure returns None": (
            """\
def f(a):
    print(a)
""",
            {"f": "None", "f.a": None},
        ),
        "constructor returns None": (
            """\
class K:
    def __init__(self):
        self.x = 1
""",
            {"__init__": "None"},
        ),
        "async procedure returns None": (
            """\
async def f(a: int):
    print(a)
""",
            {"f": "None"},
        ),
        "async value": (
            """\
async def f():
    return 1
""",
            {"f": "int"},
        ),
        "mixed bare and value returns": (
            """\
def f(a):
    if a:
        return
    return 1
""",
            {"f": "int | None", "f.a": None},
        ),
        "generator": (
            """\
def f():
    yield 1
""",
            {"f": None},
        ),
        "stub body": (
            """\
def f(): ...
""",
            {"f": None},
        ),
        "constant return": (
            """\
def one():
    return 1
""",
            {"one": "int"},
        ),
        "string return": (
            """\
def name():
    return 'x'
""",
            {"name": "str"},
        ),
        "list return": (
            """\
def items():
    return [1, 2]
""",
            {"items": "list[int]"},
        ),
        "comparison return": (
            """\
def ok(a: int):
    return a > 0
""",
            {"ok": "bool"},
        ),
        "declared parameter feeds return": (
            """\
def n(items: list):
    return len(items)
""",
            {"n": "int"},
        ),
        "untyped local taints return": (
            """\
def f(x):
    y = x * 2
    return y
""",
            {"f": None, "f.x": None},
        ),
        "typed local flows to return": (
            """\
def f(x):
    y = x * 2
    return y


f(3)
""",
            {"f": "int", "f.x": "int"},
        ),
        "method call on a constructed instance is resolved": (
            """\
class K:
    def m(self, a):
        return a


K().m(1)
""",
            {"m": "int", "m.a": "int"},
        ),
        "overridden method gives no call-site evidence": (
            """\
class K:
    def m(self, a):
        return a


class L(K):
    def m(self, b):
        return b


K().m(1)
""",
            {"m": None, "m.a": None, "m.b": None},
        ),
        "variadics are never hinted": (
            """\
def f(*args, **kw):
    return args
""",
            {"f": None},
        ),
        "shadowed callee gives no evidence": (
            """\
def f(x):
    return x


def g(f):
    f(1)
""",
            {"f": None, "f.x": None, "g": "None", "g.f": None},
        ),
        "redefined function gives no evidence": (
            (
                """\
def f(x):
    return x


f(1)


def f(x, y):
    return x
"""
            ),
            {"f": None, "f.x": None, "f.y": None},
        ),
    }


def _hints(*, source: str) -> Expected:
    """Collect accepted hints for every unannotated name of a snippet.

    Args:
        source: Python source with top-level functions and classes.

    Returns:
        Hint sources by ``function`` or ``function.parameter`` path, with
        ``None`` for refusals.

    """
    module: CommentedModule = parse(source=source, filename="gold.py")
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    found: Expected = {}
    hint: Hint | None
    for function in walk(node=module):
        if not isinstance(function, (FunctionDef, AsyncFunctionDef)):
            continue
        if function.returns is None:
            hint = index.hint_for(node=function)
            found[function.name] = None if hint is None else hint.source
        parameters: list[arg] = [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]
        for parameter in parameters:
            if parameter.arg in {"self", "cls"} or parameter.annotation:
                continue
            hint = index.hint_for(node=parameter)
            found[(f"{function.name}.{parameter.arg}")] = (
                None if hint is None else hint.source
            )
    return found


@pytest.mark.parametrize(
    ("source", "expected"),
    list(Constants.gold.values()),
    ids=list(Constants.gold),
)
def test_gold_set_has_no_wrong_hints(
    *,
    source: str,
    expected: Expected,
) -> None:
    """Accept exactly the hints a reviewer verified; refuse the rest.

    Args:
        source: Snippet under test.
        expected: Hint (or refusal) for every unannotated name.

    """
    expect_equal(actual=_hints(source=source), expected=expected)


def _typing_catalog() -> Catalog:
    """Restrict the default catalog to the type-hint rule and its fixes.

    Returns:
        A catalog containing only TYP003 and the two hint fixes.

    """
    catalog: Catalog = load_default_catalog(registries=default_registries())
    allowed: set[str] = {
        "typing.add-none-return",
        "typing.add-inferred-annotation",
    }
    return replace(
        catalog,
        rules=tuple(
            replace(
                rule,
                fixes=tuple(key for key in rule.fixes if key in allowed),
            )
            for rule in catalog.rules
            if rule.code == "TYP003"
        ),
        fixes=tuple(f for f in catalog.fixes if f.key in allowed),
    )


def _comments(*, text: str) -> list[str]:
    """List the comments of a source in order.

    Args:
        text: Python source.

    Returns:
        The comment tokens.

    """
    return [
        token.string
        for token in generate_tokens(
            readline=StringIO(initial_value=text).readline,
        )
        if token.type == COMMENT
    ]


def _stripped(*, source: str) -> str:
    """Dump a tree after removing parameter and return annotations.

    Args:
        source: Python source.

    Returns:
        The textual dump of the stripped tree.

    """
    tree: Module = parse_python(source=source)
    for node in walk(node=tree):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            node.returns = None
        if isinstance(node, arg):
            node.annotation = None
    return dump(node=tree)


def _annotations(*, source: str) -> list[str | None]:
    """List every parameter and return annotation in source order.

    Args:
        source: Python source.

    Returns:
        The annotation texts, ``None`` where absent.

    """
    found: list[str | None] = []
    for node in walk(node=parse_python(source=source)):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            found.append(
                None
                if node.returns is None
                else unparse(ast_obj=node.returns),
            )
        if isinstance(node, arg):
            found.append(
                None
                if node.annotation is None
                else unparse(ast_obj=node.annotation),
            )
    return found


def _fix(*, source: str, name: str) -> FixResult:
    """Run the guarded type-hint fixer on a source.

    Args:
        source: Python source.
        name: File name.

    Returns:
        The fix result.

    """
    return fix_source(
        source=source,
        filename=name,
        catalog=_typing_catalog(),
        registries=default_registries(),
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


@pytest.mark.parametrize(
    "path",
    Constants.corpus_files,
    ids=[path.name for path in Constants.corpus_files],
)
def test_corpus_fixes_parse_keep_comments_and_are_stable(
    *,
    path: Path,
) -> None:
    """Fix a real module without losing syntax, comments or stability.

    Args:
        path: Vendored module under test.

    """
    source: str = path.read_text(encoding="utf-8")
    result: FixResult = _fix(source=source, name=path.name)
    expect_equal(actual=result.parse_error, expected=None)
    parse_python(source=result.source)
    expect_equal(
        actual=_stripped(source=result.source),
        expected=_stripped(source=source),
    )
    expect_equal(
        actual=_comments(text=result.source),
        expected=_comments(text=source),
    )
    before: list[str | None] = _annotations(source=source)
    after: list[str | None] = _annotations(source=result.source)
    expect_equal(actual=len(before), expected=len(after))
    added: list[str] = [
        new
        for old, new in zip(before, after, strict=True)
        if old is None and new is not None
    ]
    expect_equal(actual=len(added), expected=len(result.applied))
    for text in added:
        names: set[str] = {
            node.id
            for node in walk(node=parse_python(source=text, mode="eval"))
            if isinstance(node, Name)
        }
        expect_false(condition=bool(names & Constants.banned), message=text)
    expect_true(condition=all(item.reason != "" for item in result.skipped))
    if (
        source.count("""\

""")
        <= Constants.stable_check_lines
    ):
        again: FixResult = _fix(source=result.source, name=path.name)
        expect_equal(actual=again.source, expected=result.source)
        expect_equal(actual=again.applied, expected=())


def test_runner_changes_realistic_code() -> None:
    """Guard against a vacuous pass: the fixer does write hints."""
    path: Path = next(
        p for p in Constants.corpus_files if p.name == "patterns.py.txt"
    )
    source: str = path.read_text(encoding="utf-8")
    result: FixResult = _fix(source=source, name=path.name)
    expect_true(condition=len(result.applied) > 0)
    expect_true(condition=result.source != source)
