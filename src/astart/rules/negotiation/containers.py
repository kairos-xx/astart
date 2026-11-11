"""Find what is put into a local container that starts out empty.

``out = []`` followed by ``out.append(x)`` is a ``list`` of whatever ``x``
is. That holds only while every use of ``out`` is understood: a use the
analysis does not recognise (passing it to a function, ``extend``, a closure)
could add anything, so the container is then reported as escaping.

"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Dict,
    DictComp,
    For,
    FunctionDef,
    If,
    IfExp,
    Lambda,
    List,
    ListComp,
    Load,
    Name,
    Not,
    Return,
    Set,
    SetComp,
    Starred,
    Subscript,
    Tuple,
    UnaryOp,
    While,
    comprehension,
    expr,
    iter_child_nodes,
    keyword,
    walk,
)
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Mapping

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        constructors (Final[dict[str, str]]): Calls that build an empty
            container, by kind.
        adders (Final[dict[str, dict[str, int]]]): Method name to the index of
            the added element, by kind.
        readers (Final[dict[str, frozenset[str]]]): Methods that never add an
            element, by kind.
        pure_calls (Final[frozenset[str]]): Builtins that only read their
            arguments.
        scopes (Final[tuple[type[AST], ...]]): Node types that open a scope
            element flow must not cross.

    """

    constructors: Final[dict[str, str]] = {"list": "list", "set": "set"}
    adders: Final[dict[str, dict[str, int]]] = {
        "list": {"append": 0, "insert": 1},
        "set": {"add": 0},
        "dict": {},
    }
    readers: Final[dict[str, frozenset[str]]] = {
        "list": frozenset(
            {"pop", "remove", "clear", "sort", "reverse", "index", "count"},
        ),
        "set": frozenset({"pop", "remove", "discard", "clear"}),
        "dict": frozenset(
            {
                "get",
                "items",
                "keys",
                "values",
                "copy",
                "pop",
                "popitem",
                "clear",
            },
        ),
    }
    pure_calls: Final[frozenset[str]] = frozenset(
        {
            "len",
            "sorted",
            "list",
            "tuple",
            "set",
            "frozenset",
            "sum",
            "min",
            "max",
            "any",
            "all",
            "reversed",
            "enumerate",
            "iter",
            "bool",
            "str",
            "repr",
        },
    )
    scopes: Final[tuple[type[AST], ...]] = (
        FunctionDef,
        AsyncFunctionDef,
        Lambda,
        ClassDef,
    )


def empty_kind(*, value: expr, counts: Mapping[str, int]) -> str | None:
    """Tell whether an expression builds an empty list or set.

    Args:
        value (expr): The assigned expression.
        counts (Mapping[str, int]): Module binding counts, to see that
            ``list`` /``set`` are the builtins.

    Returns:
        str | None: ``"list"`` or ``"set"``, or ``None``.

    """
    if isinstance(value, List) and not value.elts:
        return "list"
    if (
        isinstance(value, Call)
        and isinstance(value.func, Name)
        and not value.args
        and not value.keywords
        and value.func.id in Constants.constructors
        and counts.get(value.func.id, 0) == 0
    ):
        return Constants.constructors[value.func.id]
    return None


def literal_kind(*, value: expr) -> str | None:
    """Tell whether an expression builds a non-empty list, set or dict.

    Args:
        value (expr): The assigned expression.

    Returns:
        str | None: ``"list"``, ``"set"`` or ``"dict"`` for
            a literal or comprehension, or ``None``.

    """
    if isinstance(value, (List, ListComp)) and not (
        isinstance(value, List) and not value.elts
    ):
        return "list"
    if isinstance(value, (Set, SetComp)):
        return "set"
    if isinstance(value, (Dict, DictComp)) and not (
        isinstance(value, Dict) and not value.keys
    ):
        return "dict"
    return None


def _parents(*, function: Function) -> dict[int, AST]:
    """Map each node of a function to its parent.

    Args:
        function (Function): Function definition.

    Returns:
        dict[int, AST]: Parent node by child identity.

    """
    found: dict[int, AST] = {}
    for parent in walk(node=function):
        for child in iter_child_nodes(node=parent):
            found[id(child)] = parent
    return found


def _read_only(
    *,
    name: AST,
    parent: AST,
    parents: Mapping[int, AST],
    counts: Mapping[str, int],
) -> bool:
    """Tell whether a use of the container cannot add an element.

    Args:
        name (AST): The use.
        parent (AST): Its parent node.
        parents (Mapping[int, AST]): Parent map of the function.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        bool: ``True`` for iteration, tests, subscript reads,
            returns (also inside a returned tuple) and
            the builtins that only read their argument.

    """
    if isinstance(parent, (For, comprehension)):
        return parent.iter is name
    if isinstance(parent, (If, While, IfExp)):
        return parent.test is name
    if isinstance(parent, Subscript):
        return parent.value is name and isinstance(parent.ctx, Load)
    if isinstance(parent, UnaryOp):
        return isinstance(parent.op, Not)
    if (
        _unpacked(name=name, parent=parent)
        or isinstance(parent, (Return, Compare, BoolOp))
    ) or (
        isinstance(parent, Tuple)
        and isinstance(parents.get(id(parent)), Return)
    ):
        return True
    return (
        isinstance(parent, Call)
        and isinstance(parent.func, Name)
        and parent.func.id in Constants.pure_calls
        and counts.get(parent.func.id, 0) == 0
    )


