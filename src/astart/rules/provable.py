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
    GeneratorExp,
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
    parse,
    stmt,
    unparse,
    walk,
)
from ast import (
    arguments as ast_arguments,
)
from typing import TYPE_CHECKING, Final, cast, final

from astart.rules.resolve import constructor_key
from astart.rules.scopes import names_bound_by

type StrOrNone = str | None
type ListStr = list[str]
type SetStr = set[str]
type DictStr = dict[str, str]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        numeric (Final[frozenset[str]]): Grouped module constant.
        call_types (Final[dict[str, str]]): Grouped module constant.
        constant_types (Final[frozenset[str]]): Grouped module constant.
        scalar_annotations (Final[frozenset[str]]): Builtin scalars accepted as
            plain annotations.
        scope_nodes (Final[tuple[type[AST], ...]]): Grouped module constant.
        min_bindings (Final[int]): Fewest bindings that make a local worth
            proving here.
        noreturn_mark (Final[str]): Call-node attribute flagging a call that
            never returns.
        noreturn_rounds (Final[int]): Passes that propagate never-returning
            helpers.
        placeholder (Final[str]): Exception that marks an abstract hook.
        str_to_list (Final[frozenset[str]]): ``str`` methods that return
            ``list[str]``.
        rebound_rounds (Final[int]): Passes that settle locals whose bindings
            depend on one another.
        str_to_str (Final[frozenset[str]]): ``str`` methods whose result is
            always ``str``.
        str_to_bool (Final[frozenset[str]]): ``str`` methods whose result is
            always ``bool``.
        str_to_int (Final[frozenset[str]]): ``str`` methods whose result is
            always ``int``.
        container_none (Final[frozenset[str]]): Container methods that always
            return ``None``.
        container_scalar (Final[frozenset[str]]): Container methods returning a
            fixed scalar.
        special_calls (Final[frozenset[str]]): Builtin names ``_call`` handles
            argument-by-argument.
        key_value_arity (Final[int]): Arity of a ``K, V`` pair in a subscript.
        defaulted_args (Final[int]): Arity of a call carrying an optional
            default.
        variadic_tuple_arity (Final[int]): Type argument count of a homogeneous
            tuple.
        enumerate_arity (Final[int]): Most positional arguments accepted by
            enumerate.

    """

    rebound_rounds: Final[int] = 4
    str_to_list: Final[frozenset[str]] = frozenset(
        {"split", "rsplit", "splitlines"},
    )
    min_bindings: Final[int] = 2
    key_value_arity: Final[int] = 2
    defaulted_args: Final[int] = 2
    variadic_tuple_arity: Final[int] = 2
    enumerate_arity: Final[int] = 2
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
    container_none: Final[frozenset[str]] = frozenset(
        {
            "append",
            "extend",
            "insert",
            "remove",
            "clear",
            "sort",
            "reverse",
            "add",
            "discard",
            "update",
        },
    )
    container_scalar: Final[frozenset[str]] = frozenset(
        {"index", "count"},
    )
    special_calls: Final[frozenset[str]] = frozenset(
        {
            "abs",
            "round",
            "min",
            "max",
            "sorted",
            "list",
            "set",
            "tuple",
            "dict",
            "sum",
            "next",
        },
    )
    call_types: Final[dict[str, str]] = {
        "all": "bool",
        "any": "bool",
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
        function (Function): Function definition.

    Yields:
        AST: Every node that belongs to the function itself.

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


def _receiver_parts(*, receiver: str) -> tuple[StrOrNone, ListStr]:
    """Split a proven receiver type into origin name and arguments.

    Args:
        receiver (str): Annotation source such as ``dict[str, int]``.

    Returns:
        tuple[StrOrNone, ListStr]: The origin name and its argument sources;
            ``([], [])``
            parts when the text is not a name or subscript of names.

    """
    try:
        node: expr = parse(source=receiver, mode="eval").body
    except SyntaxError:
        return None, []
    if isinstance(node, Subscript):
        inner: expr = node.slice
        args: ListStr = [
            unparse(ast_obj=part)
            for part in (inner.elts if isinstance(inner, Tuple) else (inner,))
        ]
        node = node.value
    else:
        args = []
    while isinstance(node, Attribute):
        return node.attr, args
    if isinstance(node, Name):
        return node.id, args
    return None, []


def _container_method(
    *,
    receiver: str,
    attr: str,
    node: Call,
    type_of: Callable[[AST], str | None],
) -> StrOrNone:
    """Give the result type of a method on a builtin container.

    Only methods whose result the arguments cannot change are tabled,
    plus ``get``/``pop``/``setdefault`` where the default's proven type
    joins the element type.

    Args:
        receiver (str): Proven type of the receiver, e.g. ``dict[str, int]``.
        attr (str): Method name.
        node (Call): The call, for argument-sensitive methods.
        type_of (Callable[[AST], str | None]): Typer for argument expressions.

    Returns:
        StrOrNone: The result type, or ``None`` when the method is not known.

    """
    head, args = _receiver_parts(receiver=receiver)
    if head == "dict" and len(args) == Constants.key_value_arity:
        return _dict_method(
            key=args[0],
            value=args[1],
            attr=attr,
            node=node,
            type_of=type_of,
        )
    return _sequence_method(
        head=head,
        args=args,
        attr=attr,
        receiver=receiver,
    )


def _sequence_method(
    *,
    head: StrOrNone,
    args: ListStr,
    attr: str,
    receiver: str,
) -> StrOrNone:
    """Give the result type of a method on a list/set/tuple receiver.

    Args:
        head (StrOrNone): Container origin name.
        args (ListStr): Subscript arguments as source text.
        attr (str): Method name.
        receiver (str): Proven receiver type text.

    Returns:
        StrOrNone: The result type, or ``None``.

    """
    if head in {"list", "set", "frozenset"} and args:
        element: str = args[0]
        if attr == "copy":
            return receiver
        if attr == "pop":
            return element
        if attr in Constants.container_none:
            return "None"
        if head != "set" and attr in Constants.container_scalar:
            return "int"
    if head == "tuple" and attr in Constants.container_scalar:
        return "int"
    return None


def _dict_method(
    *,
    key: str,
    value: str,
    attr: str,
    node: Call,
    type_of: Callable[[AST], str | None],
) -> StrOrNone:
    """Give the result type of a ``dict`` method.

    Args:
        key (str): Proven key type.
        value (str): Proven element type.
        attr (str): Method name.
        node (Call): The call, for ``get``/``pop``/``setdefault``.
        type_of (Callable[[AST], str | None]): Typer for argument expressions.

    Returns:
        StrOrNone: The result type, or ``None``.

    """
    if attr == "copy":
        return f"dict[{key}, {value}]"
    if attr == "popitem":
        return f"tuple[{key}, {value}]"
    if attr == "setdefault":
        return value
    if attr in {"update", "clear"}:
        return "None"
    if attr in {"get", "pop"}:
        return _dict_lookup(
            value=value,
            attr=attr,
            node=node,
            type_of=type_of,
        )
    return None


def _dict_lookup(
    *,
    value: str,
    attr: str,
    node: Call,
    type_of: Callable[[AST], str | None],
) -> StrOrNone:
    """Type ``d.get``/``d.pop``/``d.setdefault`` with an optional default.

    Args:
        value (str): Proven element type.
        attr (str): Method name.
        node (Call): The call.
        type_of (Callable[[AST], str | None]): Typer for argument expressions.

    Returns:
        StrOrNone: ``V`` , ``V | None`` or ``V | <default type>`` ,
            or ``None`` when the arguments are not provable.

    """
    if node.keywords or not 1 <= len(node.args) <= Constants.defaulted_args:
        return None
    if len(node.args) == Constants.defaulted_args:
        default: StrOrNone = type_of(node.args[1])
        if default is None:
            return None
        return value if default == value else f"{value} | {default}"
    if attr == "pop":
        return value
    return f"{value} | None"


def _method_result(
    *,
    receiver: StrOrNone,
    attr: str,
    node: Call,
    type_of: Callable[[AST], str | None],
) -> StrOrNone:
    """Give the result type of a known method call.

    Args:
        receiver (StrOrNone): Proven type of the receiver.
        attr (str): Method name.
        node (Call): The call, for argument-sensitive methods.
        type_of (Callable[[AST], str | None]): Typer for argument expressions.

    Returns:
        StrOrNone: The result type, or ``None`` when the method is not known.

    """
    if receiver == "bytes":
        return "str" if attr == "decode" else None
    if receiver == "str":
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
    if receiver is not None:
        return _container_method(
            receiver=receiver,
            attr=attr,
            node=node,
            type_of=type_of,
        )
    return None


def _bound_names(*, target: AST) -> ListStr:
    """List the names a comprehension target binds.

    Args:
        target (AST): The ``for`` target.

    Returns:
        ListStr: Every stored name in it.

    """
    return [
        node.id
        for node in walk(node=target)
        if isinstance(node, Name) and isinstance(node.ctx, Store)
    ]


def _unpacked_types(*, target: expr, source: str) -> DictStr:
    """Bind a comprehension pattern from a known tuple item type.

    Args:
        target (expr): A name or recursively nested tuple/list target.
        source (str): Type of one iterated value.

    Returns:
        DictStr:
            Known bindings; unsupported shapes contribute no guessed types.

    """
    if isinstance(target, Name):
        return {target.id: source}
    if not isinstance(target, (Tuple, List)):
        return {}
    head: StrOrNone
    args: ListStr
    head, args = _receiver_parts(receiver=source)
    if head != "tuple":
        return {}
    if len(args) == Constants.variadic_tuple_arity and args[1] == "...":
        args = [args[0]] * len(target.elts)
    if len(args) != len(target.elts):
        return {}
    found: DictStr = {}
    for child, kind in zip(target.elts, args, strict=True):
        found.update(_unpacked_types(target=child, source=kind))
    return found


@final
class _Typer:
    """Type expressions whose type the syntax determines."""

    def __init__(
        self,
        *,
        env: DictStr,
        counts: Mapping[str, int],
    ) -> None:
        """Store the typing environment.

        Args:
            env (DictStr): Known types of names (typed parameters and locals).
            counts (Mapping[str, int]): Module binding counts, to detect
                shadowed builtins.

        """
        self.env: DictStr = env
        self.reads: int = 0
        self.pure: SetStr = set()
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
            GeneratorExp: self._comprehension,
        }

    def type_of(self, node: AST) -> StrOrNone:
        """Return the provable type of an expression.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone:
                The annotation source, or ``None`` when it is not provable.

        """
        for kind, handler in self._handlers.items():
            if isinstance(node, kind):
                resolved: Callable[[AST], str | None] = handler
                return resolved(node)
        return None

    def _attribute(self, node: AST) -> StrOrNone:
        """Type ``receiver.attr`` from a table entry keyed ``"receiver.attr"``.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The recorded type, or ``None`` when the table has none.

        """
        if not (isinstance(node, Attribute) and isinstance(node.value, Name)):
            return None
        found: StrOrNone = self.env.get(f"{node.value.id}.{node.attr}")
        if found is not None:
            self.reads += 1
        return found

    @staticmethod
    def _constant(node: AST) -> StrOrNone:
        """Type a literal.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The literal's type name, or ``None``.

        """
        if not isinstance(node, Constant):
            return None
        if node.value is None:
            return "None"
        name: str = type(node.value).__name__
        return name if name in Constants.constant_types else None

    @staticmethod
    def _joined(_node: AST) -> StrOrNone:
        """Type an f-string.

        Args:
            _node (AST): Expression.

        Returns:
            StrOrNone: Always ``"str"``.

        """
        return "str"

    @staticmethod
    def _numeric(*, op: operator, left: str, right: str) -> StrOrNone:
        """Type arithmetic on numbers.

        Args:
            op (operator): Operator.
            left (str): Left operand type.
            right (str): Right operand type.

        Returns:
            StrOrNone:
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

    def _same(self, nodes: list[expr]) -> StrOrNone:
        """Return the shared type of several expressions.

        Args:
            nodes (list[expr]): Expressions.

        Returns:
            StrOrNone: The common type, or ``None``.

        """
        types: set[StrOrNone] = {self.type_of(node=item) for item in nodes}
        return types.pop() if len(types) == 1 else None

    def _name(self, node: AST) -> StrOrNone:
        """Type a name from the environment.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The known type, or ``None``.

        """
        if not isinstance(node, Name):
            return None
        found: StrOrNone = self.env.get(node.id)
        if found is not None and node.id not in self.pure:
            self.reads += 1
        return found

    def _unary(self, node: AST) -> StrOrNone:
        """Type ``not x`` and numeric signs.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The result type, or ``None``.

        """
        if not isinstance(node, UnaryOp):
            return None
        if isinstance(node.op, Not):
            return "bool"
        found: StrOrNone = self.type_of(node=node.operand)
        if found in {"bool", "int"}:
            return "int"
        if found == "float" and (not isinstance(node.op, Invert)):
            return "float"
        return None

    def _compare(self, node: AST) -> StrOrNone:
        """Type a comparison when every operand has a known type.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: ``"bool"`` or ``None``.

        """
        if not isinstance(node, Compare):
            return None
        operands: list[expr] = [node.left, *node.comparators]
        known: bool = all(
            self.type_of(node=item) is not None for item in operands
        )
        return "bool" if known else None

    def _boolop(self, node: AST) -> StrOrNone:
        """Type ``and`` / ``or`` when every operand has one type.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The shared type, or ``None``.

        """
        return (
            self._same(nodes=node.values) if isinstance(node, BoolOp) else None
        )

    def _ifexp(self, node: AST) -> StrOrNone:
        """Type a conditional expression with equally typed branches.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The shared type, or ``None``.

        """
        if not isinstance(node, IfExp):
            return None
        return self._same(nodes=[node.body, node.orelse])

    def _call(self, node: AST) -> StrOrNone:
        """Type calls of builtin constructors that are not shadowed.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The result type, or ``None``.

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

    def _attribute_call(self, *, node: Call) -> StrOrNone:
        """Type ``receiver.method(...)`` for known ``str`` methods.

        Args:
            node (Call): Call whose function is an attribute.

        Returns:
            StrOrNone: The result type, or ``None``.

        """
        func: expr = node.func
        if not isinstance(func, Attribute):
            return None
        return _method_result(
            receiver=self.type_of(node=func.value),
            attr=func.attr,
            node=node,
            type_of=self.type_of,
        )

    def _builtin_call(self, *, name: str, node: Call) -> StrOrNone:
        """Type ``abs``/``round``/``min``/``max``/``sorted``/containers.

        Args:
            name (str): Callee name, one of ``Constants.special_calls``.
            node (Call): Call expression.

        Returns:
            StrOrNone: The result type, or ``None``.

        """
        if name in {"list", "set", "tuple"}:
            return self._collection_call(name=name, node=node)
        if name == "dict":
            return self._dict_call(node=node)
        if name == "sum":
            return self._sum_call(node=node)
        if name == "next":
            return self._next_call(node=node)
        return self._scalar_call(name=name, node=node)

    def _scalar_call(self, *, name: str, node: Call) -> StrOrNone:
        """Type ``abs``, ``round``, ``min``, ``max`` and ``sorted``.

        Args:
            name (str): Callee name.
            node (Call): Call expression.

        Returns:
            StrOrNone: The result type, or ``None``.

        """
        if node.keywords:
            return None
        if name in {"abs", "round"}:
            return self._rounding_call(name=name, node=node)
        if name == "sorted":
            return self._sorted_call(node=node)
        return self._extreme_call(node=node)

    def _rounding_call(self, *, name: str, node: Call) -> StrOrNone:
        """Type ``abs``/``round`` over one typed numeric argument.

        Args:
            name (str): ``"abs"`` or ``"round"``.
            node (Call): Call expression.

        Returns:
            StrOrNone: The operand type for ``abs`` ,
                ``"int"`` for ``round``, or ``None``.

        """
        if len(node.args) != 1:
            return None
        found: StrOrNone = self.type_of(node=node.args[0])
        if found not in {"int", "float"}:
            return None
        return found if name == "abs" else "int"

    def _sorted_call(self, *, node: Call) -> StrOrNone:
        """Type ``sorted`` over a ``list[T]`` argument.

        Args:
            node (Call): Call expression.

        Returns:
            StrOrNone: The ``list[T]`` type, or ``None``.

        """
        if not node.args:
            return None
        whole: StrOrNone = self.type_of(node=node.args[0])
        if whole is None:
            return None
        head: StrOrNone
        head, _args = _receiver_parts(receiver=whole)
        return whole if head == "list" else None

    def _extreme_call(self, *, node: Call) -> StrOrNone:
        """Type ``min``/``max`` over agreeing scalar arguments.

        Args:
            node (Call): Call expression.

        Returns:
            StrOrNone: The shared scalar type, or ``None``.

        """
        if len(node.args) <= 1:
            return None
        types: list[StrOrNone] = [
            self.type_of(node=argument) for argument in node.args
        ]
        first: StrOrNone = types[0]
        if first is None or first not in Constants.scalar_annotations:
            return None
        return first if all(item == first for item in types) else None

    def _collection_call(self, *, name: str, node: Call) -> StrOrNone:
        """Type ``list``/``set``/``tuple`` over one typed iterable.

        Args:
            name (str): ``"list"``, ``"set"`` or ``"tuple"``.
            node (Call): Call expression.

        Returns:
            StrOrNone: The container type, or ``None``.

        """
        if len(node.args) != 1 or node.keywords:
            return None
        whole: StrOrNone = self.type_of(node=node.args[0])
        head: StrOrNone
        head, _ = _receiver_parts(receiver=whole or "")
        if name == "tuple" and head == "tuple":
            return whole
        item: StrOrNone = self._item_type(
            typer=self,
            iterable=node.args[0],
        )
        if item is None:
            return None
        return f"tuple[{item}, ...]" if name == "tuple" else f"{name}[{item}]"

    def _dict_call(self, *, node: Call) -> StrOrNone:
        """Type ``dict`` over a mapping or an iterable of pairs.

        Args:
            node (Call): Call expression.

        Returns:
            StrOrNone: The dict type, or ``None``.

        """
        if node.keywords or len(node.args) != 1:
            return None
        whole: StrOrNone = self.type_of(node=node.args[0])
        if whole is None:
            return None
        found: tuple[str, str] | None = _Typer._dict_item(whole=whole)
        if found is not None:
            return whole
        return _Typer._pairs_dict(whole=whole)

    @staticmethod
    def _pairs_dict(*, whole: str) -> StrOrNone:
        """Type ``dict`` over ``list[tuple[K, V]]``.

        Args:
            whole (str): Proven type of the call argument.

        Returns:
            StrOrNone: ``dict[K, V]``, or ``None``.

        """
        head: StrOrNone
        outer: ListStr
        head, outer = _receiver_parts(receiver=whole)
        if head != "list" or len(outer) != 1:
            return None
        inner_head: StrOrNone
        pair: ListStr
        inner_head, pair = _receiver_parts(receiver=outer[0])
        if inner_head != "tuple" or len(pair) != Constants.key_value_arity:
            return None
        key: str = pair[0].strip()
        value: str = pair[1].strip()
        if not key or not value:
            return None
        return f"dict[{key}, {value}]"

    def _sum_call(self, *, node: Call) -> StrOrNone:
        """Type ``sum`` over a numeric iterable.

        Args:
            node (Call): Call expression.

        Returns:
            StrOrNone: ``"int"`` or ``"float"``, or ``None``.

        """
        count: int = len(node.args)
        if node.keywords or not 1 <= count <= Constants.defaulted_args:
            return None
        item: StrOrNone = self._item_type(typer=self, iterable=node.args[0])
        if item is None:
            return None
        kinds: SetStr = set(_union_arms(kind=item)) or {
            item,
        }
        if len(node.args) == Constants.defaulted_args:
            start: StrOrNone = self.type_of(node=node.args[1])
            if start is None or start not in {"int", "float"}:
                return None
            kinds.add(start)
        if not kinds or not kinds <= {"int", "float", "bool"}:
            return None
        return "float" if "float" in kinds else "int"

    def _next_call(self, *, node: Call) -> StrOrNone:
        """Type ``next`` over an iterable, with an optional default.

        Args:
            node (Call): Call expression.

        Returns:
            StrOrNone: The element type, possibly unioned
                with the default's, or ``None``.

        """
        count: int = len(node.args)
        if node.keywords or not 1 <= count <= Constants.defaulted_args:
            return None
        item: StrOrNone = self._item_type(typer=self, iterable=node.args[0])
        if item is None:
            return None
        if len(node.args) == 1:
            return item
        default: StrOrNone = self.type_of(node=node.args[1])
        if default is None:
            return None
        return item if default == item else f"{item} | {default}"

    def _binop(self, node: AST) -> StrOrNone:
        """Type arithmetic and string operations on known scalars.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The result type, or ``None``.

        """
        if not isinstance(node, BinOp):
            return None
        left: StrOrNone = self.type_of(node=node.left)
        right: StrOrNone = self.type_of(node=node.right)
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
        if isinstance(node.op, Add) and left is not None and left == right:
            head: StrOrNone
            args: ListStr
            head, args = _receiver_parts(receiver=left)
            if head == "list" and args:
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
        left: StrOrNone,
        right: StrOrNone,
    ) -> StrOrNone:
        """Type ``base ** exponent`` without claiming complex results.

        An integral exponent on an ``int``/``bool`` base stays ``int``; a
        ``float`` on either side gives ``float`` only when no complex result
        is possible — an integral exponent, or a base that is a non-negative
        literal. A possibly negative base with a fractional exponent can be
        ``complex``, so it is refused.

        Args:
            node (BinOp): The ``**`` expression.
            left (StrOrNone): Left operand type.
            right (StrOrNone): Right operand type.

        Returns:
            StrOrNone: ``"int"``, ``"float"`` or ``None``.

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

    def _list(self, node: AST) -> StrOrNone:
        """Type a list display of equally typed items.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The list type, or ``None``.

        """
        return self._sequence(kind="list", node=node)

    def _set(self, node: AST) -> StrOrNone:
        """Type a set display of equally typed items.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The set type, or ``None``.

        """
        return self._sequence(kind="set", node=node)

    def _sequence(self, *, kind: str, node: AST) -> StrOrNone:
        """Type a list or set display.

        Args:
            kind (str): Container name.
            node (AST): Expression.

        Returns:
            StrOrNone:
                The container type, or ``None`` for empty or mixed displays.

        """
        if not isinstance(node, (List, Set)) or not node.elts:
            return None
        item: StrOrNone = self._same(nodes=node.elts)
        return None if item is None else f"{kind}[{item}]"

    def _tuple(self, node: AST) -> StrOrNone:
        """Type a tuple display of known items.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The tuple type, or ``None``.

        """
        if not isinstance(node, Tuple) or not node.elts:
            return None
        parts: list[StrOrNone] = [self.type_of(node=e) for e in node.elts]
        known: ListStr = [part for part in parts if part is not None]
        if len(known) != len(parts):
            return None
        return f"tuple[{', '.join(known)}]"

    def _comprehension(self, node: AST) -> StrOrNone:
        """Type a comprehension or generator from its element bindings.

        Loop variables are typed only when the iterable fixes them (``range``
        gives ``int``; typed iterables and mapping views retain their item
        structure). Tuple patterns unpack that structure recursively. An
        unknown binding hides the outer name it shadows.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The container type, or ``None``.

        """
        if not isinstance(node, (ListComp, SetComp, DictComp, GeneratorExp)):
            return None
        inner: _Typer = _Typer(env=dict(self.env), counts=self._counts)
        inner.pure = set(self.pure)
        for generator in node.generators:
            if generator.is_async:
                return None
            item: StrOrNone = self._item_type(
                typer=inner,
                iterable=generator.iter,
            )
            for name in _bound_names(target=generator.target):
                inner.env.pop(name, None)
                inner.pure.discard(name)
            if item is not None:
                bindings: DictStr = _unpacked_types(
                    target=generator.target,
                    source=item,
                )
                inner.env.update(bindings)
                inner.pure.update(bindings)
        if isinstance(node, DictComp):
            key: StrOrNone = inner.type_of(node=node.key)
            value: StrOrNone = inner.type_of(node=node.value)
            shape: StrOrNone = (
                None
                if key is None or value is None
                else f"dict[{key}, {value}]"
            )
        else:
            element: StrOrNone = inner.type_of(node=node.elt)
            kind: str = (
                "list"
                if isinstance(node, ListComp)
                else "Generator"
                if isinstance(node, GeneratorExp)
                else "set"
            )
            shape = None if element is None else f"{kind}[{element}]"
        self.reads += inner.reads
        return shape

    def _item_type(self, *, typer: _Typer, iterable: expr) -> StrOrNone:
        """Give the type iterating an expression yields, when provable.

        Args:
            typer (_Typer): Typer whose environment sees the comprehension's
                names.
            iterable (expr): The ``for`` clause's iterable.

        Returns:
            StrOrNone: The item type, or ``None``.

        """
        if isinstance(iterable, Call):
            called: StrOrNone = self._iteration_call(
                typer=typer,
                call=iterable,
            )
            if called is not None:
                return called
        whole: StrOrNone = typer.type_of(node=iterable)
        if whole in {"str", "bytes", "bytearray", "range"}:
            return "str" if whole == "str" else "int"
        head: StrOrNone
        args: ListStr
        head, args = _receiver_parts(receiver=whole or "")
        if (
            head
            in {
                "list",
                "set",
                "frozenset",
                "Sequence",
                "MutableSequence",
                "Iterable",
                "Iterator",
                "Generator",
                "Collection",
                "deque",
                "dict",
                "Mapping",
                "MutableMapping",
                "defaultdict",
            }
            and args
        ):
            return args[0]
        if head == "tuple" and args:
            return (
                args[0]
                if len(args) == Constants.variadic_tuple_arity
                and args[1] == "..."
                else None
                if "..." in args
                else " | ".join(sorted(set(args)))
            )
        return None

    def _iteration_call(self, *, typer: _Typer, call: Call) -> StrOrNone:
        """Resolve builtin enumeration and mapping-view element types.

        Args:
            typer (_Typer): Environment at this comprehension clause.
            call (Call): Iterable-producing call.

        Returns:
            StrOrNone:
                The yielded type, or ``None`` for an unknown or shadowed call.

        """
        if isinstance(call.func, Name) and not self._counts.get(call.func.id):
            if call.func.id == "range":
                return "int"
            if (
                call.func.id == "enumerate"
                and len(call.args) <= Constants.enumerate_arity
            ):
                sources: list[expr] = [
                    *call.args[:1],
                    *(k.value for k in call.keywords if k.arg == "iterable"),
                ]
                if len(sources) == 1 and all(
                    k.arg in {"iterable", "start"} for k in call.keywords
                ):
                    item: StrOrNone = self._item_type(
                        typer=typer,
                        iterable=sources[0],
                    )
                    return None if item is None else f"tuple[int, {item}]"
        if not isinstance(call.func, Attribute) or call.args or call.keywords:
            return None
        whole: StrOrNone = typer.type_of(node=call.func.value)
        head: StrOrNone
        args: ListStr
        head, args = _receiver_parts(receiver=whole or "")
        if head not in {"dict", "Mapping", "MutableMapping", "defaultdict"}:
            return None
        if len(args) != Constants.key_value_arity:
            return None
        shapes: DictStr = {
            "keys": args[0],
            "values": args[1],
            "items": f"tuple[{args[0]}, {args[1]}]",
        }
        return shapes.get(call.func.attr)

    def _dict(self, node: AST) -> StrOrNone:
        """Type a dict display of equally typed keys and values.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The dict type, or ``None``.

        """
        if not isinstance(node, Dict) or not node.keys:
            return None
        keys: list[expr] = [k for k in node.keys if k is not None]
        if len(keys) != len(node.keys):
            return None
        key_type: StrOrNone = self._same(nodes=keys)
        value_type: StrOrNone = self._same(nodes=node.values)
        if key_type is None or value_type is None:
            return None
        return f"dict[{key_type}, {value_type}]"

    @staticmethod
    def _dict_item(*, whole: str) -> tuple[str, str] | None:
        """Split ``dict[K, V]`` into key and value type strings.

        Args:
            whole (str): Container type string.

        Returns:
            tuple[str, str] | None:
                ``(K, V)``, or ``None`` when ``whole`` is not a dict type.

        """
        head: StrOrNone
        args: ListStr
        head, args = _receiver_parts(receiver=whole)
        if head != "dict" or len(args) != Constants.key_value_arity:
            return None
        key: str = args[0].strip()
        value: str = args[1].strip()
        return (key, value) if key and value else None

    def _subscript(self, node: AST) -> StrOrNone:
        """Type ``value[index]`` for known containers.

        ``list[T]`` with an integer literal gives ``T`` and with a slice
        gives ``list[T]``; ``str`` gives ``str`` for either; ``dict[K, V]``
        gives ``V`` when the key types to ``K``.

        Args:
            node (AST): Expression.

        Returns:
            StrOrNone: The element type, or ``None``.

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
        head: StrOrNone
        args: ListStr
        head, args = _receiver_parts(receiver=whole)
        if head == "list" and args:
            if integer_index:
                return args[0]
            return whole if isinstance(slc, Slice) else None
        if whole == "str":
            return "str" if integer_index or isinstance(slc, Slice) else None
        item: tuple[str, str] | None = self._dict_item(whole=whole)
        if item is None:
            return None
        key, value = item
        index_type: StrOrNone = self.type_of(node=slc)
        return value if index_type == key else None


def _try_can_fall_off(*, statement: Try | TryStar) -> bool:
    """Report whether control can leave a ``try`` statement normally.

    A ``finally`` block that cannot fall off decides the outcome. Otherwise
    control continues after the statement when the body (followed by the
    ``else`` block) or any handler falls off its end; an exception that no
    handler catches propagates and never reaches the next statement.

    Args:
        statement (Try | TryStar): The ``try`` statement.

    Returns:
        bool: Whether execution may continue after it.

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
        body (list[stmt]): Statements.

    Returns:
        bool: Whether execution may continue after the last statement.

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
        function (Function): Function definition.

    Returns:
        dict[str, int]: Store counts by name.

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
) -> StrOrNone:
    """Prove the type of a single expression.

    Args:
        node (AST): Expression.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible where the
            expression is evaluated, from
            :func:`scope_types` and :func:`module_constants`; ``None`` types
            no names.

    Returns:
        StrOrNone: The annotation source, or ``None`` when it is not provable.

    """
    return _Typer(env=dict(env or {}), counts=counts).type_of(node=node)


