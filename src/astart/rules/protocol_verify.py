"""Check a synthesized Protocol against the arguments callers really pass.

A Protocol built from how a function *uses* a parameter is only worth writing
if the module's own callers can satisfy it. This module looks at every direct
call of the function and reports the first argument whose type is provable
and provably lacks a required member: a builtin value (``"abc"`` has no
``read``), ``None``, or an instance of a plain class defined in the module.
Anything it cannot decide counts as no objection.
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    FunctionDef,
    Name,
    walk,
)
from typing import TYPE_CHECKING, Final, final

from astart.rules.provable import expression_type, module_constants
from astart.semantic import ArgumentOrigin, BoundCall

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType

    from astart.rules.facts import ModuleFacts

    type Function = FunctionDef | AsyncFunctionDef


@final
class Constants:
    """Group module-level constants.

    Attributes:
        passed: Argument origins that carry a caller's value.
        dynamic: Class members that make attribute lookup unpredictable.

    """

    passed: Final[frozenset[ArgumentOrigin]] = frozenset(
        {ArgumentOrigin.POSITIONAL, ArgumentOrigin.KEYWORD},
    )
    dynamic: Final[frozenset[str]] = frozenset(
        {"__getattr__", "__getattribute__"},
    )


def _builtin_type(*, text: str) -> type | None:
    """Resolve a proven annotation like ``list[int]`` to its builtin class.

    Args:
        text: Annotation source from the typer.

    Returns:
        The class, or ``None`` when it is not a builtin type.

    """
    module: ModuleType = __import__("builtins")
    name: str = text.split(sep="[", maxsplit=1)[0]
    return (
        module.__dict__[name]
        if isinstance(module.__dict__.get(name), type)
        else None
    )


def _class_members(*, cls: ClassDef) -> set[str] | None:
    """Collect every name an instance of a plain class can have.

    Args:
        cls: Class definition.

    Returns:
        The member names, or ``None`` when inheritance, decorators or dynamic
        lookup make the set unknowable.

    """
    if cls.bases or cls.keywords or cls.decorator_list:
        return None
    names: set[str] = set()
    for node in walk(node=cls):
        match node:
            case FunctionDef(name=found) | AsyncFunctionDef(name=found):
                names.add(found)
            case ClassDef(name=found) if node is not cls:
                names.add(found)
            case Name(id=found, ctx=ctx) if type(ctx).__name__ == "Store":
                names.add(found)
            case Attribute(attr=found, ctx=ctx) if (
                type(ctx).__name__ == "Store"
            ):
                names.add(found)
            case _:
                continue
    return None if names & Constants.dynamic else names


def _lacks(
    *,
    value: AST,
    members: Iterable[str],
    facts: ModuleFacts,
) -> str | None:
    """Name a required member the argument provably lacks.

    Args:
        value: The argument expression.
        members: Members the Protocol would require.
        facts: Resolved imports and the parsed module.

    Returns:
        The missing member, or ``None`` when nothing is provable.

    """
    required: list[str] = list(members)
    if isinstance(value, Constant) and value.value is None:
        known: set[str] | None = set(dir(type(None)))
    elif (
        isinstance(value, Call)
        and isinstance(value.func, Name)
        and facts.binding_counts.get(value.func.id) == 1
    ):
        cls: ClassDef | None = next(
            (
                item
                for item in facts.module.body
                if isinstance(item, ClassDef) and item.name == value.func.id
            ),
            None,
        )
        found: set[str] | None = (
            None if cls is None else _class_members(cls=cls)
        )
        known = None if found is None else found | set(dir(object))
    else:
        text: str | None = expression_type(
            node=value,
            counts=facts.binding_counts,
            env=module_constants(
                module=facts.module,
                counts=facts.binding_counts,
            ),
        )
        kind: type | None = None if text is None else _builtin_type(text=text)
        known = None if kind is None else set(dir(kind))
    if known is None:
        return None
    return next((name for name in required if name not in known), None)


def call_site_objection(
    *,
    function: Function,
    parameter: str,
    members: Iterable[str],
    facts: ModuleFacts,
) -> str | None:
    """Find a caller whose argument cannot satisfy the required members.

    Args:
        function: The function that owns the parameter.
        parameter: Parameter name.
        members: Members the Protocol would require.
        facts: Resolved imports and the parsed module.

    Returns:
        A short description of the first objection, or ``None``.

    """
    if facts.calls is None:
        return None
    required: list[str] = list(members)
    for node in walk(node=facts.module):
        if not isinstance(node, Call):
            continue
        bound: BoundCall | None = facts.calls.get(call=node)
        if bound is None or bound.signature.declaration is not function:
            continue
        for argument in bound.arguments:
            if (
                argument.parameter.name != parameter
                or argument.origin not in Constants.passed
            ):
                continue
            for value in argument.values:
                missing: str | None = _lacks(
                    value=value,
                    members=required,
                    facts=facts,
                )
                if missing is not None:
                    return f"line {node.lineno}: argument lacks {missing!r}"
    return None
