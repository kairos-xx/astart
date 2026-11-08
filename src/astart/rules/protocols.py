"""Derive a structural ``Protocol`` from how a parameter is used.

A parameter that is only ever accessed as ``name.attr`` or called as
``name.attr(...)`` is used structurally: any object with those members would
do. :func:`structural_usage` proves that, member by member, and refuses on any
other use. :func:`protocol_source` renders the matching ``Protocol`` class.
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Await,
    Call,
    Expr,
    FunctionDef,
    Load,
    Name,
    Return,
    Starred,
    arg,
    arguments,
    iter_child_nodes,
    unparse,
    walk,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from astart.rules.provable import expression_type
from astart.rules.scopes import names_bound_by

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        indent: Grouped module constant.
        private_prefix: Grouped module constant.
        receiver: Grouped module constant.
        docstring_marker: Grouped module constant.
        callable_member: Attribute name marking a callback protocol.

    """

    indent: Final[str] = "    "
    private_prefix: Final[str] = "__"
    receiver: Final[str] = "self"
    callable_member: Final[str] = "__call__"
    docstring_marker: Final[str] = "Structural type of ``"


@final
@dataclass(frozen=True, slots=True)
class Member:
    """One member a parameter is required to have.

    Attributes:
        name: Attribute name.
        is_method: ``True`` when it is called, ``False`` for a property.
        positional: Annotation source per positional argument, or ``None``
            where the argument type is not provable.
        keywords: ``(name, annotation)`` pairs, sorted by name.
        returns: Return annotation proven from how every result is used, or
            ``None`` when it is not provable.
        is_async: ``True`` when every call is awaited.

    """

    name: str
    is_method: bool
    positional: tuple[str | None, ...]
    keywords: tuple[tuple[str, str | None], ...]
    returns: str | None = None
    is_async: bool = False


@final
@dataclass(frozen=True, slots=True)
class StructuralUsage:
    """Everything a function requires of one parameter.

    Attributes:
        members: Required members sorted by name.

    """

    members: tuple[Member, ...]


@final
@dataclass(frozen=True, slots=True)
class _Call:
    """One call of a member and how its result is used.

    Attributes:
        positional: Annotation source per positional argument.
        keywords: ``(name, annotation)`` pairs, sorted by name.
        awaited: ``True`` when the call is directly awaited.
        result: ``"returned"``, ``"unused"`` or ``"other"`` for how the
            (awaited) result flows.

    """

    positional: tuple[str | None, ...]
    keywords: tuple[tuple[str, str | None], ...]
    awaited: bool
    result: str


@final
@dataclass(slots=True)
class _Draft:
    """Accumulate the uses of one attribute.

    Attributes:
        calls: Call shapes seen.
        reads: Result uses of non-call attribute reads.

    """

    calls: list[_Call]
    reads: list[str]


def parameter_has_default(*, function: Function, parameter: arg) -> bool:
    """Tell whether a parameter has a default value.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter to look up.

    Returns:
        ``True`` when the parameter has a default.

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
        function: Function whose body is walked.

    Yields:
        Each node, statements first.

    """
    for statement in function.body:
        yield from walk(node=statement)


