"""Match type-only AST patterns without interpreting annotation metadata."""

from __future__ import annotations

from ast import (
    Attribute,
    BinOp,
    BitOr,
    Constant,
    List,
    Load,
    Name,
    Starred,
    Subscript,
    Tuple,
    dump,
    expr,
    walk,
)
from copy import deepcopy
from dataclasses import dataclass
from typing import Final, final


@final
class Constants:
    """Define recognized type constructors and protected value contexts.

    Attributes:
        constructors (Final[frozenset[str]]): Known constructors with ordinary
            type argument slots.
        opaque (Final[frozenset[str]]): Special forms unsuitable for automatic
            alias extraction.
        dictionary_arity (Final[int]): Number of dictionary type arguments.

    """

    dictionary_arity: Final[int] = 2
    constructors: Final[frozenset[str]] = frozenset(
        {
            "list",
            "dict",
            "tuple",
            "set",
            "frozenset",
            "type",
            "Callable",
            "Sequence",
            "MutableSequence",
            "Mapping",
            "MutableMapping",
            "Iterable",
            "Iterator",
            "Collection",
            "Container",
            "Awaitable",
            "AsyncIterable",
            "AsyncIterator",
            "Coroutine",
            "Generator",
            "AsyncGenerator",
            "deque",
            "defaultdict",
            "Counter",
            "ChainMap",
            "Pattern",
            "Match",
            "KeysView",
            "ItemsView",
            "ValuesView",
            "Union",
            "Optional",
            "Annotated",
            "Literal",
            "ClassVar",
            "Final",
            "Required",
            "NotRequired",
            "ReadOnly",
            "TypeGuard",
            "TypeIs",
        },
    )
    opaque: Final[frozenset[str]] = frozenset(
        {
            "ClassVar",
            "Final",
            "Required",
            "NotRequired",
            "ReadOnly",
            "TypeGuard",
            "TypeIs",
            "Unpack",
            "Concatenate",
            "Self",
        },
    )


def key(*, node: expr) -> str:
    """Fingerprint syntax while excluding source coordinates.

    Args:
        node (expr): Type expression.

    Returns:
        str: Deterministic structural key.

    """
    return dump(node=node, include_attributes=False)


def head(*, node: expr) -> str:
    """Read a plain or qualified constructor's terminal identifier.

    Args:
        node (expr): Constructor expression.

    Returns:
        str: Identifier, or an empty string for dynamic expressions.

    """
    return (
        node.id
        if isinstance(node, Name)
        else (node.attr if isinstance(node, Attribute) else "")
    )


def alias_name(*, node: expr, parameters: tuple[str, ...] = ()) -> str:
    """Derive the release optimizer's structural declaration spelling.

    Args:
        node (expr): Alias body with any referenced aliases already expanded.
        parameters (tuple[str, ...]): Generic binders represented by the word
            Value.

    Returns:
        str: A deterministic PascalCase identifier derived from type structure.

    """
    if isinstance(node, Name):
        return "Value" if node.id in parameters else _pascal(text=node.id)
    if isinstance(node, Attribute):
        return _pascal(text=node.attr)
    if isinstance(node, Subscript):
        expected_arguments: int = 2
        arguments: tuple[expr, ...] = (
            tuple(node.slice.elts)
            if isinstance(node.slice, Tuple)
            else (node.slice,)
        )
        if (
            head(node=node.value) == "dict"
            and len(arguments) == expected_arguments
            and (isinstance(arguments[0], Name) and arguments[0].id == "str")
        ):
            return "Dict" + alias_name(
                node=arguments[1],
                parameters=parameters,
            )
        return alias_name(node=node.value, parameters=parameters) + "".join(
            alias_name(node=item, parameters=parameters) for item in arguments
        )
    if isinstance(node, (Tuple, List)):
        return "".join(
            alias_name(node=item, parameters=parameters) for item in node.elts
        )
    return (
        (
            alias_name(node=node.left, parameters=parameters)
            + "Or"
            + (alias_name(node=node.right, parameters=parameters))
        )
        if isinstance(node, BinOp) and isinstance(node.op, BitOr)
        else (
            _constant_name(node=node) if isinstance(node, Constant) else "Type"
        )
    )


def _pascal(*, text: str) -> str:
    """Normalize identifier words without a source-text regular expression.

    Args:
        text (str): Identifier or literal label.

    Returns:
        str: PascalCase words with no punctuation or leading number.

    """
    words: list[str] = "".join(
        character if character.isalnum() else " " for character in text
    ).split()
    result: str = "".join(word[:1].upper() + word[1:] for word in words)
    return result if result and not result[0].isdigit() else "Value" + result


