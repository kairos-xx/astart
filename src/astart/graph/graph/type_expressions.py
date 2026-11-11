"""Structured type-expression data model, parser, and renderer."""

from __future__ import annotations

from ast import AST, Attribute, BinOp, BitOr, Constant, Name, Subscript, expr
from ast import List as AstList
from ast import Tuple as AstTuple
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal, final

from astart.graph.graph.semantics import build_annotation

type Variance = Literal["invariant", "covariant", "contravariant"]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        none_name (Final[str]): Grouped module constant.
        callable_names (Final[frozenset[str]]): Grouped module constant.
        callable_arg_count (Final[int]): Grouped module constant.

    """

    none_name: Final[str] = "None"
    callable_names: Final[frozenset[str]] = frozenset(
        {"Callable", "typing.Callable"},
    )
    callable_arg_count: Final[int] = 2


class TypeExpressionError(ValueError):
    """Raised when a type expression cannot be parsed."""


class RequiredImport(StrEnum):
    """Imports commonly needed by generated type expressions.

    Attributes:
        CALLABLE: Callable associated with this instance.
        PARAM_SPEC: Param spec associated with this instance.
        PROTOCOL: Protocol associated with this instance.
        TYPE_VAR: Type var associated with this instance.

    """

    CALLABLE = "Callable"
    PARAM_SPEC = "ParamSpec"
    PROTOCOL = "Protocol"
    TYPE_VAR = "TypeVar"


@dataclass(frozen=True, slots=True)
class TypeName:
    """A named type expression such as ``int`` or ``Path``.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str


@dataclass(frozen=True, slots=True)
class TypeVarExpression:
    """A synthesized TypeVar-like expression.

    Attributes:
        bound (TypeExpression | None): Bound retained as TypeExpression | None
            by this instance.
        name (str): Identifier used to refer to the name.
        variance (Variance): Variance retained as Variance by this instance.

    """

    name: str
    bound: TypeExpression | None = None
    variance: Variance = "invariant"


