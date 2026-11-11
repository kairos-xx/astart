"""TypeUnionDict normalization, resolver rejections and stream output."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from io import StringIO
from runpy import run_path
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.transforms import typeuniondict
from astart.transforms.typeuniondict import (
    TypeUnionDict,
    TypeUnionDictType,
    aprint,
)

from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_is,
    expect_not_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.capture import CaptureResult
    from astart.transforms.typeuniondict import TypeInput


@final
class _CustomClass:
    """Custom type registered through an explicit namespace."""


@final
class _AnotherClass:
    """Second custom type for union member checks."""


@final
class Constants:
    """Group module-level constants.

    Attributes:
        module_path (Final[Path]): Path of the module under test.
        namespace (Final[dict[str, type]]): Explicit custom-class registry.
        reserved_names (Final[tuple[str, ...]]): Names the resolver reserves.
        unsupported_expressions (Final[tuple[str, ...]]): Rejected syntax.
        invalid_special_forms (Final[tuple[str, ...]]): Rejected typing forms.

    """

    module_path: Final[Path] = (
        Paths.root / "src" / "astart" / "transforms" / "typeuniondict.py"
    )
    namespace: Final[dict[str, type]] = {
        "CustomClass": _CustomClass,
        "AnotherClass": _AnotherClass,
        "models.CustomClass": _CustomClass,
    }
    reserved_names: Final[tuple[str, ...]] = (
        "str",
        "int",
        "Mapping",
        "Union",
        "Optional",
        "Callable",
    )
    unsupported_expressions: Final[tuple[str, ...]] = (
        "str()",
        "int + str",
        "x()[int]",
        "[str, int]",
        "{'a': int}",
        "lambda x: x",
        "[x for x in range(10)]",
        "True",
        "typing.List[int]",
        "Foo[int]",
    )
    invalid_special_forms: Final[tuple[str, ...]] = (
        "Literal['pending', 'done']",
        "Annotated[str]",
        "Annotated[str, 'metadata']",
        "Required[str]",
        "Required[str, int]",
        "NotRequired[str]",
        "NotRequired[str, int]",
        "Optional[str, int]",
        "Union[()]",
        "Callable[str, int]",
    )


def _fields(
    *,
    values: dict[str, TypeInput] | TypeUnionDictType,
) -> TypeUnionDict:
    """Build a TypeUnionDict from an explicitly typed value mapping.

    Args:
        values (dict[str, TypeInput]): Field names to type expressions.

    Returns:
        TypeUnionDict: The normalized field dictionary.

    """
    return TypeUnionDict(values=values)


def test_runtime_values_pass_through_unchanged() -> None:
    """Runtime type objects are stored without re-resolution."""
    values: TypeUnionDictType = TypeUnionDict(
        values={
            "plain": str,
            "union": "str | int",
            "generic": "list[str]",
            "optional": "str | None",
        },
    )
    fields: TypeUnionDict = _fields(values=values)
    expect_is(actual=fields["plain"], expected=str)
    expect_equal(actual=fields["union"], expected=str | int)
    expect_equal(actual=fields["generic"], expected=list[str])
    expect_equal(actual=fields["optional"], expected=str | None)


def test_textual_annotations_resolve_to_runtime_types() -> None:
    """Registered names, generics and special forms parse from strings."""
    fields: TypeUnionDict = _fields(
        values={
            "name": "str",
            "pipe": "str | int | None",
            "optional": "Optional[int]",
            "union": "Union[str, int, None]",
            "single_union": "Union[str]",
            "list": "list[str]",
            "dict": "dict[str, int]",
            "nested": "list[str | int | None]",
            "variadic": "tuple[int, ...]",
            "mapping": "Mapping[str, int]",
            "qualified": "collections.abc.Mapping[str, int]",
            "sequence": "Sequence[str]",
            "iterable": "Iterable[str]",
            "callable": "Callable[[str], bool]",
            "callable_ellipsis": "Callable[..., str]",
            "callable_empty": "Callable[[], None]",
            "callable_nested": "Callable[[list[int]], dict[str, bool]]",
            "typing_union": "typing.Union[str, int]",
            "none": "None",
            "empty_tuple": "tuple[()]",
        },
    )
    expect_is(actual=fields["name"], expected=str)
    expect_equal(actual=fields["pipe"], expected=str | int | None)
    expect_equal(actual=fields["optional"], expected=int | None)
    expect_equal(actual=fields["union"], expected=str | int | None)
    expect_is(actual=fields["single_union"], expected=str)
    expect_equal(actual=fields["list"], expected=list[str])
    expect_equal(actual=fields["dict"], expected=dict[str, int])
    expect_equal(
        actual=fields["nested"],
        expected=list[str | int | None],
    )
    expect_equal(actual=fields["variadic"], expected=tuple[int, ...])
    expect_equal(
        actual=fields["mapping"],
        expected=Mapping[str, int],
    )
    expect_equal(
        actual=fields["qualified"],
        expected=Mapping[str, int],
    )
    expect_equal(actual=fields["sequence"], expected=Sequence[str])
    expect_equal(actual=fields["iterable"], expected=Iterable[str])
    expect_equal(
        actual=fields["callable"],
        expected=Callable[[str], bool],
    )
    expect_equal(
        actual=fields["callable_ellipsis"],
        expected=Callable[..., str],
    )
    expect_equal(
        actual=fields["callable_empty"],
        expected=Callable[[], type(None)],
    )
    expect_equal(
        actual=fields["callable_nested"],
        expected=Callable[[list[int]], dict[str, bool]],
    )
    expect_equal(actual=fields["typing_union"], expected=str | int)
    expect_is(actual=fields["none"], expected=type(None))
    expect_equal(actual=fields["empty_tuple"], expected=tuple[()])


def test_member_collections_normalize_each_entry() -> None:
    """Tuples, lists and mixed members each become one union."""
    fields: TypeUnionDict = _fields(
        values={
            "runtime": str,
            "text": "str",
            "tuple_members": (str, int, None),
            "list_members": ["str", "float", None],
            "mixed": (str, "int", None),
            "duplicates": ("str", "str", "int"),
            "single": "str",
            "single_none": None,
        },
    )
    expect_is(actual=fields["runtime"], expected=str)
    expect_is(actual=fields["text"], expected=str)
    expect_equal(actual=fields["tuple_members"], expected=str | int | None)
    expect_equal(actual=fields["list_members"], expected=str | float | None)
    expect_equal(actual=fields["mixed"], expected=str | int | None)
    expect_equal(actual=fields["duplicates"], expected=str | int)
    expect_is(actual=fields["single"], expected=str)
    expect_is(actual=fields["single_none"], expected=type(None))


def test_custom_namespace_resolves_registered_classes() -> None:
    """Explicit namespaces resolve custom and qualified names."""
    fields: TypeUnionDict = TypeUnionDict(
        values={
            "custom": "CustomClass",
            "custom_union": "CustomClass | AnotherClass",
            "custom_optional": "CustomClass | None",
            "qualified": "models.CustomClass",
            "nested": "dict[str, list[CustomClass | None]]",
        },
        namespace=Constants.namespace,
    )
    expect_is(actual=fields["custom"], expected=_CustomClass)
    expect_equal(
        actual=fields["custom_union"],
        expected=_CustomClass | _AnotherClass,
    )
    expect_equal(
        actual=fields["custom_optional"],
        expected=_CustomClass | None,
    )
    expect_is(actual=fields["qualified"], expected=_CustomClass)
    expect_equal(
        actual=fields["nested"],
        expected=dict[str, list[_CustomClass | None]],
    )


def test_constructor_discovers_caller_locals() -> None:
    """Without a namespace, caller locals and globals supply classes."""

    class LocalWidget:
        """Class visible only inside this function's locals."""

    values: dict[str, TypeInput] = {"widget": "LocalWidget | None"}
    fields: TypeUnionDict = TypeUnionDict(values=values)
    expect_equal(actual=fields["widget"], expected=LocalWidget | None)


