"""Whole-project index: definitions, call graph, escapes and exports.

:class:`ProjectIndex` builds on the symbol table. For every module it
records top-level and nested definitions, every direct call whose callee
resolves inside the project, and every load of a project name that is not
a direct call (an escape, which makes that function's caller set
unknowable). Module records are keyed by content hash, so
:meth:`refresh` of an unchanged file is free and a changed file only
invalidates the callees it used to call plus the ones it calls now.

"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    FunctionDef,
    Load,
    Name,
    expr,
    iter_child_nodes,
    walk,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from astart.project.scan import ImportKind, ModuleScan
from astart.project.table import (
    ResolvedSymbol,
    SymbolKind,
    SymbolTable,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


type Definition = FunctionDef | AsyncFunctionDef | ClassDef


@final
@dataclass(frozen=True, slots=True)
class CallRecord:
    """One project-internal call site.

    Attributes:
        module (str): Module containing the call.
        caller (str): Qualified name of the scope the call executes in — the
            enclosing function, the enclosing class body, or the module
            itself for top-level statements.
        node (Call): The call AST, retained for argument binding.
        callee (ResolvedSymbol | None): Where the callee resolved, or ``None``
            when the target is external or ambiguous.

    """

    module: str
    caller: str
    node: Call
    callee: ResolvedSymbol | None


@final
@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Toggles controlling how complete the caller set is assumed to be.

    Attributes:
        assume_external_callers (bool): When true, exported project functions
            may be called from
            outside the analysed set, so their call-site evidence
            is incomplete and guarded fixes must stay guarded.
            When false every project-internal definition is closed-world:
            its recorded callers are all of its callers.

    """

    assume_external_callers: bool = True


def _dotted(func: expr) -> str:
    """Render an attribute chain as a dotted path.

    Args:
        func (expr): Expression to render (usually ``call.func``).

    Returns:
        str: ``"a.b.c"`` for name/attribute chains, ``""`` otherwise.

    """
    match func:
        case Name(id=name):
            return name
        case Attribute(value=value, attr=attr):
            base: str = _dotted(func=value)
            return f"{base}.{attr}" if base else ""
        case _:
            return ""


def _resolve_callee(
    *,
    table: SymbolTable,
    module: str,
    func: expr,
) -> ResolvedSymbol | None:
    """Resolve a call's target to a project symbol.

    Handles ``f()``, ``pkg.mod.f()`` and the constructor-method shape
    ``C().m()``; anything unresolved stays ``None``.

    Args:
        table (SymbolTable): Symbol table.
        module (str): Module containing the call.
        func (expr): The ``call.func`` expression.

    Returns:
        ResolvedSymbol | None: The resolved callee, or ``None``.

    """
    match func:
        case Attribute(value=Call(func=ctor), attr=method):
            base: str = _dotted(func=ctor)
            if not base:
                return None
            resolved: ResolvedSymbol | None = table.resolve_path(
                module=module,
                dotted=base,
            )
            if resolved is None or resolved.kind is not SymbolKind.class_:
                return None
            return ResolvedSymbol(
                module=resolved.module,
                name=method,
                qualified=f"{resolved.qualified}.{method}",
                kind=SymbolKind.variable,
                via=resolved.via,
            )
        case Name() | Attribute():
            dotted: str = _dotted(func=func)
            if not dotted:
                return None
            return table.resolve_path(module=module, dotted=dotted)
        case _:
            return None


@final
class _Collector:
    """Accumulates one module's calls, escapes and definitions.

    Attributes:
        table: Symbol table for callee resolution.
        module: Module being scanned.
        callee_ids: Ids of every node inside some ``Call.func`` chain;
            loads of those are callees, not escapes.
        calls: Call records accumulate here.
        escaped: Escaped name/attribute loads accumulate here.
        definitions: Qualified definitions accumulate here.

    """

    def __init__(self, *, table: SymbolTable, module: str) -> None:
        """Start empty accumulation for one module.

        Args:
            table (SymbolTable): Symbol table for callee resolution.
            module (str): Module being scanned.

        """
        self.table: SymbolTable = table
        self.module: str = module
        self.callee_ids: frozenset[int] = frozenset()
        self.calls: list[CallRecord] = []
        self.escaped: list[expr] = []
        self.definitions: dict[str, Definition] = {}


def _header_parts(*, node: AST) -> tuple[AST | None, ...]:
    """List the parts of a definition that run in the outer scope.

    Args:
        node (AST): Function, async function or class definition.

    Returns:
        tuple[AST | None, ...]: Decorators, signature, return annotation, type
            parameters and
            — for classes — bases and keyword values, in source order.

    """
    match node:
        case FunctionDef() | AsyncFunctionDef():
            return (
                *node.decorator_list,
                node.args,
                node.returns,
                *node.type_params,
            )
        case ClassDef():
            return (
                *node.decorator_list,
                *node.bases,
                *node.type_params,
                *(kw.value for kw in node.keywords),
            )
        case _:
            return ()


