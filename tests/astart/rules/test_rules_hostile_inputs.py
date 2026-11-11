"""``fix_source`` survives hostile inputs without raising."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.runner import FixResult
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_instance, expect_not_none

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _result(*, source: str) -> FixResult:
    """Run the fix pipeline on ``source``.

    Args:
        source (str): Python source text.

    Returns:
        FixResult: The fix result, including any parse error.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


@pytest.mark.parametrize(
    "source",
    [
        "",
        """\
# only a comment
""",
        '"""Only a docstring."""\n',
        """\
\ufeffx = 1
""",
        """\
def f():
\treturn 1
""",
        "x = " + "1" * 4996 + "\n",
        "x = 1",
        """\
x = (
""",
    ],
)
def test_fix_source_never_raises(*, source: str) -> None:
    """Check hostile input returns a result instead of raising.

    Args:
        source (str): Hostile source text.

    """
    result: FixResult = _result(source=source)
    expect_instance(value=result, kind=FixResult)


def test_unparsable_source_reports_parse_error() -> None:
    """Check ``x = (`` yields ``parse_error`` instead of a rewrite."""
    result: FixResult = _result(
        source="""\
x = (
""",
    )
    expect_not_none(value=result.parse_error)
