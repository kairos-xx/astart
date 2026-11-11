"""End-to-end tests for keywording calls via the ``libkw`` table."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.rules.catalog import load_default_catalog
from astart.rules.facts import default_registries
from astart.rules.runner import (
    FixResult,
    FixSafety,
    FixSettings,
    fix_source,
)

from tests.support.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the guarded fix pipeline on one source.

    Args:
        source (str): Python source text.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="library.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            """\
import json
x = json.dumps({'a': 1})
""",
            "x = json.dumps(obj={'a': 1})",
            id="module-attribute",
        ),
        pytest.param(
            """\
import re
y = re.sub('a', 'b', s, 1)
""",
            "y = re.sub(pattern='a', repl='b', string=s, count=1)",
            id="several-positionals",
        ),
        pytest.param(
            """\
from os import replace
z = replace(a, b)
""",
            "z = replace(src=a, dst=b)",
            id="from-import-name",
        ),
        pytest.param(
            """\
import os
z = os.replace(a, b)
""",
            "z = os.replace(src=a, dst=b)",
            id="dotted-module",
        ),
        pytest.param(
            """\
x = pow(2, 3)
""",
            "x = pow(base=2, exp=3)",
            id="builtin-name",
        ),
        pytest.param(
            """\
import json
x = json.dumps({'a': 1}, skipkeys=True)
""",
            "x = json.dumps(obj={'a': 1}, skipkeys=True)",
            id="existing-keyword-kept",
        ),
        pytest.param(
            """\
import json
x = json.dumps(obj={'a': 1})
""",
            "x = json.dumps(obj={'a': 1})",
            id="already-keyworded",
        ),
    ],
)
def test_library_call_is_keyworded(*, source: str, expected: str) -> None:
    """Keyword-safe library calls gain parameter names.

    Args:
        source (str): Python source text.
        expected (str): Expected last line after fixing.

    """
    result: FixResult = _fix(source=source)
    expect_in(item=expected, container=result.source)
    _ = compile(source=result.source, filename="library.py", mode="exec")


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """\
print(1, 2)
""",
            id="var-positional-absorbed",
        ),
        pytest.param(
            """\
import posixpath
w = posixpath.join('a', 'b')
""",
            id="positional-only-prefix",
        ),
        pytest.param(
            """\
import json
x = json.dumps({'a': 1}, True)
""",
            id="beyond-signature",
        ),
        pytest.param(
            """\
x = getattr(obj, 'name')
""",
            id="positional-only-builtin",
        ),
        pytest.param(
            """\
import json
json = Other()
x = json.dumps(1)
""",
            id="rebound-import-root",
        ),
        pytest.param(
            "from json import dumps\n"
            "def dumps(x):\n"
            "    return x\n"
            "y = dumps(1)\n",
            id="shadowed-from-import",
        ),
        pytest.param(
            """\
import json
x = json.dumps({'a': 1}, **kw)
""",
            id="double-star-expansion",
        ),
    ],
)
def test_library_call_is_refused(*, source: str) -> None:
    """Uncertain library calls stay positional.

    Args:
        source (str): Python source text.

    """
    result: FixResult = _fix(source=source)
    expect_not_in(item="obj=", container=result.source)
    expect_not_in(item="pattern=", container=result.source)
    expect_not_in(item="src=", container=result.source)
    expect_not_in(item="base=", container=result.source)


def test_unknown_keyword_still_keywords_positionals() -> None:
    """``**kwargs`` callees tolerate unknown keywords.

    Positional arguments still gain names.

    """
    result: FixResult = _fix(
        source="""\
import json
x = json.dumps({'a': 1}, unknown=1)
""",
    )
    expect_in(item="obj=", container=result.source)
