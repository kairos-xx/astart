"""Verify the single-pass fix runner."""

from __future__ import annotations

import ast
from dataclasses import replace
from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.ast import CommentedModule
from astart.rules import (
    Catalog,
    apply_fix,
    default_registries,
    load_default_catalog,
)
from astart.rules.appliers import Appliers
from astart.rules.model import Example, Fix, Rule
from astart.rules.predicate import AllOf, Compare, CompareOp, Not
from astart.rules.runner import FixResult, FixSettings, fix_source
from astart.rules.vocabulary import (
    Domain,
    FixSafety,
    Maturity,
    Owner,
    Severity,
)

from tests.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from pathlib import Path

    from astart import GraphConversion
    from astart.rules.facts import ModuleFacts, Subject


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_inferences: Grouped module constant.

    """

    max_inferences: Final[int] = 2


SAMPLE = """\
# header
LIMIT = 3  # limit


def scale(x, k):  # scale
    print(x * k)


scale(2, 3)  # call
"""


def _run(
    *,
    source: str,
    ceiling: FixSafety,
    catalog: Catalog | None = None,
    settings: FixSettings | None = None,
) -> FixResult:
    """Run the fixer with the default catalog unless told otherwise.

    Args:
        source: Python source.
        ceiling: Highest fix safety to apply.
        catalog: Catalog override.
        settings: Settings override; the ceiling is applied on top.

    Returns:
        The fix result.

    """
    registries = default_registries()
    chosen = catalog or load_default_catalog(registries=registries)
    base = settings or FixSettings(ceiling=ceiling)
    return fix_source(
        source=dedent(text=source),
        filename="s.py",
        catalog=chosen,
        registries=registries,
        settings=replace(base, ceiling=ceiling),
    )


def _applied_keys(*, result: FixResult) -> set[str]:
    """Return the distinct fix keys that were applied.

    Args:
        result: Fix result.

    Returns:
        The fix keys.

    """
    return {item.fix_key for item in result.applied}


def test_ceiling_selects_fixes() -> None:
    """Apply only what the ceiling allows."""
    safe = _run(source=SAMPLE, ceiling=FixSafety.proven)
    expect_equal(
        actual=_applied_keys(result=safe),
        expected={"typing.add-final", "typing.add-none-return"},
    )
    expect_in(item="scale(2, 3)", container=safe.source)
    guarded = _run(source=SAMPLE, ceiling=FixSafety.guarded)
    expect_equal(
        actual=_applied_keys(result=guarded),
        expected={
            "typing.add-final",
            "typing.add-none-return",
            "typing.add-inferred-annotation",
            "calls.add-keywords",
        },
    )
    with pytest.raises(expected_exception=ValueError, match="ceiling"):
        _run(source=SAMPLE, ceiling=FixSafety.suggest)


def test_all_fixes_apply_in_one_pass() -> None:
    """Edit one tree, write once, keep every comment."""
    result = _run(source=SAMPLE, ceiling=FixSafety.guarded)
    for expected in (
        "# header",
        "LIMIT: Final[int] = 3  # limit",
        "def scale(x: int, k: int) -> None:  # scale",
        "scale(x=2, k=3)  # call",
        "from typing import Final",
    ):
        expect_in(item=expected, container=result.source)
    ast.parse(source=result.source)
    expect_equal(actual=result.skipped, expected=())
    expect_equal(actual=result.parse_error, expected=None)


def _two_fix_catalog(*, first_before: tuple[str, ...] = ()) -> Catalog:
    """Build a catalog where two fixes target the same node.

    Args:
        first_before: Fixes the first fix must run before.

    Returns:
        The catalog.

    """
    fact = Compare(
        fact="binding.is_module_global",
        op=CompareOp.eq,
        value=True,
    )
    rule = Rule(
        key="glob",
        code="GLOB",
        title="glob",
        rationale="test",
        domain=Domain.typing,
        severity=Severity.error,
        maturity=Maturity.stable,
        owner=Owner.astart,
        subject=("Assign",),
        message="m",
        when=AllOf(
            items=(
                fact,
                Compare(
                    fact="binding.name_is_uppercase",
                    op=CompareOp.eq,
                    value=True,
                ),
                Not(
                    item=Compare(
                        fact="binding.is_final",
                        op=CompareOp.eq,
                        value=True,
                    ),
                ),
            ),
        ),
        requires=(
            "binding.is_final",
            "binding.is_module_global",
            "binding.name_is_uppercase",
        ),
        fixes=("fix.a", "fix.b"),
        examples=(
            Example(
                source="""\
