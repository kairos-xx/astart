"""Semantic AST construction, rendering, and traversal helpers.

This module replaces source-string round-tripping (``ast.parse`` /
``ast.unparse``) and flat tree scans (``ast.walk``) with direct, semantic
operations on the AST graph:

* :func:`build_annotation` constructs an annotation expression node from a
  type-expression string without invoking the Python parser.
* :func:`render_annotation` renders an annotation expression node back to a
  canonical type-expression string without invoking the unparser.
* :func:`nodes_of_type` collects descendant nodes of given types through a
  semantic visitor instead of a flat ``walk`` scan.

The annotation grammar handled here is the closed set of forms the inference
engine emits: dotted names, subscripts (``a[b, c]``), parameter lists
(``Callable[[int], str]``), unions (``a | b``), ellipses (``...``), string
forward references, function calls (``ParamSpec('P')``), and
numeric/boolean/``None`` literals.
"""

from __future__ import annotations

from ast import (
    AST,
    Attribute,
    BinOp,
    BitOr,
    Call,
    Constant,
    List,
    Load,
    Name,
    NodeVisitor,
    Subscript,
    Tuple,
    expr,
    iter_fields,
)
from typing import TYPE_CHECKING, Final, cast, final

if TYPE_CHECKING:
    from types import EllipsisType


@final
class Constants:
    """Group module-level constants.

    Attributes:
        ident_start: Grouped module constant.
        ident_body: Grouped module constant.
        digits: Grouped module constant.
        constant_names: Grouped module constant.

    """

    ident_start: Final[frozenset[str]] = frozenset(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",
    )
    ident_body: Final[frozenset[str]] = ident_start | frozenset("0123456789")
    digits: Final[frozenset[str]] = frozenset("0123456789")
    constant_names: Final[dict[str, bool | None]] = {
        "None": None,
        "True": True,
        "False": False,
    }


class _Token:
    """A single lexical token from a type-expression string."""

    __slots__ = ("kind", "value")

    def __init__(self, *, kind: str, value: str) -> None:
        """Init.

        Args:
            kind: Kind supplied to this operation.
            value: Parsed annotation expression.

        """
        self.kind = kind
        self.value = value


def _tokenize(text: str) -> list[_Token]:
    """Split a type-expression string into tokens.

    Args:
        text: Text supplied as str for this operation.

    Returns:
        list[_Token] produced by this operation.

    Raises:
        ValueError: If this operation cannot satisfy its documented contract.

    """
    tokens: list[_Token] = []
    index: int = 0
    length: int = len(text)
    while index < length:
        char: str = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("...", index):
            tokens.append(_Token(kind="ellipsis", value="..."))
            index += 3
            continue
        if char in "[],|.()":
            tokens.append(_Token(kind=char, value=char))
            index += 1
            continue
        if char in {"'", '"'}:
            end: int = text.index(char, index + 1)
            tokens.append(_Token(kind="string", value=text[index + 1 : end]))
            index = end + 1
            continue
        if char in Constants.digits:
            start: int = index
            while index < length and text[index] in Constants.digits:
                index += 1
            tokens.append(_Token(kind="number", value=text[start:index]))
            continue
        if char in Constants.ident_start:
            start = index
            while index < length and text[index] in Constants.ident_body:
                index += 1
            tokens.append(_Token(kind="name", value=text[start:index]))
            continue
        msg: str = f"Unexpected character {char!r} in annotation {text!r}"
        raise ValueError(msg)
    return tokens


