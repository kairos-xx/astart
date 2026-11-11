"""Typed access to attributes that Astart attaches to ``ast`` nodes.

The standard ``ast.AST`` stub declares neither keyword construction nor the
extra attributes Astart stores on nodes (inferred values, symbol identities).
These lowercase functions reach them through ``getattr`` and ``setattr`` with
a runtime-checked result, so call sites stay precise without any suppression.

"""

from __future__ import annotations

from ast import AST, unparse
from typing import TYPE_CHECKING, Final, cast, final

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


@final
class Constants:
    """Group module-level constants.

    Attributes:
        initializer (Final[str]): Grouped module constant.
        renderer (Final[str]): Grouped module constant.

    """

    initializer: Final[str] = "__init__"
    renderer: Final[str] = "unparse"


type FieldValue = (
    str
    | bool
    | int
    | AST
    | Sequence[AST]
    | Sequence[str]
    | Sequence[int]
    | None
)


def read_attribute[T](*, node: AST, name: str, kind: type[T]) -> T | None:
    """Return a dynamic attribute when present and of the expected class.

    Args:
        node (AST): Node that may carry the attribute.
        name (str): Attribute name.
        kind (type[T]): Class the attribute value must be an instance of.

    Returns:
        T | None: The value, or ``None`` when absent or of another class.

    """
    value: object = getattr(node, name, None)
    return value if isinstance(value, kind) else None


def write_attribute[T](*, node: AST, name: str, value: T) -> T:
    """Attach a dynamic attribute to ``node``.

    Args:
        node (AST): Node receiving the attribute.
        name (str): Attribute name.
        value (T): Value to store.

    Returns:
        T: ``value``, so a call can be used inline.

    """
    setattr(node, name, value)
    return value


def clear_attribute(*, node: AST, name: str) -> None:
    """Remove a dynamic attribute from ``node`` when it is present.

    Args:
        node (AST): Node that may carry the attribute.
        name (str): Attribute name.

    """
    if hasattr(node, name):
        delattr(node, name)


def initialize_node(*, node: AST, **fields: FieldValue) -> None:
    """Run the native ``ast.AST`` initializer with keyword fields.

    Args:
        node (AST): Node being constructed.
        **fields (FieldValue): Field and location values to store on the node.

    """
    initializer: Callable[..., None] = getattr(AST, Constants.initializer)
    initializer(node, **fields)


def list_items[T](*, value: T) -> list[T]:
    """Return the items of a list-valued attribute, or nothing otherwise.

    Args:
        value (T): Attribute value read from a node.

    Returns:
        list[T]: The list items as plain objects, or an empty list for other
            values.

    """
    if isinstance(value, list):
        return cast(typ="list[T]", val=value)
    return []


def render_source(*, tree: AST, on_format_conflict: str | None = None) -> str:
    """Render ``tree`` to source, preserving formatting when it can.

    Args:
        tree (AST): Module or node to render.
        on_format_conflict (str | None): Optional conflict policy for formatted
            trees.

    Returns:
        str: Source text from the tree's own formatter, or ``ast.unparse``.

    """
    renderer: Callable[..., str] | None = getattr(
        tree,
        Constants.renderer,
        None,
    )
    if renderer is None:
        return unparse(ast_obj=tree)
    options: dict[str, bool | str] = {"preserve_formatting": True}
    if on_format_conflict is not None:
        options["on_format_conflict"] = on_format_conflict
    return renderer(**options)


def reclassify_node(
    *,
    node: AST,
    kind: type[AST],
    removed: Sequence[str],
    fields: Mapping[str, FieldValue],
) -> None:
    """Change a native node's syntax kind without replacing its identity.

    Args:
        node (AST): Authoritative node whose metadata must survive.
        kind (type[AST]): Replacement native AST class.
        removed (Sequence[str]): Obsolete syntax-field names to discard.
        fields (Mapping[str, FieldValue]): Replacement syntax fields; unrelated
            metadata is retained.

    """
    attributes: dict[str, object] = vars(node)
    for name in removed:
        attributes.pop(name, None)
    attributes.update(fields)
    object.__setattr__(node, "__class__", kind)