X = 1
""",
                triggers=True,
            ),
        ),
    )

    def fix(*, key: str, before: tuple[str, ...] = ()) -> Fix:
        return Fix(
            key=key,
            rules=("glob",),
            safety=FixSafety.proven,
            min_confidence=1.0,
            edits=("typing.add-final",),
            preconditions=Compare(
                fact="binding.value_is_immutable_literal",
                op=CompareOp.eq,
                value=True,
            ),
            idempotent=True,
            before=before,
        )

    return Catalog(
        rules=(rule,),
        fixes=(fix(key="fix.a", before=first_before), fix(key="fix.b")),
        profiles=(),
        relations=(),
    )


def test_conflicting_offers_on_one_node_are_skipped() -> None:
    """Apply the first offer; skip the second as a conflict."""
    result = _run(
        source="""\
X = 1
""",
        ceiling=FixSafety.proven,
        catalog=_two_fix_catalog(),
    )
    expect_equal(
        actual=[a.fix_key for a in result.applied],
        expected=["fix.a"],
    )
    expect_equal(
        actual=[(s.fix_key, s.reason) for s in result.skipped],
        expected=[("fix.b", "conflict")],
    )


def test_fix_order_follows_before_after_relations() -> None:
    """Let ``before`` decide which of two conflicting fixes wins."""
    result = _run(
        source="""\
X = 1
""",
        ceiling=FixSafety.proven,
        catalog=_two_fix_catalog(first_before=("fix.b",)),
    )
    expect_equal(
        actual=[a.fix_key for a in result.applied],
        expected=["fix.a"],
    )
    flipped = _two_fix_catalog()
    flipped = replace(
        flipped,
        fixes=(flipped.fixes[0], replace(flipped.fixes[1], before=("fix.a",))),
    )
    result = _run(
        source="""\
X = 1
""",
        ceiling=FixSafety.proven,
        catalog=flipped,
    )
    expect_equal(
        actual=[a.fix_key for a in result.applied],
        expected=["fix.b"],
    )


def test_failing_applier_is_skipped_with_reason() -> None:
    """Report an applier that raises and leave the source alone."""

    def boom(_subject: Subject, _facts: ModuleFacts) -> None:
        msg = "boom"
        raise ValueError(msg)

    result = _run(
        source="""\
LIMIT = 3
""",
        ceiling=FixSafety.proven,
        settings=FixSettings(
            ceiling=FixSafety.proven,
            appliers={"typing.add-final": boom},
        ),
    )
    expect_equal(
        actual=result.source,
        expected="""\
LIMIT = 3
""",
    )
    expect_equal(actual=result.applied, expected=())
    expect_true(condition=any("boom" in s.reason for s in result.skipped))


def test_unparsable_source_returns_parse_error_without_raising() -> None:
    """Report syntax errors as data."""
    result = _run(
        source="""\
