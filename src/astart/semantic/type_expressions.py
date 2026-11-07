"""Dependency-free, loss-aware parsing of structured Python type expressions.

The representation models structured annotations as immutable type shapes
shared by the integrated source and semantic inference subsystems.
No annotation is evaluated as Python code.
"""

from __future__ import annotations

from ast import (
    AST,
    Attribute,
    BinOp,
    BitOr,
    Constant,
    List,
    Name,
    Subscript,
    Tuple,
    expr,
    parse,
    unparse,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Callable


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TypeExpression:
    """A loss-aware structured Python annotation expression.

    Attributes:
        arguments: Arguments retained as tuple[TypeExpression, ...] by this
            instance.
        name: Identifier used to refer to the name.

    """

    name: str
    arguments: tuple[TypeExpression, ...] = ()

    def __str__(self) -> str:
        """Render a normalized annotation without executing it."""
        if self.name == "union":
            return " | ".join(str(object=item) for item in self.arguments)
        if self.name == "parameters":
            return (
                "["
                + ", ".join(str(object=item) for item in self.arguments)
                + "]"
            )
        return (
            (
                f"{self.name}"
                f"["
                f"{', '.join((str(object=item) for item in self.arguments))}"
                f"]"
            )
            if self.arguments
            else self.name
        )


@final
class TypeExpressionCodec:
    """Parse annotation ASTs into deterministic structural representations."""

    @classmethod
    def from_source(cls, *, source: str) -> TypeExpression:
        """Parse source as an expression without evaluating its contents.

        Raises:
            SyntaxError: The annotation is syntactically invalid.



        Args:
            source: The source examined while parse source as an expression
                without evaluating its contents.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.from_ast(
            node=parse(source=source, mode="eval").body,
        )

    @classmethod
    def from_ast(cls, *, node: AST) -> TypeExpression:
        """Convert supported annotation syntax to a structural expression.

        Dispatches on the lowercase node class name to the matching
        ``convert_<kind>`` function; unsupported kinds keep their source text.


        Args:
            node: The node examined while convert supported annotation syntax
                to a structural expression.

        Returns:
            TypeExpression produced by this operation.

        """
        handler: Callable[..., TypeExpression] = getattr(
            TypeExpressionCodec,
            f"convert_{type(node).__name__.lower()}",
            cls.convert_other,
        )
        return handler(node=node)

    @classmethod
    def convert_constant(cls, *, node: Constant) -> TypeExpression:
        """Convert ``None``, ``...``, forward references and literals.

        Args:
            node: The node examined while convert ``None``, ``...``, forward
                references and literals.

        Returns:
            TypeExpression produced by this operation.

        """
        if node.value is None:
            return TypeExpression(name="None")
        if node.value is Ellipsis:
            return TypeExpression(name="...")
        if isinstance(node.value, str):
            # A string annotation is a forward reference. Its contents
            # must be parsed as annotation syntax, never executed.
            try:
                return cls.from_source(source=node.value)
            except SyntaxError:
                return TypeExpression(name=repr(node.value))
        return TypeExpression(name=repr(node.value))

    @classmethod
    def convert_binop(cls, *, node: BinOp) -> TypeExpression:
        """Convert ``A | B`` unions; other operators stay opaque.

        Args:
            node: The node examined while convert ``A | B`` unions; other
                operators stay opaque.

        Returns:
            TypeExpression produced by this operation.

        """
        if not isinstance(node.op, BitOr):
            return cls.convert_other(node=node)
        return cls.union(
            members=(
                cls.from_ast(node=node.left),
                cls.from_ast(node=node.right),
            ),
        )

    @classmethod
    def convert_sequence(cls, *, items: list[expr]) -> TypeExpression:
        """Convert list or tuple elements into a parameter list.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return TypeExpression(
            name="parameters",
            arguments=tuple(cls.from_ast(node=item) for item in items),
        )

    @classmethod
    def convert_list(cls, *, node: List) -> TypeExpression:
        """Convert a list of parameters.

        Args:
            node: The node examined while convert a list of parameters.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.convert_sequence(items=node.elts)

    @classmethod
    def convert_tuple(cls, *, node: Tuple) -> TypeExpression:
        """Convert a tuple of parameters.

        Args:
            node: The node examined while convert a tuple of parameters.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.convert_sequence(items=node.elts)

    @classmethod
    def convert_subscript(cls, *, node: Subscript) -> TypeExpression:
        """Convert a subscripted generic, ``Optional`` or ``Union``.

        Args:
            node: The node examined while convert a subscripted generic,
                ``Optional`` or ``Union``.

        Returns:
            TypeExpression produced by this operation.

        """
        base: TypeExpression = cls.from_ast(node=node.value)
        members: tuple[AST, ...] = (
            tuple(node.slice.elts)
            if isinstance(node.slice, Tuple)
            else (node.slice,)
        )
        arguments: tuple[TypeExpression, ...] = tuple(
            TypeExpression(name=repr(item.value))
            if (
                base.name in ("Literal", "typing.Literal")
                or (
                    base.name in ("Annotated", "typing.Annotated")
                    and index > 0
                )
            )
            and isinstance(item, Constant)
            and isinstance(item.value, str)
            else cls.from_ast(node=item)
            for index, item in enumerate(iterable=members)
        )
        if (
            base.name in ("Optional", "typing.Optional")
            and len(arguments) == 1
        ):
            return cls.union(
                members=(arguments[0], TypeExpression(name="None")),
            )
        if base.name in ("Union", "typing.Union"):
            return cls.union(members=arguments)
        return TypeExpression(name=base.name, arguments=arguments)

    @staticmethod
    def convert_other(*, node: AST) -> TypeExpression:
        """Keep unsupported syntax, including calls, as opaque source.

        Args:
            node: The node examined while keep unsupported syntax, including
                calls, as opaque source.

        Returns:
            TypeExpression produced by this operation.

        """
        return TypeExpression(name=unparse(ast_obj=node))

    @staticmethod
    def convert_name(*, node: Name) -> TypeExpression:
        """Convert a bare name.

        Args:
            node: The node examined while convert a bare name.

        Returns:
            TypeExpression produced by this operation.

        """
        return TypeExpression(name=node.id)

    @staticmethod
    def convert_attribute(*, node: Attribute) -> TypeExpression:
        """Convert a dotted name.

        Args:
            node: The node examined while convert a dotted name.

        Returns:
            TypeExpression produced by this operation.

        """
        return TypeExpression(name=unparse(ast_obj=node))

    @staticmethod
    def union(*, members: tuple[TypeExpression, ...]) -> TypeExpression:
        """Flatten and canonicalize union members without numeric promotion.

        Args:
            members: Members supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        all_members: dict[str, TypeExpression] = {}
        for member in members:
            for part in (
                member.arguments if member.name == "union" else (member,)
            ):
                all_members[str(object=part)] = part
        ordered: tuple[TypeExpression, ...] = tuple(
            all_members[key]
            for key in sorted(
                all_members,
                key=lambda key: (key == "None", key),
            )
        )
        return (
            ordered[0]
            if len(ordered) == 1
            else TypeExpression(name="union", arguments=ordered)
        )

    @staticmethod
    def required_imports(*, expression: TypeExpression) -> frozenset[str]:
        """Return standard typing names needed to render an expression.

        Args:
            expression: The expression examined while return standard typing
                names needed to render an expression.

        Returns:
            frozenset[str] produced by this operation.

        """
        known: frozenset[str] = frozenset(
            (
                "Annotated",
                "Callable",
                "ClassVar",
                "Final",
                "Literal",
                "ParamSpec",
                "Protocol",
                "TypeVar",
                "Unpack",
                "Never",
                "Self",
                "Required",
                "NotRequired",
                "TypeGuard",
                "TypeIs",
            ),
        )
        pending: list[TypeExpression] = [expression]
        found: set[str] = set()
        while pending:
            current: TypeExpression = pending.pop()
            if current.name in known:
                found.add(current.name)
            pending.extend(current.arguments)
        return frozenset(found)
