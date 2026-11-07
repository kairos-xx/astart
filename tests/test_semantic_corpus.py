"""Run the semantic analyzer over real-world modules from the corpus."""

from __future__ import annotations

from ast import AsyncFunctionDef, Call, ClassDef, FunctionDef, Name, walk
from pathlib import Path
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.ast import CommentedModule

from tests.expectations import expect_equal, expect_true

if TYPE_CHECKING:
    from astart.semantic import SemanticAnalyzer


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_directory: Grouped module constant.
        semantic_files: Grouped module constant.
        evaluator_source: Grouped module constant.

    """

    corpus_directory: Final[Path] = Path(__file__).parent / "corpus"
    semantic_files: Final[tuple[str, ...]] = (
        "tokenize.py.txt",
        "types.py.txt",
        "zipapp.py.txt",
    )
    evaluator_source: Final[str] = """\
import contextlib

class Error(Exception):
    pass

def matcher(command, mapping, items):
    match command:
        case [first, second, *rest]:
            a = first + second
        case {"key": value, **others}:
            a = value
        case 1 | 2 | 3:
            a = 0
        case str() as text if text:
            a = len(text)
        case Error(args=args):
            a = args
        case _:
            a = None
    return a

def contexts(path):
    with open(path) as handle, contextlib.suppress(Error):
        data = handle.read()
    with contextlib.nullcontext() as other:
        data = other
    return data

def raising(flag):
    try:
        if flag:
            raise Error("bad")
        raise ValueError from None
    except (Error, ValueError) as caught:
        return str(caught)
    else:
        return "fine"
    finally:
        flag = None

def loops(n):
    total = 0
    items = []
    for i in range(n):
        total += i
        items.append(total)
        if total > 10:
            break
    else:
        total = -1
    while total:
        total -= 1
        if total == 3:
            continue
    for a, (b, c) in [(1, (2, 3))]:
        total = a + b + c
    name = f"{total!r:>{n}} items"
    return total, items, name, range(3), range(1, 5), range(0, 10, 2)

def comprehensions(data):
    squares = [x * x for x in data if x]
    lookup = {k: v for k, v in zip(data, data)}
    uniq = {x for x in data}
    gen = (x for x in data)
    nested = [[y for y in range(x)] for x in data]
    return squares, lookup, uniq, gen, nested

class Base:
    attribute = 1

    def method(self, value=2, *args, key=3, **kwargs):
        self.value = value
        return self.attribute + value

class Derived(Base):
    def method(self, value=5):
        result = super().method(value)
        lam = lambda q, r=1: q + r
        return lam(result)

def walrus_and_unpack(values):
    if (count := len(values)) > 2:
        first, *middle, last = values
        return first, middle, last, count
    a = b = c = 0
    a, b = b, a
    del c
    assert a == b, "equal"
    global GLOBAL
    GLOBAL = a
    return not a, -b, a if b else c, a and b, a or b, a < b < c

async def runner(session):
    async with session as active:
        async for item in active:
            await item
    return [x async for x in active]

value = matcher([1, 2], {}, [])
other = contexts("x")
"""


@pytest.mark.parametrize("name", Constants.semantic_files)
def test_semantic_analysis_of_real_modules(*, name: str) -> None:
    """Evaluate, resolve and rebuild real modules without losing text.

    Args:
        name: Corpus file name under ``tests/corpus``.

    """
    source: str = (Constants.corpus_directory / name).read_text(
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    semantic: SemanticAnalyzer = tree.semantic
    semantic.evaluate()
    scopes: int = 0
    for node in walk(node=tree):
        if isinstance(node, FunctionDef | AsyncFunctionDef | ClassDef):
            semantic.cfg(scope=node)
            scopes += 1
        if isinstance(node, Name):
            semantic.symbol(node=node)
    semantic.cfg()
    expect_true(condition=scopes > 0)
    expect_equal(actual=tree.unparse(), expected=source)


def test_semantic_evaluator_handles_statement_forms() -> None:
    """Evaluate match, with, try, loop and comprehension statements."""
    tree: CommentedModule = CommentedModule.parse(
        source=Constants.evaluator_source,
    )
    semantic: SemanticAnalyzer = tree.semantic
    semantic.evaluate()
    for node in walk(node=tree):
        if isinstance(node, FunctionDef | AsyncFunctionDef | ClassDef):
            semantic.cfg(scope=node)
        if isinstance(node, Name):
            semantic.symbol(node=node)
    expect_equal(actual=tree.unparse(), expected=Constants.evaluator_source)


def test_type_inference_handles_nested_definitions() -> None:
    """Infer types in modules whose functions define nested functions."""
    source: str = (Constants.corpus_directory / "types.py.txt").read_text(
        encoding="utf-8",
    )
    tree: CommentedModule = CommentedModule.parse(source=source)
    inferred: int = 0
    for node in walk(node=tree):
        if isinstance(node, Name | Call):
            tree.infer_type(node=node)
            inferred += 1
    expect_true(condition=inferred > 0)
