"""Recovery scoring tells contradictions from compatible differences."""

from __future__ import annotations

import pytest
from astart.rules.recovery import Context, module_context, relation

from tests.support.expectations import expect_equal


@pytest.mark.parametrize(
    ("written", "truth", "expected"),
    [
        ("str", "str | None", "narrower"),
        ("bool", "bool | None", "narrower"),
        ("int", "float", "narrower"),
        ("int", "float | int", "narrower"),
        ("bool", "int", "narrower"),
        ("NoReturn", "None", "narrower"),
        ("None", "Any", "narrower"),
        ("bool | None", "None", "looser"),
        ("None", "NoReturn", "looser"),
        ("None", "te.NoReturn", "looser"),
        ("NoReturn", "te.NoReturn", None),
        ("str", "int", "contradiction"),
        ("list[int]", "list[str]", "contradiction"),
        ("int | str", "int | bytes", "contradiction"),
        ("float", "int", "looser"),
        ("list[int]", "Sequence[int]", "narrower"),
        ("list[int]", "Iterable[int]", "narrower"),
        ("list[int]", "Sequence[float]", "narrower"),
        ("tuple[int, ...]", "Sequence[int]", "narrower"),
        ("dict[str, int]", "Mapping[str, int]", "narrower"),
        ("dict[str, int]", "Mapping[str, float]", "narrower"),
        ("dict[str, int]", "MutableMapping[str, int]", "narrower"),
        ("Sequence[int]", "list[int]", "looser"),
        ("list[str]", "Sequence[int]", "contradiction"),
        ("dict[int, int]", "Mapping[str, int]", "contradiction"),
        ("dict[str, int]", "MutableMapping[str, object]", "narrower"),
        ("dict[str, int]", "dict[str, object]", "narrower"),
        ("set[int]", "Sequence[int]", "contradiction"),
        ("list[int]", "MutableSequence[object]", "narrower"),
        ("dict[str, int]", "dict[str, str]", "contradiction"),
        ("list[int]", "Sequence[object]", "narrower"),
        (
            "list[dict[str, int]]",
            "Sequence[MutableMapping[str, object]]",
            "narrower",
        ),
        ("dict[str, int]", "Mapping[str, object]", "narrower"),
        ("Callable[[int], int]", "Callable[[object], object]", "narrower"),
        ("list[Any]", "list[dict[str, Any]]", "looser"),
        ("dict[str, Any]", "dict[str, int]", "looser"),
        ("Iterator[int]", "Iterable[int]", "narrower"),
        ("int", "Iterable[int]", "contradiction"),
        ("str", "Sized", "narrower"),
        (
            "tuple[str, None] | tuple[str, OSError]",
            'tuple[Literal["ok"], OSError | None]',
            "looser",
        ),
        (
            "tuple[int | str, bytes]",
            "tuple[int, bytes] | tuple[str, bytes]",
            None,
        ),
        ("list[int | str]", "list[int] | list[str]", "looser"),
        ("Callable[[], int]", "Callable[..., int]", "narrower"),
        ("Generator[int]", "Iterator[int]", "narrower"),
        ("Generator[int]", "Iterable[int]", "narrower"),
        ("AsyncGenerator[int]", "AsyncIterator[int]", "narrower"),
        ("Generator[int, None, None]", "Generator[int]", None),
        ("AsyncGenerator[int, None]", "AsyncGenerator[int]", None),
        (
            "Generator[int]",
            "Generator[int, int | str | None, int]",
            "narrower",
        ),
        ("Sequence[int]", "Iterable[int]", "narrower"),
        ("Iterable[int]", "Sequence[int]", "looser"),
        ("Sequence[int | None]", "Iterable", "narrower"),
        ("Iterable", "Sequence[int | None]", "looser"),
        ("Iterable[int | None]", "Sequence[int | None]", "looser"),
        ("Collection[int]", "Iterable[int]", "narrower"),
        ("Iterable[int]", "Collection[int]", "looser"),
        ("MutableSequence[int]", "Sequence[int]", "narrower"),
        ("Sequence[int]", "MutableSequence[int]", "looser"),
        ("MutableMapping[str, int]", "Mapping[str, int]", "narrower"),
        ("Mapping[str, int]", "MutableMapping[str, int]", "looser"),
        ("AbstractSet[int]", "Iterable[int]", "narrower"),
        ("MutableSet[int]", "Set[int]", "looser"),
        ("Set[int]", "MutableSet[int]", "narrower"),
        ("KeysView[str]", "Iterable[str]", "narrower"),
        ("ValuesView[int]", "Collection[int]", "narrower"),
        ("Mapping[str, int]", "Iterable[str]", "narrower"),
        ("Mapping[str, int]", "Iterable[int]", "contradiction"),
        ("Mapping[str, int]", "Collection[str]", "narrower"),
        ("Iterable", "list[int]", "looser"),
        ("Iterable[int]", "list[int]", "looser"),
        ("T", "int", "unresolved"),
        ("int", "T", "unresolved"),
        ("T", "T", None),
        ("list[T]", "list[int]", "unresolved"),
        ("dict[str, T]", "dict[str, int]", "unresolved"),
        ("list[int]", "list[T]", "unresolved"),
        ("tuple[T, ...]", "tuple[int, ...]", "unresolved"),
    ],
)
def test_relation(*, written: str, truth: str, expected: str | None) -> None:
    """Check how a written annotation relates to the original.

    Args:
        written (str): What the fixer wrote.
        truth (str): The original annotation.
        expected (str | None): ``None`` for equal, else the relation.

    """
    expect_equal(
        actual=relation(written=written, truth=truth),
        expected=expected,
    )


