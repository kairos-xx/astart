"""Writer fuzzer: random fix subsets must keep every writer invariant.

For each recorded seed the fuzzer picks a source, a subset of the
annotation-preserving fixes, a safety ceiling, a confidence floor and a
round count, then requires that the rewritten source still compiles,
keeps every comment, and -- once annotations are stripped -- is identical
to the original. A crash on any recorded seed is a failure.

"""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, Module, arg, dump, unparse, walk
from ast import parse as parse_python
from dataclasses import replace
from io import StringIO
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.model import Catalog


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus_names (Final[tuple[str, ...]]): Small corpus modules cheap
            enough to fuzz.
        seeds (Final[tuple[int, ...]]): Recorded corpus seeds; a crash on any
            is a bug.
        synthetic_seeds (Final[tuple[int, ...]]): Recorded seeds over generated
            sources.
        fix_pool (Final[tuple[str, ...]]): Fixes that never change call sites
            or add imports.
        confidence_floors (Final[tuple[float, ...]]): Floors the fuzzer
            samples.
        corpus_per_seed (Final[int]): How many corpus modules each seed fixes.

    """

    corpus_names: Final[tuple[str, ...]] = (
        "keyword.py",
        "secrets.py",
        "colorsys.py",
        "sched.py",
        "bisect.py",
        "token.py",
        "tomllib___re.py",
        "asyncio__timeouts.py",
        "importlib__resources__abc.py",
        "opcode.py",
    )
    seeds: Final[tuple[int, ...]] = (
        17,
        23,
        41,
        59,
        73,
        89,
        97,
        113,
        131,
        137,
        149,
        163,
    )
    synthetic_seeds: Final[tuple[int, ...]] = (
        3,
        7,
        11,
        19,
        29,
        37,
        43,
        53,
        61,
        67,
        71,
        79,
        83,
        101,
        107,
        109,
    )
    fix_pool: Final[tuple[str, ...]] = (
        "typing.add-none-return",
        "typing.add-inferred-annotation",
    )
    confidence_floors: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 0.9)
    corpus_per_seed: Final[int] = 3


def _src(*lines: str) -> str:
    """Join line fragments into one source text.

    Args:
        lines (str): Source fragments, concatenated verbatim.

    Returns:
        str: The joined source text.

    """
    return "".join(lines)


_SYNTHETICS: Final[tuple[str, ...]] = (
    _src(
        """\
# leading comment

""",
        """\
def f(x):
    # inner comment
""",
        """\
    return x  # trailing


f(1)
""",
    ),
    _src(
        """\
#!shebang-like comment
# -*- mode: python -*-
""",
        """\
def f(x, y=1):
""",
        """\
    return x + y  # note


f(1, 2)
""",
    ),
    _src(
        """\
def f(items):
    # loop header
""",
        """\
    for item in items:
""",
        """\
        print(item)  # body


f([1, 2, 3])
""",
    ),
    _src(
        """\
class K:
    # class comment
""",
        """\
    def m(self, a=1):
""",
        """\
        return a


K().m(2)
""",
    ),
    _src(
        """\
def f(p, q='x'):
    return p


""",
        """\
f(q='y', p=1)
# end comment
""",
    ),
    _src(
        """\
async def f(x=1.5):
    return x


""",
        """\
import asyncio
asyncio.run(f(2.5))
""",
    ),
    _src(
        """\
def outer(a):
    def inner(b):
""",
        """\
        return b  # nested
""",
        """\
    return inner(a)


outer(1)
""",
    ),
    _src(
        """\
def f(x):
    if x:
""",
        """\
        return 1  # branch one
""",
        """\
    return 2


f(True)
""",
    ),
    _src(
        """\
TWO = 2


def f(x=TWO * 0):
""",
        """\
    return x


f(1)
""",
    ),
    _src(
        """\
def f(xs):
    return sorted(xs)


f([3, 1])
""",
    ),
    _src(
        """\
def f():
    ...


""",
        """\
def g(x):
    print(x)


g('a')
""",
    ),
    _src(
        '# module doc?\n"""Docstring."""\n\n\n',
        'def f(x):\n    """Inner docstring."""\n',
        """\
    return x


f(0.5)
""",
    ),
    _src(
        """\
def f(x):
    return f'{x}'  # fstring body


f(7)
""",
    ),
    _src(
        """\
def f(*, x=2):
    return x


f(x=3)
""",
    ),
)


def _catalog(*, fix_keys: frozenset[str]) -> Catalog:
    """Restrict the default catalog to a subset of safe fixes.

    Args:
        fix_keys (frozenset[str]): Fix keys that stay selectable.

    Returns:
        Catalog: A catalog whose rules only offer the chosen fixes.

    """
    catalog: Catalog = load_default_catalog(
        registries=default_registries(),
    )
    return replace(
        catalog,
        rules=tuple(
            replace(
                rule,
                fixes=tuple(key for key in rule.fixes if key in fix_keys),
            )
            for rule in catalog.rules
        ),
        fixes=tuple(fix for fix in catalog.fixes if fix.key in fix_keys),
    )


def _comments(*, text: str) -> list[str]:
    """List the comments of a source in order.

    Args:
        text (str): Source text to tokenize.

    Returns:
        list[str]: Comment strings in source order.

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
        source (str): Module source text.

    Returns:
        str: The unparsed tree without annotations.

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
        source (str): Module source text.

    Returns:
        list[str | None]: Annotation source per subject, ``None`` when absent.

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


