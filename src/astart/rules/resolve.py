"""Shared name-binding and call-resolution helpers for rules and hints."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Del,
    ExceptHandler,
    FunctionDef,
    ImportFrom,
    MatchAs,
    MatchMapping,
    MatchStar,
    Module,
    Name,
    Store,
    alias,
    arg,
    expr,
    walk,
)
from typing import TYPE_CHECKING, final

from astart.rules.imports import Constants as ImportConstants
from astart.rules.methods import MethodIndex, dataclass_init_names

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import BoundCall, CommentedModule


def _class_level_ids(*, module: Module) -> frozenset[int]:
    """Collect nodes that bind names directly in a class body.

    Args:
        module: Parsed module.

    Returns:
        Identities of the defining nodes and target names.

    """
    ids: set[int] = set()
    for node in walk(node=module):
        if not isinstance(node, ClassDef):
            continue
        for statement in node.body:
            ids.add(id(statement))
            match statement:
                case Assign(targets=targets):
                    ids.update(id(target) for target in targets)
                case AnnAssign(target=target):
                    ids.add(id(target))
                case _:
                    continue
    return frozenset(ids)


def _bound_name(*, node: AST) -> str | None:
    """Name the identifier a node binds, if it binds one.

    Args:
        node: Any syntax node.

    Returns:
        The bound name, or ``None``.

    """
    match node:
        case Name(id=name, ctx=Store() | Del()):
            return name
        case (
            FunctionDef(name=name)
            | AsyncFunctionDef(name=name)
            | ClassDef(name=name)
            | ExceptHandler(name=name)
            | MatchAs(name=name)
            | MatchStar(name=name)
        ):
            return name
        case arg(arg=name) | MatchMapping(rest=name):
            return name
        case alias(name=name, asname=asname):
            return asname or name.split(sep=".")[0]
        case _:
            return None


def binding_counts(*, module: Module) -> dict[str, int]:
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
    for node in walk(node=module):
        name: str | None = (
            None if id(node) in skipped else _bound_name(node=node)
        )
        if name:
            counts[name] = counts.get(name, 0) + 1
    for node in walk(node=module):
        if isinstance(node, ImportFrom) and node.level == 0:
            for alias in node.names:
                if (
                    alias.asname is None
                    and alias.name in ImportConstants.constructors
                    and ImportConstants.known_imports[alias.name]
                    == node.module
                    and counts.get(alias.name) == 1
                ):
                    counts[constructor_key(name=alias.name)] = 1
    return counts


def constructor_key(*, name: str) -> str:
    """Name the binding-count entry that marks an imported constructor.

    The key contains a character no identifier can, so it never collides with
    a bound name.

    Args:
        name: Imported class name.

    Returns:
        The key under which ``binding_counts`` records the constructor.

    """
    return f"@constructor:{name}"


def root_name(*, node: expr) -> str | None:
    """Find the leftmost name of a callee expression.

    Args:
        node: Callee expression.

    Returns:
        The name, or ``None`` when the callee is not a name path.

    """
    while isinstance(node, Attribute):
        node = node.value
    return node.id if isinstance(node, Name) else None


def definition_is_plain(*, declaration: AST) -> bool:
    """Report whether a definition keeps the signature it declares.

    Args:
        declaration: Function or class definition.

    Returns:
        Whether it has no decorator that could rewrite its signature.

    """
    match declaration:
        case FunctionDef() | AsyncFunctionDef():
            return all(
                isinstance(decorator, Name)
                and decorator.id in {"staticmethod", "classmethod"}
                for decorator in declaration.decorator_list
            )
        case ClassDef():
            return not declaration.decorator_list
        case _:
            return False


def trusted_binding(
    *,
    bound: BoundCall | None,
    call: Call,
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
    declaration: AST | None = bound.signature.declaration
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

    def get(self, *, call: Call) -> BoundCall | None:
        """Return the trusted binding of a call.

        Args:
            call: Call expression of the module.

        Returns:
            The binding, or ``None``.

        """
        if self._cache is None:
            calls: list[Call] = [
                node
                for node in walk(node=self._module)
                if isinstance(node, Call)
            ]
            methods: MethodIndex = MethodIndex(
                module=self._module,
                counts=self._counts,
            )
            self._cache = {
                id(item): _vet(
                    item=item,
                    bound=bound,
                    methods=methods,
                    counts=self._counts,
                )
                for item, bound in zip(
                    calls,
                    self._module.bind_calls(nodes=calls),
                    strict=True,
                )
            }
        return self._cache.get(id(call))


def _is_plain_dataclass_call(
    *,
    item: Call,
    bound: BoundCall | None,
    counts: Mapping[str, int],
) -> bool:
    """Tell whether a call builds a simple dataclass the analyzer bound.

    Args:
        item: Call expression.
        bound: Binding reported by the analyzer, if any.
        counts: Binding counts from :func:`binding_counts`.

    Returns:
        ``True`` when the callee is a module-level name bound once to a
        dataclass whose generated parameters match the analyzer's.

    """
    if (
        bound is None
        or bound.signature.source_path is not None
        or not isinstance(item.func, Name)
        or counts.get(item.func.id) != 1
    ):
        return False
    declaration: AST | None = bound.signature.declaration
    if not isinstance(declaration, ClassDef):
        return False
    expected: list[str] | None = dataclass_init_names(cls=declaration)
    return expected is not None and expected == [
        parameter.name for parameter in bound.signature.parameters
    ]


def _vet(
    *,
    item: Call,
    bound: BoundCall | None,
    methods: MethodIndex,
    counts: Mapping[str, int],
) -> BoundCall | None:
    """Decide which binding of one call to trust.

    Args:
        item: Call expression.
        bound: Binding reported by the analyzer, if any.
        methods: Method facts of the module.
        counts: Binding counts from :func:`binding_counts`.

    Returns:
        The trusted binding, or ``None``.

    """
    if not methods.callee_allowed(call=item):
        return None
    trusted: BoundCall | None = trusted_binding(
        bound=bound,
        call=item,
        counts=counts,
    )
    if trusted is None and _is_plain_dataclass_call(
        item=item,
        bound=bound,
        counts=counts,
    ):
        return bound
    if not isinstance(item.func, Attribute):
        return trusted
    if (
        trusted is None
        and bound is not None
        and bound.signature.source_path is None
        and bound.signature.declaration is not None
        and methods.constructed_receiver(call=item)
        and definition_is_plain(declaration=bound.signature.declaration)
    ):
        trusted = bound
    if trusted is not None:
        declaration: AST | None = trusted.signature.declaration
        if declaration is not None and not methods.is_safe(
            call=item,
            declaration=declaration,
        ):
            return None
        return trusted
    return methods.bind_self_call(call=item)


def resolved_call(
    *,
    module: CommentedModule,
    counts: Mapping[str, int],
    call: Call,
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