def _visit_header(
    *,
    node: AST,
    prefix: str,
    collector: _Collector,
) -> None:
    """Visit definition header parts in the enclosing scope.

    Decorators, default values and class bases execute in the *outer*
    scope, so they are visited under the outer prefix while bodies
    recurse under the newly defined name.

    Args:
        node (AST): Definition whose header executes outside its body.
        prefix (str): Qualified name of the enclosing scope.
        collector (_Collector): Accumulator for calls, escapes and definitions.

    """
    for part in _header_parts(node=node):
        if part is not None:
            _visit(node=part, prefix=prefix, collector=collector)


def _visit(
    *,
    node: AST,
    prefix: str,
    collector: _Collector,
) -> None:
    """Walk a scope recording calls, escapes and nested definitions.

    Args:
        node (AST): AST node to visit.
        prefix (str): Qualified name of the enclosing scope.
        collector (_Collector): Accumulator for calls, escapes and definitions.

    """
    match node:
        case FunctionDef() | AsyncFunctionDef() | ClassDef():
            qualified: str = f"{prefix}.{node.name}"
            collector.definitions[qualified] = node
            _visit_header(node=node, prefix=prefix, collector=collector)
            for child in node.body:
                _visit(node=child, prefix=qualified, collector=collector)
            return
        case Call(func=func):
            collector.calls.append(
                CallRecord(
                    module=collector.module,
                    caller=prefix,
                    node=node,
                    callee=_resolve_callee(
                        table=collector.table,
                        module=collector.module,
                        func=func,
                    ),
                ),
            )
        case Name(ctx=Load()) | Attribute(ctx=Load()):
            if id(node) not in collector.callee_ids:
                collector.escaped.append(node)
        case _:
            pass
    for child in iter_child_nodes(node=node):
        _visit(node=child, prefix=prefix, collector=collector)


def _collect_scope(
    *,
    table: SymbolTable,
    scan: ModuleScan,
) -> tuple[list[CallRecord], list[expr], dict[str, Definition]]:
    """Index one module's calls, escapes and definitions.

    Args:
        table (SymbolTable): Symbol table.
        scan (ModuleScan): The module's scan.

    Returns:
        tuple[list[CallRecord], list[expr], dict[str, Definition]]:
            ``(calls, escaped loads, definitions)``.

    """
    collector: _Collector = _Collector(table=table, module=scan.name)
    collector.callee_ids = frozenset(
        id(part)
        for node in walk(node=scan.tree)
        if isinstance(node, Call)
        for part in walk(node=node.func)
    )
    for statement in scan.tree.body:
        _visit(node=statement, prefix=scan.name, collector=collector)
    return collector.calls, collector.escaped, collector.definitions


