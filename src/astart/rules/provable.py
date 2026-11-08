"""Return types that follow from the syntax alone."""

from __future__ import annotations

from ast import (
    AST,
    Add,
    AnnAssign,
    Assert,
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
    Expr,
    FloorDiv,
    FunctionDef,
    Global,
    If,
    IfExp,
    Invert,
    Is,
    IsNot,
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
    Pow,
    Raise,
    Return,
    Set,
    SetComp,
    Slice,
    Store,
    Sub,
    Subscript,
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
from typing import TYPE_CHECKING, Final, cast, final

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
        noreturn_mark: Call-node attribute flagging a call that never returns.
        noreturn_rounds: Passes that propagate never-returning helpers.
        placeholder: Exception that marks an abstract hook.
        str_to_list: ``str`` methods that return ``list[str]``.
        rebound_rounds: Passes that settle locals whose bindings depend on
            one another.
        str_to_str: ``str`` methods whose result is always ``str``.
        str_to_bool: ``str`` methods whose result is always ``bool``.
        str_to_int: ``str`` methods whose result is always ``int``.
        special_calls: Builtin names ``_call`` handles argument-by-argument.

    """

    rebound_rounds: Final[int] = 4
    str_to_list: Final[frozenset[str]] = frozenset(
        {"split", "rsplit", "splitlines"},
    )
    min_bindings: Final[int] = 2
    noreturn_mark: Final[str] = "astart_noreturn_call"
    noreturn_rounds: Final[int] = 8
    placeholder: Final[str] = "NotImplementedError"

    numeric: Final[frozenset[str]] = frozenset({"bool", "int", "float"})
    str_to_str: Final[frozenset[str]] = frozenset(
        {
            "upper",
            "lower",
            "strip",
            "lstrip",
            "rstrip",
            "title",
            "capitalize",
            "casefold",
            "swapcase",
            "replace",
            "join",
            "format",
            "zfill",
            "center",
            "ljust",
            "rjust",
            "expandtabs",
            "removeprefix",
            "removesuffix",
        },
    )
    str_to_bool: Final[frozenset[str]] = frozenset(
        {
            "startswith",
            "endswith",
            "isdigit",
            "isalpha",
            "isalnum",
            "isspace",
            "islower",
            "isupper",
            "isidentifier",
            "isnumeric",
            "isdecimal",
            "istitle",
        },
    )
    str_to_int: Final[frozenset[str]] = frozenset(
        {"find", "rfind", "index", "rindex", "count"},
    )
    special_calls: Final[frozenset[str]] = frozenset(
        {"abs", "round", "min", "max", "sorted", "list", "set", "tuple"},
    )
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


def _method_result(*, receiver: str | None, attr: str) -> str | None:
    """Give the result type of a known ``str`` or ``bytes`` method.

    Args:
        receiver: Proven type of the receiver.
        attr: Method name.

    Returns:
        The result type, or ``None`` when the method is not known.

    """
    if receiver == "bytes":
        return "str" if attr == "decode" else None
    if receiver != "str":
        return None
    for names, kind in (
        (Constants.str_to_list, "list[str]"),
        (frozenset({"encode"}), "bytes"),
        (Constants.str_to_str, "str"),
        (Constants.str_to_bool, "bool"),
        (Constants.str_to_int, "int"),
    ):
        if attr in names:
            return kind
    return None


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
            Subscript: self._subscript,
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
        if not isinstance(node, Call):
            return None
        if isinstance(node.func, Attribute):
            return self._attribute_call(node=node)
        if not isinstance(node.func, Name):
            return None
        name: str = node.func.id
        if self._counts.get(constructor_key(name=name)):
            return name
        if self._counts.get(name, 0) != 0:
            return None
        return (
            self._builtin_call(name=name, node=node)
            if name in Constants.special_calls
            else Constants.call_types.get(name)
        )

    def _attribute_call(self, *, node: Call) -> str | None:
        """Type ``receiver.method(...)`` for known ``str`` methods.

        Args:
            node: Call whose function is an attribute.

        Returns:
            The result type, or ``None``.

        """
        func: expr = node.func
        if not isinstance(func, Attribute):
            return None
        return _method_result(
            receiver=self.type_of(node=func.value),
            attr=func.attr,
        )

    def _builtin_call(self, *, name: str, node: Call) -> str | None:
        """Type ``abs``/``round``/``min``/``max``/``sorted``/containers.

        Args:
            name: Callee name, one of ``Constants.special_calls``.
            node: Call expression.

        Returns:
            The result type, or ``None``.

        """
        if name in {"list", "set", "tuple"}:
            return self._collection_call(name=name, node=node)
        return self._scalar_call(name=name, node=node)

    def _scalar_call(self, *, name: str, node: Call) -> str | None:
        """Type ``abs``, ``round``, ``min``, ``max`` and ``sorted``.

        Args:
            name: Callee name.
            node: Call expression.

        Returns:
            The result type, or ``None``.

        """
        if node.keywords:
            return None
        if name in {"abs", "round"}:
            return self._rounding_call(name=name, node=node)
        if name == "sorted":
            return self._sorted_call(node=node)
        return self._extreme_call(node=node)

    def _rounding_call(self, *, name: str, node: Call) -> str | None:
        """Type ``abs``/``round`` over one typed numeric argument.

        Args:
            name: ``"abs"`` or ``"round"``.
            node: Call expression.

        Returns:
            The operand type for ``abs``, ``"int"`` for ``round``, or
            ``None``.

        """
        if len(node.args) != 1:
            return None
        found: str | None = self.type_of(node=node.args[0])
        if found not in {"int", "float"}:
            return None
        return found if name == "abs" else "int"

    def _sorted_call(self, *, node: Call) -> str | None:
        """Type ``sorted`` over a ``list[T]`` argument.

        Args:
            node: Call expression.

        Returns:
            The ``list[T]`` type, or ``None``.

        """
        if not node.args:
            return None
        whole: str | None = self.type_of(node=node.args[0])
        return (
            whole if whole is not None and whole.startswith("list[") else None
        )

    def _extreme_call(self, *, node: Call) -> str | None:
        """Type ``min``/``max`` over agreeing scalar arguments.

        Args:
            node: Call expression.

        Returns:
            The shared scalar type, or ``None``.

        """
        if len(node.args) <= 1:
            return None
        types: list[str | None] = [
            self.type_of(node=argument) for argument in node.args
        ]
        first: str | None = types[0]
        if first is None or first not in Constants.scalar_annotations:
            return None
        return first if all(item == first for item in types) else None

    def _collection_call(self, *, name: str, node: Call) -> str | None:
        """Type ``list``/``set``/``tuple`` over one typed iterable.

        Args:
            name: ``"list"``, ``"set"`` or ``"tuple"``.
            node: Call expression.

        Returns:
            The container type, or ``None``.

        """
        if len(node.args) != 1 or node.keywords:
            return None
        whole: str | None = self.type_of(node=node.args[0])
        if whole is None:
            return None
        if name == "tuple":
            return whole if whole.startswith("tuple[") else None
        item: str | None = None
        if whole == "str":
            item = "str"
        else:
            for prefix in ("list[", "set["):
                if whole.startswith(prefix) and whole.endswith("]"):
                    item = whole[len(prefix) : -1]
                    break
        return None if item is None else f"{name}[{item}]"

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
        if isinstance(node.op, Pow):
            return self._pow(node=node, left=left, right=right)
        if (
            left is not None
            and right is not None
            and left in Constants.numeric
            and right in Constants.numeric
        ):
            return self._numeric(op=node.op, left=left, right=right)
        if (left == "str" and isinstance(node.op, Mod)) or (
            left == "str" and right == "str" and isinstance(node.op, Add)
        ):
            return "str"
        if (
            isinstance(node.op, Add)
            and left is not None
            and left == right
            and left.startswith("list[")
        ):
            return left
        return (
            "str"
            if isinstance(node.op, Mult)
            and {left, right}
            <= {
                "str",
                "int",
                "bool",
            }
            and "str" in {left, right}
            else None
        )

    @staticmethod
    def _pow(
        *,
        node: BinOp,
        left: str | None,
        right: str | None,
    ) -> str | None:
        """Type ``base ** exponent`` without claiming complex results.

        An integral exponent on an ``int``/``bool`` base stays ``int``; a
        ``float`` on either side gives ``float`` only when no complex result
        is possible — an integral exponent, or a base that is a non-negative
        literal. A possibly negative base with a fractional exponent can be
        ``complex``, so it is refused.

        Args:
            node: The ``**`` expression.
            left: Left operand type.
            right: Right operand type.

        Returns:
            ``"int"``, ``"float"`` or ``None``.

        """
        if (
            left in {"int", "bool"}
            and right in {"int", "bool"}
            and isinstance(node.right, Constant)
            and isinstance(node.right.value, int)
            and node.right.value >= 0
        ):
            return "int"
        if left == "float" and right in {"int", "bool"}:
            return "float"
        if right == "float" and left in {"int", "bool", "float"}:
            base: AST = node.left
            if (
                isinstance(base, Constant)
                and isinstance(base.value, int | float)
                and base.value >= 0
            ):
                return "float"
        return None

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

    @staticmethod
    def _dict_item(*, whole: str) -> tuple[str, str] | None:
        """Split ``dict[K, V]`` into key and value type strings.

        Args:
            whole: Container type string.

        Returns:
            ``(K, V)``, or ``None`` when ``whole`` is not a dict type.

        """
        if not (whole.startswith("dict[") and whole.endswith("]")):
            return None
        inner: str = whole[len("dict[") : -1]
        depth: int = 0
        for index, char in enumerate(iterable=inner):
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            elif char == "," and depth == 0:
                key: str = inner[:index].strip()
                value: str = inner[index + 1 :].strip()
                return (key, value) if key and value else None
        return None

    def _subscript(self, node: AST) -> str | None:
        """Type ``value[index]`` for known containers.

        ``list[T]`` with an integer literal gives ``T`` and with a slice
        gives ``list[T]``; ``str`` gives ``str`` for either; ``dict[K, V]``
        gives ``V`` when the key types to ``K``.

        Args:
            node: Expression.

        Returns:
            The element type, or ``None``.

        """
        if (
            not isinstance(
                node,
                Subscript,
            )
            or (whole := self.type_of(node=node.value)) is None
        ):
            return None

        slc: AST = node.slice
        integer_index: bool = isinstance(slc, Constant) and isinstance(
            slc.value,
            int,
        )
        if whole.startswith("list[") and whole.endswith("]"):
            if integer_index:
                return whole[len("list[") : -1]
            return whole if isinstance(slc, Slice) else None
        if whole == "str":
            return "str" if integer_index or isinstance(slc, Slice) else None
        item: tuple[str, str] | None = self._dict_item(whole=whole)
        if item is None:
            return None
        key, value = item
        index_type: str | None = self.type_of(node=slc)
        return value if index_type == key else None


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
    result: bool = True
    match last:
        case Return() | Raise():
            result = False
        case Expr(value=Call() as call) if vars(call).get(
            Constants.noreturn_mark,
        ):
            result = False
        case If(body=then, orelse=otherwise):
            result = (
                not otherwise
                or can_fall_off(body=then)
                or can_fall_off(body=otherwise)
            )
        case With(body=inner) | AsyncWith(body=inner):
            result = can_fall_off(body=inner)
        case Try() | TryStar():
            result = _try_can_fall_off(statement=last)
        case _:
            pass
    return result


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
    nodes: list[AST] = list(own_nodes(function=function))
    if any(isinstance(node, (Return, Yield, YieldFrom)) for node in nodes):
        return False
    raises: list[Raise] = [node for node in nodes if isinstance(node, Raise)]
    if raises and all(_placeholder(statement=item) for item in raises):
        return False
    return not can_fall_off(body=function.body)


def _placeholder(*, statement: Raise) -> bool:
    """Tell whether a ``raise`` only marks an abstract hook.

    A method that raises ``NotImplementedError`` is meant to be overridden by
    one that returns, so calling it ``NoReturn`` would make every override an
    incompatible one.

    Args:
        statement: A ``raise`` statement.

    Returns:
        ``True`` for ``raise NotImplementedError`` with or without arguments.

    """
    target: expr | None = statement.exc
    if isinstance(target, Call):
        target = target.func
    return isinstance(target, Name) and target.id == Constants.placeholder


def mark_noreturn_calls(
    *,
    module: Module,
    counts: Mapping[str, int],
) -> frozenset[str]:
    """Flag calls to module functions that never return.

    A function never returns when every path raises, or ends in a call to
    another such function; the second case needs a fixed point. Only plain
    synchronous module-level functions bound once qualify. Each qualifying
    call node carries a mark that :func:`can_fall_off` reads, so nothing else
    needs to know about the module.

    Args:
        module: Parsed module, marked in place.
        counts: Module binding counts.

    Returns:
        The names of the functions that never return.

    """
    functions: dict[str, FunctionDef] = {
        item.name: item
        for item in module.body
        if isinstance(item, FunctionDef) and counts.get(item.name) == 1
    }
    calls: list[Call] = [
        node
        for node in walk(node=module)
        if isinstance(node, Call)
        and isinstance(node.func, Name)
        and node.func.id in functions
    ]
    known: set[str] = set()
    for _round in range(Constants.noreturn_rounds):
        for call in calls:
            vars(call)[Constants.noreturn_mark] = (
                cast(typ="Name", val=call.func).id in known
            )
        found: set[str] = {
            name
            for name, function in functions.items()
            if name not in known and never_returns(function=function)
        }
        if not found:
            break
        known |= found
    for call in calls:
        vars(call)[Constants.noreturn_mark] = (
            cast(typ="Name", val=call.func).id in known
        )
    return frozenset(known)


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
    if any(count >= Constants.min_bindings for count in stored.values()):
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


def _union_arms(*, kind: str) -> list[str]:
    """Split a union spelling into its arms.

    Args:
        kind: Annotation source such as ``int | None``.

    Returns:
        The arms, or an empty list when ``kind`` is not a flat union.

    """
    arms: list[str] = kind.split(sep=" | ")
    return (
        arms if len(arms) > 1 and all("[" not in arm for arm in arms) else []
    )


def _narrowed(*, arms: list[str], keep: set[str]) -> str | None:
    """Join the arms that survive a test.

    Args:
        arms: All arms of the union.
        keep: Arm names that remain.

    Returns:
        The surviving union, or ``None`` when nothing or everything stays (the
        test proves nothing then).

    """
    kept: list[str] = [arm for arm in arms if arm in keep]
    return " | ".join(kept) if 0 < len(kept) < len(arms) else None


def _isinstance_classes(*, test: Call) -> set[str] | None:
    """Read the class names of ``isinstance(name, C)`` or ``(C, D)``.

    Args:
        test: An ``isinstance`` call.

    Returns:
        The names, or ``None`` when the second argument is not plain names.

    """
    second: AST = test.args[1]
    if isinstance(second, Name):
        return {second.id}
    if isinstance(second, Tuple) and all(
        isinstance(item, Name) for item in second.elts
    ):
        return {item.id for item in second.elts if isinstance(item, Name)}
    return None


def _none_arms(
    *,
    name: str,
    arms: list[str],
    when_none: bool,
) -> tuple[str, str, str] | None:
    """Arms of ``name is None`` (or ``is not None``).

    Args:
        name: The tested parameter.
        arms: Its union arms.
        when_none: ``True`` for ``is None``.

    Returns:
        The name and the type it has when the test is true and when false.

    """
    true_arm: str | None = _narrowed(arms=arms, keep={"None"})
    false_arm: str | None = _narrowed(
        arms=arms,
        keep={arm for arm in arms if arm != "None"},
    )
    if true_arm is None or false_arm is None:
        return None
    return (
        (name, true_arm, false_arm)
        if when_none
        else (name, false_arm, true_arm)
    )


def _isinstance_arms(
    *,
    test: Call,
    name: str,
    arms: list[str],
) -> tuple[str, str, str] | None:
    """Arms of ``isinstance(name, C)``.

    Args:
        test: The ``isinstance`` call.
        name: The tested parameter.
        arms: Its union arms.

    Returns:
        The name and the type it has when the test is true and when false.
        ``bool`` among the arms blocks ``int`` tests, since ``bool`` is an
        ``int`` instance.

    """
    classes: set[str] | None = _isinstance_classes(test=test)
    if classes is None or ({"int"} & classes and "bool" in arms):
        return None
    true_arm: str | None = _narrowed(arms=arms, keep=classes)
    false_arm: str | None = _narrowed(
        arms=arms,
        keep={arm for arm in arms if arm not in classes},
    )
    if true_arm is None or false_arm is None:
        return None
    return name, true_arm, false_arm


def _test_arms(
    *,
    test: AST,
    unions: Mapping[str, list[str]],
) -> tuple[str, str, str] | None:
    """Recognise a narrowing test and the type each arm sees.

    Understands ``x is None``, ``x is not None``, ``isinstance(x, C)`` with a
    class or a tuple of classes, and ``not`` of any of these.

    Args:
        test: An ``if`` condition.
        unions: Union parameters by name, with their arms.

    Returns:
        The name, its type when the test is true, and when it is false; or
        ``None`` when the test narrows nothing provably.

    """
    result: tuple[str, str, str] | None = None
    match test:
        case UnaryOp(op=Not(), operand=inner):
            swapped: tuple[str, str, str] | None = _test_arms(
                test=inner,
                unions=unions,
            )
            if swapped is not None:
                result = (swapped[0], swapped[2], swapped[1])
        case Compare(
            left=Name(id=name),
            ops=[Is() | IsNot() as operator],
            comparators=[Constant(value=None)],
        ) if name in unions:
            result = _none_arms(
                name=name,
                arms=unions[name],
                when_none=isinstance(operator, Is),
            )
        case Name(id=name) if name in unions and "None" in unions[name]:
            kept: str | None = _narrowed(
                arms=unions[name],
                keep={arm for arm in unions[name] if arm != "None"},
            )
            if kept is not None:
                result = (name, kept, " | ".join(unions[name]))
        case Call(func=Name(id="isinstance"), args=[Name(id=name), _]) if (
            name in unions
        ):
            result = _isinstance_arms(
                test=test,
                name=name,
                arms=unions[name],
            )
        case _:
            pass
    return result


def _returns_below(*, node: AST) -> list[Return]:
    """Collect the returns under a node, outside nested scopes.

    Args:
        node: A statement.

    Returns:
        Its ``return`` statements.

    """
    found: list[Return] = []
    stack: list[AST] = [node]
    while stack:
        item: AST = stack.pop()
        if isinstance(item, Return):
            found.append(item)
        stack.extend(
            child
            for child in iter_child_nodes(node=item)
            if not isinstance(
                child,
                (FunctionDef, AsyncFunctionDef, Lambda, ClassDef),
            )
        )
    return found


def _flow_returns(
    *,
    body: list[stmt],
    narrowed: Mapping[str, str],
    unions: Mapping[str, list[str]],
    defaults: Mapping[int, str],
) -> list[tuple[Return, dict[str, str]]]:
    """Pair every return with the union parameters narrowed there.

    A narrowing test (``is None``, ``isinstance``) narrows its two arms; when
    one arm cannot fall through, the other arm's narrowing also holds for the
    statements after the ``if``.

    Args:
        body: Statements in execution order.
        narrowed: Narrowings in force when the body starts.
        unions: Union parameters by name, with their arms.
        defaults: Trusted ``if x is None: x = value`` statements, by
            identity, mapped to the parameter they default.

    Returns:
        Each return with the types its narrowed names have at that point.

    """
    found: list[tuple[Return, dict[str, str]]] = []
    current: dict[str, str] = dict(narrowed)
    for statement in body:
        if id(statement) in defaults:
            name: str = defaults[id(statement)]
            current = {
                **current,
                name: " | ".join(arm for arm in unions[name] if arm != "None"),
            }
            continue
        if isinstance(statement, Assert):
            held: tuple[str, str, str] | None = _test_arms(
                test=statement.test,
                unions=unions,
            )
            if held is not None:
                current = {**current, held[0]: held[1]}
            continue
        guard: tuple[str, str, str] | None = (
            _test_arms(test=statement.test, unions=unions)
            if isinstance(statement, If)
            else None
        )
        if not (isinstance(statement, If) and guard is not None):
            found.extend(
                (ret, dict(current)) for ret in _returns_below(node=statement)
            )
            continue
        name, when_true, when_false = guard
        inside: dict[str, str] = {**current, name: when_true}
        outside: dict[str, str] = {**current, name: when_false}
        found.extend(
            _flow_returns(
                body=statement.body,
                narrowed=inside,
                unions=unions,
                defaults=defaults,
            ),
        )
        found.extend(
            _flow_returns(
                body=statement.orelse,
                narrowed=outside,
                unions=unions,
                defaults=defaults,
            ),
        )
        body_open: bool = can_fall_off(body=statement.body)
        else_open: bool = not statement.orelse or can_fall_off(
            body=statement.orelse,
        )
        if not body_open and else_open:
            current = outside
        elif body_open and not else_open:
            current = inside
    return found


def _defaulting_guards(
    *,
    function: Function,
    typer: _Typer,
    known_types: Mapping[str, str],
    stored: Mapping[str, int],
) -> dict[int, str]:
    """Find ``if name is None: name = value`` statements the prover can trust.

    A parameter qualifies when every write to it is such a statement and
    every assigned value has a proven type that is one of the non-``None``
    arms of its declared union; after the ``if`` it then holds only those
    arms.

    Args:
        function: Function definition.
        typer: Typer for the assigned values.
        known_types: Declared types of the parameters.
        stored: How often each name is written in the function.

    Returns:
        The trusted ``if`` statements (by identity) mapped to the parameter.

    """
    found: dict[str, list[tuple[AST, expr]]] = {}
    for node in own_nodes(function=function):
        match node:
            case If(
                test=Compare(
                    left=Name(id=name),
                    ops=[Is()],
                    comparators=[Constant(value=None)],
                ),
                body=[Assign(targets=[Name(id=target)], value=value)],
                orelse=[],
            ) if name == target:
                found.setdefault(name, []).append((node, value))
            case _:
                continue
    trusted: dict[int, str] = {}
    for name, items in found.items():
        arms: list[str] = _union_arms(kind=known_types.get(name, ""))
        allowed: set[str] = {arm for arm in arms if arm != "None"}
        if (
            "None" in arms
            and stored.get(name) == len(items)
            and all(typer.type_of(node=value) in allowed for _, value in items)
        ):
            trusted.update({id(node): name for node, _ in items})
    return trusted


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
    stored: dict[str, int] = _single_assignments(function=function)
    defaults: dict[int, str] = _defaulting_guards(
        function=function,
        typer=typer,
        known_types=known_types,
        stored=stored,
    )
    defaulted: set[str] = set(defaults.values())
    unions: dict[str, list[str]] = {
        name: arms
        for name, kind in known_types.items()
        if name not in rebound
        and (name not in stored or name in defaulted)
        and (arms := _union_arms(kind=kind))
    }
    for node, overrides in _flow_returns(
        body=function.body,
        narrowed={},
        unions=unions,
        defaults=defaults,
    ):
        saved: dict[str, str] = {name: typer.env[name] for name in overrides}
        typer.env.update(overrides)
        result: str | None = (
            "None" if node.value is None else typer.type_of(node=node.value)
        )
        typer.env.update(saved)
        if result is None:
            return None, False
        types.append(result)
    if can_fall_off(body=function.body):
        types.append("None")
    return _join_types(types=types), typer.reads == 0
