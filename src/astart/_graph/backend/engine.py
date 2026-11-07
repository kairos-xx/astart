"""Graph-only strict type and kwargs converter prototype v15.

The converter parses source once, builds semantic indexes over the AST,
edits the AST data model, and renders the final source once with
``ast.unparse``.  The optional benchmark file is never read by conversion
and is used only for a final quality comparison.
"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    AsyncWith,
    Attribute,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    DictComp,
    Div,
    ExceptHandler,
    Expr,
    FloorDiv,
    For,
    FunctionDef,
    GeneratorExp,
    If,
    IfExp,
    Import,
    ImportFrom,
    Lambda,
    List,
    ListComp,
    Load,
    Match,
    MatMult,
    Mod,
    Module,
    Mult,
    Name,
    NamedExpr,
    Raise,
    Return,
    Set,
    SetComp,
    Slice,
    Starred,
    Store,
    Sub,
    Subscript,
    Try,
    Tuple,
    UnaryOp,
    With,
    alias,
    arg,
    comprehension,
    expr,
    fix_missing_locations,
    keyword,
    match_case,
    parse,
    stmt,
    unparse,
    walk,
)
from ast import ParamSpec as AstParamSpec
from ast import Tuple as AstTuple
from ast import TypeVar as AstTypeVar
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import unified_diff
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Self, cast, final
from zipfile import ZipFile

from astart._graph.aprint import aprint
from astart._graph.backend.parentheses import ParenthesizedRenderer
from astart._graph.dispatch import LowercaseTransformer, LowercaseVisitor

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from types import EllipsisType


class Parenthesized(expr):
    """AST node representing a parenthesized expression.

    This custom node preserves parentheses in the output,
    which are otherwise lost by ast.unparse due to operator precedence.
    Stores source positions to enable parentheses re-insertion.
    """

    __slots__ = ("end_pos", "start_pos", "value")

    def __init__(
        self,
        value: expr,
        start_pos: tuple[int, int] | None = None,
        end_pos: tuple[int, int] | None = None,
    ) -> None:
        """Initialize Parenthesized node with value and positions.

        Args:
            end_pos: End pos supplied as tuple[int, int] | None for this
                operation.
            start_pos: Start pos supplied as tuple[int, int] | None for this
                operation.
            value: The value examined while initialize Parenthesized node with
                value and positions.

        """
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

    _fields: ClassVar[tuple[str, ...]] = ("value",)

    def __hash__(self) -> int:
        """Return hash based on object identity."""
        return id(self)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        unknown: Grouped module constant.
        none: Grouped module constant.
        self_names: Grouped module constant.
        min_type_args: Grouped module constant.
        isinstance_arg_count: Grouped module constant.
        paramspec_names: Grouped module constant.
        binary_magic_methods: Grouped module constant.
        parenthesized_renderer: Grouped module constant.
        object: Grouped module constant.
        int: Grouped module constant.
        float: Grouped module constant.
        bool: Grouped module constant.
        str: Grouped module constant.

    """

    unknown: Final[str] = "Unknown"
    none: Final[str] = "None"
    self_names: Final[frozenset[str]] = frozenset({"self", "cls"})
    min_type_args: Final[int] = 2
    isinstance_arg_count: Final[int] = 2
    paramspec_names: Final[frozenset[str]] = frozenset({"P", "Q", "R", "S"})
    binary_magic_methods: Final[dict[str, type]] = {
        "__add__": Add,
        "__sub__": Sub,
        "__mul__": Mult,
        "__truediv__": Div,
        "__floordiv__": FloorDiv,
        "__mod__": Mod,
    }
    parenthesized_renderer: Final[ParenthesizedRenderer] = (
        ParenthesizedRenderer()
    )
    object: Final[str] = "object"
    int: Final[str] = "int"
    float: Final[str] = "float"
    bool: Final[str] = "bool"
    str: Final[str] = "str"


def _is_none_annotation(annotation: expr | None) -> bool:
    """Check if annotation is None type.

    Args:
        annotation: The annotation examined while check if annotation is None
            type.

    Returns:
        Whether the requested condition holds.

    """
    if annotation is None:
        return False
    return (isinstance(annotation, Constant) and annotation.value is None) or (
        isinstance(annotation, Name) and annotation.id == "None"
    )


type TypeKind = Literal[
    "name",
    "generic",
    "union",
    "callable",
    "tuple",
    "ellipsis",
]
type ScopeKind = Literal["module", "class", "function"]
type MethodKind = Literal[
    "function",
    "instance",
    "class",
    "static",
    "property",
]
type InferExprFunction = object


@dataclass(frozen=True, slots=True)
class TypeExpr:
    """Recursive data model for type expressions.

    Attributes:
        args: Args retained as tuple[TypeExpr, ...] by this instance.
        kind: Kind retained as TypeKind by this instance.
        name: Identifier used to refer to the name.
        parameters: Parameters retained as tuple[TypeExpr, ...] by this
            instance.
        return_type: Type information associated with the return.

    """

    kind: TypeKind
    name: str = ""
    args: tuple[TypeExpr, ...] = ()
    parameters: tuple[TypeExpr, ...] = ()
    return_type: TypeExpr | None = None

    @classmethod
    def name_expr(cls, name: str) -> Self:
        """Create a simple name type expression.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Self produced by this operation.

        """
        return cls(kind="name", name=name)

    @classmethod
    def generic(cls, name: str, *args: TypeExpr) -> Self:
        """Create a generic type expression with type arguments.

        Args:
            args: Collection of args supplied for this operation.
            name: Identifier of the name being resolved.

        Returns:
            Self produced by this operation.

        """
        return cls(kind="generic", name=name, args=args)

    @classmethod
    def union(cls, *items: TypeExpr) -> Self:
        """Create a union type expression, flattening nested unions.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            Self produced by this operation.

        """
        flat: list[TypeExpr] = []
        item: TypeExpr
        for item in items:
            if item.is_unknown():
                continue
            if item.kind == "union":
                flat.extend(item.args)
            else:
                flat.append(item)
        by_key: dict[str, TypeExpr] = {}
        for item in flat:
            by_key[item.key()] = item
        values: tuple[TypeExpr, ...] = tuple(
            sorted(by_key.values(), key=lambda value: value.key()),
        )
        if not values:
            return cls.name_expr(name=Constants.object)
        if len(values) == 1:
            return cast(typ="Self", val=values[0])
        return cls(kind="union", args=values)

    @classmethod
    def callable_expr(
        cls,
        parameters: Sequence[TypeExpr],
        return_type: TypeExpr,
    ) -> Self:
        """Create a callable type expression.

        Args:
            parameters: Collection of parameters supplied for this operation.
            return_type: Return type supplied as TypeExpr for this operation.

        Returns:
            Self produced by this operation.

        """
        return cls(
            kind="callable",
            name="Callable",
            parameters=tuple(parameters),
            return_type=return_type,
        )

    @classmethod
    def ellipsis_expr(cls) -> Self:
        """Create an ellipsis type expression.

        Returns:
            Self produced by this operation.

        """
        return cls(kind="ellipsis", name="...")

    def is_unknown(self) -> bool:
        """Check if this type expression represents an unknown type.

        Returns:
            Whether the requested condition holds.

        """
        return self.kind == "name" and self.name == Constants.unknown

    def key(self) -> str:
        """Generate a unique string key for this type expression.

        Returns:
            str produced by this operation.

        """
        if self.kind in {"name", "ellipsis"}:
            return f"{self.kind}:{self.name}"
        if self.kind == "generic":
            args_str: str = ",".join(arg.key() for arg in self.args)
            return f"{self.name}[{args_str}]"
        if self.kind == "union":
            return "|".join(arg.key() for arg in self.args)
        if self.kind == "tuple":
            args_str = ",".join(arg.key() for arg in self.args)
            return f"tuple({args_str})"
        ret: str = (
            self.return_type.key()
            if self.return_type is not None
            else Constants.object
        )
        params_str: str = ",".join(arg.key() for arg in self.parameters)
        return f"Callable[{params_str}]->{ret}"

    def to_ast(self) -> expr:
        """Convert to an AST expression without text manipulation.

        Returns:
            expr produced by this operation.

        """
        if self.kind == "name":
            return Name(id=self.name, ctx=Load())
        if self.kind == "ellipsis":
            return Constant(value=Ellipsis)
        if self.kind == "generic":
            slice_node: expr
            if len(self.args) == 1:
                slice_node = self.args[0].to_ast()
            else:
                slice_node = Tuple(
                    elts=[arg.to_ast() for arg in self.args],
                    ctx=Load(),
                )
            return Subscript(
                value=Name(id=self.name, ctx=Load()),
                slice=slice_node,
                ctx=Load(),
            )
        if self.kind == "union":
            expression: expr = self.args[0].to_ast()
            for item in self.args[1:]:
                expression = BinOp(
                    left=expression,
                    op=BitOr(),
                    right=item.to_ast(),
                )
            return expression
        if self.kind == "callable":
            params: expr
            if (
                len(self.parameters) == 1
                and self.parameters[0].kind == "ellipsis"
            ):
                params = Constant(value=Ellipsis)
            else:
                params = List(
                    elts=[parameter.to_ast() for parameter in self.parameters],
                    ctx=Load(),
                )
            ret: TypeExpr = self.return_type or TypeExpr.name_expr(
                name=Constants.object,
            )
            return Subscript(
                value=Name(id="Callable", ctx=Load()),
                slice=Tuple(elts=[params, ret.to_ast()], ctx=Load()),
                ctx=Load(),
            )
        return Name(id=Constants.object, ctx=Load())

    def to_source(self) -> str:
        """Convert this type expression to source code string.

        Returns:
            Rendered source text produced by this operation.

        """
        return unparse(ast_obj=self.to_ast())


_INT_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.int)
_FLOAT_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.float)
_STR_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.str)
_BOOL_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.bool)
_NONE_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.none)
_OBJECT_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.object)
_UNKNOWN_TYPE: Final[TypeExpr] = TypeExpr.name_expr(name=Constants.unknown)


@dataclass(frozen=True, slots=True)
class Reason:
    """One inference reason.

    Attributes:
        confidence: Confidence assigned to this inference or observation.
        message: Explanation associated with this result.

    """

    message: str
    confidence: float


@dataclass(slots=True)
class Evidence:
    """A type with confidence and reasons.

    Attributes:
        confidence: Confidence assigned to this inference or observation.
        expression: AST expression associated with this record.
        reasons: Reasons retained as tuple[Reason, ...] by this instance.

    """

    expression: TypeExpr
    confidence: float = 0.5
    reasons: tuple[Reason, ...] = ()

    @classmethod
    def unknown(cls) -> Self:
        """Create an unknown evidence instance.

        Returns:
            Self produced by this operation.

        """
        return cls(expression=_UNKNOWN_TYPE, confidence=0.0)

    def is_unknown(self) -> bool:
        """Check if this evidence represents an unknown type.

        Returns:
            Whether the requested condition holds.

        """
        return self.expression.is_unknown()


@dataclass(frozen=True, slots=True)
class BranchCondition:
    """A branch-local predicate used for call-site specialization.

    Attributes:
        false_reachable: False reachable retained as bool by this instance.
        false_type: Type information associated with the false.
        name: Identifier used to refer to the name.
        reason: Explanation associated with this result.
        true_reachable: True reachable retained as bool by this instance.
        true_type: Type information associated with the true.

    """

    name: str
    true_type: TypeExpr | None = None
    false_type: TypeExpr | None = None
    true_reachable: bool = True
    false_reachable: bool = True
    reason: str = ""


@dataclass(frozen=True, slots=True)
class SpecializedCallKey:
    """Cycle guard key for recursive call-return specialization.

    Attributes:
        argument_signature: Argument signature retained as str by this
            instance.
        function_name: Identifier used to refer to the function.

    """

    function_name: str
    argument_signature: str


@dataclass(slots=True)
class FunctionInfo:
    """Semantic function model.

    Attributes:
        class_name: Identifier used to refer to the class.
        local_types: Local types retained as dict[str, TypeExpr] by this
            instance.
        method_kind: Method kind retained as MethodKind by this instance.
        node: AST node associated with this record.
        param_types: Param types retained as dict[str, TypeExpr] by this
            instance.
        qualified_name: Identifier used to refer to the qualified.
        return_type: Type information associated with the return.

    """

    node: FunctionDef | AsyncFunctionDef
    qualified_name: str
    class_name: str | None = None
    method_kind: MethodKind = "function"
    param_types: dict[str, TypeExpr] = field(default_factory=dict)
    return_type: TypeExpr = _UNKNOWN_TYPE
    local_types: dict[str, TypeExpr] = field(default_factory=dict)

    def public_parameters(self) -> list[arg]:
        """Get all public parameters (positional and keyword-only).

        Returns:
            list[arg] produced by this operation.

        """
        params: list[arg] = []
        params.extend(self.node.args.posonlyargs)
        params.extend(self.node.args.args)
        params.extend(self.node.args.kwonlyargs)
        return params

    def implicit_parameter_name(self) -> str | None:
        """Get the implicit parameter name (self/cls) if applicable.

        Returns:
            str | None produced by this operation.

        """
        if self.class_name is None or self.method_kind == "static":
            return None
        positional: list[arg] = [
            *self.node.args.posonlyargs,
            *self.node.args.args,
        ]
        if not positional:
            return None
        if self.method_kind in {"instance", "class", "property"}:
            return positional[0].arg
        return None

    def explicit_parameters(self) -> list[arg]:
        """Get all explicit parameters excluding implicit self/cls.

        Returns:
            list[arg] produced by this operation.

        """
        implicit_name: str | None = self.implicit_parameter_name()
        return [
            parameter
            for parameter in self.public_parameters()
            if parameter.arg != implicit_name
        ]


@dataclass(slots=True)
class ClassInfo:
    """Semantic class model.

    Attributes:
        attributes: Attributes retained as dict[str, TypeExpr] by this
            instance.
        bases: Bases retained as tuple[str, ...] by this instance.
        is_namedtuple_shape: Is namedtuple shape retained as bool by this
            instance.
        is_protocol_shape: Is protocol shape retained as bool by this instance.
        methods: Methods retained as dict[str, FunctionInfo] by this instance.
        name: Identifier used to refer to the name.
        node: AST node associated with this record.

    """

    node: ClassDef
    name: str
    bases: tuple[str, ...]
    methods: dict[str, FunctionInfo] = field(default_factory=dict)
    attributes: dict[str, TypeExpr] = field(default_factory=dict)
    is_protocol_shape: bool = False
    is_namedtuple_shape: bool = False


@dataclass(slots=True)
class LazyStubIndex:
    """Tiny lazy typeshed-backed signature index for known call facts.

    Attributes:
        callable_returns: Callable returns retained as dict[str, TypeExpr] by
            this instance.
        loaded_modules: Loaded modules retained as set[str] by this instance.
        method_returns: Method returns retained as dict[tuple[str, str],
            TypeExpr] by this instance.
        path: Path to the path used by this instance.

    """

    path: Path | None = None
    loaded_modules: set[str] = field(default_factory=set)
    callable_returns: dict[str, TypeExpr] = field(default_factory=dict)
    method_returns: dict[tuple[str, str], TypeExpr] = field(
        default_factory=dict,
    )

    @classmethod
    def default(cls) -> Self:
        """Create a default LazyStubIndex with common builtin signatures.

        Returns:
            Self produced by this operation.

        """
        candidate: Path = Path("/mnt/data/typeshed(1).zip")
        index: Self = cls(path=candidate if candidate.exists() else None)
        index.method_returns.update(
            {
                ("Path", "read_text"): _STR_TYPE,
                ("Path", "write_text"): _INT_TYPE,
                ("Path", "unlink"): _NONE_TYPE,
                ("str", "upper"): _STR_TYPE,
                ("str", "lower"): _STR_TYPE,
                ("str", "strip"): _STR_TYPE,
            },
        )
        index.callable_returns.update(
            {
                "importlib.import_module": TypeExpr.name_expr(
                    name="ModuleType",
                ),
                "__import__": TypeExpr.name_expr(name="ModuleType"),
            },
        )
        return index

    def ensure_module(self, *, module_name: str) -> None:
        """Lazily read a typeshed branch only when a module is consulted.

        Args:
            module_name: Identifier of the module being resolved.

        """
        if self.path is None or module_name in self.loaded_modules:
            return
        self.loaded_modules.add(module_name)
        try:
            with ZipFile(file=self.path) as archive:
                names: list[str] = [
                    name
                    for name in archive.namelist()
                    if name.endswith(
                        (
                            (f"stdlib/{module_name}.pyi"),
                            (f"stdlib/{module_name}/__init__.pyi"),
                        ),
                    )
                ]
                if names:
                    _ = archive.read(name=names[0])
        except OSError:
            return


@dataclass(slots=True)
class ScopeState:
    """A mutable type scope during analysis.

    Attributes:
        local_classes: Local classes retained as set[str] by this instance.
        name: Identifier used to refer to the name.
        owner: Owner retained as FunctionInfo | None by this instance.
        parent: Parent retained as ScopeState | None by this instance.
        variables: Variables retained as dict[str, TypeExpr] by this instance.

    """

    name: str
    variables: dict[str, TypeExpr] = field(default_factory=dict)
    parent: ScopeState | None = None
    local_classes: set[str] = field(default_factory=set)
    owner: FunctionInfo | None = None

    def get(self, name: str) -> TypeExpr:
        """Get a variable type from this scope or parent scopes.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            TypeExpr produced by this operation.

        """
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.get(name=name)
        return _UNKNOWN_TYPE

    def set(self, name: str, type_expr: TypeExpr) -> None:
        """Set a variable type, merging with existing type if present.

        Args:
            name: Identifier of the name being resolved.
            type_expr: The type expr examined while set a variable type,
                merging with existing type if present.

        """
        old: TypeExpr | None = self.variables.get(name)
        self.variables[name] = (
            type_expr
            if old is None
            else merge_types(left=old, right=type_expr)
        )

    def set_exact(self, name: str, type_expr: TypeExpr) -> None:
        """Set a variable type without merging.

        Args:
            name: Identifier of the name being resolved.
            type_expr: The type expr examined while set a variable type without
                merging.

        """
        self.variables[name] = type_expr

    def clone(self, *, name: str | None = None) -> Self:
        """Create a copy of this scope with an optional new name.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Self produced by this operation.

        """
        return self.__class__(
            name=name or self.name,
            variables=dict(self.variables),
            parent=self.parent,
            local_classes=set(self.local_classes),
            owner=self.owner,
        )


class GraphIndexer(LowercaseVisitor):
    """Build class and function indexes from AST."""

    def __init__(self) -> None:
        """Initialize the GraphIndexer."""
        self.classes: dict[str, ClassInfo] = {}
        self.functions: dict[str, FunctionInfo] = {}
        self.functions_by_node_id: dict[int, FunctionInfo] = {}
        self.class_stack: list[str] = []
        self.scope_path: list[str] = []

    def visit_classdef(self, node: ClassDef) -> None:
        """Visit a ClassDef node and build class information.

        Args:
            node: The node examined while visit a ClassDef node and build class
                information.

        """
        bases: tuple[str, ...] = tuple(
            expr_name(node=base) for base in node.bases
        )
        info: ClassInfo = ClassInfo(
            node=node,
            name=node.name,
            bases=bases,
            is_protocol_shape=node.name.startswith("Supports"),
            is_namedtuple_shape=is_plain_result_class(node=node),
        )
        self.classes[node.name] = info
        self.class_stack.append(node.name)
        self.scope_path.append(node.name)
        stmt_item: stmt
        for stmt_item in node.body:
            if isinstance(stmt_item, (FunctionDef, AsyncFunctionDef)):
                function_info: FunctionInfo = self._function_info(
                    node=stmt_item,
                )
                function_info.method_kind = method_kind_from_decorators(
                    function=stmt_item,
                )
                info.methods[stmt_item.name] = function_info
                self.functions[function_info.qualified_name] = function_info
                self.functions_by_node_id[id(stmt_item)] = function_info
            elif isinstance(stmt_item, Assign):
                class_attr: tuple[str, TypeExpr] | None = (
                    infer_class_assignment(statement=stmt_item)
                )
                if class_attr is not None:
                    info.attributes[class_attr[0]] = class_attr[1]
        for stmt_item in node.body:
            if isinstance(stmt_item, Assign):
                update_method_kind_from_descriptor_assignment(
                    statement=stmt_item,
                    class_info=info,
                )
        for stmt_item in node.body:
            self.visit(node=stmt_item)
        self.scope_path.pop()
        self.class_stack.pop()

    def visit_functiondef(self, node: FunctionDef) -> None:
        """Visit a FunctionDef node and build function information.

        Args:
            node: The node examined while visit a FunctionDef node and build
                function information.

        """
        info: FunctionInfo = self._function_info(node=node)
        self.functions.setdefault(info.qualified_name, info)
        self.functions_by_node_id.setdefault(id(node), info)
        self.functions_by_node_id.setdefault(id(node), info)
        self.scope_path.append(node.name)
        self.generic_visit(node=node)
        self.scope_path.pop()

    def visit_asyncfunctiondef(self, node: AsyncFunctionDef) -> None:
        """Visit an AsyncFunctionDef node and build function information.

        Args:
            node: The node examined while visit an AsyncFunctionDef node and
                build function information.

        """
        info: FunctionInfo = self._function_info(node=node)
        self.functions.setdefault(info.qualified_name, info)
        self.functions_by_node_id.setdefault(id(node), info)
        self.scope_path.append(node.name)
        self.generic_visit(node=node)
        self.scope_path.pop()

    def _function_info(
        self,
        node: FunctionDef | AsyncFunctionDef,
    ) -> FunctionInfo:
        """Index metadata for a function definition.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Indexed metadata describing the function definition.

        """
        class_name: str | None = (
            self.class_stack[-1] if self.class_stack else None
        )
        qualified_name: str = ".".join([*self.scope_path, node.name])
        if not qualified_name:
            qualified_name = node.name
        if class_name is None and len(self.scope_path) == 0:
            qualified_name = node.name
        return FunctionInfo(
            node=node,
            qualified_name=qualified_name,
            class_name=class_name,
        )


