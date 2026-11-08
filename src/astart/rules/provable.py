"""Return types that follow from the syntax alone."""

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
    FloorDiv,
    FunctionDef,
    Global,
    If,
    IfExp,
    Invert,
    JoinedStr,
    Lambda,
    List,
    ListComp,
    Load,
    Mod,
    Module,
    Mult,
    Name,
    Nonlocal,
    Not,
    Raise,
    Return,
    Set,
    SetComp,
    Store,
    Sub,
    Try,
    TryStar,
    Tuple,
    UnaryOp,
    With,
    Yield,
    YieldFrom,
    arg,
    expr,
    iter_child_nodes,
    operator,
    stmt,
    walk,
)
from ast import (
    arguments as ast_arguments,
)
from typing import TYPE_CHECKING, Final, final

from astart.rules.resolve import constructor_key
from astart.rules.scopes import names_bound_by

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        numeric: Grouped module constant.
        call_types: Grouped module constant.
        constant_types: Grouped module constant.
        scalar_annotations: Builtin scalars accepted as plain annotations.
        scope_nodes: Grouped module constant.
        min_bindings: Fewest bindings that make a local worth proving here.
        rebound_rounds: Passes that settle locals whose bindings depend on
            one another.

    """

    rebound_rounds: Final[int] = 4
    min_bindings: Final[int] = 2

    numeric: Final[frozenset[str]] = frozenset({"bool", "int", "float"})
    call_types: Final[dict[str, str]] = {
        "ascii": "str",
        "bin": "str",
        "bool": "bool",
        "callable": "bool",
        "chr": "str",
        "float": "float",
        "format": "str",
        "hasattr": "bool",
        "hash": "int",
        "hex": "str",
        "id": "int",
        "int": "int",
        "isinstance": "bool",
        "issubclass": "bool",
        "len": "int",
        "oct": "str",
        "ord": "int",
        "repr": "str",
        "str": "str",
    }
    constant_types: Final[frozenset[str]] = frozenset(
        {"bool", "bytes", "float", "int", "str"},
    )
    scalar_annotations: Final[frozenset[str]] = frozenset(
        {"bool", "bytes", "float", "int", "str"},
    )
    scope_nodes: Final[tuple[type[AST], ...]] = (
        FunctionDef,
        AsyncFunctionDef,
        ClassDef,
        Lambda,
    )


def own_nodes(*, function: Function) -> Iterator[AST]:
    """Walk a function body without entering nested scopes.

    Args:
        function: Function definition.

    Yields:
        Every node that belongs to the function itself.

    """
    stack: list[AST] = [
        statement
        for statement in reversed(function.body)
        if not isinstance(statement, Constants.scope_nodes)
    ]
    while stack:
        node: AST = stack.pop()
        yield node
        stack.extend(
            child
            for child in reversed(list(iter_child_nodes(node=node)))
            if not isinstance(child, Constants.scope_nodes)
        )


def _bound_names(*, target: AST) -> list[str]:
    """List the names a comprehension target binds.

    Args:
        target: The ``for`` target.

    Returns:
        Every stored name in it.

    """
    return [
        node.id
        for node in walk(node=target)
        if isinstance(node, Name) and isinstance(node.ctx, Store)
    ]


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
        self.reads: int = 0
        self.pure: set[str] = set()
        self._counts: Mapping[str, int] = counts
        self._handlers: dict[
            type[AST],
            Callable[[AST], str | None],
        ] = {
            Constant: self._constant,
            JoinedStr: self._joined,
            Name: self._name,
            Attribute: self._attribute,
            UnaryOp: self._unary,
            Compare: self._compare,
            BoolOp: self._boolop,
            IfExp: self._ifexp,
            BinOp: self._binop,
            Call: self._call,
            List: self._list,
            Set: self._set,
            Tuple: self._tuple,
            Dict: self._dict,
            ListComp: self._comprehension,
            SetComp: self._comprehension,
            DictComp: self._comprehension,
        }

    def type_of(self, node: AST) -> str | None:
        """Return the provable type of an expression.

        Args:
            node: Expression.

        Returns:
            The annotation source, or ``None`` when it is not provable.

        """
        for kind, handler in self._handlers.items():
            if isinstance(node, kind):
                resolved: Callable[[AST], str | None] = handler
                return resolved(node)
        return None

    def _attribute(self, node: AST) -> str | None:
        """Type ``receiver.attr`` from a table entry keyed ``"receiver.attr"``.

        Args:
            node: Expression.

        Returns:
            The recorded type, or ``None`` when the table has none.

        """
        if not (isinstance(node, Attribute) and isinstance(node.value, Name)):
            return None
        found: str | None = self.env.get(f"{node.value.id}.{node.attr}")
        if found is not None:
            self.reads += 1
        return found

    @staticmethod
    def _constant(node: AST) -> str | None:
        """Type a literal.

        Args:
            node: Expression.

        Returns:
            The literal's type name, or ``None``.

        """
        if not isinstance(node, Constant):
            return None
        if node.value is None:
            return "None"
        name: str = type(node.value).__name__
        return name if name in Constants.constant_types else None

    @staticmethod
    def _joined(_node: AST) -> str | None:
        """Type an f-string.

        Args:
            _node: Expression.

        Returns:
            Always ``"str"``.

        """
        return "str"

    @staticmethod
    def _numeric(*, op: operator, left: str, right: str) -> str | None:
        """Type arithmetic on numbers.

        Args:
            op: Operator.
            left: Left operand type.
            right: Right operand type.

        Returns:
            ``"float"`` or ``"int"``, or ``None`` for other operators.

        """
        if isinstance(op, Div):
            return "float"
        if isinstance(op, (Add, Sub, Mult, FloorDiv, Mod)):
            return "float" if "float" in {left, right} else "int"
        if isinstance(op, (BitAnd, BitOr, BitXor)) and "float" not in {
            left,
            right,
        }:
            return "bool" if left == right == "bool" else "int"
        return None

    def _same(self, nodes: list[expr]) -> str | None:
        """Return the shared type of several expressions.

        Args:
            nodes: Expressions.

        Returns:
            The common type, or ``None``.

        """
        types: set[str | None] = {self.type_of(node=item) for item in nodes}
        return types.pop() if len(types) == 1 else None

    def _name(self, node: AST) -> str | None:
        """Type a name from the environment.

        Args:
            node: Expression.

        Returns:
            The known type, or ``None``.

        """
        if not isinstance(node, Name):
            return None
        found: str | None = self.env.get(node.id)
        if found is not None and node.id not in self.pure:
            self.reads += 1
        return found

    def _unary(self, node: AST) -> str | None:
        """Type ``not x`` and numeric signs.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, UnaryOp):
            return None
        if isinstance(node.op, Not):
            return "bool"
        found: str | None = self.type_of(node=node.operand)
        if found in {"bool", "int"}:
            return "int"
        if found == "float" and (not isinstance(node.op, Invert)):
            return "float"
        return None

    def _compare(self, node: AST) -> str | None:
        """Type a comparison when every operand has a known type.

        Args:
            node: Expression.

        Returns:
            ``"bool"`` or ``None``.

        """
        if not isinstance(node, Compare):
            return None
        operands: list[expr] = [node.left, *node.comparators]
        known: bool = all(
            self.type_of(node=item) is not None for item in operands
        )
        return "bool" if known else None

    def _boolop(self, node: AST) -> str | None:
        """Type ``and`` / ``or`` when every operand has one type.

        Args:
            node: Expression.

        Returns:
            The shared type, or ``None``.

        """
        return (
            self._same(nodes=node.values) if isinstance(node, BoolOp) else None
        )

    def _ifexp(self, node: AST) -> str | None:
        """Type a conditional expression with equally typed branches.

        Args:
            node: Expression.

        Returns:
            The shared type, or ``None``.

        """
        if not isinstance(node, IfExp):
            return None
        return self._same(nodes=[node.body, node.orelse])

    def _call(self, node: AST) -> str | None:
        """Type calls of builtin constructors that are not shadowed.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, Call) or not isinstance(
            node.func,
            Name,
        ):
            return None
        name: str = node.func.id
        if self._counts.get(constructor_key(name=name)):
            return name
        if self._counts.get(name, 0) != 0:
            return None
        return Constants.call_types.get(name)

    def _binop(self, node: AST) -> str | None:
        """Type arithmetic and string operations on known scalars.

        Args:
            node: Expression.

        Returns:
            The result type, or ``None``.

        """
        if not isinstance(node, BinOp):
            return None
        left: str | None = self.type_of(node=node.left)
        right: str | None = self.type_of(node=node.right)
        if (
            left is not None
            and right is not None
            and left in Constants.numeric
            and right in Constants.numeric
        ):
            return self._numeric(op=node.op, left=left, right=right)
        if left == "str" and right == "str" and isinstance(node.op, Add):
            return "str"
        repeats: bool = isinstance(node.op, Mult) and {left, right} <= {
            "str",
            "int",
            "bool",
        }
        return "str" if repeats and "str" in {left, right} else None

    def _list(self, node: AST) -> str | None:
        """Type a list display of equally typed items.

        Args:
            node: Expression.

        Returns:
            The list type, or ``None``.

        """
        return self._sequence(kind="list", node=node)

    def _set(self, node: AST) -> str | None:
        """Type a set display of equally typed items.

        Args:
            node: Expression.

        Returns:
            The set type, or ``None``.

        """
        return self._sequence(kind="set", node=node)

    def _sequence(self, *, kind: str, node: AST) -> str | None:
        """Type a list or set display.

        Args:
            kind: Container name.
            node: Expression.

        Returns:
            The container type, or ``None`` for empty or mixed displays.

        """
        if not isinstance(node, (List, Set)) or not node.elts:
            return None
        item: str | None = self._same(nodes=node.elts)
        return None if item is None else f"{kind}[{item}]"

    def _tuple(self, node: AST) -> str | None:
        """Type a tuple display of known items.

        Args:
            node: Expression.

        Returns:
            The tuple type, or ``None``.

        """
        if not isinstance(node, Tuple) or not node.elts:
            return None
        parts: list[str | None] = [self.type_of(node=e) for e in node.elts]
        known: list[str] = [part for part in parts if part is not None]
        if len(known) != len(parts):
            return None
        return f"tuple[{', '.join(known)}]"

    def _comprehension(self, node: AST) -> str | None:
        """Type a list, set or dict comprehension from its element types.

        Loop variables are typed only when the iterable fixes them (``range``
        gives ``int``; a typed ``str``, ``list[T]`` or ``set[T]`` gives its
        item). Any other variable hides the outer name it shadows.

        Args:
            node: Expression.

        Returns:
            The container type, or ``None``.

        """
        if not isinstance(node, (ListComp, SetComp, DictComp)):
            return None
        inner: _Typer = _Typer(env=dict(self.env), counts=self._counts)
        inner.pure = set(self.pure)
        for generator in node.generators:
            if generator.is_async:
                return None
            item: str | None = self._item_type(
                typer=inner,
                iterable=generator.iter,
            )
            for name in _bound_names(target=generator.target):
                inner.env.pop(name, None)
                inner.pure.discard(name)
            if isinstance(generator.target, Name) and item is not None:
                inner.env[generator.target.id] = item
                inner.pure.add(generator.target.id)
        if isinstance(node, DictComp):
            key: str | None = inner.type_of(node=node.key)
            value: str | None = inner.type_of(node=node.value)
            shape: str | None = (
                None
                if key is None or value is None
                else f"dict[{key}, {value}]"
            )
        else:
            element: str | None = inner.type_of(node=node.elt)
            kind: str = "list" if isinstance(node, ListComp) else "set"
            shape = None if element is None else f"{kind}[{element}]"
        self.reads += inner.reads
        return shape

    def _item_type(self, *, typer: _Typer, iterable: expr) -> str | None:
        """Give the type iterating an expression yields, when provable.

        Args:
            typer: Typer whose environment sees the comprehension's names.
            iterable: The ``for`` clause's iterable.

        Returns:
            The item type, or ``None``.

        """
        if (
            isinstance(iterable, Call)
            and isinstance(iterable.func, Name)
            and iterable.func.id == "range"
            and self._counts.get("range", 0) == 0
        ):
            return "int"
        whole: str | None = typer.type_of(node=iterable)
        if whole == "str":
            return "str"
        for prefix in ("list[", "set["):
            if whole is not None and whole.startswith(prefix):
                return whole[len(prefix) : -1]
        return None

    def _dict(self, node: AST) -> str | None:
        """Type a dict display of equally typed keys and values.

        Args:
            node: Expression.

        Returns:
            The dict type, or ``None``.

        """
        if not isinstance(node, Dict) or not node.keys:
            return None
        keys: list[expr] = [k for k in node.keys if k is not None]
        if len(keys) != len(node.keys):
            return None
        key_type: str | None = self._same(nodes=keys)
        value_type: str | None = self._same(nodes=node.values)
        if key_type is None or value_type is None:
            return None
        return f"dict[{key_type}, {value_type}]"


def _try_can_fall_off(*, statement: Try | TryStar) -> bool:
    """Report whether control can leave a ``try`` statement normally.

    A ``finally`` block that cannot fall off decides the outcome. Otherwise
    control continues after the statement when the body (followed by the
    ``else`` block) or any handler falls off its end; an exception that no
    handler catches propagates and never reaches the next statement.

    Args:
        statement: The ``try`` statement.

    Returns:
        Whether execution may continue after it.

    """
    if statement.finalbody and not can_fall_off(body=statement.finalbody):
        return False
    normal: bool = can_fall_off(body=statement.body) and (
        can_fall_off(body=statement.orelse) if statement.orelse else True
    )
    return normal or any(
        can_fall_off(body=handler.body) for handler in statement.handlers
    )


def can_fall_off(*, body: list[stmt]) -> bool:
    """Report whether control can reach the end of a statement list.

    Args:
        body: Statements.

    Returns:
        Whether execution may continue after the last statement.

    """
    if not body:
        return True
    last: stmt = body[-1]
    match last:
        case Return() | Raise():
            return False
        case If(body=then, orelse=otherwise):
            return (
                not otherwise
                or can_fall_off(body=then)
                or can_fall_off(body=otherwise)
            )
        case With(body=inner) | AsyncWith(body=inner):
            return can_fall_off(body=inner)
        case Try() | TryStar():
            return _try_can_fall_off(statement=last)
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
    for node in own_nodes(function=function):
        if isinstance(node, Name) and isinstance(node.ctx, Store):
            counts[node.id] = counts.get(node.id, 0) + 1
    return counts


def expression_type(
    *,
    node: AST,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Prove the type of a single expression.

    Args:
        node: Expression.
        counts: Module binding counts.
        env: Types of names visible where the expression is evaluated, from
            :func:`scope_types` and :func:`module_constants`; ``None`` types
            no names.

    Returns:
        The annotation source, or ``None`` when it is not provable.

    """
    return _Typer(env=dict(env or {}), counts=counts).type_of(node=node)