def _call_shape(
    *,
    call: Call,
    counts: Mapping[str, int],
    env: Mapping[str, str] | None,
) -> tuple[tuple[str | None, ...], tuple[tuple[str, str | None], ...]] | None:
    """Describe the arguments of a call to a member.

    Args:
        call: Call expression.
        counts: Module binding counts, for typing arguments.
        env: Types of names visible at the call sites,
            for flow-typed arguments.

    Returns:
        Positional and keyword types, or ``None`` for star arguments.

    """
    if any(isinstance(item, Starred) for item in call.args):
        return None
    if any(item.arg is None for item in call.keywords):
        return None
    if any(item.arg == Constants.receiver for item in call.keywords):
        return None
    positional: tuple[str | None, ...] = tuple(
        expression_type(node=item, counts=counts, env=env)
        for item in call.args
    )
    keywords: tuple[tuple[str, str | None], ...] = tuple(
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
        values: Non-empty list of annotations.

    Returns:
        ``True`` when all values agree.

    """
    return all(value == values[0] for value in values)


def _result_kind(*, node: AST, parents: Mapping[AST, AST]) -> str:
    """Classify how a member result flows.

    Args:
        node: Call or attribute node whose result is classified.
        parents: Parent of every node.

    Returns:
        ``"returned"``, ``"unused"`` or ``"other"``.

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
    function_returns: str | None,
) -> Member | None:
    """Combine every call of one attribute into a member.

    Args:
        name: Attribute name.
        draft: Calls and reads seen for the attribute.
        function_returns: Annotation source of the owning function's return,
            or ``None``.

    Returns:
        The member, or ``None`` when the calls disagree on their shape.

    """
    if not draft.calls:
        returns: str | None = (
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
    merged_positional: tuple[str | None, ...] = tuple(
        first_positional[index]
        if _same(values=[call.positional[index] for call in draft.calls])
        else None
        for index in range(len(first_positional))
    )
    merged_keywords: tuple[tuple[str, str | None], ...] = tuple(
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
        draft: Draft to append to.
        call: Call expression.
        parents: Parent of every node.
        counts: Module binding counts.
        env: Types of names visible at the call site.

    Returns:
        ``False`` when the call shape is not provable.

    """
    shape: (
        tuple[tuple[str | None, ...], tuple[tuple[str, str | None], ...]]
        | None
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
        nodes: Every node of the function body.
        parents: Parent of every node.
        parameter: Parameter name.
        counts: Module binding counts.
        env: Types of names visible at the call sites.

    Returns:
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
                _Draft(calls=[], reads=[]),
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
            and isinstance(parent.ctx, Load)
            and (not parent.attr.startswith(Constants.private_prefix))
        ):
            return None
        attribute: Attribute = parent
        draft = drafts.setdefault(
            attribute.attr,
            _Draft(calls=[], reads=[]),
        )
        attribute_parent: AST | None = parents.get(attribute)
        if isinstance(attribute_parent, Await):
            return None
        if isinstance(attribute_parent, Call) and (
            attribute_parent.func is attribute
        ):
            if not _record_call(
                draft=draft,
                call=attribute_parent,
                parents=parents,
                counts=counts,
                env=env,
            ):
                return None
        else:
            draft.reads.append(
                _result_kind(node=attribute, parents=parents),
            )
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
        function: Function that owns the parameter.
        parameter: Parameter name.
        counts: Module binding counts, for typing call arguments.
        env: Types of names visible at the call sites, for flow-typed
            arguments.

    Returns:
        The required members, or ``None`` when the parameter is rebound, used
        as a plain value, written to, awaited through, or unused.

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
    function_returns: str | None = (
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
        members.append(member)
    return StructuralUsage(members=tuple(members)) if members else None


def _annotated(*, name: str, annotation: str | None) -> str:
    """Spell a parameter with its optional annotation.

    Args:
        name: Parameter name.
        annotation: Annotation source, or ``None``.

    Returns:
        ``name`` or ``name: annotation``.

    """
    return name if annotation is None else f"{name}: {annotation}"


def _member_source(*, member: Member) -> str:
    """Render one member as protocol source.

    Args:
        member: Member to render.

    Returns:
        Indented source lines.

    """
    pad: str = Constants.indent
    returns: str = (
        f" -> {member.returns}" if member.returns is not None else ""
    )
    if not member.is_method:
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
) -> str:
    """Render the ``Protocol`` class for a structural usage.

    Args:
        name: Class name.
        function: Name of the function the usage was derived from.
        parameter: Name of the parameter.
        usage: Required members.

    Returns:
        Python source for the class, ending with a newline.

    """
    header: str = f"""\
class {name}(Protocol):
{Constants.indent}\"""{Constants.docstring_marker}{parameter}`` in \
``{function}``.\"""
"""
    body: str = """\

""".join(_member_source(member=member) for member in usage.members)
    return f"""\
{header}
{body}"""