def own_calls(*, function: Function) -> list[Call]:
    """List the calls a function makes itself, outside nested scopes.

    Args:
        function (Function): Function definition.

    Returns:
        list[Call]: Its call expressions.

    """
    return [
        node for node in own_nodes(function=function) if isinstance(node, Call)
    ]


def _annotated_scalar(
    *,
    annotation: AST | None,
    counts: Mapping[str, int],
) -> StrOrNone:
    """Read a plain builtin scalar annotation.

    Args:
        annotation (AST | None): Annotation expression, if any.
        counts (Mapping[str, int]): Module binding counts, to detect shadowed
            builtins.

    Returns:
        StrOrNone: The type name for ``int``, ``str``, ``float``, ``bool`` or
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
) -> DictStr:
    """Type the names a function can rely on at its call sites.

    Includes module constants, parameters annotated with a builtin scalar, and
    locals assigned exactly once to a provable value. A name that is also
    rebound by ``global``/``nonlocal``, a loop, ``with``, an import, a nested
    definition or a handler is left out.

    Args:
        function (Function): Function definition.
        counts (Mapping[str, int]): Module binding counts.
        constants (Mapping[str, str]): Types of module-level constants.
        declared (Mapping[str, str] | None): Types already accepted for this
            function's own
            parameters (hints decided earlier), by parameter name.

    Returns:
        DictStr: Types by name.

    """
    rebound: frozenset[str] = _declared_elsewhere(function=function)
    env: DictStr = {
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
        found: StrOrNone = _annotated_scalar(
            annotation=parameter.annotation,
            counts=counts,
        )
        if found is None and declared is not None:
            found = declared.get(parameter.arg)
        if found is not None and parameter.arg not in rebound:
            env[parameter.arg] = found
    other: SetStr = {
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
) -> DictStr:
    """Type the uppercase module-level constants that are never rebound.

    Args:
        module (Module): Parsed module.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        DictStr: Types by name for ``NAME = <provable>`` and
            ``NAME: <scalar> = ...`` statements whose name
            is bound once and never declared ``global``.

    """
    declared: SetStr = {
        name
        for node in walk(node=module)
        if isinstance(node, (Global, Nonlocal))
        for name in node.names
    }
    found: DictStr = {}
    for statement in module.body:
        name: StrOrNone = None
        kind: StrOrNone = None
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
        function (Function): Function definition.

    Returns:
        bool: Whether the function has no ``return`` or ``yield`` and its body
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
        statement (Raise): A ``raise`` statement.

    Returns:
        bool: ``True`` for ``raise NotImplementedError``
            with or without arguments.

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
        module (Module): Parsed module, marked in place.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        frozenset[str]: The names of the functions that never return.

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
    known: SetStr = set()
    for _round in range(Constants.noreturn_rounds):
        for call in calls:
            vars(call)[Constants.noreturn_mark] = (
                cast(typ="Name", val=call.func).id in known
            )
        found: SetStr = {
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
        function (Function): Function definition.

    Returns:
        frozenset[str]: Names declared ``global`` or ``nonlocal`` anywhere
            in the function, including nested functions.

    """
    names: SetStr = set()
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
        typer (_Typer): Typer whose environment is extended in place.
        function (Function): Function definition.
        fixed (frozenset[str]): Names that must keep their given type or stay
            untyped.

    """
    stored: dict[str, int] = _single_assignments(function=function)
    for node in own_nodes(function=function):
        match node:
            case Assign(targets=[Name(id=name)], value=value) if (
                stored.get(name) == 1 and name not in fixed
            ):
                before: int = typer.reads
                found: StrOrNone = typer.type_of(node=value)
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
        function (Function): Function definition.
        fixed (frozenset[str]): Names that must keep their given type or stay
            untyped.

    Returns:
        dict[str, list[AST]]: For each local bound at least twice, only by
            ``name = value``
            and ``name op= value`` statements, those statements.

    """
    parameters: SetStr = {
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
    blocked: SetStr = set(parameters) | set(fixed)
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
        typer (_Typer): Typer whose environment is extended in place.
        function (Function): Function definition.
        fixed (frozenset[str]): Names that must keep their given type or stay
            untyped.

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
            found: StrOrNone = _agreed_binding(
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
) -> StrOrNone:
    """Find the one type all of a local's bindings produce.

    Args:
        typer (_Typer): Typer holding the types settled so far.
        name (str): The local.
        statements (list[AST]): Its plain and augmented assignments.

    Returns:
        StrOrNone:
            The agreed type, or ``None`` when they disagree or cannot be typed.

    """
    values: list[expr] = [
        item.value for item in statements if isinstance(item, Assign)
    ]
    kinds: SetStr = set()
    for value in values:
        found: StrOrNone = typer.type_of(node=value)
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


def _join_types(*, types: ListStr) -> StrOrNone:
    """Combine the types of every exit of a function.

    Args:
        types (ListStr): One type per return path.

    Returns:
        StrOrNone: The common type, ``T | None`` for one type plus
            ``None``, or ``None`` when the paths disagree.

    """
    unique: ListStr = list(dict.fromkeys(types))
    others: ListStr = [item for item in unique if item != "None"]
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
) -> StrOrNone:
    """Prove a function's return annotation from its body.

    Args:
        function (Function): Function definition.
        known_types (Mapping[str, str]): Types of parameters (accepted hints or
            annotations).
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        StrOrNone: The annotation source, or ``None`` when it is not provable.

    """
    return provable_return_detail(
        function=function,
        known_types=known_types,
        counts=counts,
    )[0]


