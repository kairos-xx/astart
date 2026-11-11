"""Derive a structural ``Protocol`` from how a parameter is used.

A parameter that is only ever accessed as ``name.attr`` or called as
``name.attr(...)`` is used structurally: any object with those members would
do. :func:`structural_usage` proves that, member by member, and refuses on any
other use. :func:`protocol_source` renders the matching ``Protocol`` class.

"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    Assert,
    Assign,
    AsyncFor,
    AsyncFunctionDef,
    AsyncWith,
    Attribute,
    Await,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    BoolOp,
    Call,
    Compare,
    Del,
    Div,
    Eq,
    Expr,
    FloorDiv,
    For,
    FormattedValue,
    FunctionDef,
    Gt,
    GtE,
    If,
    IfExp,
    In,
    Invert,
    Load,
    LShift,
    Lt,
    LtE,
    MatMult,
    Mod,
    Mult,
    Name,
    Not,
    NotEq,
    NotIn,
    Pow,
    Return,
    RShift,
    Starred,
    Store,
    Sub,
    Subscript,
    Tuple,
    UAdd,
    UnaryOp,
    USub,
    While,
    With,
    YieldFrom,
    arg,
    arguments,
    comprehension,
    iter_child_nodes,
    unparse,
    walk,
    withitem,
)
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart.docstrings.protocols import protocol_marker
from astart.rules.provable import expression_type
from astart.rules.scopes import names_bound_by

type StrOrNone = str | None
type ListTupleStrCall = list[tuple[str, _Call]]

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Mapping, Sequence

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        indent (Final[str]): Grouped module constant.
        private_prefix (Final[str]): Grouped module constant.
        receiver (Final[str]): Grouped module constant.
        docstring_marker (Final[str]): Grouped module constant.
        callable_member (Final[str]): Attribute name marking a callback
            protocol.
        exit_positional (Final[tuple[str | None, ...]]): ``__exit__``
            positional parameter types.
        builtin_calls (Final[Mapping[str, str]]): Builtin name to the dunder it
            dispatches to.
        iterable_calls (Final[frozenset[str]]): Calls whose argument must be
            iterable.
        str_calls (Final[frozenset[str]]): Calls whose argument must be a
            string.
        binop_left (Final[Mapping[type, str]]): Binary operator to the
            left-operand dunder.
        compare_left (Final[Mapping[type, str]]): Comparison operator to the
            left-operand dunder.
        compare_right (Final[Mapping[type, str]]): Comparison operator to the
            right-operand dunder.
        unary_ops (Final[Mapping[type, str]]): Unary operator to its dunder.
        fixed_returns (Final[Mapping[str, str]]): Dunder to the return type it
            always has.
        vacuous (Final[frozenset[str]]): Dunders every object already satisfies
            for the syntax that requires them.
        builtin_protocols: Final[
                tuple[tuple[frozenset[str], str, str], ...]
            ]: Grouped module constant.

    """

    indent: Final[str] = "    "
    private_prefix: Final[str] = "__"
    receiver: Final[str] = "self"
    callable_member: Final[str] = "__call__"
    docstring_marker: Final[str] = protocol_marker()
    exit_positional: Final[tuple[str | None, ...]] = (None, None, None)
    builtin_calls: Final[Mapping[str, str]] = {
        "abs": "__abs__",
        "aiter": "__aiter__",
        "anext": "__anext__",
        "bool": "__bool__",
        "complex": "__complex__",
        "float": "__float__",
        "format": "__format__",
        "hash": "__hash__",
        "index": "__index__",
        "int": "__int__",
        "iter": "__iter__",
        "len": "__len__",
        "next": "__next__",
        "repr": "__repr__",
        "reversed": "__reversed__",
        "str": "__str__",
    }
    iterable_calls: Final[frozenset[str]] = frozenset(
        {
            "all",
            "any",
            "frozenset",
            "list",
            "max",
            "min",
            "print",
            "set",
            "sorted",
            "sum",
            "tuple",
        },
    )
    str_calls: Final[frozenset[str]] = frozenset({"print"})
    binop_left: Final[Mapping[type, str]] = {
        Add: "__add__",
        Sub: "__sub__",
        Mult: "__mul__",
        MatMult: "__matmul__",
        Div: "__truediv__",
        FloorDiv: "__floordiv__",
        Mod: "__mod__",
        Pow: "__pow__",
        LShift: "__lshift__",
        RShift: "__rshift__",
        BitOr: "__or__",
        BitXor: "__xor__",
        BitAnd: "__and__",
    }
    compare_left: Final[Mapping[type, str]] = {
        Lt: "__lt__",
        LtE: "__le__",
        Gt: "__gt__",
        GtE: "__ge__",
        Eq: "__eq__",
        NotEq: "__ne__",
        In: "__eq__",
        NotIn: "__eq__",
    }
    compare_right: Final[Mapping[type, str]] = {
        Lt: "__gt__",
        LtE: "__ge__",
        Gt: "__lt__",
        GtE: "__le__",
        Eq: "__eq__",
        NotEq: "__ne__",
        In: "__contains__",
        NotIn: "__contains__",
    }
    unary_ops: Final[Mapping[type, str]] = {
        USub: "__neg__",
        UAdd: "__pos__",
        Invert: "__invert__",
    }
    fixed_returns: Final[Mapping[str, str]] = {
        "__bool__": "bool",
        "__contains__": "bool",
        "__delitem__": "None",
        "__eq__": "bool",
        "__exit__": "bool | None",
        "__aexit__": "bool | None",
        "__format__": "str",
        "__ge__": "bool",
        "__gt__": "bool",
        "__hash__": "int",
        "__index__": "int",
        "__int__": "int",
        "__float__": "float",
        "__complex__": "complex",
        "__le__": "bool",
        "__len__": "int",
        "__lt__": "bool",
        "__ne__": "bool",
        "__repr__": "str",
        "__setitem__": "None",
        "__str__": "str",
    }
    vacuous: Final[frozenset[str]] = frozenset(
        {
            "__bool__",
            "__eq__",
            "__format__",
            "__hash__",
            "__ne__",
            "__repr__",
            "__str__",
        },
    )

    builtin_protocols: Final[tuple[tuple[frozenset[str], str, str], ...]] = (
        (frozenset({"__len__"}), "collections.abc", "Sized"),
        (frozenset({"__iter__"}), "collections.abc", "Iterable"),
        (frozenset({"__aiter__"}), "collections.abc", "AsyncIterable"),
        (frozenset({"__iter__", "__next__"}), "collections.abc", "Iterator"),
        (
            frozenset({"__aiter__", "__anext__"}),
            "collections.abc",
            "AsyncIterator",
        ),
        (frozenset({"__contains__"}), "collections.abc", "Container"),
        (frozenset({"__hash__"}), "collections.abc", "Hashable"),
        (frozenset({"__await__"}), "collections.abc", "Awaitable"),
        (
            frozenset({"__reversed__", "__len__"}),
            "collections.abc",
            "Reversible",
        ),
        (
            frozenset({"__contains__", "__iter__", "__len__"}),
            "collections.abc",
            "Collection",
        ),
        (
            frozenset({"__enter__", "__exit__"}),
            "contextlib",
            "AbstractContextManager",
        ),
        (
            frozenset({"__aenter__", "__aexit__"}),
            "contextlib",
            "AbstractAsyncContextManager",
        ),
        (frozenset({"__fspath__"}), "os", "PathLike"),
    )


