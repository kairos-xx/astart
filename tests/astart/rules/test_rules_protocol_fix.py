"""Verify Protocol synthesis through the fix runner."""

from __future__ import annotations

from ast import parse
from subprocess import CompletedProcess, run
from sys import executable
from textwrap import dedent
from typing import TYPE_CHECKING

from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.registry import Registries


def _importable(*, source: str, directory: Path) -> None:
    """Assert a converted module imports cleanly in a subprocess.

    Args:
        source (str): Module source to write and import.
        directory (Path): Temporary directory to hold the module.

    """
    path: Path = directory / "converted_module.py"
    path.write_text(data=source)
    completed: CompletedProcess[bytes] = run(
        args=[executable, "-c", "import converted_module"],
        cwd=directory,
        check=False,
        capture_output=True,
    )
    expect_equal(actual=completed.returncode, expected=0)


def _fix(*, source: str, settings: FixSettings | None = None) -> FixResult:
    """Run the guarded fixer on a dedented snippet.

    Args:
        source (str): Python source.
        settings (FixSettings | None): Fixer settings; guarded ceiling by
            default.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=settings or FixSettings(ceiling=FixSafety.guarded),
    )


def test_unannotated_structural_parameter_gets_a_protocol() -> None:
    """Check that unannotated structural parameter gets a protocol."""
    result: FixResult = _fix(
        source="""
        def load(src):
            return src.read(1)
        """,
    )
    parse(source=result.source)
    expect_in(item="from typing import Protocol", container=result.source)
    expect_in(item="class SupportsReading(Protocol):", container=result.source)
    expect_in(item="def load(src: SupportsReading)", container=result.source)
    expect_in(item="def read(self, arg0: int, /)", container=result.source)


def test_protocol_precedes_the_function_that_uses_it() -> None:
    """Check that protocol precedes the function that uses it."""
    result: FixResult = _fix(
        source="""
        def load(src):
            return src.read(1)
        """,
    )
    expect_true(
        condition=result.source.index("class SupportsReading")
        < result.source.index("def load("),
    )


def test_second_run_changes_nothing() -> None:
    """Check that second run changes nothing."""
    first: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)
""",
    )
    expect_equal(
        actual=(_fix(source=first.source)).source,
        expected=first.source,
    )


def test_identical_usage_shares_one_protocol() -> None:
    """Check that identical usage shares one protocol."""
    result: FixResult = _fix(
        source="""
        def a(src):
            return src.read(1)


        def b(stream):
            return stream.read(2)
        """,
    )
    expect_equal(actual=result.source.count("(Protocol):"), expected=1)
    expect_in(item="def b(stream: SupportsReading", container=result.source)


def test_existing_protocol_import_is_reused() -> None:
    """Check that existing protocol import is reused."""
    result: FixResult = _fix(
        source="""
        from typing import Protocol


        def load(src):
            return src.read(1)
        """,
    )
    expect_equal(actual=result.source.count("import Protocol"), expected=1)


def test_value_use_gets_no_protocol() -> None:
    """Check that value use gets no protocol."""
    result: FixResult = _fix(
        source="""\
def load(src):
    return src
""",
    )
    expect_not_in(item="Protocol", container=result.source)


def test_default_value_gets_no_protocol() -> None:
    """Check that default value gets no protocol."""
    result: FixResult = _fix(
        source="""\
def load(src=None):
    return src.read(1)
""",
    )
    expect_not_in(item="Protocol", container=result.source)


def test_method_parameter_protocol_precedes_the_class() -> None:
    """Check that method parameter protocol precedes the class."""
    result: FixResult = _fix(
        source="""
        class Loader:
            def load(self, src):
                return src.read(1)
        """,
    )
    parse(source=result.source)
    expect_true(
        condition=result.source.index("(Protocol):")
        < result.source.index("class Loader"),
    )
    expect_in(
        item="def load(self, src: SupportsReading",
        container=result.source,
    )


def test_proven_ceiling_does_not_synthesize() -> None:
    """Check that proven ceiling does not synthesize."""
    registries: Registries = default_registries()
    result: FixResult = fix_source(
        source="""\
def load(src):
    return src.read(1)
""",
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.proven),
    )
    expect_not_in(item="Protocol", container=result.source)


