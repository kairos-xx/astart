"""Collect, from an untyped module, the evidence that leads to a type.

Everything here reads the AST of the untyped source (no text patterns, no
execution). For a parameter, a return or a variable it lists the facts a
reader would use to decide its type: default values, call sites that bind to
the parameter, return statements, assignments, mutations and how the body
uses the name. ``conclusion`` then compares what the evidence shows with the
type the author wrote.

Used by ``scripts/conversion_report.py``.
"""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    DictComp,
    Div,
    Expr,
    For,
    FunctionDef,
    GeneratorExp,
    JoinedStr,
    Lambda,
    List,
    ListComp,
    Module,
    Name,
    Not,
    Pass,
    Raise,
    Return,
    Set,
    SetComp,
    Starred,
    Subscript,
    Tuple,
    UnaryOp,
    Yield,
    YieldFrom,
    arg,
    arguments,
    expr,
    iter_child_nodes,
    parse,
    stmt,
    unparse,
    walk,
)
from collections import defaultdict
from dataclasses import dataclass, field, replace
from importlib import import_module
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


@final
class Constants:
    """Group module-level constants.

    Attributes:
        scalars: Python value class to type name.
        builtin_calls: Builtin call to the type it returns.
        str_methods: String methods that return ``str``.
        method_families: Method name to the kind of object that has it.
        common_methods: Method names of builtin types, never matched by name.
        max_calls: Call sites kept per parameter.
        max_usage: Body usages kept per parameter.
        text_limit: Longest expression text shown.

    """

    scalars: Final[dict[type, str]] = {
        bool: "bool",
        int: "int",
        float: "float",
        str: "str",
        bytes: "bytes",
        complex: "complex",
        type(None): "None",
    }
    builtin_calls: Final[dict[str, str]] = {
        "len": "int",
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "repr": "str",
        "list": "list[?]",
        "dict": "dict[?, ?]",
        "set": "set[?]",
        "tuple": "tuple[?]",
        "sorted": "list[?]",
    }
    str_methods: Final[frozenset[str]] = frozenset(
        {"join", "format", "strip", "lower", "upper", "replace", "title"},
    )
    method_families: Final[dict[str, str]] = {
        **dict.fromkeys(
            ("append", "extend", "insert", "pop", "remove", "sort", "reverse"),
            "a list",
        ),
        **dict.fromkeys(
            ("items", "keys", "values", "get", "update", "setdefault"),
            "a dict",
        ),
        **dict.fromkeys(("add", "discard", "union", "intersection"), "a set"),
        **dict.fromkeys(
            ("strip", "split", "lower", "upper", "startswith", "endswith"),
            "a str",
        ),
    }
    common_methods: Final[frozenset[str]] = frozenset(
        {
            "write",
            "read",
            "close",
            "copy",
            "clear",
            "count",
            "index",
            "format",
            "find",
            "replace",
            "append",
            "extend",
            "update",
            "get",
            "items",
            "keys",
            "values",
            "pop",
            "add",
            "remove",
            "join",
            "split",
        },
    )
    max_calls: Final[int] = 4
    max_usage: Final[int] = 4
    text_limit: Final[int] = 90


@final
@dataclass(frozen=True, slots=True)
class Evidence:
    """One fact in the code that bears on a type.

    Attributes:
        line: Line of the fact in the untyped source.
        kind: What sort of fact (default value, call site, return, ...).
        text: What the code says, shortened.
        type: The type the fact suggests, when it does.
        certain: ``False`` when a call site was matched only by name.

    """

    line: int
    kind: str
    text: str
    type: str | None = None
    certain: bool = True


@final
@dataclass(slots=True)
class Function:
    """A function or method of the module, keyed like the scorer.

    Attributes:
        key: Qualified path, for example ``Class.method``.
        node: The definition.
        owner: Name of the enclosing class when it is a method.
        static: Whether it is a ``staticmethod``.
        classmethod: Whether it is a ``classmethod``.

    """

    key: str
    node: FunctionDef | AsyncFunctionDef
    owner: str | None
    static: bool
    classmethod: bool


