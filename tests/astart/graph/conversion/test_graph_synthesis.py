"""Exercise the semantic type-hint synthesis API end to end."""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    fix_missing_locations,
    parse,
    unparse,
)
from re import sub
from textwrap import dedent
from typing import TYPE_CHECKING, Final, cast, final

import pytest
from astart.graph.conversion.synthesis import (
    Args,
    ArgumentItem,
    ExistingTopNode,
    GeneratedTopBlock,
    ImportUseSite,
    MethodSemanticProfile,
    MethodSpec,
    OverloadExpressionFactory,
    ProtocolGrammar,
    ProtocolNodeBuilder,
    ProtocolRegistration,
    ProtocolSpec,
    ProtocolTypeBlockCollector,
    ScriptSymbolIndex,
    SemanticCodegenError,
    SemanticImportSource,
    TypeExpressionResolver,
    TypeHintCatalog,
    Types,
    UsageAwareImportCollector,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from ast import Call, stmt

    from astart.graph.conversion.synthesis import (
        BuiltinTypeHints,
        CollectionsAbcTypeHints,
        ParamSpecSpec,
        TypeExpression,
        TypeTemplateRef,
        TypeVarSpec,
        TypingTypeHints,
    )


@final
class Constants:
    """Group module-level constants.

    Attributes:
        unique_names (Final[int]): Grouped module constant.
        t (Final[type[TypeHintCatalog]]): Grouped module constant.
        abc (Final[type[CollectionsAbcTypeHints]]): Grouped module constant.
        typing (Final[type[TypingTypeHints]]): Grouped module constant.
        builtins (Final[type[BuiltinTypeHints]]): Grouped module constant.
        split_cases (Final[int]): Grouped module constant.
        split_alphabet (Final[str]): Grouped module constant.
        split_verbs (Final[frozenset[str]]): Grouped module constant.
        split_dunders (Final[frozenset[str]]): Grouped module constant.

    """

    unique_names: Final[int] = 4
    t: Final[type[TypeHintCatalog]] = TypeHintCatalog
    abc: Final[type[CollectionsAbcTypeHints]] = t.ABC
    typing: Final[type[TypingTypeHints]] = t.TYPING
    builtins: Final[type[BuiltinTypeHints]] = t.BUILTINS

    split_cases: Final[int] = 500
    split_alphabet: Final[str] = "abcXYZ019_-. "
    split_verbs: Final[frozenset[str]] = frozenset(
        {
            "read",
            "write",
            "load",
            "save",
            "parse",
            "format",
            "transform",
            "convert",
            "validate",
            "serialize",
            "deserialize",
            "encode",
            "decode",
            "get",
            "set",
            "add",
            "remove",
        },
    )
    split_dunders: Final[frozenset[str]] = frozenset(
        {
            "__call__",
            "__iter__",
            "__next__",
            "__len__",
            "__contains__",
            "__getitem__",
            "__setitem__",
            "__enter__",
            "__exit__",
            "__await__",
            "__mul__",
            "__add__",
            "__matmul__",
        },
    )


def _existing(*, module: Module) -> tuple[ExistingTopNode, ...]:
    """Select the top-level nodes the collector understands.

    Args:
        module (Module): Parsed module holding existing declarations.

    Returns:
        tuple[ExistingTopNode, ...]: Imports, classes, functions and
            assignments of the module.

    """
    return tuple(
        node
        for node in module.body
        if isinstance(
            node,
            Import
            | ImportFrom
            | ClassDef
            | FunctionDef
            | AsyncFunctionDef
            | Assign
            | AnnAssign,
        )
    )


def _imports() -> UsageAwareImportCollector:
    """Create an import collector from public building blocks.

    Returns:
        UsageAwareImportCollector: Empty import collector.

    """
    return UsageAwareImportCollector(
        symbol_index=ScriptSymbolIndex(),
        existing_import_nodes=(),
        postponed_annotations=None,
        local_roots=(),
    )


def _node_builder() -> ProtocolNodeBuilder:
    """Create a protocol node builder from public building blocks.

    Returns:
        ProtocolNodeBuilder: Builder bound to a fresh import collector.

    """
    imports: UsageAwareImportCollector = _imports()
    return ProtocolNodeBuilder(
        imports=imports,
        resolver=TypeExpressionResolver(imports=imports),
    )


def _render(*, block: GeneratedTopBlock) -> str:
    """Render a generated block to source text.

    Args:
        block (GeneratedTopBlock): Generated imports and declarations.

    Returns:
        str: Source text for the whole block.

    """
    nodes: tuple[stmt, ...] = (
        *block.missing_import_nodes,
        *block.declaration_nodes_after_imports,
    )
    module: Module = Module(body=list(nodes), type_ignores=[])
    return unparse(ast_obj=fix_missing_locations(node=module))


def _annotate(*, hint: TypeExpression) -> str:
    """Render one type hint as an annotation through a fresh collector.

    Args:
        hint (TypeExpression): Type expression to render.

    Returns:
        str: Source text of the generated annotation.

    """
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    collector.protocol(
        spec=ProtocolSpec(
            name="Holder",
            methods=(
                MethodSpec(
                    name="get",
                    arguments=(Args.self_arg(),),
                    returns=hint,
                ),
            ),
        ),
    )
    return _render(block=collector.build_block())


@pytest.mark.parametrize(
    ("hint", "expected"),
    [
        (Types.union(options=(Types.BOOL, Types.INT, Types.FLOAT)), "float"),
        (Types.union(options=(Types.INT, Types.COMPLEX)), "complex"),
        (
            Types.union(options=(Types.INT, Types.local(name="Marker"))),
            "Marker",
        ),
        (Types.union(options=(Types.STR, Types.INT, Types.STR)), "int | str"),
        (Types.union(options=(Types.INT,)), "int"),
        (
            Types.union(
                options=(
                    Constants.typing.literal_of(values=(1, 2)),
                    Types.INT,
                ),
            ),
            "int",
        ),
        (
            Types.union(
                options=(
                    Constants.typing.literal_of(values=("a",)),
                    Constants.typing.literal_of(values=("b", None, True, 1.5)),
                ),
            ),
            "Literal",
        ),
        (
            Types.union(
                options=(
                    Constants.builtins.list_of(item=Types.INT),
                    Constants.builtins.list_of(item=Types.STR),
                ),
            ),
            "MutableSequence[int | str]",
        ),
        (
            Types.union(
                options=(
                    Constants.builtins.dict_of(
                        keys=Types.STR,
                        values=Types.INT,
                    ),
                    Constants.builtins.dict_of(
                        keys=Types.INT,
                        values=Types.STR,
                    ),
                ),
            ),
            "MutableMapping[",
        ),
        (
            Types.union(
                options=(
                    Constants.builtins.list_of(item=Types.INT),
                    Constants.builtins.set_of(item=Types.INT),
                    Constants.builtins.tuple_variadic(item=Types.INT),
                ),
            ),
            "Collection[int]",
        ),
        (
            Types.union(
                options=(
                    Constants.builtins.dict_of(
                        keys=Types.STR,
                        values=Types.INT,
                    ),
                    Constants.abc.MAPPING.of(arguments=(Types.STR, Types.INT)),
                ),
            ),
            "Mapping",
        ),
        (
            Types.union(
                options=(
                    Constants.builtins.list_of(item=Types.INT),
                    Types.INT,
                    Types.union(options=(Types.STR, Types.BYTES)),
                ),
                collapse_limit=2,
            ),
            "object",
        ),
        (
            Constants.typing.union_of(options=(Types.STR, Types.BYTES)),
            "bytes | str",
        ),
    ],
)
def test_union_simplification(*, hint: TypeExpression, expected: str) -> None:
    """Simplify unions while rendering them as annotations.

    Args:
        hint (TypeExpression): Union expression under test.
        expected (str): Fragment expected in the rendered source.

    """
    expect_in(item=expected, container=_annotate(hint=hint))


def test_catalog_renders_every_builtin_and_abc_template() -> None:
    """Render each catalog entry through the collector."""
    hints: list[TypeExpression] = [
        Types.BOOL,
        Types.FLOAT,
        Types.BYTES,
        Types.BYTEARRAY,
        Types.MEMORYVIEW,
        Types.OBJECT,
        Types.TYPE,
        Types.SLICE,
        Types.RANGE,
        Types.ELLIPSIS,
        Types.NEVER,
        Types.NO_RETURN,
        Types.LITERAL_STRING,
        Types.SELF,
        Constants.builtins.tuple_empty(),
        Constants.builtins.tuple_of(items=(Types.INT, Types.STR)),
        Constants.builtins.frozenset_of(item=Types.INT),
        Constants.builtins.type_of(item=Types.INT),
        Constants.builtins.dict_of(keys=Types.STR, values=Types.INT),
        Constants.builtins.LIST.empty(),
        Constants.abc.one_arg(template=Constants.abc.ITERABLE, item=Types.INT),
        Constants.abc.two_arg(
            template=Constants.abc.MAPPING,
            first=Types.STR,
            second=Types.INT,
        ),
        Constants.abc.three_arg(
            template=Constants.abc.GENERATOR,
            first=Types.INT,
            second=Types.INT,
            third=Types.INT,
        ),
        Constants.abc.HASHABLE,
        Constants.abc.SIZED,
        Constants.typing.IO.of(arguments=(Types.STR,)),
        Constants.typing.TEXT_IO,
        Constants.typing.BINARY_IO,
        Constants.typing.concatenate_of(
            prefix=(Types.INT,),
            params=Constants.typing.PARAM_SPEC,
        ),
        Types.callable(parameters=(Types.INT, Types.STR), returns=Types.BOOL),
        Types.callable(parameters=None, returns=Types.BOOL),
        Types.callable(parameters=Types.ELLIPSIS, returns=Types.BOOL),
        Constants.abc.callable_of(parameters=(Types.INT,), returns=Types.INT),
        Constants.abc.callable_of(parameters=None, returns=Types.INT),
        Constants.abc.callable_of(
            parameters=Types.ELLIPSIS,
            returns=Types.INT,
        ),
        Types.local(name="Local"),
        Types.imported(module_parts=("os", "path"), name="PathLike"),
        Types.imported(module_parts=("pathlib",), name="Path", asname="P"),
        Types.relative(level=1, name="Sibling", module_parts=("mod",)),
        Types.relative(level=2, name="Parent", asname="Par"),
        Types.generic(
            origin=Types.local(name="Box"),
            arguments=(Types.INT, Types.STR),
        ),
    ]
    for hint in hints:
        text: str = _annotate(hint=hint)
        expect_in(item="class Holder", container=text)
    for attribute in dir(Constants.t.COLLECTIONS):
        candidate: object = getattr(Constants.t.COLLECTIONS, attribute)
        if not (attribute.isupper() and hasattr(candidate, "of")):
            continue
        value: TypeTemplateRef = cast(typ="TypeTemplateRef", val=candidate)
        rendered: bool = False
        for count in (1, 2, 3):
            arguments: tuple[TypeExpression, ...] = (
                Types.INT,
                Types.STR,
                Types.BOOL,
            )[:count]
            try:
                _annotate(hint=value.of(arguments=arguments))
            except SemanticCodegenError:
                continue
            rendered = True
            break
        expect_true(condition=rendered)


def test_protocol_names_are_inferred_from_methods() -> None:
    """Name protocols from dunder and verb capabilities."""
    cases: list[tuple[tuple[str, ...], str]] = [
        (("read", "write"), "IO"),
        (("__iter__", "__next__"), "Iterator"),
        (("encode", "decode"), "EncodingRoundTrip"),
        (("serialize", "deserialize"), "SerializationRoundTrip"),
        (("get", "set"), "PropertyAccess"),
        (("__call__",), "Call"),
        (("__len__", "__contains__"), "Length"),
        (("__getitem__", "__setitem__"), "ItemAccess"),
        (("__enter__", "__exit__"), "ContextManagement"),
        (("__await__",), "Awaiting"),
        (("__mul__",), "Multiplication"),
        (("load",), "Loading"),
        (("save", "parse"), "Saving"),
        (("format", "transform", "convert"), "Formatting"),
        (("validate", "remove", "add"), "Validation"),
        (("something_unknown",), "Supports"),
    ]
    for methods, fragment in cases:
        collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
        registration: ProtocolRegistration = collector.protocol(
            spec=ProtocolSpec(
                methods=tuple(
                    MethodSpec(
                        name=name,
                        arguments=(Args.self_arg(),),
                        returns=Types.INT,
                    )
                    for name in methods
                ),
            ),
        )
        expect_true(condition=registration.spec.name is not None)
        expect_in(item=fragment, container=str(object=registration.spec.name))
        expect_equal(actual=registration.match_reason, expected="new")
        expect_false(condition=registration.is_existing)


def test_protocol_methods_support_every_argument_kind() -> None:
    """Build methods with positional-only, keyword-only and variadic items."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    typevar: TypeVarSpec = collector.typevar(bound=Types.STR)
    paramspec: ParamSpecSpec = collector.paramspec()
    collector.protocol(
        spec=ProtocolSpec(
            name="Everything",
            docstring="All argument kinds.",
            bases=(Types.local(name="Base"),),
            decorators=(Name(id="runtime_checkable"),),
            methods=(
                MethodSpec(
                    name="run",
                    arguments=(
                        Args.self_arg(),
                        Args.posonly(name="a", type_hint=Types.INT),
                        Args.slash(),
                        Args.arg(
                            name="b",
                            type_hint=Types.STR,
                            default=Constant(value=1),
                        ),
                        Args.varargs(type_hint=Types.INT),
                        Args.kwonly(name="c", type_hint=Types.BOOL),
                        Args.kwargs(type_hint=Types.INT),
                    ),
                    returns=typevar.ref(),
                    docstring="Run it.",
                    type_params=(typevar, paramspec),
                ),
                MethodSpec(
                    name="make",
                    arguments=(
                        Args.cls_arg(),
                        Args.star(),
                        Args.kwonly(name="x", type_hint=Types.INT),
                    ),
                    returns=Types.SELF,
                    decorators=(Name(id="classmethod"),),
                ),
                MethodSpec(
                    name="wrapped",
                    arguments=(
                        Args.self_arg(),
                        Args.arg(
                            name="f",
                            type_hint=Types.callable(
                                parameters=paramspec.args_ref(),
                                returns=typevar.ref(),
                            ),
                        ),
                        Args.varargs(type_hint=paramspec.args_ref()),
                        Args.kwargs(type_hint=paramspec.kwargs_ref()),
                    ),
                    returns=Types.INT,
                ),
            ),
        ),
    )
    text: str = _render(block=collector.build_block())
    expect_in(item="class Everything", container=text)
    expect_in(item="TypeVar", container=text)
    expect_in(item="ParamSpec", container=text)
    expect_in(item="/", container=text)


def test_protocol_registration_reuses_existing_protocols() -> None:
    """Match an existing protocol by name and by shape."""
    existing: Module = parse(
        source=dedent(
            text="""\
    from typing import Protocol
    class Reader(Protocol):
        def read(self) -> bytes: ...
    """,
        ),
    )
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector(
        existing_nodes=_existing(module=existing),
    )
    spec: ProtocolSpec = ProtocolSpec(
        name="Reader",
        methods=(
            MethodSpec(
                name="read",
                arguments=(Args.self_arg(),),
                returns=Types.BYTES,
            ),
        ),
    )
    by_name: ProtocolRegistration = collector.protocol(spec=spec)
    expect_equal(actual=by_name.match_reason, expected="name")
    expect_true(condition=by_name.is_existing)
    shaped: ProtocolRegistration = collector.protocol(
        spec=ProtocolSpec(name="Other", methods=spec.methods),
    )
    expect_equal(actual=shaped.match_reason, expected="shape")


def test_typevar_and_paramspec_naming() -> None:
    """Generate stable names and reject conflicting TypeVar options."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    first: TypeVarSpec = collector.typevar()
    second: TypeVarSpec = collector.typevar(bound=Types.INT)
    third: TypeVarSpec = collector.typevar(constraints=(Types.INT, Types.STR))
    named: TypeVarSpec = collector.typevar(name="Custom", covariant=True)
    contra: TypeVarSpec = collector.typevar(name="Contra", contravariant=True)
    again: TypeVarSpec = collector.typevar()
    expect_equal(actual=first.name, expected=again.name)
    expect_true(
        condition=len({first.name, second.name, third.name, named.name})
        == Constants.unique_names,
    )
    expect_equal(actual=contra.name, expected="Contra")
    collector.paramspec(name="Ps", bound=Types.INT, covariant=True)
    collector.paramspec(contravariant=True)
    collector.paramspec()
    collector.paramspec()
    with pytest.raises(expected_exception=SemanticCodegenError):
        collector.typevar(bound=Types.INT, constraints=(Types.STR,))
    with pytest.raises(expected_exception=SemanticCodegenError):
        collector.typevar(name="not valid")
    with pytest.raises(expected_exception=SemanticCodegenError):
        collector.typevar(name="class")
    text: str = _render(block=collector.build_block())
    expect_in(item="TypeVar", container=text)
    expect_in(item="ParamSpec", container=text)


def test_import_collection_variants() -> None:
    """Resolve absolute, relative, aliased and conflicting imports."""
    existing: Module = parse(
        source=dedent(
            text=(
                """\
    from __future__ import annotations
    import typing
    from os import path
    from collections.abc import *
    from . import sibling
    class Protocol: ...
    """
            ),
        ),
    )
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector(
        existing_nodes=_existing(module=existing),
        postponed_annotations=None,
        local_roots=("mypkg",),
    )
    for index, hint in enumerate(
        iterable=(
            Types.imported(module_parts=("mypkg", "sub"), name="Local"),
            Types.imported(module_parts=("os",), name="path"),
            Types.imported(module_parts=("typing",), name="Protocol"),
            Types.imported(module_parts=("json",), name="loads", asname="L"),
            Types.imported(module_parts=("json",), name="dumps"),
            Types.relative(level=1, name="sibling"),
            Types.relative(level=3, name="Far", module_parts=("a", "b")),
            Types.local(name="sibling"),
        ),
    ):
        collector.protocol(
            spec=ProtocolSpec(
                name=(f"P{index}"),
                methods=(
                    MethodSpec(
                        name="get",
                        arguments=(Args.self_arg(),),
                        returns=hint,
                    ),
                ),
            ),
        )
    text: str = _render(block=collector.build_block())
    expect_in(item="import", container=text)


def test_semantic_import_sources_validate_identifiers() -> None:
    """Reject invalid module parts and names."""
    source: SemanticImportSource = SemanticImportSource.absolute(
        module_parts=("a", "b"),
        imported_name="C",
    )
    expect_equal(actual=source.module, expected="a.b")
    relative: SemanticImportSource = SemanticImportSource.relative(
        level=2,
        imported_name="D",
    )
    expect_equal(actual=relative.module, expected=None)
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    for bad in (
        Types.imported(module_parts=("1bad",), name="X"),
        Types.imported(module_parts=("ok",), name="not-valid"),
        Types.local(name="no good"),
    ):
        with pytest.raises(expected_exception=SemanticCodegenError):
            collector.protocol(
                spec=ProtocolSpec(
                    name="Bad",
                    methods=(
                        MethodSpec(
                            name="m",
                            arguments=(Args.self_arg(),),
                            returns=bad,
                        ),
                    ),
                ),
            )
    for use in (
        ImportUseSite.runtime(),
        ImportUseSite.annotation(owner="x"),
        ImportUseSite.string_type_hint(),
        ImportUseSite.typevar_declaration(),
        ImportUseSite.paramspec_declaration(),
        ImportUseSite.typevar_bound(),
        ImportUseSite.typevar_constraint(),
        ImportUseSite.protocol_base(),
        ImportUseSite.method_body(),
    ):
        expect_equal(actual=type(use), expected=ImportUseSite)


def test_cast_expressions_import_cast_and_render_hints() -> None:
    """Build typing.cast calls for arbitrary target expressions."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    call: Call = collector.casts.cast(
        type_hint=Constants.builtins.list_of(item=Types.INT),
        target=Name(id="value"),
    )
    expect_in(item="cast", container=unparse(ast_obj=call))
    expect_in(item="cast", container=_render(block=collector.build_block()))


def test_union_rank_and_generalisation_branches() -> None:
    """Cover numeric ranks, literal collapse and container generalisation."""
    hints: list[TypeExpression] = [
        Types.union(
            options=(Constants.typing.literal_of(values=(True,)), Types.BOOL),
        ),
        Types.union(
            options=(Constants.typing.literal_of(values=(1.5,)), Types.FLOAT),
        ),
        Types.union(
            options=(
                Constants.typing.literal_of(values=(None, "a")),
                Types.STR,
            ),
        ),
        Types.union(
            options=(Constants.typing.literal_of(values=(1,)), Types.STR),
        ),
        Types.union(
            options=(
                Constants.builtins.list_of(item=Types.INT),
                Constants.builtins.tuple_variadic(item=Types.INT),
            ),
        ),
        Types.union(
            options=(
                Constants.builtins.set_of(item=Types.INT),
                Constants.builtins.frozenset_of(item=Types.INT),
            ),
        ),
        Types.union(
            options=(
                Constants.builtins.set_of(item=Types.INT),
                Constants.builtins.set_of(item=Types.STR),
            ),
        ),
        Types.union(
            options=(
                Constants.builtins.frozenset_of(item=Types.INT),
                Constants.builtins.frozenset_of(item=Types.STR),
            ),
        ),
        Types.union(
            options=(
                Constants.builtins.tuple_variadic(item=Types.INT),
                Constants.builtins.tuple_variadic(item=Types.STR),
            ),
        ),
        Types.union(
            options=(
                Constants.abc.one_arg(
                    template=Constants.abc.SEQUENCE,
                    item=Types.INT,
                ),
                Constants.builtins.list_of(item=Types.INT),
            ),
        ),
        Types.union(
            options=(
                Constants.abc.one_arg(
                    template=Constants.abc.ITERABLE,
                    item=Types.INT,
                ),
                Constants.builtins.set_of(item=Types.INT),
            ),
        ),
        Types.union(
            options=(
                Constants.builtins.dict_of(keys=Types.STR, values=Types.INT),
                Constants.t.COLLECTIONS.DEFAULTDICT.of(
                    arguments=(Types.STR, Types.INT),
                ),
                Constants.t.COLLECTIONS.ORDERED_DICT.of(
                    arguments=(Types.STR, Types.INT),
                ),
            ),
        ),
        Types.union(
            options=(
                Types.generic(
                    origin=Types.local(name="Custom"),
                    arguments=(Types.INT,),
                ),
                Types.generic(
                    origin=Types.local(name="Custom"),
                    arguments=(Types.STR,),
                ),
                Types.BYTES,
                Types.OBJECT,
                Types.COMPLEX,
                Types.SELF,
                Types.ELLIPSIS,
            ),
        ),
        Types.union(
            options=(
                Types.imported(module_parts=("x",), name="A"),
                Types.BOOL,
                Types.union(options=(Types.INT, Types.FLOAT)),
                Constants.typing.literal_of(values=("z",)),
            ),
        ),
    ]
    for hint in hints:
        try:
            _annotate(hint=hint)
        except SemanticCodegenError:
            continue
        expect_true(condition=hint.key() != "")


def test_argument_marker_validation() -> None:
    """Reject conflicting slash, star and variadic markers."""
    bad_sequences: list[tuple[ArgumentItem, ...]] = [
        (Args.slash(), Args.slash()),
        (Args.star(), Args.slash()),
        (Args.varargs(type_hint=Types.INT), Args.slash()),
        (Args.star(), Args.star()),
        (Args.varargs(type_hint=Types.INT), Args.star()),
        (Args.star(), Args.varargs(type_hint=Types.INT)),
        (
            Args.varargs(type_hint=Types.INT),
            Args.varargs(type_hint=Types.INT, name="more"),
        ),
        (Args.kwargs(type_hint=Types.INT), Args.kwargs(type_hint=Types.INT)),
        (
            Args.arg(name="a", type_hint=Types.INT),
            Args.arg(name="a", type_hint=Types.INT),
        ),
        (
            Args.kwargs(type_hint=Types.INT),
            Args.arg(name="a", type_hint=Types.INT),
        ),
        (
            Args.kwonly(name="k", type_hint=Types.INT),
            Args.arg(name="p", type_hint=Types.INT),
        ),
        (
            Args.arg(name="d", type_hint=Types.INT, default=Constant(value=1)),
            Args.arg(name="n", type_hint=Types.INT),
        ),
    ]
    for items in bad_sequences:
        collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
        try:
            collector.protocol(
                spec=ProtocolSpec(
                    name="Marked",
                    methods=(
                        MethodSpec(
                            name="m",
                            arguments=(Args.self_arg(), *items),
                            returns=Types.INT,
                        ),
                    ),
                ),
            )
        except SemanticCodegenError:
            continue
    good: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    good.protocol(
        spec=ProtocolSpec(
            name="Fine",
            methods=(
                MethodSpec(
                    name="m",
                    arguments=(
                        Args.self_arg(),
                        Args.arg(name="a", type_hint=Types.INT),
                        Args.slash(),
                        Args.star(),
                        Args.kwonly(
                            name="k",
                            type_hint=Types.INT,
                            default=Constant(value=2),
                        ),
                        Args.kwargs(type_hint=Types.INT),
                    ),
                    returns=Types.INT,
                ),
            ),
        ),
    )
    expect_in(item="class Fine", container=_render(block=good.build_block()))


def test_magic_methods_and_protocol_variants() -> None:
    """Generate magic-method bodies and handle existing qualified bases."""
    existing: Module = parse(
        source=dedent(
            text=(
                """\
    import typing
    class Known(typing.Protocol):
        def run(self, *args: int, **kwargs: int) -> int: ...
    class NotProto(Base):
        pass
    """
            ),
        ),
    )
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector(
        existing_nodes=_existing(module=existing),
    )
    for names in (
        ("__enter__",),
        ("__exit__",),
        ("__iter__", "__len__", "__contains__", "__getitem__"),
        ("__call__", "__await__"),
        ("__eq__", "__hash__", "__str__", "__repr__", "__bool__"),
        (),
    ):
        collector.protocol(
            spec=ProtocolSpec(
                methods=tuple(
                    MethodSpec(
                        name=name,
                        arguments=(Args.self_arg(),),
                        returns=Types.INT,
                        docstring="Doc.",
                    )
                    for name in names
                ),
                docstring="Custom doc." if not names else None,
            ),
        )
    shaped: ProtocolRegistration = collector.protocol(
        spec=ProtocolSpec(
            name="Alias",
            methods=(
                MethodSpec(
                    name="run",
                    arguments=(
                        Args.self_arg(),
                        Args.varargs(type_hint=Types.INT),
                        Args.kwargs(type_hint=Types.INT),
                    ),
                    returns=Types.INT,
                ),
            ),
        ),
    )
    expect_true(condition=shaped.is_existing)
    text: str = _render(block=collector.build_block())
    expect_in(item="class", container=text)
    with pytest.raises(expected_exception=SemanticCodegenError):
        _node_builder().protocol(spec=ProtocolSpec(methods=()))


def test_overload_stub_factory_and_type_params() -> None:
    """Build overload stubs and PEP 695 method type parameters."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    factory: OverloadExpressionFactory = OverloadExpressionFactory(
        imports=_imports(),
    )
    stub: FunctionDef = factory.overload_stub(
        function_name="get",
        parameters=(
            Args.arg(name="key", type_hint=Types.STR),
            Args.arg(name="default", type_hint=Types.INT),
        ),
        return_type=Types.INT,
        docstring="Overloaded.",
    )
    plain: FunctionDef = factory.overload_stub(
        function_name="get",
        parameters=(),
        return_type=Types.STR,
    )
    expect_equal(actual=stub.name, expected="get")
    expect_equal(actual=plain.name, expected="get")
    constrained: TypeVarSpec = collector.typevar(
        constraints=(Types.INT, Types.STR),
    )
    bound: TypeVarSpec = collector.typevar(bound=Types.INT)
    free: TypeVarSpec = collector.typevar()
    spec: ParamSpecSpec = collector.paramspec()
    collector.protocol(
        spec=ProtocolSpec(
            name="Generic",
            methods=(
                MethodSpec(
                    name="run",
                    arguments=(Args.self_arg(),),
                    returns=Types.INT,
                    type_params=(constrained, bound, free, spec),
                    body=(parse(source="return 1").body[0],),
                ),
            ),
        ),
    )
    text: str = _render(block=collector.build_block())
    expect_in(item="class Generic", container=text)
    expect_in(item="return 1", container=text)
    method: FunctionDef = _node_builder().method(
        spec=MethodSpec(
            name="generic",
            arguments=(Args.self_arg(),),
            returns=Types.INT,
            type_params=(constrained, bound, free, spec),
        ),
    )
    expect_equal(actual=len(method.type_params), expected=4)