def test_aliases_of_the_original_module_are_unfolded() -> None:
    """Check ``StyleType = Union[str, Style]`` makes ``str`` narrower."""
    context: Context = module_context(
        source="""\
StyleType = Union[str, Style]
class Style: ...
""",
    )
    expect_equal(
        actual=relation(written="str", truth="StyleType", context=context),
        expected="narrower",
    )
    expect_equal(
        actual=relation(written="int", truth="StyleType", context=context),
        expected="contradiction",
    )


def test_self_is_narrower_than_its_class() -> None:
    """Check ``-> Self`` against the original ``-> Element``."""
    context: Context = module_context(
        source="""\
class Element: ...
""",
    )
    expect_equal(
        actual=relation(written="Self", truth="Element", context=context),
        expected="narrower",
    )
    expect_equal(
        actual=relation(written="Self", truth="int", context=context),
        expected="contradiction",
    )


def test_literal_of_strings_fits_under_str() -> None:
    """Check ``Literal`` arms against a plain ``str``."""
    expect_equal(
        actual=relation(written="str", truth='Literal["a", "b"]'),
        expected="looser",
    )


def test_names_imported_from_elsewhere_are_unresolved() -> None:
    """Check that an alias this module does not define cannot be judged."""
    expect_equal(
        actual=relation(written="str", truth="StyleType"),
        expected="unresolved",
    )


def test_a_type_guard_is_a_bool() -> None:
    """Check that ``bool`` is looser than ``TypeGuard[...]``."""
    expect_equal(
        actual=relation(written="bool", truth="TypeGuard[int]"),
        expected="looser",
    )


def test_a_type_variable_of_the_module_accepts_any_element() -> None:
    """Check that ``Sequence[T]`` takes ``list[int]`` for a TypeVar ``T``."""
    context: Context = module_context(
        source="""\
from typing import TypeVar
T = TypeVar('T')
""",
    )
    expect_equal(
        actual=relation(
            written="list[int]",
            truth="Sequence[T]",
            context=context,
        ),
        expected="narrower",
    )


def test_a_class_with_an_imported_base_cannot_be_judged_against_abcs() -> None:
    """Check ``ByteStream(Imported)`` vs ``Iterable[bytes]`` is unresolved."""
    context: Context = module_context(
        source=(
            "from elsewhere import Base\n"
            "class ByteStream(Base):\n    pass\n"
            "class Local:\n    pass\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="AsyncIterable[bytes] | Iterable[bytes]",
            context=context,
        ),
        expected="unresolved",
    )
    expect_equal(
        actual=relation(
            written="Local",
            truth="Iterable[bytes]",
            context=context,
        ),
        expected="contradiction",
    )
    expect_equal(
        actual=relation(written="ByteStream", truth="int", context=context),
        expected="contradiction",
    )


def test_an_imported_name_cannot_be_judged_against_abcs() -> None:
    """Check that a name the module only imports is unresolved, not wrong."""
    context: Context = module_context(
        source="""\
from elsewhere import ByteStream
""",
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="Iterable[bytes]",
            context=context,
        ),
        expected="unresolved",
    )


def test_protocols_compare_by_members_not_names() -> None:
    """Check ``SupportsVector`` and ``_Vec`` with equal members are equal."""
    context: Context = module_context(
        source=(
            "from typing import Protocol\n"
            "class SupportsVector(Protocol):\n"
            "    x: int\n"
            "    y: int\n"
            "    def __add__(\n"
            "        self, other: SupportsVector\n"
            "    ) -> SupportsVector: ...\n"
            "class _Vec(Protocol):\n"
            "    x: int\n"
            "    y: int\n"
            "    def __add__(self, other: _Vec) -> _Vec: ...\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="SupportsVector",
            truth="_Vec",
            context=context,
        ),
        expected=None,
    )


