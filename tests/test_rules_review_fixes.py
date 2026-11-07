"""Regression tests for defects found by the whole-branch review."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from astart.rules import (
    Catalog,
    CatalogError,
    Finding,
    apply_fix,
    check,
    default_registries,
    load_default_catalog,
    verify_catalog,
)
from astart.rules.model import Example

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_not_equal,
    expect_true,
)

if TYPE_CHECKING:
    from astart.rules import CheckResult


def _catalog() -> Catalog:
    """Load the seed catalog.

    Returns:
        The validated seed catalog.

    """
    return load_default_catalog(registries=default_registries())


def _check(*, source: str) -> CheckResult:
    """Check a source with the seed catalog.

    Args:
        source: Python source.

    Returns:
        The check result.

    """
    return check(
        source=source,
        filename="s.py",
        catalog=_catalog(),
        registries=default_registries(),
    )


def _keys(*, source: str) -> list[str]:
    """List the rule keys reported on a source.

    Args:
        source: Python source.

    Returns:
        Rule keys in source order, ignoring the missing-annotation rule
        (these tests are about the other rules).

    """
    return [
        f.rule_key
        for f in _check(source=source).findings
        if f.rule_key != "typing.missing-annotation"
    ]


def _apply(*, source: str, rule_key: str, fix_key: str) -> str:
    """Apply a fix to the first finding of a rule that offers it.

    Args:
        source: Python source.
        rule_key: Rule whose finding is fixed.
        fix_key: Fix to apply.

    Returns:
        The resulting source.

    """
    finding: Finding = next(
        f
        for f in _check(source=source).findings
        if f.rule_key == rule_key and f.fix_offers
    )
    return apply_fix(
        source=source,
        finding=finding,
        fix=_catalog().fix(key=fix_key),
        registries=default_registries(),
    )


def test_shadowed_or_decorated_callee_is_not_reported() -> None:
    """Never invent keywords for a callable that is not the definition."""
    cases = (
        """\
def f(a, b): ...


def g(f):
    f(1, 2)
""",
        """\
def f(a, b): ...


f(1, 2)


def f(c, d, e): ...
""",
        dedent(
            text="""\
    def deco(fn):
        return fn


    @deco
    def f(a, b): ...


    f(1, 2)
    """,
        ),
    )
    for source in cases:
        expect_equal(
            actual=[k for k in _keys(source=source) if k.startswith("calls")],
            expected=[],
            message=source,
        )
    expect_equal(
        actual=_keys(
            source="""\
def f(a, b): ...


f(1, 2)
""",
        ),
        expected=["calls.missing-keyword"],
    )


def test_method_named_like_a_function_does_not_hide_the_function() -> None:
    """Class-level names do not shadow module functions."""
    source = dedent(
        text="""\
    def run(a, b): ...


    class K:
        def run(self) -> None: ...


    run(1, 2)
    """,
    )
    expect_equal(
        actual=_keys(source=source),
        expected=["calls.missing-keyword"],
    )


def test_apply_fix_survives_unpreservable_formatting() -> None:
    """Return parseable source instead of raising."""
    cases = (
        (
            """\
def f(a, b): ...


f(
    1,  # one
    2,  # two
)
""",
            "calls.missing-keyword",
            "calls.add-keywords",
        ),
        (
            """\
A = 1; B = 2
""",
            "typing.uppercase-global-not-final",
            "typing.add-final",
        ),
        (
            """\
A = 1
\x0c
B = 2
""",
            "typing.uppercase-global-not-final",
            "typing.add-final",
        ),
    )
    for source, rule_key, fix_key in cases:
        result = _apply(source=source, rule_key=rule_key, fix_key=fix_key)
        ast.parse(source=result)


def test_final_fix_is_not_offered_when_it_would_be_wrong() -> None:
    """Offer Final only for names bound once and spellable."""
    cases = (
        """\
A = 1
A = 2
""",
        """\
A = 1
A += 1
""",
        """\
A = 1


def f() -> None:
    global A
    A = 2
""",
        """\
if cond:
    A = 1
else:
    A = 2
""",
        """\
Final = 3
A = 1
""",
        """\
