"""Detect parameters that only flow through to the return value.

A parameter whose every use is as (an element of) a returned value is generic:
its type is whatever the caller passes. :func:`passthrough_return` proves
that and spells the return annotation in terms of a type variable.
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Await,
    BoolOp,
    Call,
    ClassDef,
    Constant,
    Dict,
    FunctionDef,
    If,
    IfExp,
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
    iter_child_nodes,
    parse,
    walk,
)
from dataclasses import dataclass, replace
from re import search as re_search
from typing import TYPE_CHECKING, Final, final

from astart.rules.protocols import (
    Member,
    StructuralUsage,
    parameter_has_default,
)
from astart.rules.provable import can_fall_off, provable_return
from astart.rules.scopes import names_bound_by

if TYPE_CHECKING:
    from collections.abc import Mapping

    type Function = FunctionDef | AsyncFunctionDef


@final
@dataclass(frozen=True, slots=True)
class TypeVarPlan:
    """How a parameter and the return value should be annotated.

    Attributes:
        annotate: ``True`` when the parameter receives an annotation.
        param: Parameter annotation source, or ``None``.
        returns: Return annotation source.
        variable: ``True`` when a ``TypeVar`` declaration is required.
        constraints: Constraint class names for a constrained TypeVar.
        bound: Required members for a bound TypeVar's protocol, or ``None``.
        imports: ``(source, name)`` pairs the annotations rely on.

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
        node: The ``Name`` node of the parameter.
        parents: Parent of every node.

    Returns:
        ``True`` when the chain up to the ``return`` is only containers and
        conditional branches.

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
            case _:
                return False
        child, parent = parent, parents.get(parent)
    return parent is not None