def test_a_class_covering_a_protocol_is_narrower() -> None:
    """Check ``Vector`` satisfies ``SupportsVector`` structurally."""
    context: Context = module_context(
        source=(
            "from typing import Protocol\n"
            "class SupportsVector(Protocol):\n"
            "    x: int\n"
            "    y: int\n"
            "class Vector:\n"
            "    def __init__(self, x: int, y: int) -> None:\n"
            "        self.x: int = x\n"
            "        self.y: int = y\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="Vector",
            truth="SupportsVector",
            context=context,
        ),
        expected="narrower",
    )
    expect_equal(
        actual=relation(
            written="int",
            truth="SupportsVector",
            context=context,
        ),
        expected="contradiction",
    )


def test_a_written_protocol_against_a_builtin_is_looser() -> None:
    """Check a synthesized ``Protocol`` reads as broader than ``str``."""
    context: Context = module_context(
        source=(
            "from typing import Protocol\n"
            "class ValueProtocol(Protocol):\n"
            "    def upper(self) -> str: ...\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="ValueProtocol",
            truth="str",
            context=context,
        ),
        expected="looser",
    )


def test_a_callable_protocol_matches_a_callable_annotation() -> None:
    """Check a ``__call__`` protocol compares equal to ``Callable[...]``."""
    context: Context = module_context(
        source=(
            "from typing import Protocol\n"
            "class Func(Protocol):\n"
            "    def __call__(self, arg0: object) -> object: ...\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="Func",
            truth="Callable[[object], object]",
            context=context,
        ),
        expected=None,
    )
    expect_equal(
        actual=relation(
            written="Func",
            truth="Callable[[int], str]",
            context=context,
        ),
        expected="looser",
    )


def test_a_class_satisfying_a_typing_protocol_is_narrower() -> None:
    """Check ``__iter__``/``__aiter__`` members satisfy ``Iterable`` arms."""
    context: Context = module_context(
        source=(
            "class ByteStream:\n"
            "    def __iter__(self) -> Iterator[bytes]: ...\n"
            "    async def __aiter__(self) -> AsyncIterator[bytes]: ...\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="AsyncIterable[bytes] | Iterable[bytes]",
            context=context,
        ),
        expected="narrower",
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="Iterable[bytes]",
            context=context,
        ),
        expected="narrower",
    )
    expect_equal(
        actual=relation(
            written="ByteStream",
            truth="Iterable[int]",
            context=context,
        ),
        expected="contradiction",
    )


def test_an_alias_inside_a_generic_argument_is_unfolded() -> None:
    """Check ``tuple[Alias, X]`` compares the alias's target."""
    context: Context = module_context(
        source=(
            """\
from typing import Literal
Outcome = Literal["ok", "lost"]
"""
        ),
    )
    expect_equal(
        actual=relation(
            written="tuple[Outcome, OSError]",
            truth="tuple[str, OSError]",
            context=context,
        ),
        expected="narrower",
    )


def test_a_written_import_cannot_be_judged_a_contradiction() -> None:
    """Check an unresolvable written name reads ``unresolved``."""
    context: Context = module_context(
        source="""\
from elsewhere import Session
""",
    )
    expect_equal(
        actual=relation(
            written="Session",
            truth="dict[str, Any]",
            context=context,
        ),
        expected="unresolved",
    )


def test_pep695_aliases_compare_by_meaning_inside_containers() -> None:
    """Recognise modern aliases without flattening generic parameters."""
    context: Context = module_context(
        source=(
            "type IntDict = dict[str, int]\n"
            "type Pair = tuple[IntDict, IntDict]\n"
            "type Generic[T] = list[T]\n"
        ),
    )
    expect_equal(
        actual=relation(
            written="tuple[dict[str, int], dict[str, int]]",
            truth="Pair",
            context=context,
        ),
        expected=None,
    )
    expect_equal(
        actual=relation(
            written="dict[int, str]",
            truth="IntDict",
            context=context,
        ),
        expected="contradiction",
    )
    expect_equal(actual=context.alias_parameters["Generic"], expected=("T",))
    expect_equal(
        actual=relation(
            written="list[int]",
            truth="Generic[int]",
            context=context,
        ),
        expected=None,
    )
    expect_equal(
        actual=relation(
            written="list[int]",
            truth="Generic[str]",
            context=context,
        ),
        expected="contradiction",
    )