def _flat_arm(*, arm: expr) -> bool:
    """Tell whether a union arm carries no bracketed type arguments.

    Args:
        arm (expr): One union member expression.

    Returns:
        bool: ``True`` when the arm's spelling holds no ``[`` — subscripts and
            list literals are the only nodes that render one, aside from
            string or bytes constants that literally contain the character.

    """
    return all(
        not isinstance(node, (Subscript, List))
        and not (
            isinstance(node, Constant)
            and (
                (isinstance(node.value, str) and "[" in node.value)
                or (isinstance(node.value, bytes) and b"[" in node.value)
            )
        )
        for node in walk(node=arm)
    )


def _union_arms(*, kind: str) -> ListStr:
    """Split a union spelling into its arms.

    Args:
        kind (str): Annotation source such as ``int | None``.

    Returns:
        ListStr: The arms, or an empty list when ``kind`` is not a flat union.

    """
    try:
        node: expr = parse(source=kind, mode="eval").body
    except SyntaxError:
        return []
    arms: list[expr] = []
    pending: list[expr] = [node]
    while pending:
        current: expr = pending.pop()
        if isinstance(current, BinOp) and isinstance(current.op, BitOr):
            pending.extend((current.left, current.right))
        else:
            arms.append(current)
    texts: ListStr = [unparse(ast_obj=arm) for arm in arms]
    return (
        texts
        if len(texts) > 1 and all(_flat_arm(arm=arm) for arm in arms)
        else []
    )


