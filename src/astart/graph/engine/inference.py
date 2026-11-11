"""Sound, evidence-based inference passes for the from-scratch engine.

The engine annotates parameters, return types, and instance attributes using
direct evidence (literals, operators, method calls, known returns). When the
evidence is insufficient it falls back to ``object`` so the emitted source is
always internally consistent under a strict type checker.

"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    AsyncFunctionDef,
    Attribute,
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
    FloorDiv,
    FunctionDef,
    GeneratorExp,
    IfExp,
    List,
    ListComp,
    LShift,
    Mod,
    Mult,
    Name,
    Not,
    Pow,
    Return,
    RShift,
    Set,
    SetComp,
    Starred,
    Sub,
    Tuple,
    UnaryOp,
    arg,
    expr,
    operator,
    stmt,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, cast, final

from astart.graph.engine import types
from astart.graph.graph.semantics import child_nodes

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import EllipsisType


@final
class Constants:
    """Group module-level constants.

    Attributes:
        arithmetic_ops (Final[tuple[type[operator], ...]]): Grouped module
            constant.
        str_methods (Final[frozenset[str]]): Grouped module constant.
        scalar_types (Final[tuple[tuple[type, str], ...]]): Grouped module
            constant.
        builtin_call_returns (Final[dict[str, str]]): Grouped module constant.

    """

    arithmetic_ops: Final[tuple[type[operator], ...]] = (
        Add,
        Sub,
        Mult,
        FloorDiv,
        Mod,
        Pow,
        LShift,
        RShift,
        BitOr,
        BitAnd,
        BitXor,
    )
    str_methods: Final[frozenset[str]] = frozenset(
        {"upper", "lower", "strip", "lstrip", "rstrip", "title", "capitalize"},
    )
    scalar_types: Final[tuple[tuple[type, str], ...]] = (
        (bool, types.Constants.bool),
        (int, types.Constants.int),
        (float, types.Constants.float),
        (str, types.Constants.str),
        (bytes, types.Constants.bytes),
    )
    builtin_call_returns: Final[dict[str, str]] = {
        "int": types.Constants.int,
        "float": types.Constants.float,
        "str": types.Constants.str,
        "bool": types.Constants.bool,
        "bytes": types.Constants.bytes,
        "len": types.Constants.int,
        "abs": types.Constants.int,
        "repr": types.Constants.str,
        "hash": types.Constants.int,
        "ord": types.Constants.int,
        "sorted": "list[object]",
        "list": "list[object]",
        "dict": "dict[object, object]",
        "set": "set[object]",
        "tuple": "tuple[object, ...]",
        "range": "range",
        "enumerate": "enumerate[object]",
        "zip": "zip[object, ...]",
        "map": "map[object, object]",
        "filter": "filter[object, object]",
        "sum": types.Constants.int,
        "max": types.Constants.object,
        "min": types.Constants.object,
        "any": types.Constants.bool,
        "all": types.Constants.bool,
        "isinstance": types.Constants.bool,
        "issubclass": types.Constants.bool,
        "type": "type[object]",
    }


type _FunctionDef = FunctionDef | AsyncFunctionDef
type Scope = dict[str, str]


def constant_type(
    *,
    value: str | bytes | complex | bool | None | EllipsisType,
) -> str:
    """Return the type source for a literal constant value.

    Args:
        value (str | bytes | complex | bool | None | EllipsisType): The value
            examined while return the type
            source for a literal constant value.

    Returns:
        str: Rendered source text produced by this operation.

    """
    if value is None:
        return types.Constants.none
    for python_type, source in Constants.scalar_types:
        if isinstance(value, python_type):
            return source
    return types.Constants.object


@dataclass(slots=True)
class ModuleFacts:
    """Module-wide signatures used to resolve calls and constructions.

    Attributes:
        class_names (set[str]): Class names retained as set[str] by this
            instance.
        function_params (dict[str, list[str]]): Function params retained as
            dict[str, list[str]] by this instance.
        function_returns (Scope): Function returns retained as dict[str, str]
            by this instance.

    """

    function_returns: Scope = field(default_factory=dict)
    function_params: dict[str, list[str]] = field(default_factory=dict)
    class_names: set[str] = field(default_factory=set)


class ExpressionInferer:
    """Infer a type-source string for an expression within a scope."""

    def __init__(self, *, facts: ModuleFacts) -> None:
        """Store module facts and build the per-node-type handler table.

        Args:
            facts (ModuleFacts): Facts supplied as ModuleFacts for this
                operation.

        """
        self.facts: ModuleFacts = facts
        self._handlers: dict[type[expr], Callable[[expr, Scope], str]] = {
            Constant: self._constant,
            Name: self._name,
            Attribute: self._attribute,
            BoolOp: _bool,
            Compare: _bool,
            UnaryOp: self._unary,
            BinOp: self._binop,
            IfExp: self._ifexp,
            List: self._list,
            Set: self._set,
            Tuple: self._tuple,
            Dict: self._dict,
            ListComp: self._listcomp,
            SetComp: self._setcomp,
            DictComp: _dict_comp,
            GeneratorExp: self._generatorexp,
            Call: self._call,
        }

    def infer(self, *, node: expr, scope: Scope) -> str:
        """Return the inferred type source for ``node`` within ``scope``.

        Args:
            node (expr): The node examined while return the inferred
                type source for ``node`` within ``scope``.
            scope (Scope): The scope examined while return the inferred
                type source for ``node`` within ``scope``.

        Returns:
            str: Rendered source text produced by this operation.

        """
        handler: Callable[[expr, Scope], str] | None = self._handlers.get(
            type(node),
        )
        return (
            types.Constants.object if handler is None else handler(node, scope)
        )

    @staticmethod
    def _constant(node: expr, _scope: Scope) -> str:
        """Constant.

        Args:
            _scope (Scope): Scope provided to this handler.
            node (expr): AST node being inspected or transformed.

        Returns:
            str: Inferred type representation for the expression.

        """
        return constant_type(value=cast(typ="Constant", val=node).value)

    @staticmethod
    def _name(node: expr, scope: Scope) -> str:
        """Name.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        return scope.get(cast(typ="Name", val=node).id, types.Constants.object)

    @staticmethod
    def _attribute(node: expr, scope: Scope) -> str:
        """Attribute.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        path: str | None = _attr_path(node=cast(typ="Attribute", val=node))
        return scope.get(path or "", types.Constants.object)

    def _unary(self, node: expr, scope: Scope) -> str:
        """Unary.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        unary: UnaryOp = cast(typ="UnaryOp", val=node)
        if isinstance(unary.op, Not):
            return types.Constants.bool
        return self.infer(node=unary.operand, scope=scope)

    def _ifexp(self, node: expr, scope: Scope) -> str:
        """Ifexp.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        ifexp: IfExp = cast(typ="IfExp", val=node)
        return types.union(
            self.infer(node=ifexp.body, scope=scope),
            self.infer(node=ifexp.orelse, scope=scope),
        )

    def _binop(self, node: expr, scope: Scope) -> str:
        """Binop.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        binop: BinOp = cast(typ="BinOp", val=node)
        left: str = self.infer(node=binop.left, scope=scope)
        right: str = self.infer(node=binop.right, scope=scope)
        pair: set[str] = {left, right}
        if types.Constants.str in pair and isinstance(binop.op, Add | Mod):
            return types.Constants.str
        if types.Constants.float in pair:
            return types.Constants.float
        if pair <= {types.Constants.int, types.Constants.bool}:
            return types.Constants.int
        if left == right and left in {
            types.Constants.int,
            types.Constants.str,
            types.Constants.bytes,
        }:
            return left
        return types.Constants.object

    def _list(self, node: expr, scope: Scope) -> str:
        """List.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        elements: str = self._elements(
            nodes=cast(typ="List", val=node).elts,
            scope=scope,
        )
        return f"list[{elements}]"

    def _set(self, node: expr, scope: Scope) -> str:
        """Set.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        elements: str = self._elements(
            nodes=cast(typ="Set", val=node).elts,
            scope=scope,
        )
        return f"set[{elements}]"

    def _listcomp(self, node: expr, scope: Scope) -> str:
        """Listcomp.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        element: str = self.infer(
            node=cast(typ="ListComp", val=node).elt,
            scope=scope,
        )
        return f"list[{element}]"

    def _setcomp(self, node: expr, scope: Scope) -> str:
        """Setcomp.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        element: str = self.infer(
            node=cast(typ="SetComp", val=node).elt,
            scope=scope,
        )
        return f"set[{element}]"

    def _generatorexp(self, node: expr, scope: Scope) -> str:
        """Generatorexp.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Result of the operation, according to the declared return
                type.

        """
        gen: GeneratorExp = cast(typ="GeneratorExp", val=node)
        element: str = self.infer(node=gen.elt, scope=scope)
        return f"Generator[{element}, None, None]"

    def _tuple(self, node: expr, scope: Scope) -> str:
        """Tuple.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        elts: list[expr] = cast(typ="Tuple", val=node).elts
        if any(isinstance(element, Starred) for element in elts):
            return f"tuple[{self._elements(nodes=elts, scope=scope)}, ...]"
        if not elts:
            return "tuple[()]"
        parts: str = ", ".join(
            self.infer(node=element, scope=scope) for element in elts
        )
        return f"tuple[{parts}]"

    def _dict(self, node: expr, scope: Scope) -> str:
        """Infer the type of a dict display.

        Args:
            node (expr): AST node being inspected or transformed.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        mapping: Dict = cast(typ="Dict", val=node)
        keys: list[expr] = [k for k in mapping.keys if k is not None]
        key: str = types.union(
            *(self.infer(node=k, scope=scope) for k in keys),
        )
        value: str = types.union(
            *(self.infer(node=v, scope=scope) for v in mapping.values),
        )
        return f"dict[{key}, {value}]"

    def _elements(self, *, nodes: list[expr], scope: Scope) -> str:
        """Elements.

        Args:
            nodes (list[expr]): AST expressions to infer and combine.
            scope (Scope): Lexical scope containing the expression.

        Returns:
            str: Inferred type representation for the expression.

        """
        inferred: list[str] = [
            self.infer(node=element, scope=scope)
            for element in nodes
            if not isinstance(element, Starred)
        ]
        return types.union(*inferred) if inferred else types.Constants.object

    def _call(self, node: expr, _scope: Scope) -> str:
        """Call.

        Args:
            _scope (Scope): Scope provided to this handler.
            node (expr): AST node being inspected or transformed.

        Returns:
            str: Parsed annotation expression.

        """
        name: str | None = _callable_name(node=cast(typ="Call", val=node).func)
        if name is None:
            return types.Constants.object
        builtin: str | None = Constants.builtin_call_returns.get(name)
        if builtin is not None:
            return builtin
        if name in self.facts.class_names:
            return name
        return self.facts.function_returns.get(name, types.Constants.object)


