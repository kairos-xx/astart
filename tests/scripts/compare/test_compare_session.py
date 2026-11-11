"""The unified reporting module shares three authoritative source trees."""

from __future__ import annotations

from argparse import Namespace
from ast import parse as ast_parse
from json import loads
from typing import TYPE_CHECKING, cast

from astart.rules import recovery

from scripts.compare import (
    conversion_report,
    conversion_structure,
    evidence,
    session,
)
from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from ast import Expression
    from collections.abc import Callable
    from pathlib import Path

    import pytest
    from astart import CommentedModule

    from scripts.compare.conversion_structure import Difference


def test_integrated_report_parses_each_source_once(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All report phases reuse the same module nodes.

    Args:
        tmp_path (Path): Isolated report directory.
        monkeypatch (pytest.MonkeyPatch): Scoped parser and argument guards.

    """
    untyped: str = 'def run(value):\n    """Run."""\n    return value\n'
    typed: str = (
        'def run(value: int) -> int:\n    """Run."""\n    return value\n'
    )
    input_path: Path = tmp_path / "input.py"
    reference_path: Path = tmp_path / "reference.py"
    todo_path: Path = tmp_path / "TODO.md"
    out_dir: Path = tmp_path / "artifacts"
    out_dir.mkdir()
    input_path.write_text(data=untyped, encoding="utf-8")
    reference_path.write_text(data=typed, encoding="utf-8")
    (out_dir / "result.py").write_text(
        data=typed,
        encoding="utf-8",
    )
    todo_path.write_text(
        data="""\
<!-- conversion:start -->
<!-- conversion:end -->
""",
        encoding="utf-8",
    )
    original: Callable[..., CommentedModule] = session.parse
    parsed: list[str] = []

    def counted(*, source: str) -> CommentedModule:
        """Count each session-owned input parse.

        Args:
            source (str): Comparison input.

        Returns:
            CommentedModule: Its authoritative module.

        """
        parsed.append(source)
        return original(source=source)

    def expression_only(*, source: str, mode: str = "exec") -> Expression:
        """Refuse whole-source reparses in report helpers.

        Args:
            source (str): Annotation expression or forbidden module text.
            mode (str): Parser grammar.

        Returns:
            Expression: An annotation expression tree.

        """
        expect_equal(actual=mode, expected="eval")
        return ast_parse(source=source, mode="eval")

    monkeypatch.setattr(target=session, name="parse", value=counted)
    for module in (
        conversion_report,
        conversion_structure,
        evidence,
        recovery,
    ):
        monkeypatch.setattr(target=module, name="parse", value=expression_only)
    monkeypatch.setattr(
        target=conversion_report,
        name="_arguments",
        value=lambda: Namespace(
            untyped=input_path,
            typed=reference_path,
            reference_graph=None,
            out_dir=out_dir,
            todo=todo_path,
            no_opacity=True,
            no_todo=False,
            reuse=True,
            min_confidence=0.5,
            examples=1,
            checker=False,
            ledger="",
        ),
    )
    expect_equal(actual=conversion_report.main(), expected=0)
    expect_equal(actual=parsed, expected=[untyped, typed, typed])
    data: dict[str, object] = loads(
        s=(out_dir / "conversion-report.json").read_text(encoding="utf-8"),
    )
    summary: dict[str, object] = cast(
        typ="dict[str, object]",
        val=data["agent_summary"],
    )
    expect_equal(
        actual=summary["comparison_module_parses"],
        expected=3,
    )
    expect_equal(actual=len(list(out_dir.glob(pattern="*.json"))), expected=1)
    expect_equal(actual=len(list(out_dir.glob(pattern="*.md"))), expected=1)
    expect_in(
        item="Documentation and generated declarations",
        container=todo_path.read_text(),
    )


def test_type_parameter_families_and_output_only_classes() -> None:
    """Separate type-parameter kinds and retain class origin evidence."""
    source: str = """from typing import TypeVar, ParamSpec, TypeVarTuple
T = TypeVar("T", bound=int, default=int)
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")
class Synthesized[T]:
    value: T
"""
    differences: list[Difference] = conversion_structure.compare_artifacts(
        typed=source,
        converted=source,
        untyped="",
    )
    kinds: set[str] = {item.kind for item in differences}
    expect_true(
        condition={"typevars", "paramspecs", "type_var_tuples", "classes"}
        <= kinds,
    )
    generated: Difference = next(
        item for item in differences if item.kind == "classes"
    )
    expect_true(condition=generated.actual is not None)
    if generated.actual is not None:
        expect_equal(
            actual=generated.actual.fields["origin"],
            expected="output_only",
        )