def _constant_name(*, node: Constant) -> str:
    """Spell a literal component without generalizing its value semantics.

    Args:
        node (Constant): Constant in a protected literal/value position.

    Returns:
        str: Deterministic literal label.

    """
    if node.value is None:
        return "None"
    if isinstance(node.value, str):
        return _pascal(text=node.value) or "Text"
    if isinstance(node.value, bool):
        return "True" if node.value else "False"
    if isinstance(node.value, int):
        return f"Value{abs(node.value)}"
    return "Variadic" if node.value is Ellipsis else "Type"


def children(
    *,
    node: expr,
    constructors: frozenset[str] = Constants.constructors,
) -> tuple[expr, ...]:
    """Visit type slots while preserving Literal and Annotated payloads.

    Args:
        node (expr): Type expression at a type position.
        constructors (frozenset[str]): Constructors whose arguments are proven
            type slots.

    Returns:
        tuple[expr, ...]: Type children, excluding metadata
            and unknown constructor arguments.

    """
    if isinstance(node, Subscript):
        name: str = head(node=node.value)
        if name == "Annotated":
            return (
                (node.slice.elts[0],)
                if (isinstance(node.slice, Tuple) and node.slice.elts)
                else ()
            )
        return (
            (node.slice,)
            if (name in constructors and name != "Literal")
            else ()
        )
    if isinstance(node, (Tuple, List)):
        return tuple(node.elts)
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return node.left, node.right
    if isinstance(node, Starred):
        return (node.value,)
    return ()


def rebuild(*, node: expr, parts: tuple[expr, ...]) -> expr:
    """Construct fresh syntax with replacements only in known type slots.

    Args:
        node (expr): Original type syntax, never mutated.
        parts (tuple[expr, ...]): Replacements in children order.

    Returns:
        expr: Detached expression suitable for a staged annotation replacement.

    """
    if isinstance(node, Subscript) and parts:
        argument: expr = (
            Tuple(
                elts=[
                    parts[0],
                    *(deepcopy(x=item) for item in node.slice.elts[1:]),
                ],
                ctx=Load(),
            )
            if head(node=node.value) == "Annotated"
            and isinstance(node.slice, Tuple)
            else parts[0]
        )
        return Subscript(
            value=deepcopy(x=node.value),
            slice=argument,
            ctx=Load(),
        )
    if isinstance(node, Tuple):
        return Tuple(elts=list(parts), ctx=Load())
    if isinstance(node, List):
        return List(elts=list(parts), ctx=Load())
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return BinOp(left=parts[0], op=BitOr(), right=parts[1])
    if isinstance(node, Starred):
        return Starred(value=parts[0], ctx=Load())
    return deepcopy(x=node)