@final
@dataclass(frozen=True, slots=True)
class Member:
    """One member a parameter is required to have.

    Attributes:
        name (str): Attribute name.
        is_method (bool): ``True`` when it is called, ``False`` for a property.
        positional (tuple[StrOrNone, ...]): Annotation source per positional
            argument, or
            ``None`` where the argument type is not provable.
        keywords (tuple[tuple[str, StrOrNone], ...]): ``(name, annotation)``
            pairs, sorted by name.
        returns (StrOrNone): Return annotation proven from how every result
            is used, or ``None`` when it is not provable.
        is_async (bool): ``True`` when every call is awaited.
        writable (bool): ``True`` when the member is assigned to, ``del``-ed or
            augmented; ``returns`` then spells the stored type.

    """

    name: str
    is_method: bool
    positional: tuple[StrOrNone, ...]
    keywords: tuple[tuple[str, StrOrNone], ...]
    returns: StrOrNone = None
    is_async: bool = False
    writable: bool = False


@final
@dataclass(frozen=True, slots=True)
class StructuralUsage:
    """Everything a function requires of one parameter.

    Attributes:
        members (tuple[Member, ...]): Required members sorted by name.

    """

    members: tuple[Member, ...]


@dataclass(frozen=True)
class ProtocolEmit:
    """How a synthesized protocol class is emitted.

    Attributes:
        runtime_checkable (bool): Prepend ``@runtime_checkable`` so the
            protocol works with ``isinstance``.
        type_checking (bool): Wrap the class in ``if TYPE_CHECKING:`` for
            annotation-only use.

    """

    runtime_checkable: bool = False
    type_checking: bool = False


@final
@dataclass(frozen=True, slots=True)
class _Call:
    """One call of a member and how its result is used.

    Attributes:
        positional (tuple[StrOrNone, ...]): Annotation source per positional
            argument.
        keywords (tuple[tuple[str, StrOrNone], ...]): ``(name, annotation)``
            pairs, sorted by name.
        awaited (bool): ``True`` when the call is directly awaited.
        result (str): ``"returned"``, ``"unused"`` or ``"other"`` for how the
            (awaited) result flows.

    """

    positional: tuple[StrOrNone, ...]
    keywords: tuple[tuple[str, StrOrNone], ...]
    awaited: bool
    result: str


@final
@dataclass(slots=True)
class _Draft:
    """Accumulate the uses of one attribute.

    Attributes:
        calls (list[_Call]): Call shapes seen.
        reads (list[str]): Result uses of non-call attribute reads.
        writes (list[StrOrNone]): Stored value types of attribute writes
            (``None`` when a written type is not provable).

    """

    calls: list[_Call]
    reads: list[str]
    writes: list[StrOrNone]


def parameter_has_default(*, function: Function, parameter: arg) -> bool:
    """Tell whether a parameter has a default value.

    Args:
        function (Function): Function that owns the parameter.
        parameter (arg): Parameter to look up.

    Returns:
        bool: ``True`` when the parameter has a default.

    """
    arguments: arguments = function.args
    positional: list[arg] = [*arguments.posonlyargs, *arguments.args]
    if parameter in positional:
        offset: int = len(positional) - len(arguments.defaults)
        return positional.index(parameter) >= offset
    if parameter in arguments.kwonlyargs:
        index: int = arguments.kwonlyargs.index(parameter)
        return arguments.kw_defaults[index] is not None
    return False


def _walk(*, function: Function) -> Iterator[AST]:
    """Yield every node of a function body.

    Args:
        function (Function): Function whose body is walked.

    Yields:
        AST: Each node, statements first.

    """
    for statement in function.body:
        yield from walk(node=statement)