@final
class ProjectIndex:
    """Project-wide resolution, call graph and open-world classification.

    Attributes:
        config: Open-world policy.
        scans: Module scans by dotted name (replaced on refresh).
        table: Symbol table over ``scans``.
        missing: Imported names absent from the scan set.

    """

    def __init__(
        self,
        *,
        scans: Mapping[str, ModuleScan],
        config: ProjectConfig | None = None,
    ) -> None:
        """Build the index over a set of module scans.

        Args:
            scans (Mapping[str, ModuleScan]): Module scans by dotted name.
            config (ProjectConfig | None): Open-world policy; defaults to
                assuming
                external callers for exported functions.

        """
        self.config: ProjectConfig = config or ProjectConfig()
        self.scans: dict[str, ModuleScan] = dict(scans)
        self.version: int = 0
        self.table: SymbolTable = SymbolTable(scans=self.scans)
        self._calls: dict[str, list[CallRecord]] = {}
        self._by_callee: dict[str, list[CallRecord]] = {}
        self._definitions: dict[str, Definition] = {}
        self._escaped_loads: dict[str, list[expr]] = {}
        self._escaped: set[str] = set()
        for scan in self.scans.values():
            self._index_module(scan=scan)
        self.missing: frozenset[str] = self.table.missing

    def module_scan(self, *, module: str) -> ModuleScan | None:
        """Scan a module.

        Args:
            module (str): Dotted module name.

        Returns:
            ModuleScan | None: The scan, or ``None``.

        """
        return self.scans.get(module)

    def resolve_callee(
        self,
        *,
        module: str,
        func: expr,
    ) -> ResolvedSymbol | None:
        """Resolve a call's target as seen inside one module.

        Args:
            module (str): Module containing the call.
            func (expr): The ``call.func`` expression.

        Returns:
            ResolvedSymbol | None: The resolved callee — project definition
                or external symbol — or ``None``.

        """
        return _resolve_callee(
            table=self.table,
            module=module,
            func=func,
        )

    def defined(self) -> frozenset[str]:
        """Every qualified name the project defines.

        Returns:
            frozenset[str]: Qualified names of all indexed functions, methods
                and classes.

        """
        return frozenset(self._definitions)

    def records_for(self, *, qualified: str) -> tuple[CallRecord, ...]:
        """All recorded call sites of one project callee.

        Args:
            qualified (str): Qualified name such as ``"pkg.mod.func"``.

        Returns:
            tuple[CallRecord, ...]: Call records across the whole project.

        """
        return tuple(self._by_callee.get(qualified, ()))

    def callers(self, *, qualified: str) -> frozenset[str]:
        """Qualified names of scopes that call a callee.

        Args:
            qualified (str): Qualified callee name.

        Returns:
            frozenset[str]: The caller set.

        """
        return frozenset(
            record.caller for record in self._by_callee.get(qualified, ())
        )

    def definition(self, *, qualified: str) -> Definition | None:
        """Return the AST node defining a qualified name.

        Args:
            qualified (str): Qualified name.

        Returns:
            Definition | None:
                The defining ``def`` /``class`` node, or ``None``.

        """
        return self._definitions.get(qualified)

    def imported_names(
        self,
        *,
        module: str,
    ) -> dict[str, ResolvedSymbol]:
        """Every bound name in a module and where it resolves.

        Args:
            module (str): Dotted module name.

        Returns:
            dict[str, ResolvedSymbol]: Local name to resolution, for names that
                resolve at all.

        """
        scan: ModuleScan | None = self.scans.get(module)
        if scan is None:
            return {}
        out: dict[str, ResolvedSymbol] = {}
        for name in scan.bound_names:
            resolved: ResolvedSymbol | None = self.table.resolve(
                module=module,
                name=name,
            )
            if resolved is not None:
                out[name] = resolved
        return out

    def escaped(self, *, qualified: str) -> bool:
        """Whether a project name is read anywhere but as a direct callee.

        Args:
            qualified (str): Qualified name.

        Returns:
            bool: Whether the name escapes.

        """
        return qualified in self._escaped

    def exported(self, *, qualified: str) -> bool:
        """Whether a qualified name is part of its module's public surface.

        A member is exported when it appears in the owning module's
        exports or when a package ``__init__`` re-exports it. Methods of
        exported classes inherit the class's surface.

        Args:
            qualified (str): Qualified name such as ``"pkg.mod.func"`` or
                ``"pkg.mod.C.m"``.

        Returns:
            bool: Whether the name is exported.

        """
        owner, _, name = qualified.rpartition(".")
        if not owner or not name or name.startswith("_"):
            return False
        owner_module: str = self._owning_module(owner=owner)
        scan: ModuleScan | None = self.scans.get(owner_module)
        if scan is None:
            return False
        if owner != owner_module:
            parent: str = owner.removeprefix(f"{owner_module}.").partition(
                ".",
            )[0]
            return parent in self.table.exports(module=owner_module)
        if name in self.table.exports(module=owner_module):
            return True
        return self._reexported(owner_module=owner_module, name=name)

    def open_world(self, *, qualified: str) -> bool:
        """Whether a callee's recorded callers might be incomplete.

        Escaped names are always incomplete — someone can call the
        function object through an alias the graph cannot see. With
        ``assume_external_callers`` exported functions are incomplete too.

        Args:
            qualified (str): Qualified callee name.

        Returns:
            bool: Whether caller evidence for the callee is incomplete.

        """
        if self.escaped(qualified=qualified):
            return True
        return self.config.assume_external_callers and self.exported(
            qualified=qualified,
        )

    def refresh(self, *, scan: ModuleScan) -> frozenset[str]:
        """Insert or replace one module's scan.

        Unchanged content hashes are a no-op; otherwise the module's old
        call records, definitions and escapes are dropped and re-indexed.
        The returned callee set covers both the old and the new edges, so
        callers can invalidate exactly the evidence that could differ.

        Args:
            scan (ModuleScan): Fresh scan of the module.

        Returns:
            frozenset[str]: Qualified callees whose evidence may have changed.

        """
        old: ModuleScan | None = self.scans.get(scan.name)
        if old is not None and old.content_hash == scan.content_hash:
            return frozenset()
        affected: set[str] = set()
        if old is not None:
            affected.update(self._drop_module(scan=old))
        self.scans[scan.name] = scan
        self._rebuild_table()
        affected.update(self._index_module(scan=scan))
        self._rebuild_escapes()
        self.version += 1
        return frozenset(affected)

    def remove(self, *, name: str) -> frozenset[str]:
        """Drop a module from the index.

        Args:
            name (str): Dotted module name.

        Returns:
            frozenset[str]: Callees whose evidence may have changed.

        """
        scan: ModuleScan | None = self.scans.pop(name, None)
        if scan is None:
            return frozenset()
        affected: set[str] = set(self._drop_module(scan=scan))
        self._rebuild_table()
        self._rebuild_escapes()
        self.version += 1
        return frozenset(affected)

    def _owning_module(self, *, owner: str) -> str:
        """Find the longest module prefix of a qualified owner path.

        Args:
            owner (str): Qualified name of the containing scope, e.g.
                ``"pkg.mod.C"`` for a method.

        Returns:
            str: The owning module's dotted name.

        """
        parts: list[str] = owner.split(sep=".")
        for length in range(len(parts), 0, -1):
            prefix: str = ".".join(parts[:length])
            if prefix in self.scans:
                return prefix
        return owner

    def _reexported(self, *, owner_module: str, name: str) -> bool:
        """Check whether a package ``__init__`` re-exports a name.

        Args:
            owner_module (str): Module the name is defined in.
            name (str): Member name.

        Returns:
            bool: Whether some package's export surface contains the name
                because it imported it from ``owner_module``.

        """
        for scan in self.scans.values():
            if not scan.is_package:
                continue
            for record in scan.imports:
                if (
                    record.kind is ImportKind.member
                    and record.module == owner_module
                    and record.symbol == name
                    and record.local in self.table.exports(module=scan.name)
                ):
                    return True
        return False

    def _rebuild_table(self) -> None:
        """Rebuild the symbol table and re-resolve every call.

        A changed module can alter resolution for callers in other
        modules (a removed export), so every retained call record is
        re-resolved and the by-callee map rebuilt wholesale.

        """
        self.table = SymbolTable(scans=self.scans)
        self.missing = self.table.missing
        for scan in self.scans.values():
            self._calls[scan.name] = [
                CallRecord(
                    module=record.module,
                    caller=record.caller,
                    node=record.node,
                    callee=_resolve_callee(
                        table=self.table,
                        module=scan.name,
                        func=record.node.func,
                    ),
                )
                for record in self._calls.get(scan.name, ())
            ]
        self._by_callee = {}
        for records in self._calls.values():
            for record in records:
                if record.callee is None or record.callee.external:
                    continue
                self._by_callee.setdefault(
                    record.callee.qualified,
                    [],
                ).append(record)

    def _index_module(self, *, scan: ModuleScan) -> set[str]:
        """Add a module's definitions, calls and escapes to the index.

        Args:
            scan (ModuleScan): The module's scan.

        Returns:
            set[str]: Callees the module's calls resolve to.

        """
        calls, escaped, definitions = _collect_scope(
            table=self.table,
            scan=scan,
        )
        prefix: str = f"{scan.name}."
        for qualified, node in definitions.items():
            if qualified.startswith(prefix):
                self._definitions[qualified] = node
        self._calls[scan.name] = calls
        self._escaped_loads[scan.name] = escaped
        touched: set[str] = set()
        for record in calls:
            if record.callee is None or record.callee.external:
                continue
            self._by_callee.setdefault(
                record.callee.qualified,
                [],
            ).append(record)
            touched.add(record.callee.qualified)
        self._mark_escapes(escaped=escaped, scan=scan)
        return touched

    def _drop_module(self, *, scan: ModuleScan) -> set[str]:
        """Remove a module's records, definitions and escapes.

        Args:
            scan (ModuleScan): The module's old scan.

        Returns:
            set[str]: Callees the module used to call.

        """
        prefix: str = f"{scan.name}."
        self._definitions = {
            key: value
            for key, value in self._definitions.items()
            if not key.startswith(prefix)
        }
        self._escaped_loads.pop(scan.name, None)
        records: list[CallRecord] = self._calls.pop(scan.name, [])
        return {
            record.callee.qualified
            for record in records
            if record.callee is not None and not record.callee.external
        }

    def _rebuild_escapes(self) -> None:
        """Recompute the escaped set from all retained loads.

        Escapes must be re-resolved wholesale because a refresh can make
        an old load resolve differently (a removed export, a new module).

        """
        self._escaped.clear()
        for name, loads in self._escaped_loads.items():
            scan: ModuleScan | None = self.scans.get(name)
            if scan is None:
                continue
            self._mark_escapes(escaped=loads, scan=scan)

    def _mark_escapes(
        self,
        *,
        escaped: list[expr],
        scan: ModuleScan,
    ) -> None:
        """Resolve each escape load and mark resolved internal symbols.

        Args:
            escaped (list[expr]): Escaped load expressions from one module.
            scan (ModuleScan): Module the loads came from.

        """
        for load in escaped:
            dotted: str = _dotted(func=load)
            if not dotted:
                continue
            resolved: ResolvedSymbol | None = self.table.resolve_path(
                module=scan.name,
                dotted=dotted,
            )
            if resolved is not None and not resolved.external:
                self._escaped.add(resolved.qualified)