@pytest.mark.parametrize("name", Constants.reserved_names)
def test_reserved_namespace_names_are_rejected(name: str) -> None:
    """Namespaces cannot shadow builtins, generics or special forms."""
    with pytest.raises(
        expected_exception=ValueError,
        match="Reserved type name",
    ):
        TypeUnionDict(
            values={"value": "int"},
            namespace={name: _CustomClass},
        )


@pytest.mark.parametrize("expression", Constants.unsupported_expressions)
def test_unsupported_expressions_are_rejected(expression: str) -> None:
    """Calls, arithmetic, containers and literals never evaluate."""
    with pytest.raises(
        expected_exception=(TypeError, ValueError, SyntaxError),
    ):
        TypeUnionDict.union(expression)


@pytest.mark.parametrize("expression", Constants.invalid_special_forms)
def test_invalid_special_forms_are_rejected(expression: str) -> None:
    """Malformed or unsupported typing constructs raise TypeError."""
    with pytest.raises(expected_exception=TypeError):
        TypeUnionDict.union(expression)


def test_unknown_names_raise_value_error() -> None:
    """Unregistered identifiers and modules fail name resolution."""
    with pytest.raises(
        expected_exception=ValueError,
        match="Unknown type name: UnknownClass",
    ):
        TypeUnionDict.union("UnknownClass")
    with pytest.raises(
        expected_exception=ValueError,
        match="Unknown type name: unknown.module.Type",
    ):
        TypeUnionDict.union("unknown.module.Type")