def own_calls(*, function: Function) -> list[Call]:
    """List the calls a function makes itself, outside nested scopes.

    Args:
        function: Function definition.

    Returns:
        Its call expressions.

    """
    return [
        node for node in own_nodes(function=function) if isinstance(node, Call)
    ]


def _annotated_scalar(
    *,
    annotation: AST | None,
    counts: Mapping[str, int],
) -> str | None:
    """Read a plain builtin scalar annotation.

    Args:
        annotation: Annotation expression, if any.
        counts: Module binding counts, to detect shadowed builtins.

    Returns:
        The type name for ``int``, ``str``, ``float``, ``bool`` or
        ``bytes``; otherwise ``None``.

    """
    if (
        isinstance(annotation, Name)
        and annotation.id in Constants.scalar_annotations
        and counts.get(annotation.id, 0) == 0
    ):
        return annotation.id
    return None


def scope_types(
    *,
    function: Function,
    counts: Mapping[str, int],
    constants: Mapping[str, str],
    declared: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Type the names a function can rely on at its call sites.

    Includes module constants, parameters annotated with a builtin scalar, and
    locals assigned exactly once to a provable value. A name that is also
    rebound by ``global``/``nonlocal``, a loop, ``with``, an import, a nested
    definition or a handler is left out.

    Args:
        function: Function definition.
        counts: Module binding counts.
        constants: Types of module-level constants.
        declared: Types already accepted for this function's own
            parameters (hints decided earlier), by parameter name.

    Returns:
        Types by name.

    """
    rebound: frozenset[str] = _declared_elsewhere(function=function)
    env: dict[str, str] = {
        name: found for name, found in constants.items() if name not in rebound
    }
    arguments: ast_arguments = function.args
    parameters: list[arg] = [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
    ]
    for parameter in parameters:
        env.pop(parameter.arg, None)
        found: str | None = _annotated_scalar(
            annotation=parameter.annotation,
            counts=counts,
        )
        if found is None and declared is not None:
            found = declared.get(parameter.arg)
        if found is not None and parameter.arg not in rebound:
            env[parameter.arg] = found
    other: set[str] = {
        name
        for node in own_nodes(function=function)
        if not (isinstance(node, Name) and isinstance(node.ctx, Store))
        for name in names_bound_by(node=node)
    }
    typer: _Typer = _Typer(env=env, counts=counts)
    _type_locals(
        typer=typer,
        function=function,
        fixed=frozenset({*other, *rebound, *(p.arg for p in parameters)}),
    )
    return typer.env


def module_constants(
    *,
    module: Module,
    counts: Mapping[str, int],
) -> dict[str, str]:
    """Type the uppercase module-level constants that are never rebound.

    Args:
        module: Parsed module.
        counts: Module binding counts.

    Returns:
        Types by name for ``NAME = <provable>`` and ``NAME: <scalar> = ...``
        statements whose name is bound once and never declared ``global``.

    """
    declared: set[str] = {
        name
        for node in walk(node=module)
        if isinstance(node, (Global, Nonlocal))
        for name in node.names
    }
    found: dict[str, str] = {}
    for statement in module.body:
        name: str | None = None
        kind: str | None = None
        match statement:
            case Assign(targets=[Name(id=name)], value=value):
                kind = expression_type(node=value, counts=counts)
            case AnnAssign(target=Name(id=name), annotation=annotation):
                kind = _annotated_scalar(annotation=annotation, counts=counts)
            case _:
                continue
        if (
            kind is not None
            and name.isupper()
            and counts.get(name) == 1
            and name not in declared
        ):
            found[name] = kind
    return found


def never_returns(*, function: Function) -> bool:
    """Prove that every path of a function raises.

    Args:
        function: Function definition.

    Returns:
        Whether the function has no ``return`` or ``yield`` and its body
        cannot reach the end, so calling it never produces a value.

    """
    if any(
        isinstance(node, (Return, Yield, YieldFrom))
        for node in own_nodes(function=function)
    ):
        return False
    return not can_fall_off(body=function.body)


def _declared_elsewhere(*, function: Function) -> frozenset[str]:
    """Collect names that ``global`` or ``nonlocal`` lets other code rebind.

    Args:
        function: Function definition.

    Returns:
        Names declared ``global`` or ``nonlocal`` anywhere in the function,
        including nested functions.

    """
    names: set[str] = set()
    for node in walk(node=function):
        if isinstance(node, (Global, Nonlocal)):
            names.update(node.names)
    return frozenset(names)


def _type_locals(
    *,
    typer: _Typer,
    function: Function,
    fixed: frozenset[str],
) -> None:
    """Type single-assignment locals and mark the ones typed purely.

    Args:
        typer: Typer whose environment is extended in place.
        function: Function definition.
        fixed: Names that must keep their given type or stay untyped.

    """
    stored: dict[str, int] = _single_assignments(function=function)
    for node in own_nodes(function=function):
        match node:
            case Assign(targets=[Name(id=name)], value=value) if (
                stored.get(name) == 1 and name not in fixed
            ):
                before: int = typer.reads
                found: str | None = typer.type_of(node=value)
                if found is not None:
                    typer.env[name] = found
                    if typer.reads == before:
                        typer.pure.add(name)
            case _:
                continue
    _type_rebound_locals(typer=typer, function=function, fixed=fixed)


def _plain_bindings(
    *,
    function: Function,
    fixed: frozenset[str],
) -> dict[str, list[AST]]:
    """Collect the locals whose every binding is a plain assignment.

    Args:
        function: Function definition.
        fixed: Names that must keep their given type or stay untyped.

    Returns:
        For each local bound at least twice, only by ``name = value`` and
        ``name op= value`` statements, those statements.

    """
    parameters: set[str] = {
        item.arg
        for item in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
            function.args.vararg,
            function.args.kwarg,
        )
        if item is not None
    }
    plain: dict[int, AST] = {}
    for node in own_nodes(function=function):
        match node:
            case (
                Assign(targets=[Name() as target])
                | AugAssign(
                    target=Name() as target,
                )
            ):
                plain[id(target)] = node
            case _:
                continue
    statements: dict[str, list[AST]] = {}
    blocked: set[str] = set(parameters) | set(fixed)
    for node in own_nodes(function=function):
        for name in names_bound_by(node=node):
            if id(node) in plain:
                statements.setdefault(name, []).append(plain[id(node)])
            else:
                blocked.add(name)
    return {
        name: found
        for name, found in statements.items()
        if name not in blocked and len(found) >= Constants.min_bindings
    }


def _type_rebound_locals(
    *,
    typer: _Typer,
    function: Function,
    fixed: frozenset[str],
) -> None:
    """Type locals bound several times to one provable type.

    Every plain assignment must have the same type; an augmented assignment
    must keep it, checked with the local already assumed to have it (the
    induction that makes ``total = 0; total += 1`` an ``int``).

    Args:
        typer: Typer whose environment is extended in place.
        function: Function definition.
        fixed: Names that must keep their given type or stay untyped.

    """
    candidates: dict[str, list[AST]] = _plain_bindings(
        function=function,
        fixed=fixed,
    )
    for _round in range(Constants.rebound_rounds):
        settled: bool = False
        for name, statements in candidates.items():
            if name in typer.env:
                continue
            found: str | None = _agreed_binding(
                typer=typer,
                name=name,
                statements=statements,
            )
            if found is not None:
                typer.env[name] = found
                settled = True
        if not settled:
            return


def _agreed_binding(
    *,
    typer: _Typer,
    name: str,
    statements: list[AST],
) -> str | None:
    """Find the one type all of a local's bindings produce.

    Args:
        typer: Typer holding the types settled so far.
        name: The local.
        statements: Its plain and augmented assignments.

    Returns:
        The agreed type, or ``None`` when they disagree or cannot be typed.

    """
    values: list[expr] = [
        item.value for item in statements if isinstance(item, Assign)
    ]
    kinds: set[str] = set()
    for value in values:
        found: str | None = typer.type_of(node=value)
        if found is not None:
            kinds.add(found)
    if len(kinds) != 1:
        return None
    (kind,) = kinds
    typer.env[name] = kind
    try:
        for value in values:
            if typer.type_of(node=value) != kind:
                return None
        for item in statements:
            if isinstance(item, AugAssign) and (
                typer.type_of(
                    node=BinOp(
                        left=Name(id=name, ctx=Load()),
                        op=item.op,
                        right=item.value,
                    ),
                )
                != kind
            ):
                return None
    finally:
        del typer.env[name]
    return kind


def _join_types(*, types: list[str]) -> str | None:
    """Combine the types of every exit of a function.

    Args:
        types: One type per return path.

    Returns:
        The common type, ``T | None`` for one type plus ``None``, or
        ``None`` when the paths disagree.

    """
    unique: list[str] = list(dict.fromkeys(types))
    others: list[str] = [item for item in unique if item != "None"]
    if len(unique) == 1:
        return unique[0]
    if "None" in unique and len(others) == 1:
        return f"{others[0]} | None"
    return None


def provable_return(
    *,
    function: Function,
    known_types: Mapping[str, str],
    counts: Mapping[str, int],
) -> str | None:
    """Prove a function's return annotation from its body.

    Args:
        function: Function definition.
        known_types: Types of parameters (accepted hints or annotations).
        counts: Module binding counts.

    Returns:
        The annotation source, or ``None`` when it is not provable.

    """
    return provable_return_detail(
        function=function,
        known_types=known_types,
        counts=counts,
    )[0]


def provable_return_detail(
    *,
    function: Function,
    known_types: Mapping[str, str],
    counts: Mapping[str, int],
) -> tuple[str | None, bool]:
    """Prove a function's return annotation and say how it was proven.

    Every returned expression must have a type the syntax determines, using
    literals, operators, builtin constructors and typed parameters or
    single-assignment locals. Paths that fall off the end add ``None``.

    Args:
        function: Function definition.
        known_types: Types of parameters (accepted hints or annotations).
        counts: Module binding counts.

    Returns:
        The annotation source (``None`` when it is not provable) and whether
        the proof is *language-guaranteed*: it read the type of no parameter
        or variable, only literals, f-strings, ``not``, and builtins whose
        result type is fixed (``len``, ``str``, ``isinstance``, …).

    """
    rebound: frozenset[str] = _declared_elsewhere(function=function)
    typer: _Typer = _Typer(
        env={k: v for k, v in known_types.items() if k not in rebound},
        counts=counts,
    )
    _type_locals(
        typer=typer,
        function=function,
        fixed=frozenset({*known_types, *rebound}),
    )
    typer.reads = 0
    types: list[str] = []
    for node in own_nodes(function=function):
        if not isinstance(node, Return):
            continue
        result: str | None = (
            "None" if node.value is None else typer.type_of(node=node.value)
        )
        if result is None:
            return None, False
        types.append(result)
    if can_fall_off(body=function.body):
        types.append("None")
    return _join_types(types=types), typer.reads == 0
