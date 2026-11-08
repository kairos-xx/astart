"""Place a new ``Final`` constant inside an existing ``Constants`` class.

The house convention keeps module constants in ``@final class Constants``.
When ``typing.add-final`` makes a module global ``Final`` and such a class
already exists, the constant joins that class and the module's uses become
``Constants.NAME``. Anything that could break stays a plain module global:
exported names, names reached by ``global``, names the class body or the
module's import-time code reads before the class exists, and name clashes.
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Global,
    Lambda,
    Load,
    Module,
    Name,
    Nonlocal,
    Pass,
    Store,
    expr,
    iter_child_nodes,
    iter_fields,
    stmt,
    walk,
)
from typing import TYPE_CHECKING, Final, cast, final

from astart.rules.imports import header_end, insert_import

if TYPE_CHECKING:
    from collections.abc import Mapping


@final
class Constants:
    """Group module-level constants.

    Attributes:
        class_name: Name of the class constants are grouped into.
        exports: Name of the module's export list.
        section: Heading of the docstring section that lists attributes.
        placeholder: Description written for a newly documented constant.
        class_doc: Docstring text written into the generated class.

    """

    class_name: Final[str] = "Constants"
    exports: Final[str] = "__all__"
    section: Final[str] = "Attributes:"
    class_doc: Final[str] = (
        "Group module-level constants.\n\n    Attributes:\n\n    "
    )
    placeholder: Final[str] = "Grouped module constant."


def _parents(*, module: Module) -> dict[int, AST]:
    """Map every node to its parent.

    Args:
        module: Parsed module.

    Returns:
        Parent by node identity.

    """
    return {
        id(child): parent
        for parent in walk(node=module)
        for child in iter_child_nodes(node=parent)
    }


def _deferred(*, node: AST, parents: Mapping[int, AST]) -> bool:
    """Tell whether a node runs only when a function is called.

    Decorators, default values and annotations of a function run when it is
    defined, so only the body counts as deferred.

    Args:
        node: Expression node.
        parents: Parent by node identity.

    Returns:
        ``True`` when the node sits in a function or lambda body.

    """
    child: AST = node
    parent: AST | None = parents.get(id(child))
    while parent is not None:
        if isinstance(parent, (FunctionDef, AsyncFunctionDef)) and any(
            child is item for item in parent.body
        ):
            return True
        if isinstance(parent, Lambda) and child is parent.body:
            return True
        child, parent = parent, parents.get(id(parent))
    return False


def _within(*, node: AST, outer: AST, parents: Mapping[int, AST]) -> bool:
    """Tell whether a node lies inside another one.

    Args:
        node: Inner candidate.
        outer: Outer candidate.
        parents: Parent by node identity.

    Returns:
        ``True`` when ``outer`` is an ancestor of ``node``.

    """
    current: AST | None = parents.get(id(node))
    while current is not None:
        if current is outer:
            return True
        current = parents.get(id(current))
    return False


def _top_index(
    *,
    node: AST,
    module: Module,
    parents: Mapping[int, AST],
) -> int:
    """Find the module-body statement that contains a node.

    Args:
        node: Any node of the module.
        module: Parsed module.
        parents: Parent by node identity.

    Returns:
        Its index in ``module.body``.

    """
    current: AST = node
    while parents.get(id(current)) is not module:
        current = parents[id(current)]
    return next(
        index
        for index, statement in enumerate(iterable=module.body)
        if statement is current
    )


def _claimed(*, cls: ClassDef) -> set[str]:
    """List the names a class body already defines.

    Args:
        cls: The grouping class.

    Returns:
        Attribute, method and nested-class names.

    """
    names: set[str] = set()
    for item in cls.body:
        if isinstance(item, (FunctionDef, AsyncFunctionDef, ClassDef)):
            names.add(item.name)
        for node in walk(node=item):
            if isinstance(node, Name) and isinstance(node.ctx, Store):
                names.add(node.id)
    return names


def _exported(*, module: Module, name: str) -> bool:
    """Tell whether the module lists a name in ``__all__``.

    Args:
        module: Parsed module.
        name: Constant name.

    Returns:
        ``True`` when any assignment to ``__all__`` mentions the name.

    """
    for statement in module.body:
        if isinstance(statement, (Assign, AnnAssign, AugAssign)):
            targets: list[expr] = (
                statement.targets
                if isinstance(statement, Assign)
                else [statement.target]
            )
            if any(
                isinstance(target, Name) and target.id == Constants.exports
                for target in targets
            ) and any(
                isinstance(node, Constant) and node.value == name
                for node in walk(node=statement)
            ):
                return True
    return False


def find_group(
    *,
    module: Module,
    statement: AST,
    name: str,
    counts: Mapping[str, int],
) -> ClassDef | None:
    """Find the ``Constants`` class a new constant can safely join.

    Args:
        module: Parsed module.
        statement: The module-level statement that defines the constant.
        name: Constant name.
        counts: Module binding counts.

    Returns:
        The class, or ``None`` when there is none or moving is unsafe.

    """
    classes: list[ClassDef] = [
        item
        for item in module.body
        if isinstance(item, ClassDef) and item.name == Constants.class_name
    ]
    if len(classes) != 1 or counts.get(Constants.class_name) != 1:
        return None
    cls: ClassDef = classes[0]
    if (
        name in _claimed(cls=cls)
        or _exported(module=module, name=name)
        or any(
            isinstance(node, (Global, Nonlocal)) and name in node.names
            for node in walk(node=module)
        )
    ):
        return None
    parents: dict[int, AST] = _parents(module=module)
    class_index: int = next(
        index for index, item in enumerate(iterable=module.body) if item is cls
    )
    for node in walk(node=module):
        if not (isinstance(node, Name) and node.id == name):
            continue
        if _within(node=node, outer=statement, parents=parents):
            continue
        if not isinstance(node.ctx, Load):
            return None
        deferred: bool = _deferred(node=node, parents=parents)
        index: int = _top_index(node=node, module=module, parents=parents)
        if not deferred and (
            index <= class_index
            or _within(node=node, outer=cls, parents=parents)
        ):
            return None
    return cls


def creatable(
    *,
    module: Module,
    statement: AST,
    counts: Mapping[str, int],
) -> bool:
    """Tell whether a ``Constants`` class could be created for a constant.

    Args:
        module: Parsed module.
        statement: The constant's statement.
        counts: Module binding counts.

    Returns:
        ``True`` when nothing in the module is bound to ``Constants`` and the
        statement is a module-level annotated literal.

    """
    return (
        counts.get(Constants.class_name) is None
        and not any(
            isinstance(item, ClassDef) and item.name == Constants.class_name
            for item in module.body
        )
        and any(item is statement for item in module.body)
        and isinstance(statement, AnnAssign)
        and isinstance(statement.value, Constant)
    )


def create_group(*, module: Module) -> ClassDef:
    """Create an empty ``@final class Constants`` after the leading imports.

    Args:
        module: Parsed module, modified in place.

    Returns:
        The new class, ready for :func:`move_into`.

    """
    local: str = insert_import(
        module=module,
        source="typing",
        name="final",
        before=len(module.body),
    )
    created: ClassDef = ClassDef(
        name=Constants.class_name,
        bases=[],
        keywords=[],
        body=[
            Expr(value=Constant(value=Constants.class_doc)),
            Pass(),
        ],
        decorator_list=[Name(id=local, ctx=Load())],
        type_params=[],
    )
    module.body.insert(header_end(module=module), created)
    return created


def _replace(*, parent: AST, old: AST, new: AST) -> None:
    """Swap one child of a node for another.

    Args:
        parent: Node that holds the child.
        old: Child to replace.
        new: Replacement.

    """
    for field, value in iter_fields(node=parent):
        if value is old:
            setattr(parent, field, new)
            return
        if isinstance(value, list):
            children: list[AST] = cast(typ="list[AST]", val=value)
            for position, item in enumerate(iterable=children):
                if item is old:
                    children[position] = new
                    return


def _document(*, cls: ClassDef, name: str) -> None:
    """Add the constant to the class docstring's ``Attributes:`` section.

    The docstring is left alone when it has no such section or already
    documents the name.

    Args:
        cls: The grouping class.
        name: Constant name.

    """
    first: stmt | None = cls.body[0] if cls.body else None
    if not (
        isinstance(first, Expr)
        and isinstance(first.value, Constant)
        and isinstance(first.value.value, str)
    ):
        return
    lines: list[str] = first.value.value.split(sep="\n")
    header: int | None = next(
        (
            index
            for index, line in enumerate(iterable=lines)
            if line.strip() == Constants.section
        ),
        None,
    )
    if header is None or header + 1 >= len(lines):
        return
    entry: str = lines[header + 1]
    if not entry.strip():
        title: str = lines[header]
        pad: str = title[: len(title) - len(title.lstrip())]
        lines.insert(
            header + 1,
            f"{pad}    {name}: {Constants.placeholder}",
        )
        first.value.value = "\n".join(lines)
        return
    indent: str = entry[: len(entry) - len(entry.lstrip())]
    end: int = header + 1
    while end < len(lines) and lines[end].strip():
        end += 1
    if any(line.startswith(f"{indent}{name}:") for line in lines[header:end]):
        return
    lines.insert(end, f"{indent}{name}: {Constants.placeholder}")
    first.value.value = "\n".join(lines)


def move_into(
    *,
    module: Module,
    cls: ClassDef,
    statement: stmt,
    name: str,
) -> None:
    """Move a constant's statement into the class and rewrite its uses.

    Args:
        module: Parsed module.
        cls: The grouping class from :func:`find_group`.
        statement: The constant's (now annotated) statement.
        name: Constant name.

    """
    parents: dict[int, AST] = _parents(module=module)
    for node in walk(node=module):
        if (
            isinstance(node, Name)
            and node.id == name
            and not _within(node=node, outer=statement, parents=parents)
        ):
            _replace(
                parent=parents[id(node)],
                old=node,
                new=Attribute(
                    value=Name(id=Constants.class_name, ctx=Load()),
                    attr=name,
                    ctx=Load(),
                ),
            )
    module.body[:] = [item for item in module.body if item is not statement]
    position: int = 0
    for index, item in enumerate(iterable=cls.body):
        is_doc: bool = (
            index == 0
            and isinstance(item, Expr)
            and isinstance(item.value, Constant)
        )
        if is_doc or isinstance(item, (AnnAssign, Assign)):
            position = index + 1
        else:
            break
    cls.body.insert(position, statement)
    cls.body[:] = [
        item
        for item in cls.body
        if not (isinstance(item, Pass) and len(cls.body) > 1)
    ]
    _document(cls=cls, name=name)