def passthrough_return(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> str | None:
    """Prove a parameter is generic and spell the matching return type.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter name.
        variable: Name of the type variable standing for the parameter.
        counts: Module binding counts.

    Returns:
        The return annotation source, or ``None`` when the parameter is
        rebound, used for anything but being returned, or the function is
        already annotated or is a generator.

    """
    if function.returns is not None:
        return None
    nodes: list[AST] = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(parameter in names_bound_by(node=node) for node in nodes):
        return None
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    parents: dict[AST, AST] = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    uses: list[AST] = [
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
    if result is None or re_search(
        pattern=r"\b(?:Unknown|Any)\b",
        string=result,
    ):
        return None
    mentioned: bool = any(
        isinstance(node, Name) and node.id == variable
        for node in walk(node=parse(source=result, mode="eval"))
    )
    return result if mentioned else None


def _scope(
    *,
    function: Function,
) -> tuple[list[AST], dict[AST, AST]] | None:
    """Collect a function's own nodes and parents when it is a candidate.

    Args:
        function: Function to inspect.

    Returns:
        ``(nodes, parents)`` or ``None`` when the function is already
        annotated or is a generator.

    """
    if function.returns is not None:
        return None
    nodes: list[AST] = [
        node for statement in function.body for node in walk(node=statement)
    ]
    if any(isinstance(node, (Yield, YieldFrom)) for node in nodes):
        return None
    parents: dict[AST, AST] = {
        child: parent
        for parent in nodes
        for child in iter_child_nodes(node=parent)
    }
    return nodes, parents


def _uses(*, nodes: list[AST], parameter: str) -> list[Name]:
    """Collect the load-time uses of a parameter name.

    Args:
        nodes: Function body nodes.
        parameter: Parameter name.

    Returns:
        ``Name`` nodes that read the parameter.

    """
    return [
        node
        for node in nodes
        if isinstance(node, Name)
        and node.id == parameter
        and isinstance(node.ctx, Load)
    ]


def _rebound(*, nodes: list[AST], parameter: str) -> bool:
    """Tell whether a parameter name is bound anywhere in the function.

    Args:
        nodes: Function body nodes.
        parameter: Parameter name.

    Returns:
        ``True`` when the name is rebound.

    """
    return any(parameter in names_bound_by(node=node) for node in nodes)


def _returns(*, nodes: list[AST]) -> list[Return]:
    """Collect the return statements of a function body.

    Args:
        nodes: Function body nodes.

    Returns:
        ``Return`` nodes in source order.

    """
    return [node for node in nodes if isinstance(node, Return)]


def receiver_info(
    *,
    module: Module,
    function: Function,
) -> tuple[str, bool] | None:
    """Identify a direct class method's receiver parameter.

    Args:
        module: Module that owns the function.
        function: Function to inspect.

    Returns:
        ``(receiver name, is_classmethod)``, or ``None`` when the function
        is not a direct method of a class or is a static method.

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
        decorated: set[str] = {
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
    nodes: list[AST],
    parents: dict[AST, AST],
    parameter: str,
    is_classmethod: bool,
) -> bool:
    """Tell whether every return hands back the receiver itself.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        parameter: Receiver parameter name.
        is_classmethod: ``True`` for ``return cls()`` shapes.

    Returns:
        ``True`` when every return is ``return self`` or ``return cls()``
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


def _isinstance_guard(
    *,
    test: AST,
    parameter: str,
    counts: Mapping[str, int],
) -> frozenset[str] | None:
    """Collect constraint classes when a test is only isinstance checks.

    Args:
        test: ``If`` test expression.
        parameter: Parameter name.
        counts: Module binding counts, to reject a shadowed ``isinstance``.

    Returns:
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
            names: list[str] = [
                item.id for item in second.elts if isinstance(item, Name)
            ]
            if len(names) == len(second.elts):
                return frozenset(names)
        return None
    if isinstance(test, BoolOp):
        merged: set[str] = set()
        for value in test.values:
            part: frozenset[str] | None = _isinstance_guard(
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
    parents: dict[AST, AST],
    parameter: str,
    counts: Mapping[str, int],
) -> set[str] | None:
    """Collect the isinstance class names guarding one return.

    Args:
        node: Return statement to inspect.
        parents: Parent of every node.
        parameter: Parameter name.
        counts: Module binding counts.

    Returns:
        Guarded class names, or ``None`` when no enclosing ``if`` body
        guards the return with an isinstance test on the parameter.

    """
    found: set[str] = set()
    child: AST = node
    cursor: AST | None = parents.get(node)
    while cursor is not None and not isinstance(
        cursor,
        (FunctionDef, AsyncFunctionDef),
    ):
        if isinstance(cursor, If) and any(
            stmt is child for stmt in cursor.body
        ):
            guard: frozenset[str] | None = _isinstance_guard(
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
    nodes: list[AST],
    parents: dict[AST, AST],
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> TypeVarPlan | None:
    """Plan a constrained TypeVar for isinstance-guarded returns.

    Every return must hand back the bare parameter from inside an ``if``
    body whose test consists only of ``isinstance(parameter, ...)`` checks,
    so the parameter is provably one of the collected classes.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        parameter: Parameter name.
        variable: Type variable name.
        counts: Module binding counts.

    Returns:
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
    constraints: set[str] = set()
    for node in returns:
        found: set[str] | None = _guarded_constraints(
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
        node: Slice expression.

    Returns:
        ``True`` for non-bool integer constants.

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
        value: Returned expression.
        parameter: Parameter name.
        counts: Module binding counts.

    Returns:
        ``"subscript"`` or the constructor name, or ``None``.

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
    parents: dict[AST, AST],
    shape: str | None,
    counts: Mapping[str, int],
) -> bool:
    """Tell whether one parameter use matches the return shape.

    Args:
        use: Parameter name node.
        parents: Parent of every node.
        shape: Uniform return shape, if any.
        counts: Module binding counts.

    Returns:
        ``True`` when the use is the expected subscript or constructor
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
    nodes: list[AST],
    parents: dict[AST, AST],
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
) -> TypeVarPlan | None:
    """Plan element pass-through: ``items[0]`` or ``list(items)``.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        parameter: Parameter name.
        variable: Type variable name.
        counts: Module binding counts.

    Returns:
        The plan, or ``None`` when returns mix shapes or the parameter is
        used anywhere else.

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
        positional: Positional argument counts seen.
        keywords: Keyword argument name sets seen.
        awaited: Awaited-call count.
        calls: Total call count.

    """

    positional: set[int]
    keywords: set[frozenset[str]]
    awaited: int
    calls: int


def _member_calls(
    *,
    nodes: list[AST],
    parents: dict[AST, AST],
    parameter: str,
) -> dict[str, _MemberCalls] | None:
    """Collect the ``param.member(...)`` call shapes for a parameter.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        parameter: Parameter name.

    Returns:
        Call shapes by member name, or ``None`` when a use is not a
        bare return or a plain attribute call.

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
        parent: Parent node of the use.
        use: Parameter name node.

    Returns:
        The attribute node, or ``None``.

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
        calls: Call shapes by member name.

    Returns:
        Member list, or ``None`` when a member's call shapes are not a
        single uniform signature.

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
    nodes: list[AST],
    parents: dict[AST, AST],
    parameter: str,
    variable: str,
) -> TypeVarPlan | None:
    """Plan a bound TypeVar for member-use-plus-return shapes.

    The parameter may only be returned bare or used as ``param.member(...)``;
    every return must hand back the parameter itself.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        parameter: Parameter name.
        variable: Type variable name.

    Returns:
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
        function: Function that owns the parameter.
        parameter: Parameter name.
        variable: Type variable name to spell annotations with.
        counts: Module binding counts.
        receiver: ``(name, is_classmethod)`` when the function is a method.

    Returns:
        The plan, or ``None`` when nothing is provable.

    """
    scope: tuple[list[AST], dict[AST, AST]] | None = _scope(function=function)
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
            plan: Plan to adjust.

        Returns:
            The plan, with ``| None`` appended when needed.

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
    return _noneable(plan=plan)


def _generic_plan(
    *,
    function: Function,
    parameter: str,
    variable: str,
    counts: Mapping[str, int],
    scope: tuple[list[AST], dict[AST, AST]],
) -> TypeVarPlan | None:
    """Plan the generic pass-through via ``provable_return``.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter name.
        variable: Type variable name.
        counts: Module binding counts.
        scope: Body nodes and parent map.

    Returns:
        The plan, or ``None`` when the proven return is unusable.

    """
    nodes, parents = scope
    uses: list[Name] = _uses(nodes=nodes, parameter=parameter)
    result: str | None = provable_return(
        function=function,
        known_types={parameter: variable},
        counts=counts,
    )
    if result is None or re_search(
        pattern=r"\b(?:Unknown|Any)\b",
        string=result,
    ):
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
) -> dict[str, arg]:
    """Collect parameters eligible for synthesized annotations.

    Args:
        function: Function that owns the parameters.
        receiver: ``(name, is_classmethod)`` when the function is a method.

    Returns:
        ``{name: arg}`` for unannotated, defaultless positional parameters,
        excluding the receiver.

    """
    excluded: str | None = receiver[0] if receiver is not None else None
    candidates: dict[str, arg] = {}
    for parameter in (*function.args.posonlyargs, *function.args.args):
        if (
            parameter.annotation is None
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
) -> tuple[str, list[str]] | None:
    """Spell a flat container of parameter names.

    Args:
        value: Return expression.
        candidates: Parameter name to type variable name.

    Returns:
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
) -> tuple[str, list[str]] | None:
    """Spell a flat list/set/tuple of parameter names.

    Args:
        value: Container return expression.
        candidates: Parameter name to type variable name.

    Returns:
        ``(annotation source, involved parameter names)`` or ``None``.

    """
    parts: list[str] = []
    involved: list[str] = []
    for element in value.elts:
        if not (isinstance(element, Name) and element.id in candidates):
            return None
        parts.append(candidates[element.id])
        involved.append(element.id)
    unique: list[str] = sorted(dict.fromkeys(parts))
    if isinstance(value, Tuple):
        return f"tuple[{', '.join(parts)}]", involved
    kind: str = "list" if isinstance(value, List) else "set"
    return f"{kind}[{' | '.join(unique)}]", involved


def _dict_container(
    *,
    value: Dict,
    candidates: Mapping[str, str],
) -> tuple[str, list[str]] | None:
    """Spell a flat dict of parameter-name keys and values.

    Args:
        value: Dict return expression.
        candidates: Parameter name to type variable name.

    Returns:
        ``(annotation source, involved parameter names)`` or ``None``.

    """
    keys: list[str] = []
    values: list[str] = []
    key_involved: list[str] = []
    value_involved: list[str] = []
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
) -> tuple[list[AST], dict[AST, AST], list[Return]] | None:
    """Collect body nodes, parents and returns for ``multi_return``.

    Args:
        function: Function that owns the parameters.
        candidates: Parameter name to type variable name.

    Returns:
        ``(nodes, parents, returns)`` or ``None`` when the body yields,
        rebinds a candidate or has no returns.

    """
    nodes: list[AST] = [
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
    parents: dict[AST, AST] = {
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
        function: Function that owns the parameters.
        candidates: Parameter name to type variable name.

    Returns:
        ``(involved parameter names, return annotation source)`` or
        ``None``.

    """
    if function.returns is not None or len(candidates) <= 1:
        return None
    scope: tuple[list[AST], dict[AST, AST], list[Return]] | None = (
        _multi_return_scope(function=function, candidates=candidates)
    )
    if scope is None:
        return None
    nodes, parents, returns = scope
    spelled: list[str] = []
    involved: list[str] = []
    for node in returns:
        shaped: tuple[str, list[str]] | None = _flat_container(
            value=node.value,
            candidates=candidates,
        )
        if shaped is None:
            return None
        spelled.append(shaped[0])
        involved.extend(shaped[1])
    unique_involved: list[str] = list(dict.fromkeys(involved))
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
    nodes: list[AST],
    parents: dict[AST, AST],
    involved: list[str],
) -> bool:
    """Tell whether every involved parameter use sits in a returned container.

    Args:
        nodes: Function body nodes.
        parents: Parent of every node.
        involved: Parameter names that appear in the return containers.

    Returns:
        ``True`` when each use's parent is a container directly returned.

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
