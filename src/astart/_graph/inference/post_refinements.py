"""Generic AST post-refinements for inferred source output.

This module contains graph-compatible, source-agnostic refinements that
operate on parsed backend output.  The rules are intentionally generic:
they look at annotation evidence, expression shapes, and common
standard-library call semantics rather than at fixture-specific names.
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Dict,
    DictComp,
    Expr,
    For,
    FunctionDef,
    IfExp,
    Import,
    ImportFrom,
    List,
    Load,
    Module,
    Name,
    Return,
    Starred,
    Subscript,
    Tuple,
    Yield,
    YieldFrom,
    alias,
    arg,
    arguments,
    comprehension,
    dump,
    expr,
    keyword,
    stmt,
)
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Final, Protocol, cast, final

from astart._graph.backend.finalizer import finalize_and_format_module
from astart._graph.backend.refiner import self_attr_assignment_param_map
from astart._graph.conversion.synthesis import (
    ExistingNodeContext,
    ScriptSymbolIndex,
    TypeExpressionResolver,
    UsageAwareImportCollector,
    create_simple_typevar,
)
from astart._graph.graph.semantics import (
    child_nodes,
    nodes_of_type,
    render_annotation,
)


def _make_name_node(name: str, ctx: type[Load] = Load) -> Name:
    """Create a Name node with the given identifier and context.

    Args:
        ctx: Ctx supplied as type[Load] for this operation.
        name: Identifier of the name being resolved.

    Returns:
        Name produced by this operation.

    """
    return Name(id=name, ctx=ctx())


def _make_subscript_node(value: expr, slice_expr: expr) -> Subscript:
    """Create a Subscript node with the given value and slice.

    Args:
        slice_expr: Slice expr supplied as expr for this operation.
        value: The value examined while create a Subscript node with the given
            value and slice.

    Returns:
        Subscript produced by this operation.

    """
    return Subscript(value=value, slice=slice_expr, ctx=Load())


def _make_tuple_node(elts: list[expr]) -> Tuple:
    """Create a Tuple node with the given elements.

    Args:
        elts: Elts supplied as list[expr] for this operation.

    Returns:
        Tuple produced by this operation.

    """
    return Tuple(elts=elts, ctx=Load())


def _make_bit_or_node(left: expr, right: expr) -> BinOp:
    """Create a BinOp node with BitOr operator.

    Args:
        left: Left supplied as expr for this operation.
        right: Right supplied as expr for this operation.

    Returns:
        BinOp produced by this operation.

    """
    return BinOp(left=left, op=BitOr(), right=right)


def _make_type_subscript(name: str, param: expr) -> Subscript:
    """Create a type[...] subscript node.

    Args:
        name: Identifier of the name being resolved.
        param: Param supplied as expr for this operation.

    Returns:
        Subscript produced by this operation.

    """
    return _make_subscript_node(
        value=_make_name_node(name=name),
        slice_expr=param,
    )


def _make_generic_subscript(name: str, params: list[expr]) -> Subscript:
    """Create a generic subscript like list[int] or dict[str, int].

    Args:
        name: Identifier of the name being resolved.
        params: Params supplied as list[expr] for this operation.

    Returns:
        Subscript produced by this operation.

    """
    if len(params) == 1:
        slice_expr: expr = params[0]
    else:
        slice_expr = _make_tuple_node(elts=params)
    return _make_subscript_node(
        value=_make_name_node(name=name),
        slice_expr=slice_expr,
    )


@final
class Constants:
    """Group module-level constants.

    Attributes:
        callable_node: Grouped module constant.
        self_node: Grouped module constant.
        iterable_node: Grouped module constant.
        tuple_node: Grouped module constant.
        set_node: Grouped module constant.
        tuple_empty_node: Grouped module constant.
        pair_size: Grouped module constant.
        none_node: Grouped module constant.
        object_node: Grouped module constant.
        list_object_node: Grouped module constant.
        dict_object_object_node: Grouped module constant.
        type_object_node: Grouped module constant.
        list_list_object_node: Grouped module constant.
        int_node: Grouped module constant.
        iterable_int_node: Grouped module constant.
        str_node: Grouped module constant.
        dict_str_object_node: Grouped module constant.
        bool_node: Grouped module constant.
        float_node: Grouped module constant.
        bytes_node: Grouped module constant.
        ellipsis_node: Grouped module constant.
        generator_source_arity: Grouped module constant.
        descriptor_get_arg_count: Grouped module constant.

    """

    callable_node: Final[expr] = Name(id="Callable", ctx=Load())
    self_node: Final[expr] = Name(id="Self", ctx=Load())
    iterable_node: Final[expr] = Name(id="Iterable", ctx=Load())
    tuple_node: Final[expr] = Name(id="tuple", ctx=Load())
    set_node: Final[expr] = Name(id="set", ctx=Load())
    tuple_empty_node: Final[expr] = _make_generic_subscript(
        name="tuple",
        params=[],
    )
    pair_size: Final[int] = 2
    none_node: Final[expr] = Constant(value=None)
    object_node: Final[expr] = Name(id="object", ctx=Load())
    list_object_node: Final[expr] = _make_generic_subscript(
        name="list",
        params=[object_node],
    )
    dict_object_object_node: Final[expr] = _make_generic_subscript(
        name="dict",
        params=[object_node, object_node],
    )
    type_object_node: Final[expr] = _make_type_subscript(
        name="type",
        param=object_node,
    )
    list_list_object_node: Final[expr] = _make_generic_subscript(
        name="list",
        params=[list_object_node],
    )
    int_node: Final[expr] = Name(id="int", ctx=Load())
    iterable_int_node: Final[expr] = _make_generic_subscript(
        name="Iterable",
        params=[int_node],
    )
    str_node: Final[expr] = Name(id="str", ctx=Load())
    dict_str_object_node: Final[expr] = _make_generic_subscript(
        name="dict",
        params=[str_node, object_node],
    )
    bool_node: Final[expr] = Name(id="bool", ctx=Load())
    float_node: Final[expr] = Name(id="float", ctx=Load())
    bytes_node: Final[expr] = Name(id="bytes", ctx=Load())
    ellipsis_node: Final[expr] = Constant(value=...)
    generator_source_arity: Final[int] = 3
    descriptor_get_arg_count: Final[int] = 3


def _make_union_node(*types: expr) -> expr:
    """Create a union node (a | b | c) using BitOp.

    Args:
        types: Collection of types supplied for this operation.

    Returns:
        expr produced by this operation.

    """
    if not types:
        return _make_name_node(name="object")
    if len(types) == 1:
        return types[0]
    result: expr = types[0]
    for typ in types[1:]:
        result = _make_bit_or_node(left=result, right=typ)
    return result


_NONE_OBJECT_NODE: Final[expr] = _make_union_node(
    Constants.none_node,
    Constants.object_node,
)
_SET_OBJECT_NODE: Final[expr] = _make_generic_subscript(
    name="set",
    params=[Constants.object_node],
)
_UNKNOWN_COLLECTION_SOURCES: Final[frozenset[TypeSource]] = frozenset(
    {
        Constants.list_object_node,
        Constants.dict_str_object_node,
        _SET_OBJECT_NODE,
    },
)


def _ast_equals(a: expr, b: expr) -> bool:
    """Compare two AST nodes for structural equality (ignoring positions).

    Args:
        a: A supplied as expr for this operation.
        b: B supplied as expr for this operation.

    Returns:
        Whether the requested condition holds.

    """
    return dump(node=a) == dump(node=b)


def _is_callable_type(node: expr) -> bool:
    """Check if a type node represents a Callable.

    Args:
        node: The node examined while check if a type node represents a
            Callable.

    Returns:
        Whether the requested condition holds.

    """
    if isinstance(node, Name):
        return node.id == "Callable"
    if isinstance(node, Subscript):
        return isinstance(node.value, Name) and node.value.id == "Callable"
    return False


def _make_callable_subscript(
    *,
    params: list[expr] | None,
    returns: expr,
) -> Subscript:
    """Create a Callable[[...], ...] subscript node.

    Args:
        params: Params supplied as list[expr] | None for this operation.
        returns: Returns supplied as expr for this operation.

    Returns:
        Subscript produced by this operation.

    """
    if params is None:
        params_list: expr = _make_name_node(name="...")
    else:
        params_list = List(elts=params, ctx=Load())
    return Subscript(
        value=_make_name_node(name="Callable"),
        slice=Tuple(elts=[params_list, returns], ctx=Load()),
        ctx=Load(),
    )


def _ast_node_to_string(node: expr | None) -> str:
    """Convert an AST node to a normalized string for comparison.

    Args:
        node: The node examined while convert an AST node to a normalized
            string for comparison.

    Returns:
        str produced by this operation.

    """
    if node is None:
        return ""
    return render_annotation(node=node)


type TypeSource = expr
type ExpressionInferer = Callable[
    [AST, FunctionTypeEnvironment],
    TypeSource | None,
]


class CallInferer(Protocol):
    """Typed callback accepting the named source and environment."""

    def __call__(
        self,
        *,
        node: Call,
        environment: FunctionTypeEnvironment,
    ) -> TypeSource | None:
        """Infer the return type of a known source call.

        Args:
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            node: The node examined while infer the return type of a known
                source call.

        Returns:
            TypeSource | None produced by this operation.

        """
        ...


@dataclass(slots=True)
class RefinementStats:
    """Summary of generic post-refinements.

    Attributes:
        changed_annotations: Changed annotations retained as int by this
            instance.
        changed_calls: Changed calls retained as int by this instance.
        changed_returns: Changed returns retained as int by this instance.

    """

    changed_annotations: int = 0
    changed_returns: int = 0
    changed_calls: int = 0

    def changed(self) -> bool:
        """Return whether at least one refinement changed the tree.

        Returns:
            Whether the requested condition holds.

        """
        return (
            self.changed_annotations > 0
            or self.changed_returns > 0
            or self.changed_calls > 0
        )


@dataclass(slots=True)
class FunctionTypeEnvironment:
    """Local annotation evidence collected within one function body.

    Attributes:
        names: Names retained as dict[str, TypeSource] by this instance.

    """

    names: dict[str, TypeSource] = field(default_factory=dict)

    def set_if_better(self, *, name: str, source: TypeSource) -> None:
        """Store a type for ``name`` when it is more precise.

        Args:
            name: Identifier of the name being resolved.
            source: The source examined while store a type for ``name`` when it
                is more precise.

        """
        current: TypeSource | None = self.names.get(name)
        if current is None or should_replace_type(
            current=current,
            candidate=source,
        ):
            self.names[name] = source

    def get(self, *, name: str) -> TypeSource | None:
        """Return the current inferred type for ``name``.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            TypeSource | None produced by this operation.

        """
        return self.names.get(name)


@dataclass(slots=True)
class _ProxyTarget:
    """The proxy-decorator pieces retargeted as ``type[T]`` contracts.

    Attributes:
        init_method: Init method retained as FunctionDef by this instance.
        parameter: Parameter retained as arg by this instance.
        wrapper_class: Wrapper class retained as ClassDef by this instance.

    """

    parameter: arg
    wrapper_class: ClassDef
    init_method: FunctionDef


@dataclass(slots=True)
class GenericPostRefiner:
    """Apply generic type refinements to an inferred module AST.

    Attributes:
        function_returns: Function returns retained as dict[str, TypeSource] by
            this instance.
        module: Module retained as Module by this instance.
        stats: Stats retained as RefinementStats by this instance.

    """

    module: Module
    stats: RefinementStats = field(default_factory=RefinementStats)
    function_returns: dict[str, TypeSource] = field(default_factory=dict)
    _synthesis_imports: UsageAwareImportCollector = field(init=False)
    _synthesis_resolver: TypeExpressionResolver = field(init=False)

    @staticmethod
    def find_matching_protocol(
        *,
        attributes: set[str],
        protocol_attributes: dict[str, dict[str, AnnAssign]],
    ) -> str | None:
        """Find a Protocol that defines all the given attributes.

        Args:
            attributes: Attributes supplied as set[str] for this operation.
            protocol_attributes: Protocol attributes supplied as dict[str,
                dict[str, AnnAssign]] for this operation.

        Returns:
            str | None produced by this operation.

        """
        for protocol_name, proto_attrs in protocol_attributes.items():
            if attributes.issubset(proto_attrs.keys()):
                return protocol_name
        return None

    @staticmethod
    def find_protocol_by_attribute(
        *,
        attribute_name: str,
        protocol_attributes: dict[str, dict[str, AnnAssign]],
    ) -> str | None:
        """Find a Protocol that defines a specific attribute.

        Args:
            attribute_name: Identifier of the attribute being resolved.
            protocol_attributes: Protocol attributes supplied as dict[str,
                dict[str, AnnAssign]] for this operation.

        Returns:
            str | None produced by this operation.

        """
        for protocol_name, proto_attrs in protocol_attributes.items():
            if attribute_name in proto_attrs:
                return protocol_name
        return None

    def refine(self) -> Module:
        """Return the refined module.

        Returns:
            Module produced by this operation.

        """
        self._refresh_function_returns()
        function: FunctionDef
        for function in self._module_functions():
            self._refine_function(function=function)
        self._refine_class_methods()
        self._refine_self_returns()
        self._refine_descriptor_signatures()
        self._refine_property_setter_parameters()
        self._refine_identity_class_decorators()
        self._refine_proxy_class_decorators()
        self._refine_misassigned_callable_annotations()
        self._refine_singleton_new_returns()
        self._refine_nested_numeric_attributes()
        self._refine_protocol_attributes()
        self._refine_callable_parameter_signatures()
        self._refine_returned_local_callables()
        self._simplify_generator_annotations()
        self._refine_contextmanager_returns()
        self._refine_async_generator_return_types()
        self._refine_returned_class_bases()
        self._refine_metaclass_signatures()
        self._refine_metaclass_call_protocols()
        self._refine_list_object_unions()
        self._alias_heterogeneous_result_returns()
        self._refine_keyword_arguments()
        self._refine_builtin_override_signatures()
        self._refine_metaclass_parameter_types()
        self._refine_dataclass_like_attributes()
        for function in self._module_functions():
            self._refine_function(function=function)
        self._refine_linear_flow()
        self._annotate_bare_assignments()
        self._refine_returned_class_bases()
        self._refine_list_object_unions()
        self._alias_heterogeneous_result_returns()
        self._refine_class_attributes_from_init()
        self._insert_synthesis_imports()
        return self.module

    def refine_returned_local_classes(self) -> None:
        """Annotate factories that return locally-defined classes.

        A function whose body defines and returns a single class should
        have return type ``ClassName`` instead of ``type[object]``.
        """
        for function in self._module_functions():
            if function.returns is None:
                continue
            current: TypeSource = normalize_source(source=function.returns)
            if not (
                _ast_equals(a=current, b=_make_name_node(name="type"))
                or _ast_equals(a=current, b=Constants.type_object_node)
            ):
                continue
            local_class_name: str | None = returned_local_class_name(
                function=function,
            )
            if local_class_name is None:
                continue
            candidate: TypeSource = _make_name_node(name=local_class_name)
            function.returns = candidate
            self.function_returns[function.name] = candidate
            self.stats.changed_returns += 1

    def annotate_instance_aliases(
        self,
        *,
        function: FunctionDef,
        instance_name: str,
        protocol_name: str,
    ) -> None:
        """Annotate simple aliases of the instance variable.

        Args:
            function: The function examined while annotate simple aliases of
                the instance variable.
            instance_name: Identifier of the instance being resolved.
            protocol_name: Identifier of the protocol being resolved.

        """
        for index, statement in enumerate(iterable=function.body):
            if not isinstance(statement, Assign):
                continue
            if (
                len(statement.targets) == 1
                and isinstance(statement.targets[0], Name)
                and isinstance(statement.value, Name)
                and (statement.value.id == instance_name)
            ):
                target: Name = statement.targets[0]
                annotated: AnnAssign = AnnAssign(
                    target=target,
                    annotation=_make_name_node(name=protocol_name),
                    value=statement.value,
                    simple=1,
                )
                function.body[index] = annotated
                self.stats.changed_annotations += 1

    def add_cast_to_instance(
        self,
        *,
        function: FunctionDef,
        instance_name: str,
        protocol_name: str,
    ) -> None:
        """Add a cast annotation to an instance variable.

        Args:
            function: The function examined while add a cast annotation to an
                instance variable.
            instance_name: Identifier of the instance being resolved.
            protocol_name: Identifier of the protocol being resolved.

        """
        for index, statement in enumerate(iterable=function.body):
            if not isinstance(statement, Assign):
                continue
            if not isinstance(statement.value, Call):
                continue
            call: Call = statement.value
            if not isinstance(call.func, Attribute):
                continue
            if call.func.attr != "__call__":
                continue
            for target in statement.targets:
                if not isinstance(target, Name):
                    continue
                if target.id != instance_name:
                    continue
                cast_call: Call = Call(
                    func=Name(id="cast", ctx=Load()),
                    args=[
                        Constant(value=protocol_name, kind=None),
                        statement.value,
                    ],
                    keywords=[],
                )
                new_annotation: AnnAssign = AnnAssign(
                    target=target,
                    annotation=_make_name_node(name=protocol_name),
                    value=cast_call,
                    simple=1,
                )
                function.body[index] = new_annotation
                self.stats.changed_annotations += 1
                return

    def widen_attribute_type(
        self,
        *,
        class_def: ClassDef,
        attr_name: str,
        init_value: expr,
    ) -> None:
        """Widen attribute type to include the init value type.

        Args:
            attr_name: Identifier of the attr being resolved.
            class_def: Class def supplied as ClassDef for this operation.
            init_value: Init value supplied as expr for this operation.

        """
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.target.id == attr_name)
            ):
                current_type: TypeSource = normalize_source(
                    source=item.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    value_type: str | None = self._infer_value_type(
                        value=init_value,
                    )
                    if value_type:
                        new_annotation: expr = _make_union_node(
                            _make_name_node(name="None"),
                            _make_name_node(name=value_type),
                        )
                        item.annotation = new_annotation
                        self.stats.changed_annotations += 1

    def widen_init_param_type(
        self,
        *,
        init_method: FunctionDef,
        attr_name: str,
        init_value: expr,
    ) -> None:
        """Widen __init__ parameter type to match attribute type.

        Args:
            attr_name: Identifier of the attr being resolved.
            init_method: Init method supplied as FunctionDef for this
                operation.
            init_value: Init value supplied as expr for this operation.

        """
        for param in init_method.args.args:
            if param.arg == attr_name:
                if param.annotation is None:
                    return
                current_type: TypeSource = normalize_source(
                    source=param.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    value_type: str | None = self._infer_value_type(
                        value=init_value,
                    )
                    if value_type:
                        new_annotation: expr = _make_union_node(
                            _make_name_node(name="None"),
                            _make_name_node(name=value_type),
                        )
                        param.annotation = new_annotation
                        self.stats.changed_annotations += 1

    def widen_attribute_type_with_union(
        self,
        *,
        class_def: ClassDef,
        attr_name: str,
        type1: str,
        type2: str,
    ) -> None:
        """Widen attribute type to include both types.

        Args:
            attr_name: Identifier of the attr being resolved.
            class_def: Class def supplied as ClassDef for this operation.
            type1: Type1 supplied as str for this operation.
            type2: Type2 supplied as str for this operation.

        """
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.target.id == attr_name)
            ):
                current_type: TypeSource = normalize_source(
                    source=item.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    new_annotation: expr = _make_union_node(
                        _make_name_node(name="None"),
                        _make_name_node(name=type1),
                        _make_name_node(name=type2),
                    )
                    item.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def widen_init_param_type_with_union(
        self,
        *,
        init_method: FunctionDef,
        attr_name: str,
        type1: str,
        type2: str,
    ) -> None:
        """Widen __init__ parameter type to include both types.

        Args:
            attr_name: Identifier of the attr being resolved.
            init_method: Init method supplied as FunctionDef for this
                operation.
            type1: Type1 supplied as str for this operation.
            type2: Type2 supplied as str for this operation.

        """
        for param in init_method.args.args:
            if param.arg == attr_name:
                if param.annotation is None:
                    return
                current_type: TypeSource = normalize_source(
                    source=param.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    new_annotation: expr = _make_union_node(
                        _make_name_node(name="None"),
                        _make_name_node(name=type1),
                        _make_name_node(name=type2),
                    )
                    param.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def widen_attribute_type_to_object(
        self,
        *,
        class_def: ClassDef,
        attr_name: str,
    ) -> None:
        """Widen attribute type to object.

        Args:
            attr_name: Identifier of the attr being resolved.
            class_def: Class def supplied as ClassDef for this operation.

        """
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.target.id == attr_name)
            ):
                current_type: TypeSource = normalize_source(
                    source=item.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    new_annotation: expr = _make_name_node(name="object")
                    item.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def widen_init_param_type_to_object(
        self,
        *,
        init_method: FunctionDef,
        attr_name: str,
    ) -> None:
        """Widen __init__ parameter type to object | None.

        Args:
            attr_name: Identifier of the attr being resolved.
            init_method: Init method supplied as FunctionDef for this
                operation.

        """
        for param in init_method.args.args:
            if param.arg == attr_name:
                if param.annotation is None:
                    return
                current_type: TypeSource = normalize_source(
                    source=param.annotation,
                )
                if _ast_equals(a=current_type, b=Constants.none_node):
                    new_annotation: expr = _make_union_node(
                        _make_name_node(name="object"),
                        _make_name_node(name="None"),
                    )
                    param.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def widen_attribute_type_with_specific(
        self,
        *,
        class_def: ClassDef,
        attr_name: str,
        type_name: str,
    ) -> None:
        """Widen attribute type to include specific type.

        Args:
            attr_name: Identifier of the attr being resolved.
            class_def: Class def supplied as ClassDef for this operation.
            type_name: Identifier of the type being resolved.

        """
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.target.id == attr_name)
            ):
                current_type: TypeSource = normalize_source(
                    source=item.annotation,
                )
                if _ast_equals(a=current_type, b=_NONE_OBJECT_NODE):
                    new_annotation: expr = _make_union_node(
                        _make_name_node(name="None"),
                        _make_name_node(name=type_name),
                    )
                    item.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def widen_init_param_type_with_specific(
        self,
        *,
        init_method: FunctionDef,
        attr_name: str,
        type_name: str,
    ) -> None:
        """Widen __init__ parameter type to include specific type.

        Args:
            attr_name: Identifier of the attr being resolved.
            init_method: Init method supplied as FunctionDef for this
                operation.
            type_name: Identifier of the type being resolved.

        """
        for param in init_method.args.args:
            if param.arg == attr_name:
                if param.annotation is None:
                    return
                current_type: TypeSource = normalize_source(
                    source=param.annotation,
                )
                if _ast_equals(a=current_type, b=_NONE_OBJECT_NODE):
                    new_annotation: expr = _make_union_node(
                        _make_name_node(name="None"),
                        _make_name_node(name=type_name),
                    )
                    param.annotation = new_annotation
                    self.stats.changed_annotations += 1

    def __post_init__(self) -> None:
        """Initialize synthesis infrastructure."""
        context: ExistingNodeContext = ExistingNodeContext.from_nodes(
            nodes=[
                node
                for node in self.module.body
                if isinstance(node, (Import, ImportFrom, ClassDef))
            ],
        )
        symbol_index: ScriptSymbolIndex = ScriptSymbolIndex.from_context(
            context=context,
        )
        self._synthesis_imports = UsageAwareImportCollector(
            symbol_index=symbol_index,
            existing_import_nodes=[
                node
                for node in self.module.body
                if isinstance(node, (Import, ImportFrom))
            ],
            postponed_annotations=None,
            local_roots=(),
        )
        self._synthesis_resolver = TypeExpressionResolver(
            imports=self._synthesis_imports,
        )

    @staticmethod
    def _infer_protocol_name_from_attribute() -> str | None:
        """Infer a protocol name from an attribute name.

        Returns:
            str | None produced by this operation.

        """
        return None

    @staticmethod
    def _find_super_call_instances(
        *,
        function: FunctionDef,
    ) -> dict[str, set[str]]:
        """Find instance variables from super().__call__() calls.

        Args:
            function: The function examined while find instance variables from
                super().__call__() calls.

        Returns:
            dict[str, set[str]] produced by this operation.

        """
        instance_assignments: dict[str, set[str]] = {}
        for statement in nodes_of_type(root=function, types=(Assign,)):
            if not isinstance(statement.value, Call):
                continue
            call: Call = statement.value
            if not isinstance(call.func, Attribute):
                continue
            if call.func.attr != "__call__":
                continue
            for target in statement.targets:
                if not isinstance(target, Name):
                    continue
                instance_name: str = target.id
                instance_assignments[instance_name] = set()
        return instance_assignments

    @staticmethod
    def _track_instance_aliases(
        *,
        function: FunctionDef,
        instance_assignments: dict[str, set[str]],
    ) -> dict[str, str]:
        """Track aliases of instance variables.

        Args:
            function: The function examined while track aliases of instance
                variables.
            instance_assignments: Instance assignments supplied as dict[str,
                set[str]] for this operation.

        Returns:
            dict[str, str] produced by this operation.

        """
        instance_aliases: dict[str, str] = {}
        for statement in nodes_of_type(root=function, types=(Assign,)):
            if (
                len(statement.targets) == 1
                and isinstance(statement.targets[0], Name)
                and isinstance(statement.value, Name)
                and (statement.value.id in instance_assignments)
            ):
                instance_aliases[statement.targets[0].id] = statement.value.id
        return instance_aliases

    @staticmethod
    def _collect_field_proposals(
        *,
        statement: stmt,
        flow: FunctionTypeEnvironment,
        counts: dict[str, int],
        fields: dict[str, dict[str, AnnAssign]],
        proposals: dict[tuple[str, str], TypeSource],
    ) -> None:
        """Propose narrower NamedTuple fields from a single construction.

        Args:
            counts: Counts supplied as dict[str, int] for this operation.
            fields: Fields supplied as dict[str, dict[str, AnnAssign]] for this
                operation.
            flow: Flow supplied as FunctionTypeEnvironment for this operation.
            proposals: Proposals supplied as dict[tuple[str, str], TypeSource]
                for this operation.
            statement: The statement examined while propose narrower NamedTuple
                fields from a single construction.

        """
        for node in walk_without_classes(node=statement):
            if not isinstance(node, Call):
                continue
            class_name: str | None = callable_name(node=node.func)
            if class_name is None or class_name not in fields:
                continue
            if counts.get(class_name, 0) != 1:
                continue
            entries: dict[str, AnnAssign] = fields[class_name]
            for k in node.keywords:
                if k.arg is None or k.arg not in entries:
                    continue
                inferred: TypeSource | None = infer_expression_type(
                    node=k.value,
                    environment=flow,
                )
                if inferred is None:
                    continue
                current: TypeSource = normalize_source(
                    source=entries[k.arg].annotation,
                )
                if is_narrowing(current=current, candidate=inferred):
                    proposals[class_name, k.arg] = inferred

    @staticmethod
    def _is_concrete_type(*, node: expr) -> bool:
        """Check if a type node is a concrete type (not None or union).

        Args:
            node: The node examined while check if a type node is a concrete
                type (not None or union).

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(node, Name):
            return node.id != "None"
        return isinstance(node, Subscript)

    @staticmethod
    def _make_union_type(*, left: expr, right: expr) -> Subscript:
        """Create a union type AST node (left | right).

        Args:
            left: Left supplied as expr for this operation.
            right: Right supplied as expr for this operation.

        Returns:
            Subscript produced by this operation.

        """
        return Subscript(
            value=Name(id="Union", ctx=Load()),
            slice=Tuple(elts=[left, right], ctx=Load()),
            ctx=Load(),
        )

    @staticmethod
    def _function_returns_callable(*, function: FunctionDef) -> bool:
        """Check if function returns a Callable.

        Args:
            function: The function examined while check if function returns a
                Callable.

        Returns:
            Whether the requested condition holds.

        """
        if function.returns is None:
            return False
        return_type: TypeSource = normalize_source(source=function.returns)
        return _is_callable_type(node=return_type)

    @staticmethod
    def _function_contains_nested_function(*, function: FunctionDef) -> bool:
        """Check if function contains a nested function definition.

        Args:
            function: The function examined while check if function contains a
                nested function definition.

        Returns:
            Whether the requested condition holds.

        """
        return any(isinstance(item, FunctionDef) for item in function.body)

    @staticmethod
    def _find_init_method(*, class_def: ClassDef) -> FunctionDef | None:
        """Find the __init__ method in a class.

        Args:
            class_def: Class def supplied as ClassDef for this operation.

        Returns:
            FunctionDef | None produced by this operation.

        """
        for item in class_def.body:
            if isinstance(item, FunctionDef) and item.name == "__init__":
                return item
        return None

    @staticmethod
    def _get_class_attribute_assignments(
        *,
        class_def: ClassDef,
    ) -> dict[str, expr]:
        """Get attribute assignments from class body.

        Args:
            class_def: Class def supplied as ClassDef for this operation.

        Returns:
            dict[str, expr] produced by this operation.

        """
        assignments: dict[str, expr] = {}
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.value is not None)
            ):
                assignments[item.target.id] = item.value
            elif isinstance(item, Assign):
                for target in item.targets:
                    if isinstance(target, Name):
                        assignments[target.id] = item.value
        return assignments

    @staticmethod
    def _get_init_assignments(*, init_method: FunctionDef) -> dict[str, expr]:
        """Get self.attribute assignments from __init__.

        Args:
            init_method: Init method supplied as FunctionDef for this
                operation.

        Returns:
            dict[str, expr] produced by this operation.

        """
        assignments: dict[str, expr] = {}
        for statement in init_method.body:
            if isinstance(statement, Assign):
                for target in statement.targets:
                    if (
                        isinstance(target, Attribute)
                        and isinstance(target.value, Name)
                        and (target.value.id == "self")
                    ):
                        assignments[target.attr] = statement.value
        return assignments

    @staticmethod
    def _get_init_conditional_assignments(
        *,
        init_method: FunctionDef,
    ) -> dict[str, expr]:
        """Get conditional expressions in __init__ that assign to attrs.

        Args:
            init_method: Init method supplied as FunctionDef for this
                operation.

        Returns:
            dict[str, expr] produced by this operation.

        """
        assignments: dict[str, expr] = {}
        for statement in init_method.body:
            if isinstance(statement, Assign):
                for target in statement.targets:
                    if (
                        isinstance(target, Attribute)
                        and isinstance(target.value, Name)
                        and (target.value.id == "self")
                        and isinstance(statement.value, IfExp)
                    ):
                        assignments[target.attr] = statement.value
        return assignments

    @staticmethod
    def _is_none_value(*, value: expr) -> bool:
        """Check if a value is None.

        Args:
            value: The value examined while check if a value is None.

        Returns:
            Whether the requested condition holds.

        """
        return isinstance(value, Constant) and value.value is None

    @staticmethod
    def _infer_value_type(*, value: expr) -> str | None:
        """Infer the type of a value expression.

        Args:
            value: The value examined while infer the type of a value
                expression.

        Returns:
            str | None produced by this operation.

        """
        if isinstance(value, Constant):
            if isinstance(value.value, int):
                return "int"
            if isinstance(value.value, str):
                return "str"
        if isinstance(value, List):
            return "list"
        if isinstance(value, Dict):
            return "dict"
        if isinstance(value, Name):
            return "object"
        return None

    @staticmethod
    def _seed_environment_from_parameters(
        *,
        function: FunctionDef,
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Seed local evidence from annotated parameters.

        Args:
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            function: The function examined while seed local evidence from
                annotated parameters.

        """
        parameter: arg
        for parameter in function.args.posonlyargs:
            _seed_parameter(parameter=parameter, environment=environment)
        for parameter in function.args.args:
            _seed_parameter(parameter=parameter, environment=environment)
        for parameter in function.args.kwonlyargs:
            _seed_parameter(parameter=parameter, environment=environment)

    @staticmethod
    def _seed_from_simple_assign(
        *,
        statement: Assign,
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Seed environment from simple name-to-name assignments.

        Args:
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            statement: The statement examined while seed environment from
                simple name-to-name assignments.

        """
        if (
            len(statement.targets) == 1
            and isinstance(statement.targets[0], Name)
            and isinstance(statement.value, Name)
        ):
            existing_type: TypeSource | None = environment.get(
                name=statement.value.id,
            )
            if existing_type is not None:
                environment.set_if_better(
                    name=statement.targets[0].id,
                    source=existing_type,
                )

    def _insert_synthesis_imports(self) -> None:
        """Insert synthesis-generated imports at the top of the module."""
        import_nodes: tuple[stmt, ...] = self._synthesis_imports.import_nodes()
        if not import_nodes:
            return
        insert_index: int = 0
        for index, node in enumerate(iterable=self.module.body):
            if isinstance(node, (Import, ImportFrom)):
                insert_index = index + 1
            else:
                break
        self.module.body[insert_index:insert_index] = import_nodes

    def _refresh_function_returns(self) -> None:
        """Refresh known function return annotations."""
        for function in self._module_functions():
            if function.returns is not None:
                self.function_returns[function.name] = function.returns

    def _module_functions(self) -> tuple[FunctionDef, ...]:
        """Return all functions in stable AST order.

        Returns:
            tuple[FunctionDef, ...] produced by this operation.

        """
        return tuple(
            node for node in self.module.body if isinstance(node, FunctionDef)
        )

    def _module_classes(self) -> tuple[ClassDef, ...]:
        """Return all class definitions in stable AST order.

        Returns:
            tuple[ClassDef, ...] produced by this operation.

        """
        return tuple(
            node for node in self.module.body if isinstance(node, ClassDef)
        )

    def _refine_class_methods(self) -> None:
        """Refine method annotations from class-local attribute evidence."""
        for class_node in self._all_classes():
            attributes: dict[str, TypeSource] = class_instance_attributes(
                class_node=class_node,
            )
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                environment: FunctionTypeEnvironment = FunctionTypeEnvironment(
                    names={**attributes},
                )
                self._refine_function(
                    function=item,
                    parent_environment=environment,
                )

    def _refine_self_returns(self) -> None:
        """Refine fluent instance methods that return ``self`` to ``Self``."""
        changed: bool = False
        for class_node in self._all_classes():
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                if item.returns is None or not returns_self(function=item):
                    continue
                current: TypeSource = normalize_source(source=item.returns)
                if _ast_equals(
                    a=current,
                    b=Constants.self_node,
                ) or _ast_equals(a=current, b=Constants.none_node):
                    continue
                if not _ast_equals(a=current, b=Constants.object_node) and (
                    not (
                        isinstance(current, Name)
                        and current.id == class_node.name
                    )
                ):
                    continue
                item.returns = _make_name_node(name="Self")
                self.function_returns[item.name] = Constants.self_node
                self.stats.changed_returns += 1
                changed = True
        if changed:
            ensure_imported_name(
                module=self.module,
                module_name="typing",
                imported_name="Self",
            )

    def _refine_descriptor_signatures(self) -> None:
        """Refine standard descriptor method signatures."""
        for class_node in self._all_classes():
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                if item.name != "__get__":
                    continue
                objtype_parameter: arg | None = next(
                    (p for p in item.args.args if p.arg == "objtype"),
                    None,
                )
                if objtype_parameter is None:
                    continue
                if objtype_parameter.annotation is None:
                    continue
                current: TypeSource = normalize_source(
                    source=objtype_parameter.annotation,
                )
                if current == Constants.object_node:
                    objtype_parameter.annotation = _make_subscript_node(
                        value=_make_name_node(name="type"),
                        slice_expr=_make_name_node(name="object"),
                    )
                    self.stats.changed_annotations += 1
                elif _ast_equals(
                    a=current,
                    b=_make_bit_or_node(
                        left=Constants.int_node,
                        right=Constants.none_node,
                    ),
                ) or _ast_equals(
                    a=current,
                    b=_make_bit_or_node(
                        left=Constants.none_node,
                        right=Constants.int_node,
                    ),
                ):
                    objtype_parameter.annotation = _make_bit_or_node(
                        left=_make_subscript_node(
                            value=_make_name_node(name="type"),
                            slice_expr=_make_name_node(name="object"),
                        ),
                        right=_make_name_node(name="None"),
                    )
                    self.stats.changed_annotations += 1

    def _refine_property_setter_parameters(self) -> None:
        """Refine property setter parameters from attribute types."""
        for class_node in self._all_classes():
            class_attributes: dict[str, TypeSource] = (
                class_instance_attributes(class_node=class_node)
            )
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                if not has_decorator(function=item, decorator_name="setter"):
                    continue
                self._refine_single_property_setter(
                    function=item,
                    class_attributes=class_attributes,
                )

    def _refine_single_property_setter(
        self,
        *,
        function: FunctionDef,
        class_attributes: dict[str, TypeSource],
    ) -> None:
        """Refine a single property setter's parameters.

        Args:
            class_attributes: Class attributes supplied as dict[str,
                TypeSource] for this operation.
            function: The function examined while refine a single property
                setter's parameters.

        """
        attr_to_param: dict[str, str] = self_attr_assignment_param_map(
            function=function,
        )
        for attr_name, param_name in attr_to_param.items():
            attr_key: str = f"self.{attr_name}"
            if attr_key not in class_attributes:
                continue
            attr_type: TypeSource = class_attributes[attr_key]
            if _ast_equals(
                a=normalize_source(source=attr_type),
                b=Constants.object_node,
            ):
                continue
            for parameter in function.args.args:
                if parameter.arg != param_name:
                    continue
                if parameter.annotation is None:
                    parameter.annotation = attr_type
                    self.stats.changed_annotations += 1
                else:
                    current: TypeSource = normalize_source(
                        source=parameter.annotation,
                    )
                    if _ast_equals(a=current, b=Constants.object_node):
                        parameter.annotation = attr_type
                        self.stats.changed_annotations += 1

    def _refine_identity_class_decorators(self) -> None:
        """Refine class decorators that return the same class object."""
        changed: bool = False
        for function in all_functions(module=self.module):
            if not is_identity_class_decorator(function=function):
                continue
            parameter: arg | None = next(
                (p for p in function.args.args if p.arg == "cls"),
                None,
            )
            if parameter is None:
                continue
            parameter_annotation: expr | None = parameter.annotation
            return_annotation: expr | None = function.returns
            if parameter_annotation is None or return_annotation is None:
                continue
            type_t_node: expr = _make_type_subscript(
                name="type",
                param=_make_name_node(name="T"),
            )
            parameter.annotation = type_t_node
            function.returns = type_t_node
            set_function_type_parameter(function=function, name="T")
            self._refine_identity_decorator_body(function=function)
            self.function_returns[function.name] = type_t_node
            self.stats.changed_annotations += 1
            self.stats.changed_returns += 1
            changed = True
        if changed:
            ensure_imported_name(
                module=self.module,
                module_name="typing",
                imported_name="TypeVar",
            )

    def _refine_proxy_class_decorators(self) -> None:
        """Refine class decorators that wrap classes in a proxy class."""
        changed: bool = False
        for function in all_functions(module=self.module):
            target: _ProxyTarget | None = _proxy_decorator_target(
                function=function,
            )
            if target is None:
                continue
            self._apply_proxy_decorator(function=function, target=target)
            changed = True
        if changed:
            ensure_imported_name(
                module=self.module,
                module_name="typing",
                imported_name="TypeVar",
            )

    def _apply_proxy_decorator(
        self,
        *,
        function: FunctionDef,
        target: _ProxyTarget,
    ) -> None:
        """Rewrite a proxy decorator's signature and instance typing.

        Args:
            function: The function examined while rewrite a proxy decorator's
                signature and instance typing.
            target: The target examined while rewrite a proxy decorator's
                signature and instance typing.

        """
        type_t_node: expr = _make_type_subscript(
            name="type",
            param=_make_name_node(name="T"),
        )
        target.parameter.annotation = type_t_node
        function.returns = type_t_node
        set_function_type_parameter(function=function, name="T")
        self._cast_proxy_return(
            function=function,
            wrapper_class=target.wrapper_class,
        )
        self._retarget_instance_annotations(target=target)
        self.function_returns[function.name] = _make_name_node(name="type")
        self.stats.changed_annotations += 1
        self.stats.changed_returns += 1

    def _cast_proxy_return(
        self,
        *,
        function: FunctionDef,
        wrapper_class: ClassDef,
    ) -> None:
        """Wrap ``return Wrapper`` in a ``cast`` to ``type[T]``.

        Args:
            function: The function examined while wrap ``return Wrapper`` in a
                ``cast`` to ``type[T]``.
            wrapper_class: Wrapper class supplied as ClassDef for this
                operation.

        """
        for node in function.body:
            if (
                isinstance(node, Return)
                and isinstance(node.value, Name)
                and (node.value.id == wrapper_class.name)
            ):
                ensure_imported_name(
                    module=self.module,
                    module_name="typing",
                    imported_name="cast",
                )
                node.value = Call(
                    func=_make_name_node(name="cast"),
                    args=[Constant(value="type[T]"), node.value],
                    keywords=[],
                )
                self.stats.changed_returns += 1
                break

    def _retarget_instance_annotations(self, *, target: _ProxyTarget) -> None:
        """Type ``instance`` annotations in the proxy wrapper as ``T``.

        Args:
            target: The target examined while type ``instance`` annotations in
                the proxy wrapper as ``T``.

        """
        candidates: tuple[AST, ...] = (
            *walk_without_classes(node=target.init_method),
            *target.wrapper_class.body,
        )
        for node in candidates:
            if (
                isinstance(node, AnnAssign)
                and isinstance(node.target, Name)
                and (node.target.id == "instance")
                and (
                    not _ast_equals(
                        a=normalize_source(source=node.annotation),
                        b=_make_name_node(name="T"),
                    )
                )
            ):
                node.annotation = _make_name_node(name="T")
                self.stats.changed_annotations += 1

    def _refine_identity_decorator_body(
        self,
        *,
        function: FunctionDef,
    ) -> None:
        """Refine local variables/functions inside identity decorators.

        Args:
            function: The function examined while refine local
                variables/functions inside identity decorators.

        """
        for node in walk_without_classes(node=function):
            if isinstance(node, AnnAssign):
                current: TypeSource = normalize_source(source=node.annotation)
                if _ast_equals(
                    a=current,
                    b=Constants.type_object_node,
                ) or _ast_equals(a=current, b=Constants.object_node):
                    node.annotation = _make_type_subscript(
                        name="type",
                        param=_make_name_node(name="T"),
                    )
                    self.stats.changed_annotations += 1
            if not isinstance(node, FunctionDef):
                continue
            first_parameter: arg | None = next(
                (p for p in node.args.args if p.arg == "self"),
                None,
            )
            if first_parameter is None:
                continue
            if first_parameter.annotation is None:
                continue
            current = normalize_source(source=first_parameter.annotation)
            if not _ast_equals(a=current, b=Constants.object_node):
                continue
            first_parameter.annotation = _make_name_node(name="T")
            self.stats.changed_annotations += 1

    def _refine_singleton_new_returns(self) -> None:
        """Refine singleton-style ``__new__`` methods to return ``Self``."""
        changed: bool = False
        for class_node in self._all_classes():
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                if not is_singleton_new_method(function=item):
                    continue
                return_annotation: expr | None = item.returns
                if return_annotation is None:
                    continue
                item.returns = _make_name_node(name="Self")
                self.function_returns[item.name] = Constants.self_node
                self.stats.changed_returns += 1
                changed = True
        if changed:
            ensure_imported_name(
                module=self.module,
                module_name="typing",
                imported_name="Self",
            )

    def _refine_nested_numeric_attributes(self) -> None:
        """Refine nested object lists used in arithmetic matrix patterns."""
        for class_node in self._all_classes():
            if not class_has_nested_numeric_evidence(class_node=class_node):
                continue
            for item in class_node.body:
                if not isinstance(item, FunctionDef):
                    continue
                self._refine_nested_numeric_function(function=item)

    def _refine_nested_numeric_function(
        self,
        *,
        function: FunctionDef,
    ) -> None:
        """Refine nested numeric list annotations inside one function.

        Args:
            function: The function examined while refine nested numeric list
                annotations inside one function.

        """
        for parameter in function_parameters(function=function):
            if refine_nested_numeric_parameter(parameter=parameter):
                self.stats.changed_annotations += 1
        for node in iter_child_statements(statement=function):
            if not isinstance(node, AnnAssign):
                continue
            if refine_nested_numeric_assignment(assignment=node):
                self.stats.changed_annotations += 1

    def _refine_protocol_attributes(self) -> None:
        """Refine protocol attributes from typed receiver assignments."""
        protocol_attributes: dict[str, dict[str, AnnAssign]] = (
            protocol_attribute_annotations(module=self.module)
        )
        if not protocol_attributes:
            return
        receiver_types: dict[str, TypeSource] = name_annotation_sources(
            module=self.module,
        )
        for statement in iter_assignment_nodes(module=self.module):
            target: Attribute | None = assignment_attribute_target(
                node=statement,
            )
            if target is None or not isinstance(target.value, Name):
                continue
            protocol_name: TypeSource | None = receiver_types.get(
                target.value.id,
            )
            if protocol_name is None:
                continue
            if isinstance(protocol_name, Name):
                protocol_name_str: str = protocol_name.id
            else:
                protocol_name_str = _ast_node_to_string(node=protocol_name)
            attributes: dict[str, AnnAssign] | None = protocol_attributes.get(
                protocol_name_str,
            )
            if attributes is None or target.attr not in attributes:
                continue
            value: AST | None = assignment_value(node=statement)
            if value is None:
                continue
            candidate: TypeSource | None = infer_expression_type(
                node=value,
                environment=FunctionTypeEnvironment(),
            )
            if candidate is None:
                continue
            annotation: AnnAssign = attributes[target.attr]
            current: TypeSource = annotation.annotation
            if not should_replace_type(current=current, candidate=candidate):
                continue
            annotation.annotation = candidate
            self.stats.changed_annotations += 1

    def _refine_callable_parameter_signatures(self) -> None:
        """Refine ``Callable[..., R]`` parameters from direct calls."""
        for function in all_functions(module=self.module):
            environment: FunctionTypeEnvironment = FunctionTypeEnvironment()
            self._seed_environment_from_parameters(
                function=function,
                environment=environment,
            )
            self._seed_environment_from_body(
                body=function.body,
                environment=environment,
            )
            for parameter in function_parameters(function=function):
                candidate: TypeSource | None = callable_parameter_candidate(
                    function=function,
                    parameter=parameter,
                    environment=environment,
                )
                if candidate is None or parameter.annotation is None:
                    continue
                current: TypeSource = parameter.annotation
                if not should_replace_callable_signature(
                    current=current,
                    candidate=candidate,
                ):
                    continue
                parameter.annotation = candidate
                self.stats.changed_annotations += 1

    def _refine_misassigned_callable_annotations(self) -> None:
        """Fix variables typed as Callable but assigned call results."""
        for node in iter_assignment_nodes(module=self.module):
            if not isinstance(node, AnnAssign) or not isinstance(
                node.target,
                Name,
            ):
                continue
            self._refine_misassigned_callable(node=node)

    def _refine_misassigned_callable(self, *, node: AnnAssign) -> None:
        """Correct one Callable-annotated name holding a call result.

        Args:
            node: The node examined while correct one Callable-annotated name
                holding a call result.

        """
        current: TypeSource = normalize_source(source=node.annotation)
        if not isinstance(node.value, Call):
            return
        if (
            _is_callable_type(node=current)
            and isinstance(current, Subscript)
            and isinstance(current.slice, Tuple)
            and (len(current.slice.elts) == Constants.pair_size)
        ):
            node.annotation = current.slice.elts[1]
            self.stats.changed_annotations += 1
        self._refine_callable_result_annotation(node=node)

    def _refine_callable_result_annotation(self, *, node: AnnAssign) -> None:
        """Adopt a callable-returning function's signature as annotation.

        Args:
            node: The node examined while adopt a callable-returning function's
                signature as annotation.

        """
        value: expr | None = node.value
        if not isinstance(value, Call) or not isinstance(value.func, Name):
            return
        for function in all_functions(module=self.module):
            if (
                function.name == value.func.id
                and function.returns is not None
                and _is_callable_type(node=function.returns)
            ):
                node.annotation = function.returns
                self.stats.changed_annotations += 1
                break

    def _refine_returned_local_callables(self) -> None:
        """Refine functions returning local functions from their signatures."""
        for function in all_functions(module=self.module):
            local_signatures: dict[str, TypeSource] = {
                item.name: function_signature_source(function=item)
                for item in function.body
                if isinstance(item, FunctionDef)
            }
            if not local_signatures:
                continue
            candidate: TypeSource | None = returned_local_callable_type(
                function=function,
                local_signatures=local_signatures,
            )
            if candidate is None or function.returns is None:
                continue
            current: TypeSource = function.returns
            if not should_replace_callable_signature(
                current=current,
                candidate=candidate,
            ):
                continue
            function.returns = candidate
            self.function_returns[function.name] = candidate
            self.stats.changed_returns += 1

    def _refine_contextmanager_returns(self) -> None:
        """Expose ``@contextmanager`` functions as ``Generator[T]`` APIs."""
        changed: bool = False
        for function in self._module_functions():
            candidate: TypeSource | None = contextmanager_api_return(
                function=function,
            )
            if candidate is None or function.returns is None:
                continue
            current: TypeSource = function.returns
            if _ast_equals(a=normalize_source(source=current), b=candidate):
                continue
            function.returns = candidate
            self.function_returns[function.name] = candidate
            self.stats.changed_returns += 1
            changed = True
        if changed:
            ensure_imported_name(
                module=self.module,
                module_name="collections.abc",
                imported_name="Generator",
            )

    def _refine_returned_class_bases(self) -> None:
        """Annotate factories that return a known-base class as ``type[Base]``.

        A function whose body defines and returns a single class that
        subclasses a module-level class keeps that base in its return type,
        e.g. ``type[AbstractBase]`` instead of the broader ``type[object]``.
        """
        available: frozenset[str] = module_class_names(module=self.module)
        for function in self._module_functions():
            if function.returns is None:
                continue
            base: str | None = returned_class_base(
                function=function,
                available_names=available,
            )
            if base is None:
                continue
            candidate: TypeSource = _make_type_subscript(
                name="type",
                param=_make_name_node(name=base),
            )
            current: TypeSource = normalize_source(source=function.returns)
            if not (
                _ast_equals(a=current, b=_make_name_node(name="type"))
                or _ast_equals(a=current, b=Constants.type_object_node)
            ):
                continue
            function.returns = candidate
            self.function_returns[function.name] = candidate
            self.stats.changed_returns += 1

    def _refine_metaclass_signatures(self) -> None:
        """Annotate metaclass ``__new__`` first parameter as ``type[Meta]``."""
        for class_node in self._all_classes():
            if not class_has_base(class_node=class_node, base_name="type"):
                continue
            for item in class_node.body:
                if not isinstance(item, FunctionDef) or item.name != "__new__":
                    continue
                first: arg | None = next(
                    (p for p in item.args.args if p.arg == "cls"),
                    None,
                )
                if first is None:
                    continue
                if first.annotation is not None:
                    continue
                first.annotation = _make_type_subscript(
                    name="type",
                    param=_make_name_node(name=class_node.name),
                )
                self.stats.changed_annotations += 1

    def _refine_metaclass_call_protocols(self) -> None:
        """Refine metaclass ``__call__`` to cast instances to Protocols."""
        for class_node in self._all_classes():
            if not class_has_base(class_node=class_node, base_name="type"):
                continue
            for item in class_node.body:
                if (
                    not isinstance(item, FunctionDef)
                    or item.name != "__call__"
                ):
                    continue
                self._refine_metaclass_call_body(function=item)

    def _refine_metaclass_call_body(self, *, function: FunctionDef) -> None:
        """Refine a single metaclass __call__ method body.

        Args:
            function: The function examined while refine a single metaclass
                __call__ method body.

        """
        instance_assignments: dict[str, set[str]] = (
            self._collect_instance_assignments(function=function)
        )
        for instance_name, attrs in instance_assignments.items():
            if not attrs:
                continue
            protocol_name: str | None = (
                self._infer_protocol_name_from_attribute()
            )
            if protocol_name is None:
                continue
            self.add_cast_to_instance(
                function=function,
                instance_name=instance_name,
                protocol_name=protocol_name,
            )
            self.annotate_instance_aliases(
                function=function,
                instance_name=instance_name,
                protocol_name=protocol_name,
            )
            break

    def _collect_instance_assignments(
        self,
        *,
        function: FunctionDef,
    ) -> dict[str, set[str]]:
        """Collect instance variable names and their assigned attributes.

        Args:
            function: The function examined while collect instance variable
                names and their assigned attributes.

        Returns:
            dict[str, set[str]] produced by this operation.

        """
        instance_assignments: dict[str, set[str]] = (
            self._find_super_call_instances(function=function)
        )
        self._add_attribute_assignments(
            function=function,
            instance_assignments=instance_assignments,
        )
        return instance_assignments

    def _add_attribute_assignments(
        self,
        *,
        function: FunctionDef,
        instance_assignments: dict[str, set[str]],
    ) -> None:
        """Add attribute assignments to instance variables.

        Args:
            function: The function examined while add attribute assignments to
                instance variables.
            instance_assignments: Instance assignments supplied as dict[str,
                set[str]] for this operation.

        """
        instance_aliases: dict[str, str] = self._track_instance_aliases(
            function=function,
            instance_assignments=instance_assignments,
        )
        for statement in nodes_of_type(root=function, types=(Assign,)):
            for target in statement.targets:
                if not isinstance(target, Attribute):
                    continue
                if not isinstance(target.value, Name):
                    continue
                var_name: str = target.value.id
                if var_name in instance_assignments:
                    instance_assignments[var_name].add(target.attr)
                if var_name in instance_aliases:
                    instance_assignments[instance_aliases[var_name]].add(
                        target.attr,
                    )

    def _refine_linear_flow(self) -> None:
        """Narrow single-assignment locals and single-build NamedTuples.

        Each function body is walked in order, tracking the concrete type most
        recently assigned to every local. A union-typed annotation copied from
        such a local is narrowed to that concrete type, and a NamedTuple built
        exactly once is narrowed to its construction argument types.
        """
        counts: dict[str, int] = self._construction_counts()
        fields: dict[str, dict[str, AnnAssign]] = self._namedtuple_fields()
        proposals: dict[tuple[str, str], TypeSource] = {}
        for function in self._module_functions():
            self._narrow_function_flow(
                function=function,
                counts=counts,
                fields=fields,
                proposals=proposals,
            )
        for (class_name, field_name), source in proposals.items():
            node: AnnAssign = fields[class_name][field_name]
            node.annotation = source
            self.stats.changed_annotations += 1

    def _annotate_bare_assignments(self) -> None:
        """Annotate single-assignment locals whose value type is inferable.

        Only names assigned exactly once at a function's top level are
        annotated, which avoids redeclaring a variable that legitimately
        changes type across the body (e.g. ``evolving_value``).
        """
        for function in all_functions(module=self.module):
            environment: FunctionTypeEnvironment = FunctionTypeEnvironment()
            self._seed_environment_from_parameters(
                function=function,
                environment=environment,
            )
            self._seed_environment_from_body(
                body=function.body,
                environment=environment,
            )
            counts: dict[str, int] = top_level_target_counts(
                body=function.body,
            )
            for parameter in function_parameters(function=function):
                counts[parameter.arg] = counts.get(parameter.arg, 0) + 1
            function.body = self._annotate_assignment_body(
                body=function.body,
                environment=environment,
                counts=counts,
            )
            function.body = self._annotate_simple_assignments(
                body=function.body,
                environment=environment,
                counts=counts,
            )

    def _annotate_assignment_body(
        self,
        *,
        body: list[stmt],
        environment: FunctionTypeEnvironment,
        counts: dict[str, int],
    ) -> list[stmt]:
        """Return a body with eligible bare assignments annotated.

        Args:
            body: Body supplied as list[stmt] for this operation.
            counts: Counts supplied as dict[str, int] for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.

        Returns:
            list[stmt] produced by this operation.

        """
        new_body: list[stmt] = []
        for item in body:
            annotated: AnnAssign | None = self._bare_assignment_annotation(
                statement=item,
                environment=environment,
                counts=counts,
            )
            new_body.append(annotated if annotated is not None else item)
        return new_body

    def _bare_assignment_annotation(
        self,
        *,
        statement: stmt,
        environment: FunctionTypeEnvironment,
        counts: dict[str, int],
    ) -> AnnAssign | None:
        """Return an annotated assignment for an eligible bare assignment.

        Args:
            counts: Counts supplied as dict[str, int] for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            statement: The statement examined while return an annotated
                assignment for an eligible bare assignment.

        Returns:
            AnnAssign | None produced by this operation.

        """
        if (
            not isinstance(statement, Assign)
            or len(statement.targets) != 1
            or (not isinstance(statement.targets[0], Name))
        ):
            return None
        target: Name = statement.targets[0]
        if counts.get(target.id, 0) != 1:
            return None
        candidate: TypeSource | None = self._infer_assignment_value(
            value=statement.value,
            environment=environment,
        )
        if candidate is None:
            return None
        environment.set_if_better(name=target.id, source=candidate)
        self.stats.changed_annotations += 1
        annotated: AnnAssign = AnnAssign(
            target=target,
            annotation=candidate,
            value=statement.value,
            simple=1,
        )
        return annotated

    def _annotate_simple_assignments(
        self,
        *,
        body: list[stmt],
        environment: FunctionTypeEnvironment,
        counts: dict[str, int],
    ) -> list[stmt]:
        """Annotate simple name-to-name assignments with the source type.

        Args:
            body: Body supplied as list[stmt] for this operation.
            counts: Counts supplied as dict[str, int] for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.

        Returns:
            list[stmt] produced by this operation.

        """
        new_body: list[stmt] = []
        for item in body:
            if (
                isinstance(item, Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], Name)
                and isinstance(item.value, Name)
            ):
                target: Name = item.targets[0]
                if counts.get(target.id, 0) == 1:
                    source_type: TypeSource | None = environment.get(
                        name=item.value.id,
                    )
                    if source_type is not None:
                        environment.set_if_better(
                            name=target.id,
                            source=source_type,
                        )
                        annotated: AnnAssign = AnnAssign(
                            target=target,
                            annotation=source_type,
                            value=item.value,
                            simple=1,
                        )
                        new_body.append(annotated)
                        self.stats.changed_annotations += 1
                        continue
            new_body.append(item)
        return new_body

    def _construction_counts(self) -> dict[str, int]:
        """Count module-wide call sites keyed by callable name.

        Returns:
            dict[str, int] produced by this operation.

        """
        counts: dict[str, int] = {}
        for node in nodes_of_type(root=self.module, types=(Call,)):
            name: str | None = callable_name(node=node.func)
            if name is not None:
                counts[name] = counts.get(name, 0) + 1
        return counts

    def _namedtuple_fields(self) -> dict[str, dict[str, AnnAssign]]:
        """Map each NamedTuple class to its field annotation nodes.

        Returns:
            dict[str, dict[str, AnnAssign]] produced by this operation.

        """
        result: dict[str, dict[str, AnnAssign]] = {}
        for class_node in ast_classes(module=self.module):
            if not class_has_base(
                class_node=class_node,
                base_name="NamedTuple",
            ):
                continue
            entries: dict[str, AnnAssign] = {}
            for item in class_node.body:
                if isinstance(item, AnnAssign) and isinstance(
                    item.target,
                    Name,
                ):
                    entries[item.target.id] = item
            result[class_node.name] = entries
        return result

    def _narrow_function_flow(
        self,
        *,
        function: FunctionDef,
        counts: dict[str, int],
        fields: dict[str, dict[str, AnnAssign]],
        proposals: dict[tuple[str, str], TypeSource],
    ) -> None:
        """Narrow locals and collect field proposals for one function body.

        Args:
            counts: Counts supplied as dict[str, int] for this operation.
            fields: Fields supplied as dict[str, dict[str, AnnAssign]] for this
                operation.
            function: The function examined while narrow locals and collect
                field proposals for one function body.
            proposals: Proposals supplied as dict[tuple[str, str], TypeSource]
                for this operation.

        """
        flow: FunctionTypeEnvironment = FunctionTypeEnvironment()
        for statement in function.body:
            if isinstance(statement, FunctionDef | ClassDef):
                continue
            self._update_flow(statement=statement, flow=flow)
            self._collect_field_proposals(
                statement=statement,
                flow=flow,
                counts=counts,
                fields=fields,
                proposals=proposals,
            )

    def _update_flow(
        self,
        *,
        statement: stmt,
        flow: FunctionTypeEnvironment,
    ) -> None:
        """Track the latest concrete type assigned to each local name.

        Args:
            flow: Flow supplied as FunctionTypeEnvironment for this operation.
            statement: The statement examined while track the latest concrete
                type assigned to each local name.

        """
        if isinstance(statement, Assign):
            if len(statement.targets) == 1 and isinstance(
                statement.targets[0],
                Name,
            ):
                inferred: TypeSource | None = self._infer_assignment_value(
                    value=statement.value,
                    environment=flow,
                )
                if inferred is not None:
                    flow.names[statement.targets[0].id] = inferred
            return
        if not isinstance(statement, AnnAssign):
            return
        name: str | None = name_from_target(node=statement.target)
        if name is None:
            return
        current: TypeSource = normalize_source(source=statement.annotation)
        if isinstance(statement.value, Name):
            src_type: TypeSource | None = flow.get(name=statement.value.id)
            if (
                src_type is not None
                and src_type != Constants.none_node
                and is_union(source=current)
                and is_narrowing(current=current, candidate=src_type)
            ):
                statement.annotation = src_type
                self.stats.changed_annotations += 1
                flow.names[name] = src_type
                return
        inferred = (
            self._infer_assignment_value(
                value=statement.value,
                environment=flow,
            )
            if statement.value is not None
            else None
        )
        flow.names[name] = inferred if inferred is not None else current

    def _simplify_generator_annotations(self) -> None:
        """Collapse ``Generator[T, None, None]`` to ``Generator[T]``."""
        for function in all_functions(module=self.module):
            if function.returns is not None:
                function.returns = simplify_generator_annotation(
                    annotation=function.returns,
                )
            for parameter in function_parameters(function=function):
                if parameter.annotation is not None:
                    parameter.annotation = simplify_generator_annotation(
                        annotation=parameter.annotation,
                    )
        for assignment in iter_assignment_nodes(module=self.module):
            if isinstance(assignment, AnnAssign):
                assignment.annotation = simplify_generator_annotation(
                    annotation=assignment.annotation,
                )

    def _refine_list_object_unions(self) -> None:
        """Narrow ``list[object]`` inside unions using sibling evidence."""
        for assignment in iter_assignment_nodes(module=self.module):
            if not isinstance(assignment, AnnAssign):
                continue
            candidate: TypeSource | None = list_object_union_candidate(
                source=assignment.annotation,
            )
            if candidate is None:
                continue
            assignment.annotation = candidate
            self.stats.changed_annotations += 1

    def _alias_heterogeneous_result_returns(self) -> None:
        """Widen heterogeneous result-dictionary returns structurally.

        Functions that build a string-keyed dictionary of mixed value types
        are given the structural widening ``dict[str, object]``. No named
        alias is fabricated: the source does not define one, so inventing a
        name would be specific to a particular corpus rather than agnostic.
        """
        widened: TypeSource = Constants.dict_str_object_node
        for function in self._module_functions():
            if (
                function.returns is None
                or not heterogeneous_result_return_candidate(function=function)
            ):
                continue
            current: TypeSource = normalize_source(source=function.returns)
            if _ast_equals(a=current, b=widened):
                continue
            function.returns = widened
            self.function_returns[function.name] = widened
            self.stats.changed_returns += 1

    def _refine_keyword_arguments(self) -> None:
        """Rewrite safe positional calls to keyword-argument calls."""
        changed_calls: int = refine_keyword_arguments(module=self.module)
        self.stats.changed_calls += changed_calls

    def _all_classes(self) -> tuple[ClassDef, ...]:
        """Return all classes, including classes nested in functions.

        Returns:
            tuple[ClassDef, ...] produced by this operation.

        """
        return tuple(
            node
            for node in child_nodes(node=self.module)
            if isinstance(node, ClassDef)
        ) + tuple(
            node
            for top_level in self.module.body
            if isinstance(top_level, FunctionDef)
            for node in child_nodes(node=top_level)
            if isinstance(node, ClassDef)
        )

    def _generate_get_overload_stubs(
        self,
        *,
        method: FunctionDef,
        default_param: arg,
    ) -> list[FunctionDef]:
        """Generate @overload stubs for dict.get method.

        Args:
            default_param: Default param supplied as arg for this operation.
            method: Method supplied as FunctionDef for this operation.

        Returns:
            list[FunctionDef] produced by this operation.

        """
        key_param: arg | None = next(
            (p for p in method.args.args if p.arg == "key"),
            None,
        )
        if key_param is None:
            return []
        if key_param.annotation is None or default_param.annotation is None:
            return []
        ensure_imported_name(
            module=self.module,
            module_name="typing",
            imported_name="overload",
        )
        overload1: FunctionDef = FunctionDef(
            name=method.name,
            args=arguments(
                posonlyargs=[],
                args=[
                    arg(arg="self", annotation=None),
                    arg(arg=key_param.arg, annotation=key_param.annotation),
                    arg(
                        arg=default_param.arg,
                        annotation=Name(id="None", ctx=Load()),
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                vararg=None,
                defaults=[Constant(value=None)],
            ),
            body=[Expr(value=Constant(value=...))],
            decorator_list=[Name(id="overload", ctx=Load())],
            returns=method.returns,
            type_comment=None,
        )
        overload2: FunctionDef = FunctionDef(
            name=method.name,
            args=arguments(
                posonlyargs=[],
                args=[
                    arg(arg="self", annotation=None),
                    arg(arg=key_param.arg, annotation=key_param.annotation),
                    arg(
                        arg=default_param.arg,
                        annotation=default_param.annotation,
                    ),
                ],
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                vararg=None,
                defaults=[],
            ),
            body=[Expr(value=Constant(value=...))],
            decorator_list=[Name(id="overload", ctx=Load())],
            returns=method.returns,
            type_comment=None,
        )
        return [overload1, overload2]

    def _refine_builtin_override_signatures(self) -> None:
        """Fix override signatures in builtin subclass methods."""
        for class_node in self._all_classes():
            for item in tuple(class_node.body):
                if not isinstance(item, FunctionDef) or _has_overload_marker(
                    item=item,
                ):
                    continue
                self._refine_append_override(class_node=class_node, item=item)
                self._refine_get_override(class_node=class_node, item=item)

    def _refine_append_override(
        self,
        *,
        class_node: ClassDef,
        item: FunctionDef,
    ) -> None:
        """Align a custom ``append`` parameter with the element type.

        Args:
            class_node: Class node supplied as ClassDef for this operation.
            item: Item supplied as FunctionDef for this operation.

        """
        if item.name != "append":
            return
        parameter: arg | None = next(
            (p for p in item.args.args if p.arg == "value"),
            None,
        )
        if parameter is None or parameter.annotation is None:
            return
        current: TypeSource = normalize_source(source=parameter.annotation)
        base_element: TypeSource | None = _infer_list_element_type(
            class_node=class_node,
        )
        if base_element is not None and (
            not _ast_equals(a=current, b=base_element)
        ):
            parameter.annotation = base_element
            self.stats.changed_annotations += 1

    def _refine_get_override(
        self,
        *,
        class_node: ClassDef,
        item: FunctionDef,
    ) -> None:
        """Emit overloads when ``get`` narrows the base ``default`` type.

        Args:
            class_node: Class node supplied as ClassDef for this operation.
            item: Item supplied as FunctionDef for this operation.

        """
        if item.name != "get":
            return
        default_param: arg | None = next(
            (p for p in item.args.args if p.arg == "default"),
            None,
        )
        if default_param is None or default_param.annotation is None:
            return
        current_type: TypeSource = normalize_source(
            source=default_param.annotation,
        )
        if not self._is_concrete_type(node=current_type):
            return
        overload_stubs: list[FunctionDef] = self._generate_get_overload_stubs(
            method=item,
            default_param=default_param,
        )
        if not overload_stubs:
            return
        try:
            method_index: int = class_node.body.index(item)
        except ValueError:
            return
        for stub in reversed(overload_stubs):
            class_node.body.insert(method_index, stub)
        default_param.annotation = self._make_union_type(
            left=current_type,
            right=Constants.none_node,
        )
        self.stats.changed_annotations += 1

    def _refine_async_generator_return_types(self) -> None:
        """Fix async generator return types to use 2 parameters."""
        for function in all_async_functions(module=self.module):
            if function.returns is None:
                continue
            current: TypeSource = normalize_source(source=function.returns)
            if is_generic(source=current, base="Generator"):
                gen_args: tuple[TypeSource, ...] = generic_arguments(
                    source=current,
                )
                if len(gen_args) >= 1:
                    async_gen_type: TypeSource = _make_generic_subscript(
                        name="AsyncGenerator",
                        params=[gen_args[0], Constants.none_node],
                    )
                    function.returns = async_gen_type
                    self.stats.changed_returns += 1
            if is_generic(source=current, base="AsyncGenerator"):
                arguments: tuple[TypeSource, ...] = generic_arguments(
                    source=current,
                )
                if len(arguments) == Constants.generator_source_arity:
                    simplified: TypeSource = _make_generic_subscript(
                        name="AsyncGenerator",
                        params=[arguments[0], arguments[1]],
                    )
                    function.returns = simplified
                    self.stats.changed_returns += 1

    def _refine_metaclass_parameter_types(self) -> None:
        """Fix metaclass __new__ parameter types for bases and namespace."""
        for class_node in self._all_classes():
            if not class_has_base(class_node=class_node, base_name="type"):
                continue
            self._refine_metaclass_new_params(class_node=class_node)
            self._refine_metaclass_registry_annotation(class_node=class_node)

    def _refine_metaclass_new_params(self, *, class_node: ClassDef) -> None:
        """Refine __new__ parameter types in metaclasses.

        Args:
            class_node: Class node supplied as ClassDef for this operation.

        """
        for item in class_node.body:
            if not isinstance(item, FunctionDef) or item.name != "__new__":
                continue
            bases_param: arg | None = next(
                (p for p in item.args.args if p.arg == "bases"),
                None,
            )
            namespace_param: arg | None = next(
                (p for p in item.args.args if p.arg == "namespace"),
                None,
            )
            if bases_param is not None and bases_param.annotation is not None:
                self._refine_object_to_tuple_type(parameter=bases_param)
            if (
                namespace_param is not None
                and namespace_param.annotation is not None
            ):
                self._refine_object_to_dict_type(parameter=namespace_param)

    def _refine_object_to_tuple_type(self, *, parameter: arg) -> None:
        """Replace object annotation with tuple[type, ...].

        Args:
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter.annotation is None:
            return
        current: TypeSource = normalize_source(source=parameter.annotation)
        if _ast_equals(a=current, b=Constants.object_node):
            parameter.annotation = _make_generic_subscript(
                name="tuple",
                params=[_make_name_node(name="type"), Constant(value=...)],
            )
            self.stats.changed_annotations += 1

    def _refine_object_to_dict_type(self, *, parameter: arg) -> None:
        """Replace object annotation with dict[str, object].

        Args:
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter.annotation is None:
            return
        current: TypeSource = normalize_source(source=parameter.annotation)
        if _ast_equals(a=current, b=Constants.object_node):
            str_param: expr = _make_name_node(name="str")
            object_param: expr = _make_name_node(name="object")
            parameter.annotation = _make_generic_subscript(
                name="dict",
                params=[str_param, object_param],
            )
            self.stats.changed_annotations += 1

    def _refine_metaclass_registry_annotation(
        self,
        *,
        class_node: ClassDef,
    ) -> None:
        """Refine registry attribute annotation in metaclasses.

        Args:
            class_node: Class node supplied as ClassDef for this operation.

        """
        for class_item in class_node.body:
            if not (
                isinstance(class_item, AnnAssign)
                and isinstance(class_item.target, Name)
                and (class_item.target.id == "registry")
            ):
                continue
            registry_current: TypeSource = normalize_source(
                source=class_item.annotation,
            )
            if _ast_equals(a=registry_current, b=Constants.none_node):
                str_param: expr = _make_name_node(name="str")
                object_param: expr = _make_name_node(name="object")
                dict_node: expr = _make_generic_subscript(
                    name="dict",
                    params=[str_param, object_param],
                )
                none_node: expr = _make_name_node(name="None")
                class_item.annotation = _make_union_node(dict_node, none_node)
                self.stats.changed_annotations += 1

    def _refine_dataclass_like_attributes(self) -> None:
        """Refine dataclass-like attributes based on constructor assignments.

        For classes with attributes initialized to None in the class body
        but assigned other types in __init__, widen the type to a union.
        """
        for class_def in self._module_classes():
            init_method: FunctionDef | None = self._find_init_method(
                class_def=class_def,
            )
            if init_method is None:
                continue
            self._widen_attribute_types_from_init(
                class_def=class_def,
                init_method=init_method,
            )
            self._widen_attribute_types_from_call_sites(
                class_def=class_def,
                init_method=init_method,
            )

    def _refine_class_attributes_from_init(self) -> None:
        """Refine class attribute types from __init__ parameter types.

        For class attributes that are assigned directly from __init__
        parameters with the same name, update the class attribute type to
        match the parameter type.
        """
        for class_def in self._all_classes():
            init_method: FunctionDef | None = self._find_init_method(
                class_def=class_def,
            )
            if init_method is None:
                continue
            param_types: dict[str, expr] = {
                param.arg: param.annotation
                for param in init_method.args.args
                if param.annotation is not None
            }
            for statement in init_method.body:
                self._apply_init_parameter_type(
                    class_def=class_def,
                    statement=statement,
                    param_types=param_types,
                )

    def _apply_init_parameter_type(
        self,
        *,
        class_def: ClassDef,
        statement: stmt,
        param_types: dict[str, expr],
    ) -> None:
        """Copy an ``__init__`` parameter type to a matching attribute.

        Args:
            class_def: Class def supplied as ClassDef for this operation.
            param_types: Param types supplied as dict[str, expr] for this
                operation.
            statement: The statement examined while copy an ``__init__``
                parameter type to a matching attribute.

        """
        if not isinstance(statement, Assign) or len(statement.targets) != 1:
            return
        target: expr = statement.targets[0]
        if not (
            isinstance(target, Attribute)
            and isinstance(target.value, Name)
            and (target.value.id == "self")
            and isinstance(statement.value, Name)
            and (statement.value.id in param_types)
        ):
            return
        self._retarget_class_attribute(
            class_def=class_def,
            attr_name=target.attr,
            annotation=param_types[statement.value.id],
        )

    def _retarget_class_attribute(
        self,
        *,
        class_def: ClassDef,
        attr_name: str,
        annotation: expr,
    ) -> None:
        """Replace a declared class attribute's annotation.

        Args:
            annotation: The annotation examined while replace a declared class
                attribute's annotation.
            attr_name: Identifier of the attr being resolved.
            class_def: Class def supplied as ClassDef for this operation.

        """
        for item in class_def.body:
            if (
                isinstance(item, AnnAssign)
                and isinstance(item.target, Name)
                and (item.target.id == attr_name)
            ):
                item.annotation = annotation
                self.stats.changed_annotations += 1

    def _widen_attribute_types_from_init(
        self,
        *,
        class_def: ClassDef,
        init_method: FunctionDef,
    ) -> None:
        """Widen attribute types based on __init__ assignments.

        Args:
            class_def: Class def supplied as ClassDef for this operation.
            init_method: Init method supplied as FunctionDef for this
                operation.

        """
        attr_assignments: dict[str, expr] = (
            self._get_class_attribute_assignments(class_def=class_def)
        )
        init_assignments: dict[str, expr] = self._get_init_assignments(
            init_method=init_method,
        )
        conditional_assignments: dict[str, expr] = (
            self._get_init_conditional_assignments(init_method=init_method)
        )
        for attr_name, attr_value in attr_assignments.items():
            if attr_name not in init_assignments:
                continue
            init_value: expr = init_assignments[attr_name]
            if not self._is_none_value(value=attr_value):
                continue
            if self._is_none_value(value=init_value):
                continue
            self.widen_attribute_type(
                class_def=class_def,
                attr_name=attr_name,
                init_value=init_value,
            )
            self.widen_init_param_type(
                init_method=init_method,
                attr_name=attr_name,
                init_value=init_value,
            )
        for attr_name, cond_value in conditional_assignments.items():
            if not self._is_none_value(
                value=attr_assignments.get(
                    attr_name,
                    cast(typ="expr", val=Constant(value=None)),
                ),
            ):
                continue
            if isinstance(cond_value, IfExp):
                body_type: str | None = self._infer_value_type(
                    value=cond_value.body,
                )
                orelse_type: str | None = self._infer_value_type(
                    value=cond_value.orelse,
                )
                if body_type and orelse_type and (body_type != orelse_type):
                    self.widen_attribute_type_to_object(
                        class_def=class_def,
                        attr_name=attr_name,
                    )
                    self.widen_init_param_type_to_object(
                        init_method=init_method,
                        attr_name=attr_name,
                    )

    def _widen_attribute_types_from_call_sites(
        self,
        *,
        class_def: ClassDef,
        init_method: FunctionDef,
    ) -> None:
        """Widen attribute types based on call site arguments.

        Args:
            class_def: Class def supplied as ClassDef for this operation.
            init_method: Init method supplied as FunctionDef for this
                operation.

        """
        call_sites: list[Call] = self._find_class_call_sites(
            class_name=class_def.name,
        )
        for call in call_sites:
            for keyword_arg in call.keywords:
                if keyword_arg.arg is None:
                    continue
                attr_name: str = keyword_arg.arg
                type_name: str | None = self._infer_value_type(
                    value=keyword_arg.value,
                )
                if type_name:
                    self.widen_attribute_type_with_specific(
                        class_def=class_def,
                        attr_name=attr_name,
                        type_name=type_name,
                    )
                    self.widen_init_param_type_with_specific(
                        init_method=init_method,
                        attr_name=attr_name,
                        type_name=type_name,
                    )

    def _find_class_call_sites(self, *, class_name: str) -> list[Call]:
        """Find all call sites for a class constructor.

        Args:
            class_name: Identifier of the class being resolved.

        Returns:
            list[Call] produced by this operation.

        """
        return [
            node
            for node in nodes_of_type(root=self.module, types=(Call,))
            if isinstance(node.func, Name) and node.func.id == class_name
        ]

    def _refine_function(
        self,
        *,
        function: FunctionDef,
        parent_environment: FunctionTypeEnvironment | None = None,
    ) -> None:
        """Refine annotations inside one function body.

        Args:
            function: The function examined while refine annotations inside one
                function body.
            parent_environment: Parent environment supplied as
                FunctionTypeEnvironment | None for this operation.

        """
        environment: FunctionTypeEnvironment = FunctionTypeEnvironment()
        if parent_environment is not None:
            environment.names.update(parent_environment.names)
        self._seed_environment_from_parameters(
            function=function,
            environment=environment,
        )
        self._seed_environment_from_body(
            body=function.body,
            environment=environment,
        )
        self._refine_body_annotations(
            body=function.body,
            environment=environment,
        )
        self._refine_function_return(
            function=function,
            environment=environment,
        )

    def _seed_environment_from_body(
        self,
        *,
        body: list[stmt],
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Seed local evidence from annotations and simple assignments.

        Args:
            body: Body supplied as list[stmt] for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.

        """
        item: stmt
        for item in body:
            if isinstance(item, AnnAssign):
                var_name: str | None = name_from_target(node=item.target)
                if var_name is not None:
                    environment.set_if_better(
                        name=var_name,
                        source=item.annotation,
                    )
                continue
            if isinstance(item, Assign):
                self._seed_from_simple_assign(
                    statement=item,
                    environment=environment,
                )
                continue
            if isinstance(item, ClassDef):
                environment.set_if_better(
                    name=item.name,
                    source=class_type_source(
                        class_node=item,
                        available_names=module_class_names(module=self.module),
                    ),
                )
                continue
            if isinstance(item, FunctionDef):
                continue
            for nested in iter_child_statements(statement=item):
                if isinstance(nested, AnnAssign):
                    nested_name: str | None = name_from_target(
                        node=nested.target,
                    )
                    if nested_name is not None:
                        environment.set_if_better(
                            name=nested_name,
                            source=nested.annotation,
                        )

    def _refine_body_annotations(
        self,
        *,
        body: list[stmt],
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Refine local annotations from value expressions.

        Args:
            body: Body supplied as list[stmt] for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.

        """
        item: stmt
        for item in body:
            if isinstance(item, AnnAssign):
                self._refine_annassign(
                    assignment=item,
                    environment=environment,
                )
            elif isinstance(item, FunctionDef):
                self._refine_function(
                    function=item,
                    parent_environment=environment,
                )
            else:
                nested: stmt
                for nested in iter_child_statements(statement=item):
                    if isinstance(nested, AnnAssign):
                        self._refine_annassign(
                            assignment=nested,
                            environment=environment,
                        )
                    elif isinstance(nested, FunctionDef):
                        self._refine_function(
                            function=nested,
                            parent_environment=environment,
                        )

    def _refine_annassign(
        self,
        *,
        assignment: AnnAssign,
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Refine one annotated assignment.

        Args:
            assignment: Assignment supplied as AnnAssign for this operation.
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.

        """
        if assignment.value is None:
            return
        candidate: TypeSource | None = self._infer_assignment_value(
            value=assignment.value,
            environment=environment,
        )
        if candidate is None:
            return
        current: TypeSource = assignment.annotation
        if not (
            should_replace_type(current=current, candidate=candidate)
            or should_replace_callable_signature(
                current=current,
                candidate=candidate,
            )
        ):
            return
        assignment.annotation = candidate
        name: str | None = name_from_target(node=assignment.target)
        if name is not None:
            environment.set_if_better(name=name, source=candidate)
        self.stats.changed_annotations += 1

    def _infer_assignment_value(
        self,
        *,
        value: AST,
        environment: FunctionTypeEnvironment,
    ) -> TypeSource | None:
        """Infer assignment value types with known function returns.

        Args:
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            value: The value examined while infer assignment value types with
                known function returns.

        Returns:
            TypeSource | None produced by this operation.

        """
        if isinstance(value, Call):
            name: str | None = callable_name(node=value.func)
            if name is not None and name in self.function_returns:
                return self.function_returns[name]
            globals_name: str | None = globals_subscript_callee(call=value)
            if (
                globals_name is not None
                and globals_name in self.function_returns
            ):
                return self.function_returns[globals_name]
        return infer_expression_type(node=value, environment=environment)

    def _refine_function_return(
        self,
        *,
        function: FunctionDef,
        environment: FunctionTypeEnvironment,
    ) -> None:
        """Refine the return annotation for a function.

        Args:
            environment: Environment supplied as FunctionTypeEnvironment for
                this operation.
            function: The function examined while refine the return annotation
                for a function.

        """
        candidate: TypeSource | None = infer_function_return_type(
            function=function,
            environment=environment,
        )
        if candidate is None or function.returns is None:
            return
        current: TypeSource = function.returns
        if should_keep_broad_return(current=current, candidate=candidate):
            return
        if not should_replace_type(current=current, candidate=candidate):
            return
        function.returns = candidate
        self.function_returns[function.name] = candidate
        self.stats.changed_returns += 1


@dataclass(frozen=True, slots=True)
class RefinementResult:
    """Source plus stats returned by the post-refinement stage.

    Attributes:
        source: Original source text retained for parsing and reconstruction.
        stats: Stats retained as RefinementStats by this instance.

    """

    source: str
    stats: RefinementStats


def refine_inferred_module(*, module: Module) -> RefinementResult:
    """Refine an inferred module using generic AST evidence.

    Args:
        module: The module examined while refine an inferred module using
            generic AST evidence.

    Returns:
        RefinementResult produced by this operation.

    """
    refiner: GenericPostRefiner = GenericPostRefiner(module=module)
    refined: Module = refiner.refine()
    return RefinementResult(
        source=finalize_and_format_module(module=refined),
        stats=refiner.stats,
    )


def infer_function_return_type(
    *,
    function: FunctionDef,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a function return type from explicit return statements.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        function: The function examined while infer a function return type from
            explicit return statements.

    Returns:
        TypeSource | None produced by this operation.

    """
    returns: list[TypeSource] = []
    statement: stmt
    for statement in function.body:
        if isinstance(statement, Return):
            returns.extend(
                inferred_return_sources(
                    value=statement.value,
                    environment=environment,
                ),
            )
        elif not isinstance(statement, FunctionDef):
            nested: stmt
            for nested in iter_child_statements(statement=statement):
                if isinstance(nested, FunctionDef):
                    continue
                if isinstance(nested, Return):
                    returns.extend(
                        inferred_return_sources(
                            value=nested.value,
                            environment=environment,
                        ),
                    )
    if not returns:
        return None
    return merge_sources(sources=tuple(returns))


def inferred_return_sources(
    *,
    value: AST | None,
    environment: FunctionTypeEnvironment,
) -> tuple[TypeSource, ...]:
    """Return inferred type sources for one return expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        value: The value examined while return inferred type sources for one
            return expression.

    Returns:
        tuple[TypeSource, ...] produced by this operation.

    """
    if value is None:
        return (Constants.none_node,)
    if isinstance(value, IfExp):
        body_type: TypeSource | None = infer_expression_type(
            node=value.body,
            environment=environment,
        )
        else_type: TypeSource | None = infer_expression_type(
            node=value.orelse,
            environment=environment,
        )
        return tuple(
            source for source in (body_type, else_type) if source is not None
        )
    inferred: TypeSource | None = infer_expression_type(
        node=value,
        environment=environment,
    )
    return () if inferred is None else (inferred,)


def infer_expression_type(
    *,
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a type source for one expression from local graph evidence.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a type source for one expression
            from local graph evidence.

    Returns:
        TypeSource | None produced by this operation.

    """
    inferer: ExpressionInferer
    for inferer in expression_inferers():
        result: TypeSource | None = inferer(node, environment)
        if result is not None:
            return result
    return None


def expression_inferers() -> tuple[ExpressionInferer, ...]:
    """Return expression inference handlers in precedence order.

    Returns:
        tuple[ExpressionInferer, ...] produced by this operation.

    """
    return (
        infer_constant_expression,
        infer_name_expression,
        infer_attribute_expression,
        infer_list_expression,
        infer_tuple_expression,
        infer_dict_expression,
        infer_dict_comp_expression,
        infer_call_expression,
        infer_subscript_expression,
        infer_if_expression,
        infer_binop_expression,
    )


def infer_constant_expression(
    node: AST,
    _environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a constant expression.

    Args:
        _environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a constant expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Constant):
        return infer_constant_type(node=node)
    return None


def infer_name_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a name expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a name expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Name):
        return environment.get(name=node.id)
    return None


def infer_attribute_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer an attribute expression from local attribute evidence.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer an attribute expression from local
            attribute evidence.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Attribute):
        name: str | None = name_from_target(node=node)
        if name is not None:
            return environment.get(name=name)
    return None


def infer_list_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a list expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a list expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, List):
        return infer_list_literal_type(node=node, environment=environment)
    return None


def infer_tuple_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a tuple expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a tuple expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Tuple):
        return infer_tuple_literal_type(node=node, environment=environment)
    return None


def infer_dict_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a dict expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a dict expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Dict):
        return infer_dict_literal_type(node=node, environment=environment)
    return None


def infer_dict_comp_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a dict-comprehension expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a dict-comprehension expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, DictComp):
        return infer_dict_comprehension_type(
            node=node,
            environment=environment,
        )
    return None


def infer_call_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a call expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a call expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Call):
        return infer_call_type(node=node, environment=environment)
    return None


def infer_subscript_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a subscript expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a subscript expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, Subscript):
        return infer_subscript_type(node=node, environment=environment)
    return None


def infer_if_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a ternary expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a ternary expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, IfExp):
        return merge_sources(
            sources=inferred_return_sources(
                value=node,
                environment=environment,
            ),
        )
    return None


def infer_binop_expression(
    node: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a binary expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a binary expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    if isinstance(node, BinOp):
        return infer_binary_type(node=node, environment=environment)
    return None


def infer_constant_type(*, node: Constant) -> TypeSource:
    """Infer a type source for a literal constant.

    Args:
        node: The node examined while infer a type source for a literal
            constant.

    Returns:
        TypeSource produced by this operation.

    """
    value: object = node.value
    result: TypeSource = Constants.object_node
    if value is None:
        result = Constants.none_node
    elif isinstance(value, bool):
        result = Constants.bool_node
    elif isinstance(value, int):
        result = Constants.int_node
    elif isinstance(value, float):
        result = Constants.float_node
    elif isinstance(value, str):
        result = Constants.str_node
    elif isinstance(value, bytes):
        result = Constants.bytes_node
    return result


def infer_list_literal_type(
    *,
    node: List,
    environment: FunctionTypeEnvironment,
) -> TypeSource:
    """Infer ``list[T]`` from a list literal.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``list[T]`` from a list literal.

    Returns:
        TypeSource produced by this operation.

    """
    element_types: list[TypeSource] = []
    for element in node.elts:
        if isinstance(element, Starred):
            starred_type: TypeSource | None = infer_expression_type(
                node=element.value,
                environment=environment,
            )
            if starred_type is not None:
                element_types.append(element_type(source=starred_type))
            continue
        inferred: TypeSource | None = infer_expression_type(
            node=element,
            environment=environment,
        )
        if inferred is not None:
            element_types.append(inferred)
    if not element_types:
        return Constants.list_object_node
    return _make_generic_subscript(
        name="list",
        params=[merge_sources(sources=tuple(element_types))],
    )


def infer_tuple_literal_type(
    *,
    node: Tuple,
    environment: FunctionTypeEnvironment,
) -> TypeSource:
    """Infer a fixed-length tuple literal.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a fixed-length tuple literal.

    Returns:
        TypeSource produced by this operation.

    """
    element_types: tuple[TypeSource, ...] = tuple(
        infer_expression_type(node=element, environment=environment)
        or Constants.object_node
        for element in node.elts
    )
    return _make_generic_subscript(name="tuple", params=list(element_types))


def infer_dict_literal_type(
    *,
    node: Dict,
    environment: FunctionTypeEnvironment,
) -> TypeSource:
    """Infer ``dict[K, V]`` from a dict literal and unpacking.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``dict[K, V]`` from a dict literal
            and unpacking.

    Returns:
        TypeSource produced by this operation.

    """
    key_types: list[TypeSource] = []
    value_types: list[TypeSource] = []
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None:
            unpacked: TypeSource | None = infer_expression_type(
                node=value,
                environment=environment,
            )
            if unpacked is not None and is_generic(
                source=unpacked,
                base="dict",
            ):
                arguments: tuple[TypeSource, ...] = generic_arguments(
                    source=unpacked,
                )
                if len(arguments) == Constants.pair_size:
                    key_types.append(arguments[0])
                    value_types.append(arguments[1])
            continue
        key_type: TypeSource | None = infer_expression_type(
            node=key,
            environment=environment,
        )
        value_type: TypeSource | None = infer_expression_type(
            node=value,
            environment=environment,
        )
        key_types.append(key_type or Constants.object_node)
        value_types.append(value_type or Constants.object_node)
    return (
        Constants.dict_object_object_node
        if not key_types or not value_types
        else _make_generic_subscript(
            name="dict",
            params=[
                merge_sources(sources=tuple(key_types)),
                merge_sources(sources=tuple(value_types)),
            ],
        )
    )


def infer_dict_comprehension_type(
    *,
    node: DictComp,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a dict comprehension from ``some_dict.items()`` evidence.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer a dict comprehension from
            ``some_dict.items()`` evidence.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not node.generators:
        return None
    generator: comprehension = node.generators[0]
    iterable_type: TypeSource | None = infer_expression_type(
        node=generator.iter,
        environment=environment,
    )
    target_names: tuple[str, ...] = tuple_target_names(node=generator.target)
    if (
        iterable_type is not None
        and len(target_names) == Constants.pair_size
        and is_generic(source=iterable_type, base="Iterable")
    ):
        item_type: TypeSource = generic_arguments(source=iterable_type)[0]
        if is_generic(source=item_type, base="tuple"):
            pair_types: tuple[TypeSource, ...] = generic_arguments(
                source=item_type,
            )
            if len(pair_types) >= Constants.pair_size:
                local_env: FunctionTypeEnvironment = FunctionTypeEnvironment(
                    names={**environment.names},
                )
                local_env.set_if_better(
                    name=target_names[0],
                    source=pair_types[0],
                )
                local_env.set_if_better(
                    name=target_names[1],
                    source=pair_types[1],
                )
                key_type: TypeSource | None = infer_expression_type(
                    node=node.key,
                    environment=local_env,
                )
                value_type: TypeSource | None = infer_expression_type(
                    node=node.value,
                    environment=local_env,
                )
                if key_type is not None and value_type is not None:
                    return _make_generic_subscript(
                        name="dict",
                        params=[key_type, value_type],
                    )
    return None


def infer_call_type(
    *,
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer common call return types.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer common call return types.

    Returns:
        TypeSource | None produced by this operation.

    """
    name: str | None = callable_name(node=node.func)
    if name is None:
        return None
    inferer: CallInferer | None = call_inferers().get(name)
    if inferer is not None:
        return inferer(node=node, environment=environment)
    if isinstance(node.func, Attribute) and node.func.attr == "items":
        return infer_items_call_type(node=node, environment=environment)
    if isinstance(node.func, Name):
        callee_type: TypeSource | None = environment.get(name=node.func.id)
        if callee_type is not None:
            return callable_return_source(source=callee_type)
    return None


def callable_return_source(*, source: TypeSource) -> TypeSource | None:
    """Return the result type ``R`` of a ``Callable[..., R]`` source.

    Args:
        source: The source examined while return the result type ``R`` of a
            ``Callable[..., R]`` source.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not is_generic(source=source, base="Callable"):
        return None
    arguments: tuple[TypeSource, ...] = generic_arguments(source=source)
    if len(arguments) != Constants.pair_size:
        return None
    return arguments[1]


def globals_subscript_callee(*, call: Call) -> str | None:
    """Return the function name in a ``globals()["name"](...)`` call.

    Args:
        call: The call examined while return the function name in a
            ``globals()["name"](...)`` call.

    Returns:
        str | None produced by this operation.

    """
    func: AST = call.func
    if not isinstance(func, Subscript):
        return None
    if not (
        isinstance(func.value, Call)
        and callable_name(node=func.value.func) == "globals"
    ):
        return None
    key: AST = func.slice
    if isinstance(key, Constant) and isinstance(key.value, str):
        return key.value
    return None


def call_inferers() -> dict[str, CallInferer]:
    """Return generic call inference handlers by final callable name.

    Returns:
        dict[str, CallInferer] produced by this operation.

    """
    return {
        "accumulate": infer_first_argument_iterable_call,
        "chain": infer_chain_call,
        "compress": infer_first_argument_iterable_call,
        "dropwhile": infer_second_argument_iterable_call,
        "islice": infer_first_argument_iterable_call,
        "list": infer_list_call,
        "product": infer_tuple_iterable_call,
        "range": infer_range_call,
        "set": infer_set_call,
        "sorted": infer_sorted_call,
        "takewhile": infer_second_argument_iterable_call,
        "tuple": infer_tuple_call,
        "zip": infer_tuple_iterable_call,
        "zip_longest": infer_tuple_iterable_call,
    }


def infer_list_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``list(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``list(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not node.args:
        return Constants.list_object_node
    return list_from_iterable_call_type(
        argument=node.args[0],
        environment=environment,
    )


def infer_range_call(
    *,
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``range(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``range(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    _ = (node, environment)
    return Constants.iterable_int_node


def infer_sorted_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``sorted(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``sorted(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not node.args:
        return None
    iterable_type: TypeSource | None = infer_expression_type(
        node=node.args[0],
        environment=environment,
    )
    if iterable_type is None:
        return None
    return _make_generic_subscript(
        name="list",
        params=[element_type(source=iterable_type)],
    )


def infer_tuple_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``tuple(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``tuple(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not node.args:
        return Constants.tuple_empty_node
    iterable_type: TypeSource | None = infer_expression_type(
        node=node.args[0],
        environment=environment,
    )
    if iterable_type is None:
        return None
    return _make_generic_subscript(
        name="tuple",
        params=[element_type(source=iterable_type), Constants.ellipsis_node],
    )


def infer_set_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``set(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``set(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not node.args:
        return _SET_OBJECT_NODE
    iterable_type: TypeSource | None = infer_expression_type(
        node=node.args[0],
        environment=environment,
    )
    if iterable_type is None:
        return None
    return _make_generic_subscript(
        name="set",
        params=[element_type(source=iterable_type)],
    )


def infer_tuple_iterable_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer tuple-yielding iterable calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer tuple-yielding iterable calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    name: str | None = callable_name(node=node.func)
    if name is None:
        return None
    return iterable_tuple_call_type(
        name=name,
        node=node,
        environment=environment,
    )


def infer_chain_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``chain(...)`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``chain(...)`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    return iterable_union_call_type(node=node, environment=environment)


def infer_first_argument_iterable_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer calls that return an iterable from the first argument.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer calls that return an iterable from
            the first argument.

    Returns:
        TypeSource | None produced by this operation.

    """
    return infer_indexed_argument_iterable_call(
        node=node,
        environment=environment,
        argument_index=0,
    )


def infer_second_argument_iterable_call(
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer calls that return an iterable from the second argument.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer calls that return an iterable from
            the second argument.

    Returns:
        TypeSource | None produced by this operation.

    """
    return infer_indexed_argument_iterable_call(
        node=node,
        environment=environment,
        argument_index=1,
    )


def infer_indexed_argument_iterable_call(
    *,
    node: Call,
    environment: FunctionTypeEnvironment,
    argument_index: int,
) -> TypeSource | None:
    """Infer an iterable result from one indexed argument.

    Args:
        argument_index: Argument index supplied as int for this operation.
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer an iterable result from one indexed
            argument.

    Returns:
        TypeSource | None produced by this operation.

    """
    if len(node.args) <= argument_index:
        return None
    iterable_type: TypeSource | None = infer_expression_type(
        node=node.args[argument_index],
        environment=environment,
    )
    if iterable_type is None:
        return None
    return _make_generic_subscript(
        name="Iterable",
        params=[element_type(source=iterable_type)],
    )


def infer_items_call_type(
    *,
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``dict.items()`` calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer ``dict.items()`` calls.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not isinstance(node.func, Attribute):
        return None
    receiver_type: TypeSource | None = infer_expression_type(
        node=node.func.value,
        environment=environment,
    )
    if receiver_type is None or not is_generic(
        source=receiver_type,
        base="dict",
    ):
        return None
    key_type, value_type = generic_arguments(source=receiver_type)
    return _make_generic_subscript(
        name="Iterable",
        params=[
            _make_generic_subscript(
                name="tuple",
                params=[key_type, value_type],
            ),
        ],
    )


def list_from_iterable_call_type(
    *,
    argument: AST,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer ``list(...)`` from the iterable argument.

    Args:
        argument: Argument supplied as AST for this operation.
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    iterable_type: TypeSource | None = infer_expression_type(
        node=argument,
        environment=environment,
    )
    if iterable_type is None:
        return None
    if is_generic(source=iterable_type, base="Iterable"):
        return _make_generic_subscript(
            name="list",
            params=[generic_arguments(source=iterable_type)[0]],
        )
    if is_generic(source=iterable_type, base="list"):
        return iterable_type
    if is_generic(source=iterable_type, base="tuple"):
        return _make_generic_subscript(
            name="list",
            params=[element_type(source=iterable_type)],
        )
    return None


def iterable_tuple_call_type(
    *,
    name: str,
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer tuple-yielding calls such as zip/product/zip_longest.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        name: Identifier of the name being resolved.
        node: The node examined while infer tuple-yielding calls such as
            zip/product/zip_longest.

    Returns:
        TypeSource | None produced by this operation.

    """
    element_types: list[TypeSource] = []
    argument: AST
    for argument in node.args:
        argument_type: TypeSource | None = infer_expression_type(
            node=argument,
            environment=environment,
        )
        if argument_type is None:
            element_types.append(Constants.object_node)
        else:
            element_types.append(element_type(source=argument_type))
    if not element_types:
        return None
    if name == "zip_longest":
        fillvalue_type: TypeSource = zip_longest_fillvalue_type(node=node)
        element_types = [
            merge_sources(sources=(element_type_source, fillvalue_type))
            for element_type_source in element_types
        ]
    if name == "product" and len(element_types) == 1:
        return _make_generic_subscript(
            name="Iterable",
            params=[
                _make_generic_subscript(
                    name="tuple",
                    params=[element_types[0], Constants.ellipsis_node],
                ),
            ],
        )
    return _make_generic_subscript(
        name="Iterable",
        params=[_make_generic_subscript(name="tuple", params=element_types)],
    )


def iterable_union_call_type(
    *,
    node: Call,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer calls that concatenate several iterables.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer calls that concatenate several
            iterables.

    Returns:
        TypeSource | None produced by this operation.

    """
    element_types: list[TypeSource] = []
    for argument in node.args:
        argument_type: TypeSource | None = infer_expression_type(
            node=argument,
            environment=environment,
        )
        if argument_type is not None:
            element_types.append(element_type(source=argument_type))
    if not element_types:
        return None
    return _make_generic_subscript(
        name="Iterable",
        params=[merge_sources(sources=tuple(element_types))],
    )


def zip_longest_fillvalue_type(*, node: Call) -> TypeSource:
    """Return the fillvalue type for ``itertools.zip_longest``.

    Args:
        node: The node examined while return the fillvalue type for
            ``itertools.zip_longest``.

    Returns:
        TypeSource produced by this operation.

    """
    for k in node.keywords:
        if k.arg == "fillvalue":
            if isinstance(k.value, Constant):
                return infer_constant_type(node=k.value)
            return Constants.object_node
    return Constants.none_node


def infer_subscript_type(
    *,
    node: Subscript,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer the result type of a subscript expression.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer the result type of a subscript
            expression.

    Returns:
        TypeSource | None produced by this operation.

    """
    value_type: TypeSource | None = infer_expression_type(
        node=node.value,
        environment=environment,
    )
    if value_type is None:
        return None
    if is_generic(source=value_type, base="list"):
        return generic_arguments(source=value_type)[0]
    if is_generic(source=value_type, base="dict"):
        return generic_arguments(source=value_type)[1]
    if is_generic(source=value_type, base="tuple"):
        arguments: tuple[TypeSource, ...] = generic_arguments(
            source=value_type,
        )
        if (
            isinstance(node.slice, Constant)
            and isinstance(node.slice.value, int)
            and (0 <= node.slice.value < len(arguments))
        ):
            return arguments[node.slice.value]
        return merge_sources(sources=arguments)
    return None


def infer_binary_type(
    *,
    node: BinOp,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer common binary expression results.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while infer common binary expression results.

    Returns:
        TypeSource | None produced by this operation.

    """
    left: TypeSource | None = infer_expression_type(
        node=node.left,
        environment=environment,
    )
    right: TypeSource | None = infer_expression_type(
        node=node.right,
        environment=environment,
    )
    if left is None or right is None:
        return None
    result: TypeSource | None = None
    if (
        (
            _ast_equals(a=Constants.float_node, b=left)
            or _ast_equals(a=Constants.float_node, b=right)
        )
        and (
            _ast_equals(a=Constants.int_node, b=left)
            or _ast_equals(a=Constants.float_node, b=left)
        )
        and (
            _ast_equals(a=Constants.int_node, b=right)
            or _ast_equals(a=Constants.float_node, b=right)
        )
    ):
        result = Constants.float_node
    elif _ast_equals(a=left, b=right):
        result = left
    elif _ast_equals(a=Constants.int_node, b=left) and _ast_equals(
        a=Constants.int_node,
        b=right,
    ):
        result = Constants.int_node
    elif _is_type_variable(source=left) and _ast_equals(
        a=Constants.int_node,
        b=right,
    ):
        result = left
    elif _is_type_variable(source=right) and _ast_equals(
        a=Constants.int_node,
        b=left,
    ):
        result = right
    else:
        result = merge_sources(sources=(left, right))
    return result


def _is_type_variable(*, source: TypeSource) -> bool:
    """Check if a type source is a type variable (single uppercase letter).

    Args:
        source: The source examined while check if a type source is a type
            variable (single uppercase letter).

    Returns:
        Whether the requested condition holds.

    """
    if not isinstance(source, Name):
        return False
    name: str = source.id
    if len(name) != 1:
        return False
    return name.isupper() and name.isalpha()


def all_functions(*, module: Module) -> tuple[FunctionDef, ...]:
    """Return every function definition in stable AST order.

    Args:
        module: The module examined while return every function definition in
            stable AST order.

    Returns:
        tuple[FunctionDef, ...] produced by this operation.

    """
    return tuple(
        node
        for node in walk_without_classes(node=module)
        if isinstance(node, FunctionDef)
    )


def all_async_functions(*, module: Module) -> tuple[AsyncFunctionDef, ...]:
    """Return every async function definition in stable AST order.

    Args:
        module: The module examined while return every async function
            definition in stable AST order.

    Returns:
        tuple[AsyncFunctionDef, ...] produced by this operation.

    """
    return tuple(
        node
        for node in walk_without_classes(node=module)
        if isinstance(node, AsyncFunctionDef)
    )


def walk_without_classes(*, node: AST) -> tuple[AST, ...]:
    """Walk a tree while not descending into nested class bodies.

    Args:
        node: The node examined while walk a tree while not descending into
            nested class bodies.

    Returns:
        tuple[AST, ...] produced by this operation.

    """
    nodes: list[AST] = [node]
    child: AST
    for child in child_nodes(node=node):
        nodes.append(child)
        if isinstance(child, ClassDef):
            continue
        nodes.extend(walk_without_classes(node=child))
    return tuple(nodes)


def _has_overload_marker(*, item: FunctionDef) -> bool:
    """Check whether a method is already an ``@overload`` stub.

    Args:
        item: Item supplied as FunctionDef for this operation.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        isinstance(decorator, Name) and decorator.id == "overload"
        for decorator in item.decorator_list
    )


def _calls_function_name(*, node: AST, name: str) -> bool:
    """Check whether ``node`` calls ``name(...)`` outside nested classes.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while check whether ``node`` calls
            ``name(...)`` outside nested classes.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        isinstance(item, Call)
        and isinstance(item.func, Name)
        and (item.func.id == name)
        for item in walk_without_classes(node=node)
    )


def _defines_getattr(*, wrapper_class: ClassDef) -> bool:
    """Check whether the wrapper defines ``__getattr__`` delegation.

    Args:
        wrapper_class: Wrapper class supplied as ClassDef for this operation.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        isinstance(item, FunctionDef) and item.name == "__getattr__"
        for item in wrapper_class.body
    )


def _proxy_cls_parameter(*, function: FunctionDef) -> arg | None:
    """Return the ``cls`` parameter when it accepts any class object.

    Args:
        function: The function examined while return the ``cls`` parameter when
            it accepts any class object.

    Returns:
        arg | None produced by this operation.

    """
    parameter: arg | None = next(
        (item for item in function.args.args if item.arg == "cls"),
        None,
    )
    if parameter is None or parameter.annotation is None:
        return parameter
    parameter_type: TypeSource = normalize_source(source=parameter.annotation)
    if _ast_equals(
        a=parameter_type,
        b=Constants.object_node,
    ) or _is_callable_type(node=parameter_type):
        return parameter
    return None


def _proxy_decorator_target(*, function: FunctionDef) -> _ProxyTarget | None:
    """Locate the proxy wrapper pieces of a class decorator.

    Args:
        function: The function examined while locate the proxy wrapper pieces
            of a class decorator.

    Returns:
        _ProxyTarget | None produced by this operation.

    """
    parameter: arg | None = _proxy_cls_parameter(function=function)
    if parameter is None:
        return None
    wrapper_class: ClassDef | None = next(
        (item for item in function.body if isinstance(item, ClassDef)),
        None,
    )
    if wrapper_class is None:
        return None
    init_method: FunctionDef | None = next(
        (
            item
            for item in wrapper_class.body
            if isinstance(item, FunctionDef) and item.name == "__init__"
        ),
        None,
    )
    if init_method is None or not _calls_function_name(
        node=init_method,
        name=parameter.arg,
    ):
        return None
    if not _defines_getattr(wrapper_class=wrapper_class):
        return None
    return _ProxyTarget(
        parameter=parameter,
        wrapper_class=wrapper_class,
        init_method=init_method,
    )


def returns_self(*, function: FunctionDef) -> bool:
    """Return whether a method explicitly returns ``self``.

    Args:
        function: The function examined while return whether a method
            explicitly returns ``self``.

    Returns:
        Whether the requested condition holds.

    """
    for statement in function.body:
        if isinstance(statement, FunctionDef | ClassDef):
            continue
        if isinstance(statement, Return):
            return (
                isinstance(statement.value, Name)
                and statement.value.id == "self"
            )
        for nested in iter_child_statements(statement=statement):
            if isinstance(nested, FunctionDef | ClassDef):
                continue
            if isinstance(nested, Return):
                return (
                    isinstance(nested.value, Name)
                    and nested.value.id == "self"
                )
    return False


def refine_nested_numeric_parameter(*, parameter: arg) -> bool:
    """Refine one nested numeric list parameter annotation.

    Args:
        parameter: Parameter supplied as arg for this operation.

    Returns:
        Whether the requested condition holds.

    """
    if parameter.annotation is None:
        return False
    current: TypeSource = normalize_source(source=parameter.annotation)
    if not _ast_equals(a=current, b=Constants.list_list_object_node):
        return False
    inner_list: expr = _make_generic_subscript(
        name="list",
        params=[_make_name_node(name="int")],
    )
    parameter.annotation = _make_generic_subscript(
        name="list",
        params=[inner_list],
    )
    return True


def refine_nested_numeric_assignment(*, assignment: AnnAssign) -> bool:
    """Refine one nested numeric list assignment annotation.

    Args:
        assignment: Assignment supplied as AnnAssign for this operation.

    Returns:
        Whether the requested condition holds.

    """
    current: TypeSource = normalize_source(source=assignment.annotation)
    if not _ast_equals(a=current, b=Constants.list_list_object_node):
        return False
    inner_list: expr = _make_generic_subscript(
        name="list",
        params=[_make_name_node(name="int")],
    )
    assignment.annotation = _make_generic_subscript(
        name="list",
        params=[inner_list],
    )
    return True


def is_identity_class_decorator(*, function: FunctionDef) -> bool:
    """Return whether a function behaves as an identity class decorator.

    Args:
        function: The function examined while return whether a function behaves
            as an identity class decorator.

    Returns:
        Whether the requested condition holds.

    """
    if function.returns is None:
        return False
    parameter: arg | None = next(
        (p for p in function.args.args if p.arg == "cls"),
        None,
    )
    if parameter is None:
        return False
    if parameter.annotation is None:
        return False
    parameter_type: TypeSource = normalize_source(source=parameter.annotation)
    return_type: TypeSource = normalize_source(source=function.returns)
    types_match: bool = (
        _ast_equals(a=parameter_type, b=Constants.type_object_node)
        and _ast_equals(a=return_type, b=Constants.type_object_node)
    ) or (
        _ast_equals(a=parameter_type, b=Constants.object_node)
        and _ast_equals(a=return_type, b=Constants.object_node)
    )
    if not types_match:
        return False
    return any(
        isinstance(statement, Return)
        and isinstance(statement.value, Name)
        and (statement.value.id == parameter.arg)
        for statement in function.body
    )


def set_function_type_parameter(*, function: FunctionDef, name: str) -> None:
    """Set a single PEP 695 type parameter on ``function``.

    Args:
        function: The function examined while set a single PEP 695 type
            parameter on ``function``.
        name: Identifier of the name being resolved.

    """
    function.type_params = [create_simple_typevar(name=name)]


def is_singleton_new_method(*, function: FunctionDef) -> bool:
    """Return whether ``__new__`` returns a cached class instance.

    Args:
        function: The function examined while return whether ``__new__``
            returns a cached class instance.

    Returns:
        Whether the requested condition holds.

    """
    if function.name != "__new__" or function.returns is None:
        return False
    current: TypeSource = normalize_source(source=function.returns)
    if not _ast_equals(a=current, b=Constants.object_node):
        return False
    return any(
        isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and (node.value.id == "cls")
        for node in walk_without_classes(node=function)
    )


def class_has_nested_numeric_evidence(*, class_node: ClassDef) -> bool:
    """Return whether a class uses nested object lists numerically.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        Whether the requested condition holds.

    """
    has_nested_object_list: bool = False
    has_numeric_matrix_operation: bool = False
    for item in class_node.body:
        if not isinstance(item, FunctionDef):
            continue
        for node in walk_without_classes(node=item):
            if isinstance(node, arg) and node.annotation is not None:
                source: TypeSource = normalize_source(source=node.annotation)
                has_nested_object_list = has_nested_object_list or _ast_equals(
                    a=source,
                    b=Constants.list_list_object_node,
                )
            if isinstance(node, AnnAssign):
                source = normalize_source(source=node.annotation)
                has_nested_object_list = has_nested_object_list or _ast_equals(
                    a=source,
                    b=Constants.list_list_object_node,
                )
            if isinstance(node, BinOp) and arithmetic_expression(node=node):
                has_numeric_matrix_operation = True
    return has_nested_object_list and has_numeric_matrix_operation


def arithmetic_expression(*, node: BinOp) -> bool:
    """Return whether a binary expression is numeric-style arithmetic.

    Args:
        node: The node examined while return whether a binary expression is
            numeric-style arithmetic.

    Returns:
        Whether the requested condition holds.

    """
    operator_name: str = node.op.__class__.__name__
    return operator_name in {"Add", "Sub", "Mult", "MatMult"}


def simplify_generator_annotation(*, annotation: expr) -> expr:
    """Return a shorter equivalent generator annotation when possible.

    Args:
        annotation: The annotation examined while return a shorter equivalent
            generator annotation when possible.

    Returns:
        expr produced by this operation.

    """
    source: TypeSource = normalize_source(source=annotation)
    if not is_generic(source=source, base="Generator"):
        return annotation
    arguments: tuple[TypeSource, ...] = generic_arguments(source=source)
    if len(arguments) != Constants.generator_source_arity or arguments[1:] != (
        Constants.none_node,
        Constants.none_node,
    ):
        return annotation
    yield_type: expr = arguments[0]
    generator_node: expr = _make_generic_subscript(
        name="Generator",
        params=[yield_type],
    )
    return generator_node


def function_parameters(*, function: FunctionDef) -> tuple[arg, ...]:
    """Return all explicit positional and keyword-only parameters.

    Args:
        function: The function examined while return all explicit positional
            and keyword-only parameters.

    Returns:
        tuple[arg, ...] produced by this operation.

    """
    return (
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    )


def callable_parameter_candidate(
    *,
    function: FunctionDef,
    parameter: arg,
    environment: FunctionTypeEnvironment,
) -> TypeSource | None:
    """Infer a callable parameter signature from direct calls.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        function: The function examined while infer a callable parameter
            signature from direct calls.
        parameter: Parameter supplied as arg for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    current: TypeSource | None = callable_ellipsis_return_source(
        parameter=parameter,
    )
    if current is None:
        return None
    call_arg_types: tuple[TypeSource, ...] | None = direct_call_arg_types(
        function=function,
        name=parameter.arg,
        environment=environment,
    )
    if call_arg_types is None:
        return None
    return _make_callable_subscript(
        params=list(call_arg_types),
        returns=current,
    )


def callable_ellipsis_return_source(*, parameter: arg) -> TypeSource | None:
    """Return ``R`` from ``Callable[..., R]`` parameter annotations.

    Args:
        parameter: Parameter supplied as arg for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    if parameter.annotation is None:
        return None
    current: TypeSource = normalize_source(source=parameter.annotation)
    if not is_generic(source=current, base="Callable"):
        return None
    arguments: tuple[TypeSource, ...] = generic_arguments(source=current)
    if (
        len(arguments) != Constants.pair_size
        or not isinstance(arguments[0], Constant)
        or arguments[0].value is not Ellipsis
    ):
        return None
    return arguments[1]


def direct_call_arg_types(
    *,
    function: FunctionDef,
    name: str,
    environment: FunctionTypeEnvironment,
) -> tuple[TypeSource, ...] | None:
    """Merge positional argument types for direct calls to ``name``.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        function: The function examined while merge positional argument types
            for direct calls to ``name``.
        name: Identifier of the name being resolved.

    Returns:
        tuple[TypeSource, ...] | None produced by this operation.

    """
    call_arg_types: list[TypeSource] = []
    for direct_call in direct_calls_to_name(function=function, name=name):
        candidate_args: tuple[TypeSource, ...] | None = call_arg_types_for(
            call=direct_call,
            environment=environment,
        )
        if candidate_args is None:
            return None
        if not call_arg_types:
            call_arg_types = list(candidate_args)
            continue
        if len(call_arg_types) != len(candidate_args):
            return None
        call_arg_types = [
            merge_sources(sources=(left, right))
            for left, right in zip(call_arg_types, candidate_args, strict=True)
        ]
    return tuple(call_arg_types) if call_arg_types else None


def call_arg_types_for(
    *,
    call: Call,
    environment: FunctionTypeEnvironment,
) -> tuple[TypeSource, ...] | None:
    """Return positional argument types for one call expression.

    Args:
        call: The call examined while return positional argument types for one
            call expression.
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.

    Returns:
        tuple[TypeSource, ...] | None produced by this operation.

    """
    if not call.args and call.keywords:
        return None
    return tuple(
        infer_expression_type(node=item, environment=environment)
        or Constants.object_node
        for item in call.args
    )


def direct_calls_to_name(
    *,
    function: FunctionDef,
    name: str,
) -> tuple[Call, ...]:
    """Return direct calls to a local name inside a function body.

    Args:
        function: The function examined while return direct calls to a local
            name inside a function body.
        name: Identifier of the name being resolved.

    Returns:
        tuple[Call, ...] produced by this operation.

    """
    calls: list[Call] = []
    for statement in function.body:
        if isinstance(statement, FunctionDef | ClassDef):
            continue
        calls.extend(
            node
            for node in walk_without_classes(node=statement)
            if isinstance(node, Call)
            and isinstance(node.func, Name)
            and (node.func.id == name)
        )
    return tuple(calls)


def function_signature_source(*, function: FunctionDef) -> TypeSource:
    """Render a function definition as a callable type expression.

    Args:
        function: The function examined while render a function definition as a
            callable type expression.

    Returns:
        TypeSource produced by this operation.

    """
    if function.args.vararg is not None or function.args.kwarg is not None:
        returns: TypeSource = (
            function.returns
            if function.returns is not None
            else Constants.object_node
        )
        return _make_callable_subscript(params=None, returns=returns)
    parameters: tuple[arg, ...] = function_parameters(function=function)
    parameter_sources: tuple[TypeSource, ...] = tuple(
        parameter.annotation
        if parameter.annotation is not None
        else Constants.object_node
        for parameter in parameters
    )
    returns = (
        function.returns
        if function.returns is not None
        else Constants.object_node
    )
    return _make_callable_subscript(
        params=list(parameter_sources),
        returns=returns,
    )


def returned_local_callable_type(
    *,
    function: FunctionDef,
    local_signatures: dict[str, TypeSource],
) -> TypeSource | None:
    """Return callable type for functions that return a local callable.

    Args:
        function: The function examined while return callable type for
            functions that return a local callable.
        local_signatures: Local signatures supplied as dict[str, TypeSource]
            for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    returned: list[TypeSource] = []
    for statement in function.body:
        if not isinstance(statement, Return):
            continue
        if isinstance(statement.value, Name):
            signature: TypeSource | None = local_signatures.get(
                statement.value.id,
            )
            if signature is not None:
                returned.append(signature)
            continue
        if isinstance(statement.value, Call):
            partial_signature: TypeSource | None = partial_return_type(
                call=statement.value,
                local_signatures=local_signatures,
            )
            if partial_signature is not None:
                returned.append(partial_signature)
    if not returned:
        return None
    return merge_sources(sources=tuple(returned))


def partial_return_type(
    *,
    call: Call,
    local_signatures: dict[str, TypeSource],
) -> TypeSource | None:
    """Infer the callable shape returned by ``functools.partial``.

    Args:
        call: The call examined while infer the callable shape returned by
            ``functools.partial``.
        local_signatures: Local signatures supplied as dict[str, TypeSource]
            for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    if callable_name(node=call.func) != "partial" or not call.args:
        return None
    first_argument: AST = call.args[0]
    if not isinstance(first_argument, Name):
        return None
    signature: TypeSource | None = local_signatures.get(first_argument.id)
    if signature is None:
        return None
    return drop_bound_callable_arguments(
        signature=signature,
        bound_positional_count=len(call.args) - 1,
        bound_keyword_names=frozenset(
            keyword.arg for keyword in call.keywords if keyword.arg is not None
        ),
    )


def drop_bound_callable_arguments(
    *,
    signature: TypeSource,
    bound_positional_count: int,
    bound_keyword_names: frozenset[str],
) -> TypeSource | None:
    """Return a callable signature after binding partial arguments.

    Args:
        bound_keyword_names: Bound keyword names supplied as frozenset[str] for
            this operation.
        bound_positional_count: Bound positional count supplied as int for this
            operation.
        signature: Signature supplied as TypeSource for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    normalized: TypeSource = normalize_source(source=signature)
    if not is_generic(source=normalized, base="Callable"):
        return None
    arguments: tuple[TypeSource, ...] = generic_arguments(source=normalized)
    if len(arguments) != Constants.pair_size:
        return None
    parameter_block, return_source = arguments
    if (
        isinstance(parameter_block, Constant)
        and parameter_block.value is Ellipsis
    ):
        return _make_callable_subscript(params=None, returns=return_source)
    parameters: list[TypeSource] = callable_parameter_sources(
        source=parameter_block,
    )
    if bound_positional_count > len(parameters):
        return None
    remaining: list[TypeSource] = parameters[bound_positional_count:]
    if bound_keyword_names:
        return None
    return _make_callable_subscript(params=remaining, returns=return_source)


def callable_parameter_sources(*, source: TypeSource) -> list[TypeSource]:
    """Return parameter sources from a ``Callable`` parameter block.

    Args:
        source: The source examined while return parameter sources from a
            ``Callable`` parameter block.

    Returns:
        list[TypeSource] produced by this operation.

    """
    node: expr = parse_type_expression(source=source)
    if not isinstance(node, List):
        return []
    return list(node.elts)


def should_replace_callable_signature(
    *,
    current: TypeSource,
    candidate: TypeSource,
) -> bool:
    """Return whether a callable candidate carries more parameter shape.

    Args:
        candidate: Candidate supplied as TypeSource for this operation.
        current: Current supplied as TypeSource for this operation.

    Returns:
        Whether the requested condition holds.

    """
    normalized_current: TypeSource = normalize_source(source=current)
    normalized_candidate: TypeSource = normalize_source(source=candidate)
    if normalized_current == normalized_candidate:
        return False
    if not (
        is_generic(source=normalized_current, base="Callable")
        and is_generic(source=normalized_candidate, base="Callable")
    ):
        return False
    current_args: tuple[TypeSource, ...] = generic_arguments(
        source=normalized_current,
    )
    candidate_args: tuple[TypeSource, ...] = generic_arguments(
        source=normalized_candidate,
    )
    if (
        len(current_args) == Constants.pair_size
        and len(candidate_args) == Constants.pair_size
        and isinstance(current_args[0], Constant)
        and (current_args[0].value is Ellipsis)
        and (
            not (
                isinstance(candidate_args[0], Constant)
                and candidate_args[0].value is Ellipsis
            )
        )
    ):
        return True
    current_has_ellipsis: bool = has_callable_with_ellipsis_params(
        source=normalized_current,
    )
    candidate_has_parameters: bool = has_callable_with_listed_params(
        source=normalized_candidate,
    )
    return current_has_ellipsis and candidate_has_parameters


def contextmanager_api_return(*, function: FunctionDef) -> TypeSource | None:
    """Return the public API type for a ``@contextmanager`` function.

    Args:
        function: The function examined while return the public API type for a
            ``@contextmanager`` function.

    Returns:
        TypeSource | None produced by this operation.

    """
    if not has_decorator(function=function, decorator_name="contextmanager"):
        return None
    if function.returns is not None:
        current: TypeSource = normalize_source(source=function.returns)
        if is_generic(source=current, base="Generator"):
            return current
        if is_generic(source=current, base="Iterator"):
            arguments: tuple[TypeSource, ...] = generic_arguments(
                source=current,
            )
            if arguments:
                return _make_generic_subscript(
                    name="Generator",
                    params=[arguments[0]],
                )
    yielded: TypeSource | None = infer_yielded_type(function=function)
    if yielded is None:
        return None
    return _make_generic_subscript(name="Generator", params=[yielded])


def has_decorator(*, function: FunctionDef, decorator_name: str) -> bool:
    """Return whether a function has a decorator by final name.

    Args:
        decorator_name: Identifier of the decorator being resolved.
        function: The function examined while return whether a function has a
            decorator by final name.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        callable_name(node=decorator) == decorator_name
        for decorator in function.decorator_list
    )


def infer_yielded_type(*, function: FunctionDef) -> TypeSource | None:
    """Infer yielded value type from a context-manager generator body.

    Args:
        function: The function examined while infer yielded value type from a
            context-manager generator body.

    Returns:
        TypeSource | None produced by this operation.

    """
    environment: FunctionTypeEnvironment = FunctionTypeEnvironment()
    for statement in function.body:
        if isinstance(statement, AnnAssign):
            name: str | None = name_from_target(node=statement.target)
            if name is not None:
                environment.set_if_better(
                    name=name,
                    source=statement.annotation,
                )
    yielded: list[TypeSource] = []
    for node in child_nodes(node=function):
        if isinstance(node, FunctionDef | ClassDef):
            continue
        yielded.extend(
            yield_sources_from_node(node=node, environment=environment),
        )
    if not yielded:
        return None
    return merge_sources(sources=tuple(yielded))


def yield_sources_from_node(
    *,
    node: AST,
    environment: FunctionTypeEnvironment,
) -> tuple[TypeSource, ...]:
    """Return yield expression types from a subtree.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        node: The node examined while return yield expression types from a
            subtree.

    Returns:
        tuple[TypeSource, ...] produced by this operation.

    """
    results: list[TypeSource] = []
    if isinstance(node, Yield) and node.value is not None:
        inferred: TypeSource | None = infer_expression_type(
            node=node.value,
            environment=environment,
        )
        if inferred is not None:
            results.append(inferred)
    if isinstance(node, YieldFrom):
        inferred = infer_expression_type(
            node=node.value,
            environment=environment,
        )
        if inferred is not None:
            results.append(element_type(source=inferred))
    for child in child_nodes(node=node):
        if isinstance(child, FunctionDef | ClassDef):
            continue
        results.extend(
            yield_sources_from_node(node=child, environment=environment),
        )
    return tuple(results)


def list_object_union_candidate(*, source: TypeSource) -> TypeSource | None:
    """Infer ``list[T]`` inside a union that also contains scalar ``T``.

    Args:
        source: The source examined while infer ``list[T]`` inside a union that
            also contains scalar ``T``.

    Returns:
        TypeSource | None produced by this operation.

    """
    parts: tuple[TypeSource, ...] = split_union(
        source=normalize_source(source=source),
    )
    if len(parts) < Constants.pair_size or not any(
        _ast_equals(a=part, b=Constants.list_object_node) for part in parts
    ):
        return None
    scalar_parts: tuple[TypeSource, ...] = tuple(
        part
        for part in parts
        if _ast_equals(a=part, b=Constants.int_node)
        or _ast_equals(a=part, b=Constants.str_node)
        or _ast_equals(a=part, b=Constants.bool_node)
        or _ast_equals(a=part, b=Constants.float_node)
    )
    if len(scalar_parts) != 1:
        return None
    narrowed_parts: tuple[TypeSource, ...] = tuple(
        _make_generic_subscript(name="list", params=[scalar_parts[0]])
        if _ast_equals(a=part, b=Constants.list_object_node)
        else part
        for part in parts
    )
    return merge_sources(sources=narrowed_parts)


def heterogeneous_result_return_candidate(*, function: FunctionDef) -> bool:
    """Return whether a function has a heterogeneous result mapping.

    Args:
        function: The function examined while return whether a function has a
            heterogeneous result mapping.

    Returns:
        Whether the requested condition holds.

    """
    if function.returns is None:
        return False
    source: TypeSource = normalize_source(source=function.returns)
    if _ast_equals(a=source, b=Constants.dict_str_object_node):
        return True
    if not _ast_equals(a=source, b=Constants.dict_object_object_node):
        return False
    return returns_string_keyed_dict(function=function)


def returns_string_keyed_dict(*, function: FunctionDef) -> bool:
    """Return whether all explicit returned dictionary keys are strings.

    Args:
        function: The function examined while return whether all explicit
            returned dictionary keys are strings.

    Returns:
        Whether the requested condition holds.

    """
    saw_dictionary: bool = False
    for node in walk_without_classes(node=function):
        if not isinstance(node, Return) or not isinstance(node.value, Dict):
            continue
        saw_dictionary = True
        for key in node.value.keys:
            if key is None:
                continue
            if not isinstance(key, Constant) or not isinstance(key.value, str):
                return False
    return saw_dictionary


def ensure_imported_name(
    *,
    module: Module,
    module_name: str,
    imported_name: str,
) -> None:
    """Ensure ``from module_name import imported_name`` exists.

    Args:
        imported_name: Identifier of the imported being resolved.
        module: The module examined while ensure ``from module_name import
            imported_name`` exists.
        module_name: Identifier of the module being resolved.

    """
    statement: stmt
    for statement in module.body:
        if not isinstance(statement, ImportFrom):
            continue
        if statement.module != module_name:
            continue
        existing: set[str] = {item.name for item in statement.names}
        if imported_name not in existing:
            statement.names.append(alias(name=imported_name))
        return
    insert_at: int = import_insert_index(module=module)
    module.body.insert(
        insert_at,
        ImportFrom(
            module=module_name,
            names=[alias(name=imported_name)],
            level=0,
        ),
    )


def import_insert_index(*, module: Module) -> int:
    """Return a stable insertion index for new imports.

    Args:
        module: The module examined while return a stable insertion index for
            new imports.

    Returns:
        int produced by this operation.

    """
    index: int = 0
    if (
        module.body
        and isinstance(module.body[0], Expr)
        and isinstance(module.body[0].value, Constant)
        and isinstance(module.body[0].value.value, str)
    ):
        index = 1
    while index < len(module.body):
        statement: stmt = module.body[index]
        is_future_import: bool = (
            isinstance(statement, ImportFrom)
            and statement.module == "__future__"
        )
        if not is_future_import:
            break
        index += 1
    return index


def protocol_attribute_annotations(
    *,
    module: Module,
) -> dict[str, dict[str, AnnAssign]]:
    """Return mutable protocol attribute annotation nodes by class.

    Args:
        module: The module examined while return mutable protocol attribute
            annotation nodes by class.

    Returns:
        dict[str, dict[str, AnnAssign]] produced by this operation.

    """
    result: dict[str, dict[str, AnnAssign]] = {}
    for class_node in ast_classes(module=module):
        if not class_has_base(class_node=class_node, base_name="Protocol"):
            continue
        attributes: dict[str, AnnAssign] = {}
        for item in class_node.body:
            if isinstance(item, AnnAssign) and isinstance(item.target, Name):
                attributes[item.target.id] = item
        if attributes:
            result[class_node.name] = attributes
    return result


def name_annotation_sources(*, module: Module) -> dict[str, TypeSource]:
    """Return simple name annotations visible in the module tree.

    Args:
        module: The module examined while return simple name annotations
            visible in the module tree.

    Returns:
        dict[str, TypeSource] produced by this operation.

    """
    result: dict[str, TypeSource] = {}
    for item in iter_assignment_nodes(module=module):
        if isinstance(item, AnnAssign) and isinstance(item.target, Name):
            result[item.target.id] = item.annotation
    return result


def iter_assignment_nodes(*, module: Module) -> tuple[Assign | AnnAssign, ...]:
    """Return assignment nodes in stable tree order.

    Args:
        module: The module examined while return assignment nodes in stable
            tree order.

    Returns:
        tuple[Assign | AnnAssign, ...] produced by this operation.

    """
    nodes: list[Assign | AnnAssign] = []
    for node in child_nodes(node=module):
        collect_assignment_nodes(node=node, nodes=nodes)
    return tuple(nodes)


def collect_assignment_nodes(
    *,
    node: AST,
    nodes: list[Assign | AnnAssign],
) -> None:
    """Collect assignment nodes recursively.

    Args:
        node: The node examined while collect assignment nodes recursively.
        nodes: Collection of nodes supplied for this operation.

    """
    if isinstance(node, Assign | AnnAssign):
        nodes.append(node)
    for child in child_nodes(node=node):
        collect_assignment_nodes(node=child, nodes=nodes)


def assignment_attribute_target(
    *,
    node: Assign | AnnAssign,
) -> Attribute | None:
    """Return an attribute assignment target when unique and simple.

    Args:
        node: The node examined while return an attribute assignment target
            when unique and simple.

    Returns:
        Attribute | None produced by this operation.

    """
    if isinstance(node, AnnAssign) and isinstance(node.target, Attribute):
        return node.target
    if isinstance(node, Assign) and len(node.targets) == 1:
        target: expr = node.targets[0]
        if isinstance(target, Attribute):
            return target
    return None


def assignment_value(*, node: Assign | AnnAssign) -> AST | None:
    """Return the assigned value for assignment-like nodes.

    Args:
        node: The node examined while return the assigned value for
            assignment-like nodes.

    Returns:
        AST | None produced by this operation.

    """
    return node.value


def ast_classes(*, module: Module) -> tuple[ClassDef, ...]:
    """Return all class definitions in a module tree.

    Args:
        module: The module examined while return all class definitions in a
            module tree.

    Returns:
        tuple[ClassDef, ...] produced by this operation.

    """
    return tuple(
        node for node in child_nodes(node=module) if isinstance(node, ClassDef)
    ) + tuple(
        node
        for top_level in module.body
        for node in child_nodes(node=top_level)
        if isinstance(node, ClassDef)
    )


def class_has_base(*, class_node: ClassDef, base_name: str) -> bool:
    """Return whether a class has a base with ``base_name``.

    Args:
        base_name: Identifier of the base being resolved.
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        class_base_name(node=base) == base_name for base in class_node.bases
    )


def class_type_source(
    *,
    class_node: ClassDef,
    available_names: frozenset[str],
) -> TypeSource:
    """Infer a stable return type for a local class object.

    Args:
        available_names: Available names supplied as frozenset[str] for this
            operation.
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        TypeSource produced by this operation.

    """
    for base in class_node.bases:
        base_name: str | None = class_base_name(node=base)
        if base_name is not None and base_name in available_names:
            return _make_type_subscript(
                name="type",
                param=_make_name_node(name=base_name),
            )
    return Constants.type_object_node


def returned_class_base(
    *,
    function: FunctionDef,
    available_names: frozenset[str],
) -> str | None:
    """Return a module-level base of the single class a function returns.

    Returns ``None`` unless the function body defines exactly one class, that
    class is the returned value, and it subclasses a module-scope class.


    Args:
        available_names: Available names supplied as frozenset[str] for this
            operation.
        function: The function examined while return a module-level base of the
            single class a function returns.

    Returns:
        str | None produced by this operation.

    """
    returned_names: set[str] = set()
    for node in walk_without_classes(node=function):
        if isinstance(node, Return) and isinstance(node.value, Name):
            returned_names.add(node.value.id)
    classes: tuple[ClassDef, ...] = tuple(
        node
        for node in child_nodes(node=function)
        if isinstance(node, ClassDef)
    )
    if len(classes) != 1 or classes[0].name not in returned_names:
        return None
    for base in classes[0].bases:
        base_name: str | None = class_base_name(node=base)
        if base_name is not None and base_name in available_names:
            return base_name
    return None


def returned_local_class_name(*, function: FunctionDef) -> str | None:
    """Return the name of the single locally-defined class a function returns.

    Returns ``None`` unless the function body defines exactly one class, that
    class is the returned value.


    Args:
        function: The function examined while return the name of the single
            locally-defined class a function returns.

    Returns:
        str | None produced by this operation.

    """
    returned_names: set[str] = set()
    for node in walk_without_classes(node=function):
        if isinstance(node, Return) and isinstance(node.value, Name):
            returned_names.add(node.value.id)
    classes: tuple[ClassDef, ...] = tuple(
        node
        for node in child_nodes(node=function)
        if isinstance(node, ClassDef)
    )
    if len(classes) != 1 or classes[0].name not in returned_names:
        return None
    return classes[0].name


def module_class_names(*, module: Module) -> frozenset[str]:
    """Return names of classes available at module annotation scope.

    Args:
        module: The module examined while return names of classes available at
            module annotation scope.

    Returns:
        frozenset[str] produced by this operation.

    """
    return frozenset(
        item.name for item in module.body if isinstance(item, ClassDef)
    )


def class_base_name(*, node: AST) -> str | None:
    """Return a usable class base name from a base expression.

    Args:
        node: The node examined while return a usable class base name from a
            base expression.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Subscript):
        return class_base_name(node=node.value)
    if isinstance(node, Attribute):
        return node.attr
    return None


def class_instance_attributes(
    *,
    class_node: ClassDef,
) -> dict[str, TypeSource]:
    """Collect ``self.attr`` annotations known inside a class body.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        dict[str, TypeSource] produced by this operation.

    """
    attributes: dict[str, TypeSource] = {}
    for item in class_node.body:
        if isinstance(item, AnnAssign) and isinstance(item.target, Name):
            attributes[f"self.{item.target.id}"] = item.annotation
        if not isinstance(item, FunctionDef):
            continue
        for nested in iter_child_statements(statement=item):
            if not isinstance(nested, AnnAssign):
                continue
            name: str | None = name_from_target(node=nested.target)
            if name is None or not name.startswith("self."):
                continue
            attributes[name] = nested.annotation
    return attributes


def _infer_list_element_type(*, class_node: ClassDef) -> TypeSource | None:
    """Infer the element type from a list subclass base.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        TypeSource | None produced by this operation.

    """
    for base in class_node.bases:
        if (
            isinstance(base, Subscript)
            and isinstance(base.value, Name)
            and (base.value.id == "list")
        ):
            return base.slice
    return None


def _seed_parameter(
    *,
    parameter: arg,
    environment: FunctionTypeEnvironment,
) -> None:
    """Seed one parameter annotation.

    Args:
        environment: Environment supplied as FunctionTypeEnvironment for this
            operation.
        parameter: Parameter supplied as arg for this operation.

    """
    if parameter.annotation is None:
        return
    environment.set_if_better(name=parameter.arg, source=parameter.annotation)


def iter_child_statements(*, statement: stmt) -> tuple[stmt, ...]:
    """Return descendant statements but skip nested function/class bodies.

    Args:
        statement: The statement examined while return descendant statements
            but skip nested function/class bodies.

    Returns:
        tuple[stmt, ...] produced by this operation.

    """
    children: list[stmt] = []
    for child in statement_child_statements(statement=statement):
        children.append(child)
        if isinstance(child, FunctionDef):
            continue
        children.extend(iter_child_statements(statement=child))
    return tuple(children)


def statement_child_statements(*, statement: stmt) -> tuple[stmt, ...]:
    """Return direct child statements for control-flow constructs.

    Args:
        statement: The statement examined while return direct child statements
            for control-flow constructs.

    Returns:
        tuple[stmt, ...] produced by this operation.

    """
    return tuple(
        child
        for child in child_nodes(node=statement)
        if isinstance(child, stmt)
    )


def name_from_target(*, node: AST) -> str | None:
    """Return a local target name when the target is simple enough.

    Args:
        node: The node examined while return a local target name when the
            target is simple enough.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute) and isinstance(node.value, Name):
        return f"{node.value.id}.{node.attr}"
    return None


def top_level_target_counts(*, body: list[stmt]) -> dict[str, int]:
    """Count how often each name is an assignment target at body top level.

    Args:
        body: Body supplied as list[stmt] for this operation.

    Returns:
        dict[str, int] produced by this operation.

    """
    counts: dict[str, int] = {}
    for item in body:
        targets: tuple[AST, ...] = ()
        if isinstance(item, Assign):
            targets = tuple(item.targets)
        elif isinstance(item, AnnAssign):
            targets = (item.target,)
        for target in targets:
            if isinstance(target, Name):
                counts[target.id] = counts.get(target.id, 0) + 1
    return counts


def callable_name(*, node: AST) -> str | None:
    """Return the final callable name for a call expression.

    Args:
        node: The node examined while return the final callable name for a call
            expression.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def tuple_target_names(*, node: AST) -> tuple[str, ...]:
    """Return simple target names from a tuple-like target.

    Args:
        node: The node examined while return simple target names from a
            tuple-like target.

    Returns:
        tuple[str, ...] produced by this operation.

    """
    if isinstance(node, Tuple):
        return tuple(
            element.id for element in node.elts if isinstance(element, Name)
        )
    if isinstance(node, Name):
        return (node.id,)
    return ()


def element_type(*, source: TypeSource) -> TypeSource:
    """Return the element type for a known collection source.

    Args:
        source: The source examined while return the element type for a known
            collection source.

    Returns:
        TypeSource produced by this operation.

    """
    normalized: TypeSource = normalize_source(source=source)
    for base in ("list", "set", "Iterable", "Iterator", "Sequence"):
        if is_generic(source=normalized, base=base):
            return generic_arguments(source=normalized)[0]
    if is_generic(source=normalized, base="tuple"):
        arguments: tuple[TypeSource, ...] = generic_arguments(
            source=normalized,
        )
        if (
            len(arguments) == Constants.pair_size
            and isinstance(arguments[1], Constant)
            and (arguments[1].value is Ellipsis)
        ):
            return arguments[0]
        return merge_sources(sources=arguments)
    if is_generic(source=normalized, base="dict"):
        key_type, value_type = generic_arguments(source=normalized)
        return _make_generic_subscript(
            name="tuple",
            params=[key_type, value_type],
        )
    return Constants.object_node


@lru_cache(maxsize=512)
def _parse_type_cached(normalized: TypeSource) -> expr:
    """Parse a normalized type source once and memoize the node.

    The returned node is shared across callers, so it must only ever be read
    for structural inspection -- never mutated or inserted into an output
    tree. Node construction for output always uses ``parse_annotation``.


    Args:
        normalized: Normalized supplied as TypeSource for this operation.

    Returns:
        expr produced by this operation.

    """
    return normalized


def parse_type_expression(*, source: TypeSource) -> expr:
    """Return a cached, read-only annotation node for structural inspection.

    Args:
        source: The source examined while return a cached, read-only annotation
            node for structural inspection.

    Returns:
        expr produced by this operation.

    """
    return _parse_type_cached(normalized=normalize_source(source=source))


def generic_arguments(*, source: TypeSource) -> tuple[TypeSource, ...]:
    """Return top-level generic arguments by reading the subscript node.

    Args:
        source: The source examined while return top-level generic arguments by
            reading the subscript node.

    Returns:
        tuple[TypeSource, ...] produced by this operation.

    """
    if not isinstance(source, Subscript):
        return ()
    slice_node: expr = source.slice
    elements: tuple[expr, ...] = (
        tuple(slice_node.elts)
        if isinstance(slice_node, Tuple)
        else (slice_node,)
    )
    return elements


def is_generic(*, source: TypeSource, base: str) -> bool:
    """Return whether ``source`` is a ``base[...]`` subscript expression.

    Args:
        base: Base supplied as str for this operation.
        source: The source examined while return whether ``source`` is a
            ``base[...]`` subscript expression.

    Returns:
        Whether the requested condition holds.

    """
    return (
        isinstance(source, Subscript)
        and isinstance(source.value, Name)
        and (source.value.id == base)
    )


def is_union(*, source: TypeSource) -> bool:
    """Return whether ``source`` is a top-level ``a | b`` union.

    Args:
        source: The source examined while return whether ``source`` is a
            top-level ``a | b`` union.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(source, BinOp) and isinstance(source.op, BitOr)


def mentions_object(*, source: TypeSource) -> bool:
    """Return whether a type source references the ``object`` name anywhere.

    Args:
        source: The source examined while return whether a type source
            references the ``object`` name anywhere.

    Returns:
        Whether the requested condition holds.

    """
    parsed_node: expr = parse_type_expression(source=source)
    return any(
        child.id == Constants.object_node
        for child in nodes_of_type(root=parsed_node, types=(Name,))
    )


def _is_callable_with(*, node: AST, ellipsis_params: bool) -> bool:
    """Return whether ``node`` is a ``Callable`` with that parameter form.

    Args:
        ellipsis_params: Ellipsis params supplied as bool for this operation.
        node: The node examined while return whether ``node`` is a ``Callable``
            with that parameter form.

    Returns:
        Whether the requested condition holds.

    """
    if not (
        isinstance(node, Subscript)
        and isinstance(node.value, Name)
        and (node.value.id == "Callable")
    ):
        return False
    slice_node: expr = node.slice
    if not (isinstance(slice_node, Tuple) and slice_node.elts):
        return False
    first: expr = slice_node.elts[0]
    if ellipsis_params:
        return isinstance(first, Constant) and first.value is Ellipsis
    return isinstance(first, List)


def has_callable_with_ellipsis_params(*, source: TypeSource) -> bool:
    """Return whether ``source`` contains a ``Callable[..., R]`` anywhere.

    Args:
        source: The source examined while return whether ``source`` contains a
            ``Callable[..., R]`` anywhere.

    Returns:
        Whether the requested condition holds.

    """
    node: expr = parse_type_expression(source=source)
    return any(
        _is_callable_with(node=child, ellipsis_params=True)
        for child in nodes_of_type(root=node, types=(Name,))
    )


def has_callable_with_listed_params(*, source: TypeSource) -> bool:
    """Return whether ``source`` contains a ``Callable[[...], R]`` anywhere.

    Args:
        source: The source examined while return whether ``source`` contains a
            ``Callable[[...], R]`` anywhere.

    Returns:
        Whether the requested condition holds.

    """
    node: expr = parse_type_expression(source=source)
    return any(
        _is_callable_with(node=child, ellipsis_params=False)
        for child in nodes_of_type(root=node, types=(Name,))
    )


def merge_sources(*, sources: tuple[TypeSource, ...]) -> TypeSource:
    """Merge type sources into a normalized union.

    Args:
        sources: Sources supplied as tuple[TypeSource, ...] for this operation.

    Returns:
        TypeSource produced by this operation.

    """
    flattened: list[TypeSource] = []
    source: TypeSource
    for source in sources:
        flattened.extend(split_union(source=source))
    cleaned: list[TypeSource] = [
        normalize_source(source=item)
        for item in flattened
        if not _ast_equals(a=item, b=Constants.none_node)
        and (not _is_never(node=item))
    ]
    if not cleaned:
        return Constants.object_node
    if any(_ast_equals(a=item, b=Constants.object_node) for item in cleaned):
        return Constants.object_node
    unique: dict[TypeSource, None] = {}
    for item in cleaned:
        unique[item] = None
    if len(unique) == 1:
        return next(iter(unique))
    return _make_union_node(*sorted(unique, key=union_sort_key))


def _is_never(*, node: TypeSource) -> bool:
    """Check if a node represents Never.

    Args:
        node: The node examined while check if a node represents Never.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(node, Name) and node.id == "Never"


def split_union(*, source: TypeSource) -> tuple[TypeSource, ...]:
    """Split a PEP 604 union by walking its ``BinOp`` ``|`` chain.

    Args:
        source: The source examined while split a PEP 604 union by walking its
            ``BinOp`` ``|`` chain.

    Returns:
        tuple[TypeSource, ...] produced by this operation.

    """
    return union_members(node=source)


def union_members(*, node: expr) -> tuple[expr, ...]:
    """Flatten a ``a | b | c`` union expression into its member nodes.

    Args:
        node: The node examined while flatten a ``a | b | c`` union expression
            into its member nodes.

    Returns:
        tuple[expr, ...] produced by this operation.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return union_members(node=node.left) + union_members(node=node.right)
    return (node,)


def normalize_source(*, source: TypeSource) -> TypeSource:
    """Normalize qualified names in a type source.

    Named aliases (``IntDict`` etc.) are folded only at the terminal finalize
    step, so they never reach inference here and need no expansion.


    Args:
        source: The source examined while normalize qualified names in a type
            source.

    Returns:
        TypeSource produced by this operation.

    """
    if isinstance(source, Name):
        if source.id.startswith("typing."):
            return Name(id=source.id.replace("typing.", ""), ctx=Load())
        if source.id.startswith("collections.abc."):
            return Name(
                id=source.id.replace("collections.abc.", ""),
                ctx=Load(),
            )
    return source


def union_sort_key(source: TypeSource) -> tuple[int, str]:
    """Sort ``None`` last in unions.

    Args:
        source: The source examined while sort ``None`` last in unions.

    Returns:
        tuple[int, str] produced by this operation.

    """
    return (
        1 if _ast_equals(a=source, b=Constants.none_node) else 0,
        _ast_node_to_string(node=source),
    )


def is_narrowing(*, current: TypeSource, candidate: TypeSource) -> bool:
    """Return whether ``candidate`` strictly, soundly narrows ``current``.

    Handles union-member subsets (``int | None`` -> ``int``) and element
    narrowing inside matching collection generics (``list[int | str]`` ->
    ``list[int]``).


    Args:
        candidate: Candidate supplied as TypeSource for this operation.
        current: Current supplied as TypeSource for this operation.

    Returns:
        Whether the requested condition holds.

    """
    cur: TypeSource = normalize_source(source=current)
    cand: TypeSource = normalize_source(source=candidate)
    if cur == cand:
        return False
    cur_members: frozenset[TypeSource] = frozenset(split_union(source=cur))
    cand_members: frozenset[TypeSource] = frozenset(split_union(source=cand))
    if len(cur_members) > 1 or len(cand_members) > 1:
        return cand_members < cur_members
    for base in ("list", "set", "Sequence", "Iterable", "Iterator"):
        if is_generic(source=cur, base=base) and is_generic(
            source=cand,
            base=base,
        ):
            return is_narrowing(
                current=generic_arguments(source=cur)[0],
                candidate=generic_arguments(source=cand)[0],
            )
    if is_generic(source=cur, base="dict") and is_generic(
        source=cand,
        base="dict",
    ):
        cur_args: tuple[TypeSource, ...] = generic_arguments(source=cur)
        cand_args: tuple[TypeSource, ...] = generic_arguments(source=cand)
        if (
            len(cur_args) == Constants.pair_size
            and len(cand_args) == Constants.pair_size
            and (cur_args[0] == cand_args[0])
        ):
            return is_narrowing(current=cur_args[1], candidate=cand_args[1])
    return False


def should_replace_type(*, current: TypeSource, candidate: TypeSource) -> bool:
    """Return whether ``candidate`` is more useful than ``current``.

    Args:
        candidate: Candidate supplied as TypeSource for this operation.
        current: Current supplied as TypeSource for this operation.

    Returns:
        Whether the requested condition holds.

    """
    normalized_current: TypeSource = normalize_source(source=current)
    normalized_candidate: TypeSource = normalize_source(source=candidate)
    if normalized_current == normalized_candidate:
        return False
    if normalized_current in _UNKNOWN_COLLECTION_SOURCES:
        return True
    current_has_object: bool = mentions_object(source=normalized_current)
    if current_has_object and (
        not mentions_object(source=normalized_candidate)
    ):
        return True
    current_is_dict: bool = is_generic(source=normalized_current, base="dict")
    candidate_is_dict: bool = is_generic(
        source=normalized_candidate,
        base="dict",
    )
    if current_is_dict and candidate_is_dict:
        return current_has_object
    current_is_list: bool = is_generic(source=normalized_current, base="list")
    candidate_is_list: bool = is_generic(
        source=normalized_candidate,
        base="list",
    )
    if current_is_list and candidate_is_list:
        return current_has_object
    return _is_tuple_element_widening(
        current=normalized_current,
        candidate=normalized_candidate,
    )


def _is_tuple_element_widening(
    *,
    current: TypeSource,
    candidate: TypeSource,
) -> bool:
    """Return True when candidate widens current tuple elements.

    Args:
        candidate: Candidate supplied as TypeSource for this operation.
        current: Current supplied as TypeSource for this operation.

    Returns:
        Whether the requested condition holds.

    """
    cur_elems: tuple[TypeSource, ...] = tuple_element_sources(source=current)
    cand_elems: tuple[TypeSource, ...] = tuple_element_sources(
        source=candidate,
    )
    if not cur_elems or len(cur_elems) != len(cand_elems):
        return False
    widened: bool = False
    for cur_elem, cand_elem in zip(cur_elems, cand_elems, strict=True):
        cur_strs: frozenset[str] = frozenset(
            render_annotation(node=m)
            for m in split_union(source=normalize_source(source=cur_elem))
        )
        cand_strs: frozenset[str] = frozenset(
            render_annotation(node=m)
            for m in split_union(source=normalize_source(source=cand_elem))
        )
        if cur_strs == cand_strs:
            continue
        if not cur_strs < cand_strs:
            return False
        widened = True
    return widened


def should_keep_broad_return(
    *,
    current: TypeSource,
    candidate: TypeSource,
) -> bool:
    """Return whether a broad return is safer than a local candidate.

    Args:
        candidate: Candidate supplied as TypeSource for this operation.
        current: Current supplied as TypeSource for this operation.

    Returns:
        Whether the requested condition holds.

    """
    normalized_current: TypeSource = normalize_source(source=current)
    normalized_candidate: TypeSource = normalize_source(source=candidate)
    if normalized_current == normalized_candidate:
        return True
    return _ast_equals(a=normalized_current, b=Constants.dict_str_object_node)


@dataclass(frozen=True, slots=True)
class KeywordCallSignature:
    """Callable signature subset used for safe keyword rewrites.

    Attributes:
        parameters: Parameters retained as tuple[str, ...] by this instance.
        positional_only_count: Positional only count retained as int by this
            instance.

    """

    parameters: tuple[str, ...]
    positional_only_count: int = 0

    def keywordable_prefix_size(self, *, positional_count: int) -> int:
        """Return how many positional arguments can be represented safely.

        Args:
            positional_count: Positional count supplied as int for this
                operation.

        Returns:
            int produced by this operation.

        """
        if positional_count > len(self.parameters):
            return 0
        if positional_count <= self.positional_only_count:
            return 0
        return positional_count


@dataclass(slots=True)
class KeywordRewriteScope:
    """Name and type evidence available while rewriting calls.

    Attributes:
        class_bases: Class bases retained as list[str] by this instance.
        class_signatures: Class signatures retained as dict[str,
            KeywordCallSignature] by this instance.
        current_class: Current class retained as ClassDef | None by this
            instance.
        function_signatures: Function signatures retained as dict[str,
            KeywordCallSignature] by this instance.
        method_signatures: Method signatures retained as dict[tuple[str, str],
            KeywordCallSignature] by this instance.
        variable_types: Variable types retained as dict[str, TypeSource] by
            this instance.

    """

    function_signatures: dict[str, KeywordCallSignature]
    class_signatures: dict[str, KeywordCallSignature]
    method_signatures: dict[tuple[str, str], KeywordCallSignature]
    variable_types: dict[str, TypeSource] = field(default_factory=dict)
    current_class: ClassDef | None = None
    class_bases: list[str] = field(default_factory=list)

    def child(self) -> KeywordRewriteScope:
        """Create a child scope that inherits the current evidence.

        Returns:
            KeywordRewriteScope produced by this operation.

        """
        return KeywordRewriteScope(
            function_signatures=dict(self.function_signatures),
            class_signatures=self.class_signatures,
            method_signatures=self.method_signatures,
            variable_types=dict(self.variable_types),
            current_class=self.current_class,
            class_bases=list(self.class_bases),
        )


def refine_keyword_arguments(*, module: Module) -> int:
    """Rewrite safe positional call arguments into keyword arguments.

    Args:
        module: The module examined while rewrite safe positional call
            arguments into keyword arguments.

    Returns:
        int produced by this operation.

    """
    scope: KeywordRewriteScope = KeywordRewriteScope(
        function_signatures=module_function_signatures(module=module),
        class_signatures=module_class_signatures(module=module),
        method_signatures=module_method_signatures(module=module),
        variable_types=module_variable_type_sources(module=module),
    )
    return refine_statement_list_keyword_arguments(
        statements=module.body,
        scope=scope,
    )


def refine_statement_list_keyword_arguments(
    *,
    statements: list[stmt],
    scope: KeywordRewriteScope,
) -> int:
    """Rewrite calls inside a statement list.

    Args:
        scope: The scope examined while rewrite calls inside a statement list.
        statements: Collection of statements supplied for this operation.

    Returns:
        int produced by this operation.

    """
    local_scope: KeywordRewriteScope = scope.child()
    seed_local_function_signatures(statements=statements, scope=local_scope)
    seed_local_variable_types(statements=statements, scope=local_scope)
    changed: int = 0
    statement: stmt
    for statement in statements:
        changed += refine_node_keyword_arguments(
            node=statement,
            scope=local_scope,
        )
    return changed


def refine_node_keyword_arguments(
    *,
    node: AST,
    scope: KeywordRewriteScope,
) -> int:
    """Rewrite calls in one node and its children.

    Args:
        node: The node examined while rewrite calls in one node and its
            children.
        scope: The scope examined while rewrite calls in one node and its
            children.

    Returns:
        int produced by this operation.

    """
    changed: int = 0
    if isinstance(node, Call):
        changed += rewrite_call_keywords(call=node, scope=scope)
    if isinstance(node, FunctionDef):
        child_scope: KeywordRewriteScope = scope.child()
        seed_function_parameter_types(function=node, scope=child_scope)
        changed += refine_statement_list_keyword_arguments(
            statements=node.body,
            scope=child_scope,
        )
        return changed
    if isinstance(node, ClassDef):
        child_scope = scope.child()
        child_scope.current_class = node
        child_scope.class_bases = _extract_class_bases(class_node=node)
        seed_class_attribute_types(class_node=node, scope=child_scope)
        changed += refine_statement_list_keyword_arguments(
            statements=node.body,
            scope=child_scope,
        )
        return changed
    child: AST
    for child in child_nodes(node=node):
        changed += refine_node_keyword_arguments(node=child, scope=scope)
    return changed


def rewrite_call_keywords(*, call: Call, scope: KeywordRewriteScope) -> int:
    """Rewrite one call when the callee accepts keyword arguments.

    Args:
        call: The call examined while rewrite one call when the callee accepts
            keyword arguments.
        scope: The scope examined while rewrite one call when the callee
            accepts keyword arguments.

    Returns:
        int produced by this operation.

    """
    signature: KeywordCallSignature | None = signature_for_call(
        call=call,
        scope=scope,
    )
    if signature is None:
        return 0
    return apply_keyword_signature(call=call, signature=signature)


def apply_keyword_signature(
    *,
    call: Call,
    signature: KeywordCallSignature,
) -> int:
    """Apply a known signature to a call when it is syntactically safe.

    Args:
        call: The call examined while apply a known signature to a call when it
            is syntactically safe.
        signature: Signature supplied as KeywordCallSignature for this
            operation.

    Returns:
        int produced by this operation.

    """
    if not call.args:
        return 0
    if any(isinstance(argument, Starred) for argument in call.args):
        return 0
    if any(item.arg is None for item in call.keywords):
        return 0
    positional_count: int = len(call.args)
    keywordable_size: int = signature.keywordable_prefix_size(
        positional_count=positional_count,
    )
    if keywordable_size == 0:
        return 0
    keyword_start: int = signature.positional_only_count
    existing_keywords: set[str] = {
        item.arg for item in call.keywords if item.arg is not None
    }
    new_keywords: list[keyword] = []
    index: int
    argument: expr
    for index, argument in enumerate(iterable=call.args[keyword_start:]):
        parameter_name: str = signature.parameters[keyword_start + index]
        if parameter_name in existing_keywords:
            return 0
        new_keywords.append(keyword(arg=parameter_name, value=argument))
    call.args = call.args[:keyword_start]
    call.keywords = [*new_keywords, *call.keywords]
    return len(new_keywords)


def signature_for_call(
    *,
    call: Call,
    scope: KeywordRewriteScope,
) -> KeywordCallSignature | None:
    """Return a keyword-safe signature for one call expression.

    Args:
        call: The call examined while return a keyword-safe signature for one
            call expression.
        scope: The scope examined while return a keyword-safe signature for one
            call expression.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    name: str | None = callable_name(node=call.func)
    if name is None:
        return None
    builtin_signature: KeywordCallSignature | None = safe_builtin_signature(
        name=name,
        positional_count=len(call.args),
    )
    if builtin_signature is not None:
        return builtin_signature
    if isinstance(call.func, Name):
        return signature_for_named_call(name=call.func.id, scope=scope)
    if isinstance(call.func, Attribute):
        return signature_for_attribute_call(call=call, scope=scope)
    return None


def signature_for_named_call(
    *,
    name: str,
    scope: KeywordRewriteScope,
) -> KeywordCallSignature | None:
    """Return a signature for a simple-name call.

    Args:
        name: Identifier of the name being resolved.
        scope: The scope examined while return a signature for a simple-name
            call.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    function_signature: KeywordCallSignature | None = (
        scope.function_signatures.get(name)
    )
    if function_signature is not None:
        return function_signature
    class_signature: KeywordCallSignature | None = scope.class_signatures.get(
        name,
    )
    if class_signature is not None:
        return class_signature
    receiver_type: TypeSource | None = scope.variable_types.get(name)
    if receiver_type is None:
        return None
    receiver_class: TypeSource | None = receiver_type_base(
        source=receiver_type,
    )
    if receiver_class is None:
        return None
    if isinstance(receiver_class, Name):
        receiver_class_name: str = receiver_class.id
    else:
        receiver_class_name = _ast_node_to_string(node=receiver_class)
    return scope.method_signatures.get((receiver_class_name, "__call__"))


def _receiver_class_name(
    *,
    receiver: expr,
    scope: KeywordRewriteScope,
) -> str | None:
    """Resolve the class name of a method-call receiver expression.

    Args:
        receiver: Receiver supplied as expr for this operation.
        scope: The scope examined while resolve the class name of a method-call
            receiver expression.

    Returns:
        str | None produced by this operation.

    """
    receiver_name: str | None = name_from_target(node=receiver)
    if receiver_name is None:
        return None
    receiver_type: TypeSource | None = scope.variable_types.get(receiver_name)
    if receiver_type is None:
        return None
    receiver_class: TypeSource | None = receiver_type_base(
        source=receiver_type,
    )
    if not isinstance(receiver_class, Name):
        return (
            None
            if receiver_class is None
            else _ast_node_to_string(node=receiver_class)
        )
    if receiver_class.id in builtin_receiver_types():
        return None
    return receiver_class.id


def signature_for_attribute_call(
    *,
    call: Call,
    scope: KeywordRewriteScope,
) -> KeywordCallSignature | None:
    """Return a signature for ``receiver.method(...)`` calls.

    Args:
        call: The call examined while return a signature for
            ``receiver.method(...)`` calls.
        scope: The scope examined while return a signature for
            ``receiver.method(...)`` calls.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    if not isinstance(call.func, Attribute):
        return None
    if _is_super_call(node=call.func.value):
        return _signature_for_super_call(call=call, scope=scope)
    class_name: str | None = _receiver_class_name(
        receiver=call.func.value,
        scope=scope,
    )
    if class_name is None:
        return None
    return scope.method_signatures.get((class_name, call.func.attr))


def _is_super_call(*, node: AST) -> bool:
    """Check if a node is a ``super()`` call.

    Args:
        node: The node examined while check if a node is a ``super()`` call.

    Returns:
        Whether the requested condition holds.

    """
    return (
        isinstance(node, Call)
        and isinstance(node.func, Name)
        and (node.func.id == "super")
    )


def _extract_class_bases(*, class_node: ClassDef) -> list[str]:
    """Extract base class names from a ClassDef node.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        list[str] produced by this operation.

    """
    bases: list[str] = []
    for base in class_node.bases:
        if isinstance(base, Name):
            bases.append(base.id)
        elif isinstance(base, Attribute):
            bases.append(_ast_node_to_string(node=base))
    return bases


def _signature_for_super_call(
    *,
    call: Call,
    scope: KeywordRewriteScope,
) -> KeywordCallSignature | None:
    """Return a signature for ``super().method(...)`` calls.

    Args:
        call: The call examined while return a signature for
            ``super().method(...)`` calls.
        scope: The scope examined while return a signature for
            ``super().method(...)`` calls.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    if not isinstance(call.func, Attribute):
        return None
    method_name: str = call.func.attr
    for base_name in scope.class_bases:
        signature: KeywordCallSignature | None = scope.method_signatures.get(
            (base_name, method_name),
        )
        if signature is not None:
            return signature
    return None


def safe_builtin_signature(
    *,
    name: str,
    positional_count: int,
) -> KeywordCallSignature | None:
    """Return runtime-safe keyword signatures for known stdlib calls.

    Args:
        name: Identifier of the name being resolved.
        positional_count: Positional count supplied as int for this operation.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    signatures: dict[str, KeywordCallSignature] = {
        "ParamSpec": KeywordCallSignature(parameters=("name",)),
        "TypeVar": KeywordCallSignature(parameters=("name",)),
        "accumulate": KeywordCallSignature(parameters=("iterable", "func")),
        "asyncio.sleep": KeywordCallSignature(parameters=("delay", "result")),
        "cast": KeywordCallSignature(parameters=("typ", "val")),
        "compress": KeywordCallSignature(parameters=("data", "selectors")),
        "deque": KeywordCallSignature(parameters=("iterable", "maxlen")),
        "enumerate": KeywordCallSignature(parameters=("iterable", "start")),
        "groupby": KeywordCallSignature(parameters=("iterable", "key")),
        "round": KeywordCallSignature(parameters=("number", "ndigits")),
        "wraps": KeywordCallSignature(
            parameters=("wrapped", "assigned", "updated"),
        ),
    }
    signature: KeywordCallSignature | None = signatures.get(name)
    if signature is None:
        return None
    if name == "TypeVar" and positional_count != 1:
        return None
    return signature


def module_function_signatures(
    *,
    module: Module,
) -> dict[str, KeywordCallSignature]:
    """Return unambiguous top-level function call signatures.

    Args:
        module: The module examined while return unambiguous top-level function
            call signatures.

    Returns:
        dict[str, KeywordCallSignature] produced by this operation.

    """
    grouped: dict[str, list[KeywordCallSignature]] = {}
    statement: stmt
    for statement in module.body:
        if not isinstance(statement, FunctionDef):
            continue
        signature: KeywordCallSignature | None = function_keyword_signature(
            function=statement,
            drop_first=False,
        )
        if signature is not None:
            grouped.setdefault(statement.name, []).append(signature)
    return unique_signatures(grouped=grouped)


def module_class_signatures(
    *,
    module: Module,
) -> dict[str, KeywordCallSignature]:
    """Return constructor signatures for module-level classes.

    Args:
        module: The module examined while return constructor signatures for
            module-level classes.

    Returns:
        dict[str, KeywordCallSignature] produced by this operation.

    """
    signatures: dict[str, KeywordCallSignature] = {}
    statement: stmt
    for statement in module.body:
        if not isinstance(statement, ClassDef):
            continue
        signature: KeywordCallSignature | None = class_keyword_signature(
            class_node=statement,
        )
        if signature is not None:
            signatures[statement.name] = signature
    return signatures


def module_method_signatures(
    *,
    module: Module,
) -> dict[tuple[str, str], KeywordCallSignature]:
    """Return signatures for Python-defined class methods.

    Args:
        module: The module examined while return signatures for Python-defined
            class methods.

    Returns:
        dict[tuple[str, str], KeywordCallSignature] produced by this operation.

    """
    signatures: dict[tuple[str, str], KeywordCallSignature] = {}
    class_node: ClassDef
    for class_node in ast_classes(module=module):
        for item in class_node.body:
            if not isinstance(item, FunctionDef):
                continue
            is_bound_method: bool = method_has_bound_receiver(function=item)
            signature: KeywordCallSignature | None = (
                function_keyword_signature(
                    function=item,
                    drop_first=is_bound_method,
                )
            )
            if signature is not None:
                signatures[class_node.name, item.name] = signature
    return signatures


def class_keyword_signature(
    *,
    class_node: ClassDef,
) -> KeywordCallSignature | None:
    """Infer a safe constructor signature for a class.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    init_method: FunctionDef | None = class_method(
        class_node=class_node,
        name="__init__",
    )
    if init_method is not None:
        return function_keyword_signature(
            function=init_method,
            drop_first=True,
        )
    fields: tuple[str, ...] = class_field_names(class_node=class_node)
    if fields:
        return KeywordCallSignature(parameters=fields)
    return None


def class_method(*, class_node: ClassDef, name: str) -> FunctionDef | None:
    """Return a method from a class body by name.

    Args:
        class_node: Class node supplied as ClassDef for this operation.
        name: Identifier of the name being resolved.

    Returns:
        FunctionDef | None produced by this operation.

    """
    item: stmt
    for item in class_node.body:
        if isinstance(item, FunctionDef) and item.name == name:
            return item
    return None


def class_field_names(*, class_node: ClassDef) -> tuple[str, ...]:
    """Return constructor field names for NamedTuple/dataclass-like classes.

    Args:
        class_node: Class node supplied as ClassDef for this operation.

    Returns:
        tuple[str, ...] produced by this operation.

    """
    if not class_has_base(class_node=class_node, base_name="NamedTuple"):
        return ()
    return tuple(
        item.target.id
        for item in class_node.body
        if isinstance(item, AnnAssign) and isinstance(item.target, Name)
    )


def function_keyword_signature(
    *,
    function: FunctionDef,
    drop_first: bool,
) -> KeywordCallSignature | None:
    """Build a keyword rewrite signature from a function definition.

    Args:
        drop_first: Drop first supplied as bool for this operation.
        function: The function examined while build a keyword rewrite signature
            from a function definition.

    Returns:
        KeywordCallSignature | None produced by this operation.

    """
    if function.args.vararg is not None:
        fixed_count: int = len(function.args.posonlyargs) + len(
            function.args.args,
        )
        if fixed_count == 0:
            return None
    positional_parameters: list[str] = [
        parameter.arg for parameter in function.args.posonlyargs
    ]
    positional_parameters.extend(
        parameter.arg for parameter in function.args.args
    )
    positional_only_count: int = len(function.args.posonlyargs)
    if drop_first and positional_parameters:
        positional_parameters = positional_parameters[1:]
        positional_only_count = max(0, positional_only_count - 1)
    if not positional_parameters:
        return None
    return KeywordCallSignature(
        parameters=tuple(positional_parameters),
        positional_only_count=positional_only_count,
    )


def method_has_bound_receiver(*, function: FunctionDef) -> bool:
    """Return whether method calls bind the first parameter implicitly.

    Args:
        function: The function examined while return whether method calls bind
            the first parameter implicitly.

    Returns:
        Whether the requested condition holds.

    """
    if has_decorator(function=function, decorator_name="staticmethod"):
        return False
    return bool(function.args.args or function.args.posonlyargs)


def unique_signatures(
    *,
    grouped: dict[str, list[KeywordCallSignature]],
) -> dict[str, KeywordCallSignature]:
    """Keep only names with one unambiguous signature.

    Args:
        grouped: Grouped supplied as dict[str, list[KeywordCallSignature]] for
            this operation.

    Returns:
        dict[str, KeywordCallSignature] produced by this operation.

    """
    result: dict[str, KeywordCallSignature] = {}
    name: str
    signatures: list[KeywordCallSignature]
    for name, signatures in grouped.items():
        unique: set[KeywordCallSignature] = set(signatures)
        if len(unique) == 1:
            result[name] = next(iter(unique))
    return result


def seed_local_function_signatures(
    *,
    statements: list[stmt],
    scope: KeywordRewriteScope,
) -> None:
    """Add directly nested function signatures to a scope.

    Args:
        scope: The scope examined while add directly nested function signatures
            to a scope.
        statements: Collection of statements supplied for this operation.

    """
    grouped: dict[str, list[KeywordCallSignature]] = {}
    statement: stmt
    for statement in statements:
        if not isinstance(statement, FunctionDef):
            continue
        signature: KeywordCallSignature | None = function_keyword_signature(
            function=statement,
            drop_first=False,
        )
        if signature is not None:
            grouped.setdefault(statement.name, []).append(signature)
    scope.function_signatures.update(unique_signatures(grouped=grouped))


def seed_local_variable_types(
    *,
    statements: list[stmt],
    scope: KeywordRewriteScope,
) -> None:
    """Seed a scope with simple annotated local variable types.

    Args:
        scope: The scope examined while seed a scope with simple annotated
            local variable types.
        statements: Collection of statements supplied for this operation.

    """
    statement: stmt
    for statement in statements:
        if isinstance(statement, AnnAssign):
            seed_annotation_assignment_type(assignment=statement, scope=scope)
            continue
        if isinstance(statement, For):
            seed_for_loop_target_type(statement=statement, scope=scope)
        if isinstance(statement, FunctionDef | ClassDef):
            continue
        nested: stmt
        for nested in iter_child_statements(statement=statement):
            if isinstance(nested, AnnAssign):
                seed_annotation_assignment_type(assignment=nested, scope=scope)
            elif isinstance(nested, For):
                seed_for_loop_target_type(statement=nested, scope=scope)


def seed_annotation_assignment_type(
    *,
    assignment: AnnAssign,
    scope: KeywordRewriteScope,
) -> None:
    """Seed a variable type from an annotated assignment.

    Args:
        assignment: Assignment supplied as AnnAssign for this operation.
        scope: The scope examined while seed a variable type from an annotated
            assignment.

    """
    name: str | None = name_from_target(node=assignment.target)
    if name is None:
        return
    scope.variable_types[name] = assignment.annotation


def seed_function_parameter_types(
    *,
    function: FunctionDef,
    scope: KeywordRewriteScope,
) -> None:
    """Seed a function scope with annotated parameter types.

    Args:
        function: The function examined while seed a function scope with
            annotated parameter types.
        scope: The scope examined while seed a function scope with annotated
            parameter types.

    """
    parameter: arg
    for parameter in function_parameters(function=function):
        if parameter.annotation is not None:
            scope.variable_types[parameter.arg] = parameter.annotation


def seed_class_attribute_types(
    *,
    class_node: ClassDef,
    scope: KeywordRewriteScope,
) -> None:
    """Seed a class scope with class and self attribute types.

    Args:
        class_node: Class node supplied as ClassDef for this operation.
        scope: The scope examined while seed a class scope with class and self
            attribute types.

    """
    item: stmt
    for item in class_node.body:
        if isinstance(item, AnnAssign) and isinstance(item.target, Name):
            source: TypeSource = item.annotation
            scope.variable_types[item.target.id] = source
            scope.variable_types[f"self.{item.target.id}"] = source
    scope.variable_types.update(
        class_instance_attributes(class_node=class_node),
    )


def module_variable_type_sources(*, module: Module) -> dict[str, TypeSource]:
    """Return module-level annotated variable types.

    Args:
        module: The module examined while return module-level annotated
            variable types.

    Returns:
        dict[str, TypeSource] produced by this operation.

    """
    result: dict[str, TypeSource] = {}
    statement: stmt
    for statement in module.body:
        if not isinstance(statement, AnnAssign):
            continue
        name: str | None = name_from_target(node=statement.target)
        if name is not None:
            result[name] = statement.annotation
    return result


def receiver_type_base(*, source: TypeSource) -> TypeSource | None:
    """Return the nominal receiver type from an annotation source.

    Args:
        source: The source examined while return the nominal receiver type from
            an annotation source.

    Returns:
        TypeSource | None produced by this operation.

    """
    node: expr = source
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return None
    if isinstance(node, Subscript):
        if isinstance(node.value, Name) and node.value.id == "type":
            arguments: tuple[TypeSource, ...] = generic_arguments(
                source=source,
            )
            return arguments[0] if arguments else None
        return node.value
    return node


def builtin_receiver_types() -> frozenset[str]:
    """Return receiver types whose C methods reject keyword arguments.

    Returns:
        frozenset[str] produced by this operation.

    """
    return frozenset(
        {
            "bytes",
            "bytearray",
            "deque",
            "dict",
            "frozenset",
            "list",
            "memoryview",
            "range",
            "set",
            "str",
            "tuple",
        },
    )


def seed_for_loop_target_type(
    *,
    statement: For,
    scope: KeywordRewriteScope,
) -> None:
    """Seed loop-target types from iterable evidence.

    Args:
        scope: The scope examined while seed loop-target types from iterable
            evidence.
        statement: The statement examined while seed loop-target types from
            iterable evidence.

    """
    environment: FunctionTypeEnvironment = FunctionTypeEnvironment(
        names=dict(scope.variable_types),
    )
    iterable_type: TypeSource | None = infer_expression_type(
        node=statement.iter,
        environment=environment,
    )
    if iterable_type is None:
        return
    target_type: TypeSource = element_type(source=iterable_type)
    seed_target_type(target=statement.target, source=target_type, scope=scope)


def seed_target_type(
    *,
    target: AST,
    source: TypeSource,
    scope: KeywordRewriteScope,
) -> None:
    """Seed a target name or tuple from a type source.

    Args:
        scope: The scope examined while seed a target name or tuple from a type
            source.
        source: The source examined while seed a target name or tuple from a
            type source.
        target: The target examined while seed a target name or tuple from a
            type source.

    """
    if isinstance(target, Name):
        scope.variable_types[target.id] = source
        return
    if not isinstance(target, Tuple):
        return
    sources: tuple[TypeSource, ...] = tuple_element_sources(source=source)
    if len(sources) != len(target.elts):
        return
    element: expr
    element_source: TypeSource
    for element, element_source in zip(target.elts, sources, strict=True):
        if isinstance(element, Name):
            scope.variable_types[element.id] = element_source


def tuple_element_sources(*, source: TypeSource) -> tuple[TypeSource, ...]:
    """Return element sources for a fixed tuple source.

    Args:
        source: The source examined while return element sources for a fixed
            tuple source.

    Returns:
        tuple[TypeSource, ...] produced by this operation.

    """
    normalized: TypeSource = normalize_source(source=source)
    if not is_generic(source=normalized, base="tuple"):
        return ()
    arguments: tuple[TypeSource, ...] = generic_arguments(source=normalized)
    if (
        arguments
        and isinstance(arguments[-1], Constant)
        and (arguments[-1].value is Ellipsis)
    ):
        return ()
    return arguments