class _AnnotationParser:
    """Recursive-descent parser building annotation AST nodes."""

    def __init__(self, *, tokens: list[_Token], text: str) -> None:
        """Init.

        Args:
            text: Original annotation text.
            tokens: Token sequence used to parse the annotation.

        """
        self._tokens = tokens
        self._text = text
        self._position = 0

    def parse(self) -> expr:
        """Parse the full token stream into one annotation expression.

        Returns:
            expr produced by this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        node: expr = self._union()
        if self._position != len(self._tokens):
            msg: str = f"Trailing tokens in annotation {self._text!r}"
            raise ValueError(msg)
        return node

    def _peek(self) -> _Token | None:
        """Peek.

        Returns:
            Next annotation token, or None at the end of input.

        """
        if self._position < len(self._tokens):
            return self._tokens[self._position]
        return None

    def _advance(self) -> _Token:
        """Advance.

        Returns:
            Next annotation token, or None at the end of input.

        """
        token: _Token = self._tokens[self._position]
        self._position += 1
        return token

    def _union(self) -> expr:
        """Union.

        Returns:
            Parsed annotation expression.

        """
        node: expr = self._postfix()
        while True:
            token: _Token | None = self._peek()
            if token is None or token.kind != "|":
                return node
            self._advance()
            node = BinOp(left=node, op=BitOr(), right=self._postfix())

    def _postfix(self) -> expr:
        """Postfix.

        Returns:
            Parsed annotation expression.

        """
        node: expr = self._atom()
        while True:
            token: _Token | None = self._peek()
            if token is None:
                return node
            if token.kind == "[":
                node = self._subscript(value=node)
            elif token.kind == ".":
                self._advance()
                node = Attribute(
                    value=node,
                    attr=self._advance().value,
                    ctx=Load(),
                )
            elif token.kind == "(":
                node = self._call(func=node)
            else:
                return node

    def _subscript(self, *, value: expr) -> Subscript:
        """Subscript.

        Args:
            value: Parsed annotation expression.

        Returns:
            Parsed annotation expression.

        """
        self._advance()
        arguments: list[expr] = self._arguments()
        self._advance()
        single: Final[int] = 1
        slice_node: expr = (
            arguments[0]
            if len(arguments) == single
            else Tuple(elts=arguments, ctx=Load())
        )
        return Subscript(value=value, slice=slice_node, ctx=Load())

    def _call(self, *, func: expr) -> Call:
        """Call.

        Args:
            func: Callable expression being parsed.

        Returns:
            Parsed annotation expression.

        """
        self._advance()
        arguments: list[expr] = self._call_arguments()
        self._advance()
        return Call(func=func, args=arguments, keywords=[])

    def _arguments(self) -> list[expr]:
        """Arguments.

        Returns:
            Parsed argument expressions in source order.

        """
        arguments: list[expr] = []
        token: _Token | None = self._peek()
        if token is not None and token.kind == "]":
            return arguments
        arguments.append(self._union())
        while True:
            token = self._peek()
            if token is None or token.kind != ",":
                return arguments
            self._advance()
            token = self._peek()
            if token is not None and token.kind == "]":
                return arguments
            arguments.append(self._union())

    def _call_arguments(self) -> list[expr]:
        """Call arguments.

        Returns:
            Parsed argument expressions in source order.

        """
        arguments: list[expr] = []
        token: _Token | None = self._peek()
        if token is not None and token.kind == ")":
            return arguments
        arguments.append(self._union())
        while True:
            token = self._peek()
            if token is None or token.kind != ",":
                return arguments
            self._advance()
            token = self._peek()
            if token is not None and token.kind == ")":
                return arguments
            arguments.append(self._union())

    def _atom(self) -> expr:
        """Atom.

        Returns:
            Parsed annotation expression.

        Raises:
            ValueError: Raised when the annotation cannot be parsed.

        """
        token: _Token | None = self._peek()
        if token is None:
            msg: str = f"Unexpected end of annotation {self._text!r}"
            raise ValueError(msg)
        if token.kind == "[":
            self._advance()
            elements: list[expr] = self._arguments()
            self._advance()
            return List(elts=elements, ctx=Load())
        self._advance()
        if token.kind == "ellipsis":
            return Constant(value=...)
        if token.kind == "string":
            return Constant(value=token.value)
        if token.kind == "number":
            return Constant(value=int(token.value))
        if token.kind == "name":
            if token.value in Constants.constant_names:
                return Constant(value=Constants.constant_names[token.value])
            return Name(id=token.value, ctx=Load())
        msg = f"Unexpected token {token.value!r} in {self._text!r}"
        raise ValueError(msg)


def build_annotation(text: str) -> expr:
    """Build an annotation expression node from a type string.

    This is a semantic replacement for ``ast.parse(text, mode="eval").body``
    restricted to the type-expression grammar emitted by the inference
    engine. It never invokes the Python parser.


    Args:
        text: Text supplied as str for this operation.

    Returns:
        expr produced by this operation.

    """
    return _AnnotationParser(tokens=_tokenize(text=text), text=text).parse()


def render_annotation(node: AST | None) -> str:
    """Render an annotation expression node to a canonical type string.

    This is a semantic replacement for ``ast.unparse`` over the annotation
    grammar. ``None`` renders as ``"object"`` to mirror an absent annotation.


    Args:
        node: The node examined while render an annotation expression node to a
            canonical type string.

    Returns:
        Rendered source text produced by this operation.

    Raises:
        ValueError: If this operation cannot satisfy its documented contract.

    """
    if node is None:
        return "object"
    leaf: str | None = _render_leaf(node=node)
    if leaf is not None:
        return leaf
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        left: str = render_annotation(node=node.left)
        right: str = render_annotation(node=node.right)
        return f"{left} | {right}"
    if isinstance(node, Subscript):
        base: str = render_annotation(node=node.value)
        return f"{base}[{_render_slice(node=node.slice)}]"
    if isinstance(node, List):
        return f"[{_render_elements(elements=node.elts)}]"
    if isinstance(node, Tuple):
        return _render_elements(elements=node.elts)
    msg: str = f"Cannot render annotation node {type(node).__name__}"
    raise ValueError(msg)


def _render_leaf(*, node: AST) -> str | None:
    """Render a leaf annotation node, or ``None`` if it is composite.

    Args:
        node: The node examined while render a leaf annotation node, or
            ``None`` if it is composite.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Constant):
        return _render_constant(value=node.value)
    if isinstance(node, Attribute):
        return f"{render_annotation(node=node.value)}.{node.attr}"
    return None