def _call_shape(
    *,
    call: Call,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> tuple[tuple[StrOrNone, ...], tuple[tuple[str, StrOrNone], ...]] | None:
    """Describe the arguments of a call to a member.

    Args:
        call (Call): Call expression.
        counts (Mapping[str, int]): Module binding counts, for typing
            arguments.
        env (Mapping[str, str] | None): Types of names visible at the call
            sites, for flow-typed arguments.

    Returns:
        tuple[tuple[StrOrNone, ...], tuple[tuple[str, StrOrNone], ...]] | None:
            Positional and keyword types, or ``None`` for star arguments.

    """
    if any(isinstance(item, Starred) for item in call.args):
        return None
    if any(item.arg is None for item in call.keywords):
        return None
    if any(item.arg == Constants.receiver for item in call.keywords):
        return None
    positional: tuple[StrOrNone, ...] = tuple(
        expression_type(node=item, counts=counts, env=env)
        for item in call.args
    )
    keywords: tuple[tuple[str, StrOrNone], ...] = tuple(
        sorted(
            (
                item.arg,
                expression_type(node=item.value, counts=counts, env=env),
            )
            for item in call.keywords
            if item.arg is not None
        ),
    )
    return (positional, keywords)


def _same(*, values: Sequence[str | None]) -> bool:
    """Tell whether every value equals the first.

    Args:
        values (Sequence[str | None]): Non-empty list of annotations.

    Returns:
        bool: ``True`` when all values agree.

    """
    return all(value == values[0] for value in values)


def _result_kind(*, node: AST, parents: Mapping[AST, AST]) -> str:
    """Classify how a member result flows.

    Args:
        node (AST): Call or attribute node whose result is classified.
        parents (Mapping[AST, AST]): Parent of every node.

    Returns:
        str: ``"returned"``, ``"unused"`` or ``"other"``.

    """
    parent: AST | None = parents.get(node)
    if isinstance(parent, Return):
        return "returned"
    if isinstance(parent, Expr):
        return "unused"
    return "other"


def _merge(
    *,
    name: str,
    draft: _Draft,
    function_returns: StrOrNone,
) -> Member | None:
    """Combine every call of one attribute into a member.

    Args:
        name (str): Attribute name.
        draft (_Draft): Calls, reads and writes seen for the attribute.
        function_returns (StrOrNone): Annotation source of the owning
            function's return, or ``None``.

    Returns:
        Member | None: The member, or ``None`` when the calls disagree
            on their shape or a written type is not provable.

    """
    if draft.writes and draft.calls:
        return None
    if not draft.calls:
        if draft.writes:
            return (
                None
                if not _same(values=draft.writes) or draft.writes[0] is None
                else Member(
                    name=name,
                    is_method=False,
                    positional=(),
                    keywords=(),
                    returns=draft.writes[0],
                    writable=True,
                )
            )
        returns: StrOrNone = (
            function_returns
            if draft.reads
            and _same(values=[*draft.reads])
            and draft.reads[0] == "returned"
            else None
        )
        return Member(
            name=name,
            is_method=False,
            positional=(),
            keywords=(),
            returns=returns,
        )
    awaited: set[bool] = {call.awaited for call in draft.calls}
    if len(awaited) > 1:
        return None
    first_positional, first_keywords = (
        draft.calls[0].positional,
        draft.calls[0].keywords,
    )
    shape: tuple[int, list[str]] = (
        len(first_positional),
        [key for key, _ in first_keywords],
    )
    for call in draft.calls:
        if (len(call.positional), [key for key, _ in call.keywords]) != shape:
            return None
    merged_positional: tuple[StrOrNone, ...] = tuple(
        first_positional[index]
        if _same(values=[call.positional[index] for call in draft.calls])
        else None
        for index in range(len(first_positional))
    )
    merged_keywords: tuple[tuple[str, StrOrNone], ...] = tuple(
        (
            (
                key,
                first_keywords[index][1]
                if _same(
                    values=[call.keywords[index][1] for call in draft.calls],
                )
                else None,
            )
            for index, (key, _) in enumerate(iterable=first_keywords)
        ),
    )
    returns = (
        function_returns
        if function_returns is not None
        and all(call.result == "returned" for call in draft.calls)
        else None
    )
    return Member(
        name=name,
        is_method=True,
        positional=merged_positional,
        keywords=merged_keywords,
        returns=returns,
        is_async=awaited.pop(),
    )


def _record_call(
    *,
    draft: _Draft,
    call: Call,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> bool:
    """Record one member call on a draft.

    Args:
        draft (_Draft): Draft to append to.
        call (Call): Call expression.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        bool: ``False`` when the call shape is not provable.

    """
    shape: (
        tuple[tuple[StrOrNone, ...], tuple[tuple[str, StrOrNone], ...]] | None
    ) = _call_shape(call=call, counts=counts, env=env)
    if shape is None:
        return False
    awaited_by: AST | None = parents.get(call)
    if isinstance(awaited_by, Await):
        draft.calls.append(
            _Call(
                positional=shape[0],
                keywords=shape[1],
                awaited=True,
                result=_result_kind(node=awaited_by, parents=parents),
            ),
        )
    else:
        draft.calls.append(
            _Call(
                positional=shape[0],
                keywords=shape[1],
                awaited=False,
                result=_result_kind(node=call, parents=parents),
            ),
        )
    return True


def _builtin_member_call(
    *,
    call: Call,
    node: Name,
    counts: Mapping[str, int],
) -> StrOrNone:
    """Name the member a builtin call on the parameter implies.

    Args:
        call (Call): Call expression.
        node (Name): Parameter name node inside the call.
        counts (Mapping[str, int]): Module binding counts, to reject shadowed
            builtins.

    Returns:
        StrOrNone: The dunder name, or ``None`` when the call
            does not constrain the parameter structurally.

    """
    if not (
        isinstance(call.func, Name)
        and counts.get(call.func.id, 0) == 0
        and not call.keywords
        and not any(isinstance(item, Starred) for item in call.args)
    ):
        return None
    builtin: str = call.func.id
    if call.args and call.args[0] is node:
        if builtin in Constants.builtin_calls:
            return Constants.builtin_calls[builtin]
        if builtin in Constants.iterable_calls:
            return "__str__" if builtin in Constants.str_calls else "__iter__"
        return None
    if builtin in ("filter", "map", "zip") and any(
        item is node for item in call.args[1:]
    ):
        return "__iter__"
    return None


def _dunder_member(
    *,
    table: Mapping[type, str],
    operation: AST,
) -> StrOrNone:
    """Resolve an operator node's dunder through wrapper subclasses.

    Token-bound ASTs reclass operator nodes as ``TokenAwareMixin``
    subclasses, so an exact ``type`` key misses; walking the MRO
    reaches the concrete ``ast`` operator class either way.

    Args:
        table (Mapping[type, str]): Operator-class to dunder-name mapping.
        operation (AST): Operator node instance.

    Returns:
        StrOrNone: The dunder name, or ``None`` when unmapped.

    """
    for klass in type(operation).__mro__:
        member: StrOrNone = table.get(klass)
        if member is not None:
            return member
    return None


def compare_members(
    *,
    compare: Compare,
    node: Name,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> list[tuple[str, tuple[StrOrNone, ...]]] | None:
    """Name the orderable members a compare operand implies.

    Args:
        compare (Compare): Comparison expression.
        node (Name): Parameter name node inside it.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        list[tuple[str, tuple[StrOrNone, ...]]] | None:
            ``(member, positional)`` pairs per applied
            operator, or ``None`` for identity tests.

    """
    found: list[tuple[str, tuple[StrOrNone, ...]]] = []
    operands: list[AST] = [compare.left, *compare.comparators]
    for index, operation in enumerate(iterable=compare.ops):
        left: AST = operands[index]
        right: AST = operands[index + 1]
        if node is left:
            member: StrOrNone = _dunder_member(
                table=Constants.compare_left,
                operation=operation,
            )
            other: AST = right
        elif node is right:
            member = _dunder_member(
                table=Constants.compare_right,
                operation=operation,
            )
            other = left
        else:
            continue
        if member is None:
            return None
        annotation: StrOrNone = (
            None
            if isinstance(other, Name)
            else expression_type(node=other, counts=counts, env=env)
        )
        found.append((member, (annotation,)))
    return found


def _compare_members(
    *,
    compare: Compare,
    node: Name,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> ListTupleStrCall | None:
    """Spell the comparison members a compare operand implies.

    Args:
        compare (Compare): Comparison expression.
        node (Name): Parameter name node inside it.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        ListTupleStrCall | None:
            ``(member, call)`` pairs, or ``None`` for identity tests.

    """
    result: str = _result_kind(node=compare, parents=parents)
    pairs: list[tuple[str, tuple[StrOrNone, ...]]] | None = compare_members(
        compare=compare,
        node=node,
        counts=counts,
        env=env,
    )
    if pairs is None:
        return None
    return [
        (
            member,
            _Call(
                positional=positional,
                keywords=(),
                awaited=False,
                result=result,
            ),
        )
        for member, positional in pairs
    ]


def _subscript_members(
    *,
    subscript: Subscript,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> ListTupleStrCall | None:
    """Spell the item members a subscript on the parameter implies.

    Args:
        subscript (Subscript): Subscript expression.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        ListTupleStrCall | None:
            ``(member, call)`` pairs, or ``None`` for an unprovable slice.

    """
    key: StrOrNone = expression_type(
        node=subscript.slice,
        counts=counts,
        env=env,
    )
    if isinstance(subscript.ctx, Load):
        return [
            (
                "__getitem__",
                _Call(
                    positional=(key,),
                    keywords=(),
                    awaited=False,
                    result=_result_kind(node=subscript, parents=parents),
                ),
            ),
        ]
    if isinstance(subscript.ctx, Del):
        return [
            (
                "__delitem__",
                _Call(
                    positional=(key,),
                    keywords=(),
                    awaited=False,
                    result="unused",
                ),
            ),
        ]
    holder: AST | None = parents.get(subscript)
    value: StrOrNone = (
        expression_type(node=holder.value, counts=counts, env=env)
        if isinstance(holder, Assign)
        and any(target is subscript for target in holder.targets)
        else None
    )
    return [
        (
            "__setitem__",
            _Call(
                positional=(key, value),
                keywords=(),
                awaited=False,
                result="unused",
            ),
        ),
    ]


def _use_call(
    *,
    result: str,
    positional: tuple[StrOrNone, ...] = (),
    used: StrOrNone = None,
) -> _Call:
    """Build a ``_Call`` record for one dunder use.

    Args:
        result (str): How the enclosing expression consumes the call result.
        positional (tuple[StrOrNone, ...]): Types of the positional arguments.
        used (StrOrNone): Explicit consumption override.

    Returns:
        _Call: The call record.

    """
    return _Call(
        positional=positional,
        keywords=(),
        awaited=False,
        result=result if used is None else used,
    )


def _dunder_use(
    *,
    node: Name,
    parent: AST | None,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> ListTupleStrCall | None:
    """Map one syntax-level use of a parameter to its dunder members.

    Args:
        node (Name): Parameter name node.
        parent (AST | None): Its direct parent node.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs to record, or
            ``None`` when the use is not structural.

    """
    if parent is None:
        return None
    if isinstance(
        parent,
        (Subscript, Call, withitem, For, AsyncFor, comprehension),
    ):
        return _dunder_value(
            node=node,
            parent=parent,
            parents=parents,
            counts=counts,
            env=env,
        )
    if isinstance(parent, (UnaryOp, BoolOp, BinOp, Compare)):
        return _dunder_operator(
            node=node,
            parent=parent,
            parents=parents,
            counts=counts,
            env=env,
        )
    if isinstance(parent, (Await, YieldFrom, Starred, FormattedValue)):
        return _dunder_wrap(node=node, parent=parent, parents=parents)
    return _dunder_context(node=node, parent=parent, parents=parents)


def _dunder_value(
    *,
    node: Name,
    parent: AST,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> ListTupleStrCall | None:
    """Map a value-position use to its dunder members.

    Args:
        node (Name): Parameter name node.
        parent (AST): Its direct parent node.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs, or ``None``.

    """
    result: str = _result_kind(node=parent, parents=parents)
    if isinstance(parent, Subscript) and parent.value is node:
        return _subscript_members(
            subscript=parent,
            parents=parents,
            counts=counts,
            env=env,
        )
    if isinstance(parent, Call):
        member: StrOrNone = _builtin_member_call(
            call=parent,
            node=node,
            counts=counts,
        )
        return (
            [(member, _use_call(result=result))]
            if member is not None
            else None
        )
    if isinstance(parent, withitem):
        return _dunder_withitem(
            node=node,
            parent=parent,
            parents=parents,
            result=result,
        )
    if isinstance(parent, (For, AsyncFor)) and parent.iter is node:
        member = "__aiter__" if isinstance(parent, AsyncFor) else "__iter__"
        return [(member, _use_call(result=result, used="unused"))]
    if isinstance(parent, comprehension) and parent.iter is node:
        member = "__aiter__" if parent.is_async else "__iter__"
        return [(member, _use_call(result=result, used="unused"))]
    return None


def _dunder_withitem(
    *,
    node: Name,
    parent: withitem,
    parents: Mapping[AST, AST],
    result: str,
) -> ListTupleStrCall | None:
    """Map a ``with`` item use to its enter/exit members.

    Args:
        node (Name): Parameter name node.
        parent (withitem): The ``withitem`` node.
        parents (Mapping[AST, AST]): Parent of every node.
        result (str): How the enclosing expression consumes the result.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs, or ``None``.

    """
    if parent.context_expr is not node:
        return None
    owner: AST | None = parents.get(parent)
    if isinstance(owner, AsyncWith):
        return [
            ("__aenter__", _use_call(result=result, used="other")),
            (
                "__aexit__",
                _use_call(
                    result=result,
                    positional=Constants.exit_positional,
                    used="unused",
                ),
            ),
        ]
    if isinstance(owner, With):
        return [
            ("__enter__", _use_call(result=result, used="other")),
            (
                "__exit__",
                _use_call(
                    result=result,
                    positional=Constants.exit_positional,
                    used="unused",
                ),
            ),
        ]
    return None


def _dunder_operator(
    *,
    node: Name,
    parent: AST,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> ListTupleStrCall | None:
    """Map an operator operand use to its dunder members.

    Args:
        node (Name): Parameter name node.
        parent (AST): Its direct parent node.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs, or ``None``.

    """
    result: str = _result_kind(node=parent, parents=parents)
    if isinstance(parent, UnaryOp):
        if isinstance(parent.op, Not):
            return [("__bool__", _use_call(result=result, used="unused"))]
        member: StrOrNone = _dunder_member(
            table=Constants.unary_ops,
            operation=parent.op,
        )
        return (
            [(member, _use_call(result=result))]
            if member is not None
            else None
        )
    if isinstance(parent, BoolOp) and any(
        item is node for item in parent.values
    ):
        return [("__bool__", _use_call(result=result, used="other"))]
    if isinstance(parent, BinOp) and (
        parent.left is node or parent.right is node
    ):
        return _binop_members(
            node=node,
            parent=parent,
            counts=counts,
            env=env,
            result=result,
        )
    if isinstance(parent, Compare):
        return _compare_members(
            compare=parent,
            node=node,
            parents=parents,
            counts=counts,
            env=env,
        )
    return None


def _binop_members(
    *,
    node: Name,
    parent: BinOp,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
    result: str,
) -> ListTupleStrCall | None:
    """Map a binary-operator operand use to its dunder member.

    Args:
        node (Name): Parameter name node.
        parent (BinOp): The ``BinOp`` node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.
        result (str): How the enclosing expression consumes the result.

    Returns:
        ListTupleStrCall | None: The ``(member, call)`` pair, or ``None``.

    """
    member: StrOrNone = _dunder_member(
        table=Constants.binop_left,
        operation=parent.op,
    )
    if member is None:
        return None
    if parent.right is node:
        member = f"__r{member[2:]}"
    other: AST = parent.left if parent.right is node else parent.right
    positional: StrOrNone = (
        None
        if isinstance(other, Name)
        else expression_type(node=other, counts=counts, env=env)
    )
    return [
        (member, _use_call(result=result, positional=(positional,))),
    ]


def _dunder_context(
    *,
    node: Name,
    parent: AST,
    parents: Mapping[AST, AST],
) -> ListTupleStrCall | None:
    """Map a control-flow use to its dunder members.

    Args:
        node (Name): Parameter name node.
        parent (AST): Its direct parent node.
        parents (Mapping[AST, AST]): Parent of every node.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs, or ``None``.

    """
    result: str = _result_kind(node=parent, parents=parents)
    if isinstance(parent, (If, While, Assert)) and parent.test is node:
        return [("__bool__", _use_call(result=result, used="unused"))]
    if isinstance(parent, IfExp) and parent.test is node:
        return [("__bool__", _use_call(result=result, used="other"))]
    return None


def _dunder_wrap(
    *,
    node: Name,
    parent: AST,
    parents: Mapping[AST, AST],
) -> ListTupleStrCall | None:
    """Map an await/yield/star/format use to its dunder member.

    Args:
        node (Name): Parameter name node.
        parent (AST): Its direct parent node.
        parents (Mapping[AST, AST]): Parent of every node.

    Returns:
        ListTupleStrCall | None: ``(member, call)`` pairs, or ``None``.

    """
    result: str = _result_kind(node=parent, parents=parents)
    if isinstance(parent, Await) and parent.value is node:
        return [("__await__", _use_call(result=result))]
    if isinstance(parent, YieldFrom) and parent.value is node:
        return [("__iter__", _use_call(result=result, used="unused"))]
    if isinstance(parent, Starred) and parent.value is node:
        return [("__iter__", _use_call(result=result))]
    if isinstance(parent, FormattedValue) and parent.value is node:
        return [("__format__", _use_call(result=result))]
    return None


def _record_attribute(
    *,
    drafts: dict[str, _Draft],
    attribute: Attribute,
    parents: Mapping[AST, AST],
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> bool:
    """Record one attribute use into its member draft.

    Args:
        drafts (dict[str, _Draft]): Drafts gathered so far.
        attribute (Attribute): The attribute node used on the parameter.
        parents (Mapping[AST, AST]): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            site.

    Returns:
        bool: ``False`` when the use refuses the whole collection.

    """
    draft: _Draft = drafts.setdefault(
        attribute.attr,
        _Draft(calls=[], reads=[], writes=[]),
    )
    if isinstance(attribute.ctx, (Store, Del)):
        holder: AST | None = parents.get(attribute)
        stored: StrOrNone = (
            expression_type(node=holder.value, counts=counts, env=env)
            if isinstance(holder, Assign)
            and any(target is attribute for target in holder.targets)
            else None
        )
        draft.writes.append(stored)
        return True
    attribute_parent: AST | None = parents.get(attribute)
    if isinstance(attribute_parent, Await):
        return False
    if isinstance(attribute_parent, Call) and (
        attribute_parent.func is attribute
    ):
        return _record_call(
            draft=draft,
            call=attribute_parent,
            parents=parents,
            counts=counts,
            env=env,
        )
    draft.reads.append(
        _result_kind(node=attribute, parents=parents),
    )
    return True


def _collect(
    *,
    nodes: list[AST],
    parents: Mapping[AST, AST],
    parameter: str,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> dict[str, _Draft] | None:
    """Gather the attribute uses of a parameter.

    Args:
        nodes (list[AST]): Every node of the function body.
        parents (Mapping[AST, AST]): Parent of every node.
        parameter (str): Parameter name.
        counts (Mapping[str, int]): Module binding counts.
        env (Mapping[str, str] | None): Types of names visible at the call
            sites.

    Returns:
        dict[str, _Draft] | None:
            Uses per attribute, or ``None`` when any use is not structural.

    """
    drafts: dict[str, _Draft] = {}
    for node in nodes:
        if not (isinstance(node, Name) and node.id == parameter):
            continue
        parent: AST | None = parents.get(node)
        if isinstance(parent, Call) and parent.func is node:
            draft: _Draft = drafts.setdefault(
                Constants.callable_member,
                _Draft(calls=[], reads=[], writes=[]),
            )
            if not _record_call(
                draft=draft,
                call=parent,
                parents=parents,
                counts=counts,
                env=env,
            ):
                return None
            continue
        if not (
            isinstance(parent, Attribute)
            and parent.value is node
            and (not parent.attr.startswith(Constants.private_prefix))
        ):
            dunders: ListTupleStrCall | None = _dunder_use(
                node=node,
                parent=parent,
                parents=parents,
                counts=counts,
                env=env,
            )
            if dunders is None:
                return None
            for member, use in dunders:
                drafts.setdefault(
                    member,
                    _Draft(calls=[], reads=[], writes=[]),
                ).calls.append(use)
            continue
        attribute: Attribute = parent
        if not _record_attribute(
            drafts=drafts,
            attribute=attribute,
            parents=parents,
            counts=counts,
            env=env,
        ):
            return None
    return drafts


def structural_usage(
    *,
    function: Function,
    parameter: str,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None = None,
) -> StructuralUsage | None:
    """Prove that a parameter is only used through its attributes.

    Args:
        function (Function): Function that owns the parameter.
        parameter (str): Parameter name.
        counts (Mapping[str, int]): Module binding counts, for typing call
            arguments.
        env (Mapping[str, str] | None): Types of names visible at the call
            sites, for flow-typed arguments.

    Returns:
        StructuralUsage | None:
            The required members, or ``None`` when the parameter is rebound,
            used as a plain value, written to, awaited through, or unused.

    """
    nodes: list[AST] = list(_walk(function=function))
    if any(parameter in names_bound_by(node=node) for node in nodes):
        return None
    parents: dict[AST, AST] = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    drafts: dict[str, _Draft] | None = _collect(
        nodes=nodes,
        parents=parents,
        parameter=parameter,
        counts=counts,
        env=env,
    )
    if drafts is None:
        return None
    function_returns: StrOrNone = (
        unparse(ast_obj=function.returns)
        if function.returns is not None
        else None
    )
    members: list[Member] = []
    for name in sorted(drafts):
        member: Member | None = _merge(
            name=name,
            draft=drafts[name],
            function_returns=function_returns,
        )
        if member is None:
            return None
        fixed: StrOrNone = Constants.fixed_returns.get(member.name)
        if fixed is not None:
            member = replace(member, returns=fixed)
        members.append(member)
    return StructuralUsage(members=tuple(members)) if members else None


def _annotated(*, name: str, annotation: StrOrNone) -> str:
    """Spell a parameter with its optional annotation.

    Args:
        name (str): Parameter name.
        annotation (StrOrNone): Annotation source, or ``None``.

    Returns:
        str: ``name`` or ``name: annotation``.

    """
    return name if annotation is None else f"{name}: {annotation}"


def _member_source(*, member: Member) -> str:
    """Render one member as protocol source.

    Args:
        member (Member): Member to render.

    Returns:
        str: Indented source lines.

    """
    pad: str = Constants.indent
    returns: str = (
        f" -> {member.returns}" if member.returns is not None else ""
    )
    if not member.is_method:
        if member.writable:
            return f"{pad}{member.name}: {member.returns}\n"
        return f"""\
{pad}@property
{pad}def {member.name}(self){returns}: ...
"""
    taken: set[str] = {
        Constants.receiver,
        *(key for key, _ in member.keywords),
    }
    positional_names: list[str] = []
    for index in range(len(member.positional)):
        candidate: str = f"arg{index}"
        bump: int = 0
        while candidate in taken:
            bump += 1
            candidate = f"arg{index}_{bump}"
        taken.add(candidate)
        positional_names.append(candidate)
    parameters: list[str] = ["self"]
    parameters.extend(
        (
            _annotated(name=name, annotation=annotation)
            for name, annotation in zip(
                positional_names,
                member.positional,
                strict=True,
            )
        ),
    )
    if member.positional:
        parameters.append("/")
    if member.keywords:
        parameters.append("*")
        parameters.extend(
            (
                _annotated(name=key, annotation=annotation)
                for key, annotation in member.keywords
            ),
        )
    prefix: str = "async " if member.is_async else ""
    return f"""\
{pad}{prefix}def {member.name}({", ".join(parameters)}){returns}: ...
"""


def protocol_source(
    *,
    name: str,
    function: str,
    parameter: str,
    usage: StructuralUsage,
    emit: ProtocolEmit | None = None,
) -> str:
    """Render the ``Protocol`` class for a structural usage.

    Args:
        name (str): Class name.
        function (str): Name of the function the usage was derived from.
        parameter (str): Name of the parameter.
        usage (StructuralUsage): Required members.
        emit (ProtocolEmit | None): How the class is emitted; defaults to a
            plain class.

    Returns:
        str: Python source for the class, ending with a newline.

    """
    style: ProtocolEmit = ProtocolEmit() if emit is None else emit
    decorator: str = (
        """\
@runtime_checkable
"""
        if style.runtime_checkable
        else ""
    )
    header: str = f"""\
{decorator}class {name}(Protocol):
{Constants.indent}\"""{Constants.docstring_marker}{parameter}`` in \
``{function}``.\"""
"""
    body: str = "\n".join(
        _member_source(member=member) for member in usage.members
    )
    source: str = f"""\
{header}
{body}"""
    if style.type_checking:
        indented: str = "\n".join(
            f"{Constants.indent}{line}" if line else line
            for line in source.split(
                sep="\n",
            )
        )
        return f"if TYPE_CHECKING:\n{indented}\n"
    return source


def _call_member(
    member: Member,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    """Spell a ``__call__`` member as a ``Callable`` annotation.

    Args:
        member (Member): The ``__call__`` member to spell.

    Returns:
        tuple[str, tuple[tuple[str, str], ...]] | None:
            ``(annotation, imports)`` or ``None`` when keyword
            arguments or an unknown result prevent the spelling.

    """
    if member.keywords or member.returns is None or member.is_async:
        return None
    if any(positional is None for positional in member.positional):
        return None
    arguments: str = ", ".join(
        positional or "object" for positional in member.positional
    )
    return (
        f"Callable[[{arguments}], {member.returns}]",
        (("collections.abc", "Callable"),),
    )


def callable_annotation(
    *,
    usage: StructuralUsage,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    """Spell a parameter's annotation when it is only ever called.

    A parameter used solely as ``parameter(...)`` needs no protocol class: a
    ``Callable`` annotation describes the same contract. The annotation is
    spelled only when every positional type and the result type are proven;
    keyword calls refuse (a ``Callable`` cannot name them).

    Args:
        usage (StructuralUsage): Structural usage of the parameter.

    Returns:
        tuple[str, tuple[tuple[str, str], ...]] | None:
            ``(annotation, imports)`` or ``None`` when the parameter is
            not a plain callee or the call shape is not fully provable.

    """
    if len(usage.members) != 1:
        return None
    member: Member = usage.members[0]
    if not (member.is_method and member.name == Constants.callable_member):
        return None
    return _call_member(member=member)


def vacuous_usage(*, usage: StructuralUsage) -> bool:
    """Tell whether a usage constrains nothing beyond ``object``.

    Truthiness, formatting, ``str``/``repr``/``hash`` and equality are
    satisfied by every object, so a contract made only of those members
    rejects nothing — the parameter is better left unannotated.

    Args:
        usage (StructuralUsage): Structural usage of the parameter.

    Returns:
        bool: ``True`` when the member set adds
            no requirement beyond ``object``.

    """
    return (
        frozenset(member.name for member in usage.members) <= Constants.vacuous
    )


def builtin_protocol(
    *,
    usage: StructuralUsage,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    """Reuse an existing standard protocol for a member set, when exact.

    Synthesising a new ``Protocol`` is a last resort: when the required
    members spell exactly the contract of a ``collections.abc``,
    ``contextlib`` or ``os`` protocol, the existing name is both shorter and
    already known to readers and checkers. Only an exact member-set match
    qualifies — a superset annotation would reject valid arguments.

    Args:
        usage (StructuralUsage): Structural usage of the parameter.

    Returns:
        tuple[str, tuple[tuple[str, str], ...]] | None:
            ``(annotation, imports)`` for the reuse, or ``None``
            when no standard protocol's member set matches exactly.

    """
    required: frozenset[str] = frozenset(
        member.name for member in usage.members
    )
    if (
        len(usage.members) == 1
        and usage.members[0].name == Constants.callable_member
    ):
        spelled: tuple[str, tuple[tuple[str, str], ...]] | None = _call_member(
            member=usage.members[0],
        )
        if spelled is not None:
            return spelled
    if required == frozenset({Constants.callable_member}):
        return (
            "Callable[..., object]",
            (("collections.abc", "Callable"),),
        )
    for members, module, name in Constants.builtin_protocols:
        if members == required:
            return name, ((module, name),)
    return None


def _getitem_kind(*, member: Member) -> StrOrNone:
    """Classify a ``__getitem__`` parameter's key type.

    Args:
        member (Member): The ``__getitem__`` member.

    Returns:
        StrOrNone: ``"int"``, ``"str"`` or ``None``.

    """
    positional: tuple[StrOrNone, ...] = member.positional
    if positional and positional[0] == "int":
        return "int"
    if positional and positional[0] == "str":
        return "str"
    return None


def _subscript_annotation(
    *,
    names: frozenset[str],
    members: dict[str, Member],
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    """Spell the abstract type for a ``__getitem__`` member set.

    Args:
        names (frozenset[str]): Required member names.
        members (dict[str, Member]): Members by name.

    Returns:
        tuple[str, tuple[tuple[str, str], ...]] | None:
            ``(annotation, imports)`` or ``None``.

    """
    if "__getitem__" not in members:
        return None
    kind: StrOrNone = _getitem_kind(member=members["__getitem__"])
    if names == frozenset({"__getitem__", "__len__", "__setitem__"}):
        table: dict[str, tuple[str, str]] = {
            "int": ("MutableSequence[Any]", "MutableSequence"),
            "str": ("MutableMapping[str, Any]", "MutableMapping"),
        }
    elif names == frozenset({"__getitem__", "__len__"}):
        table = {
            "int": ("Sequence[Any]", "Sequence"),
            "str": ("Mapping[str, Any]", "Mapping"),
        }
    elif names == frozenset({"__getitem__"}):
        table = {"str": ("Mapping[str, Any]", "Mapping")}
    else:
        return None
    if kind is None or kind not in table:
        return None
    annotation, imported = table[kind]
    return annotation, (
        ("collections.abc", imported),
        ("typing", "Any"),
    )


def abstract_parameter(
    *,
    usage: StructuralUsage,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    """Choose an abstract parameter type when usage proves one.

    Parameters only read through the iteration, size and indexing protocols
    accept the matching abstract type: iteration spells ``Iterable``, integer
    indexing and ``len`` spell ``Sequence``, string key lookup spells
    ``Mapping`` and item assignment spells the mutable counterparts. Anything
    beyond pure read usage, or an ambiguous member set, stays concrete.

    Args:
        usage (StructuralUsage): Structural usage of the parameter.

    Returns:
        tuple[str, tuple[tuple[str, str], ...]] | None:
            ``(annotation, imports)`` or ``None`` when the usage is not a
            read-only container shape or the container kind is ambiguous.

    """
    members: dict[str, Member] = {
        member.name: member for member in usage.members
    }
    if any(member.writable for member in members.values()):
        return None
    names: frozenset[str] = frozenset(members)
    if names in (
        frozenset({"__iter__"}),
        frozenset({"__len__", "__iter__"}),
    ):
        return (
            "Iterable[Any]",
            (
                ("collections.abc", "Iterable"),
                ("typing", "Any"),
            ),
        )
    return _subscript_annotation(names=names, members=members)


def protocol_isinstanced(*, module: AST, names: Collection[str]) -> bool:
    """Tell whether a protocol name appears under ``isinstance``.

    Args:
        module (AST): Parsed module to search.
        names (Collection[str]): Protocol class names this run creates.

    Returns:
        bool: ``True`` when any ``isinstance(<expr>, <name>)``
            call references one of the names.

    """
    node_args: int = 2
    for node in walk(node=module):
        if (
            not (isinstance(node, Call) and isinstance(node.func, Name))
            or node.func.id != "isinstance"
            or len(node.args) != node_args
        ):
            continue
        target: AST = node.args[1]
        if (isinstance(target, Name) and target.id in names) or (
            isinstance(target, Tuple)
            and any(
                isinstance(item, Name) and item.id in names
                for item in target.elts
            )
        ):
            return True
    return False
