"""Verify the TYP003 rule and its two gated fixes."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

from astart import parse
from astart.rules import (
    apply_fix,
    check,
    default_registries,
    load_default_catalog,
    verify_catalog,
)
from astart.rules.appliers import Appliers
from astart.rules.facts import collect_subjects, module_facts

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.rules import Finding
    from astart.rules.engine import CheckResult
    from astart.rules.facts import Applier, ModuleFacts
    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        rule (Final[str]): Grouped module constant.
        none_fix (Final[str]): Grouped module constant.
        inferred_fix (Final[str]): Grouped module constant.

    """

    rule: Final[str] = "typing.missing-annotation"
    none_fix: Final[str] = "typing.add-none-return"
    inferred_fix: Final[str] = "typing.add-inferred-annotation"


def _findings(*, source: str) -> list[Finding]:
    """Report TYP003 findings on a snippet.

    Args:
        source (str): Python source.

    Returns:
        list[Finding]: The findings of the missing-annotation rule.

    """
    registries: Registries = default_registries()
    result: CheckResult = check(
        source=dedent(text=source),
        filename="s.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
    )
    return [f for f in result.findings if f.rule_key == Constants.rule]


def _offers(*, source: str, path: str) -> list[str]:
    """List the fix keys offered for one finding.

    Args:
        source (str): Python source.
        path (str): Subject path of the finding.

    Returns:
        list[str]: The offered fix keys.

    """
    return [
        offer.fix_key
        for finding in _findings(source=source)
        if finding.subject_path == path
        for offer in finding.fix_offers
    ]


def _apply(*, source: str, path: str, fix_key: str) -> str:
    """Apply a fix to the TYP003 finding at a path.

    Args:
        source (str): Python source.
        path (str): Subject path of the finding.
        fix_key (str): Fix to apply.

    Returns:
        str: The resulting source.

    """
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    finding: Finding = next(
        f for f in _findings(source=source) if f.subject_path == path
    )
    return apply_fix(
        source=dedent(text=source),
        finding=finding,
        fix=catalog.fix(key=fix_key),
        registries=registries,
    )


def test_missing_annotation_reports_parameters_and_returns() -> None:
    """Report each unannotated parameter and each missing return."""
    paths: list[str] = [
        f.subject_path
        for f in _findings(
            source="""\
def f(a, b): ...
""",
        )
    ]
    expect_equal(actual=sorted(paths), expected=["f", "f.a", "f.b"])
    expect_equal(
        actual=_findings(
            source="""\
def f(a: int) -> int:
    return a
""",
        ),
        expected=[],
    )


def test_receivers_are_exempt_but_variadics_are_reported() -> None:
    """Skip self and cls; report *args and **kwargs."""
    paths: list[str] = [
        f.subject_path
        for f in _findings(
            source="""\
            class K:
                def m(self, *args, **kw) -> None: ...

                @classmethod
                def c(cls) -> None: ...
            """,
        )
    ]
    expect_equal(actual=sorted(paths), expected=["K.m.args", "K.m.kw"])


def test_none_return_fix_is_offered_only_when_provable() -> None:
    """Offer ``-> None`` for procedures, not for value-returning functions."""
    expect_in(
        item=Constants.none_fix,
        container=_offers(
            source="""\
def f():
    print(1)
""",
            path="f",
        ),
    )
    expect_equal(
        actual=_offers(
            source="""\
def g():
    return 1
""",
            path="g",
        ),
        expected=[Constants.inferred_fix],
    )
    expect_equal(
        actual=_offers(
            source="""\
def h():
    yield 1
""",
            path="h",
        ),
        expected=[],
    )


def test_inferred_fix_is_offered_only_for_accepted_hints() -> None:
    """Offer parameter hints that call sites corroborate."""
    source: str = """\
    def scale(x):
        return x * 2


    def greet(name):
        return "hi " + name


    scale(3)
    """
    expect_equal(
        actual=_offers(source=source, path="scale.x"),
        expected=[Constants.inferred_fix],
    )
    expect_not_in(
        item=Constants.inferred_fix,
        container=_offers(source=source, path="greet.name"),
    )


def test_apply_adds_none_return_in_place() -> None:
    """Keep comments and layout while adding ``-> None``."""
    fixed: str = _apply(
        source="""\
# lead
def f(a: int):  # trailing
    print(a)
""",
        path="f",
        fix_key=Constants.none_fix,
    )
    expect_equal(
        actual=fixed,
        expected="""\
# lead
def f(a: int) -> None:  # trailing
    print(a)
""",
    )


def test_apply_adds_parameter_annotation_in_place() -> None:
    """Write a corroborated hint without disturbing the file."""
    fixed: str = _apply(
        source="""\
def scale(x, k=2):  # c
    return x * k


scale(3)
""",
        path="scale.x",
        fix_key=Constants.inferred_fix,
    )
    expect_in(item="def scale(x: int, k=2):  # c", container=fixed)


def test_appliers_never_replace_existing_annotations() -> None:
    """Leave an annotated parameter alone."""
    module: CommentedModule = parse(
        source="""\
def f(a: str) -> int:
    return 1
""",
    )
    facts: ModuleFacts = module_facts(module=module)
    kinds: frozenset[str] = frozenset({"Parameter", "FunctionDef"})
    for subject in collect_subjects(module=module, kinds=kinds):
        for key in (Constants.none_fix, Constants.inferred_fix):
            applier: Applier = Appliers.table[key]
            applier(subject, facts)
    expect_equal(
        actual=module.unparse(),
        expected="""\
def f(a: str) -> int:
    return 1
""",
    )


def test_catalog_still_verifies() -> None:
    """Prove examples and idempotence for the whole default catalog."""
    registries: Registries = default_registries()
    catalog: Catalog = load_default_catalog(registries=registries)
    verify_catalog(catalog=catalog, registries=registries)
    expect_true(
        condition=Constants.rule in {rule.key for rule in catalog.rules},
    )
