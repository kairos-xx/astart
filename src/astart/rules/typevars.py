"""Detect parameters that only flow through to the return value.

A parameter whose every use is as (an element of) a returned value is generic:
its type is whatever the caller passes. :func:`passthrough_return` proves
that and spells the return annotation in terms of a type variable.

"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Await,
    BinOp,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    FunctionDef,
    If,
    IfExp,
    Lambda,
    List,
    Load,
    Module,
    Name,
    Return,
    Set,
    Starred,
    Subscript,
    Tuple,
    Yield,
    YieldFrom,
    arg,
    arguments,
    expr,
    iter_child_nodes,
    keyword,
    parse,
    walk,
)
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, final

from astart.rules.protocols import (
    Member,
    StructuralUsage,
    compare_members,
    parameter_has_default,
)
from astart.rules.provable import (
    can_fall_off,
    provable_return,
)
from astart.rules.scopes import names_bound_by

type ListAST = list[AST]
type ListStr = list[str]
type SetStr = set[str]
type DictASTAST = dict[AST, AST]

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    type Function = FunctionDef | AsyncFunctionDef


@final
@dataclass(frozen=True, slots=True)
class TypeVarPlan:
    """How a parameter and the return value should be annotated.

    Attributes:
        annotate (bool): ``True`` when the parameter receives an annotation.
        param (str | None): Parameter annotation source, or ``None``.
        returns (str): Return annotation source.
        variable (bool): ``True`` when a ``TypeVar`` declaration is required.
        constraints (tuple[str, ...]): Constraint class names for a constrained
            TypeVar.
        bound (StructuralUsage | None): Required members for a bound TypeVar's
            protocol, or ``None``.
        imports (tuple[tuple[str, str], ...]): ``(source, name)`` pairs the
            annotations rely on.

    """

    annotate: bool
    param: str | None
    returns: str
    variable: bool
    constraints: tuple[str, ...] = ()
    bound: StructuralUsage | None = None
    imports: tuple[tuple[str, str], ...] = ()


def _is_pure(*, node: AST, parents: Mapping[AST, AST]) -> bool:
    """Tell whether a use only carries the value into a return.

    Args:
        node (AST): The ``Name`` node of the parameter.
        parents (Mapping[AST, AST]): Parent of every node.

    Returns:
        bool: ``True`` when the chain up to the ``return``
            is only containers and conditional branches.

    """
    child: AST = node
    parent: AST | None = parents.get(child)
    while parent is not None and not isinstance(parent, Return):
        match parent:
            case List() | Tuple() | Set():
                pass
            case Dict(values=values) if any(child is v for v in values):
                pass
            case IfExp(body=body, orelse=orelse) if (
                child is body or child is orelse
            ):
                pass
            case BoolOp():
                pass
            case Compare():
                pass
            case _:
                return False
        child, parent = parent, parents.get(parent)
    return parent is not None


def _mentions_opaque(*, result: str) -> bool:
    r"""Tell whether a proven return names ``Unknown`` or ``Any``.

    Replaces ``\\b(?:Unknown|Any)\\b``: a name counts only when both
    neighbours are non-word characters, so ``AnyStr`` and ``foo.Unknowns``
    stay clean while ``Literal["Any"]`` still disqualifies the result.

    Args:
        result (str): Proven return expression text.

    Returns:
        bool: ``True`` when ``Unknown`` or ``Any`` appears as a whole word.

    """
    return any(
        _whole_word(text=result, word=word) for word in ("Unknown", "Any")
    )


def _whole_word(*, text: str, word: str) -> bool:
    """Tell whether ``word`` occurs in ``text`` with word boundaries.

    Args:
        text (str): Haystack string.
        word (str): Needle that must not touch word characters.

    Returns:
        bool: ``True`` when an occurrence has non-word (or string-edge)
            neighbours on both sides.

    """
    start: int = 0
    while (index := text.find(word, start)) != -1:
        before: str = text[index - 1] if index > 0 else ""
        end: int = index + len(word)
        after: str = text[end] if end < len(text) else ""
        if not _is_word_char(char=before) and not _is_word_char(char=after):
            return True
        start = index + 1
    return False


def _is_word_char(*, char: str) -> bool:
    r"""Tell whether ``char`` counts as a ``\\w`` word character.

    Args:
        char (str): Single character or the empty string at a text edge.

    Returns:
        bool: ``True`` for alphanumerics and ``_`` — the ``\\w`` class.

    """
    return char == "_" or char.isalnum()


def passthrough_return(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> str | None:
    """Prove a parameter is generic and spell the matching return type.

    Args:
        function (Function): Function that owns the parameter.
        parameter (str): Parameter name.
        variable (str): Name of the type variable standing for the parameter.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        str | None:
            The return annotation source, or ``None`` when the parameter
            is rebound, used for anything but being returned, or
            the function is already annotated or is a generator.

    """
    if function.returns is not None:
        return None
    nodes: ListAST = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(parameter in names_bound_by(node=node) for node in nodes):
        return None
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    parents: DictASTAST = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    uses: ListAST = [
        node
        for node in nodes
        if isinstance(node, Name) and node.id == parameter
    ]
    if not uses or not all(
        _is_pure(node=use, parents=parents) for use in uses
    ):
        return None
    result: str | None = provable_return(
        function=function,
        known_types={parameter: variable},
        counts=counts,
    )
    if result is None or _mentions_opaque(result=result):
        return None
    mentioned: bool = any(
        isinstance(node, Name) and node.id == variable
        for node in walk(node=parse(source=result, mode="eval"))
    )
    return result if mentioned else None


def _scope(
    *,
    function: Function,
) -> tuple[ListAST, DictASTAST] | None:
    """Collect a function's own nodes and parents when it is a candidate.

    Args:
        function (Function): Function to inspect.

    Returns:
        tuple[ListAST, DictASTAST] | None:
            ``(nodes, parents)`` or ``None`` when the
            function is already annotated or is a generator.

    """
    if function.returns is not None:
        return None
    return _scope_nodes(function=function)


def _scope_nodes(
    *,
    function: Function,
) -> tuple[ListAST, DictASTAST] | None:
    """Collect a function's own nodes and parents, annotated or not.

    Args:
        function (Function): Function to inspect.

    Returns:
        tuple[ListAST, DictASTAST] | None:
            ``(nodes, parents)``, or ``None`` when the function is a
        generator. Unlike: func:`_scope` this tolerates an existing
            return annotation so a shared ``TypeVar`` written by a sibling
            parameter's fix can still be detected.

    """
    nodes: ListAST = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    parents: DictASTAST = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    return nodes, parents


def _uses(*, nodes: ListAST, parameter: str) -> list[Name]:
    """Collect the load-time uses of a parameter name.

    Args:
        nodes (ListAST): Function body nodes.
        parameter (str): Parameter name.

    Returns:
        list[Name]: ``Name`` nodes that read the parameter.

    """
    return [
        node
        for node in nodes
        if isinstance(node, Name)
        and node.id == parameter
        and isinstance(node.ctx, Load)
    ]


def _rebound(*, nodes: ListAST, parameter: str) -> bool:
    """Tell whether a parameter name is bound anywhere in the function.

    Args:
        nodes (ListAST): Function body nodes.
        parameter (str): Parameter name.

    Returns:
        bool: ``True`` when the name is rebound.

    """
    return any(parameter in names_bound_by(node=node) for node in nodes)


def _returns(*, nodes: ListAST) -> list[Return]:
    """Collect the return statements of a function body.

    Args:
        nodes (ListAST): Function body nodes.

    Returns:
        list[Return]: ``Return`` nodes in source order.

    """
    return [node for node in nodes if isinstance(node, Return)]


def receiver_info(
    *,
    module: Module,
    function: Function,
) -> tuple[str, bool] | None:
    """Identify a direct class method's receiver parameter.

    Args:
        module (Module): Module that owns the function.
        function (Function): Function to inspect.

    Returns:
        tuple[str, bool] | None:
            ``(receiver name, is_classmethod)``, or ``None`` when the
            function is not a direct method of a class or is a static method.

    """
    for statement in module.body:
        if not isinstance(statement, ClassDef):
            continue
        if not any(child is function for child in statement.body):
            continue
        positional: list[arg] = [
            *function.args.posonlyargs,
            *function.args.args,
        ]
        if not positional:
            return None
        receiver: str = positional[0].arg
        decorated: SetStr = {
            node.id if isinstance(node, Name) else node.attr
            for node in function.decorator_list
            if isinstance(node, (Name, Attribute))
        }
        if "staticmethod" in decorated:
            return None
        return receiver, "classmethod" in decorated
    return None


def _receiver_return(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    parameter: str,
    is_classmethod: bool,
) -> bool:
    """Tell whether every return hands back the receiver itself.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        parameter (str): Receiver parameter name.
        is_classmethod (bool): ``True`` for ``return cls()`` shapes.

    Returns:
        bool: ``True`` when every return is ``return self`` or ``return cls()``
            and the receiver is used nowhere else.

    """
    returns: list[Return] = _returns(nodes=nodes)
    if not returns:
        return False
    for node in returns:
        value: AST | None = node.value
        if is_classmethod:
            matched: bool = (
                isinstance(value, Call)
                and isinstance(value.func, Name)
                and value.func.id == parameter
            )
        else:
            matched = isinstance(value, Name) and value.id == parameter
        if not matched:
            return False
    for use in _uses(nodes=nodes, parameter=parameter):
        parent: AST | None = parents.get(use)
        if is_classmethod:
            grandparent: AST | None = (
                parents.get(parent) if parent is not None else None
            )
            matched = (
                isinstance(parent, Call)
                and parent.func is use
                and isinstance(grandparent, Return)
                and grandparent.value is parent
            )
        else:
            matched = isinstance(parent, Return) and parent.value is use
        if not matched:
            return False
    return True


def isinstance_guard(
    *,
    test: AST,
    parameter: str,
    counts: Mapping[str, int],
) -> frozenset[str] | None:
    """Collect constraint classes when a test is only isinstance checks.

    Args:
        test (AST): ``If`` test expression.
        parameter (str): Parameter name.
        counts (Mapping[str, int]): Module binding counts, to reject a shadowed
            ``isinstance``.

    Returns:
        frozenset[str] | None:
            The class names, or ``None`` when the test mixes in anything else.

    """
    if (
        isinstance(test, Call)
        and isinstance(test.func, Name)
        and test.func.id == "isinstance"
        and counts.get("isinstance", 0) == 0
        and not test.keywords
        and len(test.args) == _GUARD_ARITY
        and isinstance(test.args[0], Name)
        and test.args[0].id == parameter
    ):
        second: AST = test.args[1]
        if isinstance(second, Name):
            return frozenset({second.id})
        if isinstance(second, Tuple) and second.elts:
            names: ListStr = [
                item.id for item in second.elts if isinstance(item, Name)
            ]
            if len(names) == len(second.elts):
                return frozenset(names)
        return None
    if isinstance(test, BoolOp):
        merged: SetStr = set()
        for value in test.values:
            part: frozenset[str] | None = isinstance_guard(
                test=value,
                parameter=parameter,
                counts=counts,
            )
            if part is None:
                return None
            merged.update(part)
        return frozenset(merged)
    return None


def _guarded_constraints(
    *,
    node: Return,
    parents: DictASTAST,
    parameter: str,
    counts: Mapping[str, int],
) -> SetStr | None:
    """Collect the isinstance class names guarding one return.

    Args:
        node (Return): Return statement to inspect.
        parents (DictASTAST): Parent of every node.
        parameter (str): Parameter name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        SetStr | None:
            Guarded class names, or ``None`` when no enclosing ``if`` body
            guards the return with an isinstance test on the parameter.

    """
    found: SetStr = set()
    child: AST = node
    cursor: AST | None = parents.get(node)
    while cursor is not None and not isinstance(
        cursor,
        (FunctionDef, AsyncFunctionDef),
    ):
        if isinstance(cursor, If) and any(
            stmt is child for stmt in cursor.body
        ):
            guard: frozenset[str] | None = isinstance_guard(
                test=cursor.test,
                parameter=parameter,
                counts=counts,
            )
            if guard is not None:
                found.update(guard)
        child, cursor = cursor, parents.get(cursor)
    return found or None


def _constrained_plan(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> TypeVarPlan | None:
    """Plan a constrained TypeVar for isinstance-guarded returns.

    Every return must hand back the bare parameter from inside an ``if``
    body whose test consists only of ``isinstance(parameter, ...)`` checks,
    so the parameter is provably one of the collected classes.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        parameter (str): Parameter name.
        variable (str): Type variable name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        TypeVarPlan | None:
            The plan, or ``None`` when any return is unguarded or ambiguous.

    """
    returns: list[Return] = _returns(nodes=nodes)
    if not returns:
        return None
    for node in returns:
        if not (isinstance(node.value, Name) and node.value.id == parameter):
            return None
    for use in _uses(nodes=nodes, parameter=parameter):
        parent: AST | None = parents.get(use)
        guarded: bool = (
            isinstance(parent, Return) and parent.value is use
        ) or (
            isinstance(parent, Call)
            and len(parent.args) > 0
            and parent.args[0] is use
            and isinstance(parent.func, Name)
            and parent.func.id == "isinstance"
        )
        if not guarded:
            return None
    constraints: SetStr = set()
    for node in returns:
        found: SetStr | None = _guarded_constraints(
            node=node,
            parents=parents,
            parameter=parameter,
            counts=counts,
        )
        if found is None:
            return None
        constraints.update(found)
    if len(constraints) < _MIN_CONSTRAINTS:
        return None
    return TypeVarPlan(
        annotate=True,
        param=variable,
        returns=variable,
        variable=True,
        constraints=tuple(sorted(constraints)),
    )


_GUARD_ARITY: Final[int] = 2
_MIN_CONSTRAINTS: Final[int] = 2
_MIN_INVOLVED: Final[int] = 2
_ELEMENT_CONSTRUCTORS: Final[frozenset[str]] = frozenset(
    {"list", "tuple", "set", "frozenset"},
)


def _int_slice(*, node: AST) -> bool:
    """Tell whether a subscript slice is an integer literal.

    Args:
        node (AST): Slice expression.

    Returns:
        bool: ``True`` for non-bool integer constants.

    """
    return (
        isinstance(node, Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _return_shape(
    *,
    value: AST | None,
    parameter: str,
    counts: Mapping[str, int],
) -> str | None:
    """Classify one return value's pass-through shape.

    Args:
        value (AST | None): Returned expression.
        parameter (str): Parameter name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        str | None: ``"subscript"`` or the constructor name, or ``None``.

    """
    if (
        isinstance(value, Subscript)
        and isinstance(value.value, Name)
        and value.value.id == parameter
        and _int_slice(node=value.slice)
    ):
        return "subscript"
    if (
        isinstance(value, Call)
        and isinstance(value.func, Name)
        and value.func.id in _ELEMENT_CONSTRUCTORS
        and counts.get(value.func.id, 0) == 0
        and len(value.args) == 1
        and isinstance(value.args[0], Name)
        and value.args[0].id == parameter
        and not value.keywords
    ):
        return value.func.id
    return None


def _use_matches(
    *,
    use: Name,
    parents: DictASTAST,
    shape: str | None,
    counts: Mapping[str, int],
) -> bool:
    """Tell whether one parameter use matches the return shape.

    Args:
        use (Name): Parameter name node.
        parents (DictASTAST): Parent of every node.
        shape (str | None): Uniform return shape, if any.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        bool: ``True`` when the use is the expected subscript or constructor
            argument inside a return.

    """
    parent: AST | None = parents.get(use)
    grandparent: AST | None = (
        parents.get(parent) if parent is not None else None
    )
    if shape == "subscript":
        return (
            isinstance(parent, Subscript)
            and parent.value is use
            and _int_slice(node=parent.slice)
            and isinstance(grandparent, Return)
            and grandparent.value is parent
        )
    if shape is None:
        return False
    return (
        isinstance(parent, Call)
        and len(parent.args) == 1
        and parent.args[0] is use
        and isinstance(parent.func, Name)
        and parent.func.id == shape
        and counts.get(shape, 0) == 0
        and isinstance(grandparent, Return)
        and grandparent.value is parent
    )


def _element_plan(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> TypeVarPlan | None:
    """Plan element pass-through: ``items[0]`` or ``list(items)``.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        parameter (str): Parameter name.
        variable (str): Type variable name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        TypeVarPlan | None: The plan, or ``None`` when returns mix shapes
            or the parameter is used anywhere else.

    """
    returns: list[Return] = _returns(nodes=nodes)
    if not returns:
        return None
    shape: str | None = None
    for node in returns:
        current: str | None = _return_shape(
            value=node.value,
            parameter=parameter,
            counts=counts,
        )
        if current is None or (shape is not None and shape != current):
            return None
        shape = current
    for use in _uses(nodes=nodes, parameter=parameter):
        if not _use_matches(
            use=use,
            parents=parents,
            shape=shape,
            counts=counts,
        ):
            return None
    if shape == "subscript":
        return TypeVarPlan(
            annotate=True,
            param=f"Sequence[{variable}]",
            returns=variable,
            variable=True,
            imports=(("collections.abc", "Sequence"),),
        )
    spelled: str = (
        f"{shape}[{variable}, ...]"
        if shape == "tuple"
        else f"{shape}[{variable}]"
    )
    return TypeVarPlan(
        annotate=True,
        param=f"Iterable[{variable}]",
        returns=spelled,
        variable=True,
        imports=(("collections.abc", "Iterable"),),
    )


@dataclass(slots=True)
class _MemberCalls:
    """Accumulate the call shapes seen for one bound member.

    Attributes:
        positional (set[int]): Positional argument counts seen.
        keywords (set[frozenset[str]]): Keyword argument name sets seen.
        awaited (int): Awaited-call count.
        calls (int): Total call count.

    """

    positional: set[int]
    keywords: set[frozenset[str]]
    awaited: int
    calls: int


def _member_calls(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    parameter: str,
) -> dict[str, _MemberCalls] | None:
    """Collect the ``param.member(...)`` call shapes for a parameter.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        parameter (str): Parameter name.

    Returns:
        dict[str, _MemberCalls] | None:
            Call shapes by member name, or ``None`` when a use
            is not a bare return or a plain attribute call.

    """
    calls: dict[str, _MemberCalls] = {}
    for use in _uses(nodes=nodes, parameter=parameter):
        parent: AST | None = parents.get(use)
        if isinstance(parent, Return) and parent.value is use:
            continue
        attribute: Attribute | None = _member_call_parent(
            parent=parent,
            use=use,
        )
        if attribute is None:
            return None
        call: AST | None = parents.get(attribute)
        if not (isinstance(call, Call) and call.func is attribute):
            return None
        if any(isinstance(arg, Starred) for arg in call.args) or any(
            keyword.arg is None for keyword in call.keywords
        ):
            return None
        grandparent: AST | None = parents.get(call)
        entry: _MemberCalls = calls.setdefault(
            attribute.attr,
            _MemberCalls(
                positional=set(),
                keywords=set(),
                awaited=0,
                calls=0,
            ),
        )
        entry.positional.add(len(call.args))
        entry.keywords.add(
            frozenset(
                name
                for keyword in call.keywords
                if (name := keyword.arg) is not None
            ),
        )
        entry.calls += 1
        if isinstance(grandparent, Await):
            entry.awaited += 1
    return calls or None


def _member_call_parent(
    *,
    parent: AST | None,
    use: Name,
) -> Attribute | None:
    """Return the ``param.attr`` load parent of a use, if any.

    Args:
        parent (AST | None): Parent node of the use.
        use (Name): Parameter name node.

    Returns:
        Attribute | None: The attribute node, or ``None``.

    """
    if (
        isinstance(parent, Attribute)
        and parent.value is use
        and isinstance(parent.ctx, Load)
    ):
        return parent
    return None


def _bound_members(*, calls: dict[str, _MemberCalls]) -> list[Member] | None:
    """Turn collected call shapes into protocol members.

    Args:
        calls (dict[str, _MemberCalls]): Call shapes by member name.

    Returns:
        list[Member] | None: Member list, or ``None`` when a member's call
            shapes are not a single uniform signature.

    """
    members: list[Member] = []
    for name in sorted(calls):
        entry: _MemberCalls = calls[name]
        if len(entry.positional) != 1 or len(entry.keywords) != 1:
            return None
        if entry.awaited not in (0, entry.calls):
            return None
        positional_count: int = next(iter(entry.positional))
        keyword_names: frozenset[str] = next(iter(entry.keywords))
        members.append(
            Member(
                name=name,
                is_method=True,
                positional=(None,) * positional_count,
                keywords=tuple(
                    sorted((key, None) for key in keyword_names),
                ),
                is_async=entry.awaited == entry.calls,
            ),
        )
    return members


def _bound_plan(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    parameter: str,
    variable: str,
) -> TypeVarPlan | None:
    """Plan a bound TypeVar for member-use-plus-return shapes.

    The parameter may only be returned bare or used as ``param.member(...)``;
    every return must hand back the parameter itself.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        parameter (str): Parameter name.
        variable (str): Type variable name.

    Returns:
        TypeVarPlan | None:
            The plan with a ``StructuralUsage`` bound, or ``None``.

    """
    returns: list[Return] = _returns(nodes=nodes)
    if not returns:
        return None
    for node in returns:
        if not (isinstance(node.value, Name) and node.value.id == parameter):
            return None
    calls: dict[str, _MemberCalls] | None = _member_calls(
        nodes=nodes,
        parents=parents,
        parameter=parameter,
    )
    if calls is None:
        return None
    members: list[Member] | None = _bound_members(calls=calls)
    if members is None:
        return None
    return TypeVarPlan(
        annotate=True,
        param=variable,
        returns=variable,
        variable=True,
        bound=StructuralUsage(members=tuple(members)),
    )


def typevar_plan(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
    receiver: tuple[str, bool] | None,
) -> TypeVarPlan | None:
    """Choose the narrowest provable annotation plan for a parameter.

    Args:
        function (Function): Function that owns the parameter.
        parameter (str): Parameter name.
        variable (str): Type variable name to spell annotations with.
        counts (Mapping[str, int]): Module binding counts.
        receiver (tuple[str, bool] | None): ``(name, is_classmethod)`` when the
            function is a method.

    Returns:
        TypeVarPlan | None: The plan, or ``None`` when nothing is provable.

    """
    scope: tuple[ListAST, DictASTAST] | None = _scope(function=function)
    if scope is None or _rebound(nodes=scope[0], parameter=parameter):
        return None
    nodes, parents = scope
    uses: list[Name] = _uses(nodes=nodes, parameter=parameter)
    if not uses:
        return None
    fall_off: bool = can_fall_off(body=function.body)

    def _noneable(plan: TypeVarPlan) -> TypeVarPlan:
        """Add ``None`` to the return when the function can fall off the end.

        Args:
            plan (TypeVarPlan): Plan to adjust.

        Returns:
            TypeVarPlan: The plan, with ``| None`` appended when needed.

        """
        if fall_off:
            return replace(plan, returns=f"{plan.returns} | None")
        return plan

    plan: TypeVarPlan | None = None
    if (
        receiver is not None
        and parameter == receiver[0]
        and _receiver_return(
            nodes=nodes,
            parents=parents,
            parameter=parameter,
            is_classmethod=receiver[1],
        )
    ):
        plan = TypeVarPlan(
            annotate=False,
            param=None,
            returns="Self",
            variable=False,
            imports=(("typing", "Self"),),
        )
    if plan is None:
        plan = (
            _constrained_plan(
                nodes=nodes,
                parents=parents,
                parameter=parameter,
                variable=variable,
                counts=counts,
            )
            or _element_plan(
                nodes=nodes,
                parents=parents,
                parameter=parameter,
                variable=variable,
                counts=counts,
            )
            or _bound_plan(
                nodes=nodes,
                parents=parents,
                parameter=parameter,
                variable=variable,
            )
            or _generic_plan(
                function=function,
                parameter=parameter,
                variable=variable,
                counts=counts,
                scope=(nodes, parents),
            )
        )
    if plan is None:
        return None
    plan = _noneable(plan=plan)
    if plan.variable and plan.bound is None:
        bound: StructuralUsage | None = _orderable_bound(
            uses=uses,
            parents=parents,
            counts=counts,
        )
        if bound is not None:
            plan = replace(plan, bound=bound)
    return plan


_ORDER_MEMBERS: Final[frozenset[str]] = frozenset(
    {"__lt__", "__le__", "__gt__", "__ge__", "__contains__"},
)


def _orderable_bound(
    *,
    uses: list[Name],
    parents: DictASTAST,
    counts: Mapping[str, int],
) -> StructuralUsage | None:
    """Build the bound protocol for parameters used under order operators.

    ``return a if a > b else b`` only type-checks when ``a`` and ``b`` know
    how to order themselves, so the shared ``T`` needs a ``bound=`` protocol
    carrying the applied dunder members. Equality and identity operators are
    provided by ``object`` and constrain nothing.

    Args:
        uses (list[Name]): Load-time uses of the parameter.
        parents (DictASTAST): Parent of every node.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        StructuralUsage | None:
            The bound usage, or ``None`` when no use applies an order operator.

    """
    positional: dict[str, set[str | None]] = {}
    for use in uses:
        cursor: AST | None = parents.get(use)
        while cursor is not None and not isinstance(cursor, Return):
            if isinstance(cursor, Compare) and (
                use is cursor.left or use in cursor.comparators
            ):
                pairs: list[tuple[str, tuple[str | None, ...]]] | None = (
                    compare_members(
                        compare=cursor,
                        node=use,
                        counts=counts,
                        env=None,
                    )
                )
                if pairs is not None:
                    for member, operand_types in pairs:
                        if member in _ORDER_MEMBERS:
                            positional.setdefault(member, set()).add(
                                operand_types[0],
                            )
            cursor = parents.get(cursor)
    if not positional:
        return None
    members: tuple[Member, ...] = tuple(
        Member(
            name=name,
            is_method=True,
            positional=((None if len(types) > 1 else next(iter(types))),),
            keywords=(),
            returns="bool",
        )
        for name, types in sorted(positional.items())
    )
    return StructuralUsage(members=members)


def _generic_plan(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
    scope: tuple[ListAST, DictASTAST],
) -> TypeVarPlan | None:
    """Plan the generic pass-through via ``provable_return``.

    Args:
        function (Function): Function that owns the parameter.
        parameter (str): Parameter name.
        variable (str): Type variable name.
        counts (Mapping[str, int]): Module binding counts.
        scope (tuple[ListAST, DictASTAST]): Body nodes and parent map.

    Returns:
        TypeVarPlan | None:
            The plan, or ``None`` when the proven return is unusable.

    """
    nodes, parents = scope
    uses: list[Name] = _uses(nodes=nodes, parameter=parameter)
    result: str | None = provable_return(
        function=function,
        known_types={parameter: variable},
        counts=counts,
    )
    if result is None or _mentions_opaque(result=result):
        return None
    mentioned: bool = any(
        isinstance(node, Name) and node.id == variable
        for node in walk(node=parse(source=result, mode="eval"))
    )
    if not mentioned:
        return None
    uses_pure: bool = all(_is_pure(node=use, parents=parents) for use in uses)
    if not uses_pure:
        return None
    return TypeVarPlan(
        annotate=True,
        param=variable,
        returns=result,
        variable=True,
    )


def candidate_params(
    *,
    function: Function,
    receiver: tuple[str, bool] | None,
    include_annotated: bool = False,
) -> dict[str, arg]:
    """Collect parameters eligible for synthesized annotations.

    Args:
        function (Function): Function that owns the parameters.
        receiver (tuple[str, bool] | None): ``(name, is_classmethod)`` when the
            function is a method.
        include_annotated (bool): Also return parameters already carrying an
            annotation (the group a shared variable may span).

    Returns:
        dict[str, arg]: ``{name: arg}`` for positional parameters, excluding
            the receiver.

    """
    excluded: str | None = receiver[0] if receiver is not None else None
    candidates: dict[str, arg] = {}
    for parameter in (*function.args.posonlyargs, *function.args.args):
        if (
            (include_annotated or parameter.annotation is None)
            and parameter.arg != excluded
            and not parameter_has_default(
                function=function,
                parameter=parameter,
            )
        ):
            candidates[parameter.arg] = parameter
    return candidates


def _flat_container(
    *,
    value: AST | None,
    candidates: Mapping[str, str],
) -> tuple[str, ListStr] | None:
    """Spell a flat container of parameter names.

    Args:
        value (AST | None): Return expression.
        candidates (Mapping[str, str]): Parameter name to type variable name.

    Returns:
        tuple[str, ListStr] | None:
            ``(annotation source, involved parameter names)`` or ``None``.

    """
    if value is None:
        return None
    if isinstance(value, (List, Set, Tuple)):
        return _sequence_container(value=value, candidates=candidates)
    if isinstance(value, Dict):
        return _dict_container(value=value, candidates=candidates)
    return None


def _sequence_container(
    *,
    value: List | Set | Tuple,
    candidates: Mapping[str, str],
) -> tuple[str, ListStr] | None:
    """Spell a flat list/set/tuple of parameter names.

    Args:
        value (List | Set | Tuple): Container return expression.
        candidates (Mapping[str, str]): Parameter name to type variable name.

    Returns:
        tuple[str, ListStr] | None:
            ``(annotation source, involved parameter names)`` or ``None``.

    """
    parts: ListStr = []
    involved: ListStr = []
    for element in value.elts:
        if not (isinstance(element, Name) and element.id in candidates):
            return None
        parts.append(candidates[element.id])
        involved.append(element.id)
    unique: ListStr = sorted(dict.fromkeys(parts))
    if isinstance(value, Tuple):
        return f"tuple[{', '.join(parts)}]", involved
    kind: str = "list" if isinstance(value, List) else "set"
    return f"{kind}[{' | '.join(unique)}]", involved


def _dict_container(
    *,
    value: Dict,
    candidates: Mapping[str, str],
) -> tuple[str, ListStr] | None:
    """Spell a flat dict of parameter-name keys and values.

    Args:
        value (Dict): Dict return expression.
        candidates (Mapping[str, str]): Parameter name to type variable name.

    Returns:
        tuple[str, ListStr] | None:
            ``(annotation source, involved parameter names)`` or ``None``.

    """
    keys: ListStr = []
    values: ListStr = []
    key_involved: ListStr = []
    value_involved: ListStr = []
    for key, item in zip(value.keys, value.values, strict=True):
        if key is None or not (isinstance(key, Name) and key.id in candidates):
            return None
        if not (isinstance(item, Name) and item.id in candidates):
            return None
        keys.append(candidates[key.id])
        values.append(candidates[item.id])
        key_involved.append(key.id)
        value_involved.append(item.id)
    spelled: str = (
        f"dict[{' | '.join(sorted(dict.fromkeys(keys)))}, "
        f"{' | '.join(sorted(dict.fromkeys(values)))}]"
    )
    return spelled, [*key_involved, *value_involved]


def _multi_return_scope(
    *,
    function: Function,
    candidates: Mapping[str, str],
) -> tuple[ListAST, DictASTAST, list[Return]] | None:
    """Collect body nodes, parents and returns for ``multi_return``.

    Args:
        function (Function): Function that owns the parameters.
        candidates (Mapping[str, str]): Parameter name to type variable name.

    Returns:
        tuple[ListAST, DictASTAST, list[Return]] | None:
            ``(nodes, parents, returns)`` or ``None`` when the
            body yields, rebinds a candidate or has no returns.

    """
    nodes: ListAST = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    if any(
        name in names_bound_by(node=node)
        for node in nodes
        for name in candidates
    ):
        return None
    parents: DictASTAST = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    returns: list[Return] = _returns(nodes=nodes)
    if not returns:
        return None
    return nodes, parents, returns


def multi_return(
    *,
    function: Function,
    candidates: Mapping[str, str],
) -> tuple[tuple[str, ...], str] | None:
    """Prove a multi-parameter container return shape.

    Every return must be a flat ``list``/``set``/``tuple``/``dict`` of bare
    parameter names, every involved parameter must be used only inside
    those returns, and at least two distinct parameters must appear.

    Args:
        function (Function): Function that owns the parameters.
        candidates (Mapping[str, str]): Parameter name to type variable name.

    Returns:
        tuple[tuple[str, ...], str] | None:
            ``(involved parameter names, return annotation source)``
            or ``None``.

    """
    if function.returns is not None or len(candidates) <= 1:
        return None
    scope: tuple[ListAST, DictASTAST, list[Return]] | None = (
        _multi_return_scope(function=function, candidates=candidates)
    )
    if scope is None:
        return None
    nodes, parents, returns = scope
    spelled: ListStr = []
    involved: ListStr = []
    for node in returns:
        shaped: tuple[str, ListStr] | None = _flat_container(
            value=node.value,
            candidates=candidates,
        )
        if shaped is None:
            return None
        spelled.append(shaped[0])
        involved.extend(shaped[1])
    unique_involved: ListStr = list(dict.fromkeys(involved))
    if len(unique_involved) < _MIN_INVOLVED or len(set(spelled)) != 1:
        return None
    if not _container_uses_clean(
        nodes=nodes,
        parents=parents,
        involved=unique_involved,
    ):
        return None
    return tuple(unique_involved), spelled[0]


def _container_uses_clean(
    *,
    nodes: ListAST,
    parents: DictASTAST,
    involved: ListStr,
) -> bool:
    """Tell whether every involved parameter use sits in a returned container.

    Args:
        nodes (ListAST): Function body nodes.
        parents (DictASTAST): Parent of every node.
        involved (ListStr): Parameter names that appear in the return
            containers.

    Returns:
        bool: ``True`` when each use's parent is a container directly returned.

    """
    for name in involved:
        for use in _uses(nodes=nodes, parameter=name):
            parent: AST | None = parents.get(use)
            grandparent: AST | None = (
                parents.get(parent) if parent is not None else None
            )
            if not (
                isinstance(parent, (List, Set, Tuple, Dict))
                and isinstance(grandparent, Return)
                and grandparent.value is parent
            ):
                return False
    return True


def _partner_names(
    *,
    use: AST,
    parents: Mapping[AST, AST],
    candidates: Collection[str],
) -> SetStr:
    """Name the candidate parameters combined with one use.

    Args:
        use (AST): Name node where the parameter is read.
        parents (Mapping[AST, AST]): Parent of every node.
        candidates (Collection[str]): Parameter names eligible for a shared
            variable.

    Returns:
        SetStr:
            Candidate names appearing in a combining expression above ``use``.

    """
    combining: tuple[type, ...] = (BinOp, BoolOp, Compare)
    found: SetStr = set()
    cursor: AST | None = parents.get(use)
    while cursor is not None and not isinstance(
        cursor,
        (FunctionDef, AsyncFunctionDef),
    ):
        if isinstance(cursor, combining):
            found.update(
                other.id
                for other in walk(node=cursor)
                if isinstance(other, Name)
                and other.id in candidates
                and other is not use
            )
        cursor = parents.get(cursor)
    return found


def shared_parameters(
    *,
    function: Function,
    candidates: Collection[str],
) -> ListStr | None:
    """Name the parameters only ever combined with each other.

    ``def f(a, b): return a + b`` forces its two inputs through one shared
    operation — adding them only works when their types agree, so one
    ``TypeVar`` covers both. The same holds for ``a or b`` and ``a > b``.
    Parameters merely collected together (``return (a, b)``) keep their own
    variables, and parameters that never meet refuse.

    Args:
        function (Function): Function that owns the parameters.
        candidates (Collection[str]): Parameter names eligible for a shared
            variable.

    Returns:
        ListStr | None:
            The sorted parameter names sharing one ``TypeVar``, or ``None``
            when fewer than two candidates exist or they do not all belong to
        one combined group. An already-annotated return does not refuse:
            a sibling's fix may have written the shared variable already.

    """
    scope: tuple[ListAST, DictASTAST] | None = _scope_nodes(
        function=function,
    )
    if scope is None or len(candidates) <= 1:
        return None
    nodes, parents = scope
    partners: dict[str, SetStr] = {name: set() for name in candidates}
    for name in candidates:
        for use in _uses(nodes=nodes, parameter=name):
            partners[name].update(
                _partner_names(
                    use=use,
                    parents=parents,
                    candidates=candidates,
                ),
            )
    union: dict[str, str] = {name: name for name in candidates}

    def root(name: str) -> str:
        """Find the component representative of one parameter.

        Args:
            name (str): Parameter name.

        Returns:
            str: The component's representative name.

        """
        while union[name] != name:
            union[name] = union[union[name]]
            name = union[name]
        return name

    for name, others in partners.items():
        for other in others:
            union[root(name=name)] = root(name=other)
    components: SetStr = {root(name=name) for name in candidates}
    if len(components) != 1:
        return None
    return sorted(candidates)


def _combined_expression(
    *,
    node: AST,
    involved: Collection[str],
    variable: str,
) -> str | None:
    """Spell ``variable`` when an expression only combines involved names.

    ``a + b``, ``a or b`` and ``a < b`` all return one of the combined
    values (or a comparison of them), so with every operand drawn from the
    shared set the result is the shared variable itself.

    Args:
        node (AST): Expression to spell.
        involved (Collection[str]): Parameter names sharing the variable.
        variable (str): Shared type variable name.

    Returns:
        str | None: ``variable`` when every operand is involved, else ``None``.

    """
    if isinstance(node, Name):
        return variable if node.id in involved else None
    if isinstance(node, BinOp | BoolOp | Compare):
        operands: ListAST = []
        if isinstance(node, BinOp):
            operands = [node.left, node.right]
        elif isinstance(node, BoolOp):
            operands = list(node.values)
        else:
            operands = [node.left, *node.comparators]
        spelled: ListStr = []
        for operand in operands:
            piece: str | None = _combined_expression(
                node=operand,
                involved=involved,
                variable=variable,
            )
            if piece is None or piece != variable:
                return None
            spelled.append(piece)
        return variable
    return None


def shared_return(
    *,
    function: Function,
    involved: Collection[str],
    variable: str,
    counts: Mapping[str, int],
) -> str | None:
    """Spell the return type when several parameters share one ``TypeVar``.

    Args:
        function (Function): Function that owns the parameters.
        involved (Collection[str]): Parameter names sharing ``variable``.
        variable (str): Shared type variable name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        str | None:
            The return annotation source, or ``None`` when the return does not
            mention the shared variable. An existing return already spelling
            ``variable`` counts as proven (a sibling parameter's fix wrote it).

    """
    if function.returns is not None:
        return (
            variable
            if any(
                isinstance(node, Name) and node.id == variable
                for node in walk(node=function.returns)
            )
            else None
        )
    result: str | None = provable_return(
        function=function,
        known_types=dict.fromkeys(involved, variable),
        counts=counts,
    )
    if result is not None:
        if _mentions_opaque(result=result):
            return None
        mentioned: bool = any(
            isinstance(node, Name) and node.id == variable
            for node in walk(node=parse(source=result, mode="eval"))
        )
        return result if mentioned else None
    returns: list[expr] = [
        node.value
        for node in _own_nodes(function=function)
        if isinstance(node, Return) and node.value is not None
    ]
    if not returns:
        return None
    for value in returns:
        combined: str | None = _combined_expression(
            node=value,
            involved=involved,
            variable=variable,
        )
        if combined is None:
            return None
    return variable


def _own_nodes(*, function: Function) -> ListAST:
    """Collect the function's own nodes, skipping nested definitions.

    Args:
        function (Function): Function to inspect.

    Returns:
        ListAST: Nodes of the function body, excluding everything
            nested inside ``def`` /``lambda``/``class`` scopes.

    """
    found: ListAST = []
    stack: ListAST = list(function.body)
    while stack:
        node: AST = stack.pop()
        if isinstance(node, (FunctionDef, AsyncFunctionDef, Lambda, ClassDef)):
            continue
        found.append(node)
        stack.extend(iter_child_nodes(node=node))
    return found


def _own_returns(*, function: Function) -> list[Return]:
    """Collect the function's own returns, skipping nested definitions.

    Args:
        function (Function): Function to inspect.

    Returns:
        list[Return]: ``Return`` nodes of the function body, excluding returns
            inside nested ``def`` /``lambda``/``class`` scopes.

    """
    return [
        node
        for node in _own_nodes(function=function)
        if isinstance(node, Return)
    ]


def forwarding_decorator(*, function: Function) -> tuple[str, str] | None:
    """Detect a passthrough decorator that forwards ``*args``/``**kwargs``.

    ``def deco(f): ...; def wrapper(*a, **k): return f(*a, **k); return
    wrapper`` preserves the wrapped signature, so ``f`` is
    ``Callable[P, R]`` and the decorator returns ``Callable[P, R]``. A
    wrapper that alters the arguments does not forward and refuses.

    Args:
        function (Function): Function to inspect.

    Returns:
        tuple[str, str] | None:
            ``(parameter name, wrapper name)``, or ``None`` when
            the function does not forward its parameter unchanged.

    """
    parameters: SetStr = {
        parameter.arg
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
        )
    }
    returns: list[Return] = _own_returns(function=function)
    if not returns or any(
        not (isinstance(node.value, Name)) for node in returns
    ):
        return None
    returned: SetStr = {
        node.value.id for node in returns if isinstance(node.value, Name)
    }
    for statement in function.body:
        if not isinstance(statement, (FunctionDef, AsyncFunctionDef)):
            continue
        if statement.name not in returned:
            continue
        arguments_node: arguments = statement.args
        if (
            arguments_node.vararg is None
            or arguments_node.kwarg is None
            or len(statement.body) != 1
        ):
            continue
        match statement.body[0]:
            case Return(
                value=Call(
                    func=Name(id=target),
                    args=[Starred(value=Name(id=vararg))],
                    keywords=[
                        keyword(arg=None, value=Name(id=kwarg)),
                    ],
                ),
            ) if (
                target in parameters
                and vararg == arguments_node.vararg.arg
                and kwarg == arguments_node.kwarg.arg
            ):
                uses: int = sum(
                    1
                    for item in function.body
                    for node in walk(node=item)
                    if isinstance(node, Name) and node.id == target
                )
                if uses == 1:
                    return target, statement.name
                return None
            case _:
                return None
    return None


def variadic_passthrough(*, function: Function) -> str | None:
    """Name the ``*args`` parameter when it is returned unchanged.

    ``def pack(*args): return args`` preserves the variadic shape; a
    ``TypeVarTuple`` can describe it. Any other use of the variadic
    parameter refuses.

    Args:
        function (Function): Function to inspect.

    Returns:
        str | None: The ``*args`` parameter name, or ``None``.

    """
    vararg: arg | None = function.args.vararg
    if vararg is None or function.returns is not None:
        return None
    name: str = vararg.arg
    nodes: ListAST = _own_nodes(function=function)
    if any(name in names_bound_by(node=node) for node in nodes) or not (
        returns := _returns(nodes=nodes)
    ):
        return None
    for node in returns:
        value: AST | None = node.value
        if (
            (isinstance(value, Name) and value.id == name)
            or (
                isinstance(value, Call)
                and isinstance(value.func, Name)
                and value.func.id in ("list", "tuple")
                and len(value.args) == 1
                and isinstance(value.args[0], Name)
                and value.args[0].id == name
                and not value.keywords
            )
            or (
                isinstance(value, Tuple)
                and len(value.elts) == 1
                and isinstance(value.elts[0], Starred)
                and isinstance(value.elts[0].value, Name)
                and value.elts[0].value.id == name
            )
        ):
            continue
        return None
    parents: DictASTAST = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    for use in _uses(nodes=nodes, parameter=name):
        cursor: AST | None = parents.get(use)
        while cursor is not None and not isinstance(cursor, Return):
            if not isinstance(cursor, (Call, Starred, Tuple)):
                return None
            cursor = parents.get(cursor)
        if cursor is None:
            return None
    return name


def variance_role(*, statement: ClassDef, typevar: str) -> str | None:
    """Classify how a class uses a type variable.

    A type variable appearing only in result positions (return
    annotations, attribute declarations) is covariant; one appearing only
    in input positions (method parameters) is contravariant; both or
    neither is invariant.

    Args:
        statement (ClassDef): Class to inspect.
        typevar (str): Type variable name.

    Returns:
        str | None: ``"covariant"``, ``"contravariant"`` or ``None``.

    """
    reads: int = 0
    writes: int = 0
    for child in statement.body:
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            skip: SetStr = {"cls", "self"}
            for parameter in (
                *child.args.posonlyargs,
                *child.args.args,
                *child.args.kwonlyargs,
            ):
                if parameter.arg in skip or parameter.annotation is None:
                    continue
                if typevar in {
                    node.id
                    for node in walk(node=parameter.annotation)
                    if isinstance(node, Name)
                }:
                    writes += 1
            if child.returns is not None and typevar in {
                node.id
                for node in walk(node=child.returns)
                if isinstance(node, Name)
            }:
                reads += 1
        elif isinstance(child, AnnAssign) and typevar in {
            node.id
            for node in walk(node=child.annotation)
            if isinstance(node, Name)
        }:
            reads += 1
    if reads and not writes:
        return "covariant"
    if writes and not reads:
        return "contravariant"
    return None


def typevar_holders(
    *,
    module: Module,
    declaration: AST,
    name: str,
) -> tuple[frozenset[str], bool]:
    """Find the functions annotating with one module ``TypeVar``.

    Args:
        module (Module): Module to scan.
        declaration (AST): The ``TypeVar`` assignment to skip.
        name (str): Type variable name.

    Returns:
        tuple[frozenset[str], bool]: ``(holder function names, refused)`` —
            refused when
            the name is used in a body or outside a function.

    """
    holders: SetStr = set()
    for statement in module.body:
        if statement is declaration:
            continue
        if isinstance(statement, (FunctionDef, AsyncFunctionDef)):
            parts: ListAST = [
                part
                for part in (
                    parameter.annotation
                    for parameter in (
                        *statement.args.posonlyargs,
                        *statement.args.args,
                        *statement.args.kwonlyargs,
                        *(
                            (statement.args.vararg,)
                            if statement.args.vararg is not None
                            else ()
                        ),
                        *(
                            (statement.args.kwarg,)
                            if statement.args.kwarg is not None
                            else ()
                        ),
                    )
                )
                if part is not None
            ]
            if statement.returns is not None:
                parts.append(statement.returns)
            annotation_uses: int = sum(
                1
                for part in parts
                for node in walk(node=part)
                if isinstance(node, Name) and node.id == name
            )
            body_uses: int = sum(
                1
                for item in statement.body
                for node in walk(node=item)
                if isinstance(node, Name) and node.id == name
            )
            if annotation_uses:
                holders.add(statement.name)
            if body_uses:
                return frozenset(holders), True
        elif any(
            isinstance(node, Name) and node.id == name
            for node in walk(node=statement)
        ):
            return frozenset(holders), True
    return frozenset(holders), False


def pep695_candidate(*, module: Module) -> tuple[str, str] | None:
    """Name a module ``TypeVar`` used by exactly one function.

    ``T = TypeVar("T")`` at module level followed by a single
    ``def f(x: T) -> T`` collapses into ``def f[T](x: T) -> T`` under
    PEP 695 — but only when ``T`` is used nowhere else and is not
    exported through ``__all__``.

    Args:
        module (Module): Module to inspect.

    Returns:
        tuple[str, str] | None:
            ``(type variable name, function name)``, or ``None``.

    """
    exported: SetStr = set()
    for statement in module.body:
        if (
            isinstance(statement, Assign)
            and any(
                isinstance(target, Name) and target.id == "__all__"
                for target in statement.targets
            )
            and isinstance(statement.value, (List, Tuple))
        ):
            exported.update(
                element.value
                for element in statement.value.elts
                if isinstance(element, Constant)
                and isinstance(element.value, str)
            )
    for declaration in module.body:
        match declaration:
            case Assign(
                targets=[Name(id=name)],
                value=Call(
                    func=Name(id=factory) | Attribute(attr=factory),
                    args=[Constant(value=label)],
                    keywords=[],
                ),
            ) if (
                factory == "TypeVar" and label == name and name not in exported
            ):
                pass
            case _:
                continue
        holders: frozenset[str]
        refused: bool
        holders, refused = typevar_holders(
            module=module,
            declaration=declaration,
            name=name,
        )
        if refused or len(holders) != 1:
            continue
        return name, next(iter(holders))
    return None


def function_scope_names(*, function: Function) -> frozenset[str]:
    """Collect the names a generated identifier in a function must avoid.

    Args:
        function (Function): Function to inspect.

    Returns:
        frozenset[str]: Parameter names plus every name bound inside the body,
            so a
            synthesized ``TypeVar`` or ``Protocol`` never shadows user code.

    """
    names: SetStr = {
        parameter.arg
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    for statement in function.body:
        for node in walk(node=statement):
            names.update(names_bound_by(node=node))
    return frozenset(names)
