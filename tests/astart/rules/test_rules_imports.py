"""Verify automatic import insertion."""

from __future__ import annotations

from ast import (
    Module,
    expr,
    fix_missing_locations,
    parse,
    unparse,
)
from textwrap import dedent

from astart.rules.imports import ensure_names, insert_import

from tests.support.expectations import expect_equal


def _module(*, source: str) -> Module:
    """Parse a dedented snippet.

    Args:
        source (str): Python source.

    Returns:
        Module: The parsed module.

    """
    return parse(source=dedent(text=source))


def _text(*, module: Module) -> str:
    """Render a module back to source.

    Args:
        module (Module): Parsed module.

    Returns:
        str: The regenerated source.

    """
    return unparse(ast_obj=fix_missing_locations(node=module))


def test_new_import_goes_after_existing_imports() -> None:
    """Check that new import goes after existing imports."""
    module: Module = _module(
        source='''
        """Doc."""
        from __future__ import annotations
        import os

        X = 1
        ''',
    )
    insert_import(
        module=module,
        source="pathlib",
        name="Path",
        before=len(module.body),
    )
    lines: list[str] = _text(module=module).splitlines()
    expect_equal(
        actual=lines[:4],
        expected=[
            '"""Doc."""',
            "from __future__ import annotations",
            "import os",
            "from pathlib import Path",
        ],
    )


def test_name_joins_an_existing_from_import() -> None:
    """Check that name joins an existing from import."""
    module: Module = _module(
        source="""\
from typing import Final
""",
    )
    insert_import(
        module=module,
        source="typing",
        name="Protocol",
        before=len(module.body),
    )
    expect_equal(
        actual=_text(module=module),
        expected="from typing import Final, Protocol",
    )


def test_present_name_is_not_imported_twice() -> None:
    """Check that present name is not imported twice."""
    module: Module = _module(
        source="""\
from typing import Final
""",
    )
    insert_import(
        module=module,
        source="typing",
        name="Final",
        before=len(module.body),
    )
    expect_equal(
        actual=_text(module=module),
        expected="from typing import Final",
    )


def test_ensure_names_imports_only_known_missing_names() -> None:
    """Check that ensure names imports only known missing names."""
    module: Module = _module(
        source="""\
import os
""",
    )
    expression: expr = parse(
        source="dict[str, Sequence[Path]]",
        mode="eval",
    ).body
    ensure_names(
        module=module,
        expression=expression,
        before=len(module.body),
    )
    expect_equal(
        actual=_text(module=module).splitlines(),
        expected=[
            "import os",
            "from collections.abc import Sequence",
            "from pathlib import Path",
        ],
    )
