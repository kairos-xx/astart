"""Return types that follow from the syntax alone."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
type Function = ast.FunctionDef | ast.AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        numeric: Grouped module constant.
        call_types: Grouped module constant.
        constant_types: Grouped module constant.
        scope_nodes: Grouped module constant.

    """

    numeric: Final[frozenset[str]] = frozenset({"bool", "int", "float"})
    call_types: Final[dict[str, str]] = {
        "bool": "bool",
        "chr": "str",
        "float": "float",
        "int": "int",
        "len": "int",
        "ord": "int",
        "repr": "str",
        "str": "str",
    }
    constant_types: Final[frozenset[str]] = frozenset(
        {"bool", "bytes", "float", "int", "str"},
    )
    scope_nodes: Final[tuple[type[ast.AST], ...]] = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Lambda,
    )


def _own_nodes(*, function: Function) -> Iterator[ast.AST]:
    """Walk a function body without entering nested scopes.

    Args:
        function: Function definition.

    Yields:
        Every node that belongs to the function itself.

    """
    stack: list[ast.AST] = [
        statement
        for statement in reversed(function.body)
        if not isinstance(statement, Constants.scope_nodes)
    ]
    while stack:
        node: ast.AST = stack.pop()
        yield node
        stack.extend(
            child
            for child in reversed(list(ast.iter_child_nodes(node=node)))
            if not isinstance(child, Constants.scope_nodes)
        )


