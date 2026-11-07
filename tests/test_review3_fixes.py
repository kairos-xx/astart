"""Regression tests for the final review of the check/fix work."""

from __future__ import annotations

import builtins
from io import StringIO
from textwrap import dedent
from types import FunctionType
from typing import TYPE_CHECKING

from astart.cli.commands import FixCommandSettings, FixMode, run_fix
from astart.rules import (
    FixResult,
    FixSettings,
    check,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal, expect_in, expect_not_in

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.engine import CheckResult
    from astart.rules.registry import Registries


def _fix(*, source: str) -> FixResult:
    """Run the guarded fixer on a dedented snippet.

    Args:
        source: Python source.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


def _runs(*, source: str) -> None:
    """Import the fixed module, so unbound names raise.

    Args:
        source: Fixed Python source.

    """
    _ = FunctionType(
        code=compile(source=source, filename="fixed.py", mode="exec"),
        globals={"__name__": "fixed", "__builtins__": builtins},
    )()


def test_c1_keyword_colliding_with_generated_names_gets_no_protocol() -> None:
    """Check that keyword colliding with generated names gets no protocol."""
    for call in ("x.a(1, arg0=2)", "x.a(self=2)"):
        result: FixResult = _fix(
            source=f"""\
def f(x):
    return {call}
""",
        )
        compile(source=result.source, filename="m.py", mode="exec")
        expect_not_in(item="Protocol", container=result.source, message=call)


def test_c2_imports_stay_runtime_correct() -> None:
    """Check that imports stay runtime correct."""
    sources: dict[str, str] = {
        "guarded import": """
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from typing import Protocol
            def g(y):
                return y.read(1)
            """,
        "late import": """
            def g(y):
                return y.read(1)
            from typing import Protocol
            """,
        "parameter named like the import": """
            def h(TypeVar):
                return TypeVar
            def f(x):
                return x
            """,
        "rebound name": """
            Protocol = 5
            def g(y):
                return y.read(1)
            """,
        "late typevar import": """
            def f(x):
                return x
            from typing import TypeVar
            """,
    }
    for label, source in sources.items():
        result: FixResult = _fix(source=source)
        _runs(source=result.source)
        expect_equal(actual=result.parse_error, expected=None, message=label)


def test_i1_generic_class_variable_is_not_reused_for_a_method() -> None:
    """Check that generic class variable is not reused for a method."""
    result: FixResult = _fix(
        source="""
        from typing import Generic, TypeVar
        T = TypeVar("T")
        class Box(Generic[T]):
            def echo(self, x):
                return x
        """,
    )
    _runs(source=result.source)
    expect_not_in(item="x: T)", container=result.source)


def test_i2_first_parameter_of_a_method_is_never_synthesized() -> None:
    """Check that first parameter of a method is never synthesized."""
    protocol: FixResult = _fix(
        source="""\
class C:
    def f(x):
        return x.a
""",
    )
    expect_not_in(item="Protocol", container=protocol.source)
    typevar: FixResult = _fix(
        source="""\
class C:
    def n(x):
        return x
""",
    )
    expect_not_in(item="TypeVar", container=typevar.source)


def test_i3_overrides_and_dunders_are_not_narrowed() -> None:
    """Check that overrides and dunders are not narrowed."""
    dunder: FixResult = _fix(
        source=(
            dedent(
                text="""\
    class C:
        def __eq__(self, other):
            return other.x == 1
    """,
            )
        ),
    )
    expect_not_in(item="Protocol", container=dunder.source)
    override: FixResult = _fix(
        source="""
        class B:
            pass
        class D(B):
            def f(self, x):
                return x.a
        """,
    )
    expect_not_in(item="Protocol", container=override.source)


def test_i4_overload_groups_are_left_alone() -> None:
    """Check that overload groups are left alone."""
    result: FixResult = _fix(
        source="""
        from typing import overload
        @overload
        def f(x): ...
        def f(x):
            return x.a
        """,
    )
    expect_not_in(item="Protocol", container=result.source)


def test_i5_atomic_write_keeps_mode_and_symlinks(*, tmp_path: Path) -> None:
    """Check that atomic write keeps mode and symlinks.

    Args:
        tmp_path: Directory holding the symlinked file.

    """
    real: Path = tmp_path / "real.py"
    real.write_text(
        data="""\
def f(x):
    print(x)
""",
        encoding="utf-8",
    )
    real.chmod(mode=0o755)
    link: Path = tmp_path / "link.py"
    link.symlink_to(target=real)
    out: StringIO = StringIO()
    _ = run_fix(
        settings=FixCommandSettings(
            paths=(link,),
            ceiling=FixSafety.guarded,
            stubs_path=None,
            mode=FixMode.write,
            run_formatter=False,
        ),
        out=out,
    )
    expect_equal(actual=link.is_symlink(), expected=True)
    expect_equal(actual=real.stat().st_mode & 0o777, expected=0o755)
    expect_in(item="-> None", container=real.read_text(encoding="utf-8"))
    expect_equal(
        actual=(
            [p.name for p in tmp_path.iterdir() if "astart-tmp" in p.name]
        ),
        expected=[],
    )
    expect_equal(actual=real.exists(), expected=True)


def test_i6_synthesized_protocol_members_are_not_flagged() -> None:
    """Check that synthesized protocol members are not flagged."""
    result: FixResult = _fix(
        source="""\
def load(src):
    return src.read(1)
""",
    )
    registries: Registries = default_registries()
    again: CheckResult = check(
        source=result.source,
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
    )
    flagged: list[str] = [
        f.subject_path for f in again.findings if "Protocol" in f.subject_path
    ]
    expect_equal(actual=flagged, expected=[])
