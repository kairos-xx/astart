"""Parentheses preservation for AST unparsing.

This module re-inserts explicit parentheses into unparsed source that were
present in the original source but are normally discarded by Python's AST.

"""

from __future__ import annotations

from ast import (
    AST,
    Load,
    Name,
    copy_location,
    fix_missing_locations,
    iter_fields,
    unparse,
)
from copy import copy
from types import EllipsisType
from typing import Final

type CloneValue = (
    AST
    | str
    | int
    | float
    | complex
    | bytes
    | bool
    | None
    | EllipsisType
    | list[CloneValue]
    | tuple[CloneValue, ...]
    | frozenset[CloneValue]
)


class ParenthesizedNodeCloner:
    """Cloner that replaces custom nodes with unparse-safe placeholders.

    Attributes:
        counter (int): Counter retained as int by this instance.
        placeholder_prefix (Final[str]): Placeholder prefix retained as
            Final[str] by this instance.
        placeholders (dict[str, str]): Placeholders retained as dict[str, str]
            by this instance.

    """

    placeholder_prefix: Final[str] = "__parenthesized_expr_"
    placeholders: dict[str, str]
    counter: int

    def __init__(self) -> None:
        """Initialize the cloner."""
        self.placeholders = {}
        self.counter = 0

    def clone_for_stdlib_unparse(self, *, node: AST) -> AST:
        """Clone a custom tree into a stdlib-unparse-compatible tree.

        Args:
            node (AST): The node examined while clone a custom tree into a
                stdlib-unparse-compatible tree.

        Returns:
            AST: AST produced by this operation.

        """
        cloned: AST = self._clone_node(node=node)
        fix_missing_locations(node=cloned)
        return cloned

    def _clone_node(self, *, node: AST) -> AST:
        """Clone an AST node recursively.

        Args:
            node (AST): The node examined while clone an AST node recursively.

        Returns:
            AST: AST produced by this operation.

        """
        if node.__class__.__name__ == "Parenthesized":
            return self._placeholder_for_parenthesized(node=node)
        cloned: AST = copy(x=node)
        for field_name, field_value in iter_fields(node=node):
            setattr(cloned, field_name, self._clone_value(value=field_value))
        return copy_location(new_node=cloned, old_node=node)

    def _clone_value(self, *, value: CloneValue) -> CloneValue:
        """Clone a field value recursively.

        Args:
            value (CloneValue): The value examined while clone a field value
                recursively.

        Returns:
            CloneValue: CloneValue produced by this operation.

        """
        if isinstance(value, AST):
            return self._clone_node(node=value)
        if isinstance(value, list):
            cloned: list[CloneValue] = []
            for item in value:
                if isinstance(item, AST):
                    cloned.append(self._clone_node(node=item))
                elif isinstance(item, list):
                    cloned.append(
                        self._clone_value(
                            value=item,
                        ),
                    )
                else:
                    cloned.append(item)
            return cloned
        return value

    def _placeholder_for_parenthesized(self, *, node: AST) -> Name:
        """Create a placeholder Name node for a Parenthesized node.

        Args:
            node (AST): The node examined while create a placeholder
                Name node for a Parenthesized node.

        Returns:
            Name: Name produced by this operation.

        """
        placeholder: str = f"__parenthesized_expr_{self.counter}__"
        self.counter += 1
        inner: AST | None = getattr(node, "value", None)
        rendered: str = (
            ParenthesizedRenderer().render(node=inner)
            if inner is not None
            else ""
        )
        self.placeholders[placeholder] = f"({rendered})"
        name: Name = Name(id=placeholder, ctx=Load())
        return copy_location(new_node=name, old_node=node)


class ParenthesizedRenderer:
    """Unparses AST trees containing Parenthesized nodes.

    Uses a placeholder strategy: replaces Parenthesized nodes with unique
    Name identifiers, calls unparse on the cleaned tree, then
    substitutes the placeholders back with the parenthesized source.

    """

    def render(self, *, node: AST) -> str:
        """Render an AST tree to source code, preserving parentheses.

        Args:
            node (AST): The node examined while render an AST tree
                to source code, preserving parentheses.

        Returns:
            str: Rendered source text produced by this operation.

        """
        if node.__class__.__name__ == "Parenthesized":
            inner: AST | None = getattr(node, "value", None)
            return f"({self.render(node=inner)})" if inner is not None else ""
        cloner: ParenthesizedNodeCloner = ParenthesizedNodeCloner()
        source: str = unparse(
            ast_obj=(cloner.clone_for_stdlib_unparse(node=node)),
        )
        for placeholder, rendered in cloner.placeholders.items():
            source = source.replace(placeholder, rendered)
        return source
