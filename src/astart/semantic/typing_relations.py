"""Conservative structural and nominal type-contract relationships.

The library is static: no runtime imports, isinstance tests, descriptor calls,
or eval of analyzed source. Unrecognized relationships stay unresolved.

"""

from __future__ import annotations

from ast import Constant, parse
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Final, final

from astart.semantic.parameter_kinds import ParameterKind
from astart.semantic.type_shapes import TypeShape, join_types, type_shape

if TYPE_CHECKING:
    from ast import expr
    from collections.abc import Callable

    from astart.semantic.type_expressions import TypeExpression
    from astart.semantic.typing_contracts import (
        CallableContract,
        ClassContract,
        ContractIndex,
        ParameterContract,
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Compatibility:
    """A three-valued subtype result with declarative evidence.

    Attributes:
        compatible (bool | None): Compatible retained as bool | None by this
            instance.
        evidence (tuple[str, ...]): Evidence retained as tuple[str, ...] by
            this instance.

    """

    compatible: bool | None
    evidence: tuple[str, ...] = ()


@final
class Constants:
    """Static collection ABC edges and generic variance policies.

    Attributes:
        abc_bases (ClassVar[dict[str, frozenset[str]]]): Abc bases retained as
            ClassVar[dict[str,
            frozenset[str]]] by this instance.
        aliases (ClassVar[dict[str, str]]): Aliases retained as
            ClassVar[dict[str, str]] by this instance.
        covariant (frozenset[str]): Covariant retained as frozenset[str] by
            this instance.
        invariant (frozenset[str]): Invariant retained as frozenset[str] by
            this instance.
        pair_size (Final[int]): Arity of key/value type-argument pairs.
        qualifiers (Final[frozenset[str]]): Grouped module constant.
        builtin_nominals (Final[frozenset[str]]): Grouped module constant.

    """

    abc_bases: ClassVar[dict[str, frozenset[str]]] = {
        "list": frozenset(
            (
                "Collection",
                "Sequence",
                "MutableSequence",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "tuple": frozenset(
            (
                "Collection",
                "Sequence",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "str": frozenset(
            (
                "Collection",
                "Sequence",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "bytes": frozenset(
            (
                "Collection",
                "Sequence",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "set": frozenset(
            (
                "Collection",
                "Set",
                "MutableSet",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "frozenset": frozenset(
            ("Collection", "Set", "Iterable", "Sized", "Container"),
        ),
        "dict": frozenset(
            (
                "Collection",
                "Mapping",
                "MutableMapping",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "range": frozenset(
            (
                "Collection",
                "Sequence",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "generator": frozenset(("Iterator", "Generator", "Iterable")),
        "Iterator": frozenset(("Iterable",)),
        "Generator": frozenset(("Iterator", "Iterable")),
        "deque": frozenset(
            (
                "MutableSequence",
                "Sequence",
                "Collection",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
            ),
        ),
        "bytearray": frozenset(
            (
                "MutableSequence",
                "Sequence",
                "Collection",
                "Iterable",
                "Reversible",
                "Sized",
                "Container",
                "Buffer",
            ),
        ),
        "memoryview": frozenset(
            (
                "Sequence",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
                "Buffer",
            ),
        ),
        "defaultdict": frozenset(
            (
                "MutableMapping",
                "Mapping",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "OrderedDict": frozenset(
            (
                "MutableMapping",
                "Mapping",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "Counter": frozenset(
            (
                "MutableMapping",
                "Mapping",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "ChainMap": frozenset(
            (
                "MutableMapping",
                "Mapping",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "UserDict": frozenset(
            (
                "MutableMapping",
                "Mapping",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "UserList": frozenset(
            (
                "MutableSequence",
                "Sequence",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "UserString": frozenset(
            ("Sequence", "Collection", "Iterable", "Sized", "Container"),
        ),
        "MappingView": frozenset(("Sized",)),
        "KeysView": frozenset(
            (
                "MappingView",
                "Set",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "ValuesView": frozenset(
            ("MappingView", "Collection", "Iterable", "Sized", "Container"),
        ),
        "ItemsView": frozenset(
            (
                "MappingView",
                "Set",
                "Collection",
                "Iterable",
                "Sized",
                "Container",
            ),
        ),
        "AsyncIterator": frozenset(("AsyncIterable",)),
        "AsyncGenerator": frozenset(("AsyncIterator", "AsyncIterable")),
        "Coroutine": frozenset(("Awaitable",)),
        "Sequence": frozenset(
            ("Collection", "Iterable", "Sized", "Container", "Reversible"),
        ),
        "MutableSequence": frozenset(
            ("Sequence", "Collection", "Iterable", "Sized", "Container"),
        ),
        "Mapping": frozenset(("Collection", "Iterable", "Sized", "Container")),
        "MutableMapping": frozenset(
            ("Mapping", "Collection", "Iterable", "Sized", "Container"),
        ),
        "Set": frozenset(("Collection", "Iterable", "Sized", "Container")),
        "MutableSet": frozenset(
            ("Set", "Collection", "Iterable", "Sized", "Container"),
        ),
        "Collection": frozenset(("Iterable", "Sized", "Container")),
    }
    covariant: frozenset[str] = frozenset(
        (
            "Iterable",
            "Iterator",
            "Sequence",
            "Collection",
            "Set",
            "frozenset",
            "Reversible",
            "Awaitable",
            "Coroutine",
            "AsyncIterable",
            "AsyncIterator",
            "AsyncGenerator",
            "Generator",
            "ValuesView",
            "KeysView",
            "ItemsView",
        ),
    )
    invariant: frozenset[str] = frozenset(
        (
            "list",
            "dict",
            "set",
            "MutableSequence",
            "MutableSet",
            "MutableMapping",
            "deque",
            "defaultdict",
            "Counter",
            "OrderedDict",
            "ChainMap",
            "UserDict",
            "UserList",
        ),
    )
    aliases: ClassVar[dict[str, str]] = {
        "typing.List": "list",
        "typing.Dict": "dict",
        "typing.Tuple": "tuple",
        "typing.Set": "set",
        "typing.FrozenSet": "frozenset",
        "typing.Sequence": "Sequence",
        "typing.Mapping": "Mapping",
        "typing.MutableMapping": "MutableMapping",
        "typing.Iterable": "Iterable",
        "typing.Iterator": "Iterator",
        "typing.Collection": "Collection",
        "typing.Callable": "Callable",
        "collections.abc.Callable": "Callable",
        "typing.Awaitable": "Awaitable",
        "typing.Optional": "union",
        "typing.AsyncIterable": "AsyncIterable",
        "typing.AsyncIterator": "AsyncIterator",
        "typing.AsyncGenerator": "AsyncGenerator",
        "typing.Generator": "Generator",
        "typing.KeysView": "KeysView",
        "typing.ValuesView": "ValuesView",
        "typing.ItemsView": "ItemsView",
        "typing.Deque": "deque",
        "typing.DefaultDict": "defaultdict",
        "typing.Counter": "Counter",
        "typing.Literal": "Literal",
        "typing.LiteralString": "LiteralString",
        "typing.Never": "Never",
        "typing.NoReturn": "Never",
        "typing.TypeGuard": "TypeGuard",
        "typing.TypeIs": "TypeIs",
        "typing.ByteString": "ByteString",
        "typing.Hashable": "Hashable",
    }
    pair_size: Final[int] = 2

    qualifiers: Final[frozenset[str]] = frozenset(
        (
            "Annotated",
            "Final",
            "ClassVar",
            "Required",
            "NotRequired",
            "ReadOnly",
        ),
    )
    builtin_nominals: Final[frozenset[str]] = frozenset(
        (
            "str",
            "bytes",
            "int",
            "float",
            "complex",
            "bool",
            "list",
            "tuple",
            "dict",
            "set",
            "frozenset",
            "None",
            "range",
        ),
    )


def normalize(*, name: str) -> str:
    """Canonicalize well-known collection/typing generic aliases.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        str: str produced by this operation.

    """
    normalized: str = Constants.aliases.get(name, name)
    return normalized.removeprefix("collections.abc.")


def _generic_arguments(
    *,
    source: TypeShape,
    target: str,
) -> tuple[TypeShape, ...]:
    """Convert builtin collection parameters to ABC views where meaningful.

    Args:
        source (TypeShape): The source examined while convert builtin
            collection
            parameters to ABC views where meaningful.
        target (str): The target examined while convert builtin collection
            parameters to ABC views where meaningful.

    Returns:
        tuple[TypeShape, ...]: tuple[TypeShape, ...] produced by this
            operation.

    """
    if source.name in (
        "dict",
        "defaultdict",
        "OrderedDict",
        "Counter",
        "ChainMap",
        "UserDict",
    ) and target in ("Mapping", "MutableMapping"):
        return source.arguments
    if source.name in (
        "dict",
        "defaultdict",
        "OrderedDict",
        "Counter",
        "ChainMap",
        "UserDict",
    ) and target in ("Iterable", "Collection", "Container"):
        return source.arguments[:1]
    if source.name in (
        "str",
        "bytes",
        "bytearray",
        "memoryview",
        "range",
    ) and target in ("Sequence", "Iterable", "Collection", "MutableSequence"):
        return (TypeShape(name="str" if source.name == "str" else "int"),)
    return source.arguments


def _literal_value(*, source: str) -> tuple[str, str] | None:
    """Inspect only syntax literals; never evaluate analyzed expressions.

    Args:
        source (str): The source examined while inspect only syntax
            literals; never evaluate analyzed expressions.

    Returns:
        tuple[str, str] | None:
            tuple[str, str] | None produced by this operation.

    """
    try:
        node: expr = parse(source=source, mode="eval").body
    except SyntaxError:
        return None
    if isinstance(node, Constant) and (
        node.value is None or isinstance(node.value, (str, bytes, int, bool))
    ):
        return (
            "None" if node.value is None else type(node.value).__name__,
            repr(node.value),
        )
    return None


def _literal_set_inclusion(
    *,
    actual: TypeShape,
    expected: TypeShape,
) -> Compatibility:
    """Check that every actual literal is among the expected literals.

    Args:
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        expected (TypeShape): Expected supplied as TypeShape for this
            operation.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    wanted: set[tuple[str, str]] = set()
    for member in expected.arguments:
        value: tuple[str, str] | None = _literal_value(source=member.name)
        if value is None:
            return Compatibility(
                compatible=None,
                evidence=("unresolved literal member",),
            )
        wanted.add(value)
    matched: list[bool] = []
    for member in actual.arguments:
        value = _literal_value(source=member.name)
        if value is None:
            return Compatibility(
                compatible=None,
                evidence=("unresolved literal member",),
            )
        matched.append(value in wanted)
    return Compatibility(
        compatible=all(matched),
        evidence=("literal value set inclusion",),
    )


def _enum_member_comparison(
    *,
    member: TypeShape,
    right: str,
    index: ContractIndex | None,
) -> bool | None:
    """Compare an enum-member literal with a nominal expected type.

    Args:
        index (ContractIndex | None): Index identifying a position in the
            relevant sequence or source.
        member (TypeShape): Member supplied as TypeShape for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        bool | None: bool | None produced by this operation.

    """
    owner, _, _ = member.name.partition(".")
    if (
        index is not None
        and owner in index.classes
        and index.classes[owner].is_enum
    ):
        return right in (owner, "object")
    return None


def _literal_to_nominal(
    *,
    actual: TypeShape,
    expected: TypeShape,
    index: ContractIndex | None,
) -> Compatibility:
    """Check literals against a non-literal expected type.

    Args:
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        expected (TypeShape): Expected supplied as TypeShape for this
            operation.
        index (ContractIndex | None): Index identifying a position in the
            relevant sequence or source.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    right: str = normalize(name=expected.name)
    comparisons: list[bool | None] = []
    for member in actual.arguments:
        value: tuple[str, str] | None = _literal_value(source=member.name)
        if value is None:
            # Enum member literals have a declared owning nominal type.
            comparisons.append(
                _enum_member_comparison(
                    member=member,
                    right=right,
                    index=index,
                ),
            )
        elif right == "LiteralString":
            comparisons.append(value[0] == "str")
        else:
            relation: Compatibility = subtype(
                actual=TypeShape(name=value[0]),
                expected=expected,
                index=index,
            )
            comparisons.append(relation.compatible)
    return Compatibility(
        compatible=(
            False
            if False in comparisons
            else None
            if None in comparisons
            else True
        ),
        evidence=("literal-to-nominal assignability",),
    )


def _nominal_literal_relation(*, left: str, right: str) -> Compatibility:
    """Relate non-literal actual types to literal-flavored expected types.

    Args:
        left (str): Left supplied as str for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    unknown: bool = left in ("Unknown", "Any", "typing.Any", "WidenedUnknown")
    if right == "Literal":
        if unknown:
            return Compatibility(
                compatible=None,
                evidence=("unknown value cannot prove exact literal",),
            )
        return Compatibility(
            compatible=False,
            evidence=("nominal type does not identify a specific literal",),
        )
    if left == "LiteralString":
        return Compatibility(
            compatible=right in ("LiteralString", "str", "object"),
            evidence=("literal string base type",),
        )
    if right == "LiteralString":
        if unknown:
            return Compatibility(
                compatible=None,
                evidence=("string literal provenance unavailable",),
            )
        return Compatibility(
            compatible=False,
            evidence=("str does not guarantee literal provenance",),
        )
    return Compatibility(compatible=None)


def _literal_relation(
    *,
    actual: TypeShape,
    expected: TypeShape,
    index: ContractIndex | None,
) -> Compatibility:
    """Compare PEP 586 literals by value and type, not truthiness.

    Args:
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        expected (TypeShape): Expected supplied as TypeShape for this
            operation.
        index (ContractIndex | None): Index identifying a position in the
            relevant sequence or source.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    left: str = normalize(name=actual.name)
    right: str = normalize(name=expected.name)
    if left != "Literal":
        return _nominal_literal_relation(left=left, right=right)
    if not actual.arguments:
        return Compatibility(
            compatible=None,
            evidence=("empty literal selection",),
        )
    if right == "Literal":
        return _literal_set_inclusion(actual=actual, expected=expected)
    return _literal_to_nominal(actual=actual, expected=expected, index=index)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _SubtypeQuery:
    """One subtype question together with its normalized names and history.

    Attributes:
        actual (TypeShape): Actual retained as TypeShape by this instance.
        expected (TypeShape): Expected retained as TypeShape by this instance.
        index (ContractIndex | None): Index retained as ContractIndex | None by
            this instance.
        left (str): Left retained as str by this instance.
        outer_seen (frozenset[tuple[str, str]]): Outer seen retained as
            frozenset[tuple[str, str]] by this instance.
        right (str): Right retained as str by this instance.
        seen (frozenset[tuple[str, str]]): Seen retained as
            frozenset[tuple[str, str]] by this instance.

    """

    actual: TypeShape
    expected: TypeShape
    left: str
    right: str
    index: ContractIndex | None
    outer_seen: frozenset[tuple[str, str]]
    seen: frozenset[tuple[str, str]]

    def ask(self, *, actual: TypeShape, expected: TypeShape) -> Compatibility:
        """Answer a nested question using this query's cycle history.

        Args:
            actual (TypeShape): Actual supplied as TypeShape for this
                operation.
            expected (TypeShape): Expected supplied as TypeShape for this
                operation.

        Returns:
            Compatibility: Compatibility produced by this operation.

        """
        return subtype(
            actual=actual,
            expected=expected,
            index=self.index,
            _seen=self.seen,
        )


def _all_or_unknown(*, items: tuple[Compatibility, ...]) -> bool | None:
    """Join covariant results: any False fails, any None is unresolved.

    Args:
        items (tuple[Compatibility, ...]): Collection of items supplied for
            this operation.

    Returns:
        bool | None: bool | None produced by this operation.

    """
    if any(item.compatible is False for item in items):
        return False
    if any(item.compatible is None for item in items):
        return None
    return True


def _rule_actual_qualifier(query: _SubtypeQuery) -> Compatibility | None:
    """Look through type qualifiers wrapped around the actual type.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if query.left in Constants.qualifiers and query.actual.arguments:
        return subtype(
            actual=query.actual.arguments[0],
            expected=query.expected,
            index=query.index,
            _seen=query.outer_seen,
        )
    return None


def _rule_expected_qualifier(query: _SubtypeQuery) -> Compatibility | None:
    """Look through type qualifiers wrapped around the expected type.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if query.right in Constants.qualifiers and query.expected.arguments:
        return subtype(
            actual=query.actual,
            expected=query.expected.arguments[0],
            index=query.index,
            _seen=query.outer_seen,
        )
    return None


def _rule_actual_union(query: _SubtypeQuery) -> Compatibility | None:
    """Every alternative of an actual union must be compatible.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if query.left != "union":
        return None
    parts: tuple[Compatibility, ...] = tuple(
        query.ask(actual=piece, expected=query.expected)
        for piece in query.actual.arguments
    )
    return Compatibility(
        compatible=_all_or_unknown(items=parts),
        evidence=("all union alternatives",),
    )


def _rule_expected_union(query: _SubtypeQuery) -> Compatibility | None:
    """Require some alternative of an expected union to be compatible.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if query.right != "union":
        return None
    parts: tuple[Compatibility, ...] = tuple(
        query.ask(actual=query.actual, expected=piece)
        for piece in query.expected.arguments
    )
    if any(part.compatible is True for part in parts):
        verdict: bool | None = True
    elif any(part.compatible is None for part in parts):
        verdict = None
    else:
        verdict = False
    return Compatibility(compatible=verdict, evidence=("union alternative",))


def _rule_literal(query: _SubtypeQuery) -> Compatibility | None:
    """Delegate literal questions to the literal relation.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if query.left in ("Literal", "LiteralString") or query.right in (
        "Literal",
        "LiteralString",
    ):
        return _literal_relation(
            actual=query.actual,
            expected=query.expected,
            index=query.index,
        )
    return None


def _rule_callable(query: _SubtypeQuery) -> Compatibility | None:
    """Callables: contravariant parameters and covariant results.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    actual, expected = query.actual, query.expected
    if not (
        query.left == "Callable"
        and query.right == "Callable"
        and len(actual.arguments)
        == len(expected.arguments)
        == Constants.pair_size
    ):
        return None
    given, wanted = actual.arguments[0], expected.arguments[0]
    if not (
        given.name == wanted.name == "parameters"
        and len(given.arguments) == len(wanted.arguments)
    ):
        return None
    args: tuple[Compatibility, ...] = tuple(
        query.ask(actual=base, expected=child)
        for child, base in zip(given.arguments, wanted.arguments, strict=True)
    )
    returned: Compatibility = query.ask(
        actual=actual.arguments[1],
        expected=expected.arguments[1],
    )
    everything: tuple[Compatibility, ...] = (*args, returned)
    if all(item.compatible is True for item in everything):
        verdict: bool | None = True
    elif any(item.compatible is False for item in everything):
        verdict = False
    else:
        verdict = None
    return Compatibility(
        compatible=verdict,
        evidence=("callable contravariant parameters and covariant result",),
    )


def _rule_trivial(query: _SubtypeQuery) -> Compatibility | None:
    """Identity, dynamic typing, unresolved types, ``object`` and ``Never``.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    left, right = query.left, query.right
    if query.actual == query.expected or right in ("Any", "typing.Any"):
        return Compatibility(
            compatible=True,
            evidence=("identical or dynamically typed contract",),
        )
    if left in ("Any", "typing.Any", "Unknown", "WidenedUnknown") or right in (
        "Unknown",
        "WidenedUnknown",
    ):
        return Compatibility(compatible=None, evidence=("unresolved type",))
    if right == "object":
        return Compatibility(
            compatible=True,
            evidence=("all Python values are objects",),
        )
    if left == "Never":
        return Compatibility(compatible=True, evidence=("unreachable value",))
    return None


def _rule_numeric_tower(query: _SubtypeQuery) -> Compatibility | None:
    """Apply PEP 484 numeric promotion.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    left, right = query.left, query.right
    if (
        (right in ("float", "complex") and left in ("int", "bool"))
        or (right == "complex" and left == "float")
        or (right == "int" and left == "bool")
    ):
        return Compatibility(compatible=True, evidence=("numeric tower",))
    return None


def _rule_distinct_builtins(query: _SubtypeQuery) -> Compatibility | None:
    """Different builtin nominal types without an ABC relation never match.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    left, right = query.left, query.right
    if (
        left in Constants.builtin_nominals
        and right in Constants.builtin_nominals
        and left != right
        and right not in Constants.abc_bases.get(left, frozenset())
    ):
        return Compatibility(
            compatible=False,
            evidence=("different known builtin nominal types",),
        )
    return None


def _rule_protocol(query: _SubtypeQuery) -> Compatibility | None:
    """Check expected protocols structurally.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    index: ContractIndex | None = query.index
    if (
        index is not None
        and query.right in index.classes
        and index.classes[query.right].is_protocol
    ):
        return protocol_compatible(
            actual=query.actual,
            protocol=index.classes[query.right],
            index=index,
        )
    return None


def _rule_generic_nominal(query: _SubtypeQuery) -> Compatibility | None:
    """Compare type arguments of a shared nominal or ABC base.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    left, right = query.left, query.right
    if not (
        left == right or right in Constants.abc_bases.get(left, frozenset())
    ):
        return None
    largs: tuple[TypeShape, ...] = _generic_arguments(
        source=query.actual,
        target=right,
    )
    rargs: tuple[TypeShape, ...] = query.expected.arguments
    if not rargs:
        return Compatibility(
            compatible=True,
            evidence=("nominal or collection ABC base",),
        )
    if len(largs) != len(rargs):
        return Compatibility(
            compatible=None,
            evidence=("generic arity unresolved",),
        )
    if right in Constants.invariant:
        return Compatibility(
            compatible=all(a == b for a, b in zip(largs, rargs, strict=True)),
            evidence=("invariant generic arguments",),
        )
    if (
        right == "Mapping"
        and len(largs) == len(rargs) == Constants.pair_size
        and largs[0] != rargs[0]
    ):
        return Compatibility(
            compatible=False,
            evidence=("mapping keys are invariant",),
        )
    parts: tuple[Compatibility, ...] = tuple(
        query.ask(actual=a, expected=b)
        for a, b in zip(largs, rargs, strict=True)
    )
    if all(p.compatible is True for p in parts):
        verdict: bool | None = True
    elif any(p.compatible is False for p in parts):
        verdict = False
    else:
        verdict = None
    return Compatibility(
        compatible=verdict,
        evidence=("covariant generic arguments",),
    )


def _rule_declared_inheritance(query: _SubtypeQuery) -> Compatibility | None:
    """Walk declared bases of locally defined classes.

    Args:
        query (_SubtypeQuery): Query supplied as _SubtypeQuery for this
            operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    index: ContractIndex | None = query.index
    if index is None or query.left not in index.classes:
        return None
    pending: list[str] = list(index.classes[query.left].bases)
    encountered: set[str] = set()
    while pending:
        current: str = pending.pop(0)
        if current in encountered:
            continue
        encountered.add(current)
        if normalize(name=current) == query.right:
            return Compatibility(
                compatible=True,
                evidence=("declared inheritance",),
            )
        if current in index.classes:
            pending.extend(index.classes[current].bases)
    if query.right in index.classes:
        return Compatibility(
            compatible=False,
            evidence=("known unrelated nominal classes",),
        )
    return None


_SUBTYPE_RULES: Final[
    tuple[Callable[[_SubtypeQuery], Compatibility | None], ...]
] = (
    _rule_actual_qualifier,
    _rule_expected_qualifier,
    _rule_actual_union,
    _rule_expected_union,
    _rule_literal,
    _rule_callable,
    _rule_trivial,
    _rule_numeric_tower,
    _rule_distinct_builtins,
    _rule_protocol,
    _rule_generic_nominal,
    _rule_declared_inheritance,
)


def subtype(
    *,
    actual: TypeShape,
    expected: TypeShape,
    index: ContractIndex | None = None,
    _seen: frozenset[tuple[str, str]] = frozenset(),
) -> Compatibility:
    """Determine soundly known compatibility, returning None if unresolved.

    Unbound generics and unknown types are *indeterminate*, not automatically
    compatible. Invariant mutable containers do not admit numeric promotion.

    Args:
        _seen (frozenset[tuple[str, str]]): Seen supplied as
            frozenset[tuple[str, str]] for this operation.
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        expected (TypeShape): Expected supplied as TypeShape for this
            operation.
        index (ContractIndex | None): Index identifying a position in the
            relevant sequence or source.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    key: tuple[str, str] = (str(object=actual), str(object=expected))
    if key in _seen:
        return Compatibility(
            compatible=None,
            evidence=("recursive subtype cycle",),
        )
    query: _SubtypeQuery = _SubtypeQuery(
        actual=actual,
        expected=expected,
        left=normalize(name=actual.name),
        right=normalize(name=expected.name),
        index=index,
        outer_seen=_seen,
        seen=_seen | {key},
    )
    for rule in _SUBTYPE_RULES:
        verdict: Compatibility | None = rule(query)
        if verdict is not None:
            return verdict
    return Compatibility(
        compatible=None,
        evidence=("unsupported or external inheritance",),
    )


def _protocol_requirements(
    *,
    protocol: ClassContract,
    index: ContractIndex,
) -> tuple[dict[str, TypeShape], dict[str, CallableContract]]:
    """Collect fields and methods required by a protocol and its bases.

    Args:
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        protocol (ClassContract): Protocol supplied as ClassContract for this
            operation.

    Returns:
        tuple[dict[str, TypeShape], dict[str, CallableContract]]:
            tuple[dict[str, TypeShape], dict[str,
            CallableContract]] produced by this operation.

    """
    required_fields: dict[str, TypeShape] = {}
    required_methods: dict[str, CallableContract] = {}
    pending: list[str] = [protocol.name]
    seen: set[str] = set()
    while pending:
        current: str = pending.pop(0)
        if current in seen:
            continue
        seen.add(current)
        declaring: ClassContract | None = index.classes.get(current)
        if declaring is None:
            continue
        for name, hint in declaring.members:
            required_fields.setdefault(name, type_shape(expression=hint))
        for method in declaring.methods:
            method_name: str = method.qualified_name.rsplit(
                sep=".",
                maxsplit=1,
            )[-1]
            required_methods.setdefault(method_name, method)
        pending.extend(
            base for base in declaring.bases if base in index.classes
        )
    return required_fields, required_methods


def _property_implementation(
    *,
    owner: str,
    name: str,
    index: ContractIndex,
) -> TypeShape | None:
    """Find the implemented type of a field, including property getters.

    Args:
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        name (str): Identifier of the name being resolved.
        owner (str): Owner supplied as str for this operation.

    Returns:
        TypeShape | None: TypeShape | None produced by this operation.

    """
    hint: TypeExpression | None = index.class_member(owner=owner, name=name)
    if hint is not None:
        return type_shape(expression=hint)
    property_signature: CallableContract | None = next(
        (
            method
            for method in index.variants(qualified_name=f"{owner}.{name}")
            if method.method_kind == "property" and method.returns is not None
        ),
        None,
    )
    if property_signature is None:
        property_signature = index.inherited_method(owner=owner, method=name)
    if (
        property_signature is not None
        and property_signature.method_kind == "property"
        and property_signature.returns is not None
    ):
        return type_shape(expression=property_signature.returns)
    return None


def _field_mismatch(
    *,
    owner: str,
    required_fields: dict[str, TypeShape],
    index: ContractIndex,
) -> Compatibility | None:
    """Return the first unsatisfied protocol field, if any.

    Args:
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        owner (str): Owner supplied as str for this operation.
        required_fields (dict[str, TypeShape]): Required fields supplied as
            dict[str,
            TypeShape] for this operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    for name, requirement in required_fields.items():
        implementation: TypeShape | None = _property_implementation(
            owner=owner,
            name=name,
            index=index,
        )
        if implementation is None:
            return Compatibility(
                compatible=False,
                evidence=(f"missing protocol field {name}",),
            )
        match: Compatibility = subtype(
            actual=implementation,
            expected=requirement,
            index=index,
        )
        if match.compatible is not True:
            return Compatibility(
                compatible=match.compatible,
                evidence=(f"field {name}: {match.evidence}",),
            )
    return None


def _method_mismatch(
    *,
    owner: str,
    required_methods: dict[str, CallableContract],
    index: ContractIndex,
) -> Compatibility | None:
    """Return the first unsatisfied protocol method, if any.

    Args:
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        owner (str): Owner supplied as str for this operation.
        required_methods (dict[str, CallableContract]): Required methods
            supplied as dict[str,
            CallableContract] for this operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    for name, required in required_methods.items():
        existing: CallableContract | None = next(
            iter(index.variants(qualified_name=f"{owner}.{name}")),
            None,
        )
        if existing is None:
            existing = index.inherited_method(owner=owner, method=name)
        if existing is None:
            return Compatibility(
                compatible=False,
                evidence=(f"missing protocol method {name}",),
            )
        contract: Compatibility = method_compatible(
            implementation=existing,
            inherited=required,
            index=index,
        )
        if contract.compatible is not True:
            return Compatibility(
                compatible=contract.compatible,
                evidence=(f"protocol method {name}: {contract.evidence}",),
            )
    return None


def protocol_compatible(
    *,
    actual: TypeShape,
    protocol: ClassContract,
    index: ContractIndex,
) -> Compatibility:
    """Check structural protocol requirements, including inherited contracts.

    Both protocol inheritance and implementation inheritance contribute
    members. Read-only properties can satisfy attribute requirements, but
    methods retain their full callable compatibility constraints.

    Args:
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        protocol (ClassContract): Protocol supplied as ClassContract for this
            operation.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    cls: ClassContract | None = index.classes.get(normalize(name=actual.name))
    if cls is None:
        return Compatibility(
            compatible=None,
            evidence=("implementation structure unavailable",),
        )
    if cls.name == protocol.name:
        return Compatibility(compatible=True, evidence=("same protocol",))
    fields, methods = _protocol_requirements(protocol=protocol, index=index)
    failure: Compatibility | None = _field_mismatch(
        owner=cls.name,
        required_fields=fields,
        index=index,
    ) or _method_mismatch(
        owner=cls.name,
        required_methods=methods,
        index=index,
    )
    if failure is not None:
        return failure
    return Compatibility(
        compatible=True,
        evidence=("all inherited protocol contracts satisfied",),
    )


def _parameter_mismatch(
    *,
    current: ParameterContract,
    previous: ParameterContract,
    index: ContractIndex,
) -> Compatibility | None:
    """Explain why an overriding parameter is incompatible, if it is.

    Args:
        current (ParameterContract): Current supplied as ParameterContract for
            this operation.
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        previous (ParameterContract): Previous supplied as ParameterContract
            for this operation.

    Returns:
        Compatibility | None: Compatibility | None produced by this operation.

    """
    if current.kind != previous.kind:
        return Compatibility(
            compatible=False,
            evidence=(f"changed parameter kind for {previous.name}",),
        )
    if (
        current.kind
        in (ParameterKind.KEYWORD_ONLY, ParameterKind.POSITIONAL_OR_KEYWORD)
        and current.name != previous.name
    ):
        return Compatibility(
            compatible=False,
            evidence=(f"renamed keyword-capable parameter {previous.name}",),
        )
    if previous.has_default and not current.has_default:
        return Compatibility(
            compatible=False,
            evidence=(f"removed default for {previous.name}",),
        )
    if current.annotation is None or previous.annotation is None:
        return None
    argument: Compatibility = subtype(
        actual=type_shape(expression=previous.annotation),
        expected=type_shape(expression=current.annotation),
        index=index,
    )
    if argument.compatible is True:
        return None
    detail: str = (
        "narrowed against base"
        if argument.compatible is False
        else "unresolved"
    )
    return Compatibility(
        compatible=argument.compatible,
        evidence=(f"parameter {previous.name} {detail}",),
    )


def method_compatible(
    *,
    implementation: CallableContract,
    inherited: CallableContract,
    index: ContractIndex,
) -> Compatibility:
    """Check method parameter contravariance and return covariance.

    Args:
        implementation (CallableContract): Implementation supplied as
            CallableContract for this operation.
        index (ContractIndex): Index identifying a position in the relevant
            sequence or source.
        inherited (CallableContract): Inherited supplied as CallableContract
            for this operation.

    Returns:
        Compatibility: Compatibility produced by this operation.

    """
    if implementation.method_kind != inherited.method_kind and (
        implementation.method_kind in ("instance", "static", "class")
        or inherited.method_kind in ("instance", "static", "class")
    ):
        return Compatibility(
            compatible=False,
            evidence=("incompatible method binding kind",),
        )
    child: tuple[ParameterContract, ...] = implementation.parameters
    base: tuple[ParameterContract, ...] = inherited.parameters
    # Receiver spelling (self/cls) is not part of override compatibility.
    if implementation.method_kind in ("instance", "class"):
        child = child[1:]
    if inherited.method_kind in ("instance", "class"):
        base = base[1:]
    if len(child) != len(base):
        return Compatibility(
            compatible=False,
            evidence=("different effective parameter counts",),
        )
    for current, previous in zip(child, base, strict=True):
        mismatch: Compatibility | None = _parameter_mismatch(
            current=current,
            previous=previous,
            index=index,
        )
        if mismatch is not None:
            return mismatch
    if implementation.returns is not None and inherited.returns is not None:
        result: Compatibility = subtype(
            actual=type_shape(expression=implementation.returns),
            expected=type_shape(expression=inherited.returns),
            index=index,
        )
        if result.compatible is not True:
            return Compatibility(
                compatible=result.compatible,
                evidence=("override return is not proved covariant",),
            )
    return Compatibility(
        compatible=True,
        evidence=("callable override contract compatible",),
    )


def specialize(
    *,
    declared: TypeShape,
    bindings: dict[str, TypeShape],
) -> TypeShape:
    """Substitute bound generic type parameters recursively.

    Args:
        bindings (dict[str, TypeShape]): Bindings supplied as dict[str,
            TypeShape] for this operation.
        declared (TypeShape): Declared supplied as TypeShape for this
            operation.

    Returns:
        TypeShape: TypeShape produced by this operation.

    """
    return (
        bindings.get(declared.name, declared)
        if not declared.arguments
        else TypeShape(
            name=declared.name,
            arguments=tuple(
                specialize(declared=child, bindings=bindings)
                for child in declared.arguments
            ),
        )
    )


def unify(
    *,
    declared: TypeShape,
    actual: TypeShape,
    parameters: frozenset[str],
    bindings: dict[str, TypeShape],
) -> bool:
    """Unify structural generic variables; unknowns are never exact.

    Args:
        actual (TypeShape): Actual supplied as TypeShape for this operation.
        bindings (dict[str, TypeShape]): Bindings supplied as dict[str,
            TypeShape] for this operation.
        declared (TypeShape): Declared supplied as TypeShape for this
            operation.
        parameters (frozenset[str]): Collection of parameters supplied for this
            operation.

    Returns:
        bool: Whether the requested condition holds.

    """
    if declared.name in parameters:
        existing: TypeShape | None = bindings.get(declared.name)
        bindings[declared.name] = (
            actual
            if existing is None
            else join_types(left=existing, right=actual, promote=False)
        )
        return True
    if declared.name == actual.name and len(declared.arguments) == len(
        actual.arguments,
    ):
        return all(
            unify(
                declared=left,
                actual=right,
                parameters=parameters,
                bindings=bindings,
            )
            for left, right in zip(
                declared.arguments,
                actual.arguments,
                strict=True,
            )
        )
    return False
