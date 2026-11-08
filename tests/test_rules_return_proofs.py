"""Language-guaranteed return proofs and exit-path analysis."""

from __future__ import annotations

from ast import AsyncFunctionDef, FunctionDef, parse
from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.provable import can_fall_off, provable_return_detail
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_function_node,
    expect_in,
    expect_not_in,
)

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _function(*, source: str) -> FunctionDef | AsyncFunctionDef:
    """Parse ``source`` and return its first function node.

    Args:
        source: Module source text.

    Returns:
        The first function definition.

    """
    return expect_function_node(value=parse(source=source).body[0])


def _proof(*, source: str) -> tuple[str | None, bool]:
    """Compute the provable-return detail for ``source``'s function.

    Args:
        source: Module source text.

    Returns:
        ``(return type or None, guaranteed flag)``.

    """
    return provable_return_detail(
        function=_function(source=source),
        known_types={},
        counts={},
    )


def test_builtins_with_a_fixed_result_are_guaranteed() -> None:
    """Check that builtins with a fixed result are guaranteed."""
    cases: dict[str, str] = {
        "return len(x)": "int",
        "return str(x)": "str",
        "return repr(x)": "str",
        "return isinstance(x, int)": "bool",
        "return callable(x)": "bool",
        "return hasattr(x, 'a')": "bool",
        "return hash(x)": "int",
        "return not x": "bool",
        "return f'{x}'": "str",
    }
    for body, expected in cases.items():
        found: tuple[str | None, bool] = _proof(
            source=f"def f(x):\n    {body}\n",
        )
        expect_equal(actual=found, expected=(expected, True), message=body)


def test_results_that_depend_on_an_argument_are_not_guaranteed() -> None:
    """Check that results that depend on an argument are not guaranteed."""
    for body in ("return abs(x)", "return x + 1", "return x == 1", "return x"):
        found, guaranteed = _proof(source=f"def f(x):\n    {body}\n")
        expect_equal(actual=guaranteed and found is not None, expected=False)


def test_a_local_built_from_guaranteed_values_stays_guaranteed() -> None:
    """Check that a local built from guaranteed values stays guaranteed."""
    found: tuple[str | None, bool] = _proof(
        source="def f(x):\n    n = len(x)\n    return n\n",
    )
    expect_equal(actual=found, expected=("int", True))


def test_try_statements_are_analysed_by_their_exits() -> None:
    """Check that try statements are analysed by their exits."""
    never: AsyncFunctionDef | FunctionDef = _function(
        source=(
            "def f():\n    try:\n        return 1\n"
            "    except ValueError:\n        return 2\n"
        ),
    )
    expect_equal(actual=can_fall_off(body=never.body), expected=False)
    falls: AsyncFunctionDef | FunctionDef = _function(
        source=(
            "def f():\n    try:\n        return 1\n"
            "    except ValueError:\n        print('x')\n"
        ),
    )
    expect_equal(actual=can_fall_off(body=falls.body), expected=True)
    finally_returns: AsyncFunctionDef | FunctionDef = _function(
        source=(
            "def f():\n    try:\n        print('a')\n"
            "    finally:\n        return 1\n"
        ),
    )
    expect_equal(
        actual=can_fall_off(body=finally_returns.body),
        expected=False,
    )
    else_falls: AsyncFunctionDef | FunctionDef = _function(
        source=(
            "def f():\n    try:\n        print('a')\n"
            "    except ValueError:\n        return 2\n"
            "    else:\n        print('b')\n"
        ),
    )
    expect_equal(actual=can_fall_off(body=else_falls.body), expected=True)


def _fixed(*, source: str) -> str:
    """Fix ``source`` and return the rewritten module.

    Args:
        source: Module source to fix.

    Returns:
        Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=source,
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source


def test_fix_writes_guaranteed_returns_even_with_untyped_arguments() -> None:
    """Check that fix writes guaranteed returns with untyped arguments."""
    cases: dict[str, str] = {
        "def f(x):\n    return len(x)\n": "def f(x) -> int:",
        "def f(x):\n    return not x\n": "def f(x) -> bool:",
        "def f(x):\n    return f'{x}'\n": "def f(x) -> str:",
        "def f(x):\n    return isinstance(x, int)\n": "def f(x) -> bool:",
        "def f(x):\n    if x:\n        return 1\n": "def f(x) -> int | None:",
        (
            "def f(x):\n    try:\n        return 1\n"
            "    except ValueError:\n        return 2\n"
        ): "def f(x) -> int:",
    }
    for source, expected in cases.items():
        expect_in(item=expected, container=_fixed(source=source))


def test_fix_refuses_returns_that_depend_on_the_argument() -> None:
    """Check that fix refuses returns that depend on the argument."""
    for source in (
        "def f(x):\n    return abs(x)\n",
        "def f(x):\n    return sorted(x)\n",
    ):
        expect_not_in(item="->", container=_fixed(source=source))
    expect_in(
        item="-> bool",
        container=_fixed(source="def f(x):\n    return x == 1\n"),
    )
