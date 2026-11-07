"""Add the imports a synthesized annotation needs."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Mapping


@final
class Constants:
    """Group module-level constants.

    Attributes:
        known_imports: Names that may be imported automatically, with the
            module that defines each.
        constructors: Known imported classes whose call has the class as type.

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
        "Protocol": "typing",
        "TypeVar": "typing",
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


def bound_names(*, module: ast.Module) -> frozenset[str]:
    """Collect every name the module binds anywhere.

    Args:
        module: Parsed module.

    Returns:
        Imported, defined and assigned names.

    """
    names: set[str] = set()
    for node in ast.walk(node=module):
        match node:
            case ast.alias(name=name, asname=asname):
                names.add(asname or name.split(sep=".")[0])
            case (
                ast.ClassDef(name=name)
                | ast.FunctionDef(name=name)
                | ast.AsyncFunctionDef(name=name)
            ):
                names.add(name)
            case ast.Name(id=name, ctx=ast.Store() | ast.Del()):
                names.add(name)
            case ast.arg(arg=name):
                names.add(name)
            case _:
                continue
    return frozenset(names)


def _is_type_checking(*, test: ast.expr) -> bool:
    """Tell whether an ``if`` test is ``TYPE_CHECKING``.

    Args:
        test: Condition expression.

    Returns:
        ``True`` for ``TYPE_CHECKING`` and ``module.TYPE_CHECKING``.

    """
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _record_import(
    *,
    node: ast.Import | ast.ImportFrom,
    out: dict[str, tuple[str, str] | None],
) -> None:
    """Record the names an import statement binds.

    Args:
        node: Import statement.
        out: Bound names; a plain ``from`` import records its origin.

    """
    for alias in node.names:
        if isinstance(node, ast.ImportFrom):
            plain: bool = node.level == 0 and alias.asname is None
            out[alias.asname or alias.name] = (
                (node.module or "", alias.name) if plain else None
            )
        else:
            out[alias.asname or alias.name.split(".")[0]] = None


def _visit(*, node: ast.AST, out: dict[str, tuple[str, str] | None]) -> None:
    """Record the names a statement binds when the module runs.

    Definitions are recorded without entering their bodies; the body of an
    ``if TYPE_CHECKING:`` is skipped because it never runs.

    Args:
        node: Statement or expression to scan.
        out: Bound names; an import records ``(module, name)``, anything
            else records ``None``.

    """
    match node:
        case ast.If(test=test, orelse=orelse) if _is_type_checking(test=test):
            for statement in orelse:
                _visit(node=statement, out=out)
        case ast.ImportFrom() | ast.Import():
            _record_import(node=node, out=out)
        case (
            ast.FunctionDef(name=name)
            | ast.AsyncFunctionDef(name=name)
            | ast.ClassDef(name=name)
        ):
            out[name] = None
        case ast.Lambda() | ast.ListComp() | ast.SetComp() | ast.DictComp():
            pass
        case ast.Name(id=name, ctx=ast.Store() | ast.Del()):
            out[name] = None
        case _:
            for child in ast.iter_child_nodes(node):
                _visit(node=child, out=out)


def runtime_bindings(
    *,
    module: ast.Module,
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


def _header_end(*, module: ast.Module) -> int:
    """Find where a new top-level import belongs.

    Args:
        module: Module to inspect.

    Returns:
        The index after the docstring and the leading import block.

    """
    body: list[ast.stmt] = module.body
    index: int = 0
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        index = 1
    while index < len(body) and isinstance(
        body[index],
        (ast.Import, ast.ImportFrom),
    ):
        index += 1
    return index


def insert_import(
    *,
    module: ast.Module,
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
    bound = runtime_bindings(module=module, before=before)
    if name in bound:
        if bound[name] == (source, name):
            return name
        alias: str = f"_{name}"
        while alias in bound:
            alias = f"_{alias}"
        module.body.insert(
            _header_end(module=module),
            ast.ImportFrom(
                module=source,
                names=[ast.alias(name=name, asname=alias)],
                level=0,
            ),
        )
        return alias
    for statement in module.body[:before]:
        if (
            isinstance(statement, ast.ImportFrom)
            and statement.module == source
            and statement.level == 0
            and all(item.name != "*" for item in statement.names)
        ):
            statement.names.append(ast.alias(name=name))
            return name
    module.body.insert(
        _header_end(module=module),
        ast.ImportFrom(module=source, names=[ast.alias(name=name)], level=0),
    )
    return name


def ensure_names(
    *,
    module: ast.Module,
    expression: ast.expr,
    before: int,
) -> None:
    """Import every known name an annotation uses but the module lacks.

    Names are renamed in place when they had to be imported under an alias.

    Args:
        module: Module to modify in place.
        expression: Annotation expression about to be written.
        before: Index of the statement that will use the annotation.

    """
    for node in ast.walk(expression):
        if isinstance(node, ast.Name):
            source: str | None = Constants.known_imports.get(node.id)
            if source is not None:
                node.id = insert_import(
                    module=module,
                    source=source,
                    name=node.id,
                    before=before,
                )