def fillings(
    *,
    function: Function,
    name: str,
    kind: str,
    counts: Mapping[str, int],
) -> tuple[expr, ...] | None:
    """List the elements added to a container, or report that it escapes.

    Args:
        function (Function): Function whose body holds the container.
        name (str): The local's name.
        kind (str): ``"list"`` or ``"set"``.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        tuple[expr, ...] | None:
            The added element expressions in source order, or ``None``
            when some use of the container is not understood.

    """
    parents: dict[int, AST] = _parents(function=function)
    added: list[expr] = []
    for node in walk(node=function):
        if not (
            isinstance(node, Name)
            and node.id == name
            and isinstance(node.ctx, Load)
        ):
            continue
        parent: AST | None = parents.get(id(node))
        if parent is None or _inside_other_scope(
            node=node,
            parents=parents,
            function=function,
        ):
            return None
        if isinstance(parent, Attribute) and parent.value is node:
            element: expr | bool | None = _method_use(
                attribute=parent,
                parents=parents,
                kind=kind,
            )
            if element is False:
                return None
            if isinstance(element, expr):
                added.append(element)
        elif not _read_only(
            name=node,
            parent=parent,
            parents=parents,
            counts=counts,
        ):
            return None
    return tuple(added)


def _inside_other_scope(
    *,
    node: AST,
    parents: dict[int, AST],
    function: Function,
) -> bool:
    """Tell whether a use sits in a nested function, lambda or class.

    Args:
        node (AST): The use.
        parents (dict[int, AST]): Parent map of the function.
        function (Function): The enclosing function.

    Returns:
        bool: ``True`` when a scope other than the function lies between them.

    """
    current: AST | None = parents.get(id(node))
    while current is not None and current is not function:
        if isinstance(current, Constants.scopes):
            return True
        current = parents.get(id(current))
    return False


def _method_use(
    *,
    attribute: Attribute,
    parents: dict[int, AST],
    kind: str,
) -> expr | bool | None:
    """Judge one ``container.method`` use.

    Args:
        attribute (Attribute): The attribute access on the container.
        parents (dict[int, AST]): Parent map of the function.
        kind (str): ``"list"`` or ``"set"``.

    Returns:
        expr | bool | None:
            The added element expression, ``None`` for a method that
            adds nothing, or ``False`` when the use is not understood.

    """
    call: AST | None = parents.get(id(attribute))
    if not (isinstance(call, Call) and call.func is attribute):
        return False
    if attribute.attr in Constants.readers[kind]:
        return None
    position: int | None = Constants.adders[kind].get(attribute.attr)
    if position is None or call.keywords or len(call.args) <= position:
        return False
    return call.args[position]


def _unpacked(*, name: AST, parent: AST) -> bool:
    """Tell whether a use only unpacks the container into something else.

    Args:
        name (AST): The use.
        parent (AST): Its parent node.

    Returns:
        bool: ``True`` for ``*name`` and ``**name`` in a call, and ``**name``
            or ``*name`` in a display; unpacking reads the container.

    """
    if isinstance(parent, Starred):
        return parent.value is name
    if isinstance(parent, keyword):
        return parent.arg is None and parent.value is name
    if isinstance(parent, Dict):
        return any(
            key is None and value is name
            for key, value in zip(parent.keys, parent.values, strict=True)
        )
    return False


def attribute_risky(
    *,
    function: Function,
    receiver: str,
    attribute: str,
    counts: Mapping[str, int],
) -> bool:
    """Tell whether a method does something unknown with ``self.attribute``.

    A mutable container held in an attribute can change its element type
    through any use that is not a plain read, so such an attribute may only
    keep a container type when this returns ``False`` for every method.

    Args:
        function (Function): A method of the class.
        receiver (str): Name of the instance parameter.
        attribute (str): The attribute name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        bool: ``True`` when some load of the attribute is not a recognised
            read.

    """
    parents: dict[int, AST] = _parents(function=function)
    for node in walk(node=function):
        if not (
            isinstance(node, Attribute)
            and node.attr == attribute
            and isinstance(node.ctx, Load)
            and isinstance(node.value, Name)
            and node.value.id == receiver
        ):
            continue
        parent: AST | None = parents.get(id(node))
        if (
            parent is None
            or _inside_other_scope(
                node=node,
                parents=parents,
                function=function,
            )
            or not _read_only(
                name=node,
                parent=parent,
                parents=parents,
                counts=counts,
            )
        ):
            return True
    return False