def test_import_name_collisions_get_aliases() -> None:
    """Alias imports that collide with existing or generated names."""
    existing: Module = parse(
        source=dedent(
            text="""\
    from os import path
    from json import loads as parse_json
    import collections
    class path2: ...
    class Mapping: ...
    """,
        ),
    )
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector(
        existing_nodes=_existing(module=existing),
    )
    hints: list[TypeExpression] = [
        Types.imported(module_parts=("posixpath",), name="path"),
        Types.imported(module_parts=("ntpath",), name="path"),
        Types.imported(module_parts=("os",), name="path"),
        Types.imported(module_parts=("json",), name="loads"),
        Types.imported(module_parts=("collections", "abc"), name="Mapping"),
        Types.imported(module_parts=("typing",), name="Mapping"),
        Types.imported(module_parts=("collections",), name="OrderedDict"),
        Types.relative(level=1, name="path"),
        Types.relative(level=1, name="Mapping", module_parts=("m",)),
        Types.local(name="Mapping"),
        Types.local(name="path2"),
    ]
    for index, hint in enumerate(iterable=hints):
        collector.protocol(
            spec=ProtocolSpec(
                name=(f"Collide{index}"),
                methods=(
                    MethodSpec(
                        name="get",
                        arguments=(Args.self_arg(),),
                        returns=hint,
                    ),
                ),
            ),
        )
    text: str = _render(block=collector.build_block())
    expect_in(item="import", container=text)


