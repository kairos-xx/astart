"""Pure-AST callable signatures, generic contracts, class and protocol indexes.

No source is imported or executed. Bound arguments and signatures are
immutable; AST nodes referenced by records remain mutable, and a newly
created index must be used after any mutation. All static contracts are
evidence, not runtime proofs.
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Dict,
    FunctionDef,
    List,
    Module,
    Name,
    ParamSpec,
    Starred,
    Subscript,
    Tuple,
    TypeVar,
    TypeVarTuple,
    arg,
    arguments,
    keyword,
    unparse,
)
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final, final

from astart.semantic.parameter_kinds import ParameterKind
from astart.semantic.type_expressions import (
    TypeExpression,
    TypeExpressionCodec,
)
from astart.semantic.typing_relations import method_compatible

if TYPE_CHECKING:
    from astart.semantic.type_shapes import TypeShape
    from astart.semantic.typing_relations import Compatibility


@final
class Constants:
    """Group module-level constants.

    Attributes:
        newtype_argument_count: Grouped module constant.

    """

    newtype_argument_count: Final[int] = 2


class ArgumentOrigin(StrEnum):
    """Source of an individual effective call argument.

    Attributes:
        DEFAULT: Default associated with this instance.
        DEFAULT_FACTORY: Default factory associated with this instance.
        EXPANSION_UNKNOWN: Expansion unknown associated with this instance.
        IMPLICIT_RECEIVER: Implicit receiver associated with this instance.
        KEYWORD: Keyword associated with this instance.
        MISSING: Missing associated with this instance.
        POSITIONAL: Positional associated with this instance.
        VAR_KEYWORD: Var keyword associated with this instance.
        VAR_POSITIONAL: Var positional associated with this instance.

    """

    POSITIONAL = "positional"
    KEYWORD = "keyword"
    DEFAULT = "default"
    DEFAULT_FACTORY = "default_factory"
    VAR_POSITIONAL = "var_positional"
    VAR_KEYWORD = "var_keyword"
    MISSING = "missing"
    IMPLICIT_RECEIVER = "implicit_receiver"
    EXPANSION_UNKNOWN = "expansion_unknown"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterContract:
    """A source parameter with declaration, kind, and optional default.

    Attributes:
        annotation: Annotation retained as TypeExpression | None by this
            instance.
        declaration: Declaration retained as AST | None by this instance.
        default: Default retained as AST | None by this instance.
        factory: Factory retained as AST | None by this instance.
        kind: Kind retained as ParameterKind by this instance.
        name: Identifier used to refer to the name.
        optional: Optional retained as bool by this instance.

    """

    name: str
    kind: ParameterKind
    annotation: TypeExpression | None = None
    default: AST | None = None
    factory: AST | None = None
    declaration: AST | None = None
    optional: bool = False

    @property
    def has_default(self) -> bool:
        """Whether the parameter may be omitted by its caller.

        Returns:
            Whether the requested condition holds.

        """
        return (
            self.default is not None
            or self.factory is not None
            or self.optional
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CallableContract:
    """Callable declaration including full parameter-kind semantics.

    Attributes:
        declaration: Declaration retained as AST | None by this instance.
        is_overload: Is overload retained as bool by this instance.
        method_kind: Method kind retained as str by this instance.
        parameters: Parameters retained as tuple[ParameterContract, ...] by
            this instance.
        qualified_name: Identifier used to refer to the qualified.
        returns: Returns retained as TypeExpression | None by this instance.
        source_path: Path to the source used by this instance.
        type_parameters: Type parameters retained as tuple[str, ...] by this
            instance.

    """

    qualified_name: str
    parameters: tuple[ParameterContract, ...]
    returns: TypeExpression | None = None
    declaration: AST | None = None
    source_path: str | None = None
    is_overload: bool = False
    method_kind: str = "function"
    type_parameters: tuple[str, ...] = ()

    @property
    def signature(self) -> str:
        """Render an inspect.Signature-inspired declaration faithfully.

        Returns:
            Rendered source text produced by this operation.

        """
        pieces: list[str] = []
        params: tuple[ParameterContract, ...] = self.parameters
        for index, parameter in enumerate(iterable=params):
            if (
                parameter.kind is ParameterKind.KEYWORD_ONLY
                and (
                    not any(
                        p.kind is ParameterKind.VAR_POSITIONAL
                        for p in params[:index]
                    )
                )
                and (not any(part == "*" for part in pieces))
            ):
                pieces.append("*")
            prefix: str = (
                "**"
                if parameter.kind is ParameterKind.VAR_KEYWORD
                else "*"
                if parameter.kind is ParameterKind.VAR_POSITIONAL
                else ""
            )
            part: str = prefix + parameter.name
            if parameter.annotation is not None:
                part += f": {parameter.annotation}"
            if parameter.has_default:
                part += f" = {
                    (
                        unparse(ast_obj=parameter.default)
                        if parameter.default is not None
                        else '<factory>'
                        if parameter.factory is not None
                        else '...'
                    )
                }"
            pieces.append(part)
            if parameter.kind is ParameterKind.POSITIONAL_ONLY and (
                index + 1 == len(params)
                or params[index + 1].kind is not ParameterKind.POSITIONAL_ONLY
            ):
                pieces.append("/")
        suffix: str = "" if self.returns is None else f" -> {self.returns}"
        return f"{self.qualified_name}({', '.join(pieces)}){suffix}"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BoundArgument:
    """Resolved effective argument, including omitted/defaulted arguments.

    Attributes:
        definite: Definite retained as bool by this instance.
        origin: Origin retained as ArgumentOrigin by this instance.
        parameter: Parameter retained as ParameterContract by this instance.
        types: Types retained as tuple[TypeShape, ...] by this instance.
        values: Values retained as tuple[AST, ...] by this instance.

    """

    parameter: ParameterContract
    origin: ArgumentOrigin
    values: tuple[AST, ...]
    types: tuple[TypeShape, ...]
    definite: bool = True

    @property
    def name(self) -> str:
        """Parameter's declared keyword name even when passed positionally.

        Returns:
            str produced by this operation.

        """
        return self.parameter.name

    @property
    def type_hint(self) -> TypeExpression | None:
        """Return the declared parameter contract, if available.

        Returns:
            TypeExpression | None produced by this operation.

        """
        return self.parameter.annotation


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BoundCall:
    """A complete inspect-like binding with errors and uncertain expansions.

    Attributes:
        arguments: Arguments retained as tuple[BoundArgument, ...] by this
            instance.
        call: Call retained as Call by this instance.
        errors: Errors retained as tuple[str, ...] by this instance.
        indeterminate: Indeterminate retained as bool by this instance.
        signature: Signature retained as CallableContract by this instance.

    """

    call: Call
    signature: CallableContract
    arguments: tuple[BoundArgument, ...]
    errors: tuple[str, ...] = ()
    indeterminate: bool = False

    @property
    def valid(self) -> bool:
        """Whether all statically decidable binding checks passed.

        Returns:
            Whether the requested condition holds.

        """
        return not self.errors

    def parameter(self, *, name: str) -> BoundArgument | None:
        """Find a named effective binding, including an omitted default.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            BoundArgument | None produced by this operation.

        """
        return next(
            (item for item in self.arguments if item.name == name),
            None,
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FieldContract:
    """Resolved field declaration with dataclass constructor configuration.

    Attributes:
        annotation: Annotation retained as TypeExpression by this instance.
        class_variable: Class variable retained as bool by this instance.
        default: Default retained as AST | None by this instance.
        factory: Factory retained as AST | None by this instance.
        init: Init retained as bool by this instance.
        init_variable: Init variable retained as bool by this instance.
        kw_only: Kw only retained as bool by this instance.
        name: Identifier used to refer to the name.
        optional: Optional retained as bool by this instance.
        source: Original source text retained for parsing and reconstruction.

    """

    name: str
    annotation: TypeExpression
    source: AnnAssign
    default: AST | None = None
    factory: AST | None = None
    init: bool = True
    kw_only: bool = False
    class_variable: bool = False
    init_variable: bool = False
    optional: bool = False


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ClassContract:
    """Source-defined nominal class, protocol, dataclass, enum or TypedDict.

    Attributes:
        bases: Bases retained as tuple[str, ...] by this instance.
        fields: Fields retained as tuple[FieldContract, ...] by this instance.
        is_dataclass: Is dataclass retained as bool by this instance.
        is_enum: Is enum retained as bool by this instance.
        is_named_tuple: Is named tuple retained as bool by this instance.
        is_protocol: Is protocol retained as bool by this instance.
        is_typed_dict: Is typed dict retained as bool by this instance.
        members: Members retained as tuple[tuple[str, TypeExpression], ...] by
            this instance.
        methods: Methods retained as tuple[CallableContract, ...] by this
            instance.
        name: Identifier used to refer to the name.
        node: AST node associated with this record.
        type_parameters: Type parameters retained as tuple[str, ...] by this
            instance.

    """

    name: str
    bases: tuple[str, ...]
    members: tuple[tuple[str, TypeExpression], ...]
    methods: tuple[CallableContract, ...]
    node: ClassDef
    fields: tuple[FieldContract, ...] = ()
    is_protocol: bool = False
    is_dataclass: bool = False
    is_enum: bool = False
    is_typed_dict: bool = False
    is_named_tuple: bool = False
    type_parameters: tuple[str, ...] = ()

    def member(self, *, name: str) -> TypeExpression | None:
        """Find a field type without executing its initializer.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            TypeExpression | None produced by this operation.

        """
        return next(
            (value for key, value in self.members if key == name),
            None,
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ContractDiagnostic:
    """A static class-contract or override diagnostic with source syntax.

    Attributes:
        code: Code retained as str by this instance.
        description: Description retained as str by this instance.
        node: AST node associated with this record.

    """

    code: str
    description: str
    node: AST


def _decorator_name(*, node: AST) -> str:
    """Read a decorator name without executing decorator expressions.

    Args:
        node: The node examined while read a decorator name without executing
            decorator expressions.

    Returns:
        str produced by this operation.

    """
    return (
        _qualified(node=node.func)
        if isinstance(node, Call)
        else _qualified(node=node)
    )


def _qualified(*, node: AST) -> str:
    """Resolve syntactic dotted names or preserve source spelling.

    Args:
        node: The node examined while resolve syntactic dotted names or
            preserve source spelling.

    Returns:
        Rendered source text produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return f"{_qualified(node=node.value)}.{node.attr}"
    if isinstance(node, Subscript):
        return _qualified(node=node.value)
    return unparse(ast_obj=node)


