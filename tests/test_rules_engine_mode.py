"""Conversion mode: the inference engine fills what nothing else decided."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart.__main__ import main
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_in, expect_not_in

if TYPE_CHECKING:
    from importlib.machinery import ModuleSpec
    from pathlib import Path

    from astart.rules.registry import Registries


@final
class Constants:
    """Constants for the test.

    Attributes:
        total: Untyped module converted in engine mode.

    """

    total: Final[str] = """
def total(items):
    count = 0
    for item in items:
        count += item
    return count
"""


def _fixed(*, source: str, engine: bool) -> str:
    """Fix a module at the guarded ceiling.

    Args:
        source: Module text.
        engine: Whether conversion mode is on.

    Returns:
        The fixed text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            engine=engine,
            min_confidence=0.5,
        ),
    ).source


def test_the_engine_fills_what_the_evidence_leaves_open() -> None:
    """Check that ``total`` gains annotations only in conversion mode."""
    plain: str = _fixed(source=Constants.total, engine=False)
    expect_not_in(item="-> int", container=plain)
    converted: str = _fixed(source=Constants.total, engine=True)
    expect_in(item="def total(items) -> int:", container=converted)
    expect_in(item="count: int = 0", container=converted)


def test_conversion_mode_still_waits_for_the_class_to_exist(
    tmp_path: Path,
) -> None:
    """Check that an engine annotation cannot name a class defined later.

    Args:
        tmp_path: Pytest's temporary directory.

    Raises:
        AssertionError: If the converted module cannot be loaded.

    """
    fixed: str = _fixed(
        source="""
        def make():
            return Late()

        class Late:
            pass
        """,
        engine=True,
    )
    expect_not_in(item="-> Late", container=fixed)
    path: Path = tmp_path / "converted.py"
    _ = path.write_text(data=fixed, encoding="utf-8")
    spec: ModuleSpec | None = spec_from_file_location(
        name="converted",
        location=path,
    )
    if spec is None or spec.loader is None:
        msg: str = "cannot load the converted module"
        raise AssertionError(msg)
    spec.loader.exec_module(module=module_from_spec(spec=spec))


def test_the_command_line_flag_lowers_the_default_floor(
    tmp_path: Path,
) -> None:
    """Check that ``fix --engine`` writes engine annotations by default.

    Args:
        tmp_path: Pytest's temporary directory.

    """
    plain: Path = tmp_path / "plain.py"
    converted: Path = tmp_path / "converted.py"
    for path in (plain, converted):
        _ = path.write_text(
            data=dedent(text=Constants.total),
            encoding="utf-8",
        )
    base: list[str] = ["fix", "--no-format", "--checker", "off"]
    _ = main(argv=[*base, str(object=plain)])
    _ = main(argv=[*base, "--engine", str(object=converted)])
    expect_not_in(item="-> int", container=plain.read_text(encoding="utf-8"))
    expect_in(
        item="def total(items) -> int:",
        container=converted.read_text(encoding="utf-8"),
    )