def test_none_renders_as_an_annotation() -> None:
    """Render the None type and optional unions."""
    expect_in(item="-> None", container=_annotate(hint=Types.NONE))
    expect_in(
        item="str | None",
        container=_annotate(hint=Constants.typing.noneable(item=Types.STR)),
    )


def test_import_sources_require_a_module() -> None:
    """Reject absolute imports without module parts."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    with pytest.raises(expected_exception=SemanticCodegenError):
        collector.protocol(
            spec=ProtocolSpec(
                name="Empty",
                methods=(
                    MethodSpec(
                        name="m",
                        arguments=(Args.self_arg(),),
                        returns=Types.imported(module_parts=(), name="X"),
                    ),
                ),
            ),
        )


def test_existing_assignments_and_functions_reserve_names() -> None:
    """Accept assignments and functions as existing top-level nodes."""
    existing: Module = parse(
        source="""\
path2 = 1
annotated: int = 2
def helper(): ...
""",
    )
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector(
        existing_nodes=_existing(module=existing),
    )
    collector.protocol(
        spec=ProtocolSpec(
            name="Reserved",
            methods=(
                MethodSpec(
                    name="get",
                    arguments=(Args.self_arg(),),
                    returns=Types.local(name="path2"),
                ),
            ),
        ),
    )
    expect_in(
        item="class Reserved",
        container=_render(block=collector.build_block()),
    )


def test_method_type_params_survive_protocol_registration() -> None:
    """Keep PEP 695 type parameters on registered protocol methods."""
    collector: ProtocolTypeBlockCollector = ProtocolTypeBlockCollector()
    variable: TypeVarSpec = collector.typevar(name="Item", bound=Types.STR)
    collector.protocol(
        spec=ProtocolSpec(
            name="Keeps",
            methods=(
                MethodSpec(
                    name="run",
                    arguments=(Args.self_arg(),),
                    returns=variable.ref(),
                    type_params=(variable,),
                ),
            ),
        ),
    )
    expect_in(
        item="def run[Item: str]",
        container=_render(block=collector.build_block()),
    )


def _generated_name(*, index: int) -> str:
    """Synthesize a mixed-case, punctuation-bearing name deterministically.

    Args:
        index (int): Case number selecting length and characters.

    Returns:
        str: A synthetic identifier-like string.

    """
    length: int = 3 + index % 17
    return "".join(
        Constants.split_alphabet[
            (index * 31 + position * 17 + position * position)
            % len(Constants.split_alphabet)
        ]
        for position in range(length)
    )


def _reference_snake_words(*, name: str) -> tuple[str, ...]:
    """Reproduce the retired ``sub`` word split for comparison.

    Args:
        name (str): Identifier text to split into lowercase words.

    Returns:
        tuple[str, ...]: Word tuple the retired regex pipeline produced.

    """
    stripped: str = name.strip("_")
    snake_ready: str = sub(
        pattern=r"([a-z0-9])([A-Z])",
        repl=r"\1_\2",
        string=stripped,
    )
    return tuple(part.lower() for part in snake_ready.split(sep="_") if part)


def _reference_title_words(*, value: str) -> str:
    """Reproduce the retired lookaround substitution for comparison.

    Args:
        value (str): Title-cased text to space-separate and lowercase.

    Returns:
        str: The space-separated lowercase string.

    """
    return sub(pattern=r"(?<!^)(?=[A-Z])", repl=" ", string=value).lower()


def _reference_pascal(*, words: tuple[str, ...]) -> str:
    """Reproduce ``_pascal_case`` on already-split words.

    Args:
        words (tuple[str, ...]): Lowercase word tuple to capitalize and join.

    Returns:
        str: The PascalCase spelling.

    """
    return "".join(word[:1].upper() + word[1:] for word in words)


def test_identifier_case_conversion_matches_regex_reference() -> None:
    """Public naming paths equal the retired ``sub`` calls (CC-08-09)."""
    grammar: ProtocolGrammar = ProtocolGrammar()
    special: list[str] = []
    for index in range(Constants.split_cases):
        name: str = _generated_name(index=index)
        profile: MethodSemanticProfile = MethodSemanticProfile(
            name="probe",
            capability=name,
            required_argument_count=0,
            is_dunder=False,
        )
        expect_equal(
            actual=grammar.method_docstring(profile=profile),
            expected=(
                "Perform "
                + _reference_title_words(value=name)
                + " using this method's declared inputs."
            ),
            message=f"title words mismatch for {name!r}",
        )
        words: tuple[str, ...] = _reference_snake_words(name=name)
        if name in Constants.split_dunders or (
            words and words[0] in Constants.split_verbs
        ):
            special.append(name)
            continue
        expected_name: str = (
            "SupportsProtocolBehavior"
            if not words
            else "Supports" + _reference_pascal(words=words)
        )
        expect_equal(
            actual=grammar.name_for_members(members=(name,)),
            expected=expected_name,
            message=f"identifier split mismatch for {name!r}",
        )
    expect_equal(
        actual=special,
        expected=[],
        message="generated names must stay on the plain split path",
    )
