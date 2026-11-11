"""Resolve names across a project's modules.

:class:`SymbolTable` answers "where does this name come from" for every
module: local definitions first, then import bindings (which may be
``__init__`` re-exports pointing deeper into the project), then sibling
submodules. Anything outside the scanned file set is reported as
``external`` rather than unresolvable, so callers can distinguish a
library reference from an ambiguous one.

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import final

from astart.project.scan import ImportKind, ModuleScan


class SymbolKind(StrEnum):
    """What a resolved name is.

    Attributes:
        function: Module-level function.
        class_: Class definition.
        variable: Any other module-level binding.
        module: A module object itself.
        external: Something outside the scanned project (a library).

    """

    function = "function"
    class_ = "class"
    variable = "variable"
    module = "module"
    external = "external"


@final
@dataclass(frozen=True, slots=True)
class ResolvedSymbol:
    """Where a name ultimately lives.

    Attributes:
        module (str): Dotted module owning the definition. For
            :attr:`SymbolKind.external` this is the library module the name
            was imported from.
        name (str): Member name inside ``module``; empty for module bindings.
        qualified (str): ``module.name`` in one string.
        kind (SymbolKind): What the name is.
        external (bool): Whether the definition lies outside the scanned
            project.
        via (tuple[str, ...]): Intermediate qualified names the resolution
            passed
            through (re-export chain), for diagnostics.

    """

    module: str
    name: str
    qualified: str
    kind: SymbolKind
    external: bool = False
    via: tuple[str, ...] = ()


@final
class SymbolTable:
    """Project-wide name resolution built from module scans.

    Attributes:
        scans: Module scans by dotted name.
        missing: Dotted names imported but not present in the scan set,
            whether library or simply absent.

    """

    def __init__(self, *, scans: dict[str, ModuleScan]) -> None:
        """Build the table over a fixed set of scans.

        Args:
            scans (dict[str, ModuleScan]): Module scans by dotted name.

        """
        self.scans: dict[str, ModuleScan] = scans
        self._local_bindings: dict[str, dict[str, list[ResolvedSymbol]]] = {}
        self._exports_cache: dict[str, frozenset[str]] = {}
        self.missing: frozenset[str] = frozenset(
            record.module
            for scan in scans.values()
            for record in scan.imports
            if record.module and record.module not in scans
        )

    def module(self, *, name: str) -> ModuleScan | None:
        """Return the scan of a module.

        Args:
            name (str): Dotted module name.

        Returns:
            ModuleScan | None: The scan, or ``None``.

        """
        return self.scans.get(name)

    def resolve(
        self,
        *,
        module: str,
        name: str,
    ) -> ResolvedSymbol | None:
        """Resolve ``name`` as seen inside ``module``.

        Local definitions beat import bindings. Among import bindings the
        earliest record in document order wins, so ``try: import real``
        beats ``except: import fallback``. A name that is neither defined
        nor imported may still name a sibling submodule.

        Args:
            module (str): Dotted module the name is read in.
            name (str): Local name to resolve.

        Returns:
            ResolvedSymbol | None: The resolution, or ``None`` when
                the name is ambiguous or unbound.

        """
        return self._resolve(module=module, name=name, seen=())

    def resolve_path(
        self,
        *,
        module: str,
        dotted: str,
    ) -> ResolvedSymbol | None:
        """Resolve a dotted access like ``pkg.sub.func`` in ``module``.

        The leftmost name resolves in ``module``; each further attribute
        resolves inside the module or member it resolved to.

        Args:
            module (str): Module the path is read in.
            dotted (str): Attribute path (``"a"`` or ``"a.b.c"``).

        Returns:
            ResolvedSymbol | None: The final symbol, or ``None``.

        """
        parts: list[str] = dotted.split(sep=".")
        current: ResolvedSymbol | None = self.resolve(
            module=module,
            name=parts[0],
        )
        for part in parts[1:]:
            if current is None:
                return None
            current = self._member(current=current, part=part)
        return current

    def resolve_qualified(self, *, qualified: str) -> ResolvedSymbol | None:
        """Resolve a fully qualified ``module.name`` path.

        Args:
            qualified (str): Dotted path such as ``"pkg.mod.func"``.

        Returns:
            ResolvedSymbol | None: The symbol, or ``None``.

        """
        parts: list[str] = qualified.split(sep=".")
        for length in range(len(parts), 0, -1):
            prefix: str = ".".join(parts[:length])
            if prefix not in self.scans:
                continue
            current: ResolvedSymbol | None = ResolvedSymbol(
                module=prefix,
                name="",
                qualified=prefix,
                kind=SymbolKind.module,
            )
            for part in parts[length:]:
                if current is None:
                    break
                current = self._member(current=current, part=part)
            return current
        return None

    def _member(
        self,
        *,
        current: ResolvedSymbol,
        part: str,
    ) -> ResolvedSymbol | None:
        """Resolve one attribute step off an already-resolved symbol.

        Project modules resolve the attribute in their own namespace;
        external modules extend the path opaquely; anything else is a
        member access that extends the qualified name without changing
        the owning module.

        Args:
            current (ResolvedSymbol): Symbol the attribute is read off.
            part (str): Attribute name.

        Returns:
            ResolvedSymbol | None:
                The next symbol, or ``None`` when the attribute
                cannot be resolved inside a project module.

        """
        if current.kind is SymbolKind.module:
            if current.external:
                return ResolvedSymbol(
                    module=current.module,
                    name=part,
                    qualified=f"{current.qualified}.{part}",
                    kind=SymbolKind.external,
                    external=True,
                    via=current.via,
                )
            return self._resolve(
                module=current.module,
                name=part,
                seen=(current.qualified,),
            )
        return ResolvedSymbol(
            module=current.module,
            name=part,
            qualified=f"{current.qualified}.{part}",
            kind=SymbolKind.variable,
            external=current.external,
            via=current.via,
        )

    def exports(self, *, module: str) -> frozenset[str]:
        """List the names a module exports.

        ``__all__`` wins when declared literally; a dynamic ``__all__``
        falls back to every public bound name; without one, every public
        bound name counts, including names pulled in by star imports.

        Args:
            module (str): Dotted module name.

        Returns:
            frozenset[str]: The export surface.

        """
        if module in self._exports_cache:
            return self._exports_cache[module]
        self._exports_cache[module] = self._exports(
            module=module,
            seen=(module,),
        )
        return self._exports_cache[module]

    def _exports(
        self,
        *,
        module: str,
        seen: tuple[str, ...],
    ) -> frozenset[str]:
        """Compute exports with star-import cycle protection.

        Args:
            module (str): Dotted module name.
            seen (tuple[str, ...]): Modules already on this resolution chain.

        Returns:
            frozenset[str]: The export surface.

        """
        scan: ModuleScan | None = self.scans.get(module)
        if scan is None:
            return frozenset()
        if scan.all_names is not None:
            return frozenset(scan.all_names)
        exported: set[str] = {
            name for name in scan.bound_names if not name.startswith("_")
        }
        for star in scan.star_modules:
            if star == module or star in seen:
                continue
            exported.update(
                name
                for name in self._exports(module=star, seen=(*seen, star))
                if not name.startswith("_")
            )
        return frozenset(exported)

    @staticmethod
    def _kind_of(*, scan: ModuleScan, name: str) -> SymbolKind:
        """Classify a locally defined name.

        Args:
            scan (ModuleScan): Module the name is defined in.
            name (str): Defined name.

        Returns:
            SymbolKind: The symbol kind.

        """
        if name in scan.functions:
            return SymbolKind.function
        if name in scan.classes:
            return SymbolKind.class_
        return SymbolKind.variable

    def _resolve_import(
        self,
        *,
        name: str,
        scan: ModuleScan,
        qualified: str,
        seen: tuple[str, ...],
    ) -> ResolvedSymbol | None:
        """Follow named-import records binding one local name.

        Args:
            name (str): Local name being resolved.
            scan (ModuleScan): Module being searched.
            qualified (str): The name's qualified path, for ``via`` chains.
            seen (tuple[str, ...]): Qualified names already on this chain.

        Returns:
            ResolvedSymbol | None:
                The resolution, or ``None`` when no record binds the name.

        """
        for record in scan.imports:
            if record.local != name or record.kind is ImportKind.star:
                continue
            followed: ResolvedSymbol | None = self._resolve(
                module=record.module,
                name=record.symbol or "",
                seen=(*seen, qualified),
            )
            if followed is None:
                if record.module in self.scans:
                    continue
                return ResolvedSymbol(
                    module=record.module,
                    name=record.symbol or "",
                    qualified=(
                        f"{record.module}.{record.symbol}"
                        if record.symbol
                        else record.module
                    ),
                    kind=SymbolKind.module
                    if record.symbol is None
                    else SymbolKind.external,
                    external=True,
                    via=(qualified,),
                )
            return ResolvedSymbol(
                module=followed.module,
                name=followed.name,
                qualified=followed.qualified,
                kind=followed.kind,
                external=followed.external,
                via=(*seen, qualified),
            )
        return None

    def _resolve_star(
        self,
        *,
        module: str,
        name: str,
        scan: ModuleScan,
        qualified: str,
        seen: tuple[str, ...],
    ) -> ResolvedSymbol | None:
        """Resolve a name through star-imported modules.

        Args:
            module (str): Module the name is read in.
            name (str): Local name.
            scan (ModuleScan): Module being searched.
            qualified (str): The name's qualified path.
            seen (tuple[str, ...]): Modules and names already on this chain.

        Returns:
            ResolvedSymbol | None: The resolution, or ``None``.

        """
        for star in scan.star_modules:
            if star == module or star in seen:
                continue
            if name not in self._exports(module=star, seen=(*seen, star)):
                continue
            followed: ResolvedSymbol | None = self._resolve(
                module=star,
                name=name,
                seen=(*seen, qualified),
            )
            if followed is not None:
                return followed
        return None

    def _resolve(
        self,
        *,
        module: str,
        name: str,
        seen: tuple[str, ...],
    ) -> ResolvedSymbol | None:
        """Resolve one name with re-export cycle protection.

        Args:
            module (str): Module the name is read in.
            name (str): Local name.
            seen (tuple[str, ...]): Qualified names already on this chain.

        Returns:
            ResolvedSymbol | None: The resolution, or ``None``.

        """
        scan: ModuleScan | None = self.scans.get(module)
        if scan is None:
            return None
        if not name:
            return ResolvedSymbol(
                module=module,
                name="",
                qualified=module,
                kind=SymbolKind.module,
            )
        qualified: str = f"{module}.{name}"
        if qualified in seen:
            return None
        if name in scan.defined_names:
            return ResolvedSymbol(
                module=module,
                name=name,
                qualified=qualified,
                kind=self._kind_of(scan=scan, name=name),
            )
        resolved: ResolvedSymbol | None = self._resolve_import(
            name=name,
            scan=scan,
            qualified=qualified,
            seen=seen,
        ) or self._resolve_star(
            module=module,
            name=name,
            scan=scan,
            qualified=qualified,
            seen=seen,
        )
        if resolved is None and qualified in self.scans:
            resolved = ResolvedSymbol(
                module=qualified,
                name="",
                qualified=qualified,
                kind=SymbolKind.module,
            )
        return resolved