def normalize_type(
    *,
    node: expr,
    constructors: frozenset[str] = Constants.constructors,
) -> expr:
    """Merge a repeated tuple tail into one PEP 646 variadic run.

    Args:
        node (expr): Original annotation expression.
        constructors (frozenset[str]): Proven type-slot constructors at the
            source site.

    Returns:
        expr: Fresh type syntax, retaining distinct positional prefix
            contracts.

    """
    result: expr = rebuild(
        node=node,
        parts=tuple(
            normalize_type(node=child, constructors=constructors)
            for child in children(node=node, constructors=constructors)
        ),
    )
    if (
        not isinstance(result, Subscript)
        or head(node=result.value) != "tuple"
        or ("tuple" not in constructors or not isinstance(result.slice, Tuple))
    ):
        return result
    values: list[expr] = result.slice.elts
    if len(values) < Constants.dictionary_arity or any(
        isinstance(value, Starred)
        or (isinstance(value, Constant) and value.value is Ellipsis)
        for value in values
    ):
        return result
    start: int = len(values) - 1
    while start and key(node=values[start - 1]) == key(node=values[-1]):
        start -= 1
    if len(values) - start < Constants.dictionary_arity:
        return result
    repeated: Subscript = Subscript(
        value=Name(id="tuple", ctx=Load()),
        slice=Tuple(elts=[values[-1], Constant(value=Ellipsis)], ctx=Load()),
        ctx=Load(),
    )
    return (
        repeated
        if not start
        else Subscript(
            value=result.value,
            slice=Tuple(
                elts=[
                    *values[:start],
                    Starred(
                        value=repeated,
                        ctx=Load(),
                    ),
                ],
                ctx=Load(),
            ),
            ctx=Load(),
        )
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Pattern:
    """An alias template whose parameters bind only genuine type slots.

    Attributes:
        body (expr): Structural template.
        parameters (tuple[str, ...]): Ordinary, unconstrained generic binders.
        paramspecs (frozenset[str]): Binders representing complete callable
            signatures.
        constructors (frozenset[str]): Proven constructors allowed during
            structural matching.

    """

    body: expr
    parameters: tuple[str, ...] = ()
    paramspecs: frozenset[str] = frozenset()
    constructors: frozenset[str] = Constants.constructors

    def match(self, *, target: expr) -> tuple[expr, ...] | None:
        """Bind a target consistently without entering value payloads.

        Args:
            target (expr): Candidate type expression.

        Returns:
            tuple[expr, ...] | None:
                Actual argument expressions, or None when matching fails.

        """
        bindings: dict[str, expr] = {}
        return (
            tuple(bindings[name] for name in self.parameters)
            if (
                self._visit(
                    expected=self.body,
                    actual=target,
                    bindings=bindings,
                )
                and all(name in bindings for name in self.parameters)
            )
            else None
        )

    def _visit(
        self,
        *,
        expected: expr,
        actual: expr,
        bindings: dict[str, expr],
    ) -> bool:
        """Match one type position with consistent substitutions.

        Args:
            expected (expr): Template node.
            actual (expr): Target node.
            bindings (dict[str, expr]): Per-match parameter bindings.

        Returns:
            bool: Whether this subtree matches.

        """
        if isinstance(expected, Name) and expected.id in self.parameters:
            previous: expr | None = bindings.get(expected.id)
            if previous is None:
                bindings[expected.id] = actual
                return True
            return key(node=previous) == key(node=actual)
        first: tuple[expr, ...] = children(
            node=expected,
            constructors=self.constructors,
        )
        second: tuple[expr, ...] = children(
            node=actual,
            constructors=self.constructors,
        )
        if not first or len(first) != len(second):
            return key(node=expected) == key(node=actual)
        if key(node=rebuild(node=expected, parts=second)) != key(node=actual):
            return False
        return all(
            self._visit(expected=a, actual=b, bindings=bindings)
            for a, b in zip(first, second, strict=True)
        )


@final
class AntiUnifier:
    """Derive generic templates from matching type-only AST structures."""

    def __init__(
        self,
        *,
        constructors: frozenset[str] = Constants.constructors,
    ) -> None:
        """Create isolated deterministic parameter-allocation state.

        Args:
            constructors (frozenset[str]): Proven constructors with type-only
                argument slots.

        """
        self._bindings: dict[tuple[str, str], str] = {}
        self._reserved: set[str] = set()
        self._constructors: frozenset[str] = constructors

    def create(self, *, left: expr, right: expr) -> Pattern | None:
        """Anti-unify a pair without generalizing constructors or metadata.

        Args:
            left (expr): First composite annotation.
            right (expr): Second composite annotation.

        Returns:
            Pattern | None:
                A fresh generic template, or None for incompatible structures.

        """
        self._bindings.clear()
        self._reserved = {
            node.id
            for root in (left, right)
            for node in walk(node=root)
            if isinstance(node, Name)
        }
        body: expr | None = self._merge(left=left, right=right, root=True)
        return (
            Pattern(
                body=body,
                parameters=tuple(self._bindings.values()),
                constructors=self._constructors,
            )
            if body is not None and self._bindings
            else None
        )

    def _merge(
        self,
        *,
        left: expr,
        right: expr,
        root: bool = False,
    ) -> expr | None:
        """Unify a type position, reserving constructor and metadata syntax.

        Args:
            left (expr): First node.
            right (expr): Second node.
            root (bool): Whether this is the composite template's outer node.

        Returns:
            expr | None: Unified expression, or None for an unsafe template.

        """
        if key(node=left) == key(node=right):
            return deepcopy(x=left)
        first: tuple[expr, ...] = children(
            node=left,
            constructors=self._constructors,
        )
        second: tuple[expr, ...] = children(
            node=right,
            constructors=self._constructors,
        )
        if first and len(first) == len(second):
            if key(node=rebuild(node=left, parts=second)) != key(node=right):
                return None
            parts: list[expr] = []
            for a, b in zip(first, second, strict=True):
                merged: expr | None = self._merge(left=a, right=b)
                if merged is None:
                    return None
                parts.append(merged)
            return rebuild(node=left, parts=tuple(parts))
        if root or not all(
            isinstance(node, (Name, Attribute, Subscript, BinOp))
            or (isinstance(node, Constant) and node.value is None)
            for node in (left, right)
        ):
            return None
        pair: tuple[str, str] = key(node=left), key(node=right)
        parameter: str | None = self._bindings.get(pair)
        if parameter is None:
            index: int = len(self._bindings) + 1
            parameter = f"AliasT{index}"
            while parameter in self._reserved:
                index += 1
                parameter = f"AliasT{index}"
            self._reserved.add(parameter)
            self._bindings[pair] = parameter
        return Name(id=parameter, ctx=Load())
