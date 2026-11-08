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

from tests.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the guarded fix pipeline on one source.

    Args:
        source: Python source text.

    Returns:
        The fix result.

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
            "import json\nx = json.dumps({'a': 1})\n",
            "x = json.dumps(obj={'a': 1})",
            id="module-attribute",
        ),
        pytest.param(
            "import re\ny = re.sub('a', 'b', s, 1)\n",
            "y = re.sub(pattern='a', repl='b', string=s, count=1)",
            id="several-positionals",
        ),
        pytest.param(
            "from os import replace\nz = replace(a, b)\n",
            "z = replace(src=a, dst=b)",
            id="from-import-name",
        ),
        pytest.param(
            "import os\nz = os.replace(a, b)\n",
            "z = os.replace(src=a, dst=b)",
            id="dotted-module",
        ),
        pytest.param(
            "x = pow(2, 3)\n",
            "x = pow(base=2, exp=3)",
            id="builtin-name",
        ),
        pytest.param(
            "import json\nx = json.dumps({'a': 1}, skipkeys=True)\n",
            "x = json.dumps(obj={'a': 1}, skipkeys=True)",
            id="existing-keyword-kept",
        ),
        pytest.param(
            "import json\nx = json.dumps(obj={'a': 1})\n",
            "x = json.dumps(obj={'a': 1})",
            id="already-keyworded",
        ),
    ],
)
def test_library_call_is_keyworded(*, source: str, expected: str) -> None:
    """Keyword-safe library calls gain parameter names.

    Args:
        source: Python source text.
        expected: Expected last line after fixing.

    """
    result: FixResult = _fix(source=source)
    expect_in(item=expected, container=result.source)
    _ = compile(source=result.source, filename="library.py", mode="exec")


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("print(1, 2)\n", id="var-positional-absorbed"),
        pytest.param(
            "import posixpath\nw = posixpath.join('a', 'b')\n",
            id="positional-only-prefix",
        ),
        pytest.param(
            "import json\nx = json.dumps({'a': 1}, True)\n",
            id="beyond-signature",
        ),
        pytest.param(
            "x = getattr(obj, 'name')\n",
            id="positional-only-builtin",
        ),
        pytest.param(
            "import json\njson = Other()\nx = json.dumps(1)\n",
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
            "import json\nx = json.dumps({'a': 1}, **kw)\n",
            id="double-star-expansion",
        ),
    ],
)
def test_library_call_is_refused(*, source: str) -> None:
    """Uncertain library calls stay positional.

    Args:
        source: Python source text.

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
        source="import json\nx = json.dumps({'a': 1}, unknown=1)\n",
    )
    expect_in(item="obj=", container=result.source)