def _bool(_node: expr, _scope: Scope) -> str:
    """Bool.

    Args:
        _node (expr): Expression provided to this handler.
        _scope (Scope): Scope provided to this handler.

    Returns:
        str: Inferred type representation for the expression.

    """
    return types.Constants.bool


def _dict_comp(_node: expr, _scope: Scope) -> str:
    """Infer the type of a dict comprehension.

    Args:
        _node (expr): Expression provided to this handler.
        _scope (Scope): Scope provided to this handler.

    Returns:
        str: Inferred type representation for the expression.

    """
    return "dict[object, object]"


class ParameterInferer:
    """Infer a parameter type from its default and how it is used."""

    def infer(
        self,
        *,
        parameter: arg,
        default: expr | None,
        body: list[stmt],
    ) -> str:
        """Return the inferred type source for one parameter.

        Args:
            body (list[stmt]): Body supplied as list[stmt] for this operation.
            default (expr | None): Default supplied as expr | None for this
                operation.
            parameter (arg): Parameter supplied as arg for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        usage: str = self._usage_type(name=parameter.arg, body=body)
        default_type: str | None = self._default_type(default=default)
        if default_type == types.Constants.none:
            if usage == types.Constants.object:
                return types.Constants.object
            return types.optional(source=usage)
        if usage != types.Constants.object:
            return usage
        if default_type is not None:
            return default_type
        return types.Constants.object

    @staticmethod
    def _default_type(*, default: expr | None) -> str | None:
        """Infer the type of a default-value expression.

        Args:
            default (expr | None): Default-value expression used for type
                inference.

        Returns:
            str | None:
                Result of the operation, according to the declared return type.

        """
        if isinstance(default, Constant):
            return constant_type(value=default.value)
        return None

    @staticmethod
    def _evidence(*, name: str, node: AST) -> set[str]:
        """Evidence.

        Args:
            name (str): Identifier used for lookup or matching.
            node (AST): AST node being inspected or transformed.

        Returns:
            set[str]: Result of the operation, according to the declared return
                type.

        """
        if (
            isinstance(node, BinOp)
            and isinstance(node.op, Constants.arithmetic_ops)
            and (
                _is_name(node=node.left, name=name)
                or _is_name(node=node.right, name=name)
            )
        ):
            return {types.Constants.int}
        if (
            isinstance(node, Call)
            and isinstance(node.func, Attribute)
            and _is_name(node=node.func.value, name=name)
            and (node.func.attr in Constants.str_methods)
        ):
            return {types.Constants.str}
        return set()

    def _usage_type(self, *, name: str, body: list[stmt]) -> str:
        """Usage type.

        Args:
            body (list[stmt]): Statements to analyze in execution order.
            name (str): Identifier used for lookup or matching.

        Returns:
            str: Result of the operation, according to the declared return
                type.

        """
        evidence: set[str] = set()
        for node in _walk_local(nodes=body):
            evidence |= self._evidence(name=name, node=node)
        if types.Constants.str in evidence:
            return types.Constants.str
        if types.Constants.int in evidence:
            return types.Constants.int
        return types.Constants.object


class ReturnInferer:
    """Infer a function return type from its return statements."""

    def __init__(self, *, inferer: ExpressionInferer) -> None:
        """Store the expression inferer used for return values.

        Args:
            inferer (ExpressionInferer): Inferer supplied as ExpressionInferer
                for this operation.

        """
        self.inferer: ExpressionInferer = inferer

    def infer(self, *, function: _FunctionDef, scope: Scope) -> str:
        """Return the inferred return-type source for ``function``.

        Args:
            function (_FunctionDef): The function examined while return the
                inferred return-type source for ``function``.
            scope (Scope): The scope examined while return the inferred
                return-type source for ``function``.

        Returns:
            str: Rendered source text produced by this operation.

        """
        returns: list[str] = []
        saw_value: bool = False
        for node in _walk_local(nodes=function.body):
            if not isinstance(node, Return):
                continue
            if node.value is None:
                returns.append(types.Constants.none)
            else:
                saw_value = True
                returns.append(
                    self.inferer.infer(node=node.value, scope=scope),
                )
        if not saw_value:
            return types.Constants.none
        return types.union(*returns)


def _attr_path(*, node: Attribute) -> str | None:
    """Attr path.

    Args:
        node (Attribute): AST node being inspected or transformed.

    Returns:
        str | None:
            Result of the operation, according to the declared return type.

    """
    if isinstance(node.value, Name):
        return f"{node.value.id}.{node.attr}"
    return None


def _callable_name(*, node: expr) -> str | None:
    """Callable name.

    Args:
        node (expr): AST node being inspected or transformed.

    Returns:
        str | None:
            Result of the operation, according to the declared return type.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def _is_name(node: expr, name: str) -> bool:
    """Is name.

    Args:
        name (str): Identifier used for lookup or matching.
        node (expr): AST node being inspected or transformed.

    Returns:
        bool: Whether the inspected expression satisfies the condition.

    """
    return isinstance(node, Name) and node.id == name


def _walk_local(*, nodes: list[stmt]) -> list[AST]:
    """Walk statements without descending into nested function/class scopes.

    Args:
        nodes (list[stmt]): Collection of nodes supplied for this operation.

    Returns:
        list[AST]: list[AST] produced by this operation.

    """
    result: list[AST] = []
    stack: list[AST] = [
        node
        for node in nodes
        if not isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef))
    ]
    while stack:
        node: AST = stack.pop()
        result.append(node)
        stack.extend(
            child
            for child in child_nodes(node=node)
            if not isinstance(child, (FunctionDef, AsyncFunctionDef, ClassDef))
        )
    return result