def _annotation(*, node: AST | None) -> TypeExpression | None:
    """Parse a declaration annotation while retaining forward references.

    Args:
        node: The node examined while parse a declaration annotation while
            retaining forward references.

    Returns:
        TypeExpression | None produced by this operation.

    """
    return (
        TypeExpressionCodec.from_ast(node=node) if node is not None else None
    )


def _type_parameters(
    *,
    node: FunctionDef | AsyncFunctionDef | ClassDef,
) -> tuple[str, ...]:
    """Collect PEP 695 type parameter identifiers.

    Args:
        node: The node examined while collect PEP 695 type parameter
            identifiers.

    Returns:
        tuple[str, ...] produced by this operation.

    """
    return tuple(
        p.name
        for p in node.type_params
        if isinstance(p, (TypeVar, TypeVarTuple, ParamSpec))
    )


def function_contract(
    *,
    node: FunctionDef | AsyncFunctionDef,
    qualified_name: str | None = None,
    method_kind: str = "function",
) -> CallableContract:
    """Construct a source signature with Python's five binding kinds.

    Args:
        method_kind: Method kind supplied as str for this operation.
        node: The node examined while construct a source signature with
            Python's five binding kinds.
        qualified_name: Identifier of the qualified being resolved.

    Returns:
        CallableContract produced by this operation.

    """
    args: arguments = node.args
    positional: tuple[arg, ...] = (*args.posonlyargs, *args.args)
    defaults: tuple[AST | None, ...] = tuple(
        (None,) * (len(positional) - len(args.defaults)),
    ) + tuple(args.defaults)
    parameters: list[ParameterContract] = []
    for index, parameter in enumerate(iterable=positional):
        parameters.append(
            ParameterContract(
                name=parameter.arg,
                kind=ParameterKind.POSITIONAL_ONLY
                if index < len(args.posonlyargs)
                else ParameterKind.POSITIONAL_OR_KEYWORD,
                annotation=_annotation(node=parameter.annotation),
                default=defaults[index],
                declaration=parameter,
            ),
        )
    if args.vararg is not None:
        parameters.append(
            ParameterContract(
                name=args.vararg.arg,
                kind=ParameterKind.VAR_POSITIONAL,
                annotation=_annotation(node=args.vararg.annotation),
                declaration=args.vararg,
            ),
        )
    for parameter, default in zip(
        args.kwonlyargs,
        args.kw_defaults,
        strict=True,
    ):
        parameters.append(
            ParameterContract(
                name=parameter.arg,
                kind=ParameterKind.KEYWORD_ONLY,
                annotation=_annotation(node=parameter.annotation),
                default=default,
                declaration=parameter,
            ),
        )
    if args.kwarg is not None:
        parameters.append(
            ParameterContract(
                name=args.kwarg.arg,
                kind=ParameterKind.VAR_KEYWORD,
                annotation=_annotation(node=args.kwarg.annotation),
                declaration=args.kwarg,
            ),
        )
    decorators: frozenset[str] = frozenset(
        _decorator_name(node=part).split(sep=".")[-1]
        for part in node.decorator_list
    )
    return CallableContract(
        qualified_name=qualified_name or node.name,
        parameters=tuple(parameters),
        returns=_annotation(node=node.returns),
        declaration=node,
        is_overload="overload" in decorators,
        method_kind=method_kind,
        type_parameters=_type_parameters(node=node),
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _CallTerms:
    """Literal-expanded call terms and expansion uncertainty flags.

    Attributes:
        named: Named retained as tuple[tuple[str, AST, TypeShape], ...] by this
            instance.
        positional: Positional retained as tuple[tuple[AST, TypeShape,
            ArgumentOrigin], ...] by this instance.
        unknown_keyword: Unknown keyword retained as bool by this instance.
        unknown_positional: Unknown positional retained as bool by this
            instance.

    """

    positional: tuple[tuple[AST, TypeShape, ArgumentOrigin], ...]
    named: tuple[tuple[str, AST, TypeShape], ...]
    unknown_positional: bool
    unknown_keyword: bool

    @property
    def uncertain(self) -> bool:
        """Whether any expansion could not be resolved statically.

        Returns:
            Whether the requested condition holds.

        """
        return self.unknown_positional or self.unknown_keyword


def _star_expansion(
    *,
    item: Starred,
    shape: TypeShape,
) -> tuple[tuple[AST, TypeShape, ArgumentOrigin], ...] | None:
    """Expand a literal list/tuple `*` into positional terms, if literal.

    Args:
        item: Item supplied as Starred for this operation.
        shape: Shape supplied as TypeShape for this operation.

    Returns:
        tuple[tuple[AST, TypeShape, ArgumentOrigin], ...] | None produced by
        this operation.

    """
    if not isinstance(item.value, (List, Tuple)):
        return None
    element: TypeShape = shape.arguments[0] if shape.arguments else shape
    return tuple(
        (child, element, ArgumentOrigin.VAR_POSITIONAL)
        for child in item.value.elts
    )


def _dict_expansion(
    *,
    part: keyword,
    shape: TypeShape,
) -> tuple[tuple[str, AST, TypeShape], ...] | None:
    """Expand a literal dict `**` into named terms, when keys are strings.

    Args:
        part: Part supplied as keyword for this operation.
        shape: Shape supplied as TypeShape for this operation.

    Returns:
        tuple[tuple[str, AST, TypeShape], ...] | None produced by this
        operation.

    """
    if not isinstance(part.value, Dict):
        return None
    literal: list[tuple[str, AST]] = [
        (item.value, value)
        for item, value in zip(part.value.keys, part.value.values, strict=True)
        if isinstance(item, Constant) and isinstance(item.value, str)
    ]
    if len(literal) != len(part.value.keys):
        return None
    element: TypeShape = (
        shape.arguments[1] if len(shape.arguments) > 1 else shape
    )
    return tuple(((key, value, element) for key, value in literal))


def _call_terms(
    *,
    call: Call,
    positional_types: tuple[TypeShape, ...],
    keyword_types: tuple[tuple[str | None, TypeShape], ...],
) -> _CallTerms:
    """Collect literal-expanded call terms and flag unknown `*`/`**` uses.

    Args:
        call: The call examined while collect literal-expanded call terms and
            flag unknown `*`/`**` uses.
        keyword_types: Keyword types supplied as tuple[tuple[str | None,
            TypeShape], ...] for this operation.
        positional_types: Positional types supplied as tuple[TypeShape, ...]
            for this operation.

    Returns:
        _CallTerms produced by this operation.

    """
    positional: list[tuple[AST, TypeShape, ArgumentOrigin]] = []
    named: list[tuple[str, AST, TypeShape]] = []
    unknown_positional: bool = False
    unknown_keyword: bool = False
    for item, shape in zip(call.args, positional_types, strict=True):
        if not isinstance(item, Starred):
            positional.append((item, shape, ArgumentOrigin.POSITIONAL))
            continue
        expanded: tuple[tuple[AST, TypeShape, ArgumentOrigin], ...] | None = (
            _star_expansion(item=item, shape=shape)
        )
        if expanded is None:
            unknown_positional = True
        else:
            positional.extend(expanded)
    for part, (key, shape) in zip(call.keywords, keyword_types, strict=True):
        if key is not None:
            named.append((key, part.value, shape))
            continue
        entries: tuple[tuple[str, AST, TypeShape], ...] | None = (
            _dict_expansion(part=part, shape=shape)
        )
        if entries is None:
            unknown_keyword = True
        else:
            named.extend(entries)
    return _CallTerms(
        positional=tuple(positional),
        named=tuple(named),
        unknown_positional=unknown_positional,
        unknown_keyword=unknown_keyword,
    )


@final
class _SignatureBinder:
    """Incremental inspect-style binder over precomputed call terms."""

    def __init__(
        self,
        *,
        signature: CallableContract,
        terms: _CallTerms,
        receiver_type: TypeShape | None,
    ) -> None:
        """Keep the signature, terms, and binding progress together.

        Args:
            receiver_type: Receiver type supplied as TypeShape | None for this
                operation.
            signature: Signature supplied as CallableContract for this
                operation.
            terms: Terms supplied as _CallTerms for this operation.

        """
        self.signature: CallableContract = signature
        self.terms: _CallTerms = terms
        self.receiver_type: TypeShape | None = receiver_type
        self.effective: list[BoundArgument] = []
        self.errors: list[str] = []
        self.position: int = 0
        self.used: set[int] = set()

    def bind(self, *, parameter: ParameterContract) -> None:
        """Bind one parameter through each admissible term channel.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        """
        if self._receiver(parameter=parameter):
            return
        if self._varargs(parameter=parameter):
            return
        if self._varkw(parameter=parameter):
            return
        if self._positional(parameter=parameter):
            return
        if self._keyword(parameter=parameter):
            return
        self._fallback(parameter=parameter)

    def finish(self, *, call: Call) -> BoundCall:
        """Report leftover terms and seal the complete binding.

        Args:
            call: The call examined while report leftover terms and seal the
                complete binding.

        Returns:
            BoundCall produced by this operation.

        """
        if self.position < len(self.terms.positional):
            self.errors.append("too many positional arguments")
        remaining: list[str] = [
            name
            for index, (name, _, _) in enumerate(iterable=self.terms.named)
            if index not in self.used
        ]
        if remaining:
            self.errors.append(
                f"unexpected keyword arguments: {', '.join(remaining)}",
            )
        return BoundCall(
            call=call,
            signature=self.signature,
            arguments=tuple(self.effective),
            errors=tuple(self.errors),
            indeterminate=self.terms.uncertain,
        )

    def _receiver(self, *, parameter: ParameterContract) -> bool:
        """Bind an implicit receiver to a method's leading parameter.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        if (
            self.receiver_type is None
            or parameter is not self.signature.parameters[0]
            or self.signature.method_kind not in ("instance", "class")
        ):
            return False
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=ArgumentOrigin.IMPLICIT_RECEIVER,
                values=(),
                types=(self.receiver_type,),
            ),
        )
        return True

    def _varargs(self, *, parameter: ParameterContract) -> bool:
        """Consume all remaining positional terms for `*args`.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        if parameter.kind is not ParameterKind.VAR_POSITIONAL:
            return False
        items: tuple[tuple[AST, TypeShape, ArgumentOrigin], ...] = (
            self.terms.positional[self.position :]
        )
        self.position = len(self.terms.positional)
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=ArgumentOrigin.VAR_POSITIONAL,
                values=tuple((value for value, _, _ in items)),
                types=tuple((shape for _, shape, _ in items)),
                definite=not self.terms.unknown_positional,
            ),
        )
        return True

    def _varkw(self, *, parameter: ParameterContract) -> bool:
        """Consume every unconsumed named term for `**kwargs`.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        if parameter.kind is not ParameterKind.VAR_KEYWORD:
            return False
        items: list[tuple[str, AST, TypeShape]] = [
            item
            for index, item in enumerate(iterable=self.terms.named)
            if index not in self.used
        ]
        self.used.update(range(len(self.terms.named)))
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=ArgumentOrigin.VAR_KEYWORD,
                values=tuple((value for _, value, _ in items)),
                types=tuple((shape for _, _, shape in items)),
                definite=not self.terms.unknown_keyword,
            ),
        )
        return True

    def _positional(self, *, parameter: ParameterContract) -> bool:
        """Consume the next positional term for positional-capable kinds.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        if parameter.kind not in (
            ParameterKind.POSITIONAL_ONLY,
            ParameterKind.POSITIONAL_OR_KEYWORD,
        ) or self.position >= len(self.terms.positional):
            return False
        source, actual, origin = self.terms.positional[self.position]
        self.position += 1
        if parameter.kind is ParameterKind.POSITIONAL_OR_KEYWORD and any(
            (name == parameter.name for name, _, _ in self.terms.named),
        ):
            self.errors.append(
                f"multiple values for argument '{parameter.name}'",
            )
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=origin,
                values=(source,),
                types=(actual,),
            ),
        )
        return True

    def _keyword(self, *, parameter: ParameterContract) -> bool:
        """Consume a named term, flagging positional-only misuse.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        matches: list[tuple[int, AST, TypeShape]] = [
            (index, value, actual)
            for index, (name, value, actual) in enumerate(
                iterable=self.terms.named,
            )
            if name == parameter.name and index not in self.used
        ]
        if not matches:
            return False
        if parameter.kind is ParameterKind.POSITIONAL_ONLY:
            self.errors.append(
                f"positional-only argument '{parameter.name}' "
                "passed by keyword",
            )
            return False
        index, source, actual = matches[0]
        self.used.add(index)
        if len(matches) > 1:
            self.errors.append(
                f"multiple values for argument '{parameter.name}'",
            )
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=ArgumentOrigin.KEYWORD,
                values=(source,),
                types=(actual,),
            ),
        )
        return True

    def _fallback(self, *, parameter: ParameterContract) -> None:
        """Bind an unsupplied parameter to a default, expansion or a gap.

        Args:
            parameter: Parameter supplied as ParameterContract for this
                operation.

        """
        if parameter.has_default:
            self.effective.append(
                BoundArgument(
                    parameter=parameter,
                    origin=ArgumentOrigin.DEFAULT_FACTORY
                    if parameter.factory is not None
                    else ArgumentOrigin.DEFAULT,
                    values=(parameter.default,)
                    if parameter.default is not None
                    else (),
                    types=(),
                    definite=True,
                ),
            )
            return
        if self.terms.uncertain:
            self.effective.append(
                BoundArgument(
                    parameter=parameter,
                    origin=ArgumentOrigin.EXPANSION_UNKNOWN,
                    values=(),
                    types=(),
                    definite=False,
                ),
            )
            return
        self.errors.append(f"missing required argument '{parameter.name}'")
        self.effective.append(
            BoundArgument(
                parameter=parameter,
                origin=ArgumentOrigin.MISSING,
                values=(),
                types=(),
            ),
        )


def bind_signature(
    *,
    call: Call,
    signature: CallableContract,
    positional_types: tuple[TypeShape, ...],
    keyword_types: tuple[tuple[str | None, TypeShape], ...],
    receiver_type: TypeShape | None = None,
) -> BoundCall:
    """Bind source call arguments against a contract without execution.

    Unknown `*`/`**` expansions are explicitly marked indeterminate. Literal
    tuples/lists/dictionaries can be expanded safely. Every parameter gets a
    record even if omitted; implicit receivers and defaults are represented.


    Args:
        call: The call examined while bind source call arguments against a
            contract without execution.
        keyword_types: Keyword types supplied as tuple[tuple[str | None,
            TypeShape], ...] for this operation.
        positional_types: Positional types supplied as tuple[TypeShape, ...]
            for this operation.
        receiver_type: Receiver type supplied as TypeShape | None for this
            operation.
        signature: Signature supplied as CallableContract for this operation.

    Returns:
        BoundCall produced by this operation.

    """
    binder: _SignatureBinder = _SignatureBinder(
        signature=signature,
        terms=_call_terms(
            call=call,
            positional_types=positional_types,
            keyword_types=keyword_types,
        ),
        receiver_type=receiver_type,
    )
    for parameter in signature.parameters:
        binder.bind(parameter=parameter)
    return binder.finish(call=call)


@final
class ContractIndex:
    """Read-only nominal/structural declarations from the original module."""

    def __init__(self, *, root: Module) -> None:
        """Build a module-local index without running analyzed code.

        Args:
            root: Filesystem path identifying the root.

        """
        self.root: Module = root
        self.functions: dict[str, tuple[CallableContract, ...]] = {}
        self.classes: dict[str, ClassContract] = {}
        self.newtypes: dict[str, TypeExpression] = {}
        for statement in root.body:
            if isinstance(statement, (FunctionDef, AsyncFunctionDef)):
                self.functions[statement.name] = (
                    *self.functions.get(statement.name, ()),
                    function_contract(node=statement),
                )
            elif isinstance(statement, ClassDef):
                self.classes[statement.name] = self._class(node=statement)
            elif (
                isinstance(statement, Assign)
                and isinstance(statement.value, Call)
                and (
                    _qualified(node=statement.value.func).split(sep=".")[-1]
                    == "NewType"
                )
                and (
                    len(statement.value.args)
                    >= Constants.newtype_argument_count
                )
            ):
                for target in statement.targets:
                    if isinstance(target, Name):
                        self.newtypes[target.id] = (
                            TypeExpressionCodec.from_ast(
                                node=statement.value.args[1],
                            )
                        )
        self.diagnostics: tuple[ContractDiagnostic, ...] = (
            self._validate_overrides()
        )

    def variants(self, *, qualified_name: str) -> tuple[CallableContract, ...]:
        """Return all source overloads, including implementation contracts.

        Args:
            qualified_name: Identifier of the qualified being resolved.

        Returns:
            tuple[CallableContract, ...] produced by this operation.

        """
        if "." in qualified_name:
            owner, _, method = qualified_name.partition(".")
            cls: ClassContract | None = self.classes.get(owner)
            return (
                tuple(
                    item
                    for item in cls.methods
                    if item.qualified_name.rsplit(sep=".", maxsplit=1)[-1]
                    == method
                )
                if cls is not None
                else ()
            )
        return self.functions.get(qualified_name, ())

    def class_member(self, *, owner: str, name: str) -> TypeExpression | None:
        """Look up an annotated member through source-defined base classes.

        Args:
            name: Identifier of the name being resolved.
            owner: Owner supplied as str for this operation.

        Returns:
            TypeExpression | None produced by this operation.

        """
        pending: list[str] = [owner]
        seen: set[str] = set()
        while pending:
            current: str = pending.pop(0)
            if current in seen:
                continue
            seen.add(current)
            cls: ClassContract | None = self.classes.get(current)
            if cls is not None:
                member: TypeExpression | None = cls.member(name=name)
                if member is not None:
                    return member
                pending.extend(cls.bases)
        return None

    def constructor(self, *, name: str) -> CallableContract | None:
        """Provide a synthesized dataclass/NamedTuple/TypedDict constructor.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            CallableContract | None produced by this operation.

        """
        cls: ClassContract | None = self.classes.get(name)
        if cls is None:
            return None
        if init := self.variants(qualified_name=f"{name}.__init__"):
            return init[-1]
        if not (cls.is_dataclass or cls.is_named_tuple or cls.is_typed_dict):
            return CallableContract(
                qualified_name=name,
                parameters=(),
                returns=TypeExpression(name=name),
                declaration=cls.node,
            )
        field_map: dict[str, FieldContract] = {}
        pending: list[str] = list(reversed(cls.bases))
        seen: set[str] = set()
        while pending:
            current: str = pending.pop(0)
            if current in seen:
                continue
            seen.add(current)
            inherited: ClassContract | None = self.classes.get(current)
            if inherited is not None:
                pending = list(reversed(inherited.bases)) + pending
                for field in inherited.fields:
                    field_map[field.name] = field
        for field in cls.fields:
            field_map[field.name] = field
        parameters: tuple[ParameterContract, ...] = tuple(
            ParameterContract(
                name=field.name,
                kind=ParameterKind.KEYWORD_ONLY
                if field.kw_only or cls.is_typed_dict
                else ParameterKind.POSITIONAL_OR_KEYWORD,
                annotation=field.annotation,
                default=field.default,
                factory=field.factory,
                declaration=field.source,
                optional=field.optional,
            )
            for field in field_map.values()
            if field.init
        )
        return CallableContract(
            qualified_name=name,
            parameters=parameters,
            returns=TypeExpression(name=name),
            declaration=cls.node,
        )

    def inherited_method(
        self,
        *,
        owner: str,
        method: str,
    ) -> CallableContract | None:
        """Resolve a method from explicitly named source-defined bases.

        Args:
            method: Method supplied as str for this operation.
            owner: Owner supplied as str for this operation.

        Returns:
            CallableContract | None produced by this operation.

        """
        current: list[str] = [owner]
        seen: set[str] = set()
        while current:
            name: str = current.pop(0)
            if name in seen:
                continue
            seen.add(name)
            cls: ClassContract | None = self.classes.get(name)
            if cls is None:
                continue
            if name != owner:
                variants: tuple[CallableContract, ...] = self.variants(
                    qualified_name=(f"{name}.{method}"),
                )
                if variants:
                    return variants[-1]
            current.extend(cls.bases)
        return None

    @staticmethod
    def _class(*, node: ClassDef) -> ClassContract:
        """Extract inheritance, field declarations and method signatures.

        Args:
            node: The node examined while extract inheritance, field
                declarations and method signatures.

        Returns:
            ClassContract produced by this operation.

        """
        bases: tuple[str, ...] = tuple(
            _qualified(node=base) for base in node.bases
        )
        short_bases: frozenset[str] = frozenset(
            item.split(sep=".")[-1] for item in bases
        )
        decorators: frozenset[str] = frozenset(
            _decorator_name(node=item).split(sep=".")[-1]
            for item in node.decorator_list
        )
        is_dataclass: bool = "dataclass" in decorators
        is_enum: bool = bool(
            short_bases & {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"},
        )
        is_protocol: bool = "Protocol" in short_bases
        is_typed_dict: bool = "TypedDict" in short_bases
        is_named_tuple: bool = "NamedTuple" in short_bases
        class_kw_only: bool = any(
            isinstance(item, Call)
            and _decorator_name(node=item).split(sep=".")[-1] == "dataclass"
            and any(
                option.arg == "kw_only"
                and isinstance(option.value, Constant)
                and (option.value.value is True)
                for option in item.keywords
            )
            for item in node.decorator_list
        )
        total: bool = not any(
            option.arg == "total"
            and isinstance(option.value, Constant)
            and (option.value.value is False)
            for option in node.keywords
        )
        members: list[tuple[str, TypeExpression]] = []
        methods: list[CallableContract] = []
        fields: list[FieldContract] = []
        for item in node.body:
            if isinstance(item, AnnAssign) and isinstance(item.target, Name):
                hint: TypeExpression = TypeExpressionCodec.from_ast(
                    node=item.annotation,
                )
                root_name: str = hint.name.split(sep=".")[-1]
                field_call: Call | None = (
                    item.value
                    if isinstance(item.value, Call)
                    and _decorator_name(node=item.value).split(sep=".")[-1]
                    == "field"
                    else None
                )
                options: dict[str, AST] = (
                    {
                        option.arg: option.value
                        for option in field_call.keywords
                        if option.arg is not None
                    }
                    if field_call is not None
                    else {}
                )
                explicit_init: AST | None = options.get("init")
                explicit_kw_only: AST | None = options.get("kw_only")
                default_value: AST | None = (
                    options.get("default")
                    if field_call is not None
                    else item.value
                )
                factory: AST | None = options.get("default_factory")
                is_classvar: bool = root_name == "ClassVar"
                is_initvar: bool = root_name == "InitVar"
                bare_hint: TypeExpression = (
                    hint.arguments[0]
                    if root_name
                    in (
                        "ClassVar",
                        "InitVar",
                        "Required",
                        "NotRequired",
                        "ReadOnly",
                    )
                    and hint.arguments
                    else hint
                )
                optional: bool = root_name == "NotRequired" or (
                    is_typed_dict and (not total) and (root_name != "Required")
                )
                fields.append(
                    FieldContract(
                        name=item.target.id,
                        annotation=bare_hint,
                        source=item,
                        default=default_value,
                        factory=factory,
                        init=not is_classvar
                        and (
                            not (
                                isinstance(explicit_init, Constant)
                                and explicit_init.value is False
                            )
                        ),
                        kw_only=explicit_kw_only.value is True
                        if isinstance(explicit_kw_only, Constant)
                        else class_kw_only,
                        class_variable=is_classvar,
                        init_variable=is_initvar,
                        optional=optional,
                    ),
                )
                if not is_initvar:
                    members.append((item.target.id, bare_hint))
            elif isinstance(item, Assign) and is_enum:
                members.extend(
                    (target.id, TypeExpression(name=node.name))
                    for target in item.targets
                    if isinstance(target, Name)
                    and (not target.id.startswith("_"))
                )
            elif isinstance(item, (FunctionDef, AsyncFunctionDef)):
                method_decorators: frozenset[str] = frozenset(
                    _decorator_name(node=d).split(sep=".")[-1]
                    for d in item.decorator_list
                )
                kind: str = (
                    "static"
                    if "staticmethod" in method_decorators
                    else "class"
                    if "classmethod" in method_decorators
                    else "property"
                    if "property" in method_decorators
                    else "instance"
                )
                methods.append(
                    function_contract(
                        node=item,
                        qualified_name=(f"{node.name}.{item.name}"),
                        method_kind=kind,
                    ),
                )
        return ClassContract(
            name=node.name,
            bases=bases,
            members=tuple(members),
            methods=tuple(methods),
            node=node,
            fields=tuple(fields),
            is_protocol=is_protocol,
            is_dataclass=is_dataclass,
            is_enum=is_enum,
            is_typed_dict=is_typed_dict,
            is_named_tuple=is_named_tuple,
            type_parameters=_type_parameters(node=node),
        )

    def _validate_overrides(self) -> tuple[ContractDiagnostic, ...]:
        """Verify source-known override parameter and result variance.

        Returns:
            tuple[ContractDiagnostic, ...] produced by this operation.

        """
        diagnostics: list[ContractDiagnostic] = []
        for cls in self.classes.values():
            diagnostics.extend(self._final_base_diagnostics(_cls=cls))
            diagnostics.extend(self._method_diagnostics(_cls=cls))
        return tuple(diagnostics)

    def _final_base_diagnostics(
        self,
        *,
        _cls: ClassContract,
    ) -> tuple[ContractDiagnostic, ...]:
        """Flag inheritance from a source class marked as final.

        Args:
            _cls: The class contract to check.

        Returns:
            tuple[ContractDiagnostic, ...] produced by this operation.

        """
        diagnostics: list[ContractDiagnostic] = []
        for base in _cls.bases:
            parent_class: ClassContract | None = self.classes.get(base)
            if parent_class is not None and any(
                _decorator_name(node=d).split(sep=".")[-1] == "final"
                for d in parent_class.node.decorator_list
            ):
                diagnostics.append(
                    ContractDiagnostic(
                        code="final_class_inherited",
                        description=(
                            f"{_cls.name} cannot subclass final class {base}"
                        ),
                        node=_cls.node,
                    ),
                )
        return tuple(diagnostics)

    def _method_diagnostics(
        self,
        *,
        _cls: ClassContract,
    ) -> tuple[ContractDiagnostic, ...]:
        """Check one class's methods against inherited contracts.

        Args:
            _cls: The class contract to check.

        Returns:
            tuple[ContractDiagnostic, ...] produced by this operation.

        """
        diagnostics: list[ContractDiagnostic] = []
        for method in _cls.methods:
            source: AST | None = method.declaration
            if not isinstance(source, (FunctionDef, AsyncFunctionDef)):
                continue
            decorators: frozenset[str] = frozenset(
                _decorator_name(node=d).split(sep=".")[-1]
                for d in source.decorator_list
            )
            marked: bool = "override" in decorators
            parent: CallableContract | None = self.inherited_method(
                owner=_cls.name,
                method=source.name,
            )
            if parent is None:
                if marked and all(base in self.classes for base in _cls.bases):
                    diagnostics.append(
                        ContractDiagnostic(
                            code="override_missing",
                            description=(
                                f"{method.qualified_name}"
                                f" does not override a known inherited method"
                            ),
                            node=source,
                        ),
                    )
                continue
            if isinstance(
                parent.declaration,
                (FunctionDef, AsyncFunctionDef),
            ) and any(
                _decorator_name(node=d).split(sep=".")[-1] == "final"
                for d in parent.declaration.decorator_list
            ):
                diagnostics.append(
                    ContractDiagnostic(
                        code="final_method_overridden",
                        description=(
                            f"{method.qualified_name} "
                            "overrides final inherited method"
                        ),
                        node=source,
                    ),
                )
            relation: Compatibility = method_compatible(
                implementation=method,
                inherited=parent,
                index=self,
            )
            if relation.compatible is False:
                diagnostics.append(
                    ContractDiagnostic(
                        code="override_incompatible",
                        description=(
                            f"{method.qualified_name}: "
                            f"{', '.join(relation.evidence)}"
                        ),
                        node=source,
                    ),
                )
            elif relation.compatible is None and marked:
                diagnostics.append(
                    ContractDiagnostic(
                        code="override_unresolved",
                        description=(
                            f"{method.qualified_name}: "
                            f"{', '.join(relation.evidence)}"
                        ),
                        node=source,
                    ),
                )
        return tuple(diagnostics)