def _render_constant(
    *,
    value: str | bytes | complex | bool | None | EllipsisType,
) -> str:
    """Render a constant annotation value to its type-string form.

    Args:
        value: The value examined while render a constant annotation value to
            its type-string form.

    Returns:
        Rendered source text produced by this operation.

    """
    if value is None:
        return "None"
    if value is ...:
        return "..."
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(object=value)
    if isinstance(value, str):
        return repr(value)
    return repr(value)


def _render_slice(*, node: expr) -> str:
    """Render a subscript slice, flattening tuple slices to a comma list.

    Args:
        node: The node examined while render a subscript slice, flattening
            tuple slices to a comma list.

    Returns:
        Rendered source text produced by this operation.

    """
    if isinstance(node, Tuple):
        return _render_elements(elements=node.elts)
    return render_annotation(node=node)


def _render_elements(*, elements: list[expr]) -> str:
    """Render a comma-separated list of annotation elements.

    Args:
        elements: Elements supplied as list[expr] for this operation.

    Returns:
        Rendered source text produced by this operation.

    """
    return ", ".join(render_annotation(node=element) for element in elements)


class _TypeCollector[T: AST](NodeVisitor):
    """Collect descendant nodes matching a set of types in document order."""

    def __init__(self, *, types: tuple[type[T], ...]) -> None:
        """Init.

        Args:
            types: AST node classes to collect during traversal.

        """
        self._types = types
        self.found: list[T] = []

    def visit(self, node: AST) -> None:
        """Record matching nodes and recurse into every child.

        Args:
            node: The node examined while record matching nodes and recurse
                into every child.

        """
        if isinstance(node, self._types):
            self.found.append(node)
        self.generic_visit(node=node)


def nodes_of_type[T: AST](*, root: AST, types: tuple[type[T], ...]) -> list[T]:
    """Return all nodes of the given types reachable from ``root``.

    This is a semantic replacement for ``[n for n in ast.walk(root)
    if isinstance(n, types)]`` using a visitor rather than a flat scan.
    The root itself is included when it matches.


    Args:
        root: Filesystem path identifying the root.
        types: Collection of types supplied for this operation.

    Returns:
        list[T] produced by this operation.

    """
    collector: _TypeCollector[T] = _TypeCollector(types=types)
    collector.visit(node=root)
    return collector.found


def child_nodes(*, node: AST) -> list[AST]:
    """Return the direct child AST nodes of ``node``.

    This is a semantic replacement for ``ast.iter_child_nodes`` that reads
    structured fields rather than relying on the flat-scan helper.


    Args:
        node: The node examined while return the direct child AST nodes of
            ``node``.

    Returns:
        list[AST] produced by this operation.

    """
    children: list[AST] = []
    for _name, value in iter_fields(node=node):
        if isinstance(value, AST):
            children.append(value)
        elif isinstance(value, list):
            field_items: list[object] = cast(typ="list[object]", val=value)
            children.extend(
                item for item in field_items if isinstance(item, AST)
            )
    return children