@dataclass(frozen=True, slots=True)
class ParamSpecExpression:
    """A synthesized ParamSpec-like expression.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str


@dataclass(frozen=True, slots=True)
class EllipsisExpression:
    """A type-expression ellipsis for callable argument lists."""


@dataclass(frozen=True, slots=True)
class UnionExpression:
    """A normalized union expression.

    Attributes:
        members (tuple[TypeExpression, ...]): Members retained as
            tuple[TypeExpression, ...] by this instance.

    """

    members: tuple[TypeExpression, ...]


@dataclass(frozen=True, slots=True)
class GenericExpression:
    """A parametrized type expression such as ``list[int]``.

    Attributes:
        arguments (tuple[TypeExpression, ...]): Arguments retained as
            tuple[TypeExpression, ...] by this instance.
        base (TypeExpression): Base retained as TypeExpression by this
            instance.

    """

    base: TypeExpression
    arguments: tuple[TypeExpression, ...]


@dataclass(frozen=True, slots=True)
class CallableExpression:
    """A callable type expression.

    Attributes:
        parameters (tuple[TypeExpression,...]|EllipsisExpression): Parameters
            retained as tuple[TypeExpression,
            ...] | EllipsisExpression by this instance.
        returns (TypeExpression): Returns retained as TypeExpression by this
            instance.

    """

    parameters: tuple[TypeExpression, ...] | EllipsisExpression
    returns: TypeExpression


type TypeExpression = (
    TypeName
    | TypeVarExpression
    | ParamSpecExpression
    | EllipsisExpression
    | UnionExpression
    | GenericExpression
    | CallableExpression
)


class TypeExpressionCodec:
    """Convert structured type expressions to and from Python syntax."""

    @classmethod
    def union(cls, *, members: tuple[TypeExpression, ...]) -> TypeExpression:
        """Create a flattened, deduplicated, normalized union expression.

        Args:
            members (tuple[TypeExpression, ...]): Members supplied as
                tuple[TypeExpression,
                ...] for this operation.

        Returns:
            TypeExpression: TypeExpression produced by this operation.

        """
        flattened: list[TypeExpression] = []
        member: TypeExpression
        for member in members:
            match member:
                case UnionExpression(members=inner_members):
                    flattened.extend(inner_members)
                case _:
                    flattened.append(member)
        unique: dict[str, TypeExpression] = {}
        for member in flattened:
            unique[cls.to_source(type_expression=member)] = member
        if len(unique) == 1:
            return next(iter(unique.values()))
        ordered: tuple[TypeExpression, ...] = tuple(
            (
                value
                for _, value in sorted(
                    unique.items(),
                    key=lambda item: _union_sort_key(name=item[0]),
                )
            ),
        )
        return UnionExpression(members=ordered)

    @classmethod
    def from_name(cls, *, name: str) -> TypeExpression:
        """Parse a type expression, falling back to a simple name.

        Args:
            name (str): Identifier of the name being resolved.

        Returns:
            TypeExpression: TypeExpression produced by this operation.

        """
        return cls.from_source(source=name.strip())

    @classmethod
    def from_source(cls, *, source: str) -> TypeExpression:
        """Parse a Python type-expression string into the data model.

        Args:
            source (str): The source examined while parse a Python
                type-expression string into the data model.

        Returns:
            TypeExpression: TypeExpression produced by this operation.

        Raises:
            TypeExpressionError: If this operation cannot satisfy its
                documented contract.

        """
        if source == "...":
            return EllipsisExpression()
        try:
            parsed: expr = build_annotation(text=source)
        except ValueError as error:
            msg: str = f"invalid type expression: {source!r}"
            raise TypeExpressionError(msg) from error
        return cls.from_ast(node=parsed)

    @classmethod
    def from_ast(cls, *, node: expr) -> TypeExpression:
        """Convert an annotation AST expression into the data model.

        Args:
            node (expr): The node examined while convert an annotation
                AST expression into the data model.

        Returns:
            TypeExpression: TypeExpression produced by this operation.

        Raises:
            TypeExpressionError: If this operation cannot satisfy its
                documented contract.

        """
        result: TypeExpression | None = _atomic_type_expression(node=node)
        if result is None and isinstance(node, AstList):
            result = GenericExpression(
                base=TypeName(name="list"),
                arguments=tuple(cls.from_ast(node=item) for item in node.elts),
            )
        elif result is None and isinstance(node, BinOp):
            result = cls._from_binary_type_expression(node=node)
        elif result is None and isinstance(node, Subscript):
            result = cls._from_subscript(node=node)
        if result is None:
            msg: str = (
                f"unsupported type expression AST: {type(node).__name__}"
            )
            raise TypeExpressionError(msg)
        return result

    @classmethod
    def to_source(cls, *, type_expression: TypeExpression) -> str:
        """Render a type expression as Python source.

        Args:
            type_expression (TypeExpression): Type expression supplied as
                TypeExpression for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        result: str
        match type_expression:
            case (
                TypeName(name=name)
                | TypeVarExpression(name=name)
                | ParamSpecExpression(name=name)
            ):
                result = name
            case EllipsisExpression():
                result = "..."
            case UnionExpression():
                result = cls._union_to_source(type_expression=type_expression)
            case GenericExpression():
                result = cls._generic_to_source(
                    type_expression=type_expression,
                )
            case CallableExpression():
                result = cls._callable_to_source(
                    type_expression=type_expression,
                )
        return result

    @classmethod
    def required_imports(
        cls,
        *,
        type_expression: TypeExpression,
    ) -> frozenset[RequiredImport]:
        """Return typing imports required by ``type_expression``.

        Args:
            type_expression (TypeExpression): Type expression supplied as
                TypeExpression for this operation.

        Returns:
            frozenset[RequiredImport]: frozenset[RequiredImport] produced by
                this operation.

        """
        imports: set[RequiredImport] = set()
        cls._collect_required_imports(
            type_expression=type_expression,
            imports=imports,
        )
        return frozenset(imports)

    @staticmethod
    def name(*, name: str) -> TypeName:
        """Create a named type expression.

        Args:
            name (str): Identifier of the name being resolved.

        Returns:
            TypeName: TypeName produced by this operation.

        """
        return TypeName(name=name)

    @staticmethod
    def generic(
        *,
        base: str | TypeExpression,
        arguments: tuple[TypeExpression, ...],
    ) -> GenericExpression:
        """Create a generic type expression.

        Args:
            arguments (tuple[TypeExpression, ...]): Collection of arguments
                supplied for this operation.
            base (str | TypeExpression): Base supplied as str | TypeExpression
                for this operation.

        Returns:
            GenericExpression: GenericExpression produced by this operation.

        """
        base_expression: TypeExpression = (
            TypeName(name=base) if isinstance(base, str) else base
        )
        return GenericExpression(base=base_expression, arguments=arguments)

    @staticmethod
    def callable(
        *,
        parameters: tuple[TypeExpression, ...] | EllipsisExpression,
        returns: TypeExpression,
    ) -> CallableExpression:
        """Create a callable type expression.

        Args:
            parameters: Collection of parameters supplied for this operation.
            returns (TypeExpression): Returns supplied as TypeExpression for
                this operation.

        Returns:
            CallableExpression: CallableExpression produced by this operation.

        """
        return CallableExpression(parameters=parameters, returns=returns)

    @classmethod
    def _from_binary_type_expression(
        cls,
        *,
        node: BinOp,
    ) -> TypeExpression | None:
        """Parse binary type expressions such as PEP 604 unions.

        Args:
            node (BinOp): The node examined while parse binary
                type expressions such as PEP 604 unions.

        Returns:
            TypeExpression | None:
                TypeExpression | None produced by this operation.

        """
        if not isinstance(node.op, BitOr):
            return None
        return cls.union(
            members=(
                cls.from_ast(node=node.left),
                cls.from_ast(node=node.right),
            ),
        )

    @classmethod
    def _from_subscript(cls, *, node: Subscript) -> TypeExpression:
        """Parse a subscripted type expression.

        Args:
            node (Subscript): The node examined while parse a subscripted type
                expression.

        Returns:
            TypeExpression: TypeExpression produced by this operation.

        """
        base: TypeExpression = cls.from_ast(node=node.value)
        base_name: str = cls.to_source(type_expression=base)
        slice_args: tuple[TypeExpression, ...] = _subscript_arguments(
            node=node.slice,
        )
        if (
            base_name in Constants.callable_names
            and len(slice_args) == Constants.callable_arg_count
        ):
            return CallableExpression(
                parameters=_callable_parameters(type_expression=slice_args[0]),
                returns=slice_args[1],
            )
        return GenericExpression(base=base, arguments=slice_args)

    @classmethod
    def _union_to_source(cls, *, type_expression: UnionExpression) -> str:
        """Render a union expression.

        Args:
            type_expression (UnionExpression): Type expression supplied as
                UnionExpression for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return " | ".join(
            cls.to_source(type_expression=member)
            for member in type_expression.members
        )

    @classmethod
    def _generic_to_source(cls, *, type_expression: GenericExpression) -> str:
        """Render a generic expression.

        Args:
            type_expression (GenericExpression): Type expression supplied as
                GenericExpression for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        arguments: str = ", ".join(
            cls.to_source(type_expression=argument)
            for argument in type_expression.arguments
        )
        base: str = cls.to_source(type_expression=type_expression.base)
        return f"{base}[{arguments}]"

    @classmethod
    def _callable_to_source(
        cls,
        *,
        type_expression: CallableExpression,
    ) -> str:
        """Render a callable expression.

        Args:
            type_expression (CallableExpression): Type expression supplied as
                CallableExpression for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        if isinstance(type_expression.parameters, EllipsisExpression):
            parameters: str = "..."
        else:
            parameters = (
                "["
                + ", ".join(
                    cls.to_source(type_expression=parameter)
                    for parameter in type_expression.parameters
                )
                + "]"
            )
        returns: str = cls.to_source(type_expression=type_expression.returns)
        return f"Callable[{parameters}, {returns}]"

    @classmethod
    def _collect_required_imports(
        cls,
        *,
        type_expression: TypeExpression,
        imports: set[RequiredImport],
    ) -> None:
        """Collect imports needed by one expression recursively.

        Args:
            imports (set[RequiredImport]): Imports supplied as
                set[RequiredImport] for this operation.
            type_expression (TypeExpression): Type expression supplied as
                TypeExpression for this operation.

        """
        child_expressions: tuple[TypeExpression, ...] = (
            _direct_child_type_expressions(
                type_expression=type_expression,
                imports=imports,
            )
        )
        for child_expression in child_expressions:
            cls._collect_required_imports(
                type_expression=child_expression,
                imports=imports,
            )


def _atomic_type_expression(*, node: expr) -> TypeExpression | None:
    """Return a type expression for simple AST nodes.

    Args:
        node (expr): The node examined while return a
            type expression for simple AST nodes.

    Returns:
        TypeExpression | None:
            TypeExpression | None produced by this operation.

    """
    result: TypeExpression | None = None
    if isinstance(node, Name):
        result = TypeName(name=node.id)
    elif isinstance(node, Attribute):
        result = TypeName(name=_attribute_name(node=node))
    elif isinstance(node, Constant):
        result = _constant_type_expression(node=node)
    return result


def _constant_type_expression(*, node: Constant) -> TypeExpression | None:
    """Return a type expression for a constant annotation node.

    Args:
        node (Constant): The node examined while return a type
            expression for a constant annotation node.

    Returns:
        TypeExpression | None:
            TypeExpression | None produced by this operation.

    """
    if node.value is None:
        return TypeName(name=Constants.none_name)
    if node.value is Ellipsis:
        return EllipsisExpression()
    if isinstance(node.value, str):
        return TypeName(name=node.value)
    return None


def _direct_child_type_expressions(
    *,
    type_expression: TypeExpression,
    imports: set[RequiredImport],
) -> tuple[TypeExpression, ...]:
    """Return direct child expressions and update required imports.

    Args:
        imports (set[RequiredImport]): Imports supplied as set[RequiredImport]
            for this operation.
        type_expression (TypeExpression): Type expression supplied as
            TypeExpression for this operation.

    Returns:
        tuple[TypeExpression, ...]: tuple[TypeExpression, ...] produced by this
            operation.

    """
    result: tuple[TypeExpression, ...] = ()
    match type_expression:
        case TypeVarExpression(bound=bound):
            imports.add(RequiredImport.TYPE_VAR)
            result = (bound,) if bound is not None else ()
        case ParamSpecExpression():
            imports.add(RequiredImport.PARAM_SPEC)
        case UnionExpression(members=members):
            result = members
        case GenericExpression(base=base, arguments=arguments):
            result = (base, *arguments)
        case CallableExpression(parameters=parameters, returns=returns):
            imports.add(RequiredImport.CALLABLE)
            match parameters:
                case EllipsisExpression():
                    result = (returns,)
                case _:
                    result = (*parameters, returns)
        case TypeName() | EllipsisExpression():
            pass
    return result


def _union_sort_key(*, name: str) -> tuple[int, str]:
    """Return a deterministic union member ordering key.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        tuple[int, str]: tuple[int, str] produced by this operation.

    """
    return (1 if name == Constants.none_name else 0, name)


def _attribute_name(*, node: Attribute) -> str:
    """Render a dotted attribute expression without text manipulation.

    Args:
        node (Attribute): The node examined while render a dotted
            attribute expression without text manipulation.

    Returns:
        str: Rendered source text produced by this operation.

    Raises:
        TypeExpressionError: If this operation cannot satisfy its documented
            contract.

    """
    parts: list[str] = [node.attr]
    value: AST = node.value
    while isinstance(value, Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, Name):
        parts.append(value.id)
    else:
        msg: str = "unsupported attribute base in type expression"
        raise TypeExpressionError(msg)
    return ".".join(reversed(parts))


def _subscript_arguments(*, node: expr) -> tuple[TypeExpression, ...]:
    """Return the parsed arguments for a subscript slice.

    Args:
        node (expr): The node examined while return the parsed arguments for a
            subscript slice.

    Returns:
        tuple[TypeExpression, ...]: tuple[TypeExpression, ...] produced by this
            operation.

    """
    if isinstance(node, AstTuple):
        return tuple(
            TypeExpressionCodec.from_ast(node=item) for item in node.elts
        )
    return (TypeExpressionCodec.from_ast(node=node),)


def _callable_parameters(
    *,
    type_expression: TypeExpression,
) -> tuple[TypeExpression, ...] | EllipsisExpression:
    """Normalize the first argument of ``Callable``.

    Args:
        type_expression (TypeExpression): Type expression supplied as
            TypeExpression for this operation.

    Returns:
        tuple[TypeExpression, ...] | EllipsisExpression:
            tuple[TypeExpression, ...] |
            EllipsisExpression produced by this operation.

    """
    match type_expression:
        case EllipsisExpression():
            return type_expression
        case GenericExpression(
            base=TypeName(name="list"),
            arguments=arguments,
        ):
            return arguments
        case TypeName(name="[]"):
            return ()
        case TypeName():
            return (type_expression,)
        case _:
            return (type_expression,)
