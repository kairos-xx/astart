"""IMP001 fixer: rewrite ``import a`` attribute uses into ``from`` imports.

``rewrite_bare_imports`` converts module-level ``import a[.b...]``
statements whose attribute uses are all safe loads into per-attribute
``from`` imports plus rewritten use sites.  Each attribute is decided
independently: unsafe sites keep ``import a`` alive for them.

Standalone module — catalog/applier wiring is deferred (M8-22).
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    FunctionDef,
    Global,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Nonlocal,
    Store,
    alias,
    arg,
    expr,
    iter_fields,
    stmt,
    walk,
)
from dataclasses import dataclass
from typing import cast, final


@final
@dataclass(frozen=True, slots=True)
class ImportRewrite:
    """One import statement's conversion outcome.

    Attributes:
        module: Dotted module the ``from`` import targets.
        converted: Attributes rewritten to ``from``-imported names.
        kept: Attributes left untouched.
        complete: Whether the ``import`` statement was fully removed.

    """

    module: str
    converted: tuple[str, ...]
    kept: tuple[str, ...]
    complete: bool


@final
class _Parent:
    """Where a node sits inside its parent for replacement."""

    __slots__ = ("field", "index", "node")

    def __init__(self, *, node: AST, field: str, index: int | None) -> None:
        """Record the parent position of one child node.

        Args:
            node: Parent node.
            field: Attribute or list field holding the child.
            index: Position inside a list field, or ``None``.

        """
        self.node: AST = node
        self.field: str = field
        self.index: int | None = index


def _parents(*, module: Module) -> dict[int, _Parent]:
    """Map every child node id to its parent field position.

    Args:
        module: Parsed module.

    Returns:
        Node id to parent record.

    """
    result: dict[int, _Parent] = {}
    for node in walk(node=module):
        for field, value in iter_fields(node=node):
            if isinstance(value, AST):
                result[id(value)] = _Parent(node=node, field=field, index=None)
            elif isinstance(value, list):
                for position, item in enumerate(
                    iterable=cast(typ="list[object]", val=value),
                ):
                    if isinstance(item, AST):
                        result[id(item)] = _Parent(
                            node=node,
                            field=field,
                            index=position,
                        )
    return result


def _bindings(*, module: Module) -> set[str]:
    """Collect every name bound anywhere in the module.

    Args:
        module: Parsed module.

    Returns:
        Bound names.

    """
    names: set[str] = set()
    for node in walk(node=module):
        if isinstance(node, Name) and isinstance(node.ctx, Store):
            names.add(node.id)
        elif isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            names.add(node.name)
        elif isinstance(node, (arg,)):
            names.add(node.arg)
        elif isinstance(node, Import):
            for entry in node.names:
                names.add(
                    entry.asname
                    if entry.asname is not None
                    else entry.name.split(sep=".", maxsplit=1)[0],
                )
        elif isinstance(node, ImportFrom):
            for entry in node.names:
                names.add(
                    entry.asname if entry.asname is not None else entry.name,
                )
        elif isinstance(node, (Global, Nonlocal)):
            names.update(node.names)
    return names


def _existing_from(*, module: Module) -> dict[tuple[str, str], str]:
    """Map ``(module, imported)`` to the already-bound local name.

    Args:
        module: Parsed module.

    Returns:
        Existing ``from`` import bindings at module top level.

    """
    result: dict[tuple[str, str], str] = {}
    for statement in module.body:
        if isinstance(statement, ImportFrom) and statement.module:
            for entry in statement.names:
                result[(statement.module, entry.name)] = (
                    entry.asname or entry.name
                )
    return result


@final
class _Chain:
    """Attribute chain below one bound name, with nodes per depth."""

    __slots__ = ("depths", "names")

    def __init__(self) -> None:
        """Start an empty attribute chain."""
        self.names: tuple[str, ...] = ()
        self.depths: tuple[Attribute, ...] = ()


def _chains(
    *,
    module: Module,
    root: str,
) -> tuple[dict[int, _Chain], set[int]]:
    """Longest attribute chain per ``root`` Name node.

    Args:
        module: Parsed module.
        root: Bound name to collect chains for.

    Returns:
        Base node id to chain, plus ids of attribute-less uses.

    """
    chains: dict[int, _Chain] = {}
    bases: set[int] = set()
    for node in walk(node=module):
        if not isinstance(node, Attribute):
            continue
        names: list[str] = []
        depths: list[Attribute] = []
        cursor: expr = node
        while isinstance(cursor, Attribute):
            names.append(cursor.attr)
            depths.append(cursor)
            cursor = cursor.value
        if not (isinstance(cursor, Name) and cursor.id == root):
            continue
        base: int = id(cursor)
        bases.add(base)
        chain: _Chain = _Chain()
        chain.names = tuple(reversed(names))
        chain.depths = tuple(reversed(depths))
        if len(chain.names) > len(chains.get(base, _Chain()).names):
            chains[base] = chain
    bare: set[int] = {
        id(node)
        for node in walk(node=module)
        if isinstance(node, Name) and node.id == root and id(node) not in bases
    }
    return chains, bare


def _replace_node(
    *,
    parents: dict[int, _Parent],
    old: AST,
    new: AST,
) -> None:
    """Swap ``old`` for ``new`` inside its parent.

    Args:
        new: Replacement node.
        old: Node to replace.
        parents: Parent map from :func:`_parents`.

    """
    record: _Parent | None = parents.get(id(old))
    if record is None:
        return
    parent: AST = record.node
    if record.index is None:
        setattr(parent, record.field, new)
    else:
        value: AST | list[AST] = getattr(parent, record.field)
        if isinstance(value, list):
            items: list[AST] = value
            items[record.index] = new


def _local_name(
    *,
    attr: str,
    module_name: str,
    existing: dict[tuple[str, str], str],
    bindings: set[str],
) -> str | None:
    """Bound name for ``attr``, or ``None`` when it would collide.

    Args:
        attr: Attribute name to import.
        bindings: Every name already bound in the module.
        existing: Existing ``from`` import bindings.
        module_name: Dotted module being imported from.

    Returns:
        Local name to use, or ``None`` to skip this attribute.

    """
    bound: str | None = existing.get((module_name, attr))
    if bound is not None:
        return bound
    return None if attr in bindings else attr


@final
@dataclass(slots=True)
class _AttrPlan:
    """Per-attribute conversion plan for one import statement.

    Attributes:
        converted: Attributes that will be imported by name.
        rewrites: ``(attribute node, local name)`` use-site swaps.
        imports_needed: ``attr -> local name`` for the ``from`` import.
        unsafe_attrs: Attributes that keep ``import a`` alive.
        kept: Dotted names that must stay imported.

    """

    converted: list[str]
    rewrites: list[tuple[Attribute, str]]
    imports_needed: dict[str, str]
    unsafe_attrs: set[str]
    kept: list[str]


def _attribute_plan(
    *,
    chains: dict[int, _Chain],
    prefix: tuple[str, ...],
    entry_name: str,
    existing: dict[tuple[str, str], str],
    bindings: set[str],
) -> _AttrPlan:
    """Decide which attributes convert and which keep the import.

    Args:
        chains: Attribute chains below the imported root name.
        prefix: Dotted path already covered by the import.
        entry_name: Full dotted module name of the import.
        existing: Existing ``from`` bindings, ``(module, name) -> local``.
        bindings: Names bound in the module.

    Returns:
        The conversion plan.

    """
    uses_by_attr: dict[str, list[tuple[_Chain, Attribute]]] = {}
    kept: list[str] = []
    for chain in chains.values():
        if len(chain.names) <= len(prefix):
            # Bare module use, e.g. ``a.c`` for ``import a.c``.
            kept.append(entry_name)
            continue
        attr: str = chain.names[len(prefix)]
        target: Attribute = chain.depths[len(prefix)]
        uses_by_attr.setdefault(attr, []).append((chain, target))
    converted: list[str] = []
    rewrites: list[tuple[Attribute, str]] = []
    imports_needed: dict[str, str] = {}
    unsafe_attrs: set[str] = set()
    for attr, uses in uses_by_attr.items():
        local: str | None = _local_name(
            attr=attr,
            module_name=entry_name,
            existing=existing,
            bindings=bindings,
        )
        if local is None or any(
            not isinstance(target.ctx, Load) for _chain, target in uses
        ):
            unsafe_attrs.add(attr)
            continue
        imports_needed[attr] = local
        for _chain, target in uses:
            rewrites.append((target, local))
        converted.append(attr)
    kept.extend(sorted(unsafe_attrs))
    return _AttrPlan(
        converted=converted,
        rewrites=rewrites,
        imports_needed=imports_needed,
        unsafe_attrs=unsafe_attrs,
        kept=kept,
    )


@final
@dataclass(frozen=True, slots=True)
class _Context:
    """Shared rewrite context for one module pass.

    Attributes:
        module: Parsed module.
        body: Module body list, mutated in place.
        parents: Parent map from :func:`_parents`.
        bindings: Names bound in the module.
        existing: Existing ``from`` bindings.

    """

    module: Module
    body: list[stmt]
    parents: dict[int, _Parent]
    bindings: set[str]
    existing: dict[tuple[str, str], str]


def _rewrite_import(
    *,
    statement: stmt,
    position: int,
    context: _Context,
) -> ImportRewrite | None:
    """Rewrite one candidate ``import`` statement in place.

    Args:
        statement: ``import a[.b...]`` statement to process.
        position: Index just past ``statement`` in the module body.
        context: Shared module rewrite context.

    Returns:
        The conversion report, or ``None`` when the import is unsafe.

    """
    if not (
        isinstance(statement, Import)
        and len(statement.names) == 1
        and statement.names[0].asname is None
    ):
        return None
    entry: alias = statement.names[0]
    root: str = entry.name.split(sep=".", maxsplit=1)[0]
    prefix: tuple[str, ...] = tuple(entry.name.split(sep=".")[1:])
    chains, bare_ids = _chains(module=context.module, root=root)
    # Detector precondition: root bound exactly once (this import)
    # and every attribute chain covers the dotted prefix.
    bindings_of_root: int = sum(
        1
        for node in walk(node=context.module)
        if isinstance(node, (Import, ImportFrom))
        for item in node.names
        if (item.asname or item.name.split(sep=".", maxsplit=1)[0]) == root
    )
    if bindings_of_root != 1 or any(
        chain.names[: len(prefix)] != prefix for chain in chains.values()
    ):
        return None
    plan: _AttrPlan = _attribute_plan(
        chains=chains,
        prefix=prefix,
        entry_name=entry.name,
        existing=context.existing,
        bindings=context.bindings,
    )
    kept: list[str] = plan.kept
    remaining: bool = bool(kept) or bool(bare_ids)
    complete: bool = not remaining and not plan.unsafe_attrs
    for target, local in plan.rewrites:
        replacement: Name = Name(id=local, ctx=Load())
        for field_name in (
            "lineno",
            "col_offset",
            "end_lineno",
            "end_col_offset",
        ):
            if hasattr(target, field_name):
                setattr(
                    replacement,
                    field_name,
                    getattr(target, field_name),
                )
        _replace_node(parents=context.parents, old=target, new=replacement)
    if plan.imports_needed:
        names: list[alias] = [
            alias(
                name=attr,
                asname=(local if local != attr else None),
            )
            for attr, local in sorted(plan.imports_needed.items())
        ]
        from_import: ImportFrom = ImportFrom(
            module=entry.name,
            names=names,
            level=0,
        )
        for field_name in ("lineno", "col_offset"):
            if hasattr(statement, field_name):
                setattr(
                    from_import,
                    field_name,
                    getattr(statement, field_name),
                )
        if complete:
            context.body.remove(statement)
            context.body.insert(position - 1, from_import)
        else:
            context.body.insert(position, from_import)
    return ImportRewrite(
        module=entry.name,
        converted=tuple(sorted(set(plan.converted))),
        kept=tuple(sorted(set(kept))),
        complete=complete,
    )


def rewrite_bare_imports(*, module: Module) -> tuple[ImportRewrite, ...]:
    """Rewrite safe ``import a`` attribute uses into ``from`` imports.

    Only direct module-level single-name ``import`` statements are
    considered; aliases, multi-name imports, conditional and
    function-level imports are left alone.  Unsafe attribute sites
    (stores, deletes, aug-assign targets, name collisions) keep
    ``import a`` alive for them.

    Args:
        module: Parsed module, mutated in place.

    Returns:
        One report per processed import statement, in source order.

    """
    parents: dict[int, _Parent] = _parents(module=module)
    context: _Context = _Context(
        module=module,
        body=module.body,
        parents=parents,
        bindings=_bindings(module=module),
        existing=_existing_from(module=module),
    )
    reports: list[ImportRewrite] = []
    index: int = 0
    while index < len(context.body):
        statement: stmt = context.body[index]
        index += 1
        report: ImportRewrite | None = _rewrite_import(
            statement=statement,
            position=index,
            context=context,
        )
        if report is not None:
            reports.append(report)
    return tuple(reports)