def test_union_requires_at_least_one_member() -> None:
    """Empty member sequences cannot form a union."""
    with pytest.raises(expected_exception=TypeError):
        TypeUnionDict.union()
    with pytest.raises(expected_exception=TypeError):
        _fields(values={"empty": []})
    with pytest.raises(expected_exception=TypeError):
        _fields(values={"empty": ()})


def test_union_static_method_combines_members() -> None:
    """The static helper normalizes runtime and textual members."""
    result: typeuniondict.TypeForm = TypeUnionDict.union(str, "int", None)
    expect_equal(actual=result, expected=str | int | None)
    single: typeuniondict.TypeForm = TypeUnionDict.union("str")
    expect_is(actual=single, expected=str)
    custom: typeuniondict.TypeForm = TypeUnionDict.union(
        "CustomClass",
        "AnotherClass",
        namespace=Constants.namespace,
    )
    expect_equal(
        actual=custom,
        expected=_CustomClass | _AnotherClass,
    )


def test_dict_interface_behaves_like_a_mapping() -> None:
    """TypeUnionDict remains a plain dict for lookup and copying."""
    fields: TypeUnionDict = _fields(values={"a": "int", "b": "str"})
    expect_equal(actual=len(fields), expected=2)
    expect_in(item="a", container=fields)
    expect_not_in(item="missing", container=fields)
    expect_is(actual=fields["a"], expected=int)
    expect_is(actual=fields["b"], expected=str)
    copied: dict[str, typeuniondict.TypeForm] = fields.copy()
    expect_equal(actual=copied, expected=fields)
    expect_true(condition=copied is not fields)
    empty: TypeUnionDict = _fields(values={})
    expect_equal(actual=len(empty), expected=0)


def test_aprimt_writes_to_stdout(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default output goes to the module's bound standard output."""
    stream: StringIO = StringIO()
    monkeypatch.setattr(target=typeuniondict, name="stdout", value=stream)
    aprint("hello", "world", sep="-", end="!", flush=True)
    expect_equal(actual=stream.getvalue(), expected="hello-world!")


def test_aprimt_writes_to_text_stream() -> None:
    """A TextIO stream receives the joined values without a newline."""
    stream: StringIO = StringIO()
    aprint("x", 1, file=stream, sep=",", end="")
    expect_equal(actual=stream.getvalue(), expected="x,1")


def test_aprimt_appends_to_file_paths(tmp_path: Path) -> None:
    """Path destinations honor the supplied open mode."""
    target: Path = tmp_path / "out.txt"
    aprint("one", file=target, mode="w")
    aprint("two", file=target, mode="a")
    expect_equal(
        actual=target.read_text(encoding="utf-8"),
        expected="one\ntwo\n",
    )


def test_main_demonstration_runs_clean(
    *,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Executing the module as __main__ passes its self-checks."""
    _ = run_path(
        path_name=str(object=Constants.module_path),
        run_name="__main__",
    )
    captured: CaptureResult[str] = capfd.readouterr()
    expect_in(
        item="TYPEUNIONDICT - EXTENSIVE DEMONSTRATION",
        container=captured.out,
    )
    tail: str = captured.out.rsplit("Overall demonstration:", maxsplit=1)[-1]
    expect_in(item="PASS", container=tail)
    expect_not_in(item="FAIL", container=tail)
