"""Derive a structural ``Protocol`` from how a parameter is used.

A parameter that is only ever accessed as ``name.attr`` or called as
``name.attr(...)`` is used structurally: any object with those members would
do. :func:`structural_usage` proves that, member by member, and refuses on any
other use. :func:`protocol_source` renders the matching ``Protocol`` class.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from re import Pattern
from re import compile as compile_pattern
from typing import TYPE_CHECKING, Final, final

from astart.rules.provable import expression_type

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    type Function = ast.FunctionDef | ast.AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        indent: Grouped module constant.
        private_prefix: Grouped module constant.
        generated_name: Grouped module constant.
        receiver: Grouped module constant.
        docstring_marker: Grouped module constant.

    """

    indent: Final[str] = "    "
    private_prefix: Final[str] = "__"
    generated_name: Final[Pattern[str]] = compile_pattern(pattern="arg\\d+")
    receiver: Final[str] = "self"
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

    """

    name: str
    is_method: bool
    positional: tuple[str | None, ...]
    keywords: tuple[tuple[str, str | None], ...]


@final
@dataclass(frozen=True, slots=True)
class StructuralUsage:
    """Everything a function requires of one parameter.

    Attributes:
        members: Required members sorted by name.

    """

    members: tuple[Member, ...]


@final
@dataclass(slots=True)
class _Draft:
    """Accumulate the uses of one attribute.

    Attributes:
        calls: Call shapes seen: positional types and keyword types.

    """

    calls: list[
        tuple[tuple[str | None, ...], tuple[tuple[str, str | None], ...]]
    ]


def parameter_has_default(*, function: Function, parameter: ast.arg) -> bool:
    """Tell whether a parameter has a default value.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter to look up.

    Returns:
        ``True`` when the parameter has a default.

    """
    arguments: ast.arguments = function.args
    positional: list[ast.arg] = [*arguments.posonlyargs, *arguments.args]
    if parameter in positional:
        offset: int = len(positional) - len(arguments.defaults)
        return positional.index(parameter) >= offset
    if parameter in arguments.kwonlyargs:
        index: int = arguments.kwonlyargs.index(parameter)
        return arguments.kw_defaults[index] is not None
    return False


def _walk(*, function: Function) -> Iterator[ast.AST]:
    """Yield every node of a function body.

    Args:
        function: Function whose body is walked.

    Yields:
        Each node, statements first.

    """
    for statement in function.body:
        yield from ast.walk(node=statement)


def names_bound_by(*, node: ast.AST) -> tuple[str, ...]:
    """List the names a node binds, rebinds or deletes.

    Args:
        node: Node to inspect.

    Returns:
        The names it introduces, possibly none.

    """
    names: tuple[str, ...] = ()
    match node:
        case (
            ast.Name(id=found, ctx=ast.Store() | ast.Del())
            | ast.arg(arg=found)
        ):
            names = (found,)
        case ast.Global(names=listed) | ast.Nonlocal(names=listed):
            names = tuple(listed)
        case ast.alias(name=found, asname=asname):
            names = (asname or found.split(sep=".")[0],)
        case (
            ast.ExceptHandler(name=found)
            | ast.FunctionDef(name=found)
            | ast.AsyncFunctionDef(name=found)
            | ast.ClassDef(name=found)
            | ast.MatchAs(name=found)
            | ast.MatchStar(name=found)
            | ast.MatchMapping(rest=found)
        ) if found is not None:
            names = (found,)
        case _:
            pass
    return names


def _call_shape(
    *,
    call: ast.Call,
    counts: Mapping[str, int],
) -> tuple[tuple[str | None, ...], tuple[tuple[str, str | None], ...]] | None:
    """Describe the arguments of a call to a member.

    Args:
        call: Call expression.
        counts: Module binding counts, for typing arguments.

    Returns:
        Positional and keyword types, or ``None`` for star arguments.

    """
    if any(isinstance(item, ast.Starred) for item in call.args):
        return None
    if any(item.arg is None for item in call.keywords):
        return None
    if any(
        item.arg == Constants.receiver
        or Constants.generated_name.fullmatch(string=item.arg or "")
        for item in call.keywords
    ):
        return None
    positional: tuple[str | None, ...] = tuple(
        expression_type(node=item, counts=counts) for item in call.args
    )
    keywords: tuple[tuple[str, str | None], ...] = tuple(
        sorted(
            (item.arg, expression_type(node=item.value, counts=counts))
            for item in call.keywords
            if item.arg is not None
        ),
    )
    return (positional, keywords)


def _same(*, values: list[str | None]) -> bool:
    """Tell whether every value equals the first.

    Args:
        values: Non-empty list of annotations.

    Returns:
        ``True`` when all values agree.

    """
    return all(value == values[0] for value in values)


def _merge(*, name: str, draft: _Draft) -> Member | None:
    """Combine every call of one attribute into a member.

    Args:
        name: Attribute name.
        draft: Calls seen for the attribute.

    Returns:
        The member, or ``None`` when the calls disagree on their shape.

    """
    if not draft.calls:
        return Member(name=name, is_method=False, positional=(), keywords=())
    first_positional, first_keywords = draft.calls[0]
    shape = (len(first_positional), [key for key, _ in first_keywords])
    for positional, keywords in draft.calls:
        if (len(positional), [key for key, _ in keywords]) != shape:
            return None
    merged_positional: tuple[str | None, ...] = tuple(
        first_positional[index]
        if _same(values=[call[0][index] for call in draft.calls])
        else None
        for index in range(len(first_positional))
    )
    merged_keywords: tuple[tuple[str, str | None], ...] = tuple(
        (
            (
                key,
                first_keywords[index][1]
                if _same(values=[call[1][index][1] for call in draft.calls])
                else None,
            )
            for index, (key, _) in enumerate(iterable=first_keywords)
        ),
    )
    return Member(
        name=name,
        is_method=True,
        positional=merged_positional,
        keywords=merged_keywords,
    )


def _collect(
    *,
    nodes: list[ast.AST],
    parents: Mapping[ast.AST, ast.AST],
    parameter: str,
    counts: Mapping[str, int],
) -> dict[str, _Draft] | None:
    """Gather the attribute uses of a parameter.

    Args:
        nodes: Every node of the function body.
        parents: Parent of every node.
        parameter: Parameter name.
        counts: Module binding counts.

    Returns:
        Uses per attribute, or ``None`` when any use is not structural.

    """
    drafts: dict[str, _Draft] = {}
    for node in nodes:
        if not (isinstance(node, ast.Name) and node.id == parameter):
            continue
        attribute: ast.AST | None = parents.get(node)
        if not (
            isinstance(attribute, ast.Attribute)
            and attribute.value is node
            and isinstance(attribute.ctx, ast.Load)
            and (not attribute.attr.startswith(Constants.private_prefix))
        ):
            return None
        draft: _Draft = drafts.setdefault(attribute.attr, _Draft(calls=[]))
        parent: ast.AST | None = parents.get(attribute)
        if isinstance(parent, ast.Await):
            return None
        if isinstance(parent, ast.Call) and parent.func is attribute:
            shape = _call_shape(call=parent, counts=counts)
            if shape is None or isinstance(parents.get(parent), ast.Await):
                return None
            draft.calls.append(shape)
    return drafts


def structural_usage(
    *,
    function: Function,
    parameter: str,
    counts: Mapping[str, int],
) -> StructuralUsage | None:
    """Prove that a parameter is only used through its attributes.

    Args:
        function: Function that owns the parameter.
        parameter: Parameter name.
        counts: Module binding counts, for typing call arguments.

    Returns:
        The required members, or ``None`` when the parameter is rebound, used
        as a plain value, written to, awaited through, or unused.

    """
    nodes: list[ast.AST] = list(_walk(function=function))
    if any(parameter in names_bound_by(node=node) for node in nodes):
        return None
    parents: dict[ast.AST, ast.AST] = {
        child: parent
        for parent in nodes
        for child in ast.iter_child_nodes(node=parent)
    }
    drafts: dict[str, _Draft] | None = _collect(
        nodes=nodes,
        parents=parents,
        parameter=parameter,
        counts=counts,
    )
    if drafts is None:
        return None
    members: list[Member] = []
    for name in sorted(drafts):
        member: Member | None = _merge(name=name, draft=drafts[name])
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
    if not member.is_method:
        return f"""\
{pad}@property
{pad}def {member.name}(self): ...
"""
    parameters: list[str] = ["self"]
    parameters.extend(
        (
            _annotated(name=(f"arg{index}"), annotation=annotation)
            for index, annotation in enumerate(iterable=member.positional)
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
    return f"""\
{pad}def {member.name}({", ".join(parameters)}): ...
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