def test_runtime_checkable_absent_by_default() -> None:
    """Check that runtime_checkable is absent by default."""
    result: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)


def probe(thing):
    return isinstance(thing, SupportsReading)
""",
    )
    expect_in(item="class SupportsReading(Protocol):", container=result.source)
    expect_not_in(item="runtime_checkable", container=result.source)


def test_runtime_checkable_only_with_setting_and_isinstance() -> None:
    """Check that runtime_checkable needs the setting and isinstance."""
    settings: FixSettings = FixSettings(
        ceiling=FixSafety.guarded,
        runtime_protocols=True,
    )
    source: str = """\
def load(src):
    return src.read(1)


def probe(thing):
    return isinstance(thing, SupportsReading)
"""
    result: FixResult = _fix(source=source, settings=settings)
    expect_in(item="@runtime_checkable", container=result.source)
    expect_in(item="import runtime_checkable", container=result.source)
    quiet: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)
""",
        settings=settings,
    )
    expect_not_in(item="runtime_checkable", container=quiet.source)


def test_type_checking_placement_quotes_and_stays_importable(
    tmp_path: Path,
) -> None:
    """Check that type_checking placement quotes and stays importable.

    Args:
        tmp_path (Path): Directory the converted module is written to.

    """
    result: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)
""",
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            protocol_placement="type-checking",
        ),
    )
    expect_in(item="if TYPE_CHECKING:", container=result.source)
    expect_in(item="from typing import TYPE_CHECKING", container=result.source)
    expect_in(item="src: 'SupportsReading'", container=result.source)
    _importable(source=result.source, directory=tmp_path)


def test_type_checking_keeps_isinstance_protocol_at_runtime(
    tmp_path: Path,
) -> None:
    """Check that isinstance-referenced protocols stay runtime-visible.

    Args:
        tmp_path (Path): Directory the converted module is written to.

    """
    result: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)


def probe(thing):
    return isinstance(thing, SupportsReading)
""",
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            protocol_placement="type-checking",
            runtime_protocols=True,
        ),
    )
    expect_not_in(item="if TYPE_CHECKING:", container=result.source)
    expect_in(item="@runtime_checkable", container=result.source)
    _importable(source=result.source, directory=tmp_path)


def test_function_placement_moves_the_class_next_to_the_def() -> None:
    """Check that function placement moves the class next to the def."""
    source: str = """\
class Loader:
    def load(self, src):
        return src.read(1)
"""
    module_mode: FixResult = _fix(source=source)
    expect_true(
        condition=module_mode.source.index("(Protocol):")
        < module_mode.source.index("class Loader"),
    )
    function_mode: FixResult = _fix(
        source=source,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            protocol_placement="function",
        ),
    )
    parse(source=function_mode.source)
    expect_true(
        condition=function_mode.source.index("class Loader")
        < function_mode.source.index("(Protocol):")
        < function_mode.source.index("def load("),
    )


def test_index_and_len_gets_sequence_with_accept_general() -> None:
    """Check that index+len usage gets ``Sequence`` when opted in."""
    result: FixResult = _fix(
        source="""\
def total(items):
    return items[0] + len(items)
""",
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            accept_general=True,
        ),
    )
    expect_in(item="Sequence", container=result.source)
    expect_not_in(item="Protocol", container=result.source)


def test_iteration_only_reuses_iterable_by_default() -> None:
    """Check that iteration-only usage reuses ``Iterable`` by default."""
    result: FixResult = _fix(
        source="""\
def total(items):
    out = 0
    for item in items:
        out += 1
    return out
""",
    )
    expect_equal(
        actual=result.source.count("import Iterable"),
        expected=1,
    )
    expect_not_in(item="Protocol", container=result.source)


def test_positional_callee_reuses_callable() -> None:
    """Check that a positional callee reuses ``Callable``."""
    result: FixResult = _fix(
        source="""\
def apply(fn):
    return fn(1, "x")
""",
    )
    expect_in(item="Callable", container=result.source)
    expect_not_in(item="Protocol", container=result.source)