@final
@dataclass(slots=True)
class Index:
    """The module, indexed for evidence lookup.

    Attributes:
        functions: Function by qualified key.
        by_name: Functions by simple name.
        classes: Class names defined in the module.
        class_nodes: Class definition by qualified key.
        calls: Every call with the function it sits in.
        body: Statements of the module.

    """

    functions: dict[str, Function] = field(default_factory=dict)
    by_name: dict[str, list[Function]] = field(
        default_factory=lambda: defaultdict(list),
    )
    classes: set[str] = field(default_factory=set)
    class_nodes: dict[str, ClassDef] = field(default_factory=dict)
    calls: list[tuple[Call, Function | None]] = field(default_factory=list)
    body: list[AST] = field(default_factory=list)


def _decorated(*, node: FunctionDef | AsyncFunctionDef, name: str) -> bool:
    """Tell whether a function carries a decorator with the given name.

    Args:
        node: The definition.
        name: Decorator name.

    Returns:
        ``True`` when a plain-name decorator matches.

    """
    return any(
        isinstance(item, Name) and item.id == name
        for item in node.decorator_list
    )


def _collect(
    *,
    node: AST,
    trail: tuple[str, ...],
    owner: str | None,
    index: Index,
) -> None:
    """Index functions and classes the way the scorer walks them.

    Args:
        node: Node whose body is scanned.
        trail: Qualified-name prefix.
        owner: Enclosing class name, when the scan is inside a class.
        index: Destination, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            key: str = ".".join((*trail, child.name))
            function: Function = Function(
                key=key,
                node=child,
                owner=owner,
                static=_decorated(node=child, name="staticmethod"),
                classmethod=_decorated(node=child, name="classmethod"),
            )
            index.functions[key] = function
            index.by_name[child.name].append(function)
            _collect(
                node=child,
                trail=(*trail, child.name),
                owner=None,
                index=index,
            )
        elif isinstance(child, ClassDef):
            index.classes.add(child.name)
            index.class_nodes[".".join((*trail, child.name))] = child
            _collect(
                node=child,
                trail=(*trail, child.name),
                owner=child.name,
                index=index,
            )


def _enclosing(*, line: int, ordered: list[Function]) -> Function | None:
    """Find the innermost function that contains a line.

    Args:
        line: Source line.
        ordered: Functions sorted by their first line.

    Returns:
        The innermost containing function, or ``None``.

    """
    found: Function | None = None
    for function in ordered:
        if function.node.lineno > line:
            break
        if line <= (function.node.end_lineno or function.node.lineno):
            found = function
    return found


def build_index(*, source: str) -> Index:
    """Index an untyped module for evidence lookup.

    Args:
        source: Untyped source.

    Returns:
        The index.

    """
    tree: Module = parse(source=source)
    index: Index = Index(body=list(tree.body))
    _collect(node=tree, trail=(), owner=None, index=index)
    ordered: list[Function] = sorted(
        index.functions.values(),
        key=lambda function: function.node.lineno,
    )
    for node in walk(node=tree):
        if isinstance(node, Call):
            index.calls.append(
                (node, _enclosing(line=node.lineno, ordered=ordered)),
            )
    return index


def short(*, node: AST | str) -> str:
    """Render an expression for display, shortened.

    Args:
        node: An AST node or text.

    Returns:
        Single-line text of at most ``Constants.text_limit`` characters.

    """
    text: str = node if isinstance(node, str) else unparse(ast_obj=node)
    text = " ".join(text.split())
    limit: int = Constants.text_limit
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _join(*, parts: list[str]) -> str:
    """Join type names into a union, without repeats.

    Args:
        parts: Type names.

    Returns:
        The names in first-seen order, separated by `` | ``.

    """
    return " | ".join(dict.fromkeys(parts))


def type_of(*, node: expr, index: Index) -> str | None:
    """Give the type an expression shows on its face.

    Args:
        node: An expression.
        index: The module index (for class names).

    Returns:
        A type name, or ``None`` when the expression does not show one.
        ``?`` marks an element type the expression does not show.

    """
    if isinstance(node, (Constant, JoinedStr, Compare)):
        return _literal_type(node=node)
    if isinstance(
        node,
        (
            List,
            Set,
            Tuple,
            Dict,
            ListComp,
            SetComp,
            DictComp,
            GeneratorExp,
        ),
    ):
        return _collection_type(node=node, index=index)
    if isinstance(node, (UnaryOp, BinOp)):
        return _operator_type(node=node, index=index)
    if isinstance(node, Call):
        return _call_type(node=node, index=index)
    return None


def _literal_type(*, node: Constant | JoinedStr | Compare) -> str | None:
    """Give the type a literal, f-string or comparison shows.

    Args:
        node: The expression.

    Returns:
        A type name, or ``None`` for a constant of another kind.

    """
    if isinstance(node, Constant):
        return Constants.scalars.get(type(node.value))
    if isinstance(node, JoinedStr):
        return "str"
    return "bool"


def _collection_type(
    *,
    node: List
    | Set
    | Tuple
    | Dict
    | ListComp
    | SetComp
    | DictComp
    | GeneratorExp,
    index: Index,
) -> str | None:
    """Give the type a collection display or comprehension shows.

    Args:
        node: The expression.
        index: The module index (for element types).

    Returns:
        A type name with ``?`` element markers, or ``None``.

    """
    if isinstance(node, (ListComp, GeneratorExp)):
        return "list[?]"
    if isinstance(node, SetComp):
        return "set[?]"
    if isinstance(node, DictComp):
        return "dict[?, ?]"
    if isinstance(node, Dict):
        return _mapping_type(node=node, index=index)
    return _items_type(node=node, index=index)


def _items_type(*, node: List | Set | Tuple, index: Index) -> str | None:
    """Give the type a list, set or tuple display shows.

    Args:
        node: The expression.
        index: The module index (for element types).

    Returns:
        A type name, or ``None`` when an element shows no type.

    """
    if isinstance(node, Tuple):
        return _tuple_type(node=node, index=index)
    kind: str = "list" if isinstance(node, List) else "set"
    if not node.elts:
        return f"{kind}[?]"
    parts: list[str | None] = [
        type_of(node=item, index=index) for item in node.elts
    ]
    if any(part is None for part in parts):
        return None
    return f"{kind}[{_join(parts=[p for p in parts if p])}]"


def _tuple_type(*, node: Tuple, index: Index) -> str | None:
    """Give the type a tuple display shows.

    Args:
        node: The expression.
        index: The module index (for element types).

    Returns:
        A type name, or ``None`` when an element shows no type.

    """
    parts: list[str | None] = [
        type_of(node=item, index=index) for item in node.elts
    ]
    if any(part is None for part in parts):
        return None
    return "tuple[" + (", ".join(p for p in parts if p) or "()") + "]"


def _mapping_type(*, node: Dict, index: Index) -> str | None:
    """Give the type a dict display shows.

    Args:
        node: The expression.
        index: The module index (for key and value types).

    Returns:
        A type name, or ``None`` when a key or value shows no type.

    """
    if not node.keys:
        return "dict[?, ?]"
    keys: list[str | None] = [
        None if key is None else type_of(node=key, index=index)
        for key in node.keys
    ]
    values: list[str | None] = [
        type_of(node=value, index=index) for value in node.values
    ]
    if None in keys or None in values:
        return None
    return (
        f"dict[{_join(parts=[k for k in keys if k])}, "
        f"{_join(parts=[v for v in values if v])}]"
    )


def _operator_type(*, node: UnaryOp | BinOp, index: Index) -> str | None:
    """Give the type a unary or binary operation shows.

    Args:
        node: The expression.
        index: The module index (for operand types).

    Returns:
        A type name, or ``None`` when the operands show none.

    """
    if isinstance(node, UnaryOp):
        if isinstance(node.op, Not):
            return "bool"
        return type_of(node=node.operand, index=index)
    left: str | None = type_of(node=node.left, index=index)
    right: str | None = type_of(node=node.right, index=index)
    if isinstance(node.op, Div) and left in {"int", "float"}:
        return "float"
    if left == right and left in {"int", "float", "str", "bytes"}:
        return left
    if {left, right} == {"int", "float"}:
        return "float"
    return None


def _call_type(*, node: Call, index: Index) -> str | None:
    """Give the type a call shows on its face.

    Args:
        node: The expression.
        index: The module index (for class names).

    Returns:
        A type name, or ``None`` when the call shows none.

    """
    func: expr = node.func
    if isinstance(func, Name):
        if func.id in index.classes:
            return func.id
        return Constants.builtin_calls.get(func.id)
    if (
        isinstance(func, Attribute)
        and isinstance(func.value, Constant)
        and isinstance(func.value.value, str)
        and func.attr in Constants.str_methods
    ):
        return "str"
    return None


def arms(*, text: str) -> frozenset[str]:
    """Split a type into the arms of its top-level union.

    Args:
        text: Type text.

    Returns:
        The arms as normalised text, so ``A | B`` equals ``B | A``.

    """
    try:
        root: AST = parse(source=text, mode="eval").body
    except SyntaxError:
        return frozenset({text.replace(" ", "")})
    found: list[str] = []
    stack: list[AST] = [root]
    while stack:
        node: AST = stack.pop()
        if isinstance(node, BinOp) and isinstance(node.op, BitOr):
            stack.extend((node.left, node.right))
        else:
            found.append(unparse(ast_obj=node))
    return frozenset(found)


def _own_nodes(*, body: Iterable[AST]) -> list[AST]:
    """List the nodes of a scope without entering nested scopes.

    Args:
        body: Statements of one scope.

    Returns:
        Every node of the scope; nested definitions appear but are not entered.

    """
    found: list[AST] = []
    stack: list[AST] = list(body)
    while stack:
        node: AST = stack.pop()
        found.append(node)
        stack.extend(
            child
            for child in iter_child_nodes(node=node)
            if not isinstance(
                child,
                (FunctionDef, AsyncFunctionDef, Lambda, ClassDef),
            )
        )
    return found


def _targets(
    *,
    call: Call,
    caller: Function | None,
    index: Index,
) -> list[tuple[Function, bool, bool]]:
    """Find which functions a call may reach.

    Args:
        call: A call expression.
        caller: The function the call sits in.
        index: The module index.

    Returns:
        ``(function, certain, skips_receiver)`` triples.

    """
    func: expr = call.func
    found: list[tuple[Function, bool, bool]] = []
    max_targets: int = 3
    if isinstance(func, Name):
        plain: list[Function] = [
            f for f in index.by_name.get(func.id, []) if f.owner is None
        ]
        found.extend((f, len(plain) == 1, False) for f in plain)
        if func.id in index.classes:
            ctors: list[Function] = [
                f
                for f in index.by_name.get("__init__", [])
                if f.owner == func.id
            ]
            found.extend((f, len(ctors) == 1, True) for f in ctors)
    elif isinstance(func, Attribute):
        methods: list[Function] = [
            f for f in index.by_name.get(func.attr, []) if f.owner
        ]
        receiver: expr = func.value
        certain: bool = False
        skip: bool = True
        if (
            isinstance(receiver, Name)
            and receiver.id in {"self", "cls"}
            and caller is not None
            and caller.owner
        ):
            methods = [m for m in methods if m.owner == caller.owner]
            certain = len(methods) == 1
        elif isinstance(receiver, Name) and receiver.id in index.classes:
            methods = [m for m in methods if m.owner == receiver.id]
            certain = len(methods) == 1
            skip = False
        elif len(methods) > max_targets:
            methods = []
        else:
            certain = (
                len(methods) == 1 and func.attr not in Constants.common_methods
            )
        found.extend((m, certain, skip and not m.static) for m in methods)
    return found


def _bound(
    *,
    call: Call,
    function: Function,
    name: str,
    skip: bool,
) -> expr | None:
    """Find the argument a call passes for one parameter.

    Args:
        call: A call expression.
        function: The called function.
        name: Parameter name.
        skip: Whether the first parameter is the receiver.

    Returns:
        The argument expression, or ``None`` when it cannot be matched.

    """
    if any(isinstance(arg, Starred) for arg in call.args):
        return None
    args: arguments = function.node.args
    names: list[str] = [a.arg for a in (*args.posonlyargs, *args.args)]
    offset: int = 1 if skip and names else 0
    if name in names:
        position: int = names.index(name) - offset
        if 0 <= position < len(call.args):
            return call.args[position]
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


type _Fact = tuple[str, str, str | None]


def _method_fact(*, node: AST, name: str) -> _Fact | None:
    """Match a method call on the parameter.

    Args:
        node: The node.
        name: Parameter name.

    Returns:
        ``(what, text, hint)``, or ``None`` when the node is not a match.

    """
    if not (
        isinstance(node, Call)
        and isinstance(node.func, Attribute)
        and isinstance(node.func.value, Name)
        and node.func.value.id == name
    ):
        return None
    family: str | None = Constants.method_families.get(node.func.attr)
    return (
        "body calls a method",
        short(node=node),
        None if family is None else f"is {family}",
    )


def _loop_fact(*, node: AST, name: str) -> _Fact | None:
    """Match iteration over or indexing of the parameter.

    Args:
        node: The node.
        name: Parameter name.

    Returns:
        ``(what, text, hint)``, or ``None`` when the node is not a match.

    """
    if (
        isinstance(node, For)
        and isinstance(node.iter, Name)
        and node.iter.id == name
    ):
        return (
            "body iterates it",
            f"for {short(node=node.target)} in {name}",
            None,
        )
    if (
        isinstance(node, Subscript)
        and isinstance(node.value, Name)
        and node.value.id == name
    ):
        return ("body indexes it", short(node=node), None)
    return None


def _binop_fact(*, node: AST, name: str, index: Index) -> _Fact | None:
    """Match arithmetic that uses the parameter.

    Args:
        node: The node.
        name: Parameter name.
        index: The module index (for the other operand's type).

    Returns:
        ``(what, text, hint)``, or ``None`` when the node is not a match.

    """
    if not isinstance(node, BinOp):
        return None
    if not any(
        isinstance(side, Name) and side.id == name
        for side in (node.left, node.right)
    ):
        return None
    other: expr = (
        node.right
        if isinstance(node.left, Name) and node.left.id == name
        else node.left
    )
    return (
        "body uses it in arithmetic",
        short(node=node),
        type_of(node=other, index=index),
    )


def _compare_fact(*, node: AST, name: str) -> _Fact | None:
    """Match a ``None`` comparison of the parameter.

    Args:
        node: The node.
        name: Parameter name.

    Returns:
        ``(what, text, hint)``, or ``None`` when the node is not a match.

    """
    if not (isinstance(node, Compare) and isinstance(node.left, Name)):
        return None
    if node.left.id != name:
        return None
    if not any(
        isinstance(comp, Constant) and comp.value is None
        for comp in node.comparators
    ):
        return None
    return ("body compares it with None", short(node=node), None)


def _builtin_fact(*, node: AST, name: str) -> _Fact | None:
    """Match an ``isinstance`` or ``len`` call on the parameter.

    Args:
        node: The node.
        name: Parameter name.

    Returns:
        ``(what, text, hint)``, or ``None`` when the node is not a match.

    """
    if not (
        isinstance(node, Call)
        and isinstance(node.func, Name)
        and node.func.id in {"isinstance", "len"}
        and node.args
        and isinstance(node.args[0], Name)
        and node.args[0].id == name
    ):
        return None
    return (f"body calls {node.func.id}", short(node=node), None)


def _usage(*, function: Function, name: str, index: Index) -> list[Evidence]:
    """Describe how a function body uses one parameter.

    Args:
        function: The function.
        name: Parameter name.
        index: The module index.

    Returns:
        Evidence about methods called, iteration, subscripts and operators.

    """
    found: list[Evidence] = []
    seen: set[str] = set()

    def add(
        *,
        node: AST,
        what: str,
        text: str,
        hint: str | None = None,
    ) -> None:
        """Append one usage fact, skipping duplicates.

        Args:
            node: The AST node the fact came from.
            what: The usage kind.
            text: The usage description.
            hint: The apparent type, when known.

        """
        marker: str = f"{what}:{text}"
        if marker not in seen:
            seen.add(marker)
            found.append(
                Evidence(
                    line=getattr(node, "lineno", function.node.lineno),
                    kind=what,
                    text=text,
                    type=hint,
                ),
            )

    for node in _own_nodes(body=function.node.body):
        fact: _Fact | None = (
            _method_fact(node=node, name=name)
            or _loop_fact(node=node, name=name)
            or _binop_fact(node=node, name=name, index=index)
            or _compare_fact(node=node, name=name)
            or _builtin_fact(node=node, name=name)
        )
        if fact is not None:
            what, text, hint = fact
            add(node=node, what=what, text=text, hint=hint)
    found.sort(key=lambda item: item.line)
    return found[: Constants.max_usage]


def _siblings(*, index: Index, function: Function) -> list[Evidence]:
    """Point at same-named methods of other classes.

    Args:
        index: The module index.
        function: A method.

    Returns:
        Up to three pointers (no type): the types of a stub or an override
        usually come from these implementations.

    """
    if not function.owner:
        return []
    others: list[Function] = [
        other
        for other in index.by_name.get(function.node.name, [])
        if other.owner and other.key != function.key
    ]
    return [
        Evidence(
            line=other.node.lineno,
            kind=f"same-named method in {other.owner}",
            text=short(node=f"{other.key}({unparse(ast_obj=other.node.args)})"),
            certain=False,
        )
        for other in others[:3]
    ]


def _is_stub(*, function: Function) -> bool:
    """Tell whether a function body is only a docstring, ``pass`` or ``...``.

    Args:
        function: The function.

    Returns:
        ``True`` for an empty (stub) body.

    """
    return all(
        isinstance(node, Pass)
        or (
            isinstance(node, Expr)
            and isinstance(node.value, Constant)
            and (isinstance(node.value.value, str) or node.value.value is ...)
        )
        for node in function.node.body
    )


def parameter_evidence(
    *,
    index: Index,
    function: Function,
    name: str,
) -> list[Evidence]:
    """Collect the evidence for the type of one parameter.

    Args:
        index: The module index.
        function: The function that owns the parameter.
        name: Parameter name.

    Returns:
        Default value, call sites and body usage, in line order.

    """
    found: list[Evidence] = []
    args: arguments = function.node.args
    positional: list[arg] = [*args.posonlyargs, *args.args]
    defaults: list[expr | None] = [None] * (
        len(positional) - len(args.defaults)
    ) + list(args.defaults)
    pairs: list[tuple[arg, expr | None]] = [
        *zip(positional, defaults, strict=False),
        *zip(args.kwonlyargs, args.kw_defaults, strict=False),
    ]
    for parameter, default in pairs:
        if parameter.arg == name and default is not None:
            found.append(
                Evidence(
                    line=default.lineno,
                    kind="default value",
                    text=short(node=default),
                    type=type_of(node=default, index=index),
                ),
            )
    sites: list[Evidence] = []
    for call, caller in index.calls:
        for target, certain, skip in _targets(
            call=call,
            caller=caller,
            index=index,
        ):
            if target.key != function.key:
                continue
            argument: expr | None = _bound(
                call=call,
                function=target,
                name=name,
                skip=skip,
            )
            if argument is not None:
                sites.append(
                    Evidence(
                        line=call.lineno,
                        kind="call site passes",
                        text=f"{short(node=call)}  ->  {short(node=argument)}",
                        type=type_of(node=argument, index=index),
                        certain=certain,
                    ),
                )
    sure: list[Evidence] = sorted(
        (site for site in sites if site.certain),
        key=lambda site: (site.type is None, site.line),
    )
    found.extend(sure[: Constants.max_calls])
    if not sure:
        found.extend(
            replace(site, type=None) for site in sites[:2] if not site.certain
        )
    found.extend(_siblings(index=index, function=function))
    found.extend(_usage(function=function, name=name, index=index))
    found.sort(key=lambda item: item.line)
    return found


def _falls_off(*, function: Function) -> bool:
    """Tell whether a function can end without returning a value.

    Args:
        function: The function.

    Returns:
        ``True`` when some path reaches the end of the body.

    """
    try:
        check: Callable[[list[stmt]], bool] = import_module(
            name="astart.rules.provable",
        ).can_fall_off
        return check(function.node.body)
    except (ImportError, AttributeError, TypeError):
        last: stmt = function.node.body[-1]
        return not isinstance(last, (Return, Raise))


def return_evidence(*, index: Index, function: Function) -> list[Evidence]:
    """Collect the evidence for the return type of a function.

    Args:
        index: The module index.
        function: The function.

    Returns:
        Every ``return`` expression, ``yield`` and fall-off path.

    """
    nodes: list[AST] = _own_nodes(body=function.node.body)
    found: list[Evidence] = []
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        found.append(
            Evidence(
                line=function.node.lineno,
                kind="generator",
                text="the body contains `yield`",
            ),
        )
    for node in nodes:
        if isinstance(node, Return):
            value: expr | None = node.value
            found.append(
                Evidence(
                    line=node.lineno,
                    kind="return",
                    text="return" if value is None else short(node=value),
                    type="None"
                    if value is None
                    else type_of(node=value, index=index),
                ),
            )
    if _is_stub(function=function):
        found.append(
            Evidence(
                line=function.node.lineno,
                kind="stub body",
                text=(
                    "empty body (docstring or pass): the type describes "
                    "what the implementations return"
                ),
            ),
        )
        found.extend(_siblings(index=index, function=function))
    elif _falls_off(function=function):
        found.append(
            Evidence(
                line=function.node.end_lineno or function.node.lineno,
                kind="falls off the end",
                text="some path ends without `return`, so it returns None",
                type="None",
            ),
        )
    found.sort(key=lambda item: item.line)
    return found[:10]


def variable_evidence(*, index: Index, key: str) -> list[Evidence]:
    """Collect the evidence for the type of a variable.

    Args:
        index: The module index.
        key: Variable path, for example ``function.name``.

    Returns:
        Assignments and mutations of the name in its scope.

    """
    scope, _, name = key.rpartition(".")
    body: Iterable[AST]
    if scope in index.functions:
        body = list(index.functions[scope].node.body)
    elif scope in index.class_nodes:
        body = list(index.class_nodes[scope].body)
    elif not scope:
        body = index.body
    else:
        return []
    found: list[Evidence] = []
    for node in _own_nodes(body=body):
        if isinstance(node, Assign) and any(
            isinstance(t, Name) and t.id == name for t in node.targets
        ):
            found.append(
                Evidence(
                    line=node.lineno,
                    kind="assignment",
                    text=f"{name} = {short(node=node.value)}",
                    type=type_of(node=node.value, index=index),
                ),
            )
        elif (
            isinstance(node, AugAssign)
            and isinstance(node.target, Name)
            and node.target.id == name
        ):
            found.append(
                Evidence(
                    line=node.lineno,
                    kind="updated in place",
                    text=short(node=node),
                ),
            )
        elif isinstance(node, For) and isinstance(node.target, Name):
            if node.target.id == name:
                found.append(
                    Evidence(
                        line=node.lineno,
                        kind="loop variable",
                        text=f"for {name} in {short(node=node.iter)}",
                    ),
                )
        elif (
            isinstance(node, Call)
            and isinstance(node.func, Attribute)
            and isinstance(node.func.value, Name)
            and node.func.value.id == name
            and node.func.attr
            in {"append", "add", "extend", "insert", "update"}
            and node.args
        ):
            found.append(
                Evidence(
                    line=node.lineno,
                    kind="adds elements",
                    text=short(node=node),
                    type=None,
                ),
            )
    found.sort(key=lambda item: item.line)
    return found[:8]


def evidence_for(
    *,
    index: Index,
    key: str,
    scope: str,
) -> list[Evidence] | None:
    """Collect the evidence for any scored node.

    Args:
        index: The module index.
        key: Node path as the scorer names it.
        scope: ``parameters_and_returns`` or ``variables``.

    Returns:
        The evidence, or ``None`` when the node is not in the index.

    """
    if scope == "variables":
        return variable_evidence(index=index, key=key)
    if key.endswith("->"):
        function: Function | None = index.functions.get(key[:-2])
        return (
            None
            if function is None
            else return_evidence(index=index, function=function)
        )
    owner, _, name = key.rpartition(".")
    function = index.functions.get(owner)
    if function is None:
        return None
    return parameter_evidence(index=index, function=function, name=name)


def conclusion(*, author: str, evidence: list[Evidence]) -> str:
    """Compare what the evidence shows with the author's type.

    Args:
        author: The type the author wrote.
        evidence: Evidence from this module.

    Returns:
        One or two sentences saying how the evidence relates to the type.

    """
    wanted: frozenset[str] = arms(text=author)
    typed: list[Evidence] = [
        e for e in evidence if e.type and "?" not in e.type
    ]
    if not typed:
        if any(e.type and "?" in e.type for e in evidence):
            return (
                "The sources show a container but not its element type, "
                f"so nothing here fixes `{author}`; the author's choice adds "
                "knowledge from outside this file."
            )
        return (
            f"No source in this file shows the type; `{author}` is the "
            "author's intent (naming, documentation or use elsewhere)."
        )
    shown: frozenset[str] = frozenset[str]().union(
        *(arms(text=e.type or "") for e in typed),
    )
    exact: list[Evidence] = [
        e for e in typed if arms(text=e.type or "") == wanted
    ]
    if shown == wanted:
        names: str = " | ".join(sorted(shown))
        return (
            f"Joining what the {len(typed)} typed source(s) show "
            f"(`{names}`) gives exactly the author's `{author}`."
        )
    if exact:
        return (
            f"{len(exact)} of {len(typed)} typed source(s) show exactly "
            f"`{author}`; the others add nothing that contradicts it."
        )
    if shown <= wanted:
        unexplained: str = " | ".join(sorted(wanted - shown))
        return (
            f"The typed source(s) explain `{' | '.join(sorted(shown))}`; "
            f"nothing in this file shows `{unexplained}`, the part the "
            f"author adds to reach `{author}`."
        )
    return (
        (
            f"The sources show `{' | '.join(sorted(shown))}`; the author "
            f"widened to the top type (`{author}`). A narrower type that "
            "the evidence supports is valid for every caller in this file."
        )
        if "object" in author
        else (
            f"The sources show `{' | '.join(sorted(shown))}`, which does not "
            f"add up to `{author}`: either a rule is missing or the author "
            "knew something this file does not say."
        )
    )