A = B = 1
""",
    )
    for source in cases:
        offers = [
            offer
            for finding in _check(source=source).findings
            for offer in finding.fix_offers
        ]
        expect_equal(actual=offers, expected=[], message=source)
    clean = _check(
        source="""\
A = 1
""",
    )
    expect_equal(actual=len(clean.findings[0].fix_offers), expected=1)


def test_check_never_raises_on_hostile_source() -> None:
    """Report problems as parse errors, whatever the input."""
    deep = (
        "A = "
        + "+".join(["1"] * 3000)
        + """\

"""
    )
    for source in (
        deep,
        """\
A = 1\x00
""",
    ):
        result = _check(source=source)
        expect_true(condition=hasattr(result, "parse_error"))


def test_rule_needs_one_bad_and_one_good_example() -> None:
    """Reject rules whose examples are one-sided."""
    catalog = _catalog()
    rule = catalog.rules[0]
    bare = replace(
        catalog,
        rules=(replace(rule, examples=()), *catalog.rules[1:]),
    )
    with pytest.raises(
        expected_exception=CatalogError,
        match="at least one triggering",
    ):
        verify_catalog(catalog=bare, registries=default_registries())
    one_sided = replace(
        catalog,
        rules=(
            replace(
                rule,
                examples=(
                    Example(
                        source="""\
x = 1
""",
                        triggers=False,
                    ),
                ),
            ),
            *catalog.rules[1:],
        ),
    )
    with pytest.raises(
        expected_exception=CatalogError,
        match="at least one triggering",
    ):
        verify_catalog(catalog=one_sided, registries=default_registries())
    verify_catalog(catalog=catalog, registries=default_registries())


def test_repeated_subjects_have_distinct_fingerprints() -> None:
    """Keep two same-name findings apart."""
    result = _check(
        source="""\
A = 1
A = 2
""",
    )
    prints = [f.fingerprint for f in result.findings]
    paths = [f.subject_path for f in result.findings]
    expect_equal(actual=paths, expected=["A", "A#2"])
    expect_equal(actual=len(set(prints)), expected=2)
    annotated = _check(
        source="""\
from typing import Any
x: Any = 1
x: Any = 2
""",
    )
    expect_not_equal(
        actual=annotated.findings[0].fingerprint,
        unexpected=annotated.findings[1].fingerprint,
    )


def test_string_annotations_are_inspected() -> None:
    """Find Any inside quoted annotations."""
    expect_equal(
        actual=_keys(
            source="""\
from typing import Any
x: 'Any' = 1
""",
        ),
        expected=["typing.no-any"],
    )
    expect_equal(
        actual=_keys(
            source="""\
from typing import Any
x: 'list[Any]' = []
""",
        ),
        expected=["typing.no-any"],
    )
    expect_equal(
        actual=_keys(
            source="""\
from typing import Any
x: 'not valid (' = 1
""",
        ),
        expected=[],
    )


def test_type_declarations_are_not_constants() -> None:
    """Do not ask for Final on TypeVar and friends."""
    for source in (
        """\
from typing import TypeVar

T = TypeVar('T')
""",
        """\
import typing as t

P = t.ParamSpec('P')
""",
        """\
from typing import NewType

USER = NewType('USER', int)
""",
    ):
        expect_equal(actual=_keys(source=source), expected=[], message=source)


def test_rules_package_has_no_object_or_any_annotations() -> None:
    """Keep the package within the repository's typing conventions."""
    package = Path(__file__).parent.parent / "src" / "astart" / "rules"
    offenders: list[str] = []
    for path in sorted(package.glob(pattern="*.py")):
        tree = ast.parse(source=path.read_text("utf-8"))
        for node in ast.walk(node=tree):
            annotation = getattr(node, "annotation", None) or getattr(
                node,
                "returns",
                None,
            )
            if annotation is None:
                continue
            offenders.extend(
                f"{path.name}:{inner.lineno}"
                for inner in ast.walk(node=annotation)
                if isinstance(inner, ast.Name)
                and inner.id in {"object", "Any"}
            )
    expect_equal(actual=offenders, expected=[])
    expect_in(item="x", container="xy")
