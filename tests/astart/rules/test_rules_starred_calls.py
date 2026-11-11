"""``*args`` in a call is never turned into a keyword."""

from __future__ import annotations

from ast import arg, parse, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart import parse as parse_module
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.hints import HintIndex
from astart.rules.recovery import strip_annotations
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult
    from astart.source.ast import CommentedModule


@final
class Constants:
    """Constants for the starred calls tests.

    Attributes:
        source (Final[str]): Module exercising ``*args`` /``**kwargs``
            forwarding.

    """

    source: Final[str] = """
def runner(fn, *args, **options):
    return fn(*args, **options)


def wrap(func):
    return func


def run(func, *args, **options):
    return runner(wrap(func), *args, **options)
"""


def _fixed(*, source: str) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source (str): Module source to fix.

    Returns:
        str: Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_a_starred_argument_stays_positional() -> None:
    """Check that ``*args`` never becomes ``args=*args``."""
    out: str = _fixed(source=Constants.source)
    expect_not_in(item="args=*", container=out)
    expect_not_in(item="=**", container=out)
    expect_true(condition=bool(parse(source=out)))


def test_arguments_after_a_star_stay_positional() -> None:
    """Check that positions after ``*xs`` are not guessed."""
    out: str = _fixed(
        source="""
        def target(a, b, c):
            return a

        def caller(xs):
            return target(*xs, 1)
        """,
    )
    expect_in(item="target(*xs, 1)", container=out)
    expect_not_in(item="b=1", container=out)
    expect_not_in(item="c=1", container=out)
    expect_true(condition=bool(parse(source=out)))


def test_a_pipeline_that_emits_bad_code_is_contained() -> None:
    """Check that hint computation survives a broken conversion output."""
    module: CommentedModule = parse_module(
        source=dedent(text=Constants.source),
        filename="m.py",
    )
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    expect_true(
        condition=any(
            index.rejection_for(node=node) is not None
            for node in walk(node=module)
            if isinstance(node, arg)
        ),
    )


def test_the_trio_backend_module_converts_to_valid_code() -> None:
    """Check the anyio module that once produced ``args=*args``."""
    path: Path = (
        Paths.tests
        / "corpus"
        / "extended"
        / "anyio__anyio___backends___trio.py"
    )
    if not path.exists():
        return
    registries: Registries = default_registries()
    result: FixResult = fix_source(
        source=strip_annotations(source=path.read_text(encoding="utf-8")),
        filename="trio.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    expect_equal(actual=result.parse_error, expected=None)
