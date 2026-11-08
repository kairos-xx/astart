"""Add the imports a synthesized annotation needs."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    Constant,
    Del,
    DictComp,
    Expr,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Lambda,
    ListComp,
    Module,
    Name,
    SetComp,
    Store,
    alias,
    arg,
    expr,
    iter_child_nodes,
    stmt,
    walk,
)
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Mapping


@final
class Constants:
    """Group module-level constants.

    Attributes:
        known_imports: Grouped module constant.
        constructors: Grouped module constant.

    """

    known_imports: Final[Mapping[str, str]] = {
        "Awaitable": "collections.abc",
        "Callable": "collections.abc",
        "Coroutine": "collections.abc",
        "Generator": "collections.abc",
        "Iterable": "collections.abc",
        "Iterator": "collections.abc",
        "Mapping": "collections.abc",
        "MutableMapping": "collections.abc",
        "MutableSequence": "collections.abc",
        "Sequence": "collections.abc",
        "Decimal": "decimal",
        "Fraction": "fractions",
        "Path": "pathlib",
        "PurePath": "pathlib",
        "UUID": "uuid",
        "date": "datetime",
        "datetime": "datetime",
        "timedelta": "datetime",
        "Final": "typing",
        "NoReturn": "typing",
        "Optional": "typing",
        "Protocol": "typing",
        "Self": "typing",
        "TypeVar": "typing",
        "Union": "typing",
    }
    constructors: Final[frozenset[str]] = frozenset(
        {
            "Decimal",
            "Fraction",
            "Path",
            "PurePath",
            "UUID",
            "date",
            "datetime",
            "timedelta",
        },
    )


def bound_names(*, module: Module) -> frozenset[str]:
    """Collect every name the module binds anywhere.

    Args:
        module: Parsed module.

    Returns:
        Imported, defined and assigned names.

    """
    names: set[str] = set()
    for node in walk(node=module):
        match node:
            case alias(name=name, asname=asname):
                names.add(asname or name.split(sep=".")[0])
            case (
                ClassDef(name=name)
                | FunctionDef(name=name)
                | AsyncFunctionDef(name=name)
            ):
                names.add(name)
            case Name(id=name, ctx=Store() | Del()):
                names.add(name)
            case arg(arg=name):
                names.add(name)
            case _:
                continue
    return frozenset(names)


def _is_type_checking(*, test: expr) -> bool:
    """Tell whether an ``if`` test is ``TYPE_CHECKING``.

    Args:
        test: Condition expression.

    Returns:
        ``True`` for ``TYPE_CHECKING`` and ``module.TYPE_CHECKING``.

    """
    return (isinstance(test, Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, Attribute) and test.attr == "TYPE_CHECKING"
    )


def _record_import(
    *,
    node: Import | ImportFrom,
    out: dict[str, tuple[str, str] | None],
) -> None:
    """Record the names an import statement binds.

    Args:
        node: Import statement.
        out: Bound names; a plain ``from`` import records its origin.

    """
    for imported in node.names:
        if isinstance(node, ImportFrom):
            plain: bool = node.level == 0 and imported.asname is None
            out[imported.asname or imported.name] = (
                (node.module or "", imported.name) if plain else None
            )
        else:
            out[imported.asname or imported.name.split(sep=".")[0]] = None


def _visit(*, node: AST, out: dict[str, tuple[str, str] | None]) -> None:
    """Record the names a statement binds when the module runs.

    Definitions are recorded without entering their bodies; the body of an
    ``if TYPE_CHECKING:`` is skipped because it never runs.

    Args:
        node: Statement or expression to scan.
        out: Bound names; an import records ``(module, name)``, anything
            else records ``None``.

    """
    match node:
        case If(test=test, orelse=orelse) if _is_type_checking(test=test):
            for statement in orelse:
                _visit(node=statement, out=out)
        case ImportFrom() | Import():
            _record_import(node=node, out=out)
        case (
            FunctionDef(name=name)
            | AsyncFunctionDef(name=name)
            | ClassDef(name=name)
        ):
            out[name] = None
        case Lambda() | ListComp() | SetComp() | DictComp():
            pass
        case Name(id=name, ctx=Store() | Del()):
            out[name] = None
        case _:
            for child in iter_child_nodes(node=node):
                _visit(node=child, out=out)


def runtime_bindings(
    *,
    module: Module,
    before: int,
) -> dict[str, tuple[str, str] | None]:
    """List the names bound at runtime by the first ``before`` statements.

    Args:
        module: Module to scan.
        before: Number of leading top-level statements that have run.

    Returns:
        Bound names; ``(module, name)`` for a plain ``from`` import.

    """
    out: dict[str, tuple[str, str] | None] = {}
    for statement in module.body[:before]:
        _visit(node=statement, out=out)
    return out


def header_end(*, module: Module) -> int:
    """Find where a new top-level import belongs.

    Args:
        module: Module to inspect.

    Returns:
        The index after the docstring and the leading import block.

    """
    body: list[stmt] = module.body
    index: int = 0
    if (
        body
        and isinstance(body[0], Expr)
        and isinstance(body[0].value, Constant)
        and isinstance(body[0].value.value, str)
    ):
        index = 1
    while index < len(body) and isinstance(
        body[index],
        (Import, ImportFrom),
    ):
        index += 1
    return index


def insert_import(
    *,
    module: Module,
    source: str,
    name: str,
    before: int,
) -> str:
    """Make ``name`` from ``source`` usable by the statement at ``before``.

    The name joins an existing top-level ``from source import ...`` that runs
    before that statement; otherwise a new statement follows the leading
    imports. A name already bound to something else is imported under an
    underscore alias instead, so nothing is shadowed.

    Args:
        module: Module to modify in place.
        source: Module the name is imported from.
        name: Name to import.
        before: Index of the statement that will use the name.

    Returns:
        The local name to write in the annotation or base list.

    """
    bound: dict[str, tuple[str, str] | None] = runtime_bindings(
        module=module,
        before=before,
    )
    if name in bound:
        if bound[name] == (source, name):
            return name
        alias_name: str = f"_{name}"
        while alias_name in bound:
            alias_name = f"_{alias_name}"
        module.body.insert(
            header_end(module=module),
            ImportFrom(
                module=source,
                names=[alias(name=name, asname=alias_name)],
                level=0,
            ),
        )
        return alias_name
    for statement in module.body[:before]:
        if (
            isinstance(statement, ImportFrom)
            and statement.module == source
            and (statement.level == 0)
            and all(item.name != "*" for item in statement.names)
        ):
            statement.names.append(alias(name=name))
            return name
    module.body.insert(
        header_end(module=module),
        ImportFrom(module=source, names=[alias(name=name)], level=0),
    )
    return name


def module_classes(*, module: Module) -> frozenset[str]:
    """List the classes defined at the top level of a module.

    Args:
        module: Parsed module.

    Returns:
        Their names.

    """
    return frozenset(
        statement.name
        for statement in module.body
        if isinstance(statement, ClassDef)
    )


def ensure_names(
    *,
    module: Module,
    expression: expr,
    before: int,
    skip: frozenset[str] = frozenset(),
) -> None:
    """Import every known name an annotation uses but the module lacks.

    Names are renamed in place when they had to be imported under an alias.

    Args:
        module: Module to modify in place.
        expression: Annotation expression about to be written.
        before: Index of the statement that will use the annotation.
        skip: Names that already mean what the annotation means (classes the
            module defines itself) and must not be imported.

    """
    for node in walk(node=expression):
        if isinstance(node, Name) and node.id not in skip:
            source: str | None = Constants.known_imports.get(node.id)
            if source is not None:
                node.id = insert_import(
                    module=module,
                    source=source,
                    name=node.id,
                    before=before,
                )