def (:
""",
        ceiling=FixSafety.guarded,
    )
    expect_true(condition=result.parse_error is not None)
    expect_equal(
        actual=result.source,
        expected="""\
def (:
""",
    )


def test_nothing_to_fix_returns_source_unchanged() -> None:
    """Leave clean code byte for byte alone."""
    source = """\
def f(a: int) -> int:
    return a
"""
    result = _run(source=source, ceiling=FixSafety.guarded)
    expect_equal(actual=result.source, expected=source)
    expect_equal(actual=result.applied, expected=())
    expect_equal(actual=result.remaining, expected=())


def test_apply_fix_still_works_for_single_findings() -> None:
    """Keep the one-finding API available next to the runner."""
    catalog = load_default_catalog(registries=(default_registries()))
    expect_true(condition=callable(apply_fix))
    expect_true(condition=len(catalog.fixes) >= 1)


def test_unwritable_edit_does_not_block_other_fixes() -> None:
    """Apply what can be written back and report what cannot."""
    source = """\
    LIMIT = 3


    def f(a: int, b: int) -> None: ...


    f(
        1,  # one
        2,  # two
    )
    """
    result = _run(source=source, ceiling=FixSafety.guarded)
    expect_in(item="LIMIT: Final[int] = 3", container=result.source)
    expect_in(item="1,  # one", container=result.source)
    expect_equal(
        actual=[a.fix_key for a in result.applied],
        expected=["typing.add-final"],
    )
    expect_equal(
        actual=[(s.fix_key, s.reason) for s in result.skipped],
        expected=[
            (
                "calls.add-keywords",
                "cannot write back without changing formatting",
            ),
        ],
    )
    ast.parse(source=result.source)


def test_second_run_changes_nothing() -> None:
    """Reach a fixed point."""
    first = _run(source=SAMPLE, ceiling=FixSafety.guarded)
    second = _run(source=first.source, ceiling=FixSafety.guarded)
    expect_equal(actual=second.source, expected=first.source)
    expect_equal(actual=second.applied, expected=())


def test_stable_file_takes_one_round() -> None:
    """Stop as soon as a round applies nothing new."""
    calls: list[str] = []

    def counting(subject: Subject, facts: ModuleFacts) -> None:
        calls.append(subject.path)
        Appliers.table["typing.add-final"](subject, facts)

    result = _run(
        source="""\
LIMIT = 3
""",
        ceiling=FixSafety.proven,
        settings=FixSettings(
            ceiling=FixSafety.proven,
            appliers={"typing.add-final": counting},
        ),
    )
    expect_equal(actual=calls, expected=["LIMIT"])
    expect_equal(actual=len(result.applied), expected=1)


def _growing(subject: Subject, _facts: ModuleFacts) -> None:
    """Rename a constant so the same finding persists every round.

    Args:
        subject: Assignment subject.
        _facts: Unused resolved imports.

    """
    node = subject.node
    if isinstance(node, ast.Name):
        node.id = f"{node.id}A"


def test_max_rounds_bounds_the_loop() -> None:
    """Never run more passes than allowed."""
    for rounds in (1, 2, 3):
        result = _run(
            source="""\
A = 1
""",
            ceiling=FixSafety.proven,
            settings=FixSettings(
                ceiling=FixSafety.proven,
                appliers={"typing.add-final": _growing},
                max_rounds=rounds,
            ),
        )
        expect_equal(actual=len(result.applied), expected=rounds)
        expect_equal(
            actual=result.source,
            expected="A" * (rounds + 1)
            + """\
 = 1
""",
        )


def test_remaining_lists_unfixed_findings() -> None:
    """Report findings that have no applicable fix."""
    source = """\
def f(a: int) -> None:
    \"""Doc.\"""
"""
    result = _run(source=source, ceiling=FixSafety.guarded)
    expect_equal(
        actual=[f.rule_key for f in result.remaining],
        expected=["docs.missing-parameter"],
    )
    expect_equal(actual=result.applied, expected=())


def test_a_run_infers_once_per_distinct_text(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reuse inference between the check, the attempts and the re-match."""
    calls = {"convert": 0}
    original = CommentedModule.convert

    def counting(
        self: CommentedModule,
        *,
        stubs_path: Path,
        filename: str = "<memory>",
        apply: bool = False,
    ) -> GraphConversion:
        calls["convert"] += 1
        return original(
            self=self,
            stubs_path=stubs_path,
            filename=filename,
            apply=apply,
        )

    monkeypatch.setattr(target=CommentedModule, name="convert", value=counting)
    source = """\
    LIMIT = 3


    def f(a: int, b: int) -> None: ...


    f(
        1,  # one
        2,  # two
    )
    """
    expect_true(
        condition=len((_run(source=source, ceiling=FixSafety.guarded)).applied)
        > 0,
    )
    expect_true(condition=calls["convert"] <= Constants.max_inferences)
