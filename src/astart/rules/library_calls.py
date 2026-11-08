"""Bind calls to curated library signatures from ``libkw``.

``libkw.SIGNATURES`` is a typeshed-generated table of callees whose
parameters may be passed by keyword.  This module resolves a call's
callee to a ``module.qualname`` key — through the module's own import
aliases or the ``builtins`` fallback — and synthesizes a ``BoundCall``
so ``calls.add-keywords`` can rewrite positional arguments.

Only syntactically certain bindings are produced: ``*args``/``**kwargs``
expansions, attribute chains on non-imported roots, shadowed import
roots and already-keyworded duplicates all refuse.
"""

from __future__ import annotations

from ast import AST, Attribute, Call, Import, ImportFrom, Name, expr
from typing import TYPE_CHECKING

from astart.rules.libkw import SIGNATURES, KwSignature
from astart.semantic import (
    ArgumentOrigin,
    BoundArgument,
    BoundCall,
    CallableContract,
    ParameterContract,
    ParameterKind,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import CommentedModule


def _aliases(*, module: CommentedModule) -> dict[str, str]:
    """Map top-level bound names to the dotted name they refer to.

    Args:
        module: Parsed module.

    Returns:
        Bound name to dotted prefix (``import a.b as ab`` → ``ab: a.b``;
        ``from a import b`` → ``b: a.b``; plain ``import a.b`` → ``a: a``).

    """
    aliases: dict[str, str] = {}
    for node in module.body:
        if isinstance(node, Import):
            for item in node.names:
                aliases[item.asname or item.name.partition(".")[0]] = (
                    item.name if item.asname else item.name.partition(".")[0]
                )
        elif (
            isinstance(node, ImportFrom)
            and node.level == 0
            and node.module is not None
        ):
            for item in node.names:
                if item.name != "*":
                    aliases[item.asname or item.name] = (
                        f"{node.module}.{item.name}"
                    )
    return aliases


def _callee_key(
    *,
    call: Call,
    aliases: Mapping[str, str],
) -> tuple[str, str] | None:
    """Resolve a call's function to a ``(key, root)`` pair.

    Args:
        call: Call expression.
        aliases: Import aliases of the module.

    Returns:
        The ``SIGNATURES`` lookup key and the root bound name, or
        ``None`` when the callee is not a plain name or module attribute.

    """
    parts: list[str] = []
    node: AST = call.func
    while isinstance(node, Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, Name):
        return None
    root: str = node.id
    prefix: str | None = aliases.get(root)
    if prefix is not None:
        return ".".join((prefix, *reversed(parts))), root
    if parts:
        return None
    return f"builtins.{root}", root


def callee_name(
    *,
    module: CommentedModule,
    counts: Mapping[str, int],
    call: Call,
) -> str | None:
    """Name the library function a call refers to, if it is certain.

    Args:
        module: Parsed module.
        counts: Binding counts from :func:`binding_counts`.
        call: Call expression.

    Returns:
        A dotted name such as ``os.getcwd`` or ``builtins.len``; ``None``
        when the callee is not a plain imported name or unshadowed builtin.

    """
    aliases: dict[str, str] = _aliases(module=module)
    resolved: tuple[str, str] | None = _callee_key(call=call, aliases=aliases)
    if resolved is None:
        return None
    key, root = resolved
    limit: int = 1 if root in aliases else 0
    return key if counts.get(root, 0) <= limit else None


def _trusted(
    *,
    signature: KwSignature | None,
    call: Call,
    counts: Mapping[str, int],
    aliases: Mapping[str, str],
    root: str,
) -> bool:
    """Answer whether the resolved callee may be keyworded safely.

    Args:
        signature: Table entry for the callee.
        call: Call expression.
        counts: Binding counts from :func:`binding_counts`.
        aliases: Import aliases of the module.
        root: Root bound name of the callee.

    Returns:
        ``False`` for shadowed roots, ``**`` expansions, duplicate
        keywords, or positionals beyond the known signature.

    """
    if signature is None:
        return False
    if any(keyword.arg is None for keyword in call.keywords):
        return False
    bound_count: int = counts.get(root, 0)
    if root in aliases:
        if bound_count > 1:
            return False
    elif bound_count > 0:
        return False
    if len(call.args) > len(signature.positional) and (
        not signature.var_positional
    ):
        return False
    present: frozenset[str] = frozenset(
        keyword.arg for keyword in call.keywords if keyword.arg is not None
    )
    keywordable: frozenset[str] = frozenset(signature.names)
    return not any(
        index < len(signature.positional)
        and signature.positional[index] in keywordable
        and signature.positional[index] in present
        for index in range(len(call.args))
    )


def _argument(
    *,
    signature: KwSignature,
    index: int,
    value: expr,
) -> BoundArgument:
    """Bind one positional argument to its signature parameter.

    Args:
        signature: Table entry for the callee.
        index: Positional index of the argument.
        value: Argument expression.

    Returns:
        The bound argument with positional or variadic origin.

    """
    if index < len(signature.positional):
        name: str = signature.positional[index]
        kind: ParameterKind = (
            ParameterKind.POSITIONAL_OR_KEYWORD
            if name in signature.names
            else ParameterKind.POSITIONAL_ONLY
        )
        origin: ArgumentOrigin = ArgumentOrigin.POSITIONAL
    else:
        name = "args"
        kind = ParameterKind.VAR_POSITIONAL
        origin = ArgumentOrigin.VAR_POSITIONAL
    return BoundArgument(
        parameter=ParameterContract(name=name, kind=kind),
        origin=origin,
        values=(value,),
        types=(),
    )


def _has_inner_comment(*, module: CommentedModule, call: Call) -> bool:
    """Answer whether a comment sits inside the call's line span.

    Args:
        module: Parsed module carrying lexical comments.
        call: Call expression about to be rewritten.

    Returns:
        ``True`` when rewriting arguments could disturb a comment.

    """
    return any(
        comment.lineno >= call.lineno
        and comment.end_lineno <= (call.end_lineno or call.lineno)
        for comment in module.comments
    )


def library_binding(
    *,
    module: CommentedModule,
    call: Call,
    counts: Mapping[str, int],
) -> BoundCall | None:
    """Bind a call to a ``libkw`` signature when it is provably safe.

    Args:
        module: Parsed module the call lives in.
        call: Call expression.
        counts: Binding counts from :func:`binding_counts`.

    Returns:
        A synthetic binding, or ``None`` when the callee is unknown,
        shadowed, expanded, or would bind past the known signature.

    """
    aliases: dict[str, str] = _aliases(module=module)
    resolved: tuple[str, str] | None = _callee_key(call=call, aliases=aliases)
    if resolved is None:
        return None
    key, root = resolved
    signature: KwSignature | None = SIGNATURES.get(key)
    if signature is None or _has_inner_comment(module=module, call=call):
        return None
    if not _trusted(
        signature=signature,
        call=call,
        counts=counts,
        aliases=aliases,
        root=root,
    ):
        return None
    bound: list[BoundArgument] = [
        _argument(signature=signature, index=index, value=value)
        for index, value in enumerate(iterable=call.args)
    ]
    parameters: list[ParameterContract] = [item.parameter for item in bound]
    parameters.extend(
        ParameterContract(name=name, kind=ParameterKind.KEYWORD_ONLY)
        for name in signature.names
        if name not in signature.positional
    )
    return BoundCall(
        call=call,
        signature=CallableContract(
            qualified_name=key,
            parameters=tuple(parameters),
            method_kind="function",
        ),
        arguments=tuple(bound),
    )