@final
class _Typer:
    """Type expressions whose type the syntax determines."""

    def __init__(
        self,
        *,
        env: dict[str, str],
        counts: Mapping[str, int],
    ) -> None:
        """Store the typing environment.

        Args:
            env: Known types of names (typed parameters and locals).
            counts: Module binding counts, to detect shadowed builtins.

        """
        self.env: dict[str, str] = env
        self._counts: Mapping[str, int] = counts
        self._handlers: dict[
            type[ast.AST],
            Callable[[ast.AST], str | None],
        ] = {
            ast.Constant: self._constant,
            ast.JoinedStr: self._joined,
            ast.Name: self._name,
            ast.UnaryOp: self._unary,
            ast.Compare: self._compare,
            ast.BoolOp: self._boolop,
            ast.IfExp: self._ifexp,
            ast.BinOp: self._binop,
            ast.Call: self._call,
            ast.List: self._list,
            ast.Set: self._set,
            ast.Tuple: self._tuple,
            ast.Dict: self._dict,
        }

    def type_of(self, node: ast.AST) -> str | None:
        """Return the provable type of an expression.

        Args:
            node: Expression.

        Returns:
            The annotation source, or ``None`` when it is not provable.

        """
        for kind, handler in self._handlers.items():
            if isinstance(node, kind):
                return handler(node)
        return None

    @staticmethod
    def _constant(node: ast.AST) -> str | None:
        """Type a literal.

        Args:
            node: Expression.

        Returns:
            The literal's type name, or ``None``.

        """
        if not isinstance(node, ast.Constant):
            return None
        if node.value is None:
            return "None"
        name: str = type(node.value).__name__
        return name if name in Constants.constant_types else None

    @staticmethod
    def _joined(_node: ast.AST) -> str | None:
        """Type an f-string.

        Args:
            _node: Expression.

        Returns:
            Always ``"str"``.

        """
        return "str"

    @staticmethod
    def _numeric(*, op: ast.operator, left: str, right: str) -> str | None:
        """Type arithmetic on numbers.

        Args:
            op: Operator.
            left: Left operand type.
            right: Right operand type.

        Returns:
            ``"float"`` or ``"int"``, or ``None`` for other operators.

        """
        if isinstance(op, ast.Div):
            return "float"
        if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
            return "float" if "float" in {left, right} else "int"
        return None

    def _same(self, nodes: list[ast.expr]) -> str | None:
        """Return the shared type of several expressions.

        Args:
            nodes: Expressions.

        Returns:
            The common type, or ``None``.

        """
        types: set[str | None] = {self.type_of(node=item) for item in nodes}
        return types.pop() if len(types) == 1 else None

    def _name(self, node: ast.AST) -> str | None:
        """Type a name from the environment.

        Args:
            node: Expression.

        Returns:
            The known type, or ``None``.

        """
        return self.env.get(node.id) if isinstance(node, ast.Name) else None

    def _unary(self, node: ast.AST) -> str | None:
        """Type ``not x`` and numeric signs.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, ast.UnaryOp):
            return None
        if isinstance(node.op, ast.Not):
            return "bool"
        found: str | None = self.type_of(node=node.operand)
        if found in {"bool", "int"}:
            return "int"
        if found == "float" and (not isinstance(node.op, ast.Invert)):
            return "float"
        return None

    def _compare(self, node: ast.AST) -> str | None:
        """Type a comparison when every operand has a known type.

        Args:
            node: Expression.

        Returns:
            ``"bool"`` or ``None``.

        """
        if not isinstance(node, ast.Compare):
            return None
        operands: list[ast.expr] = [node.left, *node.comparators]
        known: bool = all(
            self.type_of(node=item) is not None for item in operands
        )
        return "bool" if known else None

    def _boolop(self, node: ast.AST) -> str | None:
        """Type ``and`` / ``or`` when every operand has one type.

        Args:
            node: Expression.

        Returns:
            The shared type, or ``None``.

        """
        return (
            self._same(nodes=node.values)
            if isinstance(node, ast.BoolOp)
            else None
        )

    def _ifexp(self, node: ast.AST) -> str | None:
        """Type a conditional expression with equally typed branches.

        Args:
            node: Expression.

        Returns:
            The shared type, or ``None``.

        """
        if not isinstance(node, ast.IfExp):
            return None
        return self._same(nodes=[node.body, node.orelse])

    def _call(self, node: ast.AST) -> str | None:
        """Type calls of builtin constructors that are not shadowed.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, ast.Call) or not isinstance(
            node.func,
            ast.Name,
        ):
            return None
        name: str = node.func.id
        if self._counts.get(name, 0) != 0:
            return None
        return Constants.call_types.get(name)

    def _binop(self, node: ast.AST) -> str | None:
        """Type arithmetic and string operations on known scalars.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, ast.BinOp):
            return None
        left: str | None = self.type_of(node=node.left)
        right: str | None = self.type_of(node=node.right)
        if left in Constants.numeric and right in Constants.numeric:
            return self._numeric(op=node.op, left=left, right=right)
        if left == "str" and right == "str" and isinstance(node.op, ast.Add):
            return "str"
        repeats: bool = isinstance(node.op, ast.Mult) and {left, right} <= {
            "str",
            "int",
            "bool",
        }
        return "str" if repeats and "str" in {left, right} else None

    def _list(self, node: ast.AST) -> str | None:
        """Type a list display of equally typed items.

        Args:
            node: Expression.

        Returns:
            The list type, or ``None``.

        """
        return self._sequence(kind="list", node=node)

    def _set(self, node: ast.AST) -> str | None:
        """Type a set display of equally typed items.

        Args:
            node: Expression.

        Returns:
            The set type, or ``None``.

        """
        return self._sequence(kind="set", node=node)

    def _sequence(self, *, kind: str, node: ast.AST) -> str | None:
        """Type a list or set display.

        Args:
            kind: Container name.
            node: Expression.

        Returns:
            The container type, or ``None`` for empty or mixed displays.

        """
        if not isinstance(node, (ast.List, ast.Set)) or not node.elts:
            return None
        item: str | None = self._same(nodes=node.elts)
        return None if item is None else f"{kind}[{item}]"

    def _tuple(self, node: ast.AST) -> str | None:
        """Type a tuple display of known items.

        Args:
            node: Expression.

        Returns:
            The tuple type, or ``None``.

        """
        if not isinstance(node, ast.Tuple) or not node.elts:
            return None
        parts: list[str | None] = [self.type_of(node=e) for e in node.elts]
        known: list[str] = [part for part in parts if part is not None]
        if len(known) != len(parts):
            return None
        return f"tuple[{', '.join(known)}]"

    def _dict(self, node: ast.AST) -> str | None:
        """Type a dict display of equally typed keys and values.

        Args:
            node: Expression.

        Returns:
            The dict type, or ``None``.

        """
        if not isinstance(node, ast.Dict) or not node.keys:
            return None
        keys: list[ast.expr] = [k for k in node.keys if k is not None]
        if len(keys) != len(node.keys):
            return None
        key_type: str | None = self._same(nodes=keys)
        value_type: str | None = self._same(nodes=node.values)
        if key_type is None or value_type is None:
            return None
        return f"dict[{key_type}, {value_type}]"


def can_fall_off(*, body: list[ast.stmt]) -> bool:
    """Report whether control can reach the end of a statement list.

    Args:
        body: Statements.

    Returns:
        Whether execution may continue after the last statement.

    """
    if not body:
        return True
    last: ast.stmt = body[-1]
    match last:
        case ast.Return() | ast.Raise():
            return False
        case ast.If(body=then, orelse=otherwise):
            return (
                not otherwise
                or can_fall_off(body=then)
                or can_fall_off(body=otherwise)
            )
        case ast.With(body=inner) | ast.AsyncWith(body=inner):
            return can_fall_off(body=inner)
        case _:
            return True


def _single_assignments(*, function: Function) -> dict[str, int]:
    """Count how often each name is stored in a function.

    Args:
        function: Function definition.

    Returns:
        Store counts by name.

    """
    counts: dict[str, int] = {}
    for node in _own_nodes(function=function):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            counts[node.id] = counts.get(node.id, 0) + 1
    return counts


def expression_type(*, node: ast.AST, counts: Mapping[str, int]) -> str | None:
    """Prove the type of a single expression without any name context.

    Args:
        node: Expression.
        counts: Module binding counts.

    Returns:
        The annotation source, or ``None`` when it is not provable.

    """
    return _Typer(env={}, counts=counts).type_of(node=node)


def _declared_elsewhere(*, function: Function) -> frozenset[str]:
    """Collect names that ``global`` or ``nonlocal`` lets other code rebind.

    Args:
        function: Function definition.

    Returns:
        Names declared ``global`` or ``nonlocal`` anywhere in the function,
        including nested functions.

    """
    names: set[str] = set()
    for node in ast.walk(node=function):
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
    return frozenset(names)


def provable_return(
    *,
    function: Function,
    known_types: Mapping[str, str],
    counts: Mapping[str, int],
) -> str | None:
    """Prove a function's return annotation from its body.

    Every returned expression must have a type the syntax determines, using
    literals, operators, builtin constructors and typed parameters or
    single-assignment locals. Paths that fall off the end add ``None``.

    Args:
        function: Function definition.
        known_types: Types of parameters (accepted hints or annotations).
        counts: Module binding counts.

    Returns:
        The annotation source, or ``None`` when it is not provable.

    """
    rebound: frozenset[str] = _declared_elsewhere(function=function)
    typer: _Typer = _Typer(
        env={k: v for k, v in known_types.items() if k not in rebound},
        counts=counts,
    )
    stored: dict[str, int] = _single_assignments(function=function)
    for node in _own_nodes(function=function):
        match node:
            case ast.Assign(targets=[ast.Name(id=name)], value=value) if (
                stored.get(name) == 1
                and name not in known_types
                and (name not in rebound)
            ):
                found: str | None = typer.type_of(node=value)
                if found is not None:
                    typer.env[name] = found
            case _:
                continue
    types: list[str] = []
    for node in _own_nodes(function=function):
        if not isinstance(node, ast.Return):
            continue
        result: str | None = (
            "None" if node.value is None else typer.type_of(node=node.value)
        )
        if result is None:
            return None
        types.append(result)
    if can_fall_off(body=function.body):
        types.append("None")
    unique: list[str] = list(dict.fromkeys(types))
    others: list[str] = [item for item in unique if item != "None"]
    if len(unique) == 1:
        return unique[0]
    if "None" in unique and len(others) == 1:
        return f"{others[0]} | None"
    return None