def _settings(*, seed: int) -> FixSettings:
    """Derive a deterministic fix configuration from a seed.

    Args:
        seed (int): Deterministic seed.

    Returns:
        FixSettings: The derived fix settings.

    """
    ceilings: tuple[FixSafety, ...] = (
        FixSafety.proven,
        FixSafety.guarded,
    )
    floors: tuple[float, ...] = Constants.confidence_floors
    return FixSettings(
        ceiling=ceilings[(seed >> 3) % len(ceilings)],
        min_confidence=floors[seed % len(floors)],
        max_rounds=1 + seed % 3,
    )


def _keys(*, seed: int) -> frozenset[str]:
    """Derive a deterministic fix subset from a seed.

    Args:
        seed (int): Deterministic seed.

    Returns:
        frozenset[str]: The derived fix keys.

    """
    return frozenset(
        key
        for index, key in enumerate(iterable=Constants.fix_pool)
        if (seed >> index) % 2 == 0
    )


def _run(*, source: str, seed: int) -> FixResult:
    """Run one seeded fuzz fix pass.

    Args:
        source (str): Python source text.
        seed (int): The recorded seed that picks the fix subset.

    Returns:
        FixResult: The fix result.

    """
    return fix_source(
        source=source,
        filename=f"fuzz-{seed}.py",
        catalog=_catalog(fix_keys=_keys(seed=seed)),
        registries=default_registries(),
        settings=_settings(seed=seed),
    )


def _invariants(*, source: str, result: FixResult, seed: int) -> None:
    """Check every writer invariant on one fuzz run.

    Args:
        source (str): The original text.
        result (FixResult): The fixer output.
        seed (int): The seed, for failure messages.

    """
    expect_equal(actual=result.parse_error, expected=None)
    parse_python(source=result.source)
    compile(source=result.source, filename=f"fuzz-{seed}.py", mode="exec")
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
    expect_true(
        condition=all(item.reason != "" for item in result.skipped),
        message=f"seed {seed}: a skipped fix has no reason",
    )


@pytest.mark.parametrize("seed", Constants.seeds)
def test_fuzz_corpus(*, seed: int) -> None:
    """Fix subsets over vendored modules keep every writer invariant.

    Args:
        seed (int): The recorded seed under test.

    """
    names: tuple[str, ...] = Constants.corpus_names
    start: int = seed % len(names)
    picked: tuple[str, ...] = tuple(
        names[(start + step) % len(names)]
        for step in range(Constants.corpus_per_seed)
    )
    directory: Path = Paths.tests / "corpus" / "base"
    for name in picked:
        source: str = (directory / name).read_text(encoding="utf-8")
        result: FixResult = _run(source=source, seed=seed)
        _invariants(source=source, result=result, seed=seed)


@pytest.mark.parametrize("seed", Constants.synthetic_seeds)
def test_fuzz_synthetic(*, seed: int) -> None:
    """Fix subsets over generated sources keep every writer invariant.

    Args:
        seed (int): The recorded seed under test.

    """
    source: str = _SYNTHETICS[seed % len(_SYNTHETICS)]
    result: FixResult = _run(source=source, seed=seed)
    _invariants(source=source, result=result, seed=seed)
    if seed % 2 == 0:
        again: FixResult = _run(source=result.source, seed=seed)
        expect_equal(actual=again.source, expected=result.source)
        expect_equal(actual=again.applied, expected=())


def test_fuzz_empty_subset_keeps_source() -> None:
    """A run that selects no fixes returns the source untouched."""
    source: str = _SYNTHETICS[0]
    result: FixResult = fix_source(
        source=source,
        filename="fuzz-empty.py",
        catalog=_catalog(fix_keys=frozenset()),
        registries=default_registries(),
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    expect_equal(actual=result.parse_error, expected=None)
    expect_equal(actual=result.source, expected=source)
    expect_equal(actual=result.applied, expected=())


def test_fuzz_full_subset_keeps_invariants() -> None:
    """A run that selects every fix still honours the invariants."""
    for index, source in enumerate(iterable=_SYNTHETICS[:6]):
        result: FixResult = fix_source(
            source=source,
            filename=f"fuzz-full-{index}.py",
            catalog=_catalog(fix_keys=frozenset(Constants.fix_pool)),
            registries=default_registries(),
            settings=FixSettings(ceiling=FixSafety.guarded),
        )
        _invariants(source=source, result=result, seed=index)
