"""Extract one module's definitions, imports, exports and call records.

:func:`scan_module` reads a parsed module once and records everything the
symbol table and call graph need: top-level names, every import binding
(absolute, relative and conditional), the literal ``__all__`` when one is
declared, and the parsed tree so later stages can build contracts and
bind call arguments without reparsing.
"""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    List,
    Module,
    Name,
    Set,
    Tuple,
    expr,
    parse,
    walk,
)
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from typing import TYPE_CHECKING, Final, final

from astart.project.naming import package_of

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        all_name: Attribute listing a module's public exports.
        list_methods: ``__all__`` mutation methods understood literally.
        init_stem: File stem marking a package initializer.

    """

    all_name: Final[str] = "__all__"
    list_methods: Final[frozenset[str]] = frozenset(
        {"append", "extend", "insert"},
    )
    init_stem: Final[str] = "__init__"


class ImportKind(StrEnum):
    """How an ``ImportRecord`` binds its local name.

    Attributes:
        module: A module object is bound (``import a.b``).
        member: One member of a module is bound (``from a import b``).
        star: Every export of a module is bound (``from a import *``).

    """

    module = "module"
    member = "member"
    star = "star"


@final
@dataclass(frozen=True, slots=True)
class ImportRecord:
    """One name bound by an import statement.

    Attributes:
        local: Name usable in the importing module (the ``as`` name when
            given).
        module: Absolute module the binding comes from; relative imports
            are already resolved against the importing package.
        symbol: Member name inside ``module`` for from-imports, or ``None``
            when a module object itself is bound.
        kind: Which statement shape produced the binding.
        conditional: Whether the import sits inside a conditional suite
            (``if``, ``try``, ``match``…) or a nested scope, so it might
            not run.
        lineno: Line of the import, for diagnostics.

    """

    local: str
    module: str
    symbol: str | None
    kind: ImportKind
    conditional: bool
    lineno: int


@final
@dataclass(frozen=True, slots=True)
class ModuleScan:
    """One file's facts within a project.

    Attributes:
        name: Dotted module name.
        path: Source file.
        content_hash: SHA-256 of the source text; equal hashes mean equal
            facts, so unchanged files need no rescan.
        tree: Parsed module, retained for contracts and call binding.
        is_package: Whether the file is an ``__init__``.
        functions: Top-level function names.
        classes: Top-level class names.
        assignments: Other names bound at top level.
        imports: Every import binding, in document order.
        all_names: Literal ``__all__`` contents, ``None`` when ``__all__``
            is absent or not statically literal.
        all_declared: Whether ``__all__`` is assigned at all; when true but
            ``all_names`` is ``None`` the export list is unknown.
        star_modules: Modules star-imported here; their public names count
            as bound once resolved by the symbol table.

    """

    name: str
    path: Path
    content_hash: str
    tree: Module
    is_package: bool
    functions: tuple[str, ...]
    classes: tuple[str, ...]
    assignments: tuple[str, ...]
    imports: tuple[ImportRecord, ...]
    all_names: tuple[str, ...] | None
    all_declared: bool
    star_modules: tuple[str, ...]

    @property
    def defined_names(self) -> frozenset[str]:
        """Every name the module defines itself.

        Returns:
            Functions, classes and assignments in one set.

        """
        return frozenset(
            (*self.functions, *self.classes, *self.assignments),
        )

    @property
    def bound_names(self) -> frozenset[str]:
        """Every local name, defined or imported.

        Returns:
            The names a statement in this module may legally read.

        """
        return self.defined_names | frozenset(
            record.local for record in self.imports if record.local != "*"
        )


def _absolute(
    *,
    node: ImportFrom,
    package: str,
) -> str:
    """Resolve a from-import's module to its absolute dotted name.

    Args:
        node: The ``from`` statement.
        package: Package the importing module belongs to.

    Returns:
        The absolute module name, or empty when the import climbs above
        the top-level package.

    """
    if node.level == 0:
        return node.module or ""
    base: str = package
    for _ in range(node.level - 1):
        base = base.rpartition(".")[0]
    if not base:
        return node.module or ""
    return f"{base}.{node.module}" if node.module else base


def _import_records(
    *,
    module: Module,
    package: str,
) -> tuple[ImportRecord, ...]:
    """Collect every import binding a module performs.

    Conditional imports are recorded in document order; resolution
    prefers the earliest binding of a name, which matches
    ``try: import real / except: import fallback`` semantics.

    Args:
        module: Parsed module.
        package: Package the importing module's relative imports resolve
            against.

    Returns:
        One record per bound name, in document order.

    """
    top_level: frozenset[int] = frozenset(
        id(statement) for statement in module.body
    )
    records: list[ImportRecord] = []
    for node in walk(node=module):
        conditional: bool = id(node) not in top_level
        match node:
            case Import(names=aliases):
                for entry in aliases:
                    bound: str = (
                        entry.asname
                        if entry.asname is not None
                        else entry.name.split(sep=".")[0]
                    )
                    module_name: str = (
                        entry.name if entry.asname is not None else bound
                    )
                    records.append(
                        ImportRecord(
                            local=bound,
                            module=module_name,
                            symbol=None,
                            kind=ImportKind.module,
                            conditional=conditional,
                            lineno=node.lineno,
                        ),
                    )
            case ImportFrom(names=aliases):
                absolute: str = _absolute(node=node, package=package)
                for entry in aliases:
                    if entry.name == "*":
                        records.append(
                            ImportRecord(
                                local="*",
                                module=absolute,
                                symbol=None,
                                kind=ImportKind.star,
                                conditional=conditional,
                                lineno=node.lineno,
                            ),
                        )
                        continue
                    records.append(
                        ImportRecord(
                            local=entry.asname or entry.name,
                            module=absolute,
                            symbol=entry.name,
                            kind=ImportKind.member,
                            conditional=conditional,
                            lineno=node.lineno,
                        ),
                    )
            case _:
                continue
    return tuple(records)


def _literal_strings(*, node: Assign | AnnAssign | AugAssign) -> list[str]:
    """Read literal strings out of a ``__all__`` assignment value.

    Args:
        node: Assignment or augmented assignment to ``__all__``.

    Returns:
        The strings when the value is a literal list, tuple or set;
        otherwise an empty list meaning "not statically literal".

    """
    value: expr | None = node.value
    if isinstance(value, (List, Tuple, Set)):
        return [
            element.value
            for element in value.elts
            if isinstance(element, Constant) and isinstance(element.value, str)
        ]
    return []


def _all_names(*, module: Module) -> tuple[tuple[str, ...] | None, bool]:
    """Extract a statically literal ``__all__``.

    Args:
        module: Parsed module.

    Returns:
        ``(names, declared)``: the declared names when every statement
        touching ``__all__`` is literal; ``None`` when it is absent or
        computed dynamically.

    """
    names: list[str] = []
    declared: bool = False
    dynamic: bool = False
    for statement in module.body:
        match statement:
            case (
                Assign(targets=[Name(id=target)])
                | AnnAssign(
                    target=Name(id=target),
                )
                | AugAssign(target=Name(id=target))
            ) if target == Constants.all_name:
                declared = True
                pieces: list[str] = _literal_strings(node=statement)
                if pieces or isinstance(
                    statement.value,
                    (List, Tuple, Set),
                ):
                    names.extend(pieces)
                else:
                    dynamic = True
            case Expr(
                value=Call(
                    func=Attribute(
                        value=Name(id=owner),
                        attr=method,
                    ),
                    args=[argument],
                ),
            ) if (
                owner == Constants.all_name
                and method in Constants.list_methods
            ):
                declared = True
                if isinstance(argument, Constant) and isinstance(
                    argument.value,
                    str,
                ):
                    names.append(argument.value)
                elif isinstance(argument, (List, Tuple, Set)):
                    names.extend(
                        element.value
                        for element in argument.elts
                        if isinstance(element, Constant)
                        and isinstance(element.value, str)
                    )
                else:
                    dynamic = True
            case _:
                continue
    if dynamic:
        return None, declared
    return (tuple(dict.fromkeys(names)) if declared else None), declared


def _top_level(
    *,
    module: Module,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Collect names bound directly by module-level statements.

    Args:
        module: Parsed module.

    Returns:
        Function names, class names, and other bound names, each in
        document order.

    """
    functions: list[str] = []
    classes: list[str] = []
    assignments: list[str] = []
    for statement in module.body:
        match statement:
            case FunctionDef(name=name) | AsyncFunctionDef(name=name):
                functions.append(name)
            case ClassDef(name=name):
                classes.append(name)
            case Assign(targets=targets):
                assignments.extend(
                    target.id for target in targets if isinstance(target, Name)
                )
            case AnnAssign(target=Name(id=name)):
                assignments.append(name)
            case _:
                continue
    return tuple(functions), tuple(classes), tuple(assignments)


def scan_module(
    *,
    source: str,
    name: str,
    path: Path,
) -> ModuleScan:
    """Parse and index one source file.

    Args:
        source: Python source text.
        name: Dotted module name from
            :func:`astart.project.naming.module_name`.
        path: File the text came from.

    Returns:
        The module's scan record.

    """
    tree: Module = parse(source=source, filename=str(object=path))
    is_package: bool = path.stem == Constants.init_stem
    functions, classes, assignments = _top_level(module=tree)
    records: tuple[ImportRecord, ...] = _import_records(
        module=tree,
        package=package_of(name=name, is_package=is_package),
    )
    all_names, all_declared = _all_names(module=tree)
    return ModuleScan(
        name=name,
        path=path,
        content_hash=sha256(data=source.encode(encoding="utf-8")).hexdigest(),
        tree=tree,
        is_package=is_package,
        functions=functions,
        classes=classes,
        assignments=assignments,
        imports=records,
        all_names=all_names,
        all_declared=all_declared,
        star_modules=tuple(
            record.module
            for record in records
            if record.kind is ImportKind.star
        ),
    )
