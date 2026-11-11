"""Exercise the conversion protocols and the print-like helper."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Never, cast

import astart.graph.aprint as aprint_module
import pytest
from astart.graph.aprint import aprint
from astart.graph.conversion.interfaces import (
    ConversionBackend,
    ConversionStage,
)

from tests.support.expectations import expect_equal

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from astart.graph.conversion.context import ConversionContext


def _static(*, protocol: type, name: str) -> Callable[..., Never]:
    """Return the raw function behind a protocol static method.

    Args:
        protocol (type): Protocol class declaring the method.
        name (str): Method name.

    Returns:
        Callable[..., Never]: Underlying callable.

    """
    return cast(
        typ="Callable[..., Never]",
        val=vars(protocol)[name].__func__,
    )


def _getter(
    *,
    protocol: type,
    name: str,
) -> Callable[[ConversionStage | ConversionBackend], str]:
    """Return the getter function of a protocol property.

    Args:
        protocol (type): Protocol class declaring the property.
        name (str): Property name.

    Returns:
        Callable[[ConversionStage | ConversionBackend], str]: Underlying
            getter.

    """
    return cast(
        typ="Callable[[ConversionStage | ConversionBackend], str]",
        val=vars(protocol)[name].fget,
    )


@pytest.mark.parametrize("protocol", [ConversionStage, ConversionBackend])
def test_protocol_name_properties_are_abstract(*, protocol: type) -> None:
    """Require implementations to provide a name.

    Args:
        protocol (type): Protocol class under test.

    """
    with pytest.raises(expected_exception=NotImplementedError):
        _getter(protocol=protocol, name="name")(
            cast(typ="ConversionStage", val=None),
        )


def test_protocol_methods_are_abstract() -> None:
    """Require implementations to provide run and convert."""
    context: ConversionContext = cast(typ="ConversionContext", val=None)
    with pytest.raises(expected_exception=NotImplementedError):
        _static(protocol=ConversionStage, name="run")(context=context)
    with pytest.raises(expected_exception=NotImplementedError):
        _static(protocol=ConversionBackend, name="convert")(context=context)


def test_aprint_writes_to_streams() -> None:
    """Mimic print for text streams, separators and endings."""
    buffer: StringIO = StringIO()
    aprint("a", 1, None, sep="-", end="!", file=buffer, flush=True)
    aprint("tail", file=buffer)
    expect_equal(
        actual=buffer.getvalue(),
        expected="""\
a-1-None!tail
""",
    )


def test_aprint_defaults_to_standard_output(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fall back to stdout when no file is supplied.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    """
    buffer: StringIO = StringIO()
    monkeypatch.setattr(target=aprint_module, name="stdout", value=buffer)
    aprint("hello")
    expect_equal(
        actual=buffer.getvalue(),
        expected="""\
hello
""",
    )


def test_aprint_writes_to_paths(*, tmp_path: Path) -> None:
    """Append to files named by strings or paths.

    Args:
        tmp_path (Path): Directory receiving the output file.

    """
    target: Path = tmp_path / "log.txt"
    aprint("first", file=str(object=target))
    aprint("second", file=target, mode="a")
    aprint("third", file=target, mode="w", end="")
    expect_equal(actual=target.read_text(encoding="utf-8"), expected="third")