class InferenceEngine:
    """Infer types over indexed graph."""

    def __init__(
        self,
        module: Module,
        index: GraphIndexer,
        source: str = "",
    ) -> None:
        """Initialize the InferenceEngine with module and index.

        Args:
            index: Index identifying a position in the relevant sequence or
                source.
            module: The module examined while initialize the InferenceEngine
                with module and index.
            source: The source examined while initialize the InferenceEngine
                with module and index.

        """
        self.module: Module = module
        self.index: GraphIndexer = index
        self.source: str = source
        self.module_scope: ScopeState = ScopeState(name="module")
        self.function_by_node: dict[int, FunctionInfo] = dict(
            index.functions_by_node_id,
        )
        self.calls_by_name: dict[str, list[Call]] = defaultdict(list)
        self.local_class_names: set[str] = find_local_class_names(
            module=module,
        )
        self.stubs: LazyStubIndex = LazyStubIndex.default()
        self.active_specializations: set[SpecializedCallKey] = set()

    def run(self) -> None:
        """Run the type inference engine iteratively until convergence."""
        self._seed_module_scope()
        for _ in range(10):
            before: str = self._signature_key()
            self._analyze_module_calls()
            for info in list(self.index.functions_by_node_id.values()):
                self._analyze_function(info=info)
            self._propagate_override_signatures()
            after: str = self._signature_key()
            if after == before:
                break

    def resolve_callable(self, name: str) -> FunctionInfo | None:
        """Resolve a callable name to its FunctionInfo.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            FunctionInfo | None produced by this operation.

        """
        if name in self.index.functions:
            return self.index.functions[name]
        if "." in name:
            tail: str = name.rsplit(sep=".", maxsplit=1)[-1]
            candidates: list[FunctionInfo] = [
                info
                for info in self.index.functions.values()
                if info.node.name == tail
            ]
            if len(candidates) == 1:
                return candidates[0]
        candidates = [
            info
            for key, info in self.index.functions.items()
            if key.endswith(f".{name}") or info.node.name == name
        ]
        if len(candidates) == 1:
            return candidates[0]
        return None

    def bind_target(
        self,
        target: AST,
        type_expr: TypeExpr,
        scope: ScopeState,
    ) -> None:
        """Bind a target node to a type expression in the given scope.

        Args:
            scope: The scope examined while bind a target node to a type
                expression in the given scope.
            target: The target examined while bind a target node to a type
                expression in the given scope.
            type_expr: The type expr examined while bind a target node to a
                type expression in the given scope.

        """
        if isinstance(target, Name):
            self._bind_name_target(
                target=target,
                type_expr=type_expr,
                scope=scope,
            )
        elif isinstance(target, Attribute):
            self._bind_attribute_target(
                target=target,
                type_expr=type_expr,
                scope=scope,
            )
        elif isinstance(target, (Tuple, List)):
            self._bind_sequence_target(
                target=target,
                type_expr=type_expr,
                scope=scope,
            )

    def infer_expr(self, expression: expr, scope: ScopeState) -> TypeExpr:
        """Infer the type of an expression within a given scope.

        Args:
            expression: The expression examined while infer the type of an
                expression within a given scope.
            scope: The scope examined while infer the type of an expression
                within a given scope.

        Returns:
            TypeExpr produced by this operation.

        """
        result: TypeExpr | None = None
        if isinstance(expression, (Constant, Name)):
            result = self._infer_literal(expression=expression, scope=scope)
        elif isinstance(expression, (List, Set, Tuple, Dict)):
            result = self._infer_collection_literal(
                expression=expression,
                scope=scope,
            )
        elif isinstance(
            expression,
            (DictComp, ListComp, SetComp, GeneratorExp),
        ):
            result = self._infer_comprehension(
                expression=expression,
                scope=scope,
            )
        else:
            result = self._infer_operation(expression=expression, scope=scope)
        if result is not None:
            return result
        if isinstance(expression, NamedExpr):
            value_type: TypeExpr = self.infer_expr(
                expression=expression.value,
                scope=scope,
            )
            self.bind_target(
                target=expression.target,
                type_expr=value_type,
                scope=scope,
            )
            return value_type
        return (
            self._infer_call(expression=expression, scope=scope)
            if isinstance(expression, Call)
            else _UNKNOWN_TYPE
        )

    @staticmethod
    def _should_skip_statement(*, statement: stmt) -> bool:
        """Check if statement should be skipped (nested definitions).

        Args:
            statement: The statement examined while check if statement should
                be skipped (nested definitions).

        Returns:
            Whether the requested condition holds.

        """
        return isinstance(statement, (FunctionDef, AsyncFunctionDef, ClassDef))

    @staticmethod
    def _apply_special_signature(*, info: FunctionInfo) -> None:
        """Apply special function signature if available.

        Args:
            info: The info examined while apply special function signature if
                available.

        """
        special_signature: tuple[dict[str, TypeExpr], TypeExpr] | None = (
            infer_special_function_signature(
                function=info.node,
                class_name=info.class_name,
            )
        )
        if special_signature is not None:
            special_params, special_return = special_signature
            info.param_types.update(special_params)
            info.return_type = special_return

    @staticmethod
    def _apply_none_default_union(
        *,
        parameter: arg,
        defaults: dict[str, expr],
        info: FunctionInfo,
    ) -> None:
        """Apply None union for parameters with None defaults.

        Args:
            defaults: Defaults supplied as dict[str, expr] for this operation.
            info: The info examined while apply None union for parameters with
                None defaults.
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter.arg in defaults and is_none_literal(
            node=defaults[parameter.arg],
        ):
            current_type: TypeExpr = info.param_types.get(
                parameter.arg,
                _UNKNOWN_TYPE,
            )
            if current_type.is_unknown():
                current_type = _OBJECT_TYPE
            info.param_types[parameter.arg] = TypeExpr.union(
                current_type,
                _NONE_TYPE,
            )

    @staticmethod
    def _apply_none_comparison_union(
        *,
        parameter: arg,
        info: FunctionInfo,
    ) -> None:
        """Union ``None`` into params compared against ``None`` in the body.

        Args:
            info: The info examined while union ``None`` into params compared
                against ``None`` in the body.
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter.annotation is not None:
            return
        if parameter.arg in {
            info.node.args.vararg.arg if info.node.args.vararg else "",
            info.node.args.kwarg.arg if info.node.args.kwarg else "",
        }:
            return
        if not parameter_compared_to_none(
            function=info.node,
            name=parameter.arg,
        ):
            return
        current_type: TypeExpr = info.param_types.get(
            parameter.arg,
            _UNKNOWN_TYPE,
        )
        if current_type.is_unknown():
            current_type = _OBJECT_TYPE
        if _NONE_TYPE.key() in {
            current_type.key(),
            *(arg_expr.key() for arg_expr in current_type.args),
        }:
            return
        info.param_types[parameter.arg] = TypeExpr.union(
            current_type,
            _NONE_TYPE,
        )

    @staticmethod
    def _widen_redundant_isinstance_param(
        *,
        parameter: arg,
        info: FunctionInfo,
    ) -> None:
        """Widen a param to ``object`` for a redundant ``isinstance`` guard.

        If a parameter is narrowed to exactly the type it is later
        ``isinstance``-checked against, the guard can never be false, so the
        narrowing is wrong: the author expects other types. Widen to
        ``object`` (only for a single concrete inferred type, never a union,
        whose members are meaningfully discriminated by the guard).

        For a union, widen when every member is covered by an isinstance
        check AND the function has a fallback branch (a return outside all
        isinstance guards), which proves the author expects types beyond the
        inferred union.


        Args:
            info: The info examined while widen a param to ``object`` for a
                redundant ``isinstance`` guard.
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter.annotation is not None:
            return
        current: TypeExpr = info.param_types.get(parameter.arg, _UNKNOWN_TYPE)
        if current.key() in {_OBJECT_TYPE.key(), _UNKNOWN_TYPE.key()}:
            return
        checked: set[str] = parameter_isinstance_check_names(
            function=info.node,
            name=parameter.arg,
        )
        if current.kind == "name" and current.name in checked:
            info.param_types[parameter.arg] = _OBJECT_TYPE
            return
        if (
            current.kind == "union"
            and all(
                m.kind == "name" and m.name in checked for m in current.args
            )
            and parameter_has_isinstance_fallback(
                function=info.node,
                name=parameter.arg,
            )
        ):
            info.param_types[parameter.arg] = _OBJECT_TYPE

    @staticmethod
    def _apply_vararg_kwarg_types(
        *,
        parameter: arg,
        info: FunctionInfo,
    ) -> None:
        """Apply vararg/kwarg types if applicable.

        Args:
            info: The info examined while apply vararg/kwarg types if
                applicable.
            parameter: Parameter supplied as arg for this operation.

        """
        if parameter is info.node.args.vararg:
            info.param_types[parameter.arg] = infer_vararg_item_type(
                function=info.node,
                name=parameter.arg,
            )
        if parameter is info.node.args.kwarg:
            info.param_types[parameter.arg] = infer_kwarg_value_type(
                function=info.node,
                name=parameter.arg,
            )

    @staticmethod
    def _infer_return_type(
        *,
        info: FunctionInfo,
        returns: list[TypeExpr],
    ) -> None:
        """Infer return type for function.

        Args:
            info: The info examined while infer return type for function.
            returns: Returns supplied as list[TypeExpr] for this operation.

        """
        special_return: TypeExpr | None = infer_special_return_type(
            function=info.node,
        )
        dunder_signature: tuple[dict[str, TypeExpr], TypeExpr] | None = (
            _infer_dunder_signature(
                function=info.node,
                class_name=info.class_name,
            )
        )
        if dunder_signature is not None and (
            not info.return_type.is_unknown()
        ):
            return
        if special_return is not None:
            info.return_type = special_return
        elif returns:
            info.return_type = drop_none_when_no_none_return(
                function=info.node,
                type_expr=merge_many(types=returns),
            )
        elif has_yield(function=info.node):
            info.return_type = TypeExpr.generic("Generator", _OBJECT_TYPE)

    @staticmethod
    def _bind_name_target(
        target: Name,
        type_expr: TypeExpr,
        scope: ScopeState,
    ) -> None:
        """Bind a name target to a type expression.

        Args:
            scope: The scope examined while bind a name target to a type
                expression.
            target: The target examined while bind a name target to a type
                expression.
            type_expr: The type expr examined while bind a name target to a
                type expression.

        """
        scope.set(name=target.id, type_expr=type_expr)
        if scope.owner is not None and should_annotate_name(name=target.id):
            previous: TypeExpr | None = scope.owner.local_types.get(target.id)
            scope.owner.local_types[target.id] = (
                type_expr
                if previous is None
                else merge_types(left=previous, right=type_expr)
            )

    @staticmethod
    def _infer_literal(
        expression: Constant | Name,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for literal expressions.

        Args:
            expression: The expression examined while infer types for literal
                expressions.
            scope: The scope examined while infer types for literal
                expressions.

        Returns:
            TypeExpr produced by this operation.

        """
        if isinstance(expression, Constant):
            return infer_constant(value=expression.value)
        if expression.id in scope.local_classes:
            return TypeExpr.generic("type", _OBJECT_TYPE)
        value: TypeExpr = scope.get(name=expression.id)
        return (
            value
            if not value.is_unknown()
            else infer_builtin_name(name=expression.id)
        )

    def _propagate_override_signatures(self) -> None:
        """Propagate override signatures."""
        class_info: ClassInfo
        for class_info in self.index.classes.values():
            base_name: str
            for base_name in class_info.bases:
                base_info: ClassInfo | None = self.index.classes.get(base_name)
                if base_info is None:
                    continue
                method_name: str
                method_info: FunctionInfo
                for method_name, method_info in class_info.methods.items():
                    base_method: FunctionInfo | None = base_info.methods.get(
                        method_name,
                    )
                    if base_method is None:
                        continue
                    parameter_name: str
                    parameter_type: TypeExpr
                    for (
                        parameter_name,
                        parameter_type,
                    ) in method_info.param_types.items():
                        if parameter_name in Constants.self_names:
                            continue
                        old_type: TypeExpr = base_method.param_types.get(
                            parameter_name,
                            _UNKNOWN_TYPE,
                        )
                        if (
                            old_type.is_unknown()
                            or old_type.key() == _OBJECT_TYPE.key()
                        ):
                            base_method.param_types[parameter_name] = (
                                parameter_type
                            )
                    if (
                        base_method.return_type.is_unknown()
                        or base_method.return_type.key()
                        in {_NONE_TYPE.key(), _OBJECT_TYPE.key()}
                    ):
                        base_method.return_type = method_info.return_type

    def _signature_key(self) -> str:
        """Signature key.

        Returns:
            Stable representation of the inferred function signature.

        """
        parts: list[str] = []
        for key, info in sorted(
            ((f"{info.qualified_name}:{id(info.node)}"), info)
            for info in self.index.functions_by_node_id.values()
        ):
            params: str = ",".join(
                (
                    (f"{name}:{type_expr.key()}")
                    for name, type_expr in sorted(info.param_types.items())
                ),
            )
            parts.append(f"{key}->{info.return_type.key()}({params})")
        return "|".join(parts)

    def _seed_module_scope(self) -> None:
        """Seed module scope."""
        self.module_scope.variables.update(
            {"None": _NONE_TYPE, "True": _BOOL_TYPE, "False": _BOOL_TYPE},
        )
        class_name: str
        for class_name in self.index.classes:
            if class_name not in self.local_class_names:
                self.module_scope.variables[class_name] = TypeExpr.name_expr(
                    name=class_name,
                )
        function_name: str
        for function_name, info in self.index.functions.items():
            if "." not in function_name:
                self.module_scope.variables[function_name] = (
                    TypeExpr.callable_expr(
                        parameters=[_UNKNOWN_TYPE],
                        return_type=info.return_type,
                    )
                )

    def _analyze_module_calls(self) -> None:
        """Analyze module calls."""
        for node in walk(node=self.module):
            if isinstance(node, Call):
                name: str = expr_name(node=node.func)
                self.calls_by_name[name].append(node)
                self._connect_call_arguments(
                    call=node,
                    name=name,
                    scope=self.module_scope,
                )

    def _connect_call_arguments(
        self,
        call: Call,
        name: str,
        scope: ScopeState,
    ) -> None:
        """Connect call arguments.

        Args:
            call: Call expression whose arguments are being analyzed.
            name: Identifier used for lookup or matching.
            scope: Lexical scope containing the expression.

        """
        info: FunctionInfo | None = self.resolve_callable(name=name)
        if info is None:
            return
        params: list[arg] = info.explicit_parameters()
        arg_node: expr
        for index, arg_node in enumerate(iterable=call.args):
            if index >= len(params):
                continue
            param: arg = params[index]
            inferred: TypeExpr = self.infer_expr(
                expression=arg_node,
                scope=scope,
            )
            if not inferred.is_unknown():
                info.param_types[param.arg] = merge_types(
                    left=info.param_types.get(param.arg, inferred),
                    right=inferred,
                )
        kw: keyword
        for kw in call.keywords:
            if kw.arg is None:
                continue
            inferred = self.infer_expr(expression=kw.value, scope=scope)
            if not inferred.is_unknown():
                info.param_types[kw.arg] = merge_types(
                    left=info.param_types.get(kw.arg, inferred),
                    right=inferred,
                )

    def _specialized_call_return(
        self,
        *,
        info: FunctionInfo,
        call: Call,
        caller_scope: ScopeState,
    ) -> TypeExpr:
        """Infer one call result under caller argument constraints.

        Args:
            call: The call examined while infer one call result under caller
                argument constraints.
            caller_scope: Caller scope supplied as ScopeState for this
                operation.
            info: The info examined while infer one call result under caller
                argument constraints.

        Returns:
            TypeExpr produced by this operation.

        """
        call_scope: ScopeState = self._call_scope(
            info=info,
            call=call,
            caller_scope=caller_scope,
        )
        signature: str = ",".join(
            (
                (f"{name}:{type_expr.key()}")
                for name, type_expr in sorted(call_scope.variables.items())
                if name not in {"self", "cls"}
            ),
        )
        key: SpecializedCallKey = SpecializedCallKey(
            function_name=info.qualified_name,
            argument_signature=signature,
        )
        if key in self.active_specializations:
            return info.return_type
        self.active_specializations.add(key)
        try:
            returns: list[TypeExpr] = []
            self._execute_statements(
                body=info.node.body,
                scope=call_scope,
                returns=returns,
            )
            if returns:
                return drop_none_when_no_none_return(
                    function=info.node,
                    type_expr=merge_many(types=returns),
                )
            return info.return_type
        finally:
            self.active_specializations.remove(key)

    def _call_scope(
        self,
        *,
        info: FunctionInfo,
        call: Call,
        caller_scope: ScopeState,
    ) -> ScopeState:
        """Call scope.

        Args:
            call: Call expression whose arguments are being analyzed.
            caller_scope: Scope at the call site.
            info: Indexed function metadata used by this operation.

        Returns:
            Scope state resulting from the analysis.

        """
        scope: ScopeState = ScopeState(
            name=(f"call:{info.qualified_name}"),
            parent=self.module_scope,
            local_classes=local_class_names(function=info.node),
            owner=info,
        )
        if info.class_name is not None:
            self_type: TypeExpr = TypeExpr.name_expr(name=info.class_name)
            cls_type: TypeExpr = TypeExpr.generic("type", self_type)
            scope.set_exact(name="self", type_expr=self_type)
            scope.set_exact(name="cls", type_expr=cls_type)
            implicit_name: str | None = info.implicit_parameter_name()
            if implicit_name is not None:
                scope.set_exact(
                    name=implicit_name,
                    type_expr=cls_type
                    if info.method_kind == "class"
                    else self_type,
                )
        parameter: arg
        for parameter in all_args(node=info.node):
            if parameter.arg in info.param_types:
                scope.set_exact(
                    name=parameter.arg,
                    type_expr=info.param_types[parameter.arg],
                )
        params: list[arg] = info.explicit_parameters()
        index: int
        arg_node: expr
        for index, arg_node in enumerate(iterable=call.args):
            if index >= len(params):
                continue
            scope.set_exact(
                name=params[index].arg,
                type_expr=self.infer_expr(
                    expression=arg_node,
                    scope=caller_scope,
                ),
            )
        keyword_node: keyword
        for keyword_node in call.keywords:
            if keyword_node.arg is None:
                continue
            scope.set_exact(
                name=keyword_node.arg,
                type_expr=self.infer_expr(
                    expression=keyword_node.value,
                    scope=caller_scope,
                ),
            )
        return scope

    def _handle_return_statement(
        self,
        *,
        statement: Return,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle Return statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle Return statement.
            statement: The statement examined while handle Return statement.

        Returns:
            ScopeState produced by this operation.

        """
        if statement.value is None:
            returns.append(_NONE_TYPE)
        else:
            returns.append(
                self.infer_expr(expression=statement.value, scope=scope),
            )
        return scope

    def _handle_assign_statement(
        self,
        *,
        statement: Assign,
        scope: ScopeState,
    ) -> None:
        """Handle Assign statement.

        Args:
            scope: The scope examined while handle Assign statement.
            statement: The statement examined while handle Assign statement.

        """
        value_type: TypeExpr = self.infer_expr(
            expression=statement.value,
            scope=scope,
        )
        target: expr
        for target in statement.targets:
            self.bind_target(target=target, type_expr=value_type, scope=scope)

    def _handle_ann_assign_statement(
        self,
        *,
        statement: AnnAssign,
        scope: ScopeState,
    ) -> None:
        """Handle AnnAssign statement.

        Args:
            scope: The scope examined while handle AnnAssign statement.
            statement: The statement examined while handle AnnAssign statement.

        """
        if statement.value is not None:
            value_type: TypeExpr = self.infer_expr(
                expression=statement.value,
                scope=scope,
            )
        else:
            value_type = type_expr_from_annotation(
                annotation=statement.annotation,
            )
        self.bind_target(
            target=statement.target,
            type_expr=value_type,
            scope=scope,
        )

    def _handle_aug_assign_statement(
        self,
        *,
        statement: AugAssign,
        scope: ScopeState,
    ) -> None:
        """Handle AugAssign statement.

        Args:
            scope: The scope examined while handle AugAssign statement.
            statement: The statement examined while handle AugAssign statement.

        """
        current_type: TypeExpr = self.infer_expr(
            expression=statement.target,
            scope=scope,
        )
        value_type: TypeExpr = self.infer_expr(
            expression=statement.value,
            scope=scope,
        )
        self.bind_target(
            target=statement.target,
            type_expr=infer_binop(
                left=current_type,
                right=value_type,
                op=statement.op,
            ),
            scope=scope,
        )

    def _handle_with_statement(
        self,
        *,
        statement: With | AsyncWith,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle With/AsyncWith statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle With/AsyncWith statement.
            statement: The statement examined while handle With/AsyncWith
                statement.

        Returns:
            ScopeState produced by this operation.

        """
        item: object
        for item in statement.items:
            context_expr: expr = item.context_expr
            entry_type: TypeExpr = infer_context_entry_type(
                context_type=self.infer_expr(
                    expression=context_expr,
                    scope=scope,
                ),
                context_expr=context_expr,
            )
            if item.optional_vars is not None:
                self.bind_target(
                    target=item.optional_vars,
                    type_expr=entry_type,
                    scope=scope,
                )
        return self._execute_statements(
            body=statement.body,
            scope=scope,
            returns=returns,
        )

    def _handle_try_statement(
        self,
        *,
        statement: Try,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle Try statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle Try statement.
            statement: The statement examined while handle Try statement.

        Returns:
            ScopeState produced by this operation.

        """
        branch_scopes: list[ScopeState] = []
        branch_scopes.append(
            self._execute_statements(
                body=statement.body,
                scope=scope.clone(name=(f"{scope.name}:try")),
                returns=returns,
            ),
        )
        handler: object
        for handler in statement.handlers:
            handler_scope: ScopeState = scope.clone(
                name=(f"{scope.name}:except"),
            )
            if handler.name is not None:
                handler_scope.set_exact(
                    name=handler.name,
                    type_expr=exception_type_from_handler(handler=handler),
                )
            branch_scopes.append(
                self._execute_statements(
                    body=handler.body,
                    scope=handler_scope,
                    returns=returns,
                ),
            )
        if statement.orelse:
            branch_scopes.append(
                self._execute_statements(
                    body=statement.orelse,
                    scope=scope.clone(name=(f"{scope.name}:else")),
                    returns=returns,
                ),
            )
        merged_scope: ScopeState = merge_scopes(
            name=scope.name,
            scopes=branch_scopes or [scope],
        )
        if statement.finalbody:
            merged_scope = self._execute_statements(
                body=statement.finalbody,
                scope=merged_scope,
                returns=returns,
            )
        return merged_scope

    def _handle_if_statement(
        self,
        *,
        statement: If,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle If statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle If statement.
            statement: The statement examined while handle If statement.

        Returns:
            ScopeState produced by this operation.

        """
        true_scope, false_scope = self._branch_scopes_for_test(
            test=statement.test,
            scope=scope,
        )
        branch_end_scopes: list[ScopeState] = []
        if true_scope is not None:
            branch_end_scopes.append(
                self._execute_statements(
                    body=statement.body,
                    scope=true_scope,
                    returns=returns,
                ),
            )
        if false_scope is not None:
            branch_end_scopes.append(
                self._execute_statements(
                    body=statement.orelse,
                    scope=false_scope,
                    returns=returns,
                ),
            )
        return merge_scopes(
            name=scope.name,
            scopes=branch_end_scopes or [scope],
        )

    def _handle_match_statement(
        self,
        *,
        statement: Match,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle Match statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle Match statement.
            statement: The statement examined while handle Match statement.

        Returns:
            ScopeState produced by this operation.

        """
        branch_scopes: list[ScopeState] = []
        subject_type: TypeExpr = self.infer_expr(
            expression=statement.subject,
            scope=scope,
        )
        case_node: match_case
        for case_node in statement.cases:
            case_scope: ScopeState = scope.clone(name=f"{scope.name}:case")
            bind_pattern_scope(
                pattern=case_node.pattern,
                subject_type=subject_type,
                scope=case_scope,
            )
            if case_node.guard is not None:
                guarded_true, _guarded_false = self._branch_scopes_for_test(
                    test=case_node.guard,
                    scope=case_scope,
                )
                if guarded_true is None:
                    continue
                case_scope = guarded_true
            branch_scopes.append(
                self._execute_statements(
                    body=case_node.body,
                    scope=case_scope,
                    returns=returns,
                ),
            )
        return merge_scopes(name=scope.name, scopes=branch_scopes or [scope])

    def _handle_for_statement(
        self,
        *,
        statement: For,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle For statement.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle For statement.
            statement: The statement examined while handle For statement.

        Returns:
            ScopeState produced by this operation.

        """
        iter_type: TypeExpr = self.infer_expr(
            expression=statement.iter,
            scope=scope,
        )
        self.bind_target(
            target=statement.target,
            type_expr=element_type(type_expr=iter_type),
            scope=scope,
        )
        loop_scope: ScopeState = self._execute_statements(
            body=statement.body,
            scope=scope,
            returns=returns,
        )
        if statement.orelse:
            loop_scope = self._execute_statements(
                body=statement.orelse,
                scope=loop_scope,
                returns=returns,
            )
        return loop_scope

    def _handle_fallback_statement(
        self,
        *,
        statement: stmt,
        scope: ScopeState,
    ) -> None:
        """Handle fallback statement (walk for Call nodes).

        Args:
            scope: The scope examined while handle fallback statement (walk for
                Call nodes).
            statement: The statement examined while handle fallback statement
                (walk for Call nodes).

        """
        child: AST
        for child in walk(node=statement):
            if isinstance(child, Call):
                self.infer_expr(expression=child, scope=scope)

    def _handle_expr_statement(
        self,
        *,
        statement: Expr,
        scope: ScopeState,
    ) -> None:
        """Handle Expr statement.

        Args:
            scope: The scope examined while handle Expr statement.
            statement: The statement examined while handle Expr statement.

        """
        self.infer_expr(expression=statement.value, scope=scope)

    def _dispatch_statement(
        self,
        *,
        statement: stmt,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState | None:
        """Dispatch statement to handler. Returns new scope or None.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while dispatch statement to handler.
                Returns new scope or None.
            statement: The statement examined while dispatch statement to
                handler. Returns new scope or None.

        Returns:
            ScopeState | None produced by this operation.

        """
        result: ScopeState | None = None
        if isinstance(statement, Return):
            result = self._handle_return_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        elif isinstance(statement, (Assign, AnnAssign, AugAssign)):
            self._handle_assignment_statement(statement=statement, scope=scope)
        elif isinstance(statement, (With, AsyncWith)):
            result = self._handle_with_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        elif isinstance(statement, Try):
            result = self._handle_try_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        elif isinstance(statement, Expr):
            self._handle_expr_statement(statement=statement, scope=scope)
        elif isinstance(statement, (If, Match, For)):
            result = self._handle_control_flow_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        elif not self._should_skip_statement(statement=statement):
            self._handle_fallback_statement(statement=statement, scope=scope)
        return result

    def _handle_assignment_statement(
        self,
        *,
        statement: Assign | AnnAssign | AugAssign,
        scope: ScopeState,
    ) -> None:
        """Handle assignment-type statements.

        Args:
            scope: The scope examined while handle assignment-type statements.
            statement: The statement examined while handle assignment-type
                statements.

        """
        if isinstance(statement, Assign):
            self._handle_assign_statement(statement=statement, scope=scope)
        elif isinstance(statement, AnnAssign):
            self._handle_ann_assign_statement(statement=statement, scope=scope)
        else:
            self._handle_aug_assign_statement(statement=statement, scope=scope)

    def _handle_control_flow_statement(
        self,
        *,
        statement: If | Match | For,
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Handle control flow statements.

        Args:
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while handle control flow statements.
            statement: The statement examined while handle control flow
                statements.

        Returns:
            ScopeState produced by this operation.

        """
        if isinstance(statement, If):
            return self._handle_if_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        if isinstance(statement, Match):
            return self._handle_match_statement(
                statement=statement,
                scope=scope,
                returns=returns,
            )
        return self._handle_for_statement(
            statement=statement,
            scope=scope,
            returns=returns,
        )

    def _execute_statements(
        self,
        *,
        body: Sequence[stmt],
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> ScopeState:
        """Execute statements.

        Args:
            body: Statements to analyze in execution order.
            returns: Collected return-type evidence updated during analysis.
            scope: Lexical scope containing the expression.

        Returns:
            Result of the operation, according to the declared return type.

        """
        current_scope: ScopeState = scope
        statement: stmt
        for statement in body:
            new_scope: ScopeState | None = self._dispatch_statement(
                statement=statement,
                scope=current_scope,
                returns=returns,
            )
            if new_scope is not None:
                current_scope = new_scope
        return current_scope

    def _branch_scopes_for_test(
        self,
        *,
        test: expr,
        scope: ScopeState,
    ) -> tuple[ScopeState | None, ScopeState | None]:
        """Branch scopes for test.

        Args:
            scope: Lexical scope containing the expression.
            test: Conditional expression used to split control-flow scopes.

        Returns:
            Scope state resulting from the analysis.

        """
        condition: BranchCondition | None = condition_from_test(
            test=test,
            scope=scope,
        )
        if condition is None:
            self.infer_expr(expression=test, scope=scope)
            return (
                scope.clone(name=(f"{scope.name}:true")),
                scope.clone(name=(f"{scope.name}:false")),
            )
        true_scope: ScopeState | None = None
        false_scope: ScopeState | None = None
        if condition.true_reachable:
            true_scope = scope.clone(name=f"{scope.name}:true")
            if condition.true_type is not None:
                true_scope.set_exact(
                    name=condition.name,
                    type_expr=condition.true_type,
                )
        if condition.false_reachable:
            false_scope = scope.clone(name=f"{scope.name}:false")
            if condition.false_type is not None:
                false_scope.set_exact(
                    name=condition.name,
                    type_expr=condition.false_type,
                )
        return (true_scope, false_scope)

    def _setup_function_scope(self, *, info: FunctionInfo) -> ScopeState:
        """Set up scope for function analysis.

        Args:
            info: The info examined while set up scope for function analysis.

        Returns:
            ScopeState produced by this operation.

        """
        parent_scope: ScopeState = self.module_scope
        scope: ScopeState = ScopeState(
            name=info.qualified_name,
            parent=parent_scope,
            local_classes=local_class_names(function=info.node),
            owner=info,
        )
        if info.class_name is not None:
            self_type: TypeExpr = TypeExpr.name_expr(name=info.class_name)
            cls_type: TypeExpr = TypeExpr.generic("type", self_type)
            scope.set(name="self", type_expr=self_type)
            scope.set(name="cls", type_expr=cls_type)
            implicit_name: str | None = info.implicit_parameter_name()
            if implicit_name is not None:
                scope.set(
                    name=implicit_name,
                    type_expr=cls_type
                    if info.method_kind == "class"
                    else self_type,
                )
        return scope

    def _infer_parameter_type(
        self,
        *,
        parameter: arg,
        info: FunctionInfo,
        defaults: dict[str, expr],
    ) -> TypeExpr:
        """Infer type for a single parameter.

        Args:
            defaults: Defaults supplied as dict[str, expr] for this operation.
            info: The info examined while infer type for a single parameter.
            parameter: Parameter supplied as arg for this operation.

        Returns:
            TypeExpr produced by this operation.

        """
        if parameter.annotation is not None:
            return type_expr_from_annotation(annotation=parameter.annotation)
        if parameter.arg in info.param_types:
            return info.param_types[parameter.arg]
        if parameter.arg in defaults:
            inferred_default: TypeExpr = self.infer_expr(
                expression=defaults[parameter.arg],
                scope=self.module_scope,
            )
            if not inferred_default.is_unknown():
                return infer_optional_from_default(type_expr=inferred_default)
        inferred_param: TypeExpr = infer_param_from_usage(
            function=info.node,
            name=parameter.arg,
        )
        attr_assignment_type: TypeExpr | None = None
        if (
            info.class_name is not None
            and parameter.arg != info.implicit_parameter_name()
        ):
            attr_assignment_type = infer_param_type_from_self_assignment(
                function=info.node,
                name=parameter.arg,
                class_info=self.index.classes.get(info.class_name),
            )
        if (
            attr_assignment_type is not None
            and attr_assignment_type.key()
            not in {
                _NONE_TYPE.key(),
                _OBJECT_TYPE.key(),
            }
        ):
            inferred_param = merge_types(
                left=inferred_param,
                right=attr_assignment_type,
            )
        if (
            info.class_name is not None
            and parameter.arg != info.implicit_parameter_name()
            and parameter_is_used_as_peer_instance(
                function=info.node,
                name=parameter.arg,
                class_name=info.class_name,
            )
        ):
            inferred_param = TypeExpr.name_expr(name=info.class_name)
        return inferred_param

    def _refine_parameter_type_from_self(
        self,
        *,
        parameter: arg,
        info: FunctionInfo,
    ) -> TypeExpr:
        """Refine parameter type from self assignment if applicable.

        Args:
            info: The info examined while refine parameter type from self
                assignment if applicable.
            parameter: Parameter supplied as arg for this operation.

        Returns:
            TypeExpr produced by this operation.

        """
        current_param_type: TypeExpr = info.param_types.get(
            parameter.arg,
            _OBJECT_TYPE,
        )
        if (
            info.class_name is not None
            and parameter.arg != info.implicit_parameter_name()
        ):
            refined_param_type: TypeExpr | None = (
                infer_param_type_from_self_assignment(
                    function=info.node,
                    name=parameter.arg,
                    class_info=self.index.classes.get(info.class_name),
                )
            )
            if (
                refined_param_type is not None
                and refined_param_type.key()
                not in {
                    _NONE_TYPE.key(),
                    _OBJECT_TYPE.key(),
                }
            ):
                current_param_type = refined_param_type
                info.param_types[parameter.arg] = refined_param_type
        return current_param_type

    def _analyze_function(self, info: FunctionInfo) -> None:
        """Analyze function.

        Args:
            info: Indexed function metadata used by this operation.

        """
        self._apply_special_signature(info=info)
        scope: ScopeState = self._setup_function_scope(info=info)
        args: tuple[arg, ...] = all_args(node=info.node)
        defaults: dict[str, expr] = defaults_by_arg(node=info.node)
        parameter: arg
        for parameter in args:
            if parameter.arg == info.implicit_parameter_name():
                continue
            if parameter.arg not in info.param_types:
                info.param_types[parameter.arg] = self._infer_parameter_type(
                    parameter=parameter,
                    info=info,
                    defaults=defaults,
                )
            self._apply_none_default_union(
                parameter=parameter,
                defaults=defaults,
                info=info,
            )
            self._apply_none_comparison_union(parameter=parameter, info=info)
            self._widen_redundant_isinstance_param(
                parameter=parameter,
                info=info,
            )
            self._apply_vararg_kwarg_types(parameter=parameter, info=info)
            current_param_type: TypeExpr = (
                self._refine_parameter_type_from_self(
                    parameter=parameter,
                    info=info,
                )
            )
            scope.set(name=parameter.arg, type_expr=current_param_type)
        returns: list[TypeExpr] = []
        self._analyze_statements(
            body=info.node.body,
            scope=scope,
            returns=returns,
        )
        if info.class_name is not None:
            self._refine_class_attributes_from_methods(info=info)
        self._infer_return_type(info=info, returns=returns)

    def _refine_class_attributes_from_methods(
        self,
        *,
        info: FunctionInfo,
    ) -> None:
        """Refine self attribute types from observable method operations.

        Args:
            info: The info examined while refine self attribute types from
                observable method operations.

        """
        if info.class_name is None:
            return
        class_info: ClassInfo | None = self.index.classes.get(info.class_name)
        if class_info is None:
            return
        node: AST
        for node in walk(node=info.node):
            if not isinstance(node, BinOp):
                continue
            for side in (node.left, node.right):
                if (
                    isinstance(side, Attribute)
                    and isinstance(side.value, Name)
                    and (side.value.id == "self")
                    and (side.attr in class_info.attributes)
                ):
                    class_info.attributes[side.attr] = merge_types(
                        left=class_info.attributes[side.attr],
                        right=_INT_TYPE,
                    )

    def _analyze_statements(
        self,
        body: Sequence[stmt],
        scope: ScopeState,
        returns: list[TypeExpr],
    ) -> None:
        """Analyze statements through the conditional execution engine.

        Args:
            body: Body supplied as Sequence[stmt] for this operation.
            returns: Returns supplied as list[TypeExpr] for this operation.
            scope: The scope examined while analyze statements through the
                conditional execution engine.

        """
        self._execute_statements(body=body, scope=scope, returns=returns)

    def _bind_attribute_target(
        self,
        target: Attribute,
        type_expr: TypeExpr,
        scope: ScopeState,
    ) -> None:
        """Bind an attribute target to a type expression.

        Args:
            scope: The scope examined while bind an attribute target to a type
                expression.
            target: The target examined while bind an attribute target to a
                type expression.
            type_expr: The type expr examined while bind an attribute target to
                a type expression.

        """
        if is_self_attr(node=target):
            self_type: TypeExpr = scope.get(name="self")
            class_info: ClassInfo | None = self.index.classes.get(
                self_type.name,
            )
            if class_info is not None:
                old_attr: TypeExpr | None = class_info.attributes.get(
                    target.attr,
                )
                class_info.attributes[target.attr] = (
                    merge_class_attribute_type(
                        old_attr=old_attr,
                        new_attr=type_expr,
                    )
                )

    def _bind_sequence_target(
        self,
        target: Tuple | List,
        type_expr: TypeExpr,
        scope: ScopeState,
    ) -> None:
        """Bind a sequence target to a type expression.

        Args:
            scope: The scope examined while bind a sequence target to a type
                expression.
            target: The target examined while bind a sequence target to a type
                expression.
            type_expr: The type expr examined while bind a sequence target to a
                type expression.

        """
        if target.elts and type_expr.kind == "tuple":
            for item, item_type in zip(
                target.elts,
                type_expr.args,
                strict=False,
            ):
                self.bind_target(target=item, type_expr=item_type, scope=scope)
            return
        elem: TypeExpr = element_type(type_expr=type_expr)
        for item in target.elts:
            if isinstance(item, Starred):
                self.bind_target(
                    target=item.value,
                    type_expr=TypeExpr.generic("list", elem),
                    scope=scope,
                )
            else:
                self.bind_target(target=item, type_expr=elem, scope=scope)

    def _infer_collection_literal(
        self,
        expression: List | Set | Tuple | Dict,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for collection literals.

        Args:
            expression: The expression examined while infer types for
                collection literals.
            scope: The scope examined while infer types for collection
                literals.

        Returns:
            TypeExpr produced by this operation.

        """
        if isinstance(expression, List):
            return TypeExpr.generic(
                "list",
                merge_many(
                    types=[
                        self.infer_expr(
                            expression=item.value
                            if isinstance(item, Starred)
                            else item,
                            scope=scope,
                        )
                        for item in expression.elts
                    ],
                ),
            )
        if isinstance(expression, Set):
            return TypeExpr.generic(
                "set",
                merge_many(
                    types=[
                        self.infer_expr(
                            expression=item.value
                            if isinstance(item, Starred)
                            else item,
                            scope=scope,
                        )
                        for item in expression.elts
                    ],
                ),
            )
        if isinstance(expression, Tuple):
            return TypeExpr.generic(
                "tuple",
                *[
                    self.infer_expr(expression=item, scope=scope)
                    for item in expression.elts
                ],
            )
        key_types: list[TypeExpr] = []
        value_types: list[TypeExpr] = []
        for key_node, value_node in zip(
            expression.keys,
            expression.values,
            strict=True,
        ):
            value_type: TypeExpr = self.infer_expr(
                expression=value_node,
                scope=scope,
            )
            if key_node is None:
                if (
                    value_type.kind == "generic"
                    and value_type.name
                    in {"dict", "Mapping", "OrderedDict", "defaultdict"}
                    and (len(value_type.args) >= Constants.min_type_args)
                ):
                    key_types.append(value_type.args[0])
                    value_types.append(value_type.args[1])
                continue
            key_types.append(self.infer_expr(expression=key_node, scope=scope))
            value_types.append(value_type)
        return TypeExpr.generic(
            "dict",
            merge_many(types=key_types),
            merge_many(types=value_types),
        )

    def _infer_comprehension(
        self,
        expression: DictComp | ListComp | SetComp | GeneratorExp,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for comprehensions.

        Args:
            expression: The expression examined while infer types for
                comprehensions.
            scope: The scope examined while infer types for comprehensions.

        Returns:
            TypeExpr produced by this operation.

        """
        if isinstance(expression, DictComp):
            local: ScopeState = ScopeState(name="dictcomp", parent=scope)
            generator: comprehension
            for generator in expression.generators:
                iter_type: TypeExpr = self.infer_expr(
                    expression=generator.iter,
                    scope=scope,
                )
                self.bind_target(
                    target=generator.target,
                    type_expr=element_type(type_expr=iter_type),
                    scope=local,
                )
            return TypeExpr.generic(
                "dict",
                self.infer_expr(expression=expression.key, scope=local),
                self.infer_expr(expression=expression.value, scope=local),
            )
        if isinstance(expression, GeneratorExp):
            return TypeExpr.generic(
                "Generator",
                infer_comprehension_element(
                    expression=expression,
                    engine=self,
                    scope=scope,
                ),
            )
        return TypeExpr.generic(
            "list",
            infer_comprehension_element(
                expression=expression,
                engine=self,
                scope=scope,
            ),
        )

    def _infer_comparison_operation(
        self,
        expression: Compare | BoolOp,
        scope: ScopeState,
    ) -> TypeExpr | None:
        """Infer types for comparison and boolean operations.

        Args:
            expression: The expression examined while infer types for
                comparison and boolean operations.
            scope: The scope examined while infer types for comparison and
                boolean operations.

        Returns:
            TypeExpr | None produced by this operation.

        """
        if isinstance(expression, Compare):
            return _BOOL_TYPE
        if all(
            self.infer_expr(expression=item, scope=scope).key()
            == _BOOL_TYPE.key()
            for item in expression.values
        ):
            return _BOOL_TYPE
        return merge_many(
            types=[
                self.infer_expr(expression=item, scope=scope)
                for item in expression.values
            ],
        )

    def _infer_unary_operation(
        self,
        expression: UnaryOp,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for unary operations.

        Args:
            expression: The expression examined while infer types for unary
                operations.
            scope: The scope examined while infer types for unary operations.

        Returns:
            TypeExpr produced by this operation.

        """
        return (
            _BOOL_TYPE
            if expression.op.__class__.__name__ == "Not"
            else self.infer_expr(expression=expression.operand, scope=scope)
        )

    def _infer_if_expression(
        self,
        expression: IfExp,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for if expressions.

        Args:
            expression: The expression examined while infer types for if
                expressions.
            scope: The scope examined while infer types for if expressions.

        Returns:
            TypeExpr produced by this operation.

        """
        true_scope, false_scope = self._branch_scopes_for_test(
            test=expression.test,
            scope=scope,
        )
        branch_types: list[TypeExpr] = []
        if true_scope is not None:
            branch_types.append(
                self.infer_expr(expression=expression.body, scope=true_scope),
            )
        if false_scope is not None:
            branch_types.append(
                self.infer_expr(
                    expression=expression.orelse,
                    scope=false_scope,
                ),
            )
        return merge_many(types=branch_types)

    def _infer_binary_operation(
        self,
        expression: BinOp,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for binary operations.

        Args:
            expression: The expression examined while infer types for binary
                operations.
            scope: The scope examined while infer types for binary operations.

        Returns:
            TypeExpr produced by this operation.

        """
        return infer_binop(
            left=self.infer_expr(expression=expression.left, scope=scope),
            right=self.infer_expr(expression=expression.right, scope=scope),
            op=expression.op,
        )

    def _infer_subscript_operation(
        self,
        expression: Subscript,
        scope: ScopeState,
    ) -> TypeExpr:
        """Infer types for subscript operations.

        Args:
            expression: The expression examined while infer types for subscript
                operations.
            scope: The scope examined while infer types for subscript
                operations.

        Returns:
            TypeExpr produced by this operation.

        """
        base: TypeExpr = self.infer_expr(
            expression=expression.value,
            scope=scope,
        )
        return infer_subscript(container=base, slice_node=expression.slice)

    def _infer_operation(
        self,
        expression: expr,
        scope: ScopeState,
    ) -> TypeExpr | None:
        """Infer types for operations.

        Args:
            expression: The expression examined while infer types for
                operations.
            scope: The scope examined while infer types for operations.

        Returns:
            TypeExpr | None produced by this operation.

        """
        result: TypeExpr | None = None
        if isinstance(expression, (Compare, BoolOp)):
            result = self._infer_comparison_operation(
                expression=expression,
                scope=scope,
            )
        elif isinstance(expression, UnaryOp):
            result = self._infer_unary_operation(
                expression=expression,
                scope=scope,
            )
        elif isinstance(expression, IfExp):
            result = self._infer_if_expression(
                expression=expression,
                scope=scope,
            )
        elif isinstance(expression, BinOp):
            result = self._infer_binary_operation(
                expression=expression,
                scope=scope,
            )
        elif isinstance(expression, Subscript):
            result = self._infer_subscript_operation(
                expression=expression,
                scope=scope,
            )
        elif isinstance(expression, Attribute):
            result = infer_attribute(
                expression=expression,
                scope=scope,
                classes=self.index.classes,
            )
        elif isinstance(expression, Lambda):
            result = TypeExpr.callable_expr(
                parameters=[_OBJECT_TYPE],
                return_type=self.infer_expr(
                    expression=expression.body,
                    scope=scope,
                ),
            )
        return result

    def _infer_call(self, expression: Call, scope: ScopeState) -> TypeExpr:
        """Infer call.

        Args:
            expression: Expression whose type is being inferred.
            scope: Lexical scope containing the expression.

        Returns:
            Inferred type representation for the expression.

        """
        name: str = expr_name(node=expression.func)
        self._connect_call_arguments(call=expression, name=name, scope=scope)
        result: TypeExpr | None = None
        if name in scope.local_classes:
            result = _OBJECT_TYPE
        else:
            method_result: TypeExpr | None = self._infer_method_call(
                expression=expression,
                scope=scope,
            )
            if method_result is not None:
                result = method_result
            else:
                callable_value: TypeExpr = scope.get(name=name)
                if (
                    callable_value.kind == "callable"
                    and callable_value.return_type is not None
                ):
                    result = callable_value.return_type
                else:
                    known_result: TypeExpr | None = infer_known_call(
                        call=expression,
                        name=name,
                        scope=scope,
                        infer=self.infer_expr,
                        classes=self.index.classes,
                    )
                    if known_result is not None:
                        result = known_result
                    else:
                        info: FunctionInfo | None = self.resolve_callable(
                            name=name,
                        )
                        if info is not None:
                            specialized: TypeExpr = (
                                self._specialized_call_return(
                                    info=info,
                                    call=expression,
                                    caller_scope=scope,
                                )
                            )
                            effective: TypeExpr = (
                                specialized
                                if not specialized.is_unknown()
                                else info.return_type
                            )
                            declared: TypeExpr = sanitize_annotation_type(
                                type_expr=info.return_type,
                            )
                            if (
                                declared.kind == "union"
                                and (not effective.is_unknown())
                                and (
                                    effective.key()
                                    in {m.key() for m in declared.args}
                                )
                            ):
                                effective = declared
                            result = effective
        if result is not None:
            return result
        return (
            TypeExpr.name_expr(name=name)
            if name in self.index.classes
            else _UNKNOWN_TYPE
        )

    def _infer_method_call(
        self,
        *,
        expression: Call,
        scope: ScopeState,
    ) -> TypeExpr | None:
        """Infer method call.

        Args:
            expression: Expression whose type is being inferred.
            scope: Lexical scope containing the expression.

        Returns:
            Inferred type representation for the expression.

        """
        if not isinstance(expression.func, Attribute):
            return None
        receiver_type: TypeExpr = self.infer_expr(
            expression=expression.func.value,
            scope=scope,
        )
        method_name: str = expression.func.attr
        if receiver_type.name in self.index.classes:
            class_info: ClassInfo = self.index.classes[receiver_type.name]
            method_info: FunctionInfo | None = class_info.methods.get(
                method_name,
            )
            if method_info is not None:
                self._connect_method_arguments(
                    call=expression,
                    method=method_info,
                    scope=scope,
                )
                return method_info.return_type
        return infer_builtin_method_call(
            receiver_type=receiver_type,
            method_name=method_name,
            call=expression,
            scope=scope,
            infer=self.infer_expr,
        )

    def _connect_method_arguments(
        self,
        *,
        call: Call,
        method: FunctionInfo,
        scope: ScopeState,
    ) -> None:
        """Connect method arguments.

        Args:
            call: Call expression whose arguments are being analyzed.
            method: Resolved method metadata for the call.
            scope: Lexical scope containing the expression.

        """
        params: list[arg] = method.explicit_parameters()
        for index, arg_node in enumerate(iterable=call.args):
            if index >= len(params):
                continue
            inferred: TypeExpr = self.infer_expr(
                expression=arg_node,
                scope=scope,
            )
            if not inferred.is_unknown():
                name: str = params[index].arg
                method.param_types[name] = merge_types(
                    left=method.param_types.get(name, inferred),
                    right=inferred,
                )
        for kw in call.keywords:
            if kw.arg is None:
                continue
            inferred = self.infer_expr(expression=kw.value, scope=scope)
            if not inferred.is_unknown():
                method.param_types[kw.arg] = merge_types(
                    left=method.param_types.get(kw.arg, inferred),
                    right=inferred,
                )


class StrictAstTransformer(LowercaseTransformer):
    """Apply annotations and kwargs as AST edits."""

    def __init__(self, engine: InferenceEngine) -> None:
        """Initialize the StrictAstTransformer with an InferenceEngine.

        Args:
            engine: Engine supplied as InferenceEngine for this operation.

        """
        self.engine: InferenceEngine = engine
        self.function_stack: list[FunctionInfo] = []
        self.scope_stack: list[ScopeState] = [engine.module_scope]
        self.class_stack: list[ClassInfo] = []
        self.needed_imports: set[str] = set()
        self.annotated_local_names_stack: list[set[str]] = []

    def visit_module(self, node: Module) -> Module:
        """Visit a Module node and prepend needed imports.

        Args:
            node: The node examined while visit a Module node and prepend
                needed imports.

        Returns:
            Module produced by this operation.

        """
        self.generic_visit(node=node)
        node.body = self._prepend_imports(body=node.body)
        return node

    def visit_classdef(self, node: ClassDef) -> ClassDef:
        """Visit a ClassDef node and apply protocol/namedtuple transforms.

        Args:
            node: The node examined while visit a ClassDef node and apply
                protocol/namedtuple transforms.

        Returns:
            ClassDef produced by this operation.

        """
        class_info: ClassInfo | None = self.engine.index.classes.get(node.name)
        if class_info is not None:
            self.class_stack.append(class_info)
            if class_info.is_protocol_shape and (
                not any(
                    expr_name(node=base) == "Protocol" for base in node.bases
                )
            ):
                node.bases.append(Name(id="Protocol", ctx=Load()))
                self.needed_imports.add("Protocol")
                self._protocolize_body(node=node)
            if class_info.is_namedtuple_shape:
                self._convert_result_class_to_namedtuple(node=node)
        self.generic_visit(node=node)
        if class_info is not None:
            self._ensure_class_attribute_annotations(
                node=node,
                class_info=class_info,
            )
            self.class_stack.pop()
        return node

    def visit_functiondef(self, node: FunctionDef) -> FunctionDef:
        """Visit a FunctionDef node and apply type annotations.

        Args:
            node: The node examined while visit a FunctionDef node and apply
                type annotations.

        Returns:
            FunctionDef produced by this operation.

        """
        return cast(typ="FunctionDef", val=self._visit_function(node=node))

    def visit_asyncfunctiondef(
        self,
        node: AsyncFunctionDef,
    ) -> AsyncFunctionDef:
        """Visit an AsyncFunctionDef node and apply type annotations.

        Args:
            node: The node examined while visit an AsyncFunctionDef node and
                apply type annotations.

        Returns:
            AsyncFunctionDef produced by this operation.

        """
        return cast(
            typ="AsyncFunctionDef",
            val=self._visit_function(node=node),
        )

    def visit_assign(self, node: Assign) -> stmt:
        """Visit an Assign node and add type annotation if appropriate.

        Args:
            node: The node examined while visit an Assign node and add type
                annotation if appropriate.

        Returns:
            stmt produced by this operation.

        """
        self.generic_visit(node=node)
        if len(node.targets) != 1:
            return node
        target: expr = node.targets[0]
        inferred: TypeExpr = self.engine.infer_expr(
            expression=node.value,
            scope=self.scope_stack[-1],
        )
        if inferred.is_unknown():
            return node
        result: stmt | None
        if isinstance(target, Name) and should_annotate_name(name=target.id):
            result = self._handle_name_target(
                target=target,
                inferred=inferred,
                node=node,
            )
        elif isinstance(target, Attribute) and is_self_attr(node=target):
            result = self._handle_self_attr_target(target=target, node=node)
        else:
            result = None
        return result if result is not None else node

    def visit_call(self, node: Call) -> Call:
        """Visit a Call node and keywordize arguments if appropriate.

        Args:
            node: The node examined while visit a Call node and keywordize
                arguments if appropriate.

        Returns:
            Call produced by this operation.

        """
        self.generic_visit(node=node)
        return self._keywordize_call(node=node)

    def visit_parenthesized(self, node: Parenthesized) -> Parenthesized:
        """Visit a Parenthesized node.

        Preserve it through transformation.


        Args:
            node: The node examined while visit a Parenthesized node.

        Returns:
            Parenthesized produced by this operation.

        """
        self.generic_visit(node=node.value)
        return node

    @staticmethod
    def _collect_existing_attribute_names(node: ClassDef) -> set[str]:
        """Collect existing attribute names from class body.

        Args:
            node: The node examined while collect existing attribute names from
                class body.

        Returns:
            set[str] produced by this operation.

        """
        existing: set[str] = set()
        for item in node.body:
            if isinstance(item, AnnAssign) and isinstance(item.target, Name):
                existing.add(item.target.id)
            if isinstance(item, Assign):
                for target in item.targets:
                    if isinstance(target, Name):
                        existing.add(target.id)
        return existing

    @staticmethod
    def _get_annotation_insert_position(node: ClassDef) -> int:
        """Determine where to insert new annotations in class body.

        Args:
            node: The node examined while determine where to insert new
                annotations in class body.

        Returns:
            int produced by this operation.

        """
        if (
            node.body
            and isinstance(node.body[0], Expr)
            and isinstance(node.body[0].value, Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            return 1
        return 0

    def _visit_function(
        self,
        node: FunctionDef | AsyncFunctionDef,
    ) -> FunctionDef | AsyncFunctionDef:
        """Visit function.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Transformed AST node, or None when no replacement is produced.

        """
        info: FunctionInfo = self._info_for_function(node=node)
        self.function_stack.append(info)
        self.scope_stack.append(
            ScopeState(
                name=info.qualified_name,
                parent=self.scope_stack[-1],
                local_classes=local_class_names(function=node),
                owner=info,
            ),
        )
        if info.class_name is not None:
            self_type: TypeExpr = TypeExpr.name_expr(name=info.class_name)
            cls_type: TypeExpr = TypeExpr.generic("type", self_type)
            self.scope_stack[-1].set(name="self", type_expr=self_type)
            self.scope_stack[-1].set(name="cls", type_expr=cls_type)
            implicit_name: str | None = info.implicit_parameter_name()
            if implicit_name is not None:
                self.scope_stack[-1].set(
                    name=implicit_name,
                    type_expr=cls_type
                    if info.method_kind == "class"
                    else self_type,
                )
        self._annotate_args(function=node, info=info)
        for parameter in all_args(node=node):
            if parameter.arg in info.param_types:
                self.scope_stack[-1].set(
                    name=parameter.arg,
                    type_expr=info.param_types[parameter.arg],
                )
        self._annotate_return(function=node, info=info)
        for child in walk(node=node):
            if isinstance(child, Return) and isinstance(child.value, Name):
                for stmt in walk(node=node):
                    if (
                        isinstance(stmt, ClassDef)
                        and stmt.name == child.value.id
                        and stmt.decorator_list
                    ):
                        node.returns = self._annotation_expr(
                            type_expr=_OBJECT_TYPE,
                        )
                        break
        self._maybe_add_type_params(function=node)
        self._add_override_if_needed(function=node)
        self.annotated_local_names_stack.append(set())
        self.generic_visit(node=node)
        self.annotated_local_names_stack.pop()
        self.function_stack.pop()
        self.scope_stack.pop()
        return node

    def _handle_class_attribute_inference(
        self,
        target: Name,
        inferred: TypeExpr,
    ) -> TypeExpr:
        """Handle type inference for class attributes.

        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            target: The target examined while handle type inference for class
                attributes.

        Returns:
            TypeExpr produced by this operation.

        """
        current_class: ClassInfo = self.class_stack[-1]
        if current_class.is_protocol_shape or (
            is_dataclass_class(node=current_class.node)
            and inferred.key() == _NONE_TYPE.key()
        ):
            return _OBJECT_TYPE
        class_type: TypeExpr | None = current_class.attributes.get(target.id)
        if (
            class_type is not None
            and (not class_type.is_unknown())
            and (class_type.key() != _NONE_TYPE.key())
        ):
            return class_type
        return inferred

    def _handle_annotated_name_inference(
        self,
        target: Name,
        inferred: TypeExpr,
    ) -> TypeExpr | None:
        """Handle type inference for annotated names.

        Returns None if should skip annotation.


        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            target: The target examined while handle type inference for
                annotated names.

        Returns:
            TypeExpr | None produced by this operation.

        """
        annotated_names: set[str] = self.annotated_local_names_stack[-1]
        if self.function_stack and target.id in {
            param.arg for param in all_args(node=self.function_stack[-1].node)
        }:
            self.scope_stack[-1].set(name=target.id, type_expr=inferred)
            return None
        if target.id in annotated_names:
            self.scope_stack[-1].set(name=target.id, type_expr=inferred)
            return None
        local_type: TypeExpr | None = None
        if self.function_stack:
            local_type = self.function_stack[-1].local_types.get(target.id)
        if local_type is not None and (not local_type.is_unknown()):
            inferred = local_type
        annotated_names.add(target.id)
        return inferred

    def _create_annotated_assignment(
        self,
        target: Name,
        inferred: TypeExpr,
        node: Assign,
    ) -> stmt:
        """Create an annotated assignment node.

        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            node: The node examined while create an annotated assignment node.
            target: The target examined while create an annotated assignment
                node.

        Returns:
            stmt produced by this operation.

        """
        inferred = self._widen_specialized_to_declared(
            value=node.value,
            inferred=inferred,
        )
        annotation: expr = self._annotation_expr(type_expr=inferred)
        value_expr: expr = node.value
        if self._should_cast_call_assignment(
            value=node.value,
            inferred=inferred,
        ):
            self.needed_imports.add("cast")
            value_expr = Call(
                func=Name(id="cast", ctx=Load()),
                args=[Constant(value=inferred.to_source()), node.value],
                keywords=[],
            )
        simple: AnnAssign = AnnAssign(
            target=target,
            annotation=annotation,
            value=value_expr,
            simple=1,
        )
        self.scope_stack[-1].set(name=target.id, type_expr=inferred)
        return cast(
            typ="stmt",
            val=copy_basic_location(new_node=simple, old_node=node),
        )

    def _handle_name_target(
        self,
        *,
        target: Name,
        inferred: TypeExpr,
        node: Assign,
    ) -> stmt | None:
        """Handle assignment to a Name target.

        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            node: The node examined while handle assignment to a Name target.
            target: The target examined while handle assignment to a Name
                target.

        Returns:
            stmt | None produced by this operation.

        """
        if self.class_stack and (not self.function_stack):
            inferred = self._handle_class_attribute_inference(
                target=target,
                inferred=inferred,
            )
        if self.annotated_local_names_stack:
            inferred_result: TypeExpr | None = (
                self._handle_annotated_name_inference(
                    target=target,
                    inferred=inferred,
                )
            )
            if inferred_result is None:
                return None
            inferred = inferred_result
        inferred = self._prefer_analyzed_local_type(
            target=target,
            inferred=inferred,
        )
        return self._create_annotated_assignment(
            target=target,
            inferred=inferred,
            node=node,
        )

    def _prefer_analyzed_local_type(
        self,
        *,
        target: Name,
        inferred: TypeExpr,
    ) -> TypeExpr:
        """Use the analysis pass's local type when it is more precise.

        The whole-function inference pass records a precise type for each
        local in ``FunctionInfo.local_types``. When the per-assignment
        re-inference falls back to ``object``/unknown but the analysis pass
        resolved a concrete type (for example ``defaultdict[str, int]`` from
        a constructor call), prefer the concrete analysis result.


        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            target: The target examined while use the analysis pass's local
                type when it is more precise.

        Returns:
            TypeExpr produced by this operation.

        """
        if not self.function_stack:
            return inferred
        if inferred.key() not in {_OBJECT_TYPE.key(), _UNKNOWN_TYPE.key()}:
            return inferred
        analyzed: TypeExpr | None = self.function_stack[-1].local_types.get(
            target.id,
        )
        if (
            analyzed is None
            or analyzed.is_unknown()
            or analyzed.key() == _OBJECT_TYPE.key()
        ):
            return inferred
        return analyzed

    def _handle_self_attr_target(
        self,
        *,
        target: Attribute,
        node: Assign,
    ) -> stmt | None:
        """Handle assignment to a self attribute target.

        Args:
            node: The node examined while handle assignment to a self attribute
                target.
            target: The target examined while handle assignment to a self
                attribute target.

        Returns:
            stmt | None produced by this operation.

        """
        if not (self.function_stack and self.class_stack):
            return None
        function_info: FunctionInfo = self.function_stack[-1]
        if not (
            isinstance(node.value, Name)
            and node.value.id in function_info.param_types
        ):
            return None
        param_type: TypeExpr = function_info.param_types[node.value.id]
        if param_type.key() == _OBJECT_TYPE.key():
            return None
        annotation: expr = self._annotation_expr(type_expr=param_type)
        ann_assign: AnnAssign = AnnAssign(
            target=target,
            annotation=annotation,
            value=node.value,
            simple=1,
        )
        class_info: ClassInfo = self.class_stack[-1]
        class_info.attributes[target.attr] = param_type
        return cast(
            typ="stmt",
            val=copy_basic_location(new_node=ann_assign, old_node=node),
        )

    def _keywordize_call(self, node: Call) -> Call:
        """Keywordize call.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Call expression with arguments converted to supported keywords.

        """
        if not node.args:
            return node
        if (
            isinstance(node.func, Attribute)
            and node.func.attr in unsafe_keywordized_method_names()
        ):
            return node
        name: str = expr_name(node=node.func)
        param_names: list[str] | None = call_parameter_names(
            name=name,
            engine=self.engine,
        )
        if param_names is None:
            param_names = builtin_keyword_parameters(
                name=name,
                arg_count=len(node.args),
            )
        if not param_names:
            return node
        new_args: list[expr] = []
        new_keywords: list[keyword] = list(node.keywords)
        arg_node: expr
        for index, arg_node in enumerate(iterable=node.args):
            if index >= len(param_names):
                new_args.append(arg_node)
                continue
            param_name: str = param_names[index]
            if param_name == "":
                new_args.append(arg_node)
                continue
            if any(existing.arg == param_name for existing in new_keywords):
                new_args.append(arg_node)
                continue
            new_keywords.append(keyword(arg=param_name, value=arg_node))
        node.args = new_args
        node.keywords = new_keywords
        return node

    def _widen_specialized_to_declared(
        self,
        *,
        value: expr,
        inferred: TypeExpr,
    ) -> TypeExpr:
        """Widen specialized call return to declared return when appropriate.

        When specialization narrows a ``T | None`` declared return to just
        ``T``, the emitted annotation would be incompatible with the declared
        return type. Use the declared return type instead so the annotation
        remains assignable.


        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            value: The value examined while widen specialized call return to
                declared return when appropriate.

        Returns:
            TypeExpr produced by this operation.

        """
        if not isinstance(value, Call):
            return inferred
        if inferred.key() in {_OBJECT_TYPE.key(), _UNKNOWN_TYPE.key()}:
            return inferred
        info: FunctionInfo | None = self.engine.resolve_callable(
            name=expr_name(node=value.func),
        )
        if info is None:
            return inferred
        declared: TypeExpr = sanitize_annotation_type(
            type_expr=info.return_type,
        )
        if declared.kind != "union":
            return inferred
        member_keys: set[str] = {m.key() for m in declared.args}
        if inferred.key() in member_keys:
            return declared
        return inferred

    def _should_cast_call_assignment(
        self,
        *,
        value: expr,
        inferred: TypeExpr,
    ) -> bool:
        """Cast when graph-specialized call result beats declared return.

        Args:
            inferred: Inferred supplied as TypeExpr for this operation.
            value: The value examined while cast when graph-specialized call
                result beats declared return.

        Returns:
            Whether the requested condition holds.

        """
        if not isinstance(value, Call):
            return False
        if inferred.is_unknown() or inferred.key() in {
            _OBJECT_TYPE.key(),
            _NONE_TYPE.key(),
        }:
            return False
        info: FunctionInfo | None = self.engine.resolve_callable(
            name=expr_name(node=value.func),
        )
        if info is None:
            return False
        declared: TypeExpr = sanitize_annotation_type(
            type_expr=info.return_type,
        )
        if declared.is_unknown() or declared.key() == inferred.key():
            return False
        if declared.kind == "union" and any(
            item.key() in {_OBJECT_TYPE.key(), _UNKNOWN_TYPE.key()}
            for item in declared.args
        ):
            return True
        return declared.key() == _OBJECT_TYPE.key()

    def _info_for_function(
        self,
        node: FunctionDef | AsyncFunctionDef,
    ) -> FunctionInfo:
        """Info for function.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Result of the operation, according to the declared return type.

        """
        info: FunctionInfo | None = self.engine.function_by_node.get(id(node))
        if info is not None:
            return info
        return FunctionInfo(node=node, qualified_name=node.name)

    def _annotate_args(
        self,
        function: FunctionDef | AsyncFunctionDef,
        info: FunctionInfo,
    ) -> None:
        """Annotate args.

        Args:
            function: Function definition being transformed.
            info: Indexed function metadata used by this operation.

        """
        parameter: arg
        for parameter in all_args(node=function):
            if (
                parameter.annotation is not None
                or parameter.arg == info.implicit_parameter_name()
            ):
                continue
            type_expr: TypeExpr = info.param_types.get(
                parameter.arg,
                _UNKNOWN_TYPE,
            )
            if type_expr.is_unknown():
                type_expr = infer_param_from_usage(
                    function=function,
                    name=parameter.arg,
                )
            if type_expr.is_unknown():
                type_expr = _OBJECT_TYPE
            info.param_types[parameter.arg] = type_expr
            parameter.annotation = self._annotation_expr(type_expr=type_expr)

    def _annotate_return(
        self,
        function: FunctionDef | AsyncFunctionDef,
        info: FunctionInfo,
    ) -> None:
        """Annotate return.

        Args:
            function: Function definition being transformed.
            info: Indexed function metadata used by this operation.

        """
        type_expr: TypeExpr = info.return_type
        if type_expr.is_unknown():
            type_expr = (
                _NONE_TYPE
                if not has_value_return(function=function)
                else _OBJECT_TYPE
            )
        function.returns = self._annotation_expr(type_expr=type_expr)
        has_decorated_class: bool = any(
            isinstance(stmt, ClassDef) and stmt.decorator_list
            for stmt in walk(node=function)
        )
        has_name_return: bool = any(
            isinstance(child, Return) and isinstance(child.value, Name)
            for child in walk(node=function)
        )
        if has_decorated_class and has_name_return:
            function.returns = self._annotation_expr(type_expr=_OBJECT_TYPE)

    def _annotation_expr(self, type_expr: TypeExpr) -> expr:
        """Annotation expr.

        Args:
            type_expr: Type expr supplied to this operation.

        Returns:
            AST expression representing the inferred type annotation.

        """
        safe_type: TypeExpr = sanitize_annotation_type(type_expr=type_expr)
        collect_imports(type_expr=safe_type, imports=self.needed_imports)
        return safe_type.to_ast()

    def _maybe_add_type_params(
        self,
        *,
        function: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Add type parameters if ParamSpec used in annotations.

        Args:
            function: The function examined while add type parameters if
                ParamSpec used in annotations.

        """
        used_params: set[str] = set()
        for param in all_args(node=function):
            if param.annotation is not None:
                used_params.update(
                    self._extract_type_vars(node=param.annotation),
                )
        if function.returns is not None:
            used_params.update(self._extract_type_vars(node=function.returns))
        paramspec_names: set[str] = {
            name for name in used_params if name in Constants.paramspec_names
        }
        if not paramspec_names:
            return
        existing_names: set[str] = set()
        for tp in function.type_params:
            if isinstance(tp, (AstTypeVar, AstParamSpec)):
                existing_names.add(tp.name)
        for name in sorted(paramspec_names):
            if name not in existing_names:
                function.type_params.append(
                    AstParamSpec(name=name, default_value=None),
                )

    def _extract_type_vars(self, *, node: AST) -> set[str]:
        """Extract type variable names from an annotation node.

        Args:
            node: The node examined while extract type variable names from an
                annotation node.

        Returns:
            set[str] produced by this operation.

        """
        names: set[str] = set()
        for child in walk(node=node):
            if isinstance(child, Name):
                names.add(child.id)
            elif isinstance(child, Subscript):
                if (
                    isinstance(child.value, Name)
                    and child.value.id == "Callable"
                ):
                    names.update(self._extract_type_vars(node=child.slice))
                elif isinstance(child.slice, Name):
                    names.add(child.slice.id)
                elif isinstance(child.slice, AstTuple):
                    for elt in child.slice.elts:
                        if isinstance(elt, Name):
                            names.add(elt.id)
        return names

    def _add_override_if_needed(
        self,
        function: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Add override if needed.

        Args:
            function: Function definition being transformed.

        """
        if not self.class_stack:
            return
        class_info: ClassInfo = self.class_stack[-1]
        if is_override(
            function=function,
            class_info=class_info,
            classes=self.engine.index.classes,
        ) and (not has_decorator(function=function, name="override")):
            function.decorator_list.insert(0, Name(id="override", ctx=Load()))
            self.needed_imports.add("override")

    def _create_annotation_items(
        self,
        class_info: ClassInfo,
        existing: set[str],
    ) -> list[stmt]:
        """Create annotation items for missing attributes.

        Args:
            class_info: The class info examined while create annotation items
                for missing attributes.
            existing: Existing supplied as set[str] for this operation.

        Returns:
            list[stmt] produced by this operation.

        """
        new_items: list[stmt] = []
        for name, type_expr in sorted(class_info.attributes.items()):
            if name in existing or (
                name.startswith("__") and name.endswith("__")
            ):
                continue
            annotation: expr = self._annotation_expr(type_expr=type_expr)
            new_items.append(
                AnnAssign(
                    target=Name(id=name, ctx=Store()),
                    annotation=annotation,
                    value=None,
                    simple=1,
                ),
            )
        return new_items

    def _ensure_class_attribute_annotations(
        self,
        *,
        node: ClassDef,
        class_info: ClassInfo,
    ) -> None:
        """Add class-level annotations for observed instance attributes.

        Args:
            class_info: The class info examined while add class-level
                annotations for observed instance attributes.
            node: The node examined while add class-level annotations for
                observed instance attributes.

        """
        if any(expr_name(node=base) == "NamedTuple" for base in node.bases):
            return
        existing: set[str] = self._collect_existing_attribute_names(node=node)
        insert_at: int = self._get_annotation_insert_position(node=node)
        new_items: list[stmt] = self._create_annotation_items(
            class_info=class_info,
            existing=existing,
        )
        if new_items:
            node.body[insert_at:insert_at] = new_items

    def _protocolize_body(self, node: ClassDef) -> None:
        """Protocolize body.

        Args:
            node: AST node being inspected or transformed.

        """
        for body_item in node.body:
            if isinstance(body_item, FunctionDef):
                self._fix_protocol_method(function=body_item)
            if isinstance(body_item, AnnAssign) and isinstance(
                body_item.target,
                Name,
            ):
                if annotation_is_none(annotation=body_item.annotation):
                    body_item.annotation = Name(
                        id=Constants.object,
                        ctx=Load(),
                    )
                body_item.value = None
            if (
                isinstance(body_item, Assign)
                and len(body_item.targets) == 1
                and isinstance(body_item.targets[0], Name)
            ):
                body_item.value = Constant(value=Ellipsis)

    def _fix_protocol_method(self, *, function: FunctionDef) -> None:
        """Fix protocol method annotations and body.

        Args:
            function: The function examined while fix protocol method
                annotations and body.

        """
        if (
            function.args.args
            and function.args.args[0].arg == "self"
            and (function.args.args[0].annotation is None)
        ):
            function.args.args[0].annotation = Name(id="Self", ctx=Load())
            self.needed_imports.add("Self")
        if function.name in Constants.binary_magic_methods:
            if function.returns is None or _is_none_annotation(
                annotation=function.returns,
            ):
                function.returns = Name(id="Self", ctx=Load())
                self.needed_imports.add("Self")
            if not has_ellipsis_body(function=function):
                function.body = [
                    Return(
                        value=BinOp(
                            left=Name(id="self", ctx=Load()),
                            op=Constants.binary_magic_methods[function.name](),
                            right=Name(id="other", ctx=Load()),
                        ),
                    ),
                ]

    def _convert_result_class_to_namedtuple(self, node: ClassDef) -> None:
        """Convert result class to namedtuple.

        Args:
            node: AST node being inspected or transformed.

        """
        fields: list[tuple[str, TypeExpr]] = namedtuple_fields(node=node)
        if not fields:
            return
        node.bases = [Name(id="NamedTuple", ctx=Load())]
        node.decorator_list = []
        self.needed_imports.add("NamedTuple")
        new_body: list[stmt] = []
        if (
            node.body
            and isinstance(node.body[0], Expr)
            and isinstance(node.body[0].value, Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            new_body.append(node.body[0])
        for name, type_expr in fields:
            new_body.append(
                AnnAssign(
                    target=Name(id=name, ctx=Store()),
                    annotation=self._annotation_expr(type_expr=type_expr),
                    value=None,
                    simple=1,
                ),
            )
        node.body = new_body

    def _prepend_imports(self, body: list[stmt]) -> list[stmt]:
        """Prepend imports.

        Args:
            body: Statements to analyze in execution order.

        Returns:
            Result of the operation, according to the declared return type.

        """
        used_names: set[str] = annotation_name_set(body=body)
        runtime_names: set[str] = runtime_name_set(body=body)
        retained_names: set[str] = used_names | runtime_names
        typing_names: set[str] = {
            name
            for name in self.needed_imports | used_names
            if name in typing_import_names()
        }
        abc_names: set[str] = {
            name
            for name in self.needed_imports | retained_names
            if name in collections_abc_import_names()
        }
        if typing_names:
            new_body: list[stmt] = ensure_from_import(
                body=body,
                module="typing",
                names=sorted(typing_names),
            )
            body = new_body
        if abc_names:
            new_body = ensure_from_import(
                body=body,
                module="collections.abc",
                names=sorted(abc_names),
            )
            body = new_body
        if "ReferenceType" in retained_names:
            new_body = ensure_from_import(
                body=body,
                module="weakref",
                names=["ReferenceType"],
            )
            body = new_body
        if "ModuleType" in retained_names:
            new_body = ensure_from_import(
                body=body,
                module="types",
                names=["ModuleType"],
            )
            body = new_body
        return normalize_imports(body=body, used_names=retained_names)


def infer_constant(
    *,
    value: str | bytes | complex | bool | None | EllipsisType,
) -> TypeExpr:
    """Infer the type of a constant value.

    Args:
        value: The value examined while infer the type of a constant value.

    Returns:
        TypeExpr produced by this operation.

    """
    if isinstance(value, bool):
        return _BOOL_TYPE
    if isinstance(value, int):
        return _INT_TYPE
    if isinstance(value, float):
        return _FLOAT_TYPE
    if isinstance(value, str):
        return _STR_TYPE
    if value is None:
        return _NONE_TYPE
    return _OBJECT_TYPE


def infer_builtin_name(name: str) -> TypeExpr:
    """Infer the type of a builtin name.

    Args:
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr produced by this operation.

    """
    if name in {"True", "False"}:
        return _BOOL_TYPE
    if name == "None":
        return _NONE_TYPE
    return _UNKNOWN_TYPE


def merge_scopes(*, name: str, scopes: Sequence[ScopeState]) -> ScopeState:
    """Merge branch-local scopes after conditional execution.

    Args:
        name: Identifier of the name being resolved.
        scopes: Collection of scopes supplied for this operation.

    Returns:
        ScopeState produced by this operation.

    """
    if not scopes:
        return ScopeState(name=name)
    merged: ScopeState = scopes[0].clone(name=name)
    variable_names: set[str] = set()
    scope: ScopeState
    for scope in scopes:
        variable_names.update(scope.variables)
    variable_name: str
    for variable_name in variable_names:
        values: list[TypeExpr] = [
            scope.variables[variable_name]
            for scope in scopes
            if variable_name in scope.variables
        ]
        if values:
            merged.variables[variable_name] = merge_many(types=values)
    return merged


def contains_none(type_expr: TypeExpr) -> bool:
    """Check if a type expression contains None.

    Args:
        type_expr: The type expr examined while check if a type expression
            contains None.

    Returns:
        Whether the requested condition holds.

    """
    if type_expr.name == Constants.none:
        return True
    if type_expr.kind == "union":
        return any(contains_none(type_expr=item) for item in type_expr.args)
    return False


def remove_none(type_expr: TypeExpr) -> TypeExpr:
    """Remove None from a type expression.

    Args:
        type_expr: The type expr examined while remove None from a type
            expression.

    Returns:
        TypeExpr produced by this operation.

    """
    if type_expr.name == Constants.none:
        return _UNKNOWN_TYPE
    if type_expr.kind != "union":
        return type_expr
    items: list[TypeExpr] = [
        item for item in type_expr.args if not contains_none(type_expr=item)
    ]
    return merge_many(types=items) if items else _UNKNOWN_TYPE


def only_none(type_expr: TypeExpr) -> bool:
    """Check if a type expression is only None.

    Args:
        type_expr: The type expr examined while check if a type expression is
            only None.

    Returns:
        Whether the requested condition holds.

    """
    return type_expr.name == Constants.none


def can_be_falsy(type_expr: TypeExpr) -> bool:
    """Decide if a type may produce ``False`` in bool context.

    Args:
        type_expr: The type expr examined while decide if a type may produce
            ``False`` in bool context.

    Returns:
        Whether the requested condition holds.

    """
    if type_expr.is_unknown() or type_expr.key() == _OBJECT_TYPE.key():
        return True
    if type_expr.kind == "union":
        return any(can_be_falsy(type_expr=item) for item in type_expr.args)
    if type_expr.name in {
        Constants.none,
        Constants.bool,
        Constants.int,
        Constants.float,
        Constants.str,
    }:
        return True
    if type_expr.kind == "generic" and type_expr.name in {
        "list",
        "set",
        "dict",
        "tuple",
        "Sequence",
        "Iterable",
        "Mapping",
    }:
        return True
    return True


def can_be_truthy(type_expr: TypeExpr) -> bool:
    """Decide if a type may produce ``True`` in bool context.

    Args:
        type_expr: The type expr examined while decide if a type may produce
            ``True`` in bool context.

    Returns:
        Whether the requested condition holds.

    """
    if type_expr.kind == "union":
        return any(can_be_truthy(type_expr=item) for item in type_expr.args)
    return type_expr.name != Constants.none


def type_from_isinstance_target(node: expr) -> TypeExpr:
    """Extract type expression from isinstance target.

    Args:
        node: The node examined while extract type expression from isinstance
            target.

    Returns:
        TypeExpr produced by this operation.

    """
    if isinstance(node, Name):
        return TypeExpr.name_expr(name=node.id)
    if isinstance(node, Tuple):
        return TypeExpr.union(
            *[type_from_isinstance_target(node=item) for item in node.elts],
        )
    if isinstance(node, Attribute):
        name: str = expr_name(node=node)
        return TypeExpr.name_expr(name=name.rsplit(sep=".", maxsplit=1)[-1])
    return _UNKNOWN_TYPE


def type_family(type_expr: TypeExpr) -> str:
    """Get the base name family of a type expression.

    Args:
        type_expr: The type expr examined while get the base name family of a
            type expression.

    Returns:
        str produced by this operation.

    """
    return type_expr.name


def is_definitely_instance_type(
    *,
    value_type: TypeExpr,
    target_type: TypeExpr,
) -> bool:
    """Check if value_type is definitely an instance of target_type.

    Args:
        target_type: Target type supplied as TypeExpr for this operation.
        value_type: Value type supplied as TypeExpr for this operation.

    Returns:
        Whether the requested condition holds.

    """
    if value_type.kind == "union":
        return all(
            is_definitely_instance_type(
                value_type=item,
                target_type=target_type,
            )
            for item in value_type.args
        )
    target_name: str = type_family(type_expr=target_type)
    value_name: str = type_family(type_expr=value_type)
    if target_name in {"Mapping", "MutableMapping"}:
        return value_name in {"dict", "Mapping", "OrderedDict", "defaultdict"}
    if target_name == "Sequence":
        return value_name in {"list", "tuple", "str", "Sequence"}
    if target_name in {"Iterable", "Iterator"}:
        return value_name in {
            "list",
            "tuple",
            "str",
            "set",
            "dict",
            "Mapping",
            "Iterator",
            "Iterable",
        }
    return value_name == target_name


def is_definitely_not_instance_type(
    *,
    value_type: TypeExpr,
    target_type: TypeExpr,
) -> bool:
    """Check if value_type is definitely not an instance of target_type.

    Args:
        target_type: Target type supplied as TypeExpr for this operation.
        value_type: Value type supplied as TypeExpr for this operation.

    Returns:
        Whether the requested condition holds.

    """
    if value_type.is_unknown() or value_type.key() == _OBJECT_TYPE.key():
        return False
    if value_type.kind == "union":
        return all(
            is_definitely_not_instance_type(
                value_type=item,
                target_type=target_type,
            )
            for item in value_type.args
        )
    if is_definitely_instance_type(
        value_type=value_type,
        target_type=target_type,
    ):
        return False
    target_name: str = type_family(type_expr=target_type)
    value_name: str = type_family(type_expr=value_type)
    incompatible: dict[str, set[str]] = {
        "Mapping": {"list", "tuple", "str", "int", "float", "bool", "set"},
        "Sequence": {
            "dict",
            "Mapping",
            "OrderedDict",
            "defaultdict",
            "int",
            "float",
            "bool",
        },
        "str": {"list", "dict", "Mapping", "int", "float", "bool", "set"},
        "int": {"list", "dict", "Mapping", "str", "set", "tuple"},
    }
    return value_name in incompatible.get(target_name, set())


def _handle_named_expr_condition(
    *,
    test: NamedExpr,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle NamedExpr in condition.

    Args:
        scope: The scope examined while handle NamedExpr in condition.
        test: Test supplied as NamedExpr for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    value_type: TypeExpr = infer_literal_expr(node=test.value)
    if not value_type.is_unknown():
        bind_simple_target(
            target=test.target,
            type_expr=value_type,
            scope=scope,
        )
    return None


def _handle_name_condition(
    *,
    test: Name,
    scope: ScopeState,
) -> BranchCondition:
    """Handle Name in condition (truthiness).

    Args:
        scope: The scope examined while handle Name in condition (truthiness).
        test: Test supplied as Name for this operation.

    Returns:
        BranchCondition produced by this operation.

    """
    current: TypeExpr = scope.get(name=test.id)
    visible_current: TypeExpr = (
        _OBJECT_TYPE if current.is_unknown() else current
    )
    return BranchCondition(
        name=test.id,
        true_type=visible_current,
        false_type=visible_current,
        true_reachable=can_be_truthy(type_expr=current),
        false_reachable=can_be_falsy(type_expr=current),
        reason="truthiness",
    )


def _handle_unary_op_not_condition(
    *,
    test: UnaryOp,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle UnaryOp with Not in condition.

    Args:
        scope: The scope examined while handle UnaryOp with Not in condition.
        test: Test supplied as UnaryOp for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    inner: BranchCondition | None = condition_from_test(
        test=test.operand,
        scope=scope,
    )
    if inner is None:
        return None
    return BranchCondition(
        name=inner.name,
        true_type=inner.false_type,
        false_type=inner.true_type,
        true_reachable=inner.false_reachable,
        false_reachable=inner.true_reachable,
        reason=(f"not({inner.reason})"),
    )


def _handle_isinstance_call_condition(
    *,
    test: Call,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle isinstance() call in condition.

    Args:
        scope: The scope examined while handle isinstance() call in condition.
        test: Test supplied as Call for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    checked_name: str = cast(typ="Name", val=test.args[0]).id
    target_type: TypeExpr = type_from_isinstance_target(node=test.args[1])
    if not target_type.is_unknown():
        current_type: TypeExpr = scope.get(name=checked_name)
        true_reachable: bool = not is_definitely_not_instance_type(
            value_type=current_type,
            target_type=target_type,
        )
        false_reachable: bool = not is_definitely_instance_type(
            value_type=current_type,
            target_type=target_type,
        )
        return BranchCondition(
            name=checked_name,
            true_type=current_type
            if is_definitely_instance_type(
                value_type=current_type,
                target_type=target_type,
            )
            else target_type,
            false_type=current_type,
            true_reachable=true_reachable,
            false_reachable=false_reachable,
            reason="isinstance",
        )
    return None


def _handle_bool_op_and_condition(
    *,
    test: BoolOp,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle BoolOp with And in condition.

    Args:
        scope: The scope examined while handle BoolOp with And in condition.
        test: Test supplied as BoolOp for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    current_scope: ScopeState = scope
    combined: BranchCondition | None = None
    value: expr
    for value in test.values:
        true_scope, false_scope = branch_scopes_from_condition(
            condition=condition_from_test(test=value, scope=current_scope),
            scope=current_scope,
        )
        if true_scope is None:
            return BranchCondition(
                name="",
                true_reachable=False,
                false_reachable=True,
                reason="and-unreachable",
            )
        current_scope = true_scope
        if false_scope is not None and combined is None:
            combined = condition_from_test(test=value, scope=scope)
    return combined


def _handle_compare_none_condition(
    *,
    left: Name,
    op_name: str,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle Compare with None literal.

    Args:
        left: Left supplied as Name for this operation.
        op_name: Identifier of the op being resolved.
        scope: The scope examined while handle Compare with None literal.

    Returns:
        BranchCondition | None produced by this operation.

    """
    current: TypeExpr = scope.get(name=left.id)
    visible_current: TypeExpr = (
        _OBJECT_TYPE if current.is_unknown() else current
    )
    without_none: TypeExpr = remove_none(type_expr=visible_current)
    has_none: bool = (
        contains_none(type_expr=visible_current) or current.is_unknown()
    )
    if op_name in {"IsNot", "NotEq"}:
        return BranchCondition(
            name=left.id,
            true_type=without_none
            if not without_none.is_unknown()
            else visible_current,
            false_type=_NONE_TYPE,
            true_reachable=not only_none(type_expr=current),
            false_reachable=has_none or current.is_unknown(),
            reason="is-not-none",
        )
    if op_name in {"Is", "Eq"}:
        return BranchCondition(
            name=left.id,
            true_type=_NONE_TYPE,
            false_type=without_none
            if not without_none.is_unknown()
            else visible_current,
            true_reachable=has_none or current.is_unknown(),
            false_reachable=not only_none(type_expr=current),
            reason="is-none",
        )
    return None


def _handle_compare_membership_condition(
    *,
    left: Name,
    right: expr,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle Compare with In/NotIn membership test.

    Args:
        left: Left supplied as Name for this operation.
        right: Right supplied as expr for this operation.
        scope: The scope examined while handle Compare with In/NotIn membership
            test.

    Returns:
        BranchCondition | None produced by this operation.

    """
    container_type: TypeExpr = scope.get(name=expr_name(node=right))
    narrowed: TypeExpr = element_type(type_expr=container_type)
    if narrowed.key() == _OBJECT_TYPE.key() and isinstance(
        right,
        (List, Tuple, Set),
    ):
        narrowed = merge_many(
            types=[infer_literal_expr(node=item) for item in right.elts],
        )
    if not narrowed.is_unknown():
        current_left: TypeExpr = scope.get(name=left.id)
        true_type: TypeExpr = merge_types(left=current_left, right=narrowed)
        return BranchCondition(
            name=left.id,
            true_type=true_type,
            false_type=current_left,
            true_reachable=True,
            false_reachable=True,
            reason="membership",
        )
    return None


def _handle_compare_isinstance_condition(
    *,
    test: Compare,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle Compare with isinstance call on left side.

    Args:
        scope: The scope examined while handle Compare with isinstance call on
            left side.
        test: Test supplied as Compare for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    checked_name: str = cast(
        typ="Name",
        val=cast(typ="Call", val=test.left).args[0],
    ).id
    target_type: TypeExpr = type_from_isinstance_target(
        node=cast(typ="Call", val=test.left).args[1],
    )
    if not target_type.is_unknown():
        current_type: TypeExpr = scope.get(name=checked_name)
        true_reachable: bool = not is_definitely_not_instance_type(
            value_type=current_type,
            target_type=target_type,
        )
        false_reachable: bool = not is_definitely_instance_type(
            value_type=current_type,
            target_type=target_type,
        )
        return BranchCondition(
            name=checked_name,
            true_type=target_type,
            false_type=current_type,
            true_reachable=true_reachable,
            false_reachable=false_reachable,
            reason="isinstance",
        )
    return None


def _handle_compare_condition(
    *,
    test: Compare,
    scope: ScopeState,
) -> BranchCondition | None:
    """Handle Compare node in condition.

    Args:
        scope: The scope examined while handle Compare node in condition.
        test: Test supplied as Compare for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    left: expr = test.left
    right: expr = test.comparators[0]
    op_name: str = test.ops[0].__class__.__name__
    if isinstance(left, Name) and is_none_literal(node=right):
        return _handle_compare_none_condition(
            left=left,
            op_name=op_name,
            scope=scope,
        )
    if isinstance(right, Name) and is_none_literal(node=left):
        mirrored: Compare = Compare(
            left=right,
            ops=test.ops,
            comparators=[left],
        )
        return condition_from_test(test=mirrored, scope=scope)
    if op_name in {"In", "NotIn"} and isinstance(left, Name):
        return _handle_compare_membership_condition(
            left=left,
            right=right,
            scope=scope,
        )
    if (
        isinstance(test.left, Call)
        and expr_name(node=test.left.func) == "isinstance"
        and (len(test.left.args) >= Constants.min_type_args)
        and isinstance(test.left.args[0], Name)
    ):
        return _handle_compare_isinstance_condition(test=test, scope=scope)
    return None


def condition_from_test(
    *,
    test: expr,
    scope: ScopeState,
) -> BranchCondition | None:
    """Extract branch-local type constraints from a test expression.

    Args:
        scope: The scope examined while extract branch-local type constraints
            from a test expression.
        test: Test supplied as expr for this operation.

    Returns:
        BranchCondition | None produced by this operation.

    """
    result: BranchCondition | None = None
    if isinstance(test, NamedExpr):
        result = _handle_named_expr_condition(test=test, scope=scope)
    elif isinstance(test, Name):
        result = _handle_name_condition(test=test, scope=scope)
    elif isinstance(test, UnaryOp) and test.op.__class__.__name__ == "Not":
        result = _handle_unary_op_not_condition(test=test, scope=scope)
    elif (
        isinstance(test, Call)
        and expr_name(node=test.func) == "isinstance"
        and (len(test.args) >= Constants.min_type_args)
        and isinstance(test.args[0], Name)
    ):
        result = _handle_isinstance_call_condition(test=test, scope=scope)
    elif isinstance(test, BoolOp):
        result = (
            _handle_bool_op_and_condition(test=test, scope=scope)
            if test.op.__class__.__name__ == "And" and test.values
            else None
        )
    elif (
        isinstance(test, Compare)
        and len(test.ops) == 1
        and (len(test.comparators) == 1)
    ):
        result = _handle_compare_condition(test=test, scope=scope)
    return result


def branch_scopes_from_condition(
    *,
    condition: BranchCondition | None,
    scope: ScopeState,
) -> tuple[ScopeState | None, ScopeState | None]:
    """Create true/false scopes from a branch condition.

    Args:
        condition: Condition supplied as BranchCondition | None for this
            operation.
        scope: The scope examined while create true/false scopes from a branch
            condition.

    Returns:
        tuple[ScopeState | None, ScopeState | None] produced by this operation.

    """
    if condition is None:
        return (
            scope.clone(name=(f"{scope.name}:true")),
            scope.clone(name=(f"{scope.name}:false")),
        )
    true_scope: ScopeState | None = None
    false_scope: ScopeState | None = None
    if condition.true_reachable:
        true_scope = scope.clone(name=f"{scope.name}:true")
        if condition.name and condition.true_type is not None:
            true_scope.set_exact(
                name=condition.name,
                type_expr=condition.true_type,
            )
    if condition.false_reachable:
        false_scope = scope.clone(name=f"{scope.name}:false")
        if condition.name and condition.false_type is not None:
            false_scope.set_exact(
                name=condition.name,
                type_expr=condition.false_type,
            )
    return (true_scope, false_scope)


def bind_simple_target(
    *,
    target: AST,
    type_expr: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind a simple target (Name) to a type expression.

    Args:
        scope: The scope examined while bind a simple target (Name) to a type
            expression.
        target: The target examined while bind a simple target (Name) to a type
            expression.
        type_expr: The type expr examined while bind a simple target (Name) to
            a type expression.

    """
    if isinstance(target, Name):
        scope.set(name=target.id, type_expr=type_expr)


def _bind_match_as_pattern(
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind MatchAs pattern variables.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind MatchAs pattern variables.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    bound_name: str | None = cast(
        typ="str | None",
        val=getattr(pattern, "name", None),
    )
    subpattern: AST | None = cast(
        typ="AST | None",
        val=getattr(pattern, "pattern", None),
    )
    if bound_name is not None:
        scope.set(name=bound_name, type_expr=subject_type)
    if subpattern is not None:
        bind_pattern_scope(
            pattern=subpattern,
            subject_type=subject_type,
            scope=scope,
        )


def _bind_match_star_pattern(
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind MatchStar pattern variables.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind MatchStar pattern variables.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    bound_name: str | None = cast(
        typ="str | None",
        val=getattr(pattern, "name", None),
    )
    if bound_name is not None:
        scope.set(
            name=bound_name,
            type_expr=TypeExpr.generic(
                "list",
                element_type(type_expr=subject_type),
            ),
        )


def _bind_match_sequence_pattern(
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind MatchSequence pattern variables.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind MatchSequence pattern variables.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    patterns: list[AST] = cast(
        typ="list[AST]",
        val=getattr(pattern, "patterns", []),
    )
    item_type: TypeExpr = element_type(type_expr=subject_type)
    for item in patterns:
        bind_pattern_scope(pattern=item, subject_type=item_type, scope=scope)


def _bind_match_mapping_pattern(
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind MatchMapping pattern variables.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind MatchMapping pattern variables.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    patterns: list[AST] = cast(
        typ="list[AST]",
        val=getattr(pattern, "patterns", []),
    )
    value_type: TypeExpr = (
        subject_type.args[1]
        if subject_type.kind == "generic"
        and len(subject_type.args) >= Constants.min_type_args
        else _OBJECT_TYPE
    )
    for item in patterns:
        bind_pattern_scope(pattern=item, subject_type=value_type, scope=scope)
    rest_name: str | None = cast(
        typ="str | None",
        val=getattr(pattern, "rest", None),
    )
    if rest_name is not None:
        scope.set(name=rest_name, type_expr=subject_type)


def _bind_match_class_pattern(
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind MatchClass pattern variables.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind MatchClass pattern variables.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    class_expr: expr | None = cast(
        typ="expr | None",
        val=getattr(pattern, "cls", None),
    )
    class_name: str = (
        expr_name(node=class_expr) if class_expr is not None else ""
    )
    positional_patterns: list[AST] = cast(
        typ="list[AST]",
        val=getattr(pattern, "patterns", []),
    )
    keyword_patterns: list[AST] = cast(
        typ="list[AST]",
        val=getattr(pattern, "kwd_patterns", []),
    )
    narrowed: TypeExpr = (
        TypeExpr.name_expr(name=class_name) if class_name else subject_type
    )
    for item in [*positional_patterns, *keyword_patterns]:
        bind_pattern_scope(
            pattern=item,
            subject_type=_OBJECT_TYPE,
            scope=scope,
        )
    scope.set(name="__match_subject__", type_expr=narrowed)


def bind_pattern_scope(
    *,
    pattern: AST,
    subject_type: TypeExpr,
    scope: ScopeState,
) -> None:
    """Bind simple match/case pattern variables into a case scope.

    Args:
        pattern: Pattern supplied as AST for this operation.
        scope: The scope examined while bind simple match/case pattern
            variables into a case scope.
        subject_type: Subject type supplied as TypeExpr for this operation.

    """
    pattern_name: str = pattern.__class__.__name__
    if pattern_name == "MatchAs":
        _bind_match_as_pattern(
            pattern=pattern,
            subject_type=subject_type,
            scope=scope,
        )
    elif pattern_name == "MatchStar":
        _bind_match_star_pattern(
            pattern=pattern,
            subject_type=subject_type,
            scope=scope,
        )
    elif pattern_name == "MatchSequence":
        _bind_match_sequence_pattern(
            pattern=pattern,
            subject_type=subject_type,
            scope=scope,
        )
    elif pattern_name == "MatchMapping":
        _bind_match_mapping_pattern(
            pattern=pattern,
            subject_type=subject_type,
            scope=scope,
        )
    elif pattern_name == "MatchClass":
        _bind_match_class_pattern(
            pattern=pattern,
            subject_type=subject_type,
            scope=scope,
        )


def merge_many(types: Iterable[TypeExpr]) -> TypeExpr:
    """Merge multiple type expressions into one.

    Args:
        types: Collection of types supplied for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    clean: list[TypeExpr] = [item for item in types if not item.is_unknown()]
    if not clean:
        return _UNKNOWN_TYPE
    result: TypeExpr = clean[0]
    for item in clean[1:]:
        result = merge_types(left=result, right=item)
    return result


def merge_types(left: TypeExpr, right: TypeExpr) -> TypeExpr:
    """Merge two type expressions, handling unions and generics.

    Args:
        left: Left supplied as TypeExpr for this operation.
        right: Right supplied as TypeExpr for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    if left.is_unknown():
        return right
    if right.is_unknown():
        return left
    if left.key() == right.key():
        return left
    result: TypeExpr | None = None
    if Constants.none in {left.name, right.name}:
        result = TypeExpr.union(left, right)
    elif (
        left.kind == "generic"
        and right.kind == "generic"
        and (left.name == right.name)
    ):
        if left.name == "tuple" and len(left.args) != len(right.args):
            result = TypeExpr.generic(
                "tuple",
                TypeExpr.union(*left.args, *right.args),
                TypeExpr.ellipsis_expr(),
            )
        else:
            result = TypeExpr.generic(
                left.name,
                *[
                    merge_types(left=a, right=b)
                    for a, b in zip(left.args, right.args, strict=False)
                ],
            )
    elif {left.name, right.name} <= {Constants.int, Constants.float}:
        result = (
            _FLOAT_TYPE
            if Constants.float in {left.name, right.name}
            else _INT_TYPE
        )
    return result if result is not None else TypeExpr.union(left, right)


def merge_class_attribute_type(
    *,
    old_attr: TypeExpr | None,
    new_attr: TypeExpr,
) -> TypeExpr:
    """Merge class attribute evidence treating ``None`` defaults weakly.

    Args:
        new_attr: New attr supplied as TypeExpr for this operation.
        old_attr: Old attr supplied as TypeExpr | None for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    if old_attr is None or old_attr.is_unknown():
        return new_attr
    old_key: str = old_attr.key()
    new_key: str = new_attr.key()
    none_key: str = _NONE_TYPE.key()
    object_key: str = _OBJECT_TYPE.key()
    result: TypeExpr
    if (old_key == none_key) != (new_key == none_key):
        result = new_attr if old_key == none_key else old_attr
    elif old_key == object_key and new_key != none_key:
        result = new_attr
    elif (
        new_attr.kind == "union"
        and none_key in new_key
        and (old_key in new_key)
    ) or (
        old_attr.kind == "union"
        and none_key in old_key
        and (new_key in old_key)
    ):
        result = new_attr if new_attr.kind == "union" else old_attr
    else:
        result = merge_types(left=old_attr, right=new_attr)
    return result


def infer_optional_from_default(type_expr: TypeExpr) -> TypeExpr:
    """Infer optional type from default value (None).

    Args:
        type_expr: The type expr examined while infer optional type from
            default value (None).

    Returns:
        TypeExpr produced by this operation.

    """
    if type_expr.name == Constants.none:
        return TypeExpr.union(_INT_TYPE, _NONE_TYPE)
    return type_expr


def element_type(type_expr: TypeExpr) -> TypeExpr:
    """Extract element type from container type expression.

    Args:
        type_expr: The type expr examined while extract element type from
            container type expression.

    Returns:
        TypeExpr produced by this operation.

    """
    if type_expr.kind == "generic":
        if (
            type_expr.name
            in {
                "list",
                "set",
                "Sequence",
                "Iterable",
                "Iterator",
                "Generator",
                "deque",
                "Counter",
            }
            and type_expr.args
        ):
            return type_expr.args[0]
        if (
            type_expr.name in {"dict", "Mapping", "OrderedDict", "defaultdict"}
            and len(type_expr.args) >= Constants.min_type_args
        ):
            return TypeExpr.generic(
                "tuple",
                type_expr.args[0],
                type_expr.args[1],
            )
        if type_expr.name == "tuple" and type_expr.args:
            return TypeExpr.union(*type_expr.args)
    if type_expr.name == Constants.str:
        return _STR_TYPE
    if type_expr.name == "range":
        return _INT_TYPE
    return _OBJECT_TYPE


def infer_subscript(container: TypeExpr, slice_node: expr) -> TypeExpr:
    """Infer type from subscript operation on container.

    Args:
        container: Container supplied as TypeExpr for this operation.
        slice_node: Slice node supplied as expr for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    if container.kind == "union":
        return merge_many(
            types=(
                infer_subscript(container=item, slice_node=slice_node)
                for item in container.args
            ),
        )
    result: TypeExpr | None = None
    if isinstance(slice_node, Slice):
        if container.kind == "generic":
            result = container
        elif container.name == Constants.str:
            result = _STR_TYPE
        else:
            result = container
    elif container.kind == "generic":
        if (
            container.name
            in {"list", "Sequence", "Iterable", "Iterator", "deque"}
            and container.args
        ):
            result = container.args[0]
        elif (
            container.name in {"dict", "Mapping", "OrderedDict", "defaultdict"}
            and len(container.args) >= Constants.min_type_args
        ):
            result = container.args[1]
        elif container.name == "tuple" and container.args:
            result = TypeExpr.union(*container.args)
    elif container.name == Constants.str:
        result = _STR_TYPE
    return result if result is not None else _OBJECT_TYPE


def _infer_bitwise_binop(left: TypeExpr, right: TypeExpr) -> TypeExpr:
    """Infer types for bitwise operations.

    Args:
        left: Left supplied as TypeExpr for this operation.
        right: Right supplied as TypeExpr for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    if left.name == Constants.bool and right.name == Constants.bool:
        return _BOOL_TYPE
    if (
        left.kind == "generic"
        and right.kind == "generic"
        and (left.name == right.name)
    ):
        return merge_types(left=left, right=right)
    return _INT_TYPE


def _infer_arithmetic_binop(
    left: TypeExpr,
    right: TypeExpr,
    op: AST,
) -> TypeExpr | None:
    """Infer types for arithmetic operations.

    Args:
        left: Left supplied as TypeExpr for this operation.
        op: Op supplied as AST for this operation.
        right: Right supplied as TypeExpr for this operation.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if op.__class__.__name__ in {"LShift", "RShift", "FloorDiv", "Mod", "Pow"}:
        return _INT_TYPE
    if isinstance(op, Div):
        return _FLOAT_TYPE
    if isinstance(op, (Add, Mult)):
        if Constants.str in {left.name, right.name}:
            return (
                _STR_TYPE
                if left.name in {Constants.str, Constants.int}
                and right.name in {Constants.str, Constants.int}
                else _OBJECT_TYPE
            )
        if left.kind == "generic" and left.name == "list":
            return left
        if right.kind == "generic" and right.name == "list":
            return right
    return None


def infer_binop(left: TypeExpr, right: TypeExpr, op: AST) -> TypeExpr:
    """Infer type from binary operation.

    Args:
        left: Left supplied as TypeExpr for this operation.
        op: Op supplied as AST for this operation.
        right: Right supplied as TypeExpr for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    result: TypeExpr | None = None
    if isinstance(op, (BitAnd, BitOr, BitXor)):
        result = _infer_bitwise_binop(left=left, right=right)
    else:
        result = _infer_arithmetic_binop(left=left, right=right, op=op)
    if result is not None:
        return result
    if isinstance(op, MatMult):
        return left if not left.is_unknown() else _OBJECT_TYPE
    if Constants.float in {left.name, right.name}:
        return _FLOAT_TYPE
    if left.name == Constants.int and right.name == Constants.int:
        return _INT_TYPE
    if left.name == Constants.bool and right.name == Constants.bool:
        return _BOOL_TYPE
    return merge_types(left=left, right=right)


def _infer_simple_builtin_type(name: str) -> TypeExpr | None:
    """Infer types for simple builtin type conversions.

    Args:
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    type_map: dict[str, TypeExpr] = {
        "int": _INT_TYPE,
        "str": _STR_TYPE,
        "bool": _BOOL_TYPE,
        "sum": _INT_TYPE,
        "len": _INT_TYPE,
        "all": _BOOL_TYPE,
        "any": _BOOL_TYPE,
        "isinstance": _BOOL_TYPE,
        "issubclass": _BOOL_TYPE,
        "callable": _BOOL_TYPE,
    }
    return type_map.get(name)


def _infer_iterator_call(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for iterator-related builtin calls.

    Args:
        call: The call examined while infer types for iterator-related builtin
            calls.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer types for iterator-related
            builtin calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if not call.args and name != "range":
        return None
    result: TypeExpr | None = None
    if name == "iter":
        result = TypeExpr.generic(
            "Iterator",
            element_type(type_expr=infer(call.args[0], scope)),
        )
    elif name == "next":
        result = element_type(type_expr=infer(call.args[0], scope))
    elif name == "range":
        result = TypeExpr.name_expr(name="range")
    elif name == "enumerate":
        item_type: TypeExpr = element_type(
            type_expr=infer(call.args[0], scope),
        )
        result = TypeExpr.generic(
            "Iterator",
            TypeExpr.generic("tuple", _INT_TYPE, item_type),
        )
    elif name in {"max", "min"}:
        first: TypeExpr = infer(call.args[0], scope)
        if (
            first.kind == "generic"
            and first.name == "list"
            and (len(call.args) > 1)
        ):
            values: list[TypeExpr] = [first]
            values.extend(infer(item, scope) for item in call.args[1:])
            result = merge_many(types=values)
        else:
            result = element_type(type_expr=first)
    return result


def _infer_collection_constructor(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for collection constructor calls.

    Args:
        call: The call examined while infer types for collection constructor
            calls.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer types for collection constructor
            calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if name in {"list", "set", "tuple"}:
        if not call.args:
            return TypeExpr.generic(name, _OBJECT_TYPE)
        arg_type: TypeExpr = infer(call.args[0], scope)
        if (
            name == "tuple"
            and arg_type.kind == "generic"
            and (arg_type.name == "tuple")
        ):
            return arg_type
        return TypeExpr.generic(name, element_type(type_expr=arg_type))
    return None


def _infer_dict_call(
    call: Call,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for dict constructor calls.

    Args:
        call: The call examined while infer types for dict constructor calls.
        infer: Callable used to infer the requested information.
        scope: The scope examined while infer types for dict constructor calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if call.args:
        dict_arg_type: TypeExpr = infer(call.args[0], scope)
        if (
            dict_arg_type.kind == "generic"
            and dict_arg_type.name
            in {"dict", "Mapping", "OrderedDict", "defaultdict"}
            and (len(dict_arg_type.args) >= Constants.min_type_args)
        ):
            return TypeExpr.generic(
                "dict",
                dict_arg_type.args[0],
                dict_arg_type.args[1],
            )
        if dict_arg_type.kind == "generic" and dict_arg_type.name in {
            "Iterable",
            "Iterator",
        }:
            item: TypeExpr = element_type(type_expr=dict_arg_type)
            if (
                item.kind == "generic"
                and item.name == "tuple"
                and (len(item.args) >= Constants.min_type_args)
            ):
                return TypeExpr.generic("dict", item.args[0], item.args[1])
    return TypeExpr.generic("dict", _STR_TYPE, _INT_TYPE)


def _infer_special_collection_call(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for special collection calls.

    Args:
        call: The call examined while infer types for special collection calls.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer types for special collection
            calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if name == "Counter" and call.args:
        return TypeExpr.generic(
            "Counter",
            element_type(type_expr=infer(call.args[0], scope)),
        )
    if name == "deque" and call.args:
        return TypeExpr.generic(
            "deque",
            element_type(type_expr=infer(call.args[0], scope)),
        )
    if name in {"defaultdict", "OrderedDict"}:
        return TypeExpr.generic(name, _STR_TYPE, _INT_TYPE)
    if name in {"WeakKeyDictionary", "WeakValueDictionary"}:
        return TypeExpr.generic(name, _OBJECT_TYPE, _OBJECT_TYPE)
    if name in {"permutations", "combinations"} and call.args:
        return TypeExpr.generic(
            "Iterator",
            TypeExpr.generic(
                "tuple",
                element_type(type_expr=infer(call.args[0], scope)),
                TypeExpr.ellipsis_expr(),
            ),
        )
    return None


def _infer_itertools_call(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for itertools function calls.

    Args:
        call: The call examined while infer types for itertools function calls.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer types for itertools function
            calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if name in {"product", "zip_longest"}:
        item_types: list[TypeExpr] = [
            element_type(type_expr=infer(item, scope)) for item in call.args
        ]
        if name == "zip_longest":
            item_types = [
                TypeExpr.union(item, _NONE_TYPE) for item in item_types
            ]
        return TypeExpr.generic(
            "Iterator",
            TypeExpr.generic("tuple", *item_types),
        )
    if name == "chain":
        return TypeExpr.generic(
            "Iterator",
            merge_many(
                types=(
                    element_type(type_expr=infer(item, scope))
                    for item in call.args
                ),
            ),
        )
    if (
        name in {"islice", "takewhile", "dropwhile", "compress", "accumulate"}
        and call.args
    ):
        data_arg: expr = (
            call.args[1]
            if name in {"takewhile", "dropwhile"} and len(call.args) > 1
            else call.args[0]
        )
        return TypeExpr.generic(
            "Iterator",
            element_type(type_expr=infer(data_arg, scope)),
        )
    return None


def _infer_special_function_call(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for special function calls.

    Args:
        call: The call examined while infer types for special function calls.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer types for special function calls.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if name == "partial":
        return TypeExpr.callable_expr(
            parameters=[TypeExpr.ellipsis_expr()],
            return_type=_INT_TYPE,
        )
    if name == "ref" and call.args:
        return TypeExpr.generic("ReferenceType", infer(call.args[0], scope))
    special_names: dict[str, TypeExpr] = {
        "Path": TypeExpr.name_expr(name="Path"),
        "tempfile.NamedTemporaryFile": _OBJECT_TYPE,
        "importlib.import_module": TypeExpr.name_expr(name="ModuleType"),
        "__import__": TypeExpr.name_expr(name="ModuleType"),
    }
    return special_names.get(name)


def _infer_method_like_call(name: str) -> TypeExpr | None:
    """Infer types for method-like calls (e.g., .read_text, .unlink).

    Args:
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    suffix_map: dict[str, TypeExpr] = {
        ".read_text": _STR_TYPE,
        ".unlink": _NONE_TYPE,
        ".write": _INT_TYPE,
        ".values": TypeExpr.generic("Iterable", _INT_TYPE),
        ".keys": TypeExpr.generic("Iterable", _STR_TYPE),
        ".items": TypeExpr.generic(
            "Iterable",
            TypeExpr.generic("tuple", _STR_TYPE, _INT_TYPE),
        ),
        ".upper": _STR_TYPE,
        ".lower": _STR_TYPE,
        ".__name__": _STR_TYPE,
        ".append": _NONE_TYPE,
        ".appendleft": _NONE_TYPE,
        ".update": _NONE_TYPE,
        ".add": _NONE_TYPE,
        ".pop": _NONE_TYPE,
        ".popleft": _NONE_TYPE,
    }
    return next(
        (
            return_type
            for suffix, return_type in suffix_map.items()
            if name.endswith(suffix)
        ),
        None,
    )


def infer_known_call(
    call: Call,
    name: str,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
    classes: Mapping[str, ClassInfo],
) -> TypeExpr | None:
    """Infer type from known builtin/standard library call.

    Args:
        call: The call examined while infer type from known builtin/standard
            library call.
        classes: Classes supplied as Mapping[str, ClassInfo] for this
            operation.
        infer: Callable used to infer the requested information.
        name: Identifier of the name being resolved.
        scope: The scope examined while infer type from known builtin/standard
            library call.

    Returns:
        TypeExpr | None produced by this operation.

    """
    inference_fns: list[Callable[[], TypeExpr | None]] = [
        lambda: _infer_simple_builtin_type(name=name),
        lambda: _infer_iterator_call(
            call=call,
            name=name,
            scope=scope,
            infer=infer,
        ),
        lambda: _infer_collection_constructor(
            call=call,
            name=name,
            scope=scope,
            infer=infer,
        ),
        lambda: (
            _infer_dict_call(call=call, scope=scope, infer=infer)
            if name == "dict"
            else None
        ),
        lambda: _infer_special_collection_call(
            call=call,
            name=name,
            scope=scope,
            infer=infer,
        ),
        lambda: _infer_itertools_call(
            call=call,
            name=name,
            scope=scope,
            infer=infer,
        ),
        lambda: _infer_special_function_call(
            call=call,
            name=name,
            scope=scope,
            infer=infer,
        ),
        lambda: _infer_method_like_call(name=name),
    ]
    for fn in inference_fns:
        result: TypeExpr | None = fn()
        if result is not None:
            return result
    return TypeExpr.name_expr(name=name) if name in classes else None


def _infer_path_method(method_name: str) -> TypeExpr | None:
    """Infer types for Path methods.

    Args:
        method_name: Identifier of the method being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if method_name in {"read_text", "read_file"}:
        return _STR_TYPE
    if method_name == "write_text":
        return _INT_TYPE
    if method_name == "unlink":
        return _NONE_TYPE
    return None


def _infer_str_method(method_name: str) -> TypeExpr | None:
    """Infer types for string methods.

    Args:
        method_name: Identifier of the method being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if method_name in {"upper", "lower", "strip", "replace", "join"}:
        return _STR_TYPE
    if method_name in {
        "startswith",
        "endswith",
        "isdigit",
        "isnumeric",
        "isdecimal",
        "isalnum",
        "isalpha",
    }:
        return _BOOL_TYPE
    return None


def _infer_list_method(
    receiver_type: TypeExpr,
    method_name: str,
) -> TypeExpr | None:
    """Infer types for list/Sequence methods.

    Args:
        method_name: Identifier of the method being resolved.
        receiver_type: Receiver type supplied as TypeExpr for this operation.

    Returns:
        TypeExpr | None produced by this operation.

    """
    item_type: TypeExpr = (
        receiver_type.args[0] if receiver_type.args else _OBJECT_TYPE
    )
    if method_name == "count":
        return _INT_TYPE
    if method_name in {"append", "extend", "insert", "sort", "reverse"}:
        return _NONE_TYPE
    if method_name == "pop":
        return item_type
    return None


def _infer_dict_method(
    receiver_type: TypeExpr,
    method_name: str,
    call: Call,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer types for dict/Mapping methods.

    Args:
        call: The call examined while infer types for dict/Mapping methods.
        infer: Callable used to infer the requested information.
        method_name: Identifier of the method being resolved.
        receiver_type: Receiver type supplied as TypeExpr for this operation.
        scope: The scope examined while infer types for dict/Mapping methods.

    Returns:
        TypeExpr | None produced by this operation.

    """
    key_type: TypeExpr = (
        receiver_type.args[0] if receiver_type.args else _OBJECT_TYPE
    )
    value_type: TypeExpr = (
        receiver_type.args[1] if len(receiver_type.args) > 1 else _OBJECT_TYPE
    )
    if method_name == "get":
        default_type: TypeExpr = _NONE_TYPE
        if len(call.args) >= Constants.min_type_args:
            default_type = infer(call.args[1], scope)
        for kw in call.keywords:
            if kw.arg == "default":
                default_type = infer(kw.value, scope)
        return TypeExpr.union(value_type, default_type)
    if method_name == "keys":
        return TypeExpr.generic("Iterable", key_type)
    if method_name == "values":
        return TypeExpr.generic("Iterable", value_type)
    if method_name == "items":
        return TypeExpr.generic(
            "Iterable",
            TypeExpr.generic("tuple", key_type, value_type),
        )
    return None


def _infer_generic_method(method_name: str) -> TypeExpr | None:
    """Infer types for generic collection methods.

    Args:
        method_name: Identifier of the method being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if method_name in {"append", "appendleft", "add", "pop", "popleft"}:
        return _NONE_TYPE
    return None


def infer_builtin_method_call(
    *,
    receiver_type: TypeExpr,
    method_name: str,
    call: Call,
    scope: ScopeState,
    infer: Callable[[expr, ScopeState], TypeExpr],
) -> TypeExpr | None:
    """Infer common stub-backed method return types lazily.

    Args:
        call: The call examined while infer common stub-backed method return
            types lazily.
        infer: Callable used to infer the requested information.
        method_name: Identifier of the method being resolved.
        receiver_type: Receiver type supplied as TypeExpr for this operation.
        scope: The scope examined while infer common stub-backed method return
            types lazily.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if receiver_type.name == "Path":
        return _infer_path_method(method_name=method_name)
    if receiver_type.name == Constants.str:
        return _infer_str_method(method_name=method_name)
    if receiver_type.kind == "generic" and receiver_type.name in {
        "list",
        "Sequence",
    }:
        return _infer_list_method(
            receiver_type=receiver_type,
            method_name=method_name,
        )
    if (
        receiver_type.kind == "generic"
        and receiver_type.name == "set"
        and (method_name in {"add", "discard", "update"})
    ):
        return _NONE_TYPE
    if receiver_type.kind == "generic" and receiver_type.name in {
        "dict",
        "Mapping",
        "OrderedDict",
        "defaultdict",
    }:
        return _infer_dict_method(
            receiver_type=receiver_type,
            method_name=method_name,
            call=call,
            scope=scope,
            infer=infer,
        )
    return _infer_generic_method(method_name=method_name)


def infer_attribute(
    expression: Attribute,
    scope: ScopeState,
    classes: Mapping[str, ClassInfo],
) -> TypeExpr:
    """Infer type from attribute access.

    Args:
        classes: Classes supplied as Mapping[str, ClassInfo] for this
            operation.
        expression: The expression examined while infer type from attribute
            access.
        scope: The scope examined while infer type from attribute access.

    Returns:
        TypeExpr produced by this operation.

    """
    value_name: str = expr_name(node=expression.value)
    if expression.attr == "__name__":
        return _STR_TYPE
    receiver: TypeExpr = scope.get(name=value_name)
    if receiver.name in classes:
        class_info: ClassInfo = classes[receiver.name]
        if expression.attr in class_info.attributes:
            return class_info.attributes[expression.attr]
        if expression.attr in class_info.methods:
            method: FunctionInfo = class_info.methods[expression.attr]
            return TypeExpr.callable_expr(
                parameters=[TypeExpr.ellipsis_expr()],
                return_type=method.return_type,
            )
    if receiver.name == "ModuleType" and expression.attr == "path":
        return TypeExpr.name_expr(name="ModuleType")
    attr_type_map: dict[str, TypeExpr] = {
        "name": _STR_TYPE,
        "x": _INT_TYPE,
        "y": _INT_TYPE,
        "z": _INT_TYPE,
        "seed": _INT_TYPE,
        "value": _INT_TYPE,
        "path": TypeExpr.name_expr(name="ModuleType"),
    }
    return attr_type_map.get(expression.attr, _UNKNOWN_TYPE)


def infer_comprehension_element(
    expression: GeneratorExp | ListComp | SetComp,
    engine: InferenceEngine,
    scope: ScopeState,
) -> TypeExpr:
    """Infer element type from comprehension expression.

    Args:
        engine: Engine supplied as InferenceEngine for this operation.
        expression: The expression examined while infer element type from
            comprehension expression.
        scope: The scope examined while infer element type from comprehension
            expression.

    Returns:
        TypeExpr produced by this operation.

    """
    local: ScopeState = ScopeState(name="comprehension", parent=scope)
    generator: comprehension
    for generator in expression.generators:
        iter_type: TypeExpr = engine.infer_expr(
            expression=generator.iter,
            scope=scope,
        )
        engine.bind_target(
            target=generator.target,
            type_expr=element_type(type_expr=iter_type),
            scope=local,
        )
    return engine.infer_expr(expression=expression.elt, scope=local)


def exception_type_from_handler(*, handler: ExceptHandler) -> TypeExpr:
    """Infer the bound exception variable type for an except handler.

    Args:
        handler: Handler supplied as ExceptHandler for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    handler_type: expr | None = getattr(handler, "type", None)
    if handler_type is None:
        return TypeExpr.name_expr(name="BaseException")
    if isinstance(handler_type, Name):
        return TypeExpr.name_expr(name=handler_type.id)
    if isinstance(handler_type, Tuple):
        return TypeExpr.union(
            *[
                type_from_isinstance_target(node=item)
                for item in handler_type.elts
            ],
        )
    return TypeExpr.name_expr(name="BaseException")


def infer_context_entry_type(
    *,
    context_type: TypeExpr,
    context_expr: expr,
) -> TypeExpr:
    """Infer the value produced by ``__enter__`` for common contexts.

    Args:
        context_expr: Context expr supplied as expr for this operation.
        context_type: Context type supplied as TypeExpr for this operation.

    Returns:
        TypeExpr produced by this operation.

    """
    context_name: str = expr_name(node=context_expr)
    if (
        context_name.endswith("NamedTemporaryFile")
        or context_name == "tempfile.NamedTemporaryFile"
    ):
        return TypeExpr.name_expr(name="object")
    if context_type.kind == "generic" and context_type.name == "Generator":
        return context_type.args[0] if context_type.args else _OBJECT_TYPE
    return _OBJECT_TYPE


def infer_nested_numeric_matrix_parameter(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> TypeExpr | None:
    """Detect nested numeric iteration patterns for matrix-like parameters.

    Args:
        function: The function examined while detect nested numeric iteration
            patterns for matrix-like parameters.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    for node in walk(node=function):
        if not isinstance(node, For):
            continue
        if not (isinstance(node.iter, Name) and node.iter.id == name):
            continue
        if not isinstance(node.target, Name):
            continue
        row_name: str = node.target.id
        child: AST
        for child in walk(node=node):
            if not isinstance(child, For):
                continue
            if not (
                isinstance(child.iter, Name) and child.iter.id == row_name
            ):
                continue
            if any(isinstance(grand, AugAssign) for grand in walk(node=child)):
                return TypeExpr.generic(
                    "Sequence",
                    TypeExpr.generic("Sequence", _INT_TYPE),
                )
    return None


def _handle_binop_in_param_usage(
    *,
    node: BinOp,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Handle BinOp node in param usage inference.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while handle BinOp node in param usage
            inference.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    if (
        contains_name(node=node.left, name=name)
        or contains_name(node=node.right, name=name)
    ) and (
        isinstance(node.op, (Add, Mult, BitAnd, BitOr, BitXor))
        or node.op.__class__.__name__
        in {"Sub", "FloorDiv", "Mod", "Pow", "LShift", "RShift"}
    ):
        observations.append(_INT_TYPE)


def _handle_compare_in_param_usage(
    *,
    node: Compare,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Handle Compare node in param usage inference.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while handle Compare node in param usage
            inference.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    is_none_check: bool = any(
        is_none_literal(node=comparator) for comparator in node.comparators
    )
    if not is_none_check and any(
        operator.__class__.__name__ in {"Gt", "GtE", "Lt", "LtE"}
        for operator in node.ops
    ):
        observations.append(_INT_TYPE)
        if any(
            operator.__class__.__name__ in {"In", "NotIn"}
            for operator in node.ops
        ):
            if (
                isinstance(node.left, Name)
                and node.left.id != name
                and contains_name(node=node.comparators[0], name=name)
            ):
                left_type: TypeExpr = infer_literal_expr(node=node.left)
                observations.append(TypeExpr.generic("Iterable", left_type))
            elif isinstance(node.left, Name) and node.left.id == name:
                observations.append(
                    _STR_TYPE
                    if isinstance(node.comparators[0], Constant)
                    and isinstance(node.comparators[0].value, str)
                    else _OBJECT_TYPE,
                )
        comparator_types: list[TypeExpr] = [
            infer_constant(value=comparator.value)
            for comparator in node.comparators
            if isinstance(comparator, Constant)
            and comparator.value is not None
        ]
        if comparator_types:
            observations.append(merge_many(types=comparator_types))


def _handle_call_in_param_usage(
    *,
    node: Call,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Handle Call node in param usage inference.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while handle Call node in param usage
            inference.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    call_name: str = expr_name(node=node.func)
    if call_name == "len" and any(
        contains_name(node=arg_node, name=name) for arg_node in node.args
    ):
        observations.append(TypeExpr.generic("Sequence", _OBJECT_TYPE))
    if call_name in {"all", "any", "iter", "max", "min", "sum"} and any(
        contains_name(node=arg_node, name=name) for arg_node in node.args
    ):
        observations.append(
            TypeExpr.generic(
                "Iterable",
                _INT_TYPE if call_name == "sum" else _OBJECT_TYPE,
            ),
        )
    if (
        call_name == "isinstance"
        and node.args
        and contains_name(node=node.args[0], name=name)
        and (len(node.args) > 1)
        and isinstance(node.args[1], Name)
    ):
        observations.append(TypeExpr.name_expr(name=node.args[1].id))
    if isinstance(node.func, Name) and node.func.id == name:
        observations.append(
            TypeExpr.callable_expr(
                parameters=[TypeExpr.ellipsis_expr()],
                return_type=_OBJECT_TYPE,
            ),
        )
    if (
        isinstance(node.func, Attribute)
        and isinstance(node.func.value, Name)
        and (node.func.value.id == name)
    ):
        if node.func.attr in {
            "upper",
            "lower",
            "strip",
            "isnumeric",
            "isdigit",
            "isdecimal",
            "isalnum",
            "isalpha",
        }:
            observations.append(_STR_TYPE)
        if node.func.attr in {"values", "items", "keys"}:
            observations.append(
                TypeExpr.generic("Mapping", _STR_TYPE, _INT_TYPE),
            )


def _handle_subscript_in_param_usage(
    *,
    node: Subscript,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Handle Subscript node in param usage inference.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while handle Subscript node in param usage
            inference.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    if isinstance(node.value, Name) and node.value.id == name:
        observations.append(TypeExpr.generic("Sequence", _INT_TYPE))


def _handle_raise_in_param_usage(
    *,
    node: Raise,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Handle Raise node in param usage inference.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while handle Raise node in param usage
            inference.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    if node.cause is not None and contains_name(node=node.cause, name=name):
        observations.append(TypeExpr.name_expr(name="BaseException"))


def _add_nested_loop_type_if_present(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
    observations: list[TypeExpr],
) -> None:
    """Add nested loop type observation if present.

    Args:
        function: The function examined while add nested loop type observation
            if present.
        name: Identifier of the name being resolved.
        observations: Observations supplied as list[TypeExpr] for this
            operation.

    """
    nested_loop_type: TypeExpr | None = infer_nested_numeric_matrix_parameter(
        function=function,
        name=name,
    )
    if nested_loop_type is not None:
        observations.append(nested_loop_type)


def _collect_param_usage_observations(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> list[TypeExpr]:
    """Collect type observations from function AST for parameter usage.

    Args:
        function: The function examined while collect type observations from
            function AST for parameter usage.
        name: Identifier of the name being resolved.

    Returns:
        list[TypeExpr] produced by this operation.

    """
    observations: list[TypeExpr] = []
    node: AST
    for node in walk(node=function):
        if isinstance(node, BinOp):
            _handle_binop_in_param_usage(
                node=node,
                name=name,
                observations=observations,
            )
        elif isinstance(node, Compare) and contains_name(node=node, name=name):
            _handle_compare_in_param_usage(
                node=node,
                name=name,
                observations=observations,
            )
        elif isinstance(node, Subscript):
            _handle_subscript_in_param_usage(
                node=node,
                name=name,
                observations=observations,
            )
        elif isinstance(node, Call):
            _handle_call_in_param_usage(
                node=node,
                name=name,
                observations=observations,
            )
        elif isinstance(node, Raise):
            _handle_raise_in_param_usage(
                node=node,
                name=name,
                observations=observations,
            )
    _add_nested_loop_type_if_present(
        function=function,
        name=name,
        observations=observations,
    )
    return observations


def infer_param_from_usage(
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> TypeExpr:
    """Infer parameter type from its usage in function body.

    Args:
        function: The function examined while infer parameter type from its
            usage in function body.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr produced by this operation.

    """
    if function.args.vararg is not None and function.args.vararg.arg == name:
        return infer_vararg_item_type(function=function, name=name)
    if function.args.kwarg is not None and function.args.kwarg.arg == name:
        return infer_kwarg_value_type(function=function, name=name)
    observations: list[TypeExpr] = _collect_param_usage_observations(
        function=function,
        name=name,
    )
    if not observations:
        return _UNKNOWN_TYPE
    return merge_many(types=observations)


def infer_param_type_from_self_assignment(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
    class_info: ClassInfo | None,
) -> TypeExpr | None:
    """Infer constructor parameter type from ``self.attr = parameter``.

    Args:
        class_info: The class info examined while infer constructor parameter
            type from ``self.attr = parameter``.
        function: The function examined while infer constructor parameter type
            from ``self.attr = parameter``.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if class_info is None:
        return None
    for node in walk(node=function):
        if not isinstance(node, Assign) or len(node.targets) != 1:
            continue
        target: expr = node.targets[0]
        if not (
            isinstance(target, Attribute)
            and isinstance(target.value, Name)
            and (target.value.id == "self")
            and isinstance(node.value, Name)
            and (node.value.id == name)
        ):
            continue
        attr_type: TypeExpr | None = class_info.attributes.get(target.attr)
        if attr_type is not None and (not attr_type.is_unknown()):
            return attr_type
        for class_method in class_info.methods.values():
            if attr_used_as_nested_numeric_matrix(
                function=class_method.node,
                attr_name=target.attr,
            ):
                return TypeExpr.generic(
                    "Sequence",
                    TypeExpr.generic("Sequence", _INT_TYPE),
                )
    return None


def attr_used_as_nested_numeric_matrix(
    *,
    function: FunctionDef | AsyncFunctionDef,
    attr_name: str,
) -> bool:
    """Detect nested numeric iteration over ``self.<attr_name>``.

    Args:
        attr_name: Identifier of the attr being resolved.
        function: The function examined while detect nested numeric iteration
            over ``self.<attr_name>``.

    Returns:
        Whether the requested condition holds.

    """
    for node in walk(node=function):
        if not isinstance(node, For):
            continue
        if not (
            isinstance(node.iter, Attribute)
            and isinstance(node.iter.value, Name)
            and (node.iter.value.id == "self")
            and (node.iter.attr == attr_name)
        ):
            continue
        return any(isinstance(child, AugAssign) for child in walk(node=node))
    return False


def parameter_is_used_as_peer_instance(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
    class_name: str,
) -> bool:
    """Return whether a parameter is used like another class instance.

    Args:
        class_name: Identifier of the class being resolved.
        function: The function examined while return whether a parameter is
            used like another class instance.
        name: Identifier of the name being resolved.

    Returns:
        Whether the requested condition holds.

    """
    seen_instance_attr: bool = False
    for node in walk(node=function):
        if (
            isinstance(node, Attribute)
            and isinstance(node.value, Name)
            and (node.value.id == name)
            and (node.attr in {"x", "y", "z", "value", "seed", "data"})
        ):
            seen_instance_attr = True
    return seen_instance_attr and class_name not in {"object", "type"}


def find_local_class_names(*, module: Module) -> set[str]:
    """Find all class names defined at module level.

    Args:
        module: The module examined while find all class names defined at
            module level.

    Returns:
        set[str] produced by this operation.

    """
    local_names: set[str] = set()

    class Visitor(LowercaseVisitor):
        function_depth: int = 0

        def visit_functiondef(self, node: FunctionDef) -> None:
            self.function_depth += 1
            self.generic_visit(node=node)
            self.function_depth -= 1

        def visit_asyncfunctiondef(self, node: AsyncFunctionDef) -> None:
            self.function_depth += 1
            self.generic_visit(node=node)
            self.function_depth -= 1

        def visit_classdef(self, node: ClassDef) -> None:
            if self.function_depth > 0:
                local_names.add(node.name)
            self.generic_visit(node=node)

    Visitor().visit(node=module)
    return local_names


def unsafe_keywordized_method_names() -> set[str]:
    """Return method names that are unsafe to keywordize.

    Returns:
        set[str] produced by this operation.

    """
    return {
        "add",
        "append",
        "appendleft",
        "count",
        "discard",
        "get",
        "extend",
        "insert",
        "pop",
        "popleft",
        "remove",
        "update",
        "write",
    }


def sanitize_annotation_type(*, type_expr: TypeExpr) -> TypeExpr:
    """Sanitize type expression for annotation use (replace unknown).

    Args:
        type_expr: The type expr examined while sanitize type expression for
            annotation use (replace unknown).

    Returns:
        TypeExpr produced by this operation.

    """
    if type_expr.is_unknown():
        return _OBJECT_TYPE
    if type_expr.kind == "generic":
        return TypeExpr.generic(
            type_expr.name,
            *[
                sanitize_annotation_type(type_expr=arg)
                for arg in type_expr.args
            ],
        )
    if type_expr.kind == "union":
        return TypeExpr.union(
            *[
                sanitize_annotation_type(type_expr=arg)
                for arg in type_expr.args
            ],
        )
    if type_expr.kind == "callable":
        return TypeExpr.callable_expr(
            parameters=[
                sanitize_annotation_type(type_expr=parameter)
                for parameter in type_expr.parameters
            ],
            return_type=sanitize_annotation_type(
                type_expr=type_expr.return_type or _OBJECT_TYPE,
            ),
        )
    return type_expr


def is_none_literal(node: expr) -> bool:
    """Check if node is a None literal.

    Args:
        node: The node examined while check if node is a None literal.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(node, Constant) and node.value is None


def parameter_compared_to_none(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> bool:
    """Return whether a parameter is compared against ``None`` in the body.

    A comparison such as ``name is None`` or ``name is not None`` is a strong,
    structural signal that the parameter is optional, so its inferred type
    should include ``None`` even when usage otherwise narrows it.


    Args:
        function: The function examined while return whether a parameter is
            compared against ``None`` in the body.
        name: Identifier of the name being resolved.

    Returns:
        Whether the requested condition holds.

    """
    child: AST
    for child in walk(node=function):
        if not isinstance(child, Compare):
            continue
        operands: list[expr] = [child.left, *child.comparators]
        names: set[str] = {
            operand.id for operand in operands if isinstance(operand, Name)
        }
        if name in names and any(
            is_none_literal(node=operand) for operand in operands
        ):
            return True
    return False


def parameter_isinstance_check_names(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> set[str]:
    """Return the type names a parameter is ``isinstance``-checked against.

    A call ``isinstance(name, T)`` (or ``isinstance(name, (A, B))``) is a
    structural signal that the parameter is expected to hold values of
    varied types, so being inferred as exactly one of those types would make
    the guard redundant.


    Args:
        function: The function examined while return the type names a parameter
            is ``isinstance``-checked against.
        name: Identifier of the name being resolved.

    Returns:
        set[str] produced by this operation.

    """
    checked: set[str] = set()
    child: AST
    for child in walk(node=function):
        if (
            not isinstance(child, Call)
            or not isinstance(child.func, Name)
            or child.func.id != "isinstance"
            or (len(child.args) != Constants.isinstance_arg_count)
        ):
            continue
        subject: expr = child.args[0]
        if not isinstance(subject, Name) or subject.id != name:
            continue
        checked.update(_type_names_in_expr(node=child.args[1]))
    return checked


def parameter_has_isinstance_fallback(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> bool:
    """Return True if the function body has a Return outside isinstance guards.

    A top-level ``Return`` that is not the body of an
    ``if isinstance(name, T)`` block signals that the author expects
    values of types beyond those checked, meaning the inferred union is
    too narrow.


    Args:
        function: The function examined while return True if the function body
            has a Return outside isinstance guards.
        name: Identifier of the name being resolved.

    Returns:
        Whether the requested condition holds.

    """
    for stmt_node in function.body:
        if isinstance(stmt_node, Return):
            return True
        if not isinstance(stmt_node, If):
            continue
        test: expr = stmt_node.test
        if (
            isinstance(test, Call)
            and isinstance(test.func, Name)
            and (test.func.id == "isinstance")
            and (len(test.args) == Constants.isinstance_arg_count)
            and isinstance(test.args[0], Name)
            and (test.args[0].id == name)
        ):
            continue
        return True
    return False


def _type_names_in_expr(*, node: expr) -> set[str]:
    """Return the identifier names used inside an isinstance type argument.

    Args:
        node: The node examined while return the identifier names used inside
            an isinstance type argument.

    Returns:
        set[str] produced by this operation.

    """
    if isinstance(node, Name):
        return {node.id}
    if isinstance(node, Tuple):
        names: set[str] = set()
        for element in node.elts:
            if isinstance(element, Name):
                names.add(element.id)
        return names
    return set()


def local_class_names(*, function: FunctionDef | AsyncFunctionDef) -> set[str]:
    """Find class names defined locally within a function.

    Args:
        function: The function examined while find class names defined locally
            within a function.

    Returns:
        set[str] produced by this operation.

    """
    names: set[str] = set()
    child: AST
    for child in walk(node=function):
        if isinstance(child, ClassDef):
            names.add(child.name)
    return names


def _positional_non_self_params(
    function: FunctionDef | AsyncFunctionDef,
) -> list[str]:
    """Return positional parameter names excluding the leading ``self``.

    Args:
        function: The function examined while return positional parameter names
            excluding the leading ``self``.

    Returns:
        list[str] produced by this operation.

    """
    positional: list[arg] = [*function.args.posonlyargs, *function.args.args]
    return [parameter.arg for parameter in positional[1:]]


def _infer_descriptor_signature(
    function: FunctionDef | AsyncFunctionDef,
) -> tuple[dict[str, TypeExpr], TypeExpr] | None:
    """Infer signatures for the descriptor protocol dunder methods.

    Any class that defines ``__get__``/``__set__``/``__set_name__``/
    ``__delete__`` is, by Python's data-model, a descriptor. The parameter
    roles are positional and universal, so they are seeded by position
    rather than by name (descriptors freely name them ``instance``/``obj``,
    ``owner``/``objtype``). ``__get__`` keeps its body-inferred return type;
    the optional ``owner``/``instance`` defaults and ``is None`` guards add
    ``| None`` through the ordinary parameter passes.


    Args:
        function: The function examined while infer signatures for the
            descriptor protocol dunder methods.

    Returns:
        tuple[dict[str, TypeExpr], TypeExpr] | None produced by this operation.

    """
    type_obj: TypeExpr = TypeExpr.generic("type", _OBJECT_TYPE)
    descriptor_params: dict[str, tuple[list[TypeExpr], TypeExpr]] = {
        "__get__": ([_OBJECT_TYPE, type_obj], _UNKNOWN_TYPE),
        "__set__": ([_OBJECT_TYPE, _OBJECT_TYPE], _NONE_TYPE),
        "__set_name__": ([type_obj, _STR_TYPE], _NONE_TYPE),
        "__delete__": ([_OBJECT_TYPE], _NONE_TYPE),
    }
    entry: tuple[list[TypeExpr], TypeExpr] | None = descriptor_params.get(
        function.name,
    )
    if entry is None:
        return None
    positional_types, return_type = entry
    names: list[str] = _positional_non_self_params(function=function)
    params: dict[str, TypeExpr] = {
        param_name: positional_types[index]
        for index, param_name in enumerate(iterable=names)
        if index < len(positional_types)
    }
    return (params, return_type)


def _infer_dunder_signature(
    function: FunctionDef | AsyncFunctionDef,
    class_name: str | None = None,
) -> tuple[dict[str, TypeExpr], TypeExpr] | None:
    """Infer signatures for dunder methods.

    Args:
        class_name: Identifier of the class being resolved.
        function: The function examined while infer signatures for dunder
            methods.

    Returns:
        tuple[dict[str, TypeExpr], TypeExpr] | None produced by this operation.

    """
    descriptor: tuple[dict[str, TypeExpr], TypeExpr] | None = (
        _infer_descriptor_signature(function=function)
    )
    if descriptor is not None:
        return descriptor
    if function.name == "__new__":
        if function.args.args and function.args.args[0].arg == "mcs":
            mcs_type: TypeExpr = TypeExpr.generic("type", _OBJECT_TYPE)
            return_type: TypeExpr = _OBJECT_TYPE
            if class_name is not None:
                class_type: TypeExpr = TypeExpr.name_expr(name=class_name)
                mcs_type = TypeExpr.generic("type", class_type)
                return_type = class_type
            return (
                {
                    "mcs": mcs_type,
                    "name": _STR_TYPE,
                    "bases": TypeExpr.generic(
                        "tuple",
                        TypeExpr.generic("type", _OBJECT_TYPE),
                        TypeExpr.ellipsis_expr(),
                    ),
                    "namespace": TypeExpr.generic(
                        "dict",
                        _STR_TYPE,
                        _OBJECT_TYPE,
                    ),
                    "_kwargs": _OBJECT_TYPE,
                },
                return_type,
            )
        return ({}, _OBJECT_TYPE)
    dunder_signatures: dict[str, tuple[dict[str, TypeExpr], TypeExpr]] = {
        "__eq__": ({"other": _OBJECT_TYPE}, _BOOL_TYPE),
        "__hash__": ({}, _INT_TYPE),
        "__repr__": ({}, _STR_TYPE),
        "__str__": ({}, _STR_TYPE),
        "__getattr__": ({"name": _STR_TYPE}, _OBJECT_TYPE),
    }
    return dunder_signatures.get(function.name)


def infer_special_function_signature(
    *,
    function: FunctionDef | AsyncFunctionDef,
    class_name: str | None = None,
) -> tuple[dict[str, TypeExpr], TypeExpr] | None:
    """Infer signatures for structural Python special methods (dunders).

    Only universal dunder protocols are seeded here. No fixture-specific
    function names are recognized; ordinary functions are inferred from
    their bodies and call sites.


    Args:
        class_name: Identifier of the class being resolved.
        function: The function examined while infer signatures for structural
            Python special methods (dunders).

    Returns:
        tuple[dict[str, TypeExpr], TypeExpr] | None produced by this operation.

    """
    return _infer_dunder_signature(function=function, class_name=class_name)


def drop_none_when_no_none_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    type_expr: TypeExpr,
) -> TypeExpr:
    """Remove None from union type if function has no explicit None return.

    Args:
        function: The function examined while remove None from union type if
            function has no explicit None return.
        type_expr: The type expr examined while remove None from union type if
            function has no explicit None return.

    Returns:
        TypeExpr produced by this operation.

    """
    has_explicit_none: bool = any(
        isinstance(node, Return)
        and (node.value is None or is_none_literal(node=node.value))
        for node in walk(node=function)
    )
    if has_explicit_none or type_expr.kind != "union":
        return type_expr
    remaining: list[TypeExpr] = [
        item for item in type_expr.args if item.key() != _NONE_TYPE.key()
    ]
    if not remaining:
        return _NONE_TYPE
    return TypeExpr.union(*remaining)


def _infer_return_value_type(
    *,
    value: expr,
    locals_: set[str],
    function: FunctionDef | AsyncFunctionDef,
) -> TypeExpr | None:
    """Infer type from a single return value.

    Args:
        function: The function examined while infer type from a single return
            value.
        locals_: Locals supplied as set[str] for this operation.
        value: The value examined while infer type from a single return value.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if isinstance(value, Name):
        for stmt in walk(node=function):
            if (
                isinstance(stmt, ClassDef)
                and stmt.name == value.id
                and stmt.decorator_list
            ):
                return _OBJECT_TYPE
        if value.id in locals_:
            return TypeExpr.generic("type", _OBJECT_TYPE)
    if isinstance(value, Tuple):
        return _infer_tuple_return_type(value=value, locals_=locals_)
    if (
        isinstance(value, Call)
        and isinstance(value.func, Name)
        and (value.func.id in locals_)
    ):
        return _OBJECT_TYPE
    return None


def _infer_tuple_return_type(
    *,
    value: Tuple,
    locals_: set[str],
) -> TypeExpr | None:
    """Infer type from a tuple return value.

    Args:
        locals_: Locals supplied as set[str] for this operation.
        value: The value examined while infer type from a tuple return value.

    Returns:
        TypeExpr | None produced by this operation.

    """
    items: list[TypeExpr] = []
    element: expr
    for element in value.elts:
        if isinstance(element, Name) and element.id in locals_:
            items.append(TypeExpr.generic("type", _OBJECT_TYPE))
        elif (
            isinstance(element, Call)
            and isinstance(element.func, Name)
            and (element.func.id in locals_)
        ):
            items.append(_OBJECT_TYPE)
    if len(items) == len(value.elts):
        return TypeExpr.generic("tuple", *items)
    return None


def infer_special_return_type(
    *,
    function: FunctionDef | AsyncFunctionDef,
) -> TypeExpr | None:
    """Infer return type for functions returning local class instances.

    Args:
        function: The function examined while infer return type for functions
            returning local class instances.

    Returns:
        TypeExpr | None produced by this operation.

    """
    locals_: set[str] = local_class_names(function=function)
    inferred: list[TypeExpr] = []
    child: AST
    for child in walk(node=function):
        if not isinstance(child, Return) or child.value is None:
            continue
        return_type: TypeExpr | None = _infer_return_value_type(
            value=child.value,
            locals_=locals_,
            function=function,
        )
        if return_type is not None:
            inferred.append(return_type)
    if not inferred:
        return None
    return merge_many(types=inferred)


def infer_vararg_item_type(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> TypeExpr:
    """Infer item type for *args parameter from usage.

    Args:
        function: The function examined while infer item type for *args
            parameter from usage.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr produced by this operation.

    """
    observations: list[TypeExpr] = []
    node: AST
    for node in walk(node=function):
        if (
            isinstance(node, Call)
            and expr_name(node=node.func) == "sum"
            and any(
                isinstance(item, Name) and item.id == name
                for item in node.args
            )
        ):
            observations.append(_INT_TYPE)
        if (
            isinstance(node, For)
            and isinstance(node.iter, Name)
            and (node.iter.id == name)
        ):
            target_names: set[str] = {
                child.id
                for child in walk(node=node.target)
                if isinstance(child, Name)
            }
            if any(
                (
                    isinstance(child, BinOp)
                    or child.__class__.__name__ == "AugAssign"
                )
                and contains_name(node=child, name=target_name)
                for target_name in target_names
                for child in walk(node=node)
            ):
                observations.append(_INT_TYPE)
    return merge_many(types=observations) if observations else _OBJECT_TYPE


def infer_kwarg_value_type(
    *,
    function: FunctionDef | AsyncFunctionDef,
    name: str,
) -> TypeExpr:
    """Infer value type for **kwargs parameter from usage.

    Args:
        function: The function examined while infer value type for **kwargs
            parameter from usage.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr produced by this operation.

    """
    observations: list[TypeExpr] = [
        _INT_TYPE
        for node in walk(node=function)
        if isinstance(node, Call)
        and expr_name(node=node.func) == (f"{name}.values")
    ]
    return merge_many(types=observations) if observations else _OBJECT_TYPE


def all_args(node: FunctionDef | AsyncFunctionDef) -> tuple[arg, ...]:
    """Get all arguments including vararg and kwarg.

    Args:
        node: The node examined while get all arguments including vararg and
            kwarg.

    Returns:
        tuple[arg, ...] produced by this operation.

    """
    args: list[arg] = []
    args.extend(node.args.posonlyargs)
    args.extend(node.args.args)
    if node.args.vararg is not None:
        args.append(node.args.vararg)
    args.extend(node.args.kwonlyargs)
    if node.args.kwarg is not None:
        args.append(node.args.kwarg)
    return tuple(args)


def defaults_by_arg(node: FunctionDef | AsyncFunctionDef) -> dict[str, expr]:
    """Map argument names to their default values.

    Args:
        node: The node examined while map argument names to their default
            values.

    Returns:
        dict[str, expr] produced by this operation.

    """
    result: dict[str, expr] = {}
    positional: list[arg] = [*node.args.posonlyargs, *node.args.args]
    defaults: list[expr] = list(node.args.defaults)
    if defaults:
        for parameter, default in zip(
            positional[-len(defaults) :],
            defaults,
            strict=True,
        ):
            result[parameter.arg] = default
    for parameter, default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
        strict=True,
    ):
        if default is not None:
            result[parameter.arg] = default
    return result


def has_value_return(function: FunctionDef | AsyncFunctionDef) -> bool:
    """Check if function has any non-None return statements.

    Args:
        function: The function examined while check if function has any
            non-None return statements.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        isinstance(node, Return) and node.value is not None
        for node in walk(node=function)
    )


def has_yield(function: FunctionDef | AsyncFunctionDef) -> bool:
    """Check if function is a generator (has yield).

    Args:
        function: The function examined while check if function is a generator
            (has yield).

    Returns:
        Whether the requested condition holds.

    """
    return any(
        node.__class__.__name__ in {"Yield", "YieldFrom"}
        for node in walk(node=function)
    )


def expr_name(node: AST) -> str:
    """Extract qualified name from expression node.

    Args:
        node: The node examined while extract qualified name from expression
            node.

    Returns:
        str produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        parent: str = expr_name(node=node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, Call):
        return expr_name(node=node.func)
    return ""


def contains_name(node: AST, name: str) -> bool:
    """Check if AST node contains a Name with given identifier.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while check if AST node contains a Name with
            given identifier.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        isinstance(child, Name) and child.id == name
        for child in walk(node=node)
    )


def is_self_attr(node: AST) -> bool:
    """Check if node is an attribute access on self/cls.

    Args:
        node: The node examined while check if node is an attribute access on
            self/cls.

    Returns:
        Whether the requested condition holds.

    """
    return (
        isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and (node.value.id in Constants.self_names)
    )


def is_dataclass_class(*, node: ClassDef) -> bool:
    """Return whether a class has a dataclass decorator.

    Args:
        node: The node examined while return whether a class has a dataclass
            decorator.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        expr_name(node=decorator).endswith("dataclass")
        for decorator in node.decorator_list
    )


def is_plain_result_class(node: ClassDef) -> bool:
    """Check if class is a plain Result-like data class.

    Args:
        node: The node examined while check if class is a plain Result-like
            data class.

    Returns:
        Whether the requested condition holds.

    """
    if node.decorator_list:
        return False
    methods: list[FunctionDef] = [
        item for item in node.body if isinstance(item, FunctionDef)
    ]
    if len(methods) != 1 or methods[0].name != "__init__":
        return False
    return all(
        is_init_assignment(statement=statement)
        for statement in methods[0].body
        if not is_docstring_stmt(statement=statement)
    )


def is_docstring_stmt(statement: stmt) -> bool:
    """Check if statement is a docstring.

    Args:
        statement: The statement examined while check if statement is a
            docstring.

    Returns:
        Whether the requested condition holds.

    """
    return (
        isinstance(statement, Expr)
        and isinstance(statement.value, Constant)
        and isinstance(statement.value.value, str)
    )


def is_init_assignment(statement: stmt) -> bool:
    """Check if statement is a self.attr assignment in __init__.

    Args:
        statement: The statement examined while check if statement is a
            self.attr assignment in __init__.

    Returns:
        Whether the requested condition holds.

    """
    if not isinstance(statement, Assign) or len(statement.targets) != 1:
        return False
    target: expr = statement.targets[0]
    return is_self_attr(node=target)


def namedtuple_fields(node: ClassDef) -> list[tuple[str, TypeExpr]]:
    """Extract namedtuple field names and types from class.

    Args:
        node: The node examined while extract namedtuple field names and types
            from class.

    Returns:
        list[tuple[str, TypeExpr]] produced by this operation.

    """
    for item in node.body:
        if isinstance(item, FunctionDef) and item.name == "__init__":
            params: list[arg] = [
                param for param in item.args.args if param.arg != "self"
            ]
            return [
                (
                    param.arg,
                    infer_param_from_usage(function=item, name=param.arg),
                )
                for param in params
            ]
    return []


def infer_class_assignment(statement: Assign) -> tuple[str, TypeExpr] | None:
    """Infer class-level assignment name and type.

    Args:
        statement: The statement examined while infer class-level assignment
            name and type.

    Returns:
        tuple[str, TypeExpr] | None produced by this operation.

    """
    if len(statement.targets) != 1 or not isinstance(
        statement.targets[0],
        Name,
    ):
        return None
    return (statement.targets[0].id, infer_literal_expr(node=statement.value))


def infer_literal_expr(node: expr) -> TypeExpr:
    """Infer type from literal expression.

    Args:
        node: The node examined while infer type from literal expression.

    Returns:
        TypeExpr produced by this operation.

    """
    if isinstance(node, Constant):
        return infer_constant(value=node.value)
    if isinstance(node, List):
        return TypeExpr.generic("list", _OBJECT_TYPE)
    return _OBJECT_TYPE


def _infer_callable_type(
    *,
    annotation: Subscript,
    name: str,
) -> TypeExpr | None:
    """Infer Callable type from annotation.

    Args:
        annotation: The annotation examined while infer Callable type from
            annotation.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr | None produced by this operation.

    """
    if (
        name != "Callable"
        or not isinstance(annotation.slice, Tuple)
        or len(annotation.slice.elts) != Constants.min_type_args
    ):
        return None
    params_node: expr = annotation.slice.elts[0]
    return_node: expr = annotation.slice.elts[1]
    if isinstance(params_node, List):
        params: list[TypeExpr] = [
            type_expr_from_annotation(annotation=item)
            for item in params_node.elts
        ]
    elif isinstance(params_node, Constant) and params_node.value is Ellipsis:
        params = [TypeExpr.ellipsis_expr()]
    else:
        params = [_OBJECT_TYPE]
    return TypeExpr.callable_expr(
        parameters=params,
        return_type=type_expr_from_annotation(annotation=return_node),
    )


def _infer_subscript_type(*, annotation: Subscript, name: str) -> TypeExpr:
    """Infer generic type from subscript annotation.

    Args:
        annotation: The annotation examined while infer generic type from
            subscript annotation.
        name: Identifier of the name being resolved.

    Returns:
        TypeExpr produced by this operation.

    """
    if isinstance(annotation.slice, Tuple):
        return TypeExpr.generic(
            name,
            *[
                type_expr_from_annotation(annotation=item)
                for item in annotation.slice.elts
            ],
        )
    return TypeExpr.generic(
        name,
        type_expr_from_annotation(annotation=annotation.slice),
    )


def type_expr_from_annotation(annotation: expr) -> TypeExpr:
    """Convert annotation AST node to TypeExpr.

    Args:
        annotation: The annotation examined while convert annotation AST node
            to TypeExpr.

    Returns:
        TypeExpr produced by this operation.

    """
    if isinstance(annotation, Name):
        return TypeExpr.name_expr(name=annotation.id)
    if isinstance(annotation, Constant) and annotation.value is Ellipsis:
        return TypeExpr.ellipsis_expr()
    if isinstance(annotation, BinOp) and isinstance(annotation.op, BitOr):
        return TypeExpr.union(
            type_expr_from_annotation(annotation=annotation.left),
            type_expr_from_annotation(annotation=annotation.right),
        )
    if isinstance(annotation, Subscript):
        name: str = expr_name(node=annotation.value)
        callable_type: TypeExpr | None = _infer_callable_type(
            annotation=annotation,
            name=name,
        )
        if callable_type is not None:
            return callable_type
        return _infer_subscript_type(annotation=annotation, name=name)
    return _OBJECT_TYPE


def should_annotate_name(name: str) -> bool:
    """Check if a name should be annotated (not private or constant).

    Args:
        name: Identifier of the name being resolved.

    Returns:
        Whether the requested condition holds.

    """
    return not name.startswith("_") or name.isupper()


def collect_imports(type_expr: TypeExpr, imports: set[str]) -> None:
    """Collect typing/collections.abc names from type expression.

    Args:
        imports: Imports supplied as set[str] for this operation.
        type_expr: The type expr examined while collect typing/collections.abc
            names from type expression.

    """
    if (
        type_expr.name
        in typing_import_names() | collections_abc_import_names()
    ):
        imports.add(type_expr.name)
    for arg_expr in type_expr.args:
        collect_imports(type_expr=arg_expr, imports=imports)
    for parameter in type_expr.parameters:
        collect_imports(type_expr=parameter, imports=imports)
    if type_expr.return_type is not None:
        collect_imports(type_expr=type_expr.return_type, imports=imports)


def typing_import_names() -> set[str]:
    """Return names from typing module that may need imports.

    Returns:
        set[str] produced by this operation.

    """
    return {
        "Final",
        "NamedTuple",
        "ParamSpec",
        "Protocol",
        "Self",
        "TypeVar",
        "cast",
        "override",
    }


def collections_abc_import_names() -> set[str]:
    """Return the set of commonly used collections.abc import names.

    Returns:
        set[str] produced by this operation.

    """
    return {
        "Awaitable",
        "Callable",
        "Generator",
        "Iterable",
        "Iterator",
        "Mapping",
        "Sequence",
    }


def call_parameter_names(
    name: str,
    engine: InferenceEngine,
) -> list[str] | None:
    """Get parameter names for a callable by name.

    Args:
        engine: Engine supplied as InferenceEngine for this operation.
        name: Identifier of the name being resolved.

    Returns:
        list[str] | None produced by this operation.

    """
    info: FunctionInfo | None = engine.resolve_callable(name=name)
    if info is None and name in engine.index.classes:
        class_info: ClassInfo = engine.index.classes[name]
        info = class_info.methods.get("__init__")
    if info is None:
        return None
    if info.node.args.vararg is not None:
        return None
    names: list[str] = [
        ""
        for param in info.node.args.posonlyargs
        if param.arg != info.implicit_parameter_name()
    ]
    names.extend(
        param.arg
        for param in info.node.args.args
        if param.arg != info.implicit_parameter_name()
    )
    return names


def builtin_keyword_parameters(name: str, arg_count: int) -> list[str] | None:
    """Get known keyword parameter names for builtin functions.

    Args:
        arg_count: Arg count supplied as int for this operation.
        name: Identifier of the name being resolved.

    Returns:
        list[str] | None produced by this operation.

    """
    known: dict[str, list[str]] = {
        "wraps": ["wrapped"],
        "asyncio.sleep": ["delay"],
        "tempfile.NamedTemporaryFile": ["mode"],
        "compress": ["data", "selectors"],
        "importlib.import_module": ["name"],
        "__import__": ["name"],
    }
    params: list[str] | None = known.get(name)
    if params is None:
        return None
    return params[:arg_count]


def has_decorator(function: FunctionDef | AsyncFunctionDef, name: str) -> bool:
    """Check if a function has a specific decorator.

    Args:
        function: The function examined while check if a function has a
            specific decorator.
        name: Identifier of the name being resolved.

    Returns:
        Whether the requested condition holds.

    """
    return any(
        expr_name(node=decorator) == name
        for decorator in function.decorator_list
    )


def method_kind_from_decorators(
    *,
    function: FunctionDef | AsyncFunctionDef,
) -> MethodKind:
    """Infer method binding from descriptors instead of parameter names.

    Args:
        function: The function examined while infer method binding from
            descriptors instead of parameter names.

    Returns:
        MethodKind produced by this operation.

    """
    decorator_names: set[str] = {
        expr_name(node=decorator) for decorator in function.decorator_list
    }
    if decorator_names & {"staticmethod", "abc.abstractstaticmethod"}:
        return "static"
    if decorator_names & {"classmethod", "abc.abstractclassmethod"}:
        return "class"
    if decorator_names & {
        "property",
        "functools.cached_property",
        "cached_property",
    }:
        return "property"
    for decorator in function.decorator_list:
        if (
            isinstance(decorator, Attribute)
            and decorator.attr == "setter"
            and isinstance(decorator.value, Name)
        ):
            return "property"
    return "instance"


def _validate_descriptor_assignment(
    *,
    statement: Assign,
    class_info: ClassInfo,
) -> tuple[FunctionInfo, str] | None:
    """Validate descriptor assignment and return method and descriptor name.

    Args:
        class_info: The class info examined while validate descriptor
            assignment and return method and descriptor name.
        statement: The statement examined while validate descriptor assignment
            and return method and descriptor name.

    Returns:
        tuple[FunctionInfo, str] | None produced by this operation.

    """
    if (
        len(statement.targets) != 1
        or not isinstance(statement.targets[0], Name)
        or (not isinstance(statement.value, Call))
        or (not isinstance(statement.value.func, Name))
        or (len(statement.value.args) != 1)
        or (not isinstance(statement.value.args[0], Name))
    ):
        return None
    target: Name = statement.targets[0]
    argument: Name = statement.value.args[0]
    if argument.id != target.id:
        return None
    method: FunctionInfo | None = class_info.methods.get(target.id)
    if method is None:
        return None
    return (method, statement.value.func.id)


def update_method_kind_from_descriptor_assignment(
    *,
    statement: Assign,
    class_info: ClassInfo,
) -> None:
    """Handle ``name = classmethod(name)`` and related class-body forms.

    Args:
        class_info: The class info examined while handle ``name =
            classmethod(name)`` and related class-body forms.
        statement: The statement examined while handle ``name =
            classmethod(name)`` and related class-body forms.

    """
    result: tuple[FunctionInfo, str] | None = _validate_descriptor_assignment(
        statement=statement,
        class_info=class_info,
    )
    if result is None:
        return
    method, descriptor_name = result
    if descriptor_name == "classmethod":
        method.method_kind = "class"
    elif descriptor_name == "staticmethod":
        method.method_kind = "static"
    elif descriptor_name == "property":
        method.method_kind = "property"


def is_override(
    function: FunctionDef | AsyncFunctionDef,
    class_info: ClassInfo,
    classes: Mapping[str, ClassInfo],
) -> bool:
    """Check if a function is an override of a base class method.

    Args:
        class_info: The class info examined while check if a function is an
            override of a base class method.
        classes: Classes supplied as Mapping[str, ClassInfo] for this
            operation.
        function: The function examined while check if a function is an
            override of a base class method.

    Returns:
        Whether the requested condition holds.

    """
    object_methods: set[str] = {
        "__call__",
        "__eq__",
        "__hash__",
        "__repr__",
        "__str__",
    }
    if not class_info.bases and function.name in object_methods:
        return True
    builtin_methods: dict[str, set[str]] = {
        "type": {"__call__", "__new__"},
        "list": {"append", "count", "extend", "pop"},
        "dict": {"get", "items", "keys", "update", "values"},
        "set": {"add", "discard", "update"},
    }
    for base in class_info.bases:
        base_info: ClassInfo | None = classes.get(base)
        if base_info is not None and function.name in base_info.methods:
            return True
        if function.name in builtin_methods.get(base, set()):
            return True
        if base not in {"Protocol", "ABC"} and function.name in object_methods:
            return True
    return False


def annotation_is_none(*, annotation: expr) -> bool:
    """Return whether an annotation represents ``None``.

    Args:
        annotation: The annotation examined while return whether an annotation
            represents ``None``.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(annotation, Name) and annotation.id == Constants.none


def has_ellipsis_body(function: FunctionDef) -> bool:
    """Check if a function has only an ellipsis body.

    Args:
        function: The function examined while check if a function has only an
            ellipsis body.

    Returns:
        Whether the requested condition holds.

    """
    return (
        len(function.body) == 1
        and isinstance(function.body[0], Expr)
        and isinstance(function.body[0].value, Constant)
        and (function.body[0].value.value is Ellipsis)
    )


def ensure_from_import(
    body: list[stmt],
    module: str,
    names: Sequence[str],
) -> list[stmt]:
    """Ensure specific names are imported from a module.

    Args:
        body: Body supplied as list[stmt] for this operation.
        module: The module examined while ensure specific names are imported
            from a module.
        names: Names supplied as Sequence[str] for this operation.

    Returns:
        list[stmt] produced by this operation.

    """
    required: set[str] = set(names)
    if not required:
        return body
    for statement in body:
        if isinstance(statement, ImportFrom) and statement.module == module:
            existing: set[str] = {item.name for item in statement.names}
            missing: list[str] = sorted(required - existing)
            if missing:
                statement.names.extend([alias(name=name) for name in missing])
                statement.names.sort(key=lambda item: item.name)
            return body
    insert_index: int = import_insert_index(body=body)
    body.insert(
        insert_index,
        ImportFrom(
            module=module,
            names=[alias(name=name) for name in sorted(required)],
            level=0,
        ),
    )
    return body


def import_insert_index(body: Sequence[stmt]) -> int:
    """Find the index where imports should be inserted.

    Args:
        body: Body supplied as Sequence[stmt] for this operation.

    Returns:
        int produced by this operation.

    """
    index: int = 0
    if body and is_docstring_stmt(statement=body[0]):
        index = 1
    while index < len(body):
        statement: stmt = body[index]
        if (
            isinstance(statement, ImportFrom)
            and statement.module == "__future__"
        ):
            index += 1
            continue
        if isinstance(statement, (Import, ImportFrom)):
            index += 1
            continue
        break
    return index


def _collect_annotations_from_annassign(node: AnnAssign) -> list[expr]:
    """Collect annotations from AnnAssign node.

    Args:
        node: The node examined while collect annotations from AnnAssign node.

    Returns:
        list[expr] produced by this operation.

    """
    return [node.annotation]


def _collect_annotations_from_function(
    node: FunctionDef | AsyncFunctionDef,
) -> list[expr]:
    """Collect annotations from function node.

    Args:
        node: The node examined while collect annotations from function node.

    Returns:
        list[expr] produced by this operation.

    """
    annotations: list[expr] = (
        [node.returns] if node.returns is not None else []
    )
    annotations.extend(
        parameter.annotation
        for parameter in all_args(node=node)
        if parameter.annotation is not None
    )
    return annotations


def _collect_annotations_from_classdef(node: ClassDef) -> list[expr]:
    """Collect annotations from ClassDef node.

    Args:
        node: The node examined while collect annotations from ClassDef node.

    Returns:
        list[expr] produced by this operation.

    """
    return list(node.bases)


def _collect_names_from_annotation(
    *,
    annotation: expr,
    names: set[str],
) -> None:
    """Extract names from a single annotation.

    Args:
        annotation: The annotation examined while extract names from a single
            annotation.
        names: Names supplied as set[str] for this operation.

    """
    child: AST
    for child in walk(node=annotation):
        if isinstance(child, Name):
            names.add(child.id)


def annotation_name_set(*, body: list[stmt]) -> set[str]:
    """Extract all names used in type annotations from a module body.

    Args:
        body: Body supplied as list[stmt] for this operation.

    Returns:
        set[str] produced by this operation.

    """
    names: set[str] = set()
    module: Module = Module(body=body, type_ignores=[])
    node: AST
    for node in walk(node=module):
        annotations: list[expr] = []
        if isinstance(node, AnnAssign):
            annotations = _collect_annotations_from_annassign(node=node)
        elif isinstance(node, (FunctionDef, AsyncFunctionDef)):
            annotations = _collect_annotations_from_function(node=node)
        elif isinstance(node, ClassDef):
            annotations = _collect_annotations_from_classdef(node=node)
        annotation: expr
        for annotation in annotations:
            _collect_names_from_annotation(annotation=annotation, names=names)
    return names


def runtime_name_set(*, body: list[stmt]) -> set[str]:
    """Extract all runtime names from a module body.

    Args:
        body: Body supplied as list[stmt] for this operation.

    Returns:
        set[str] produced by this operation.

    """
    names: set[str] = set()
    module: Module = Module(body=body, type_ignores=[])
    node: AST
    for node in walk(node=module):
        if isinstance(node, Name) and isinstance(node.ctx, Load):
            names.add(node.id)
    return names


def normalize_imports(*, body: list[stmt], used_names: set[str]) -> list[stmt]:
    """Normalize imports by removing unused names from specific modules.

    Args:
        body: Body supplied as list[stmt] for this operation.
        used_names: Used names supplied as set[str] for this operation.

    Returns:
        list[stmt] produced by this operation.

    """
    normalized: list[stmt] = []
    statement: stmt
    for statement in body:
        if isinstance(statement, ImportFrom) and statement.module in {
            "typing",
            "collections.abc",
            "weakref",
            "dataclasses",
        }:
            kept: list[alias] = []
            item: alias
            for item in statement.names:
                import_name: str = item.asname or item.name
                if import_name in used_names:
                    kept.append(item)
            if kept:
                statement.names = sorted(kept, key=lambda item: item.name)
                normalized.append(statement)
            continue
        normalized.append(statement)
    return normalized


def copy_basic_location(new_node: AST, old_node: AST) -> AST:
    """Copy basic location attributes from one AST node to another.

    Args:
        new_node: New node supplied as AST for this operation.
        old_node: Old node supplied as AST for this operation.

    Returns:
        AST produced by this operation.

    """
    for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
        if hasattr(old_node, attr):
            setattr(new_node, attr, getattr(old_node, attr))
    return new_node


@dataclass(frozen=True, slots=True)
class ConversionReport:
    """Report of source code conversion with metadata.

    Attributes:
        basedpyright_summary: Basedpyright summary retained as str by this
            instance.
        benchmark_sha256: Benchmark sha256 retained as str by this instance.
        converted_sha256: Converted sha256 retained as str by this instance.
        diff_preview: Diff preview retained as str by this instance.
        exact_match: Exact match retained as bool by this instance.
        ruff_summary: Ruff summary retained as str by this instance.
        source_sha256: Source sha256 retained as str by this instance.

    """

    source_sha256: str
    converted_sha256: str
    benchmark_sha256: str
    exact_match: bool
    diff_preview: str
    ruff_summary: str
    basedpyright_summary: str

    def to_text(self) -> str:
        """Convert the report to a formatted text string.

        Returns:
            str produced by this operation.

        """
        return (
            """\

""".join(
                [
                    "mode: graph_only_agnostic_inference_v15",
                    (f"source_sha256: {self.source_sha256}"),
                    (f"converted_sha256: {self.converted_sha256}"),
                    (f"benchmark_sha256: {self.benchmark_sha256}"),
                    (f"exact_match: {self.exact_match}"),
                    "ruff_summary:",
                    self.ruff_summary,
                    "basedpyright_summary:",
                    self.basedpyright_summary,
                    "diff_preview:",
                    self.diff_preview,
                ],
            )
            + """\

"""
        )


def custom_unparse(node: AST) -> str:
    """Unparse AST node, handling Parenthesized nodes.

    Wraps them in parentheses.


    Args:
        node: The node examined while unparse AST node, handling Parenthesized
            nodes.

    Returns:
        str produced by this operation.

    """
    return Constants.parenthesized_renderer.render(node=node)


def convert_source(source: str) -> str:
    """Convert untyped source to typed using graph inference.

    Args:
        source: The source examined while convert untyped source to typed using
            graph inference.

    Returns:
        Rendered source text produced by this operation.

    """
    module: Module = parse(source=source, filename="<graph-only>", mode="exec")
    index: GraphIndexer = GraphIndexer()
    index.visit(node=module)
    engine: InferenceEngine = InferenceEngine(
        module=module,
        index=index,
        source=source,
    )
    engine.run()
    transformer: StrictAstTransformer = StrictAstTransformer(engine=engine)
    converted: Module = cast(typ="Module", val=transformer.visit(node=module))
    fix_missing_locations(node=converted)
    return (
        custom_unparse(node=converted)
        + """\

"""
    )


def sha256_text(text: str) -> str:
    """Compute SHA256 hash of a text string.

    Args:
        text: Text supplied as str for this operation.

    Returns:
        str produced by this operation.

    """
    return sha256(data=text.encode(encoding="utf-8")).hexdigest()


def write_conversion(
    source_path: Path,
    output_path: Path,
    report_path: Path,
    benchmark_path: Path | None = None,
) -> None:
    """Convert source code and write output with a conversion report.

    Args:
        benchmark_path: Filesystem path identifying the benchmark.
        output_path: Filesystem path identifying the output.
        report_path: Filesystem path identifying the report.
        source_path: Filesystem path identifying the source.

    """
    source: str = source_path.read_text(encoding="utf-8")
    converted: str = convert_source(source=source)
    output_path.write_text(data=converted, encoding="utf-8")
    benchmark: str = (
        benchmark_path.read_text(encoding="utf-8")
        if benchmark_path is not None and benchmark_path.exists()
        else ""
    )
    diff: str = "".join(
        unified_diff(
            a=benchmark.splitlines(keepends=True),
            b=converted.splitlines(keepends=True),
            fromfile="benchmark.py",
            tofile="converted.py",
            n=3,
        ),
    )[:12000]
    report: ConversionReport = ConversionReport(
        source_sha256=sha256_text(text=source),
        converted_sha256=sha256_text(text=converted),
        benchmark_sha256=sha256_text(text=benchmark) if benchmark else "",
        exact_match=bool(benchmark) and benchmark == converted,
        diff_preview=diff,
        ruff_summary="run ruff externally",
        basedpyright_summary="run basedpyright externally",
    )
    report_path.write_text(data=report.to_text(), encoding="utf-8")


if __name__ == "__main__":
    base: Path = Path("/mnt/data")
    write_conversion(
        source_path=base / "test_resolver_inference_merged_untyped(4).py",
        output_path=base / "graph_only_converted_v15.py",
        report_path=base / "graph_only_v15_intermediate_report.txt",
        benchmark_path=base / "test_resolver_inference_merged_typed(4).py",
    )
    aprint(
        (base / "graph_only_v15_intermediate_report.txt").read_text(
            encoding="utf-8",
        ),
    )
