"""Source-backed comparison of documentation and generated declarations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.compare.conversion_structure import (
    artifacts,
    compare_artifacts,
    structure_json,
    structure_markdown,
)
from tests.support.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from scripts.compare.conversion_structure import Artifact, Difference


def test_missing_changed_and_extra_artifacts() -> None:
    """Retain both contracts and locations for each structural difference."""
    expected: str = '''
from typing import Protocol
type IntList = list[int]
class Readable(Protocol):
    """Readable reference."""
    def read(self) -> bytes: ...
def run(value: IntList):
    """Run.

    Args:
        value (IntList): TODO.
    """
'''
    actual: str = '''
from typing import Protocol
type IntList = list[str]
type Extra = set[int]
class Readable(Protocol):
    """Readable output."""
    def read(self) -> str: ...
def run(value: IntList):
    pass
'''
    differences: list[Difference] = compare_artifacts(
        typed=expected,
        converted=actual,
    )
    verdicts: dict[tuple[str, str], str] = {
        (item.kind, item.key): item.verdict for item in differences
    }
    expect_equal(
        actual=verdicts["type_aliases", "IntList"],
        expected="changed",
    )
    expect_equal(actual=verdicts["type_aliases", "Extra"], expected="extra")
    expect_equal(actual=verdicts["protocols", "Readable"], expected="changed")
    expect_equal(actual=verdicts["docstrings", "run"], expected="missing")
    markdown: str = "\n".join(
        structure_markdown(
            differences=differences,
            typed_link="reference.py",
            converted_link="output.py",
        ),
    )
    expect_in(item="reference.py#L", container=markdown)
    expect_in(item="output.py#L", container=markdown)
    expect_in(item="value (IntList): TODO.", container=markdown)
    expect_true(condition="items" in structure_json(differences=differences))


def test_legacy_alias_and_renamed_declaration_are_distinguished() -> None:
    """Legacy syntax and naming differences do not erase missing references."""
    differences: list[Difference] = compare_artifacts(
        typed="""\
type IntList = list[int]
""",
        converted=(
            """\
from typing import TypeAlias
Other: TypeAlias = list[int]
"""
        ),
    )
    alias: Difference = next(
        item for item in differences if item.kind == "type_aliases"
    )
    expect_equal(actual=alias.verdict, expected="equivalent")
    expect_true(condition=alias.actual is not None)
    expect_in(item="not proven", container=alias.explanation)


def test_nested_and_overloaded_docstrings_have_distinct_identities() -> None:
    """Repeated definitions and class scopes retain independent evidence."""
    found: list[Artifact] = artifacts(
        source='''
def run(value: int):
    """First."""
def run(value: str):
    """Second."""
class Box:
    def run(self):
        """Nested."""
''',
    )
    expect_equal(
        actual=[item.key for item in found if item.kind == "docstrings"],
        expected=["run", "run#definition:2", "Box.run"],
    )


def test_documentation_whitespace_and_protocol_prose_are_separate() -> None:
    """Protocol contracts are not marked changed solely by method prose."""
    first: str = '''from typing import Protocol
class Reader(Protocol):
    def read(self) -> bytes:
        """Read bytes."""
        ...
'''
    second: str = first.replace("Read bytes.", "TODO.")
    differences: list[Difference] = compare_artifacts(
        typed=first,
        converted=second,
    )
    expect_equal(
        actual=next(
            item.verdict for item in differences if item.kind == "protocols"
        ),
        expected="exact",
    )
    expect_equal(
        actual=next(
            item.verdict for item in differences if item.kind == "docstrings"
        ),
        expected="changed",
    )


def test_native_alias_reads_and_implicit_alias_syntax() -> None:
    """Reuse alias proof and count resolved references on the shared AST."""
    source: str = """\
type Numbers = list[int]
def use(x: Numbers) -> Numbers: return x
"""
    found: list[Artifact] = artifacts(source=source)
    usage: Artifact = next(
        item for item in found if item.kind == "declaration_uses"
    )
    expect_equal(actual=usage.shape, expected="2")
    differences: list[Difference] = compare_artifacts(
        typed=source,
        converted=source.replace("type Numbers", "Numbers"),
    )
    expect_equal(
        actual=next(
            item.verdict for item in differences if item.kind == "type_aliases"
        ),
        expected="equivalent",
    )


def test_generic_protocol_alias_and_docstring_field_evidence() -> None:
    """Recognize generic Protocol bases and explain missing result fields."""
    source: str = '''from typing import Protocol as P
class Reader[T](P):
    def read(self) -> T:
        """Read.

        Returns:
            T: TODO.
        """
        ...
'''
    found: list[Artifact] = artifacts(source=source)
    expect_true(condition=any(item.kind == "protocols" for item in found))
    expect_true(condition=any(item.key == "Reader.T" for item in found))
    differences: list[Difference] = compare_artifacts(
        typed=source,
        converted=source.replace(
            """\
        Returns:
            T: TODO.
""",
            "",
        ),
    )
    changed: Difference = next(
        item for item in differences if item.kind == "docstrings"
    )
    expect_in(item="returns.0", container=changed.explanation)