def _narrowed(*, arms: ListStr, keep: SetStr) -> StrOrNone:
    """Join the arms that survive a test.

    Args:
        arms (ListStr): All arms of the union.
        keep (SetStr): Arm names that remain.

    Returns:
        StrOrNone: The surviving union, or ``None`` when nothing or
            everything stays (the test proves nothing then).

    """
    kept: ListStr = [arm for arm in arms if arm in keep]
    return " | ".join(kept) if 0 < len(kept) < len(arms) else None


def _isinstance_classes(*, test: Call) -> SetStr | None:
    """Read the class names of ``isinstance(name, C)`` or ``(C, D)``.

    Args:
        test (Call): An ``isinstance`` call.

    Returns:
        SetStr | None:
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
    arms: ListStr,
    when_none: bool,
) -> tuple[str, str, str] | None:
    """Arms of ``name is None`` (or ``is not None``).

    Args:
        name (str): The tested parameter.
        arms (ListStr): Its union arms.
        when_none (bool): ``True`` for ``is None``.

    Returns:
        tuple[str, str, str] | None:
            The name and the type it has when the test is true and when false.

    """
    true_arm: StrOrNone = _narrowed(arms=arms, keep={"None"})
    false_arm: StrOrNone = _narrowed(
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
    arms: ListStr,
) -> tuple[str, str, str] | None:
    """Arms of ``isinstance(name, C)``.

    Args:
        test (Call): The ``isinstance`` call.
        name (str): The tested parameter.
        arms (ListStr): Its union arms.

    Returns:
        tuple[str, str, str] | None:
            The name and the type it has when the test is true
            and when false. ``bool`` among the arms blocks
            ``int`` tests, since ``bool`` is an ``int`` instance.

    """
    classes: SetStr | None = _isinstance_classes(test=test)
    if classes is None or ({"int"} & classes and "bool" in arms):
        return None
    true_arm: StrOrNone = _narrowed(arms=arms, keep=classes)
    false_arm: StrOrNone = _narrowed(
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
        test (AST): An ``if`` condition.
        unions (Mapping[str, list[str]]): Union parameters by name, with their
            arms.

    Returns:
        tuple[str, str, str] | None:
            The name, its type when the test is true, and when it is
            false; or ``None`` when the test narrows nothing provably.

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
            kept: StrOrNone = _narrowed(
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
        node (AST): A statement.

    Returns:
        list[Return]: Its ``return`` statements.

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
) -> list[tuple[Return, DictStr]]:
    """Pair every return with the union parameters narrowed there.

    A narrowing test (``is None``, ``isinstance``) narrows its two arms; when
    one arm cannot fall through, the other arm's narrowing also holds for the
    statements after the ``if``.

    Args:
        body (list[stmt]): Statements in execution order.
        narrowed (Mapping[str, str]): Narrowings in force when the body starts.
        unions (Mapping[str, list[str]]): Union parameters by name, with their
            arms.
        defaults (Mapping[int, str]): Trusted ``if x is None: x = value``
            statements, by
            identity, mapped to the parameter they default.

    Returns:
        list[tuple[Return, DictStr]]: Each return with the types its narrowed
            names have at that point.

    """
    found: list[tuple[Return, DictStr]] = []
    current: DictStr = dict(narrowed)
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
        inside: DictStr = {**current, name: when_true}
        outside: DictStr = {**current, name: when_false}
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
        function (Function): Function definition.
        typer (_Typer): Typer for the assigned values.
        known_types (Mapping[str, str]): Declared types of the parameters.
        stored (Mapping[str, int]): How often each name is written in the
            function.

    Returns:
        dict[int, str]: The trusted ``if`` statements (by
            identity) mapped to the parameter.

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
        arms: ListStr = _union_arms(kind=known_types.get(name, ""))
        allowed: SetStr = {arm for arm in arms if arm != "None"}
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
) -> tuple[StrOrNone, bool]:
    """Prove a function's return annotation and say how it was proven.

    Every returned expression must have a type the syntax determines, using
    literals, operators, builtin constructors and typed parameters or
    single-assignment locals. Paths that fall off the end add ``None``.

    Args:
        function (Function): Function definition.
        known_types (Mapping[str, str]): Types of parameters (accepted hints or
            annotations).
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        tuple[StrOrNone, bool]: The annotation source (``None``
            when it is not provable) and whether
        the proof is *language-guaranteed*: it read the type of no parameter
            or variable, only literals, f-strings, ``not``, and builtins whose
            result type is fixed (``len``, ``str``, ``isinstance``,…).

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
    types: ListStr = []
    stored: dict[str, int] = _single_assignments(function=function)
    defaults: dict[int, str] = _defaulting_guards(
        function=function,
        typer=typer,
        known_types=known_types,
        stored=stored,
    )
    defaulted: SetStr = set(defaults.values())
    unions: dict[str, ListStr] = {
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
        saved: DictStr = {name: typer.env[name] for name in overrides}
        typer.env.update(overrides)
        result: StrOrNone = (
            "None" if node.value is None else typer.type_of(node=node.value)
        )
        typer.env.update(saved)
        if result is None:
            return None, False
        types.append(result)
    if can_fall_off(body=function.body):
        types.append("None")
    return _join_types(types=types), typer.reads == 0
