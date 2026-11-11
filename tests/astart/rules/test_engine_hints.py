"""Engine-sourced hints: lazy conversion, variable scan, hint gating."""

from __future__ import annotations

from ast import dump
from typing import TYPE_CHECKING, cast

from astart import CommentedModule, parse
from astart.rules.engine_hints import (
    LazyConversion,
    engine_hints,
    engine_variables,
)
from astart.rules.hints import Hint, HintBasis, Key

from tests.support.expectations import expect_equal, expect_is, expect_true

if TYPE_CHECKING:
    import pytest


class _StubConversion:
    """Stand-in for ``LazyConversion`` returning fixed text."""

    def __init__(self, *, text: str | None) -> None:
        """Store the text to report.

        Args:
            text (str | None): Converted source, or ``None`` for engine
                failure.

        """
        self._text: str | None = text

    @property
    def text(self) -> str | None:
        """Give the stored text.

        Returns:
            str | None: The stored text.

        """
        return self._text


def _conversion(*, text: str | None) -> LazyConversion:
    """Wrap fixed text in the ``LazyConversion`` interface.

    Args:
        text (str | None): Converted source, or ``None`` for engine failure.

    Returns:
        LazyConversion: A conversion object reporting ``text``.

    """
    return cast(typ="LazyConversion", val=_StubConversion(text=text))


def test_engine_variables_collects_annotated_locals() -> None:
    """AnnAssign names inside functions map to ``qual.name`` paths."""
    found: dict[str, str] = engine_variables(
        converted=(
            "def f():\n"
            "    x: int = 1\n"
            "    y: list[str] = []\n"
            "class C:\n"
            "    def m(self):\n"
            "        z: bytes = b''\n"
        ),
    )
    expect_true(condition=found["f.x"] == "int")
    expect_true(condition=found["f.y"] == "list[str]")
    expect_true(
        condition=any(
            key.endswith(".z") and value == "bytes"
            for key, value in found.items()
        ),
    )


def test_engine_variables_ignores_unannotated_and_module_level() -> None:
    """Plain assignments and module-level AnnAssigns are not locals."""
    found: dict[str, str] = engine_variables(
        converted="""\
top: int = 1
def f():
    x = 2
""",
    )
    expect_equal(actual=found, expected={})


def test_lazy_conversion_returns_none_on_engine_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An engine exception leaves the module to the pipeline.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture replacing
            ``CommentedModule.convert``.

    """
    module: CommentedModule = parse(
        source="""\
x = 1
""",
    )

    def boom(_self: CommentedModule, **_kwargs: object) -> object:
        """Raise the failure the engine reports on odd input.

        Args:
            _self (CommentedModule): Module being converted.
            _kwargs (object): Ignored convert arguments.

        Returns:
            Never reached; the function always raises.

        Raises:
            ValueError: Always.

        """
        msg: str = "engine failed"
        raise ValueError(msg)

    monkeypatch.setattr(
        target=CommentedModule,
        name="convert",
        value=boom,
    )
    conversion: LazyConversion = LazyConversion(module=module)
    expect_equal(actual=conversion.text, expected=None)
    expect_equal(actual=conversion.text, expected=None)


def test_engine_hints_empty_when_conversion_fails() -> None:
    """No engine output means no engine hints."""
    module: CommentedModule = parse(
        source="""\
def f(x):
    return x
""",
    )
    found: dict[Key, Hint] = engine_hints(
        module=module,
        conversion=_conversion(text=None),
    )
    expect_equal(actual=found, expected={})


def test_engine_hints_maps_parameters_and_returns() -> None:
    """Allowed, evaluable annotations become engine-basis hints."""
    module: CommentedModule = parse(
        source="""\
def f(x):
    return x
""",
    )
    found: dict[Key, Hint] = engine_hints(
        module=module,
        conversion=_conversion(
            text="""\
def f(x: int) -> str:
    return str(x)
""",
        ),
    )
    expect_true(condition=len(found) >= 1)
    for hint in found.values():
        expect_is(actual=hint.basis, expected=HintBasis.engine)


def test_engine_hints_skips_disallowed_annotations() -> None:
    """Annotations naming unknown sources are filtered out."""
    module: CommentedModule = parse(
        source="""\
def f(x):
    return x
""",
    )
    found: dict[Key, Hint] = engine_hints(
        module=module,
        conversion=_conversion(
            text="""\
def f(x: mystery_type) -> also_missing:
    return x
""",
        ),
    )
    expect_equal(actual=found, expected={})


def test_lazy_conversion_leaves_the_module_untouched() -> None:
    """Reading the engine text must not write annotations into the module."""
    source: str = (
        "def f(items):\n"
        "    return {k: v for k, v in enumerate(items) if v % 2 == 0}\n"
        "f([1, 2])\n"
    )
    module: CommentedModule = parse(source=source)
    before: str = dump(node=module)
    _ = LazyConversion(module=module).text
    expect_equal(actual=dump(node=module), expected=before)
