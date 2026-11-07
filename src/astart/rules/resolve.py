"""Shared name-binding and call-resolution helpers for rules and hints."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import BoundCall, CommentedModule


def _class_level_ids(*, module: ast.Module) -> frozenset[int]:
    """Collect nodes that bind names directly in a class body.

    Args:
        module: Parsed module.

    Returns:
        Identities of the defining nodes and target names.

    """
    ids: set[int] = set()
    for node in ast.walk(node=module):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            ids.add(id(statement))
            match statement:
                case ast.Assign(targets=targets):
                    ids.update(id(target) for target in targets)
                case ast.AnnAssign(target=target):
                    ids.add(id(target))
                case _:
                    continue
    return frozenset(ids)


def _bound_name(*, node: ast.AST) -> str | None:
    """Name the identifier a node binds, if it binds one.

    Args:
        node: Any syntax node.

    Returns:
        The bound name, or ``None``.

    """
    match node:
        case ast.Name(id=name, ctx=ast.Store() | ast.Del()):
            return name
        case (
            ast.FunctionDef(name=name)
            | ast.AsyncFunctionDef(name=name)
            | ast.ClassDef(name=name)
            | ast.ExceptHandler(name=name)
            | ast.MatchAs(name=name)
            | ast.MatchStar(name=name)
        ):
            return name
        case ast.arg(arg=name) | ast.MatchMapping(rest=name):
            return name
        case ast.alias(name=name, asname=asname):
            return asname or name.split(sep=".")[0]
        case _:
            return None


def binding_counts(*, module: ast.Module) -> dict[str, int]:
    """Count how often each name is bound anywhere in the module.

    Names bound directly in class bodies are ignored, because they do not
    shadow module-level names.

    Args:
        module: Parsed module.

    Returns:
        Binding counts by name.

    """
    skipped: frozenset[int] = _class_level_ids(module=module)
    counts: dict[str, int] = {}
    for node in ast.walk(node=module):
        name: str | None = (
            None if id(node) in skipped else _bound_name(node=node)
        )
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts


def root_name(*, node: ast.expr) -> str | None:
    """Find the leftmost name of a callee expression.

    Args:
        node: Callee expression.

    Returns:
        The name, or ``None`` when the callee is not a name path.

    """
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def definition_is_plain(*, declaration: ast.AST) -> bool:
    """Report whether a definition keeps the signature it declares.

    Args:
        declaration: Function or class definition.

    Returns:
        Whether it has no decorator that could rewrite its signature.

    """
    match declaration:
        case ast.FunctionDef() | ast.AsyncFunctionDef():
            return all(
                isinstance(decorator, ast.Name)
                and decorator.id in {"staticmethod", "classmethod"}
                for decorator in declaration.decorator_list
            )
        case ast.ClassDef():
            return not declaration.decorator_list
        case _:
            return False


def trusted_binding(
    *,
    bound: BoundCall | None,
    call: ast.Call,
    counts: Mapping[str, int],
) -> BoundCall | None:
    """Keep a binding only when the callee can be trusted.

    The callee's root name must be bound exactly once in the module and the
    definition must have no decorator that could change its signature.

    Args:
        bound: Binding reported by the semantic analyzer.
        call: Call expression.
        counts: Binding counts from :func:`binding_counts`.

    Returns:
        The binding, or ``None`` when the callee cannot be trusted.

    """
    if bound is None or bound.signature.source_path is not None:
        return None
    root: str | None = root_name(node=call.func)
    if root is None or counts.get(root, 0) != 1:
        return None
    declaration: ast.AST | None = bound.signature.declaration
    if declaration is not None and definition_is_plain(
        declaration=declaration,
    ):
        return bound
    return None


@final
class CallBindings:
    """Trusted call bindings of one module, computed in a single batch.

    Binding calls one at a time re-checks the whole tree every time; this
    binds every call of the module once, on first use, and answers from the
    cache. The cache describes the tree as it was at that moment.
    """

    def __init__(
        self,
        *,
        module: CommentedModule,
        counts: Mapping[str, int],
    ) -> None:
        """Remember the module; nothing is computed yet.

        Args:
            module: Parsed module.
            counts: Binding counts from :func:`binding_counts`.

        """
        self._module: CommentedModule = module
        self._counts: Mapping[str, int] = counts
        self._cache: dict[int, BoundCall | None] | None = None

    def get(self, *, call: ast.Call) -> BoundCall | None:
        """Return the trusted binding of a call.

        Args:
            call: Call expression of the module.

        Returns:
            The binding, or ``None``.

        """
        if self._cache is None:
            calls: list[ast.Call] = [
                node
                for node in ast.walk(node=self._module)
                if isinstance(node, ast.Call)
            ]
            self._cache = {
                id(item): trusted_binding(
                    bound=bound,
                    call=item,
                    counts=self._counts,
                )
                for item, bound in zip(
                    calls,
                    self._module.bind_calls(nodes=calls),
                    strict=True,
                )
            }
        return self._cache.get(id(call))


def resolved_call(
    *,
    module: CommentedModule,
    counts: Mapping[str, int],
    call: ast.Call,
) -> BoundCall | None:
    """Bind one call to a definition in this module, conservatively.

    Prefer :class:`CallBindings` when binding many calls.

    Args:
        module: Parsed module.
        counts: Binding counts from :func:`binding_counts`.
        call: Call expression.

    Returns:
        The bound call, or ``None`` when the callee cannot be trusted.

    """
    return trusted_binding(
        bound=module.bind_call(node=call),
        call=call,
        counts=counts,
    )
