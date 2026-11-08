"""Non-ASCII source must not break inference: AST columns are byte offsets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
from astart import parse
from astart.ast import CommentedModule
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult

SOURCES: Final[tuple[str, ...]] = (
    'def f(a):\n    return a\n\n\nx = "éééééééééé"; y = (f(1))\n',
    'def f(a):\n    s = "ééééééééééééééééé" + str((a))\n    return s\n',
    'def f(a):\n    return ("ééééééééééééééééé", (a))\n',
    'def f(a):\n    return ("日本語日本語日本語日本語", (a)) + (a,)\n',
)


@pytest.mark.parametrize("source", SOURCES)
def test_conversion_survives_multibyte_text_before_parentheses(
    *,
    source: str,
    tmp_path: Path,
) -> None:
    """Check that conversion survives multibyte text before parentheses.

    Args:
        source: Parametrized module source.
        tmp_path: pytest temporary directory.

    """
    module: CommentedModule = parse(source=source, filename="t.py")
    _ = module.convert(stubs_path=tmp_path, apply=False)


def test_a_failing_inference_layer_degrades_instead_of_raising(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that a failing inference layer degrades instead of raising.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    """

    def boom(*_args: object, **_kwargs: object) -> None:
        """Stand-in ``convert`` that always raises.

        Args:
            _args: Ignored positional arguments.
            _kwargs: Ignored keyword arguments.

        Raises:
            IndexError: Always, to simulate a failing inference layer.

        """
        msg: str = "analyzer exploded"
        raise IndexError(msg)

    monkeypatch.setattr(target=CommentedModule, name="convert", value=boom)
    registries: Registries = default_registries()
    result: FixResult = fix_source(
        source="def f(x=1):\n    print(x)\n",
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )
    expect_equal(actual=result.parse_error, expected=None)
    expect_in(item="-> None", container=result.source)
