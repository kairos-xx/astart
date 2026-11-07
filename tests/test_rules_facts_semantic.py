"""Verify the call and docstring facts of the reference engine."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from astart import parse
from astart.rules.facts import Registry, collect_subjects, module_facts

from tests.expectations import expect_equal, expect_false, expect_true

if TYPE_CHECKING:
    from astart.rules.facts import ModuleFacts, Subject
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.predicate import FactValue


def _subject(
    *,
    source: str,
    kind: str,
    path: str,
) -> tuple[Subject, ModuleFacts]:
    """Find one subject of a snippet.

    Args:
        source: Python source.
        kind: Subject kind.
        path: Qualified path; repeated calls end in ``#2``, ``#3``.

    Returns:
        The subject and the module facts.

    """
    module = parse(source=dedent(text=source), filename="s.py")
    facts: ModuleFacts = module_facts(module=module)
    found: list[Subject] = [
        subject
        for subject in collect_subjects(module=module, kinds=frozenset({kind}))
        if subject.path == path
    ]
    return found[0], facts


def _fact(*, source: str, kind: str, path: str, fact: str) -> FactValue:
    """Compute one fact for one subject.

    Args:
        source: Python source.
        kind: Subject kind.
        path: Qualified path of the subject.
        fact: Fact name.

    Returns:
        The fact value.

    """
    subject, facts = _subject(source=source, kind=kind, path=path)
    return Registry.providers[fact](subject, facts)


def _evidence(*, source: str, kind: str, path: str, slot: str) -> JsonValue:
    """Compute one evidence slot for one subject.

    Args:
        source: Python source.
        kind: Subject kind.
        path: Qualified path of the subject.
        slot: Evidence slot name.

    Returns:
        The slot value.

    """
    subject, facts = _subject(source=source, kind=kind, path=path)
    return Registry.evidence[slot](subject, facts)


def test_candidates_count_only_keyword_capable_parameters() -> None:
    """Skip positional-only parameters and calls absorbed by *args."""
    source = """\
    def f(a, /, b, *args, c=1): ...
    def g(x, y): ...
    f(1, 2, 3)
    f(1, 2)
    g(1, y=2)
    g(1, 2)
    """
    count = "call.positional_keyword_candidates"
    expect_equal(
        actual=(_fact(source=source, kind="Call", path="f", fact=count)),
        expected=0,
    )
    expect_equal(
        actual=_fact(source=source, kind="Call", path="f#2", fact=count),
        expected=1,
    )
    expect_equal(
        actual=_evidence(
            source=source,
            kind="Call",
            path="f#2",
            slot="parameters",
        ),
        expected=["b"],
    )
    expect_equal(
        actual=_evidence(source=source, kind="Call", path="f", slot="callee"),
        expected="f",
    )
    expect_equal(
        actual=_fact(source=source, kind="Call", path="g", fact=count),
        expected=1,
    )
    expect_equal(
        actual=_fact(source=source, kind="Call", path="g#2", fact=count),
        expected=2,
    )


def test_unresolved_callee_is_not_resolved() -> None:
    """Treat builtins and unknown names as unresolved."""
    source = """\
    def f(a): ...
    f(1)
    print(1)
    unknown(1)
    """
    resolved = "call.is_resolved_in_module"
    expect_true(
        condition=bool(
            _fact(source=source, kind="Call", path="f", fact=resolved),
        ),
    )
    for name in ("print", "unknown"):
        expect_false(
            condition=bool(
                _fact(source=source, kind="Call", path=name, fact=resolved),
            ),
        )
        expect_equal(
            actual=_fact(
                source=source,
                kind="Call",
                path=name,
                fact="call.positional_keyword_candidates",
            ),
            expected=0,
        )


def test_undocumented_parameters_ignore_self_and_cls() -> None:
    """Count only parameters missing from the Args section."""
    source = '''\
    class K:
        def m(self, x, y):
            """Do.

            Args:
                x: documented.
            """

        @classmethod
        def c(cls, z):
            """Do.

            Args:
                z: documented.
            """
    '''
    fact = "function.undocumented_parameter_count"
    expect_equal(
        actual=_fact(source=source, kind="FunctionDef", path="K.m", fact=fact),
        expected=1,
    )
    expect_equal(
        actual=_evidence(
            source=source,
            kind="FunctionDef",
            path="K.m",
            slot="parameters",
        ),
        expected=["y"],
    )
    expect_equal(
        actual=_evidence(
            source=source,
            kind="FunctionDef",
            path="K.m",
            slot="function",
        ),
        expected="K.m",
    )
    expect_equal(
        actual=_fact(source=source, kind="FunctionDef", path="K.c", fact=fact),
        expected=0,
    )


def test_starred_parameters_match_their_entries() -> None:
    """Accept *args and **kwargs documented with or without stars."""
    source = '''\
    def f(a, *args, **kwargs):
        """Do.

        Args:
            a: first.
            *args: extra.
            **kwargs: more.
        """

    def g(a, *args, **kwargs):
        """Do.

        Args:
            a: first.
            args: extra.
        """
    '''
    fact = "function.undocumented_parameter_count"
    expect_equal(
        actual=_fact(source=source, kind="FunctionDef", path="f", fact=fact),
        expected=0,
    )
    expect_equal(
        actual=_fact(source=source, kind="FunctionDef", path="g", fact=fact),
        expected=1,
    )


def test_function_without_docstring_has_no_docstring_fact() -> None:
    """Report no docstring and no undocumented parameters."""
    source = """\
    def f(a): ...
    """
    expect_false(
        condition=bool(
            _fact(
                source=source,
                kind="FunctionDef",
                path="f",
                fact="function.has_docstring",
            ),
        ),
    )
    expect_equal(
        actual=_fact(
            source=source,
            kind="FunctionDef",
            path="f",
            fact="function.undocumented_parameter_count",
        ),
        expected=0,
    )
